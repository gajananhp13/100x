"""Aggregates all coding platform profiles into a combined DSA Depth Score (0-100).

Implements the spec: difficulty-weighted quality + contest global ranking over raw
volume. No breadth bonus — score is a weighted average; only a tiny
corroboration bonus (max +4) for multiple strong profiles.
"""

from __future__ import annotations

import math
import statistics

from ...models.analysis import CodingAnalysis, CodingPlatformProfile
from ...models.profiles import ConnectedProfile
from ..integrations.registry import PLATFORM_BY_ID

CODING_PLATFORMS = ("leetcode", "codeforces", "codechef", "geeksforgeeks", "hackerrank")

# Static aggregation weights per spec §10.
_SCORERS: dict[str, tuple[float]] = {
    "leetcode": (0.30,),
    "codeforces": (0.30,),
    "codechef": (0.15,),
    "hackerrank": (0.15,),
    "geeksforgeeks": (0.10,),
}

# ---------------------------------------------------------------------------
# Normalization helpers — §2.1
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _linear_norm(value: float, cap: float) -> float:
    """linear_norm(v,cap) = clamp(v/cap*100, 0,100)."""
    if cap <= 0:
        return 0.0
    return _clamp(value / cap * 100.0)


def _log_norm(value: float, ref: float) -> float:
    """log_norm(v,ref) = clamp(100*log(1+v)/log(1+ref),0,100). Diminishing returns."""
    if ref <= 0 or value <= 0:
        return 0.0
    return _clamp(100.0 * math.log1p(value) / math.log1p(ref))


def _percentile_score(pct: float) -> float:
    """Lower pct (top%) is better. top 1% ~90, top 5% ~78, top 20% ~55."""
    p = _clamp(pct, 0, 100) / 100.0
    return _clamp(100.0 * (1.0 - math.sqrt(p)))


def _exp_rating_score(rating: float, cap: float = 2600.0) -> float:
    """Contest rating -> 0..100 via 1-exp(-r/1200) scaled to cap."""
    if rating <= 0:
        return 0.0
    denom = 1.0 - math.exp(-cap / 1200.0)
    if denom <= 0:
        return 0.0
    return _clamp(100.0 * (1.0 - math.exp(-rating / 1200.0)) / denom)


def _weighted_avg(pairs: list[tuple[float | None, float]]) -> float | None:
    """Weighted average over non-None values. Returns None if no evidence."""
    num = 0.0
    den = 0.0
    for val, w in pairs:
        if val is not None:
            num += val * w
            den += w
    if den == 0:
        return None
    return num / den


# ---------------------------------------------------------------------------
# Per-platform sub-scores — §2.2-2.6
# ---------------------------------------------------------------------------

