"""Kaggle integration — simulated competition profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("kaggle", "Kaggle", "kg", "https://kaggle.com/{handle}", "username", False)


class KaggleIntegration(SimulatedPlatformMixin):
    platform_id = "kaggle"
    platform_label = "Kaggle"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        bronze = int(level * rng.randint(1, 6))
        silver = int(level * rng.randint(0, 3))
        gold = int(level * rng.randint(0, 2))
        return {
            "tier": "Contributor" if level < 0.4 else ("Expert" if level < 0.75 else "Master"),
            "competitions": rng.randint(1, 12),
            "datasets": rng.randint(0, 8),
            "notebooks": rng.randint(2, 40),
            "medals": {"gold": gold, "silver": silver, "bronze": bronze},
            "followers": rng.randint(1, 300),
        }
