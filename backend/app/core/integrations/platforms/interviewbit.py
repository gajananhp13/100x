"""InterviewBit integration — live profile scraper via Playwright.

Fetches profile data by loading the public profile page in a headless browser
and extracting the rendered DOM. InterviewBit is a fully client-rendered Next.js
app with no public user API; the profile data only appears after JavaScript
executes, so a lightweight HTTP GET is insufficient.

Results are cached in-memory for 1 hour to avoid repeated browser launches.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
import time

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

logger = logging.getLogger(__name__)

DEF = PlatformDef(
    "interviewbit",
    "InterviewBit",
    "ib",
    "https://www.interviewbit.com/profile/{handle}/",
    "username",
    True,
)

CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

# ---------------------------------------------------------------------- #
# Username parsing
# ---------------------------------------------------------------------- #


def extract_username(input_value: str) -> str:
    """Extract a clean username from a handle or profile URL."""
    trimmed = input_value.strip()
    url_match = re.search(r"interviewbit\.com/profile/([^/?#]+)", trimmed)
    if url_match:
        return url_match.group(1)
    clean = trimmed.lstrip("@").rstrip("/")
    if clean and all(c.isalnum() or c in "_-" for c in clean):
        return clean
    raise ProfileCollectError(f'Invalid InterviewBit username or URL: "{input_value}"')


# ---------------------------------------------------------------------- #
# In-memory TTL cache
# ---------------------------------------------------------------------- #

_memory_store: dict[str, tuple[dict, float]] = {}


def _cache_get(username: str) -> dict | None:
    entry = _memory_store.get(username.lower())
    if entry is None:
        return None
    data, expires_at = entry
    if time.time() * 1000 > expires_at:
        _memory_store.pop(username.lower(), None)
        return None
    return data


def _cache_set(username: str, data: dict) -> None:
    _memory_store[username.lower()] = (data, time.time() * 1000 + CACHE_TTL_MS)


def clear_interviewbit_cache() -> None:
    """Clear the in-memory cache (used by tests)."""
    _memory_store.clear()


# ---------------------------------------------------------------------- #
# Browser-based scraping
# ---------------------------------------------------------------------- #

PROFILE_URL = "https://www.interviewbit.com/profile/{username}/"

_JS_EXTRACT = """
() => {
    const out = {};
    const bodyText = document.body.innerText || '';
    const bodyHtml = document.body.innerHTML || '';

    // Detect 404 / not-found pages
    if (bodyText.includes('Page Not Found') || bodyText.includes('404') && bodyText.length < 2000) {
        return { _not_found: true };
    }

    // Profile name — try common selectors, then fall back to h1
    const nameSelectors = [
        '.profile-overview-user-details__name',
        '[class*="profile"] [class*="name"]',
        'h1', 'h2',
    ];
    for (const sel of nameSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim().length > 1 && el.textContent.trim().length < 80) {
            out.name = el.textContent.trim();
            break;
        }
    }
    if (!out.name) {
        const ogTitle = document.querySelector('meta[property="og:title"]');
        if (ogTitle) {
            const parts = ogTitle.content.split('|')[0].trim().split(' - ');
            out.name = parts[0].trim();
        }
    }

    // Total problems solved — multiple patterns
    const solvedPatterns = [
        /(\\d+)\\s*Problems?\\s*Solved/i,
        /(\\d+)\\s*\\/\\s*\\d+\\s*problems/i,
        /Solved[\\s:]+(\\d+)/i,
    ];
    for (const pat of solvedPatterns) {
        const m = bodyText.match(pat);
        if (m) { out.problems_solved = parseInt(m[1], 10); break; }
    }
    if (!out.problems_solved) out.problems_solved = 0;

    // Streak
    const streakPatterns = [
        /Max\\s*Streak[\\s:]*?(\\d+)\\s*Day/i,
        /Streak[\\s:]+(\\d+)/i,
        /(\\d+)\\s*\\*?\\s*day\\s*streak/i,
    ];
    for (const pat of streakPatterns) {
        const m = bodyText.match(pat);
        if (m) { out.streak_days = parseInt(m[1], 10); break; }
    }
    if (!out.streak_days) out.streak_days = 0;

    // Active days
    const activePatterns = [
        /(\\d+)\\s*Active\\s*Days?/i,
        /Active[\\s:]+(\\d+)/i,
    ];
    for (const pat of activePatterns) {
        const m = bodyText.match(pat);
        if (m) { out.active_days = parseInt(m[1], 10); break; }
    }
    if (!out.active_days) out.active_days = 0;

    // Submission count
    const subPatterns = [
        /(\\d+)\\s*Submissions?/i,
        /Submissions?[\\s:]+(\\d+)/i,
    ];
    for (const pat of subPatterns) {
        const m = bodyText.match(pat);
        if (m) { out.total_submissions = parseInt(m[1], 10); break; }
    }
    if (!out.total_submissions) out.total_submissions = 0;

    // Rank — try selectors
    const rankSelectors = [
        '.profile-overview-user-details__rank',
        '[class*="rank"]',
    ];
    for (const sel of rankSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim().length > 0 && el.textContent.trim().length < 60) {
            out.rank = el.textContent.trim();
            break;
        }
    }

    // Badges
    const badgeEls = document.querySelectorAll('[class*="badge"]');
    out.badges_count = badgeEls.length;

    // Topics — look for topic-like items with / or percentages
    const topicEls = document.querySelectorAll('[class*="topic"], [class*="submission-analysis"] li, [class*="skill"] li');
    const topics = [];
    topicEls.forEach(el => {
        const text = el.textContent.trim();
        if (text && text.length < 100 && (text.includes('/') || text.includes('%'))) {
            topics.push(text);
        }
    });
    out.topics = topics.slice(0, 20);

    // Study plan / progress
    const planPatterns = [
        /(\\d+)\\s*\\/\\s*(\\d+)/,
        /Progress[\\s:]+(\\d+)\\s*\\/\\s*(\\d+)/i,
    ];
    for (const pat of planPatterns) {
        const m = bodyText.match(pat);
        if (m) {
            out.plan_solved = parseInt(m[1], 10);
            out.plan_total = parseInt(m[2], 10);
            break;
        }
    }

    // Debug: capture first 500 chars of page text for error messages
    out._page_preview = bodyText.substring(0, 500);

    return out;
}
"""


def _scrape_with_playwright(username: str) -> dict:
    """Launch a headless browser, load the profile, and extract data from the DOM."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ProfileCollectError(
            "playwright is required for InterviewBit scraping. "
            "Install with: pip install playwright && python -m playwright install chromium"
        )

    profile_url = PROFILE_URL.format(username=username)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                page.goto(profile_url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                raise ProfileCollectError(
                    f"Could not load InterviewBit profile page: {e}"
                ) from e

            # Wait for the profile content to render
            try:
                page.wait_for_selector(
                    ".profile-overview-user-details, .profile-interview-prep__card, .profile-activity-heatmap",
                    timeout=15000,
                )
            except Exception:
                # Profile might not exist or page structure changed — try anyway
                pass

            # Extra settle time for dynamic content
            page.wait_for_timeout(3000)

            raw = page.evaluate(_JS_EXTRACT)

            browser.close()

    except ProfileCollectError:
        raise
    except Exception as e:
        raise ProfileCollectError(
            f"InterviewBit scraping failed for '{username}': {e}"
        ) from e

    # Validate that we got some data
    if raw.get("_not_found"):
        raise ProfileCollectError(
            f'InterviewBit profile "{username}" not found.'
        )

    # Check if page has meaningful content (problems_solved > 0 or name found)
    has_name = bool(raw.get("name"))
    has_problems = raw.get("problems_solved", 0) > 0
    if not has_name and not has_problems:
        # Last resort: check if the page has any content at all
        preview = raw.get("_page_preview", "")
        if "InterviewBit" not in preview and len(preview) < 100:
            raise ProfileCollectError(
                f'InterviewBit profile "{username}" not found or has no public data.'
            )

    return raw


# ---------------------------------------------------------------------- #
# Integration
# ---------------------------------------------------------------------- #


class InterviewBitIntegration(SimulatedPlatformMixin):
    platform_id = "interviewbit"
    platform_label = "InterviewBit"
    real_api = True

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        username = extract_username(handle)
        cached = _cache_get(username)
        if cached is not None:
            return cached

        # Playwright sync API cannot run inside an asyncio event loop (FastAPI).
        # Run the sync scraping in a thread pool when called from async context.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                raw = pool.submit(_scrape_with_playwright, username).result(timeout=60)
        else:
            raw = _scrape_with_playwright(username)

        # Strip internal debug fields
        raw.pop("_page_preview", None)
        raw.pop("_not_found", None)

        profile_data = {
            "_source": "interviewbit-profile",
            "username": username,
            "name": raw.get("name"),
            "problems_solved": raw.get("problems_solved", 0),
            "streak_days": raw.get("streak_days", 0),
            "active_days": raw.get("active_days", 0),
            "total_submissions": raw.get("total_submissions", 0),
            "rank": raw.get("rank"),
            "badges_count": raw.get("badges_count", 0),
            "topics": raw.get("topics", []),
            "plan_solved": raw.get("plan_solved"),
            "plan_total": raw.get("plan_total"),
            "_rate_limit_hint": "InterviewBit has no public API; data scraped via headless browser. Cached for 1 hour.",
        }
        _cache_set(username, profile_data)
        return profile_data

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        total = int(30 + level * 200 + rng.randint(0, 80))
        return {
            "problems_solved": total,
            "streak_days": rng.randint(0, 90),
            "active_days": rng.randint(20, 300),
            "total_submissions": int(total * rng.uniform(1.2, 2.0)),
            "rank": f"Level {rng.randint(1, 8)}",
            "badges_count": rng.randint(0, 10),
            "topics": [],
            "plan_solved": rng.randint(5, total),
            "plan_total": 330,
        }
