"""LeetCode integration — live public GraphQL scraper plus offline simulation.

Fetches profile, submission stats (with easy/medium/hard breakdown), skill
sections (fundamental / intermediate / advanced with per-topic solved counts),
activity streak, badges, contest rating and recent submissions via LeetCode's
public GraphQL API (https://leetcode.com/graphql). No auth required; requests
use realistic browser headers. Contest rating, recent submissions, skill
sections and calendar are best-effort: if those queries fail, the core
profile is still returned.

Results are cached in-memory for 1 hour to avoid hammering the API.
"""

from __future__ import annotations

import random
import re
import time

import httpx

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("leetcode", "LeetCode", "lc", "https://leetcode.com/u/{handle}/", "username", True)

API = "https://leetcode.com/graphql"
CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

COMMON_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
    "Origin": "https://leetcode.com",
    "Referer": "https://leetcode.com/",
}

MATCHED_USER_QUERY = """
query matchedUser($username: String!) {
  matchedUser(username: $username) {
    username
    profile { realName ranking }
    submitStats {
      acSubmissionNum { difficulty count }
      totalSubmissionNum { difficulty count }
    }
    badges { id displayName icon }
  }
  allQuestionsCount { difficulty count }
}
"""

CONTEST_RANKING_QUERY = """
query contestRanking($username: String!) {
  userContestRanking(username: $username) { rating }
}
"""

RECENT_SUBMISSIONS_QUERY = """
query recentSubmissions($username: String!) {
  recentSubmissionList(username: $username, limit: 10) {
    title
    statusDisplay
    timestamp
  }
}
"""

SKILL_STATS_QUERY = """
query skillStats($username: String!) {
  matchedUser(username: $username) {
    tagProblemCounts {
      advanced { tagName tagSlug problemsSolved }
      intermediate { tagName tagSlug problemsSolved }
      fundamental { tagName tagSlug problemsSolved }
    }
  }
}
"""

USER_CALENDAR_QUERY = """
query userProfileCalendar($username: String!) {
  matchedUser(username: $username) {
    userCalendar {
      streak
      totalActiveDays
    }
  }
}
"""

MAX_TOPICS_PER_SECTION = 20


# ---------------------------------------------------------------------- #
# Username parsing
# ---------------------------------------------------------------------- #

def extract_username(input_value: str) -> str:
    """Extract a clean username from a handle, @handle, or profile URL.

    Accepts inputs like:
      - "john_doe"
      - "@john_doe"
      - "https://leetcode.com/u/john_doe/"
      - "https://leetcode.com/john_doe"
    """
    trimmed = input_value.strip()
    url_match = re.search(r"leetcode\.com/u/([^/?#]+)", trimmed)
    if url_match:
        return url_match.group(1)
    clean = trimmed.lstrip("@").rstrip("/")
    if clean and all(c.isalnum() or c in "_-" for c in clean):
        return clean
    raise ProfileCollectError(f'Invalid LeetCode username or URL: "{input_value}"')


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


def clear_leetcode_cache() -> None:
    """Clear the in-memory cache (used by tests)."""
    _memory_store.clear()


def _by_difficulty(items: list[dict] | None) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items or []:
        difficulty = (item.get("difficulty") or "All").title()
        out[difficulty] = int(item.get("count", 0) or 0)
    return out


def _parse_skill_section(items: list[dict] | None) -> dict:
    topics = []
    for item in items or []:
        name = item.get("tagName")
        if not name:
            continue
        topics.append(
            {
                "name": name,
                "slug": item.get("tagSlug") or "",
                "solved": int(item.get("problemsSolved", 0) or 0),
            }
        )
    topics.sort(key=lambda t: t["solved"], reverse=True)
    return {
        "total": sum(t["solved"] for t in topics),
        "topics": topics[:MAX_TOPICS_PER_SECTION],
    }


# ---------------------------------------------------------------------- #
# Integration
# ---------------------------------------------------------------------- #

