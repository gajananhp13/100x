"""Bitbucket integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("bitbucket", "Bitbucket", "bb", "https://bitbucket.org/{handle}", "workspace", False)


class BitbucketIntegration(SimulatedPlatformMixin):
    platform_id = "bitbucket"
    platform_label = "Bitbucket"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {
            "workspaces": rng.randint(1, 3),
            "repositories": rng.randint(1, 15),
            "last_activity": f"2026-0{rng.randint(1, 8)}",
        }
