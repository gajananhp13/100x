"""HackerRank integration — live public REST API scraper plus offline simulation.

Fetches profile, badges (with per-badge star ratings / levels), practice scores,
contest participation, and submission history via HackerRank's public REST API
(https://www.hackerrank.com/rest/...). No auth required; requests use realistic
browser headers.

Results are cached in-memory for 1 hour to avoid hammering the API.

Badge stars and levels are scraped directly — each badge includes its `stars`
(1–3+) and `level` (tier) so the candidate's skill depth per domain is visible.
"""

from __future__ import annotations

import random
import re
import time
from datetime import datetime, timezone

import httpx

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("hackerrank", "HackerRank", "hr", "https://hackerrank.com/{handle}", "username", True)

# ---------------------------------------------------------------------- #
# HackerRank public REST endpoints
# ---------------------------------------------------------------------- #

PROFILE_URL = "https://www.hackerrank.com/rest/contests/master/hackers/{username}/profile"
BADGES_URL = "https://www.hackerrank.com/rest/hackers/{username}/badges"
SCORES_URL = "https://www.hackerrank.com/rest/hackers/{username}/scores_elo"
CONTESTS_URL = "https://www.hackerrank.com/rest/hackers/{username}/contest_participation"
SUBMISSIONS_URL = "https://www.hackerrank.com/rest/hackers/{username}/submission_histories"
RECENT_CHALLENGES_URL = "https://www.hackerrank.com/rest/hackers/{username}/recent_challenges"

CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": USER_AGENT,
}


# ---------------------------------------------------------------------- #
# Username parsing
# ---------------------------------------------------------------------- #

def extract_username(input_value: str) -> str:
    """Extract a clean username from a handle, @handle, or profile URL.

    Accepts inputs like:
      - "gajananpatangepg"
      - "@gajananpatangepg"
      - "https://www.hackerrank.com/gajananpatangepg"
      - "https://hackerrank.com/gajananpatangepg"
    """
    trimmed = input_value.strip()
    url_match = re.search(r"hackerrank\.com/([^/?#]+)", trimmed)
    if url_match:
        return url_match.group(1)
    clean = trimmed.lstrip("@").rstrip("/")
    if clean and all(c.isalnum() or c in "_-" for c in clean):
        return clean
    raise ProfileCollectError(f'Invalid HackerRank username or URL: "{input_value}"')


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


def clear_hackerrank_cache() -> None:
    """Clear the in-memory cache (used by tests)."""
    _memory_store.clear()


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #

