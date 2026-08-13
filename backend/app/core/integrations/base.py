"""Platform integration framework.

To add a new platform integration:
1. Subclass PlatformIntegration
2. Implement collect() returning raw public data conforming to the platform's
   data contract (see MOCK_SCHEMAS in mock.py for the expected shape).
3. Register it in PLATFORMS (in integrations/__init__.py) with id, label, url
   builder, and placeholder handle.

The pipeline never guesses: an integration only returns data it actually
retrieved from a public source (or, in mock mode, a clearly-simulated data set).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...models.profiles import ConnectedProfile


class ProfileCollectError(Exception):
    """Raised when a profile cannot be collected (bad handle, rate limit, ...)."""


@dataclass(frozen=True)
class PlatformDef:
    """Catalog entry for a connectable public profile platform.

    Defined next to the platform's integration class in core/integrations/platforms/,
    so every social connectivity feature owns its own registration.
    """

    id: str
    label: str
    icon: str  # emoji-free short glyph key used by the frontend
    url_template: str  # profile URL builder, {handle} placeholder
    handle_placeholder: str
    real_api: bool  # True => live public API integration, False => demo simulation


class PlatformIntegration(ABC):
    platform_id: str
    platform_label: str

    @abstractmethod
    def collect(self, handle: str) -> dict:
        """Retrieve public data for `handle`. Raise ProfileCollectError on failure."""

    def build_profile(self, handle: str, data: dict, url: str) -> ConnectedProfile:
        from datetime import datetime, timezone

        return ConnectedProfile(
            platform=self.platform_id,
            platform_label=self.platform_label,
            handle=handle,
            profile_url=url,
            status="collected",
            collected_at=datetime.now(timezone.utc),
            data=data,
        )