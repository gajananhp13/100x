"""Stack Overflow integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("stackoverflow", "Stack Overflow", "so", "https://stackoverflow.com/users/{handle}", "user id", False)


class StackOverflowIntegration(SimulatedPlatformMixin):
    platform_id = "stackoverflow"
    platform_label = "Stack Overflow"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {
            "reputation": int(level * rng.randint(200, 6000)),
            "badges": {"gold": rng.randint(0, 3), "silver": rng.randint(0, 12), "bronze": rng.randint(0, 40)},
            "answers": rng.randint(0, 80),
            "questions": rng.randint(0, 30),
            "top_tags": (resume.all_skill_names() if resume else ["java", "python"])[:4],
        }
