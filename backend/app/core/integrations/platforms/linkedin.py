"""LinkedIn integration — real Playwright profile scraper with offline simulation fallback.

Uses the bundled ``linkedin_scraper`` package (copied into ``backend/linkedin_scraper``) to
scrape a live LinkedIn profile: profile description (about), experience, skills, and the
certifications section (via the accomplishments extractor). The scraped data feeds the
candidate report (certifications are surfaced there).

Real scraping is **gated by config**: it only runs when ``LINKEDIN_SCRAPE_ENABLED`` is true
and a session file (``LINKEDIN_SESSION_PATH``) or credentials (``LINKEDIN_EMAIL`` /
``LINKEDIN_PASSWORD``) are available. Otherwise it returns deterministic simulated demo
data (the default), which keeps the offline demo and CI green.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import random
import time

from ....config import settings
from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("linkedin", "LinkedIn", "li", "https://linkedin.com/in/{handle}", "public profile id", True)

CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

_memory_store: dict[str, tuple[dict, float]] = {}


def _url_for_handle(handle: str) -> str:
    handle = handle.strip().lstrip("@").rstrip("/")
    return f"https://www.linkedin.com/in/{handle}"


def _cache_get(url: str) -> dict | None:
    entry = _memory_store.get(url)
    if entry is None:
        return None
    data, expires_at = entry
    if time.time() * 1000 > expires_at:
        _memory_store.pop(url, None)
        return None
    return data


def _cache_set(url: str, data: dict) -> None:
    _memory_store[url] = (data, time.time() * 1000 + CACHE_TTL_MS)


def person_to_scrape_data(person, handle: str) -> dict:
    """Map a scraped ``linkedin_scraper`` Person into the integration data contract.

    Pure function (no browser) so it is unit-testable. Certifications are filtered out of
    the generic accomplishments list; skills carry their endorsement counts.
    """
    certs: list[dict] = [
        {
            "title": c.title,
            "issuer": c.issuer,
            "issued_date": c.issued_date,
            "credential_id": c.credential_id,
            "credential_url": c.credential_url,
        }
        for c in person.accomplishments
        if c.category == "certification"
    ]
    top_exp = person.experiences[0] if person.experiences else None
    return {
        "_source": "linkedin-scraper",
        "username": handle,
        "name": person.name,
        "headline": top_exp.position_title if top_exp else None,
        "about": person.about,
        "location": person.location,
        "profile_url": person.linkedin_url,
        "current_companies": [
            e.institution_name for e in person.experiences[:3] if e.institution_name
        ],
        "schools": [
            e.institution_name for e in person.educations[:2] if e.institution_name
        ],
        "experiences": [
            {
                "position_title": e.position_title,
                "company": e.institution_name,
                "from_date": e.from_date,
                "to_date": e.to_date,
                "duration": e.duration,
                "location": e.location,
                "description": e.description,
            }
            for e in person.experiences
        ],
        "educations": [
            {
                "institution": e.institution_name,
                "degree": e.degree,
                "from_date": e.from_date,
                "to_date": e.to_date,
            }
            for e in person.educations
        ],
        "skills": [
            {"name": s.name, "endorsements": s.endorsements, "url": s.linkedin_url}
            for s in person.skills
        ],
        "certifications": certs,
        "endorsements": sum(s.endorsements or 0 for s in person.skills),
        "connections": None,
        "activity_visible": None,
    }


def _run_scrape(url: str, handle: str, session_path: str | None, email: str | None, password: str | None) -> dict:
    """Launch the async Playwright scraper in a dedicated worker thread/event loop.

    Running in a thread with its own event loop avoids colliding with FastAPI's running
    loop when ``collect()`` is invoked synchronously from a request handler.
    """
    from linkedin_scraper import BrowserManager, PersonScraper
    from linkedin_scraper.core import login_with_credentials

    def _worker() -> dict:
        async def _go():
            async with BrowserManager(headless=True) as browser:
                if session_path and os.path.exists(session_path):
                    await browser.load_session(session_path)
                else:
                    await login_with_credentials(browser.page, email, password)
                    if session_path:
                        try:
                            await browser.save_session(session_path)
                        except Exception:
                            pass
                scraper = PersonScraper(browser.page)
                person = await scraper.scrape(url)
                return person_to_scrape_data(person, handle)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_go())
        finally:
            loop.close()

    cached = _cache_get(url)
    if cached is not None:
        return cached

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_worker)
        data = future.result(timeout=180)

    _cache_set(url, data)
    return data


class LinkedInIntegration(SimulatedPlatformMixin):
    platform_id = "linkedin"
    platform_label = "LinkedIn"
    real_api = True

    def __init__(self, simulate: bool = False) -> None:
        super().__init__(simulate=simulate)

    # ------------------------------------------------------------------ #
    # Offline simulation (demo candidate / fallback when scraping disabled)
    # ------------------------------------------------------------------ #

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        headline = resume.personal.headline if resume and resume.personal.headline else "Software Developer"
        companies = [e.company for e in ((resume.experience or []) if resume else []) if e.company][:3]
        return {
            "headline": headline,
            "connections": rng.randint(200, 900),
            "current_companies": companies,
            "schools": [e.college for e in ((resume.education or []) if resume else []) if e.college][:2],
            "endorsements": rng.randint(5, 60),
            "activity_visible": bool(rng.randint(0, 1)),
        }

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        # Gated: when real scraping is disabled, behave like the legacy simulation.
        if not settings.linkedin_scrape_enabled:
            return self._simulated_collect(handle, context)

        url = _url_for_handle(handle)
        session_path = settings.linkedin_session_path
        email = settings.linkedin_email
        password = settings.linkedin_password

        have_session = bool(session_path and os.path.exists(session_path))
        have_creds = bool(email and password)
        if not have_session and not have_creds:
            raise ProfileCollectError(
                "LinkedIn real scraping is enabled but no session file "
                f"({session_path}) or LINKEDIN_EMAIL/LINKEDIN_PASSWORD credentials were found. "
                "Run scripts/create_session.py to generate a session, or set credentials."
            )

        try:
            return _run_scrape(url, handle, session_path, email, password)
        except ProfileCollectError:
            raise
        except Exception as e:  # noqa: BLE001 - surface as a clean collect error
            raise ProfileCollectError(f"LinkedIn scraping failed: {e}") from e
