from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .profiles import ConnectedProfile
from .resume import ParsedResume


class VerificationStatus(str, Enum):
    verified = "verified"
    strong_evidence = "strong_evidence"
    partial_evidence = "partial_evidence"
    limited_evidence = "limited_evidence"
    no_public_evidence = "no_public_evidence"


STATUS_ORDER: dict[VerificationStatus, int] = {
    VerificationStatus.verified: 5,
    VerificationStatus.strong_evidence: 4,
    VerificationStatus.partial_evidence: 3,
    VerificationStatus.limited_evidence: 2,
    VerificationStatus.no_public_evidence: 1,
}


def status_from_confidence(confidence: float) -> VerificationStatus:
    if confidence >= 0.8:
        return VerificationStatus.verified
    if confidence >= 0.6:
        return VerificationStatus.strong_evidence
    if confidence >= 0.4:
        return VerificationStatus.partial_evidence
    if confidence >= 0.2:
        return VerificationStatus.limited_evidence
    return VerificationStatus.no_public_evidence


class TechnologyVerification(BaseModel):
    technology: str
    category: str
    confidence: float  # 0..1
    status: VerificationStatus
    evidence: list[str] = Field(default_factory=list)


class RepoAnalysis(BaseModel):
    name: str
    full_name: str
    description: str | None = None
    html_url: str
    homepage: str | None = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    language: str | None = None
    languages: dict[str, float] = Field(default_factory=dict)
    license_name: str | None = None
    topics: list[str] = Field(default_factory=list)
    created_at: str | None = None
    pushed_at: str | None = None
    has_readme: bool = False
    readme_quality: float = 0.0  # 0..1
    has_ci: bool = False
    has_dockerfile: bool = False
    commits_count: int = 0
    contributors_count: int = 0
    open_prs: int = 0
    is_fork: bool = False
    tech_hits: dict[str, float] = Field(default_factory=dict)  # tech -> evidence confidence


class GitHubAnalysis(BaseModel):
    username: str
    avatar_url: str | None = None
    public_repos: int = 0
    total_stars: int = 0
    total_forks: int = 0
    followers: int = 0
    following: int = 0
    account_created_at: str | None = None
    language_usage: dict[str, float] = Field(default_factory=dict)
    repos: list[RepoAnalysis] = Field(default_factory=list)
    repos_with_ci: int = 0
    repos_with_docker: int = 0
    repos_with_readme: int = 0
    avg_readme_quality: float = 0.0
    avg_commits_per_repo: float = 0.0
    score_engineering: float = 0.0
    score_repo_quality: float = 0.0
    score_open_source: float = 0.0
    score_documentation: float = 0.0


class CodingPlatformProfile(BaseModel):
    platform: str
    platform_label: str
    handle: str
    url: str
    stats: dict[str, Any] = Field(default_factory=dict)


class CodingAnalysis(BaseModel):
    platforms: list[CodingPlatformProfile] = Field(default_factory=list)
    problem_solving_score: float = 0.0
    explanation: str = ""


class ProjectVerification(BaseModel):
    project_name: str
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    matched_repo: str | None = None
    repository_exists: bool = False
    deployment_exists: bool = False
    recent_activity: bool = False
    documentation_exists: bool = False
    architecture_complexity: float = 0.0  # 0..1
    score: float = 0.0  # 0..100
    status: VerificationStatus = VerificationStatus.no_public_evidence
    evidence: list[str] = Field(default_factory=list)


class AchievementVerification(BaseModel):
    title: str
    type: str
    claimed_platform: str | None = None
    score: float = 0.0  # 0..100
    status: VerificationStatus = VerificationStatus.no_public_evidence
    evidence: list[str] = Field(default_factory=list)


class ScoreItem(BaseModel):
    key: str
    label: str
    value: float  # 0..100
    explanation: str


class AnalysisBundle(BaseModel):
    resume: ParsedResume
    profiles: list[ConnectedProfile] = Field(default_factory=list)
    github: GitHubAnalysis | None = None
    coding: CodingAnalysis | None = None
    skill_verifications: list[TechnologyVerification] = Field(default_factory=list)
    project_verifications: list[ProjectVerification] = Field(default_factory=list)
    achievement_verifications: list[AchievementVerification] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    ai_summary: dict[str, str] = Field(default_factory=dict)
    scores: list[ScoreItem] = Field(default_factory=list)
    overall_score: float = 0.0

    def get_score(self, key: str) -> ScoreItem | None:
        for s in self.scores:
            if s.key == key:
                return s
        return None