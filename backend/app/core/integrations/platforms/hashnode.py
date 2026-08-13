"""Hashnode integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("hashnode", "Hashnode", "hn", "https://hashnode.com/@{handle}", "@username", False)


class HashnodeIntegration(SimulatedPlatformMixin):
    platform_id = "hashnode"
    platform_label = "Hashnode"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {"posts": rng.randint(1, 30), "followers": rng.randint(0, 200), "total_likes": rng.randint(10, 2000)}
