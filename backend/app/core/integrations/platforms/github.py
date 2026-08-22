"""GitHub integration — live public HTML scraper plus offline simulation.

Fetches a user's profile and repository list directly from GitHub's public web
pages (github.com/{handle} and the ?tab=repositories[...] listing) using
realistic browser headers. No API token and no GitHub REST API are required, so
there is no hard per-hour quota the way the old api.github.com path had.

What maps cleanly from the HTML pages:
  - profile: name, login, avatar, bio, location, followers/following,
    public repo count, "X repositories available"
  - repositories (paginated): name, description, primary language, stars,
    forks, is-fork flag, topics, last-pushed date
  - per-repo (best-effort, top-N): README presence + quality (server-rendered)

Fields the REST API exposed but GitHub's plain HTML pages don't (commit counts,
contributors, CI/Dockerfile detection, recursive file trees, per-repo language
byte breakdown) are reported with safe defaults (0/False/empty) and marked in
`_rate_limit_hint` as "HTML-page best effort" so downstream analysis treats
them as unknown rather than guessed.

Results are cached in-memory for 1 hour to avoid hammering the public site.
"""

from __future__ import annotations

import random
import re
import time

import httpx

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("github", "GitHub", "gh", "https://github.com/{handle}", "username", True)

BASE = "https://github.com"
CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

HEADERS: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_PAGES = 10
MAX_REPOS = 100
README_REPO_LIMIT = 12


# ---------------------------------------------------------------------- #
# Username parsing
# ---------------------------------------------------------------------- #

def extract_username(input_value: str) -> str:
    """Extract a clean username from a handle, @handle, or profile URL."""
    trimmed = input_value.strip()
    url_match = re.search(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]*)", trimmed)
    if url_match:
        return url_match.group(1)
    clean = trimmed.lstrip("@").rstrip("/")
    if clean and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", clean):
        return clean
    raise ProfileCollectError(f'Invalid GitHub username or URL: "{input_value}"')


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


def clear_github_cache() -> None:
    """Clear the in-memory cache (used by tests)."""
    _memory_store.clear()


# ---------------------------------------------------------------------- #
# Number / text helpers
# ---------------------------------------------------------------------- #

