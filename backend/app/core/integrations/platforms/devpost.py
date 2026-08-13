"""Devpost integration — simulated hackathon profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("devpost", "Devpost", "dp", "https://devpost.com/{handle}", "username", False)


class DevpostIntegration(SimulatedPlatformMixin):
    platform_id = "devpost"
    platform_label = "Devpost"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        n = rng.randint(1, 4)
        projects = []
        for i in range(n):
            winners = rng.randint(0, 3)
            projects.append({
                "name": f"Demo Hack Project {i + 1}",
                "likes": rng.randint(0, 120),
                "winning": winners > 0,
                "prizes": winners,
                "built_with": (resume.all_skill_names() if resume else ["Python", "React"])[:4],
            })
        return {"projects": projects, "hackathons_attended": rng.randint(1, 8)}
