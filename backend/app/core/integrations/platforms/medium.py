"""Medium integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("medium", "Medium", "md", "https://medium.com/@{handle}", "@username", False)


class MediumIntegration(SimulatedPlatformMixin):
    platform_id = "medium"
    platform_label = "Medium"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {"followers": rng.randint(0, 300), "articles": rng.randint(1, 20), "claps": rng.randint(20, 5000), "topics": ["software engineering", "ai"]}
