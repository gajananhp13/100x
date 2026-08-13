import httpx

from app.core.integrations.platforms.github import GitHubIntegration


USER = {
    "login": "octo",
    "avatar_url": "https://avatars.example/u",
    "public_repos": 2,
    "followers": 3,
    "following": 1,
    "created_at": "2020-01-01T00:00:00Z",
    "bio": "bio",
    "location": "loc",
}

REPOS = [
    {
        "name": "active-repo",
        "full_name": "octo/active-repo",
        "description": "has commits",
        "html_url": "https://github.com/octo/active-repo",
        "homepage": None,
        "default_branch": "main",
        "forks_count": 1,
        "stargazers_count": 2,
        "watchers_count": 0,
        "open_issues_count": 0,
        "language": "Python",
        "license": {"spdx_id": "MIT"},
        "topics": [],
        "created_at": "2020-01-01T00:00:00Z",
        "pushed_at": "2021-01-01T00:00:00Z",
        "fork": False,
        "private": False,
    },
    {
        "name": "empty-repo",
        "full_name": "octo/empty-repo",
        "description": "no commits",
        "html_url": "https://github.com/octo/empty-repo",
        "homepage": None,
        "default_branch": "main",
        "forks_count": 0,
        "stargazers_count": 0,
        "watchers_count": 0,
        "open_issues_count": 0,
        "language": None,
        "license": None,
        "topics": [],
        "created_at": "2021-01-01T00:00:00Z",
        "pushed_at": None,
        "fork": False,
        "private": False,
    },
]


def build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/users/octo/repos" in url:
            return httpx.Response(200, json=REPOS)
        if "/users/octo" in url:
            return httpx.Response(200, json=USER)
        if "/git/trees/" in url:
            return httpx.Response(200, json={"tree": [{"path": "README.md", "type": "blob"}]})
        if "/readme" in url:
            return httpx.Response(200, text="# Project\n\n## Setup\nusage")
        if "/languages" in url:
            return httpx.Response(200, json={"Python": 4000})
        if "/commits" in url:
            if "active-repo" in url:
                return httpx.Response(200, json=[{"sha": "a"}])
            return httpx.Response(409, json={"message": "Git Repository is empty."})
        if "/contributors" in url:
            if "active-repo" in url:
                return httpx.Response(200, json=[{"login": "octo"}])
            return httpx.Response(409, json={"message": "Git Repository is empty."})
        if "/pulls" in url:
            return httpx.Response(200, json=[])
        return httpx.Response(500, text=f"unhandled: {url}")

    return httpx.MockTransport(handler)


def test_collect_succeeds_with_empty_repo():
    profile = GitHubIntegration(transport=build_transport()).collect("octo")

    assert profile["_source"] == "github-api"
    assert profile["username"] == "octo"
    assert profile["public_repos"] == 2
    assert len(profile["repos"]) == 2

    by_name = {r["name"]: r for r in profile["repos"]}
    assert by_name["active-repo"]["commits_count"] == 1
    assert by_name["active-repo"]["contributors_count"] == 1
    assert by_name["empty-repo"]["commits_count"] == 0
    assert by_name["empty-repo"]["contributors_count"] == 0
    assert profile["total_commits_fetched"] == 1


def test_collect_user_not_found():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )
    import pytest

    from app.core.integrations.base import ProfileCollectError

    with pytest.raises(ProfileCollectError, match="not found"):
        GitHubIntegration(transport=transport).collect("ghost")


def test_collect_rejects_url_handle():
    import pytest

    from app.core.integrations.base import ProfileCollectError

    with pytest.raises(ProfileCollectError, match="no URL"):
        GitHubIntegration().collect("https://github.com/octocat")
