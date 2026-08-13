"""Genkit-based GitHub profile scraping flow.

Wraps GitHubIntegration.collect() inside a Google Genkit flow so the scrape
is exposed as a typed, schema-described Genkit action (name, input/output
JSON schemas, description) instead of a plain function call.

The OpenAI plugin is registered lazily; the AI summary is only attempted when
OPENAI_API_KEY is configured, and its failure never fails the scrape itself.

Install note: genkit 0.9.0 declares a dependency on dotpromptz-handlebars>=0.1.8
which is not published on PyPI. Pin dotpromptz-handlebars==0.1.3 and install
genkit with --no-deps (see requirements.txt).
"""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field

from genkit import Genkit, TextPart
from genkit_openai import OpenAI, openai_model

from app.config import settings
from app.core.integrations.platforms.github import GitHubIntegration

logger = logging.getLogger(__name__)

_ai = Genkit(plugins=[OpenAI()])
_summary_model = openai_model(settings.openai_model)


class ScrapeGithubProfileInput(BaseModel):
    username: str = Field(description="GitHub username or handle to scrape")


class ScrapeGithubProfileOutput(BaseModel):
    success: bool
    data: dict | None = None
    summary: str | None = None
    error: str | None = None
    cached: bool = False


@_ai.flow(
    name="scrapeGithubProfile",
    description="Scrape a GitHub profile via the GitHub API using Genkit",
)
async def scrape_github_profile(username: str) -> ScrapeGithubProfileOutput:
    """Collect a GitHub profile through Genkit and optionally summarize it."""
    try:
        integration = GitHubIntegration(simulate=False)
        data = integration.collect(username)
    except Exception as exc:  # noqa: BLE001 - flow must return a structured error
        logger.warning("Genkit flow scrapeGithubProfile failed for %r: %s", username, exc)
        return ScrapeGithubProfileOutput(success=False, error=str(exc))

    summary = None
    if settings.openai_api_key:
        try:
            response = await _ai.generate(
                model=_summary_model,
                prompt=(
                    "Summarize this GitHub profile for a recruiter in 2-3 sentences: "
                    f"{json.dumps(data, default=str)[:4000]}"
                ),
            )
            text_parts = [p.text for p in response.message.content if isinstance(p, TextPart)]
            summary = " ".join(text_parts).strip() or None
        except Exception as exc:  # noqa: BLE001 - summary is best-effort
            logger.warning("Genkit summary generation failed for %r: %s", username, exc)

    return ScrapeGithubProfileOutput(success=True, data=data, summary=summary)
