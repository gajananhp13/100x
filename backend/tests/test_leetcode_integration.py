import json

import httpx
import pytest

from app.core.integrations.platforms.leetcode import (
    LeetCodeIntegration,
    clear_leetcode_cache,
    extract_username,
)
from app.core.integrations.base import ProfileCollectError

MATCHED_RESPONSE = {
    "data": {
        "matchedUser": {
            "username": "jdoe",
            "profile": {"realName": "Jane Doe", "ranking": 123456},
            "submitStats": {
                "acSubmissionNum": [
                    {"difficulty": "All", "count": 450},
                    {"difficulty": "Easy", "count": 200},
                    {"difficulty": "Medium", "count": 200},
                    {"difficulty": "Hard", "count": 50},
                ],
                "totalSubmissionNum": [
                    {"difficulty": "All", "count": 700},
                    {"difficulty": "Easy", "count": 300},
                    {"difficulty": "Medium", "count": 300},
                    {"difficulty": "Hard", "count": 100},
                ],
            },
            "badges": [
                {"id": "b1", "displayName": "100 Days", "icon": "/static/badge.png"},
                {"id": "b2", "displayName": "No Icon", "icon": ""},
            ],
        },
        "allQuestionsCount": [
            {"difficulty": "Easy", "count": 800},
            {"difficulty": "Medium", "count": 1700},
            {"difficulty": "Hard", "count": 800},
            {"difficulty": "All", "count": 3300},
        ],
    }
}

CONTEST_RESPONSE = {
    "data": {"userContestRanking": {"rating": 1523.45}}
}

RECENT_RESPONSE = {
    "data": {
        "recentSubmissionList": [
            {"title": "Two Sum", "statusDisplay": "Accepted", "timestamp": "1719800000"},
            {"title": "", "statusDisplay": "Accepted", "timestamp": "1719700000"},
            {"title": "Three Sum", "statusDisplay": "Wrong Answer", "timestamp": "1719600000"},
        ]
    }
}

SKILLS_RESPONSE = {
    "data": {
        "matchedUser": {
            "tagProblemCounts": {
                "fundamental": [
                    {"tagName": "Array", "tagSlug": "array", "problemsSolved": 40},
                    {"tagName": "Hash Table", "tagSlug": "hash-table", "problemsSolved": 25},
                ],
                "intermediate": [
                    {"tagName": "Dynamic Programming", "tagSlug": "dynamic-programming", "problemsSolved": 18},
                ],
                "advanced": [
                    {"tagName": "Segment Tree", "tagSlug": "segment-tree", "problemsSolved": 3},
                ],
            }
        }
    }
}

CALENDAR_RESPONSE = {
    "data": {
        "matchedUser": {
            "userCalendar": {"streak": 12, "totalActiveDays": 300},
        }
    }
}


