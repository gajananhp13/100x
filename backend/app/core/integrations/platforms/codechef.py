"""CodeChef integration — simulated competitive programming profile (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("codechef", "CodeChef", "cc", "https://codechef.com/users/{handle}", "username", False)


class CodeChefIntegration(SimulatedPlatformMixin):
    platform_id = "codechef"
    platform_label = "CodeChef"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        stars = max(1, min(7, int(1 + level * 5)))
        return {"stars": stars, "rating": int(1200 + stars * 250 + rng.randint(0, 100)), "problems_solved": rng.randint(60, 500), "contests": rng.randint(3, 40)}
