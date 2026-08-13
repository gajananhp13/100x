"""DEV Community integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("devto", "DEV Community", "dv", "https://dev.to/{handle}", "username", False)


class DevtoIntegration(SimulatedPlatformMixin):
    platform_id = "devto"
    platform_label = "DEV Community"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {"articles": rng.randint(1, 25), "followers": rng.randint(0, 250), "positive_reactions": rng.randint(20, 4000), "comments": rng.randint(2, 150)}