def _safe_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if value in (None, "", "N/A"):
        return default
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    if value in (None, "", "N/A"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _badge_icon(icon: object) -> str:
    """Resolve badge icon URL from various possible shapes."""
    if isinstance(icon, dict):
        icon = icon.get("small") or icon.get("medium") or icon.get("large") or icon.get("url")
    if isinstance(icon, str) and icon.strip():
        url = icon.strip()
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith("/"):
            return f"https://www.hackerrank.com{url}"
        return url
    return ""


def _total_practice_score(scores: list[dict]) -> int:
    total = 0.0
    for track in scores:
        practice = track.get("practice") or {}
        score = practice.get("score")
        if isinstance(score, (int, float)):
            total += max(0.0, score)
    return int(round(total))


def _best_rank(scores: list[dict]) -> int:
    ranks = []
    for track in scores:
        practice = track.get("practice") or {}
        rank = _safe_int(practice.get("rank"))
        score = _safe_float(practice.get("score"))
        if rank > 0 and score > 0:
            ranks.append(rank)
    return min(ranks) if ranks else 0


def _to_timestamp(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())
    except ValueError:
        pass
    return 0


# ---------------------------------------------------------------------- #
# Integration
# ---------------------------------------------------------------------- #

class HackerRankIntegration(SimulatedPlatformMixin):
    platform_id = "hackerrank"
    platform_label = "HackerRank"
    real_api = True

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        simulate: bool = False,
    ) -> None:
        super().__init__(simulate=simulate)
        self._transport = transport

    def _get(self, client: httpx.Client, url: str, params: dict | None = None) -> httpx.Response:
        return client.get(url, headers=HEADERS, params=params)

    # ------------------------------------------------------------------ #
    # Live collection
    # ------------------------------------------------------------------ #

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        username = extract_username(handle)
        cached = _cache_get(username)
        if cached is not None:
            return cached

        profile_data: dict | None = None
        badges_data: dict = {"models": [], "version": 0}
        scores_data: list[dict] = []
        contests_data: dict = {"models": [], "total": 0}
        submission_history: dict[str, int] = {}
        recent_challenges: dict = {"models": [], "cursor": None, "last_page": True}

        try:
            with httpx.Client(timeout=20, transport=self._transport) as client:
                # Profile (required)
                try:
                    res = self._get(client, PROFILE_URL.format(username=username))
                    if res.status_code == 200:
                        body = res.json()
                        profile_data = body.get("model") if isinstance(body, dict) else None
                except Exception:
                    pass

                if not profile_data:
                    raise ProfileCollectError(f'HackerRank user "{username}" not found.')

                # Badges (required for star ratings)
                try:
                    res = self._get(client, BADGES_URL.format(username=username))
                    if res.status_code == 200:
                        body = res.json()
                        if isinstance(body, dict):
                            badges_data = body
                except Exception:
                    pass

                # Practice scores
                try:
                    res = self._get(client, SCORES_URL.format(username=username))
                    if res.status_code == 200:
                        body = res.json()
                        if isinstance(body, list):
                            scores_data = body
                except Exception:
                    pass

                # Contest participation
                try:
                    res = self._get(
                        client,
                        CONTESTS_URL.format(username=username),
                        params={"offset": 0, "limit": 50},
                    )
                    if res.status_code == 200:
                        body = res.json()
                        if isinstance(body, dict):
                            contests_data = body
                except Exception:
                    pass

                # Submission history
                try:
                    res = self._get(client, SUBMISSIONS_URL.format(username=username))
                    if res.status_code == 200:
                        body = res.json()
                        if isinstance(body, dict):
                            submission_history = _parse_submission_history(body)
                except Exception:
                    pass

                # Recent challenges
                try:
                    res = self._get(
                        client,
                        RECENT_CHALLENGES_URL.format(username=username),
                        params={"limit": 100, "response_version": "v2"},
                    )
                    if res.status_code == 200:
                        body = res.json()
                        if isinstance(body, dict):
                            recent_challenges = body
                except Exception:
                    pass

        except ProfileCollectError:
            raise
        except httpx.HTTPError as e:
            raise ProfileCollectError(f"Could not reach HackerRank API: {e}") from e

        # ------------------------------------------------------------------ #
        # Decode badges with star ratings
        # ------------------------------------------------------------------ #

        badges_raw = badges_data.get("models", []) if isinstance(badges_data, dict) else []
        badges: list[dict] = []
        max_stars = 0
        for b in badges_raw:
            if not isinstance(b, dict):
                continue
            name = str(
                b.get("badge_name")
                or b.get("display_name")
                or b.get("name")
                or "Badge"
            )
            stars = _safe_int(b.get("stars"), 0)
            level = _safe_int(b.get("level"), 0)
            icon_url = _badge_icon(b.get("icon") or b.get("badge_icon") or b.get("badge_image") or b.get("image") or b.get("url"))
            solved = _safe_int(b.get("solved"), 0)
            badges.append({
                "name": name,
                "stars": stars,
                "level": level,
                "icon": icon_url,
                "solved": solved,
            })
            if stars > max_stars:
                max_stars = stars

        total_badges = len(badges)
        total_solved_from_badges = sum(b.get("solved", 0) for b in badges)

        # ------------------------------------------------------------------ #
        # Decode practice stats
        # ------------------------------------------------------------------ #

        total_practice = _total_practice_score(scores_data)
        best_rank = _best_rank(scores_data)
        active_tracks = [
            t for t in scores_data
            if _safe_float((t.get("practice") or {}).get("score")) > 0
        ]
        track_names = [str(t.get("name", "")) for t in active_tracks if t.get("name")]

        # ------------------------------------------------------------------ #
        # Decode contests
        # ------------------------------------------------------------------ #

        contest_models = contests_data.get("models", []) if isinstance(contests_data, dict) else []
        contest_count = len(contest_models)
        contest_rating = 0
        if contest_models:
            last = contest_models[-1] if isinstance(contest_models[-1], dict) else {}
            contest_rating = _safe_int(last.get("rating") or last.get("elo") or last.get("score"))

        # ------------------------------------------------------------------ #
        # Decode recent challenges (solved count fallback)
        # ------------------------------------------------------------------ #

        challenge_models = recent_challenges.get("models", []) if isinstance(recent_challenges, dict) else []
        solved_from_challenges = len({
            str(c.get("ch_slug") or c.get("slug") or c.get("name", ""))
            for c in challenge_models
            if isinstance(c, dict)
        })

        total_solved = total_solved_from_badges or solved_from_challenges
        total_submissions = sum(submission_history.values())

        # ------------------------------------------------------------------ #
        # Profile-level stars: use badge max_stars or compute from level
        # ------------------------------------------------------------------ #

        profile_level = _safe_int(profile_data.get("level"), 0)
        # If we got star data from badges, use it; otherwise derive from level
        overall_stars = max_stars if max_stars > 0 else min(5, max(1, profile_level // 2))

        # ------------------------------------------------------------------ #
        # Build final data dict
        # ------------------------------------------------------------------ #

        result = {
            "_source": "hackerrank-api",
            "username": profile_data.get("username") or username,
            "name": profile_data.get("name") or "",
            "avatar": profile_data.get("avatar") or "",
            "country": profile_data.get("country") or "",
            "level": profile_level,
            "stars": overall_stars,
            "badges": badges,
            "total_badges": total_badges,
            "problems_solved": total_solved,
            "total_submissions": total_submissions,
            "practice_score": total_practice,
            "ranking": best_rank,
            "active_tracks": track_names,
            "contest_count": contest_count,
            "contest_rating": contest_rating,
            "submission_calendar": submission_history,
            "recent_challenges": [
                {
                    "name": c.get("name") or c.get("challenge_name") or c.get("slug", ""),
                    "slug": c.get("ch_slug") or c.get("slug", ""),
                    "status": c.get("status", "Listed"),
                    "timestamp": _to_timestamp(
                        c.get("solved_at") or c.get("created_at") or c.get("timestamp")
                    ),
                }
                for c in challenge_models
                if isinstance(c, dict)
            ],
            "_rate_limit_hint": "HackerRank public REST API (no auth). Results cached for 1 hour.",
        }

        _cache_set(username, result)
        return result

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
        stars = min(5, int(1 + level * 5))
        badge_count = rng.randint(2, 12)

        # Generate simulated badges with star ratings
        badge_templates = [
            ("C++", "CPP"), ("Java", "JAVA"), ("Python", "PY"), ("JavaScript", "JS"),
            ("Problem Solving", "PS"), ("Algorithms", "AL"), ("Data Structures", "DS"),
            ("SQL", "SQL"), ("Regex", "REGEX"), ("Mathematics", "MATH"),
            ("AI", "AI"), ("Pull Requests", "PR"), ("README", "README"),
        ]
        badges = []
        for _ in range(badge_count):
            tpl = rng.choice(badge_templates)
            badge_stars = rng.randint(1, min(3, stars))
            badges.append({
                "name": tpl[0],
                "stars": badge_stars,
                "level": badge_stars,
                "icon": "",
                "solved": rng.randint(1, 50),
            })

        return {
            "_source": "mock",
            "_warning": "Simulated demo data — connect the real platform API for production evidence.",
            "username": handle,
            "name": f"Demo User ({handle})",
            "level": int(stars * 2),
            "stars": stars,
            "badges": badges,
            "total_badges": badge_count,
            "problems_solved": int(60 + level * 260),
            "total_submissions": int(100 + level * 400),
            "practice_score": int(200 + level * 800),
            "ranking": rng.randint(500, 50000),
            "active_tracks": rng.sample(["C++", "Java", "Python", "Algorithms", "Data Structures"], k=rng.randint(1, 3)),
            "contest_count": rng.randint(0, 5),
            "contest_rating": rng.randint(0, 1800),
            "submission_calendar": {},
            "recent_challenges": [],
        }


# ---------------------------------------------------------------------- #
# Submission history parser
# ---------------------------------------------------------------------- #

def _parse_submission_history(raw_history: dict) -> dict[str, int]:
    """Parse submission history keys (epoch seconds or ISO dates) to date→count."""
    from datetime import date, timedelta

    history: dict[str, int] = {}
    for key, count in raw_history.items():
        text = str(key).strip()
        if not text:
            continue
        resolved_date = None
        if text.isdigit():
            try:
                resolved_date = datetime.fromtimestamp(int(text), tz=timezone.utc).date()
            except (ValueError, OverflowError, OSError):
                continue
        else:
            try:
                resolved_date = date.fromisoformat(text)
            except ValueError:
                continue
        if resolved_date:
            history[str(key)] = _safe_int(count)
    return history
