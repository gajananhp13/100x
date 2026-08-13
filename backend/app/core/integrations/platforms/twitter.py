"""X (Twitter) integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("twitter", "X (Twitter)", "tw", "https://x.com/{handle}", "@username", False)


class TwitterIntegration(SimulatedPlatformMixin):
    platform_id = "twitter"
    platform_label = "X (Twitter)"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {"followers": rng.randint(50, 5000), "following": rng.randint(100, 1500), "tweets": rng.randint(200, 20000), "verified": bool(rng.random() < 0.1), "bio": "Software developer"}
