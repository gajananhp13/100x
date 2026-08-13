"""Scoring engine: 10 named 0-100 scores, each with a documented formula and
a plain-language explanation of how it was calculated.

Absence of connected profiles contributes 0 to profile-dependent scores and is
explained, never penalised as dishonesty.
"""

from __future__ import annotations

from ...models.analysis import (
    AnalysisBundle,
    CodingAnalysis,
    GitHubAnalysis,
    ScoreItem,
    VerificationStatus,
    status_from_confidence,
)
from ...models.resume import ParsedResume

_STATUS_VALUE = {
    VerificationStatus.verified: 1.0,
    VerificationStatus.strong_evidence: 0.8,
    VerificationStatus.partial_evidence: 0.6,
    VerificationStatus.limited_evidence: 0.4,
    VerificationStatus.no_public_evidence: 0.15,
}


def _score_resume_completeness(resume: ParsedResume) -> ScoreItem:
    p = resume.personal
    parts = 0.0
    total = 8.0
    if p.name:
        parts += 1
    if p.email:
        parts += 1
    if p.phone:
        parts += 1
    if p.location:
        parts += 1
    if p.portfolio or p.github or p.linkedin:
        parts += 1
    if resume.education:
        parts += 2
    if resume.experience:
        parts += 1.5
    if resume.projects:
        parts += 1
    if resume.achievements:
        parts += 0.5
    value = round(min(100.0, parts / total * 100.0), 1)
    detail = []
    detail.append("name" if p.name else "no name")
    detail.append("contact" if p.email or p.phone else "no contact")
    detail.append(f"{len(resume.education)} education" if resume.education else "no education")
    detail.append(f"{len(resume.experience)} experience entries" if resume.experience else "no experience")
    detail.append(f"{len(resume.projects)} projects" if resume.projects else "no projects")
    detail.append(f"{len(resume.achievements)} achievements" if resume.achievements else "no achievements")
    explanation = f"Coverage of core resume sections ({'; '.join(detail)}). {round(parts / total * 100)}% of expected content present."
    return ScoreItem(key="resume_completeness", label="Resume Completeness Score", value=value, explanation=explanation)


def _score_resume_credibility(bundle: AnalysisBundle) -> ScoreItem:
    skills = bundle.skill_verifications
    projects = bundle.project_verifications
    achievements = bundle.achievement_verifications

    def avg(items) -> float:
        if not items:
            return 0.15
        return sum(_STATUS_VALUE[i.status] for i in items) / len(items)

    s_val, p_val, a_val = avg(skills), avg(projects), avg(achievements)
    value = round(min(100.0, (s_val * 0.4 + p_val * 0.35 + a_val * 0.25) * 100.0), 1)
    detail = (
        f"Skills {round(s_val * 100)}%, projects {round(p_val * 100)}%, "
        f"achievements {round(a_val * 100)}% (status-weighted means; no-evidence counts as {round(_STATUS_VALUE[VerificationStatus.no_public_evidence] * 100)}%, never as absence)."
    )
    return ScoreItem(key="resume_credibility", label="Resume Credibility Score", value=value,
                     explanation=f"Weighted average of verification status across {len(skills)} skills, {len(projects)} projects, {len(achievements)} achievements. {detail}")


def _score_technical_skills(bundle: AnalysisBundle) -> ScoreItem:
    sv = bundle.skill_verifications
    if not sv:
        return ScoreItem(key="technical_skills", label="Technical Skills Score", value=0.0,
                         explanation="No skills were parsed from the resume.")
    mean_conf = sum(v.confidence for v in sv) / len(sv)
    strong = sum(1 for v in sv if v.status in (VerificationStatus.verified, VerificationStatus.strong_evidence))
    breadth = min(1.0, strong / 12.0)
    value = round(min(100.0, (mean_conf * 0.75 + breadth * 0.25) * 100.0), 1)
    return ScoreItem(
        key="technical_skills", label="Technical Skills Score", value=value,
        explanation=f"Mean code-evidence confidence of {len(sv)} parsed skills is {round(mean_conf * 100)}%; {strong} skills have strong or better evidence (breadth factor {round(breadth * 100)}%).",
    )


def _score_github_engineering(bundle: AnalysisBundle) -> ScoreItem:
    g = bundle.github
    if not g:
        return ScoreItem(key="github_engineering", label="GitHub Engineering Score", value=0.0,
                         explanation="No GitHub profile was connected, so engineering activity could not be measured.")
    value = round(min(100.0, g.score_engineering), 1)
    return ScoreItem(key="github_engineering", label="GitHub Engineering Score", value=value,
                     explanation=f"Aggregated commit depth, repository activity, language breadth and contributors across {g.public_repos} repositories ({round(g.avg_commits_per_repo)} avg commits/repo).")