def _score_leetcode(s: dict) -> float:
    """LeetCode: 35% difficulty quality, 45% competitive, 10% depth, 10% quality signal."""
    easy = int(s.get("easy", 0) or 0)
    medium = int(s.get("medium", 0) or 0)
    hard = int(s.get("hard", 0) or 0)
    total = easy + medium + hard

    # --- Difficulty quality (35%) ---
    difficulty_points = 1.0 * easy + 3.0 * medium + 7.0 * hard
    vol_quality = _log_norm(difficulty_points, 2500)
    mix_quality = 100.0 * (0.6 * math.sqrt(min(medium / 250.0, 1.0)) + 0.4 * math.sqrt(min(hard / 100.0, 1.0)))
    raw_diff = 0.60 * vol_quality + 0.40 * mix_quality

    advanced_ratio = (medium + hard) / max(total, 1)
    difficulty_gate = 0.55 + 0.45 * min(advanced_ratio / 0.55, 1.0) if total > 0 else 0.55
    difficulty_quality = raw_diff * difficulty_gate
    # Threshold cap — tiny sample cannot claim mastery
    if (medium + hard) < 20:
        difficulty_quality = min(difficulty_quality, 70.0)
    # Hard-depth cap: if very few hard solves, limit extra
    # (spec: "If H < 10, cap hard-depth" — we enforce via mix already low, no extra hard cap needed)
    difficulty_quality = _clamp(difficulty_quality)

    # --- Competitive (45%) ---
    rating = int(s.get("contest_rating", 0) or 0)
    top_pct = s.get("top_percentage", None)
    try:
        top_pct_f = float(top_pct) if top_pct is not None else 0.0
    except (TypeError, ValueError):
        top_pct_f = 0.0
    attended = int(s.get("attended_contests", 0) or 0)
    # Also handle legacy field contest_rank / global_ranking
    if attended == 0:
        # try global_ranking as proxy
        if int(s.get("global_ranking", 0) or 0) > 0:
            attended = 1  # has contest history
    rating_score = _exp_rating_score(float(rating), 2600) if rating > 0 else None
    rank_score = _percentile_score(top_pct_f) if top_pct_f > 0 else None
    comp_base = _weighted_avg([(rating_score, 0.55), (rank_score, 0.45)])
    if comp_base is None:
        comp_score = None
    else:
        # contest count contributes 10% as consistency
        comp_score = 0.90 * comp_base + 0.10 * _log_norm(float(attended), 20)
        comp_score = _clamp(comp_score)

    # --- Depth / consistency (10%) ---
    # Always valid, even if total==0 -> 0
    depth = 0.70 * _log_norm(float(total), 600) + 0.30 * _log_norm(float(attended), 20)
    depth = _clamp(depth)

    # --- Reliability / quality signal (10%) ---
    acc = s.get("acceptance_rate", None)
    try:
        acc_f = float(acc) if acc is not None else None
    except (TypeError, ValueError):
        acc_f = None
    if acc_f is not None and acc_f > 0:
        accept_score = _clamp(acc_f / 85.0 * 100.0)
    else:
        accept_score = None
    streak = int(s.get("streak_days", 0) or 0)
    streak_score = _log_norm(float(streak), 150) if streak > 0 else None
    attended_score = _log_norm(float(attended), 20) if attended > 0 else None
    qs = _weighted_avg([(accept_score, 0.50), (streak_score, 0.20), (attended_score, 0.30)])
    quality_signal = qs if qs is not None else 50.0

    # --- Final LC aggregation with graceful missing-data handling ---
    # If comp is missing, redistribute its weight.
    components: list[tuple[float | None, float]] = [
        (difficulty_quality, 0.35),
        (comp_score, 0.45),
        (depth, 0.10),
        (quality_signal, 0.10),
    ]
    available = [(v, w) for v, w in components if v is not None]
    if not available:
        return 0.0
    # Weighted average then scale to 0..100; but spec says clamp(weights sum to 1 when present)
    # So we compute weighted avg and if any component missing, weights are renormalized.
    # Equivalent to weighted_avg then not scaled. However original formula is
    # 0.35*diff+0.45*comp+..., which sums to 1 when all present. When comp missing,
    # redistribute -> divide by sum of available weights.
    total_w = sum(w for _, w in available)
    raw = sum(v * w for v, w in available) / total_w

    # Vol-only fallback: if no contest AND no medium/hard, this is pure volume
    is_vol_only = (comp_score is None and (medium + hard) == 0 and total > 0)
    if is_vol_only:
        raw = min(raw, 65.0)

    return round(_clamp(raw), 1)


def _score_codeforces(s: dict) -> float:
    """Codeforces: 60% current rating, 25% peak, 15% contests. §2.3"""
    rating = int(s.get("rating", 0) or 0)
    max_rating = int(s.get("max_rating", 0) or rating)
    contests = int(s.get("contests", 0) or 0)
    # If no rating at all -> no evidence
    if rating <= 0 and max_rating <= 0:
        # try generic contest_rating
        rating = int(s.get("contest_rating", 0) or 0)
        max_rating = rating
    cf_rating = _exp_rating_score(float(rating), 2600) if rating > 0 else None
    cf_peak = _exp_rating_score(float(max_rating), 2600) if max_rating > 0 else None
    cf_cont = _log_norm(float(contests), 25)
    # contests always contributes but diminishing
    # If both rating and peak missing, treat as volume-only -> cap 65
    if cf_rating is None and cf_peak is None:
        return round(min(cf_cont, 65.0), 1)
    comp = _weighted_avg([(cf_rating, 0.60), (cf_peak, 0.25)])
    if comp is None:
        return round(_clamp(cf_cont), 1)
    score = 0.85 * comp + 0.15 * cf_cont if comp is not None else cf_cont
    # Actually spec: 0.60*rating +0.25*peak +0.15*cont  -> we recompute as weighted over 1.0
    score = _clamp((cf_rating or 0) * 0.60 + (cf_peak or 0) * 0.25 + cf_cont * 0.15)
    return round(score, 1)


