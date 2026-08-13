"""Shared simulation machinery for platform integrations.

Every platform integration lives in its own module under core/integrations/platforms/.
Real integrations (GitHub, LeetCode) subclass SimulatedPlatformMixin too, so they can
fall back to deterministic demo data when `simulate=True` (used by the offline demo
candidate). Pure-simulated platforms (LinkedIn, Codeforces, ...) simply override
`_simulate()` and inherit everything else.
"""

from __future__ import annotations

import random

from ....models.resume import ParsedResume
from ..base import PlatformIntegration, ProfileCollectError


class SimulatedPlatformMixin:
    """Deterministic demo-data generator shared by every platform integration."""

    real_api: bool = False

    def __init__(self, simulate: bool = False) -> None:
        self.simulate = simulate

    # ------------------------------------------------------------------ #
    # Simulation machinery
    # ------------------------------------------------------------------ #

    def _rng(self, handle: str) -> random.Random:
        return random.Random(f"100x-mock-{self.platform_id}-{handle.strip().lower()}")

    def _candidate_level(self, resume: ParsedResume | None) -> float:
        """0..1 rough seniority estimate used to scale demo stats."""
        if resume is None:
            return 0.5
        years = 0.0
        for exp in resume.experience:
            if exp.duration:
                nums = [int(n) for n in exp.duration if n.isdigit()]
                if len(nums) >= 2:
                    years += max(0.0, nums[-1] - nums[0])
        coding_claims = sum(1 for a in resume.achievements if a.type == "coding")
        return min(1.0, 0.3 + years * 0.12 + coding_claims * 0.05)

    def _simulated_collect(self, handle: str, context: dict | None = None) -> dict:
        handle = handle.strip()
        if not handle or len(handle) < 2:
            raise ProfileCollectError("Handle must be at least 2 characters.")
        rng = self._rng(handle)
        resume: ParsedResume | None = context.get("resume") if context else None
        data = self._simulate(rng, self._candidate_level(resume), resume, handle)
        data["_source"] = "mock"
        data["_warning"] = "Simulated demo data — connect the real platform API for production evidence."
        return data

    # ------------------------------------------------------------------ #
    # Dispatch
    # ------------------------------------------------------------------ #

    def collect(self, handle: str, context: dict | None = None) -> dict:
        if self.real_api and not self.simulate:
            return self._collect_real(handle, context)
        return self._simulated_collect(handle, context)

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        """Live-API collection — override in real integrations."""
        raise NotImplementedError(
            f"{self.platform_id} has no live API integration yet; "
            "use build_integration(id, force_mock=True) for demo data."
        )

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str,
    ) -> dict:
        """Per-platform demo data generator — override in every integration."""
        raise NotImplementedError(f"{self.platform_id} has no simulator registered.")
