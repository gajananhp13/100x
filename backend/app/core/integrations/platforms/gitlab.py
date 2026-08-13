"""GitLab integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("gitlab", "GitLab", "gl", "https://gitlab.com/{handle}", "username", False)


class GitLabIntegration(SimulatedPlatformMixin):
    platform_id = "gitlab"
    platform_label = "GitLab"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {
            "public_projects": rng.randint(1, 20),
            "followers": rng.randint(0, 80),
            "stars_total": rng.randint(0, 200),
            "last_activity": f"2026-0{rng.randint(1, 8)}",
        }