def _parse_count(value: str | None) -> int:
    """Parse Github's compact counts: '317k' -> 317000, '1.2k' -> 1200, '0' -> 0."""
    if not value:
        return 0
    text = value.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([kKmM]?)$", text)
    if not m:
        return 0
    number = float(m.group(1))
    multiplier = {"k": 1000, "m": 1000000}.get(m.group(2).lower(), 1)
    return int(round(number * multiplier))


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _trim(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


# ---------------------------------------------------------------------- #
# Integration
# ---------------------------------------------------------------------- #

class GitHubIntegration(SimulatedPlatformMixin):
    platform_id = "github"
    platform_label = "GitHub"
    real_api = True

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        simulate: bool = False,
    ) -> None:
        super().__init__(simulate=simulate)
        self._transport = transport

    # ------------------------------------------------------------------ #
    # Live HTML helpers
    # ------------------------------------------------------------------ #

    def _get_html(self, url: str) -> httpx.Response:
        with httpx.Client(timeout=25, headers=HEADERS, transport=self._transport) as client:
            resp = client.get(url, follow_redirects=True)
        if resp.status_code in (403, 429):
            raise ProfileCollectError(
                "GitHub is temporarily blocking this request. Wait a moment and try again "
                "(this is not a token quota — the HTML scraper needs no token)."
            )
        if resp.status_code == 404:
            raise ProfileCollectError(f'GitHub user "{url.split("/")[-1]}" not found — check the username.')
        if resp.status_code >= 400:
            raise ProfileCollectError(f"GitHub returned HTTP {resp.status_code}.")
        return resp

    def _profile_url(self, handle: str) -> str:
        return f"{BASE}/{handle}"

    def _repos_url(self, handle: str, page: int) -> str:
        return f"{BASE}/{handle}?tab=repositories&page={page}"

    def _repo_url(self, full_name: str) -> str:
        return f"{BASE}/{full_name}"

    # ------------------------------------------------------------------ #
    # Parsers
    # ------------------------------------------------------------------ #

    def _parse_profile(self, html: str, handle: str) -> dict:
        """Extract profile-level fields from the profile HTML page."""
        data: dict = {}
        data["login"] = handle

        # Personal vs organization guard: personal accounts render a vcard block.
        if 'class="vcard-details"' not in html and 'class="vcard-names"' not in html:
            raise ProfileCollectError("Use a personal GitHub account, not an organization.")

        # repositories available (public repo count)
        m = re.search(r"([\d,]+(?:\.[\d]+)?[kKmM]?)\s+repositories\s+available", html)
        if m:
            data["public_repos"] = _parse_count(m.group(1))

        # followers / following (compact counts supported)
        m = re.search(
            r'tab=followers"[^>]*>.*?<span class="text-bold color-fg-default">([\d.,]+[kKmM]?)</span>\s*followers',
            html, re.DOTALL,
        )
        if m:
            data["followers"] = _parse_count(m.group(1))
        m = re.search(
            r'tab=following"[^>]*>.*?<span class="text-bold color-fg-default">([\d.,]+[kKmM]?)</span>\s*following',
            html, re.DOTALL,
        )
        if m:
            data["following"] = _parse_count(m.group(1))

        # avatar
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not m:
            m = re.search(r'<img[^>]+class="avatar[^"]*"[^>]+src="([^"]+)"', html)
        if m:
            data["avatar_url"] = m.group(1).split("?")[0]

        # name
        m = re.search(r'itemprop="name"[^>]*>\s*([^<]+)', html)
        if m:
            data["name"] = _trim(m.group(1))

        # bio
        m = re.search(
            r'itemprop="description"[^>]*>\s*(.*?)\s*</(?:div|p)>',
            html, re.DOTALL,
        )
        if m:
            data["bio"] = _trim(_strip_tags(m.group(1)))

        # location
        m = re.search(r'aria-label="Location: ([^"]*)"', html)
        if m:
            data["location"] = _trim(m.group(1))

        # total contributions heading (best-effort: 'X contributions in the last year')
        m = re.search(
            r"([\d,]+(?:\.[\d]+)?[kKmM]?)\s+contributions?\s+(?:in the last year|this year)",
            html, re.IGNORECASE,
        )
        if m:
            data["total_contributions"] = _parse_count(m.group(1))

        return data

    def _parse_repo_list(self, html: str) -> list[dict]:
        """Parse the repository listing items from a ?tab=repositories page."""
        repos: list[dict] = []
        for li in re.findall(r'<li[^>]*itemprop="owns"[^>]*>.*?</li>', html, re.DOTALL):
            # Repo name + link (also used to detect a fork by the card class)
            m = re.search(r'<a href="(/[^"]+)" itemprop="name codeRepository"[^>]*>\s*([^<]+)', li)
            if not m:
                continue
            path = m.group(1)
            name = _trim(m.group(2))
            if not path or "/" not in path.lstrip("/"):
                continue
            owner, _repo = path.strip("/").split("/", 1)
            is_fork = bool(re.search(r'class="[^"]*public fork[^"]*"', li))

            # description
            m = re.search(r'itemprop="description">\s*(.*?)\s*</p>', li, re.DOTALL)
            description = _trim(_strip_tags(m.group(1))) if m else None

            # primary language
            language = None
            m = re.search(r'itemprop="programmingLanguage">\s*([^<]+)<', li)
            if m:
                language = _trim(m.group(1))

            # stars / forks
            stars = 0
            m = re.search(r'href="/[^"]*(?:/|/)stargazers"[^>]*>.*?</svg>\s*([\d.,]+[kKmM]?\s?)</a>', li, re.DOTALL)
            if not m:
                m = re.search(r'/[^"]*/stargazers".*?</svg>\s*([\d.,]+[kKmM]?)\s*</a>', li, re.DOTALL)
            if m:
                stars = _parse_count(m.group(1))
            forks = 0
            m = re.search(r'/[^"]*/forks".*?</svg>\s*([\d.,]+[kKmM]?)\s*</a>', li, re.DOTALL)
            if m:
                forks = _parse_count(m.group(1))

            # topics
            topics = [
                _trim(tm.group(1))
                for tm in re.finditer(r'data-octo-dimensions="[^"]*topic[^"]*"[^>]*>\s*([^<]+)', li)
            ]

            # last pushed / updated
            pushed_at = None
            m = re.search(r'<relative-time[^>]*datetime="([^"]+)"', li)
            if m:
                pushed_at = m.group(1)
            m = re.search(r'aria-label="Updated on ([^"]+)"', li)
            if not pushed_at and m:
                pushed_at = m.group(1)
            if pushed_at and pushed_at.endswith("Z"):
                pushed_at = pushed_at[:-1] + "+00:00"

            repos.append({
                "name": name,
                "full_name": f"{owner}/{_repo}",
                "description": description,
                "html_url": f"{BASE}/{path}",
                "language": language,
                "stars": stars,
                "forks": forks,
                "topics": topics,
                "pushed_at": pushed_at,
                "is_fork": is_fork,
            })
        return repos

    def _next_page(self, html: str) -> str | None:
        """Return the href of the next repositories page, if any."""
        m = re.search(r'rel="next"[^>]*href="([^"]*)"', html)
        if not m:
            m = re.search(r'aria-label="Next Page"[^>]*href="([^"]*)"', html)
        if not m:
            return None
        return m.group(1).replace("&amp;", "&")

    def _readme_quality(self, repo_html: str) -> tuple[bool, float]:
        """README presence + quality 0..1 from a server-rendered repo page."""
        m = re.search(r'<article[^>]*class="markdown-body[^"]*"[^>]*>(.*?)</article>', repo_html, re.DOTALL)
        if not m:
            return False, 0.0
        text = _strip_tags(m.group(1)).lower()
        if not text:
            return False, 0.0
        checks = {
            "length": len(text) > 400,
            "overview": bool(text.strip()),
            "sections": sum(
                1 for s in ("##", "###", "getting started", "usage", "install", "license", "contributing", "api", "setup")
                if s in text
            ) >= 2,
            "code_blocks": "```" in text or "npm install" in text or "pip install" in text,
            "badges": "![image]" in text or "img.shields.io" in text,
            "links": "http" in text,
        }
        return True, sum(checks.values()) / len(checks)

    # ------------------------------------------------------------------ #
    # Live collection
    # ------------------------------------------------------------------ #

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        handle = extract_username(handle)
        cached = _cache_get(handle)
        if cached is not None:
            return cached

        profile_html = self._get_html(self._profile_url(handle)).text
        profile = self._parse_profile(profile_html, handle)

        # Paginated repository listing
        repos_raw: list[dict] = []
        page = 1
        next_path: str | None = None
        while len(repos_raw) < MAX_REPOS and page <= MAX_PAGES:
            url = f"{BASE}{next_path}" if next_path else self._repos_url(handle, page)
            resp = self._get_html(url)
            chunk = self._parse_repo_list(resp.text)
            repos_raw.extend(chunk)
            next_path = self._next_page(resp.text)
            if not next_path or not chunk:
                break
            page += 1

        # Keep public, non-fork repos (consistent with the old API behavior)
        own_repos = [r for r in repos_raw if not r["is_fork"]]

        # Light per-repo enrichment: README presence/quality for top-N repos
        repo_detail: list[dict] = []
        language_count: dict[str, int] = {}
        total_stars = 0
        total_forks = 0
        repos_with_readme = 0
        readme_sum = 0.0

        from ...ai.skills_kb import SKILLS

        lang_boost = {
            "Python": {"Python"},
            "Java": {"Java"},
            "JavaScript": {"JavaScript", "Node.js"},
            "TypeScript": {"TypeScript", "React", "Next.js", "Redux"},
            "Go": {"Go"},
            "C++": {"C++"},
            "C": {"C"},
            "Ruby": {"Ruby"},
            "PHP": {"PHP"},
            "Rust": {"Rust"},
        }

        for i, r in enumerate(own_repos[:MAX_REPOS]):
            is_highlight = i < README_REPO_LIMIT

            # README from the repo page (best-effort)
            readme_ok, readme_q = False, 0.0
            languages: dict[str, float] = {}
            if is_highlight and r.get("language"):
                try:
                    repo_html = self._get_html(self._repo_url(r["full_name"])).text
                    readme_ok, readme_q = self._readme_quality(repo_html)
                    languages = {r["language"]: 1.0}
                except ProfileCollectError:
                    pass

            if readme_ok:
                repos_with_readme += 1
                readme_sum += readme_q
            if r.get("language"):
                language_count[r["language"]] = language_count.get(r["language"], 0) + 1
            stars = int(r.get("stars") or 0)
            forks = int(r.get("forks") or 0)
            total_stars += stars
            total_forks += forks

            # Tech evidence: primary language + topics + description match
            tech_hits: dict[str, float] = {}
            for tech in lang_boost.get(r.get("language") or "", ()):
                tech_hits[tech] = max(tech_hits.get(tech, 0.0), 0.35)
            desc = (r.get("description") or "").lower()
            for sd in SKILLS:
                if sd.name in tech_hits:
                    continue
                if any(p.lower() in desc for p in sd.resume_patterns):
                    tech_hits[sd.name] = max(tech_hits.get(sd.name, 0.0), 0.25)
                elif any(t.lower() in (" " + sd.name.lower()) or (sd.name.lower() in (t or "").lower()) for t in r.get("topics", [])):
                    tech_hits[sd.name] = max(tech_hits.get(sd.name, 0.0), 0.25)

            repo_detail.append({
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "homepage": None,
                "stars": stars,
                "forks": forks,
                "watchers": 0,
                "open_issues": 0,
                "language": r.get("language"),
                "languages": languages,
                "license_name": None,
                "topics": r.get("topics", []) or [],
                "created_at": None,
                "pushed_at": r.get("pushed_at"),
                "has_readme": readme_ok,
                "readme_quality": round(readme_q, 2),
                "has_ci": False,
                "has_dockerfile": False,
                "commits_count": 0,
                "contributors_count": 0,
                "open_prs": 0,
                "is_fork": False,
                "tech_hits": tech_hits,
            })

        total_lang = sum(language_count.values()) or 1
        language_usage = {
            lang: round(count / total_lang, 3)
            for lang, count in sorted(language_count.items(), key=lambda kv: -kv[1])
        }

        repo_count = len(repo_detail)
        return {
            "_source": "github-html",
            "username": profile.get("login") or handle,
            "name": profile.get("name"),
            "avatar_url": profile.get("avatar_url"),
            "public_repos": profile.get("public_repos", repo_count),
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "bio": profile.get("bio"),
            "location": profile.get("location"),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits_fetched": profile.get("total_contributions", 0),
            "repos_with_ci": 0,
            "repos_with_docker": 0,
            "repos_with_readme": repos_with_readme,
            "avg_readme_quality": round(readme_sum / repo_count, 2) if repo_count else 0.0,
            "language_usage": language_usage,
            "repos": repo_detail,
            "_rate_limit_hint": "GitHub HTML scraper (no token, no REST quota). "
            "Per-repo commits/contributors/CI/Dockerfile/file-trees are not exposed "
            "on the public pages; README quality covers the top few repos. "
            "Results cached for 1 hour.",
        }

    # ------------------------------------------------------------------ #
    # Offline simulation (demo candidate)
    # ------------------------------------------------------------------ #

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        """Simulated GitHub profile with the exact shape the real scraper returns."""
        skills = resume.all_skill_names() if resume else []
        projects = [p for p in ((resume.projects or []) if resume else []) if p.name][:3]

        def tech_hits_for(repo_skills: list[str], strength: float = 0.9) -> dict[str, float]:
            return {s: round(min(1.0, strength), 2) for s in repo_skills}

        def slug(name: str) -> str:
            return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

        repos: list[dict] = []
        n = rng.randint(4, 9)
        used_names = set()
        aligned = 0
        for p in projects:
            base = slug(p.name) or f"project-{aligned + 1}"
            used_names.add(base)
            stars = rng.randint(0, 60)
            forks = rng.randint(0, 12)
            lang = (p.tech_stack[0] if p.tech_stack else "Python").split()[0]
            repo_skills = p.tech_stack or skills[:3]
            repos.append({
                "name": base,
                "full_name": f"demo/{base}",
                "description": (p.description or p.name)[:120],
                "html_url": f"https://github.com/demo/{base}",
                "homepage": f"https://{base}.vercel.app" if rng.random() < 0.6 else None,
                "stars": stars,
                "forks": forks,
                "watchers": rng.randint(0, 5),
                "open_issues": rng.randint(0, 8),
                "language": lang,
                "languages": {lang: rng.randint(20000, 90000)},
                "license_name": rng.choice(["MIT", "Apache-2.0", "MIT", "GPL-3.0", None]),
                "topics": [s.lower().replace(" ", "-") for s in skills[:3]],
                "created_at": f"2024-{rng.randint(1, 12):02d}-01T10:00:00Z",
                "pushed_at": f"2026-0{rng.randint(1, 8):02d}-15T10:00:00Z",
                "has_readme": True,
                "readme_quality": round(rng.uniform(0.5, 0.95), 2),
                "has_ci": rng.random() < 0.7,
                "has_dockerfile": rng.random() < 0.5,
                "commits_count": rng.randint(20, 220),
                "contributors_count": rng.randint(1, 4),
                "open_prs": rng.randint(0, 5),
                "is_fork": False,
                "tech_hits": tech_hits_for(repo_skills),
            })
            aligned += 1
        filler = ["portfolio-site", "algo-solutions", "notes-api", "devops-lab", "cli-utils", "ml-experiments", "system-design"]
        for i in range(n - aligned):
            name = filler[i % len(filler)]
            if name in used_names:
                continue
            used_names.add(name)
            repos.append({
                "name": name,
                "full_name": f"demo/{name}",
                "description": rng.choice(["A personal project", "Learning repo", "Side experiment", None]),
                "html_url": f"https://github.com/demo/{name}",
                "homepage": f"https://{name}.netlify.app" if rng.random() < 0.4 else None,
                "stars": rng.randint(0, 40),
                "forks": rng.randint(0, 8),
                "watchers": rng.randint(0, 4),
                "open_issues": rng.randint(0, 10),
                "language": rng.choice(["Python", "TypeScript", "Java", "Go", "JavaScript", "C++"]),
                "languages": {},
                "license_name": rng.choice(["MIT", "MIT", "Apache-2.0", None, None]),
                "topics": [],
                "created_at": f"2023-{rng.randint(1, 12):02d}-01T10:00:00Z",
                "pushed_at": f"2026-0{rng.randint(1, 8):02d}-10T10:00:00Z",
                "has_readme": rng.random() < 0.8,
                "readme_quality": round(rng.uniform(0.2, 0.9), 2),
                "has_ci": rng.random() < 0.5,
                "has_dockerfile": rng.random() < 0.35,
                "commits_count": rng.randint(10, 150),
                "contributors_count": rng.randint(1, 3),
                "open_prs": rng.randint(0, 4),
                "is_fork": False,
                "tech_hits": tech_hits_for(skills[:2], strength=0.75) if rng.random() < 0.7 else {},
            })
        total_stars = sum(r["stars"] for r in repos)
        total_forks = sum(r["forks"] for r in repos)
        return {
            "_source": "mock",
            "username": handle,
            "avatar_url": f"https://ui-avatars.com/api/?name={handle[:2].upper()}&background=6d5efc&color=fff",
            "public_repos": len(repos),
            "followers": rng.randint(5, 90),
            "following": rng.randint(20, 200),
            "account_created_at": f"20{rng.randint(15, 19)}-06-15T00:00:00Z",
            "bio": "Software developer building things",
            "location": None,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits_fetched": sum(r["commits_count"] for r in repos),
            "repos_with_ci": sum(1 for r in repos if r["has_ci"]),
            "repos_with_docker": sum(1 for r in repos if r["has_dockerfile"]),
            "repos_with_readme": sum(1 for r in repos if r["has_readme"]),
            "avg_readme_quality": round(sum(r["readme_quality"] for r in repos) / max(len(repos), 1), 2),
            "language_usage": {"Python": 0.3, "TypeScript": 0.4, "Java": 0.3},
            "repos": repos,
            "_rate_limit_hint": "Demo data — simulated GitHub profile.",
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def validate(self, handle: str) -> tuple[bool, str]:
        """Cheap existence check used by the connect UI."""
        try:
            html = self._get_html(self._profile_url(extract_username(handle))).text
            return _parse_profile_exists(html), "ok"
        except ProfileCollectError as e:
            return False, str(e)


def _parse_profile_exists(html: str) -> bool:
    return bool(html and ('class="vcard-details"' in html or 'class="vcard-names"' in html))


def is_github_rate_limited() -> bool:
    """No longer applicable — the HTML scraper has no token rate limit."""
    return False