def _score_codechef(s: dict) -> float:
    """CodeChef: 65% rating, 25% stars, 10% contests. §2.4"""
    rating = int(s.get("rating", 0) or 0)
    stars = int(s.get("stars", 0) or 0)
    contests = int(s.get("contests", 0) or 0)
    cc_rating = _exp_rating_score(float(rating), 2500) if rating > 0 else None
    star_score = _linear_norm(float(stars), 7) if stars > 0 else None
    cc_cont = _log_norm(float(contests), 20)
    # If only contests/volume and no rating/stars -> vol-only cap
    if cc_rating is None and star_score is None:
        return round(min(cc_cont, 65.0), 1)
    # Fill missing with weighted avg renormalization
    pairs: list[tuple[float | None, float]] = [
        (cc_rating, 0.65),
        (star_score, 0.25),
        (cc_cont if contests > 0 else None, 0.10),
    ]
    # If contests==0 we omit cont to not drag down; else include
    if contests == 0:
        pairs = [(cc_rating, 0.65), (star_score, 0.25)]
    avg = _weighted_avg(pairs)
    if avg is None:
        return 0.0
    # Re-scale to 0..100 with available weights considered; but spec weights sum to 1
    # If contests missing we already renormalized via _weighted_avg denominator.
    # Need to reconstruct as sum(v*w)/total_w = avg ; _weighted_avg already does that.
    # However original intent is 0.65+0.25+0.10 =1 when all present; missing -> renormalize
    return round(_clamp(avg), 1)


def _score_geeksforgeeks(s: dict) -> float:
    """GFG: 75% coding_score (out of 1200), 25% volume, capped at 80. §2.6"""
    coding_score = int(s.get("coding_score", 0) or 0)
    problems = int(s.get("problems_solved", 0) or s.get("total_solved", 0) or 0)
    # coding_score normalization cap 1200 per spec (table says 12.0 typo -> 1200)
    cs = _linear_norm(float(coding_score), 1200) if coding_score else None
    vol = _log_norm(float(problems), 500) if problems else None
    if cs is None and vol is None:
        return 0.0
    if cs is None:
        raw = min(vol or 0, 60.0)
        return round(_clamp(raw), 1)
    if vol is None:
        raw = cs * 1.0
        return round(_clamp(min(raw, 80.0)), 1)
    raw = _weighted_avg([(cs, 0.75), (vol, 0.25)])
    if raw is None:
        return 0.0
    return round(_clamp(min(raw, 80.0)), 1)


def _score_hackerrank(s: dict) -> float:
    """HackerRank: 50% contest, 25% stars, 15% badges, 10% volume — capped at 90. §2.5"""
    contest_rating = int(s.get("contest_rating", 0) or s.get("rating", 0) or 0)
    stars = int(s.get("stars", 0) or 0)
    total_badges = int(s.get("total_badges", 0) or s.get("certificates", 0) or 0)
    problems = int(s.get("problems_solved", 0) or s.get("total_solved", 0) or 0)

    hr_rating = _exp_rating_score(float(contest_rating), 2200) if contest_rating > 0 else None
    star_score = _linear_norm(float(stars), 5) if stars > 0 else None
    badge_score = _log_norm(float(total_badges), 15) if total_badges > 0 else None
    hr_vol = _log_norm(float(problems), 300) if problems > 0 else None

    # If contest missing, redistribute weight per spec
    components: list[tuple[float | None, float]] = [
        (hr_rating, 0.50),
        (star_score, 0.25),
        (badge_score, 0.15),
        (hr_vol, 0.10),
    ]
    available = [(v, w) for v, w in components if v is not None]
    if not available:
        return 0.0
    # Vol-only detection: only HR vol/badges without contest/stars
    is_vol_only = hr_rating is None and star_score is None
    total_w = sum(w for _, w in available)
    raw = sum(v * w for v, w in available) / total_w
    raw = _clamp(raw)
    if is_vol_only:
        raw = min(raw, 60.0)
    else:
        raw = min(raw, 90.0)
    return round(raw, 1)


_SCORERS_IMPL = {
    "leetcode": _score_leetcode,
    "codeforces": _score_codeforces,
    "codechef": _score_codechef,
    "geeksforgeeks": _score_geeksforgeeks,
    "hackerrank": _score_hackerrank,
}


# ---------------------------------------------------------------------------
# Legacy helper kept for import compatibility
# ---------------------------------------------------------------------------

def _norm(value: float, cap: float, scale: float = 1.0) -> float:
    return max(0.0, min(100.0, value / cap * 100.0 * scale))


