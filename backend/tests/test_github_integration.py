import httpx

from app.core.integrations.platforms.github import GitHubIntegration


def profile_html():
    return """<html><head>
<meta property="og:image" content="https://avatars.example/u">
<meta name="description" content="octo has 2 repositories available. Follow their code on GitHub.">
</head><body>
<h1 class="vcard-names"><span itemprop="name"> The Octo </span></h1>
<ul class="vcard-details">
  <li class="vcard-detail" aria-label="Location: San Francisco"></li>
</ul>
<div class="p-note" itemprop="description"> building things </div>
<a class="Link--secondary" href="https://github.com/octo?tab=followers"><svg></svg>
  <span class="text-bold color-fg-default">3</span>
  followers
</a>
<a class="Link--secondary" href="https://github.com/octo?tab=following">
  <span class="text-bold color-fg-default">1</span>
  following
</a>
</body></html>"""


def repo_li(name, desc, language, stars, forks, updated, topic=None):
    lang = (
        f'<span itemprop="programmingLanguage">{language}</span>'
        if language else ""
    )
    topic_tag = (
        f'<a data-octo-dimensions="x:topic" >{topic}</a>'
        if topic else ""
    )
    return f"""<li class="col-12 public source" itemprop="owns">
  <div><h3 class="wb-break-all">
    <a href="/octo/{name}" itemprop="name codeRepository">{name}</a>
  </h3></div>
  <div><p itemprop="description"> {desc} </p></div>
  <div class="f6 color-fg-muted mt-2">
  {lang}
  <a href="/octo/{name}/stargazers"><svg></svg> {stars} </a>
  <a href="/octo/{name}/forks"><svg></svg> {forks} </a>
  {topic_tag}
  <relative-time datetime="{updated}">Updated</relative-time>
  </div>
</li>"""


def repos_html():
    return (
        '<div id="user-repositories-list"><ul>'
        + repo_li("active-repo", "has commits", "Python", 2, 1, "2025-01-01T00:00:00Z", "python")
        + repo_li("empty-repo", "no commits", None, 0, 0, "2025-01-02T00:00:00Z")
        + "</ul></div>"
    )


def repo_page_html():
    return """<html><body>
<article class="markdown-body entry-content" itemprop="text">
# Project

## Setup

## Usage

## getting started

code:
```
pip install foo
```
more http://example.test text
</article>
</body></html>"""


def empty_repo_page_html():
    return "<html><body><div>empty</div></body></html>"


def build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "tab=repositories" in url:
            return httpx.Response(200, text=repos_html())
        if url.rstrip("/") == "https://github.com/octo/active-repo":
            return httpx.Response(200, text=repo_page_html())
        if url.rstrip("/") == "https://github.com/octo/empty-repo":
            return httpx.Response(200, text=empty_repo_page_html())
        if url.rstrip("/") == "https://github.com/octo":
            return httpx.Response(200, text=profile_html())
        return httpx.Response(500, text=f"unhandled: {url}")

    return httpx.MockTransport(handler)


def test_collect_succeeds_with_empty_repo():
    profile = GitHubIntegration(transport=build_transport()).collect("octo")

    assert profile["_source"] == "github-html"
    assert profile["username"] == "octo"
    assert profile["public_repos"] == 2
    assert len(profile["repos"]) == 2

    by_name = {r["name"]: r for r in profile["repos"]}
    assert by_name["active-repo"]["stars"] == 2
    assert by_name["active-repo"]["forks"] == 1
    assert by_name["active-repo"]["language"] == "Python"
    assert by_name["active-repo"]["has_readme"] is True
    assert by_name["empty-repo"]["has_readme"] is False
    assert profile["total_stars"] == 2

    assert profile["followers"] == 3
    assert profile["following"] == 1
    assert profile["location"] == "San Francisco"


def test_collect_user_not_found():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, text="Not Found")
    )
    import pytest

    from app.core.integrations.base import ProfileCollectError

    with pytest.raises(ProfileCollectError, match="not found"):
        GitHubIntegration(transport=transport).collect("ghost")


def test_collect_rejects_org_account():
    import pytest

    from app.core.integrations.base import ProfileCollectError

    org_html = "<html><body><h1 class='org-n'>Some Org</h1></body></html>"
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=org_html))

    with pytest.raises(ProfileCollectError, match="personal"):
        GitHubIntegration(transport=transport).collect("someorg")


def test_collect_rejects_invalid_handle():
    import pytest

    from app.core.integrations.base import ProfileCollectError

    with pytest.raises(ProfileCollectError):
        GitHubIntegration().collect("https://github.com/")