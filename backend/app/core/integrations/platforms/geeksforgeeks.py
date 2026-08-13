"""GeeksforGeeks integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("geeksforgeeks", "GeeksforGeeks", "gg", "https://auth.geeksforgeeks.org/user/{handle}", "username", False)


class GeeksforGeeksIntegration(SimulatedPlatformMixin):
    platform_id = "geeksforgeeks"
    platform_label = "GeeksforGeeks"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {"coding_score": int(100 + level * 800 + rng.randint(0, 150)), "problems_solved": int(50 + level * 350)}
