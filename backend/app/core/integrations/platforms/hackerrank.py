"""HackerRank integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("hackerrank", "HackerRank", "hr", "https://hackerrank.com/{handle}", "username", False)


class HackerRankIntegration(SimulatedPlatformMixin):
    platform_id = "hackerrank"
    platform_label = "HackerRank"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        stars = min(5, int(1 + level * 5))
        return {"stars": stars, "badges": rng.randint(2, 12), "certificates": rng.randint(0, 3), "problems_solved": int(60 + level * 260)}
