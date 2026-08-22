"""Platform registry — the catalog of connectable public profiles.

Each platform is implemented in its own module under core/integrations/platforms/
(see `PLATFORMS` and `INTEGRATIONS` there). This module is a thin aggregator that
resolves a platform id to its integration instance.
"""

from __future__ import annotations

from .base import PlatformDef, PlatformIntegration
from .platforms import INTEGRATIONS, PLATFORMS

PLATFORM_BY_ID: dict[str, PlatformDef] = {p.id: p for p in PLATFORMS}


def url_for(platform_id: str, handle: str) -> str:
    p = PLATFORM_BY_ID.get(platform_id)
    if not p:
        return ""
    if platform_id == "portfolio":
        handle = handle if handle.startswith(("http://", "https://")) else f"https://{handle}"
        return handle
    return p.url_template.format(handle=handle)


def build_integration(platform_id: str, force_mock: bool = False) -> PlatformIntegration:
    """Return the integration instance for a platform id.

    force_mock=True routes every platform through its simulation (used by the
    demo candidate so it works fully offline).
    """
    p = PLATFORM_BY_ID.get(platform_id)
    if not p:
        raise KeyError(f"Unknown platform: {platform_id}")
    integration_cls = INTEGRATIONS.get(platform_id)
    if not integration_cls:
        raise KeyError(f"No integration registered for platform: {platform_id}")
    return integration_cls(simulate=force_mock)


def platform_categories() -> dict[str, list[PlatformDef]]:
    return {
        "Code Hosting": [p for p in PLATFORMS if p.id in ("github", "gitlab", "bitbucket")],
        "Professional & Social": [p for p in PLATFORMS if p.id in ("linkedin", "portfolio")],
        "Coding & Competitions": [p for p in PLATFORMS if p.id in ("leetcode", "interviewbit", "codeforces", "codechef", "geeksforgeeks", "hackerrank", "stackoverflow")],
        "Hackathons": [p for p in PLATFORMS if p.id == "devpost"],
    }