def _score_coding_platform(bundle: AnalysisBundle) -> ScoreItem:
    c = bundle.coding
    if not c or not c.platforms:
        return ScoreItem(key="coding_platform", label="Coding Platform Score", value=0.0,
                         explanation="No coding platform profiles were connected (LeetCode, Codeforces, etc.).")
    return ScoreItem(key="coding_platform", label="Coding Platform Score", value=c.problem_solving_score,
                     explanation=c.explanation)


def _score_project_quality(bundle: AnalysisBundle) -> ScoreItem:
    pv = [p for p in bundle.project_verifications if p.project_name != "(no projects listed)"]
    if not pv:
        return ScoreItem(key="project_quality", label="Project Quality Score", value=0.0,
                         explanation="No projects were listed on the resume.")
    mean = sum(p.score for p in pv) / len(pv)
    matched = sum(1 for p in pv if p.matched_repo)
    return ScoreItem(key="project_quality", label="Project Quality Score", value=round(mean, 1),
                     explanation=f"Average verification score of {len(pv)} listed projects ({matched} matched to a public repository), covering repo existence, deployment, recency, documentation and architecture complexity.")


def _score_open_source(bundle: AnalysisBundle) -> ScoreItem:
    g = bundle.github
    if not g:
        return ScoreItem(key="open_source", label="Open Source Score", value=0.0,
                         explanation="No GitHub profile was connected.")
    return ScoreItem(key="open_source", label="Open Source Score", value=g.score_open_source,
                     explanation=f"Based on {g.total_stars} stars, {g.total_forks} forks, {g.followers} followers and {g.public_repos} public repositories.")


def _score_documentation(bundle: AnalysisBundle) -> ScoreItem:
    g = bundle.github
    if not g:
        return ScoreItem(key="documentation", label="Documentation Score", value=0.0,
                         explanation="No GitHub profile was connected.")
    return ScoreItem(key="documentation", label="Documentation Score", value=g.score_documentation,
                     explanation=f"Average README quality of {g.repos_with_readme}/{g.public_repos} repositories ({round(g.avg_readme_quality * 100)}%) plus license coverage.")


def _score_learning_consistency(bundle: AnalysisBundle) -> ScoreItem:
    g = bundle.github
    detail: list[str] = []
    value = 0.0
    if g:
        active = sum(1 for r in g.repos if r.commits_count > 0)
        value += min(50.0, active / max(g.public_repos, 1) * 50.0)
        recent = 0
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for r in g.repos:
            try:
                pushed = datetime.fromisoformat((r.pushed_at or "").replace("Z", "+00:00"))
                if (now - pushed).days <= 120:
                    recent += 1
            except ValueError:
                pass
        value += min(30.0, recent / max(g.public_repos, 1) * 30.0)
        value += min(20.0, g.avg_commits_per_repo * 1.5)
        detail.append(f"{recent}/{g.public_repos} repos touched in last 4 months")
        detail.append(f"{round(g.avg_commits_per_repo)} avg commits/repo")
    coding = bundle.coding
    if coding and coding.platforms:
        streaks = [p.stats.get("streak_days", 0) for p in coding.platforms if p.stats.get("streak_days")]
        if streaks:
            value += min(10.0, max(streaks) / 12.0)
            detail.append(f"longest platform streak {max(streaks)} days")
    if not g and not coding:
        return ScoreItem(key="learning_consistency", label="Learning Consistency Score", value=0.0,
                         explanation="No connected activity data (GitHub or coding platforms) to measure consistency.")
    return ScoreItem(key="learning_consistency", label="Learning Consistency Score", value=round(min(100.0, value), 1),
                     explanation="Estimated from sustained activity: " + ("; ".join(detail) if detail else "no signals") + ".")


def compute_scores(bundle: AnalysisBundle) -> list[ScoreItem]:
    return [
        _score_resume_completeness(bundle.resume),
        _score_resume_credibility(bundle),
        _score_technical_skills(bundle),
        _score_github_engineering(bundle),
        _score_coding_platform(bundle),
        _score_project_quality(bundle),
        _score_open_source(bundle),
        _score_documentation(bundle),
        _score_learning_consistency(bundle),
    ]


OVERALL_WEIGHTS = {
    "resume_credibility": 0.25,
    "technical_skills": 0.2,
    "github_engineering": 0.15,
    "project_quality": 0.15,
    "coding_platform": 0.1,
    "resume_completeness": 0.08,
    "learning_consistency": 0.07,
}


def compute_overall(bundle: AnalysisBundle, scores: list[ScoreItem]) -> float:
    by_key = {s.key: s.value for s in scores}
    total = 0.0
    weight_sum = 0.0
    for key, weight in OVERALL_WEIGHTS.items():
        if key in by_key:
            total += by_key[key] * weight
            weight_sum += weight
    if not weight_sum:
        return 0.0
    return round(min(100.0, total / weight_sum), 1)
