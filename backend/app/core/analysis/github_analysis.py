"""Builds the GitHub analysis section from a collected GitHub profile."""

from __future__ import annotations

from datetime import datetime, timezone

from ...models.analysis import GitHubAnalysis, RepoAnalysis
from ...models.profiles import ConnectedProfile


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _repo_quality_score(r: RepoAnalysis) -> float:
    if not r.name:
        return 0.0
    score = 40.0
    if r.has_readme:
        score += 15.0
    score += r.readme_quality * 25.0
    if r.has_ci:
        score += 10.0
    if r.has_dockerfile:
        score += 10.0
    score += min(10.0, r.stars * 2.0)
    score += min(10.0, r.commits_count / 15.0)
    return round(min(100.0, score), 1)


def _recent(r: RepoAnalysis, now: datetime) -> bool:
    pushed = _parse_dt(r.pushed_at)
    return bool(pushed and (now - pushed).days <= 180)


def build_github_analysis(profile: ConnectedProfile) -> GitHubAnalysis | None:
    if not profile or not profile.data:
        return None
    d = profile.data
    repos: list[RepoAnalysis] = []
    for raw in d.get("repos", []):
        if isinstance(raw, dict):
            repos.append(RepoAnalysis(**raw))

    repo_count = len(repos)
    total_commits = d.get("total_commits_fetched", sum(r.commits_count for r in repos))
    now = datetime.now(timezone.utc)

    # --- Repository Quality Score ---
    quality_scores = [_repo_quality_score(r) for r in repos]
    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0.0

    # --- Engineering Score ---
    eng = 0.0
    eng_parts: list[str] = []
    if repo_count:
        commits_per_repo = total_commits / repo_count
        active = sum(1 for r in repos if _recent(r, now))
        activity_ratio = active / repo_count
        lang_breadth = len(d.get("language_usage", {}))
        contributors_total = sum(r.contributors_count for r in repos)
        eng = (
            min(35.0, commits_per_repo * 1.4)          # depth
            + activity_ratio * 30.0                     # recency/activity
            + min(15.0, lang_breadth * 3.0)             # breadth
            + min(20.0, contributors_total * 2.5)       # collaboration
        )
        eng = round(min(100.0, eng), 1)
        eng_parts = [
            f"{round(commits_per_repo, 1)} avg commits/repo",
            f"{active}/{repo_count} repos active in last 6 months",
            f"{lang_breadth} languages",
            f"{contributors_total} total contributors",
        ]

    # --- Open Source Score ---
    stars = d.get("total_stars", sum(r.stars for r in repos))
    forks = d.get("total_forks", sum(r.forks for r in repos))
    followers = d.get("followers", 0)
    oss = round(min(100.0, 20 + min(30.0, stars * 0.3) + min(20.0, forks * 0.8) + min(20.0, followers * 0.3) + repo_count * 2.0), 1)

    # --- Documentation Score ---
    readmes = [r for r in repos if r.has_readme]
    avg_readme = d.get("avg_readme_quality", round(sum(r.readme_quality for r in readmes) / max(len(readmes), 1), 2) if readmes else 0.0)
    licensed = sum(1 for r in repos if r.license_name)
    doc = round(
        min(100.0, avg_readme * 80.0 + (min(20.0, licensed / max(repo_count, 1) * 20.0))),
        1,
    )

    return GitHubAnalysis(
        username=d.get("username", profile.handle),
        avatar_url=d.get("avatar_url"),
        public_repos=d.get("public_repos", repo_count),
        total_stars=stars,
        total_forks=forks,
        followers=followers,
        following=d.get("following", 0),
        account_created_at=d.get("account_created_at"),
        language_usage=d.get("language_usage", {}),
        repos=repos,
        repos_with_ci=d.get("repos_with_ci", 0),
        repos_with_docker=d.get("repos_with_docker", 0),
        repos_with_readme=len(readmes),
        avg_readme_quality=round(float(avg_readme), 2),
        avg_commits_per_repo=round(total_commits / max(repo_count, 1), 1),
        score_engineering=eng,
        score_repo_quality=avg_quality,
        score_open_source=oss,
        score_documentation=doc,
    )
