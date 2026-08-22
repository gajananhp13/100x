import httpx
import pytest

import app.core.ai.genkit_flow as genkit_flow
from app.core.ai.genkit_flow import scrape_github_profile


def profile_html():
    return """<html><head>
<meta name="description" content="octo has 0 repositories available.">
<meta property="og:image" content="https://avatars.example/u">
</head><body>
<h1 class="vcard-names"><span itemprop="name"> The Octo </span></h1>
<ul class="vcard-details">
  <li class="vcard-detail" aria-label="Location: loc"></li>
</ul>
<a href="https://github.com/octo?tab=followers"><svg></svg>
  <span class="text-bold color-fg-default">1</span> followers</a>
<a href="https://github.com/octo?tab=following">
  <span class="text-bold color-fg-default">0</span> following</a>
</body></html>"""


def empty_repos_html():
    return '<div id="user-repositories-list"><ul></ul></div>'


def build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "tab=repositories" in url:
            return httpx.Response(200, text=empty_repos_html())
        if url.rstrip("/") == "https://github.com/octo":
            return httpx.Response(200, text=profile_html())
        return httpx.Response(500, text=f"unhandled: {url}")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_flow_collects_profile(monkeypatch):
    integration = genkit_flow.GitHubIntegration(transport=build_transport())
    monkeypatch.setattr(
        genkit_flow, "GitHubIntegration", lambda simulate=False: integration
    )

    out = await scrape_github_profile("octo")

    assert out.success is True
    assert out.data is not None
    assert out.data["_source"] == "github-html"
    assert out.data["username"] == "octo"
    assert out.summary is None
    assert out.error is None


@pytest.mark.asyncio
async def test_flow_returns_structured_error(monkeypatch):
    def boom(simulate=False):
        raise RuntimeError("boom")

    monkeypatch.setattr(genkit_flow, "GitHubIntegration", boom)

    out = await scrape_github_profile("octo")

    assert out.success is False
    assert out.data is None
    assert out.error == "boom"


@pytest.mark.asyncio
async def test_flow_generates_summary_when_key_configured(monkeypatch):
    integration = genkit_flow.GitHubIntegration(transport=build_transport())
    monkeypatch.setattr(
        genkit_flow, "GitHubIntegration", lambda simulate=False: integration
    )
    monkeypatch.setattr(genkit_flow.settings, "openai_api_key", "test-key")
    from genkit import TextPart

    class FakeMessage:
        content = [TextPart(text="Strong Python profile with 0 repos.")]

    class FakeResponse:
        message = FakeMessage()

    async def fake_generate(**kwargs):
        assert kwargs["prompt"]
        return FakeResponse()

    monkeypatch.setattr(genkit_flow._ai, "generate", fake_generate)

    out = await scrape_github_profile("octo")

    assert out.success is True
    assert out.summary == "Strong Python profile with 0 repos."