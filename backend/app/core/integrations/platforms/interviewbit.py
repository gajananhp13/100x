"""InterviewBit integration — live public REST API scraper plus offline simulation.

Fetches profile, global/university rank, strength areas (topic-wise solved counts),
difficulty breakdown, streak/score and submission analysis via InterviewBit's
public REST endpoints (https://www.interviewbit.com/v2/... and /api/v3/...).
No auth required; requests use realistic browser headers. All 6 data sources
are fetched in sequence via httpx; if any optional source fails the core
profile is still returned. Results are cached in-memory for 1 hour.

Endpoints used (all public, no login required):
  - GET /v2/profile/username?id={username}            -> global_rank, university_rank, name, university
  - GET /v2/problem_list/problems_solved_overview_count?username={username}
                                                      -> total_problems_solved, topic/course breakdown (strength areas), difficulty
  - GET /v2/profile/username/streak/?id={username}    -> current_streak, streak_score, coins, total score
  - GET /v2/profile/username/submission-analysis/?id={username}
                                                      -> correct/wrong/compilation counts
  - GET /api/v3/badges/user-progress/?username={username}
                                                      -> badges progress (optional)
  - GET /v2/profile/username/courses-progress/?id={username}
                                                      -> completed topics (optional)
"""

from __future__ import annotations

import random
import re
import time

import httpx

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef(
    "interviewbit",
    "InterviewBit",
    "ib",
    "https://www.interviewbit.com/profile/{handle}/",
    "username",
    True,
)

CACHE_TTL_MS = 60 * 60 * 1000  # 1 hour

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

COMMON_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": USER_AGENT,
    "Referer": "https://www.interviewbit.com/",
}

# ---------------------------------------------------------------------- #
# Username parsing
# ---------------------------------------------------------------------- #


def extract_username(input_value: str) -> str:
    """Extract a clean username from a handle or profile URL."""
    trimmed = input_value.strip()
    url_match = re.search(r"interviewbit\.com/profile/([^/?#]+)", trimmed)
    if url_match:
        return url_match.group(1).rstrip("/")
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


# ---------------------------------------------------------------------- #
# Integration
# ---------------------------------------------------------------------- #