class LeetCodeIntegration(SimulatedPlatformMixin):
    platform_id = "leetcode"
    platform_label = "LeetCode"
    real_api = True

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        simulate: bool = False,
    ) -> None:
        super().__init__(simulate=simulate)
        self._transport = transport

    def _post(self, client: httpx.Client, query: str, username: str) -> httpx.Response:
        return client.post(
            API,
            headers=COMMON_HEADERS,
            json={"query": query, "variables": {"username": username}},
        )

    # ------------------------------------------------------------------ #
    # Live collection
    # ------------------------------------------------------------------ #

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        username = extract_username(handle)
        cached = _cache_get(username)
        if cached is not None:
            return cached

        try:
            with httpx.Client(timeout=20, transport=self._transport) as client:
                # Core query is required; optional queries fail gracefully
                matched_res = self._post(client, MATCHED_USER_QUERY, username)
                try:
                    contest_res = self._post(client, CONTEST_RANKING_QUERY, username)
                except Exception:
                    contest_res = None
                try:
                    recent_res = self._post(client, RECENT_SUBMISSIONS_QUERY, username)
                except Exception:
                    recent_res = None
                try:
                    skills_res = self._post(client, SKILL_STATS_QUERY, username)
                except Exception:
                    skills_res = None
                try:
                    calendar_res = self._post(client, USER_CALENDAR_QUERY, username)
                except Exception:
                    calendar_res = None
        except httpx.HTTPError as e:
            raise ProfileCollectError(f"Could not reach LeetCode API: {e}") from e

        if matched_res.status_code != 200:
            text = matched_res.text[:200]
            raise ProfileCollectError(
                f"LeetCode API returned status {matched_res.status_code}"
                f"{': ' + text if text else ''}"
            )

        try:
            matched_data = matched_res.json()
        except ValueError as e:
            raise ProfileCollectError("LeetCode API returned an invalid response.") from e

        if matched_data.get("errors"):
            raise ProfileCollectError(matched_data["errors"][0]["message"])

        user = (matched_data.get("data") or {}).get("matchedUser")
        if not user:
            raise ProfileCollectError(f'User "{username}" not found')

        # Core stats -------------------------------------------------- #
        submit_stats = user.get("submitStats") or {}
        ac_map = _by_difficulty(submit_stats.get("acSubmissionNum"))
        total_map = _by_difficulty(submit_stats.get("totalSubmissionNum"))
        total_solved = ac_map.get("All", 0)
        total_attempts = total_map.get("All", 0)
        acceptance_rate = round(total_solved / total_attempts * 100) if total_attempts else 0

        all_counts = (matched_data.get("data") or {}).get("allQuestionsCount") or []
        total_questions = max((int(c.get("count", 0) or 0) for c in all_counts), default=0)

        badges: list[dict] = []
        for b in user.get("badges") or []:
            icon = b.get("icon") or ""
            if icon.startswith("/"):
                icon = f"https://leetcode.com{icon}"
            badges.append({"name": b.get("displayName") or b.get("name") or "", "icon": icon})

        # Contest rating (optional) ----------------------------------- #
        contest_rating: int | None = None
        if contest_res is not None:
            try:
                rating = ((contest_res.json().get("data") or {}).get("userContestRanking") or {}).get("rating")
                if rating:
                    contest_rating = int(rating)
            except Exception:
                pass

        # Recent submissions (optional) -------------------------------- #
        recent_submissions: list[dict] = []
        if recent_res is not None:
            try:
                for s in (recent_res.json().get("data") or {}).get("recentSubmissionList") or []:
                    title = s.get("title")
                    if not title:
                        continue
                    recent_submissions.append({
                        "title": title,
                        "status": s.get("statusDisplay") or "",
                        "timestamp": int(s.get("timestamp") or 0),
                    })
            except Exception:
                pass

        # Skill sections (optional) ------------------------------------ #
        skills: dict[str, dict] = {"fundamental": {}, "intermediate": {}, "advanced": {}}
        if skills_res is not None:
            try:
                counts = ((skills_res.json().get("data") or {}).get("matchedUser") or {}).get(
                    "tagProblemCounts"
                ) or {}
                for section in ("fundamental", "intermediate", "advanced"):
                    section_data = _parse_skill_section(counts.get(section))
                    if section_data["total"] > 0:
                        skills[section] = section_data
            except Exception:
                pass

        # Activity calendar (optional) --------------------------------- #
        streak_days = 0
        total_active_days: int | None = None
        if calendar_res is not None:
            try:
                calendar = ((calendar_res.json().get("data") or {}).get("matchedUser") or {}).get(
                    "userCalendar"
                ) or {}
                streak_days = int(calendar.get("streak", 0) or 0)
                if calendar.get("totalActiveDays"):
                    total_active_days = int(calendar["totalActiveDays"])
            except Exception:
                pass

        profile_data = {
            "_source": "leetcode-api",
            "username": user.get("username") or username,
            "name": (user.get("profile") or {}).get("realName"),
            "ranking": (user.get("profile") or {}).get("ranking") or 0,
            "total_solved": total_solved,
            "easy": ac_map.get("Easy", 0),
            "medium": ac_map.get("Medium", 0),
            "hard": ac_map.get("Hard", 0),
            "total_questions": total_questions,
            "acceptance_rate": acceptance_rate,
            "contest_rating": contest_rating or 0,
            "streak_days": streak_days,
            "total_active_days": total_active_days,
            "badges": badges,
            "skills": skills,
            "recent_submissions": recent_submissions,
            "_rate_limit_hint": "LeetCode public GraphQL API (no auth). Results cached for 1 hour.",
        }
        _cache_set(username, profile_data)
        return profile_data

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
        total = int(50 + level * 350 + (0.8 if resume and any(a.type == "coding" for a in resume.achievements) else 0.2) * rng.randint(0, 120))
        easy = int(total * rng.uniform(0.38, 0.48))
        medium = int(total * rng.uniform(0.36, 0.46))
        hard = max(0, total - easy - medium)

        def skill_section(solved: int, names: list[str]) -> dict:
            topics = []
            remaining = solved
            for name in names:
                count = rng.randint(0, max(int(solved * 0.35), 1)) if remaining > 0 else 0
                count = min(count, remaining)
                if count:
                    topics.append({"name": name, "slug": name.lower().replace(" ", "-"), "solved": count})
                    remaining -= count
            topics.sort(key=lambda t: t["solved"], reverse=True)
            return {"total": solved, "topics": topics}

        return {
            "total_solved": total,
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "contest_rating": int(rng.randint(1450, 2100) + level * 150),
            "contest_rank": rng.randint(500, 60000),
            "streak_days": rng.randint(0, 120),
            "total_active_days": rng.randint(100, 800),
            "badges": rng.randint(0, 6),
            "skills": {
                "fundamental": skill_section(
                    int(total * 0.6),
                    ["Array", "Hash Table", "String", "Two Pointers", "Sorting", "Greedy", "Math"],
                ),
                "intermediate": skill_section(
                    int(total * 0.3),
                    ["Dynamic Programming", "Binary Search", "Tree", "Graph", "Sliding Window", "Stack"],
                ),
                "advanced": skill_section(
                    int(total * 0.1),
                    ["Hard Dynamic Programming", "Segment Tree", "Trie", "Network Flow"],
                ),
            },
        }
