"""Aggregates all coding platform profiles into a combined problem-solving score."""

from __future__ import annotations

from ...models.analysis import CodingAnalysis, CodingPlatformProfile
from ...models.profiles import ConnectedProfile
from ..integrations.registry import PLATFORM_BY_ID

CODING_PLATFORMS = ("leetcode", "codeforces", "codechef", "geeksforgeeks", "hackerrank", "kaggle")

# (platform, weight, extractor) — extractor returns a 0..100 sub-score or None
_SCORERS: dict[str, tuple[float]] = {
    "leetcode": (0.30,),
    "codeforces": (0.25,),
    "codechef": (0.15,),
    "geeksforgeeks": (0.15,),
    "hackerrank": (0.10,),
    "kaggle": (0.05,),
}


def _norm(value: float, cap: float, scale: float = 1.0) -> float:
    return max(0.0, min(100.0, value / cap * 100.0 * scale))


def _score_leetcode(s: dict) -> float:
    total = int(s.get("total_solved", 0) or 0)
    rating = int(s.get("contest_rating", 0) or 0)
    base = _norm(total, 600) * 0.7
    rating_part = _norm(rating, 2600) * 0.25
    streak = _norm(int(s.get("streak_days", 0) or 0), 120) * 0.05
    return round(base + rating_part + streak, 1)


def _score_codeforces(s: dict) -> float:
    rating = int(s.get("rating", 0) or 0)
    return round(_norm(rating, 3000) * 0.9 + _norm(int(s.get("contests", 0) or 0), 50) * 0.1, 1)


def _score_codechef(s: dict) -> float:
    rating = int(s.get("rating", 0) or 0)
    return round(_norm(rating, 2700) * 0.9 + _norm(int(s.get("problems_solved", 0) or 0), 500) * 0.1, 1)


def _score_geeksforgeeks(s: dict) -> float:
    return round(_norm(int(s.get("coding_score", 0) or 0), 900), 1)


def _score_hackerrank(s: dict) -> float:
    stars = int(s.get("stars", 0) or 0)
    certs = int(s.get("certificates", 0) or 0)
    return round(_norm(stars, 5) * 0.7 + _norm(certs, 3) * 0.3, 1)


def _score_kaggle(s: dict) -> float:
    medals = s.get("medals", {}) or {}
    comps = int(s.get("competitions", 0) or 0)
    med_val = (medals.get("gold", 0) * 3 + medals.get("silver", 0) * 2 + medals.get("bronze", 0)) / 6
    return round(_norm(med_val, 4) * 0.7 + _norm(comps, 12) * 0.3, 1)


_SCORERS_IMPL = {
    "leetcode": _score_leetcode,
    "codeforces": _score_codeforces,
    "codechef": _score_codechef,
    "geeksforgeeks": _score_geeksforgeeks,
    "hackerrank": _score_hackerrank,
    "kaggle": _score_kaggle,
}


def build_coding_analysis(profiles: list[ConnectedProfile]) -> CodingAnalysis | None:
    by_platform: dict[str, ConnectedProfile] = {p.platform: p for p in profiles if p.status == "collected"}
    platform_profiles: list[CodingPlatformProfile] = []
    scored: list[tuple[float, float]] = []

    for pid in CODING_PLATFORMS:
        prof = by_platform.get(pid)
        if not prof:
            continue
        pdef = PLATFORM_BY_ID.get(pid)
        label = pdef.label if pdef else pid
        url = prof.profile_url or ""
        platform_profiles.append(
            CodingPlatformProfile(platform=pid, platform_label=label, handle=prof.handle, url=url, stats=prof.data)
        )
        scorer = _SCORERS_IMPL.get(pid)
        if scorer:
            sub = scorer(prof.data)
            scored.append((sub, _SCORERS[pid][0]))

    if not scored:
        return CodingAnalysis(platforms=[], problem_solving_score=0.0, explanation="No coding platform profiles were connected.")

    raw_total = sum(sub * w for sub, w in scored)
    weight_sum = sum(w for _, w in scored)
    score = round(raw_total / weight_sum, 1)

    # participation bonus: more platforms connected -> higher confidence in the aggregate
    coverage = len(scored) / len(CODING_PLATFORMS)
    final = round(score * (0.75 + 0.25 * coverage), 1)

    parts = [
        f"{label}: {sub}/100" for (sub, _), label in
        zip(scored, [PLATFORM_BY_ID[p.platform].label for p in platform_profiles if p.platform in PLATFORM_BY_ID])
    ]
    explanation = (
        f"Weighted aggregate across {len(scored)} connected platform(s) "
        f"({', '.join(parts)}); final score adjusted {round((0.75 + 0.25 * coverage) * 100)}% for platform coverage."
    )
    return CodingAnalysis(platforms=platform_profiles, problem_solving_score=final, explanation=explanation)