class InterviewBitIntegration(SimulatedPlatformMixin):
    platform_id = "interviewbit"
    platform_label = "InterviewBit"
    real_api = True

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        simulate: bool = False,
    ) -> None:
        super().__init__(simulate=simulate)
        self._transport = transport

    def _get(self, client: httpx.Client, url: str, params: dict | None = None) -> httpx.Response:
        return client.get(url, headers=COMMON_HEADERS, params=params)

    # ------------------------------------------------------------------ #
    # Live collection
    # ------------------------------------------------------------------ #

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        username = extract_username(handle)
        cached = _cache_get(username)
        if cached is not None:
            return cached

        profile_data: dict | None = None
        solved_data: dict | None = None
        streak_data: dict | None = None
        submission_data: list[dict] | None = None
        badges_data: list[dict] | None = None

        try:
            with httpx.Client(timeout=20, transport=self._transport, follow_redirects=True) as client:
                # 1) Core profile — required (global_rank, university_rank)
                try:
                    res = self._get(client, "https://www.interviewbit.com/v2/profile/username", params={"id": username})
                except httpx.HTTPError as e:
                    raise ProfileCollectError(f"Could not reach InterviewBit API: {e}") from e

                if res.status_code == 403:
                    raise ProfileCollectError(f'InterviewBit profile "{username}" not found.')
                if res.status_code == 404:
                    raise ProfileCollectError(f'InterviewBit profile "{username}" not found.')
                if res.status_code != 200:
                    raise ProfileCollectError(
                        f"InterviewBit API returned status {res.status_code} for profile '{username}'"
                    )
                try:
                    body = res.json()
                except ValueError as e:
                    raise ProfileCollectError("InterviewBit API returned an invalid response.") from e

                # InterviewBit returns {"global_rank": ..., "university_rank": ...} or empty on not found
                if not isinstance(body, dict) or "username" not in body:
                    # Some error payloads are {"error": ...} or missing username
                    if isinstance(body, dict) and body.get("error"):
                        raise ProfileCollectError(f'InterviewBit profile "{username}" not found.')
                    raise ProfileCollectError(f'InterviewBit profile "{username}" not found.')
                profile_data = body

                # 2) Strength areas / solved overview — optional but valuable
                try:
                    res2 = self._get(
                        client,
                        "https://www.interviewbit.com/v2/problem_list/problems_solved_overview_count",
                        params={"username": username},
                    )
                    if res2.status_code == 200:
                        solved_data = res2.json()
                except Exception:
                    pass

                # 3) Streak / score / coins — optional
                try:
                    res3 = self._get(
                        client,
                        "https://www.interviewbit.com/v2/profile/username/streak/",
                        params={"id": username},
                    )
                    if res3.status_code == 200:
                        streak_data = res3.json()
                except Exception:
                    pass

                # 4) Submission analysis — optional
                try:
                    res4 = self._get(
                        client,
                        "https://www.interviewbit.com/v2/profile/username/submission-analysis/",
                        params={"id": username},
                    )
                    if res4.status_code == 200:
                        submission_data = res4.json()
                except Exception:
                    pass

                # 5) Badges progress — optional
                try:
                    res5 = self._get(
                        client,
                        "https://www.interviewbit.com/api/v3/badges/user-progress/",
                        params={"username": username},
                    )
                    if res5.status_code == 200:
                        badges_data = res5.json()
                except Exception:
                    pass

        except ProfileCollectError:
            raise
        except httpx.HTTPError as e:
            raise ProfileCollectError(f"Could not reach InterviewBit API: {e}") from e

        # ------------------------------------------------------------------ #
        # Decode profile (required)
        # ------------------------------------------------------------------ #

        assert profile_data is not None
        global_rank = profile_data.get("global_rank")
        university_rank = profile_data.get("university_rank")
        # Normalize ranks — can be None if unranked
        global_rank_int = _safe_int(global_rank, 0) if global_rank is not None else 0
        university_rank_int = _safe_int(university_rank, 0) if university_rank is not None else 0

        # ------------------------------------------------------------------ #
        # Decode solved overview -> strength areas
        # ------------------------------------------------------------------ #

        course_areas: list[dict] = []
        topic_areas: list[dict] = []
        difficulty_breakdown: dict[str, int] = {}
        total_problems_solved = 0
        total_user_score = 0
        total_time_spent = 0

        if isinstance(solved_data, dict):
            total_problems_solved = _safe_int(solved_data.get("total_problems_solved"))
            total_time_spent = _safe_int(solved_data.get("total_time_spent"))
            # Course strengths (Programming, Databases, C++ etc.)
            for c in solved_data.get("course_problems_solved") or []:
                if not isinstance(c, dict):
                    continue
                solved = _safe_int(c.get("solved_problems_count"))
                if solved <= 0:
                    continue
                course_areas.append(
                    {
                        "id": c.get("id"),
                        "slug": c.get("slug") or "",
                        "title": c.get("title") or c.get("slug") or "",
                        "solved": solved,
                        "total_score": _safe_int(c.get("total_score")),
                        "total_user_score": _safe_int(c.get("total_user_score")),
                    }
                )
            # Topic strengths (Time Complexity, Math, SQL etc.) — main strength signal
            for t in solved_data.get("topic_problems_solved") or []:
                if not isinstance(t, dict):
                    continue
                solved = _safe_int(t.get("solved_problems_count"))
                if solved <= 0:
                    continue
                topic_areas.append(
                    {
                        "id": t.get("id"),
                        "slug": t.get("slug") or "",
                        "title": t.get("title") or t.get("slug") or "",
                        "course_id": t.get("course_id"),
                        "solved": solved,
                        "total_score": _safe_int(t.get("total_score")),
                        "total_user_score": _safe_int(t.get("total_user_score")),
                    }
                )
            for d in solved_data.get("difficulty_problems_solved") or []:
                if not isinstance(d, dict):
                    continue
                lvl = str(d.get("difficulty_level") or "").lower()
                cnt = _safe_int(d.get("solved_problems_count"))
                if lvl:
                    difficulty_breakdown[lvl] = cnt
            # Fallback total if not provided directly
            if total_problems_solved == 0:
                total_problems_solved = sum(c["solved"] for c in course_areas) or sum(t["solved"] for t in topic_areas)

        course_areas.sort(key=lambda x: x["solved"], reverse=True)
        topic_areas.sort(key=lambda x: x["solved"], reverse=True)

        # Strength areas combined for display — top topics then courses
        strength_areas = topic_areas + course_areas
        # Also build simple topics list for backward compat (list of titles)
        topics_simple = [t["title"] for t in topic_areas]

        # ------------------------------------------------------------------ #
        # Decode streak / score
        # ------------------------------------------------------------------ #

        current_streak = 0
        streak_score = 0
        coins = 0
        ib_score = 0
        if isinstance(streak_data, dict):
            current_streak = _safe_int(streak_data.get("current_streak"))
            streak_score = _safe_int(streak_data.get("streak_score"))
            coins = _safe_int(streak_data.get("coins"))
            ib_score = _safe_int(streak_data.get("score"))

        # ------------------------------------------------------------------ #
        # Decode submission analysis
        # ------------------------------------------------------------------ #

        submission_analysis: dict[str, int] = {}
        total_submissions = 0
        if isinstance(submission_data, list):
            for entry in submission_data:
                if not isinstance(entry, dict):
                    continue
                result = str(entry.get("result") or "").lower()
                cnt = _safe_int(entry.get("count"))
                if result:
                    submission_analysis[result] = cnt
            total_submissions = sum(submission_analysis.values())

        # ------------------------------------------------------------------ #
        # Decode badges
        # ------------------------------------------------------------------ #

        badges: list[dict] = []
        badges_count = 0
        if isinstance(badges_data, list):
            for b in badges_data:
                if not isinstance(b, dict):
                    continue
                # Only count badges with some progress
                if _safe_int(b.get("current_progress")) > 0:
                    badges.append(
                        {
                            "name": b.get("name") or "",
                            "goal": _safe_int(b.get("goal")),
                            "current_progress": _safe_int(b.get("current_progress")),
                            "badge_status": _safe_int(b.get("badge_status")),
                        }
                    )
            badges_count = len(badges)
            # Full total badges available (for denominator)
            total_badges_available = len(badges_data)
        else:
            total_badges_available = 0

        # ------------------------------------------------------------------ #
        # Build final data dict
        # ------------------------------------------------------------------ #

        # Backward-compat fields
        rank_str = None
        if global_rank_int and university_rank_int:
            rank_str = f"Global #{global_rank_int} / University #{university_rank_int}"
        elif global_rank_int:
            rank_str = f"Global #{global_rank_int}"
        elif university_rank_int:
            rank_str = f"University #{university_rank_int}"

        result = {
            "_source": "interviewbit-api",
            "username": profile_data.get("username") or username,
            "name": profile_data.get("name"),
            "university": profile_data.get("university"),
            "country": profile_data.get("country"),
            "city": profile_data.get("city"),
            "image": profile_data.get("image"),
            "follower_count": _safe_int(profile_data.get("follower_count")),
            "following_count": _safe_int(profile_data.get("following_count")),
            # Core requested fields
            "global_rank": global_rank_int if global_rank_int else None,
            "university_rank": university_rank_int if university_rank_int else None,
            "global_rank_raw": global_rank,
            "university_rank_raw": university_rank,
            # Strength areas
            "strength_areas": strength_areas,
            "course_areas": course_areas,
            "topic_areas": topic_areas,
            "difficulty_breakdown": difficulty_breakdown,
            # Core stats
            "problems_solved": total_problems_solved,
            "total_problems_solved": total_problems_solved,
            "total_user_score": total_user_score or ib_score,
            "score": ib_score,
            "coins": coins,
            "total_time_spent": total_time_spent,
            "current_streak": current_streak,
            "streak_days": current_streak,
            "streak_score": streak_score,
            "total_submissions": total_submissions,
            "submission_analysis": submission_analysis,
            # Badges
            "badges": badges,
            "badges_count": badges_count,
            "total_badges_available": total_badges_available,
            # Backward compat
            "rank": rank_str,
            "topics": topics_simple,
            "active_days": 0,
            "plan_solved": None,
            "plan_total": None,
            "_rate_limit_hint": "InterviewBit public REST API (no auth). Results cached for 1 hour.",
        }
        _cache_set(username, result)
        return result

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        total = int(30 + level * 200 + rng.randint(0, 80))
        # Simulated strength areas mirroring real structure
        topic_pool = [
            ("Time Complexity", "time-complexity"),
            ("Math", "math"),
            ("Arrays", "arrays"),
            ("Strings", "strings"),
            ("Hashing", "hashing"),
            ("Stacks And Queues", "stacks-and-queues"),
            ("SQL Programming", "sql-queries"),
            ("Dynamic Programming", "dynamic-programming"),
            ("Graphs", "graphs"),
            ("Binary Search", "binary-search"),
        ]
        k = rng.randint(2, min(6, len(topic_pool)))
        chosen = rng.sample(topic_pool, k=k)
        topic_areas = []
        remaining = total
        for title, slug in chosen:
            cnt = rng.randint(1, max(1, int(total * 0.35))) if remaining > 0 else 0
            cnt = min(cnt, remaining)
            if cnt:
                topic_areas.append(
                    {
                        "id": rng.randint(1, 300),
                        "slug": slug,
                        "title": title,
                        "course_id": 1,
                        "solved": cnt,
                        "total_score": cnt * rng.randint(20, 50),
                        "total_user_score": cnt * rng.randint(15, 40),
                    }
                )
                remaining -= cnt
        topic_areas.sort(key=lambda x: x["solved"], reverse=True)
        strength_areas = topic_areas
        global_rank = rng.randint(5000, 400000) if level < 0.7 else rng.randint(1000, 50000)
        university_rank = rng.randint(1, 20) if level > 0.5 else rng.randint(1, 100)
        return {
            "_source": "mock",
            "_warning": "Simulated demo data — connect the real platform API for production evidence.",
            "username": handle,
            "name": f"Demo User ({handle})",
            "university": rng.choice(["Demo University", "Nutan College Of Engineering And Research", "IIT Demo"]),
            "country": "India",
            "city": None,
            "image": None,
            "follower_count": rng.randint(0, 20),
            "following_count": rng.randint(0, 20),
            "global_rank": global_rank,
            "university_rank": university_rank,
            "global_rank_raw": global_rank,
            "university_rank_raw": university_rank,
            "strength_areas": strength_areas,
            "course_areas": [{"title": "Programming", "slug": "programming", "solved": total, "total_score": total * 30, "total_user_score": total * 25}],
            "topic_areas": topic_areas,
            "difficulty_breakdown": {
                "easy": int(total * rng.uniform(0.5, 0.7)),
                "medium": int(total * rng.uniform(0.2, 0.4)),
                "hard": max(0, total - int(total * 0.6) - int(total * 0.3)),
            },
            "problems_solved": total,
            "total_problems_solved": total,
            "total_user_score": int(total * rng.uniform(20, 50)),
            "score": rng.randint(200, 2000),
            "coins": rng.randint(0, 200),
            "total_time_spent": rng.randint(1000000, 20000000),
            "current_streak": rng.randint(0, 90),
            "streak_days": rng.randint(0, 90),
            "streak_score": rng.randint(0, 500),
            "total_submissions": int(total * rng.uniform(1.2, 2.0)),
            "submission_analysis": {"correct_answer": total, "wrong_answer": rng.randint(0, 10), "compilation_error": rng.randint(0, 5)},
            "badges": [],
            "badges_count": rng.randint(0, 10),
            "total_badges_available": 15,
            "rank": f"Global #{global_rank} / University #{university_rank}",
            "topics": [t["title"] for t in topic_areas],
            "active_days": rng.randint(20, 300),
            "plan_solved": rng.randint(5, total),
            "plan_total": 330,
        }
