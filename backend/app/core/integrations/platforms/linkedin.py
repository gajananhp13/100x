"""LinkedIn integration — simulated profile data (no public API).

Offline demo-data generator producing deterministic, resume-aware stats.
Swap in a real collector in this file only — nothing else changes.
"""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformDef
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("linkedin", "LinkedIn", "li", "https://linkedin.com/in/{handle}", "public profile id", False)


class LinkedInIntegration(SimulatedPlatformMixin):
    platform_id = "linkedin"
    platform_label = "LinkedIn"

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        headline = resume.personal.headline if resume and resume.personal.headline else "Software Developer"
        companies = [e.company for e in ((resume.experience or []) if resume else []) if e.company][:3]
        return {
            "headline": headline,
            "connections": rng.randint(200, 900),
            "current_companies": companies,
            "schools": [e.college for e in ((resume.education or []) if resume else []) if e.college][:2],
            "endorsements": rng.randint(5, 60),
            "activity_visible": bool(rng.randint(0, 1)),
        }
