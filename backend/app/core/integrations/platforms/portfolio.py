"""Portfolio Website integration — simulated profile data (no public API)."""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("portfolio", "Portfolio Website", "pf", "https://{handle}", "example.com", False)


class PortfolioIntegration(SimulatedPlatformMixin):
    platform_id = "portfolio"
    platform_label = "Portfolio Website"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        return {
            "title": f"{resume.personal.name.split()[0] if resume and resume.personal.name else 'Cand'} — Portfolio" if resume and resume.personal.name else "Personal Portfolio",
            "has_blog": bool(rng.randint(0, 1)),
            "sections": rng.randint(3, 6),
            "tech_detected": (resume.all_skill_names() if resume else ["HTML", "CSS"])[:6],
            "last_updated": f"2026-0{rng.randint(1, 7)}",
        }