def _platform_detail(pid: str, s: dict) -> str:
    if pid == "leetcode":
        easy = int(s.get("easy", 0) or 0)
        medium = int(s.get("medium", 0) or 0)
        hard = int(s.get("hard", 0) or 0)
        total = easy + medium + hard
        mix = f"{(medium + hard) / total * 100:.0f}%" if total else "0%"
        top_pct = s.get("top_percentage", None)
        try:
            tp = float(top_pct) if top_pct is not None else 0.0
        except (TypeError, ValueError):
            tp = 0.0
        rank = f"top {tp:.1f}%" if tp > 0 else "no contest"
        cr = int(s.get("contest_rating", 0) or 0)
        return f"LeetCode {easy}E/{medium}M/{hard}H (M+H {mix}, rating {cr}, {rank})"
    if pid == "codeforces":
        rating = int(s.get("rating", 0) or 0)
        return f"Codeforces rating {rating}"
    if pid == "codechef":
        stars = int(s.get("stars", 0) or 0)
        rating = int(s.get("rating", 0) or 0)
        return f"CodeChef {stars}★ (rating {rating})"
    if pid == "geeksforgeeks":
        return f"GeeksforGeeks coding score {int(s.get('coding_score', 0) or 0)}"
    if pid == "hackerrank":
        stars = int(s.get("stars", 0) or 0)
        return f"HackerRank {stars}★"
    return pid


def _corroboration_bonus(scores: list[float]) -> float:
    """Spec §3: small bonus if ≥2 strong platforms (≥75) that agree."""
    strong = [s for s in scores if s >= 75.0]
    k = len(strong)
    if k <= 1:
        return 0.0
    # agreement factor: high if scores have low spread
    try:
        sd = statistics.pstdev(strong) if len(strong) > 1 else 0.0
    except statistics.StatisticsError:
        sd = 0.0
    agree = 1.0 - (sd / 25.0)
    agree = _clamp(agree, 0.0, 1.0)
    bonus = 4.0 * (1.0 - math.exp(-0.9 * (k - 1))) * agree
    return round(bonus, 1)


def build_coding_analysis(profiles: list[ConnectedProfile]) -> CodingAnalysis | None:
    by_platform: dict[str, ConnectedProfile] = {p.platform: p for p in profiles if p.status == "collected"}
    platform_profiles: list[CodingPlatformProfile] = []
    scored: list[tuple[float, float]] = []  # (sub_score, weight)
    details: list[str] = []
    raw_scores: list[float] = []

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
            w = _SCORERS[pid][0]
            scored.append((sub, w))
            raw_scores.append(sub)
            details.append(f"{_platform_detail(pid, prof.data)} -> {sub}/100")

    if not scored:
        return CodingAnalysis(platforms=[], problem_solving_score=0.0, explanation="No coding platform profiles were connected.")

    # Weighted average — no breadth multiplication.
    raw_total = sum(sub * w for sub, w in scored)
    weight_sum = sum(w for _, w in scored)
    base = round(raw_total / weight_sum, 1) if weight_sum else 0.0

    bonus = _corroboration_bonus(raw_scores)
    final = _clamp(base + bonus)

    # Explanation per spec §9
    # Derive overall difficulty mix hint when LeetCode present
    mix_hint = ""
    for pp in platform_profiles:
        if pp.platform == "leetcode":
            e = int(pp.stats.get("easy", 0) or 0)
            m = int(pp.stats.get("medium", 0) or 0)
            h = int(pp.stats.get("hard", 0) or 0)
            tot = e + m + h
            if tot:
                pct = (m + h) / tot * 100
                mix_hint = f" {pct:.0f}% of solved problems are Medium/Hard."
                if h >= 20:
                    mix_hint += " Substantial Hard depth."
            break

    rank_hint = ""
    for pp in platform_profiles:
        tp = pp.stats.get("top_percentage", None)
        try:
            tp_f = float(tp) if tp is not None else 0
        except (TypeError, ValueError):
            tp_f = 0
        if tp_f > 0:
            cr = int(pp.stats.get("contest_rating", 0) or pp.stats.get("rating", 0) or 0)
            rank_hint = f" Ranks top {tp_f:.1f}% globally" + (f" (rating {cr})." if cr else ".")
            break

    bonus_note = f" Corroboration bonus +{bonus} for {len([s for s in raw_scores if s>=75])} strong profiles." if bonus else ""
    explanation = (
        f"Quality-weighted DSA Depth Score{bonus_note}."
        + mix_hint
        + rank_hint
        + f" {'; '.join(details)}."
        + f" Aggregate of {len(scored)} profile(s) — score reflects DSA depth, not platform count. Base {base}/100."
    )
    return CodingAnalysis(platforms=platform_profiles, problem_solving_score=float(final), explanation=explanation)