def build_transport(requests_log: list | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if requests_log is not None:
            requests_log.append(request)
        body = json.loads(request.content)
        query = body["query"]
        if "tagProblemCounts" in query:
            return httpx.Response(200, json=SKILLS_RESPONSE)
        if "userCalendar" in query:
            return httpx.Response(200, json=CALENDAR_RESPONSE)
        if "matchedUser" in query:
            return httpx.Response(200, json=MATCHED_RESPONSE)
        if "contestRanking" in query:
            return httpx.Response(200, json=CONTEST_RESPONSE)
        if "recentSubmissionList" in query:
            return httpx.Response(200, json=RECENT_RESPONSE)
        return httpx.Response(500, text="unexpected query")

    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_leetcode_cache()
    yield
    clear_leetcode_cache()


# ---------------------------------------------------------------------- #
# extract_username
# ---------------------------------------------------------------------- #

def test_extract_username_handles_all_input_forms():
    assert extract_username("jdoe") == "jdoe"
    assert extract_username("  jdoe  ") == "jdoe"
    assert extract_username("@jdoe") == "jdoe"
    assert extract_username("https://leetcode.com/u/jdoe/") == "jdoe"
    assert extract_username("https://leetcode.com/u/jdoe?tab=repos") == "jdoe"


def test_extract_username_rejects_invalid():
    with pytest.raises(ProfileCollectError):
        extract_username("")
    with pytest.raises(ProfileCollectError):
        extract_username("has space")
    with pytest.raises(ProfileCollectError):
        extract_username("https://example.com/u/jdoe")


# ---------------------------------------------------------------------- #
# collect()
# ---------------------------------------------------------------------- #

def test_collect_returns_full_profile():
    profile = LeetCodeIntegration(transport=build_transport()).collect("jdoe")

    assert profile["_source"] == "leetcode-api"
    assert profile["username"] == "jdoe"
    assert profile["name"] == "Jane Doe"
    assert profile["ranking"] == 123456
    assert profile["total_solved"] == 450
    assert profile["easy"] == 200
    assert profile["medium"] == 200
    assert profile["hard"] == 50
    assert profile["total_questions"] == 3300
    assert profile["acceptance_rate"] == 64  # round(450 / 700 * 100)
    assert profile["contest_rating"] == 1523
    assert profile["streak_days"] == 12
    assert profile["total_active_days"] == 300
    assert profile["skills"] == {
        "fundamental": {"total": 65, "topics": [
            {"name": "Array", "slug": "array", "solved": 40},
            {"name": "Hash Table", "slug": "hash-table", "solved": 25},
        ]},
        "intermediate": {"total": 18, "topics": [
            {"name": "Dynamic Programming", "slug": "dynamic-programming", "solved": 18},
        ]},
        "advanced": {"total": 3, "topics": [
            {"name": "Segment Tree", "slug": "segment-tree", "solved": 3},
        ]},
    }
    assert profile["badges"] == [
        {"name": "100 Days", "icon": "https://leetcode.com/static/badge.png"},
        {"name": "No Icon", "icon": ""},
    ]
    assert profile["recent_submissions"] == [
        {"title": "Two Sum", "status": "Accepted", "timestamp": 1719800000},
        {"title": "Three Sum", "status": "Wrong Answer", "timestamp": 1719600000},
    ]


def test_collect_user_not_found():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"data": {"matchedUser": None}})
    )
    with pytest.raises(ProfileCollectError, match="not found"):
        LeetCodeIntegration(transport=transport).collect("ghost")


def test_collect_graphql_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, json={"errors": [{"message": "Something went wrong"}]}
        )
    )
    with pytest.raises(ProfileCollectError, match="Something went wrong"):
        LeetCodeIntegration(transport=transport).collect("jdoe")


def test_collect_http_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, text="rate limited")
    )
    with pytest.raises(ProfileCollectError, match="429"):
        LeetCodeIntegration(transport=transport).collect("jdoe")


def test_optional_queries_fail_gracefully():
    def handler(request: httpx.Request) -> httpx.Response:
        query = json.loads(request.content)["query"]
        if "matchedUser" in query:
            return httpx.Response(200, json=MATCHED_RESPONSE)
        raise httpx.ConnectError("network down")

    profile = LeetCodeIntegration(transport=httpx.MockTransport(handler)).collect("jdoe")
    assert profile["username"] == "jdoe"
    assert profile["contest_rating"] == 0
    assert profile["recent_submissions"] == []
    assert profile["skills"] == {"fundamental": {}, "intermediate": {}, "advanced": {}}
    assert profile["streak_days"] == 0
    assert profile["total_active_days"] is None


def test_invalid_handle_raises():
    with pytest.raises(ProfileCollectError):
        LeetCodeIntegration().collect("not a handle")


def test_cache_short_circuits_network():
    requests_log: list[httpx.Request] = []
    integration = LeetCodeIntegration(transport=build_transport(requests_log))

    first = integration.collect("jdoe")
    second = integration.collect("jdoe")

    assert first == second
    # 6 parallel queries for the first call (matched, contest, contest_history, recent, skills, calendar), 0 for the cached second call
    assert len(requests_log) == 6
    assert integration.collect("jdoe") == first


def test_cache_is_per_username():
    def handler(request: httpx.Request) -> httpx.Response:
        username = json.loads(request.content)["variables"]["username"]
        return httpx.Response(
            200,
            json={
                "data": {
                    "matchedUser": {
                        "username": username,
                        "profile": {"realName": "", "ranking": 0},
                        "submitStats": {
                            "acSubmissionNum": [{"difficulty": "All", "count": 1}],
                            "totalSubmissionNum": [{"difficulty": "All", "count": 2}],
                        },
                        "badges": [],
                    },
                    "allQuestionsCount": [],
                }
            },
        )

    integration = LeetCodeIntegration(transport=httpx.MockTransport(handler))
    assert integration.collect("jdoe")["username"] == "jdoe"
    assert integration.collect("other")["username"] == "other"
