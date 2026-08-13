"""Analysis orchestration — runs the full verification pipeline."""

from __future__ import annotations

from typing import Callable

from ...models.analysis import AnalysisBundle
from ...models.profiles import ConnectedProfile
from ...models.resume import ParsedResume
from ..ai import get_ai_provider
from .coding_analysis import build_coding_analysis
from .github_analysis import build_github_analysis
from .scoring import compute_overall, compute_scores
from .verification import verify_achievements, verify_projects, verify_skills

StageCallback = Callable[[str, str], None]  # (stage, message)


def _noop(stage: str, message: str) -> None:
    pass


def _strengths_and_improvements(bundle: AnalysisBundle) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    improvements: list[str] = []

    top_skills = sorted(bundle.skill_verifications, key=lambda v: v.confidence, reverse=True)[:4]
    for v in top_skills:
        if v.confidence >= 0.8:
            strengths.append(f"Strong, verified skill in {v.technology} (confidence {round(v.confidence * 100)}%, found in public repositories).")
    if bundle.github and bundle.github.repos:
        top_repo = max(bundle.github.repos, key=lambda r: r.stars)
        if top_repo.stars >= 5:
            strengths.append(f"Popular repository '{top_repo.name}' with {top_repo.stars} stars and {top_repo.forks} forks.")
        doc_repos = [r for r in bundle.github.repos if r.readme_quality >= 0.7]
        if doc_repos:
            strengths.append(f"{len(doc_repos)} repository(-ies) with high-quality README documentation.")
        if bundle.github.score_engineering >= 60:
            strengths.append(f"Consistent engineering activity (GitHub engineering score {round(bundle.github.score_engineering)}/100).")
    if bundle.coding and bundle.coding.platforms:
        best = max(bundle.coding.platforms, key=lambda p: p.stats.get("contest_rating", 0))
        if best.stats.get("contest_rating"):
            strengths.append(f"Competitive programming presence on {best.platform_label} (rating {best.stats['contest_rating']}).")
    verified_ach = [a for a in bundle.achievement_verifications if a.status.value in ("verified", "strong_evidence")]
    if verified_ach:
        strengths.append(f"{len(verified_ach)} achievement(s) carry strong public evidence (e.g. '{verified_ach[0].title[:60]}').")

    low_skills = [v.technology for v in bundle.skill_verifications if v.confidence < 0.4 and not v.technology in {"Jira", "Figma", "Postman", "VS Code", "IntelliJ", "Agile", "Scrum"}]
    if low_skills:
        improvements.append(
            f"Technologies with little or no public code evidence: {', '.join(low_skills[:6])} — listed on the resume but not visible in connected repositories."
        )
    unmatched = [p for p in bundle.project_verifications if not p.matched_repo and p.project_name != "(no projects listed)"]
    if unmatched:
        improvements.append(f"{len(unmatched)} project(s) could not be matched to a public repository ({', '.join(p.project_name[:24] for p in unmatched[:3])}).")
    if bundle.github and bundle.github.repos_with_readme < max(bundle.github.public_repos, 1) * 0.7:
        improvements.append("Several repositories lack README documentation, which reduces the documentation score.")
    if bundle.coding and not bundle.coding.platforms:
        improvements.append("No coding platform profiles were connected — competitive programming ability could not be assessed.")
    if not bundle.github:
        improvements.append("No GitHub profile was connected — engineering and open-source evidence is unavailable.")

    return strengths[:6], improvements[:6]


def run_analysis(
    resume: ParsedResume,
    profiles: list[ConnectedProfile],
    on_stage: StageCallback = _noop,
    ai_mode: str | None = None,
) -> AnalysisBundle:
    on_stage("github", "Analyzing GitHub repositories and engineering quality…")
    github_profile = next((p for p in profiles if p.platform == "github" and p.status == "collected"), None)
    github = build_github_analysis(github_profile) if github_profile else None

    on_stage("coding", "Aggregating coding platform statistics…")
    coding = build_coding_analysis(profiles)

    on_stage("skills", "Verifying technical skills against public code…")
    skill_verifications = verify_skills(resume, github)

    on_stage("projects", "Verifying resume projects against repositories…")
    project_verifications = verify_projects(resume, github)

    on_stage("achievements", "Verifying achievements on connected platforms…")
    achievement_verifications = verify_achievements(resume, profiles, github)

    bundle = AnalysisBundle(
        resume=resume,
        profiles=profiles,
        github=github,
        coding=coding,
        skill_verifications=skill_verifications,
        project_verifications=project_verifications,
        achievement_verifications=achievement_verifications,
    )

    on_stage("scoring", "Computing verification scores…")
    bundle.strengths, bundle.improvements = _strengths_and_improvements(bundle)
    bundle.scores = compute_scores(bundle)
    bundle.overall_score = compute_overall(bundle, bundle.scores)

    on_stage("summary", "Writing the AI candidate summary…")
    provider = get_ai_provider(ai_mode)
    bundle.ai_summary = provider.generate_summary(bundle)

    on_stage("done", "Report ready.")
    return bundle
