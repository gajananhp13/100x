"""Codeforces integration — simulated competitive programming profile (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("codeforces", "Codeforces", "cf", "https://codeforces.com/profile/{handle}", "handle", False)


class CodeforcesIntegration(SimulatedPlatformMixin):
    platform_id = "codeforces"
    platform_label = "Codeforces"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        rating = int(rng.randint(900, 1600) + level * 600)
        rank = "Newbie" if rating < 1200 else ("Pupil" if rating < 1400 else ("Specialist" if rating < 1600 else ("Expert" if rating < 1900 else "Candidate Master")))
        return {"rating": rating, "rank": rank, "max_rating": rating + rng.randint(20, 120), "contests": rng.randint(3, 45)}
