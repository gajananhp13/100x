"""Human-claim verification: skills, projects, achievements.

Rule: never accuse the candidate. Absence of public evidence is recorded as
'No Public Evidence Found', never as 'false' or 'absent'.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from ...models.analysis import (
    AchievementVerification,
    GitHubAnalysis,
    ProjectVerification,
    RepoAnalysis,
    TechnologyVerification,
    VerificationStatus,
    status_from_confidence,
)
from ...models.profiles import ConnectedProfile
from ...models.resume import Achievement, ParsedResume, Project
from ..ai.skills_kb import NON_CODE_EVIDENCE_TECHS, category_of
from ..integrations.registry import PLATFORM_BY_ID


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Technical skill verification
# --------------------------------------------------------------------------- #

# Skills that cannot be scraped from connected code platforms, so they do not
# belong in the Technical Verification section. Version control, IDEs and
# project tools are process aids, not verifiable technical skills; testing
# frameworks and AI services (LLMs, wrappers) are excluded for the same reason.
# Technical libraries/frameworks (PyTorch, TensorFlow, Spring Boot, FastAPI, …)
# are kept because they leave real code evidence.
_EXCLUDED_VERIFICATION_CATEGORIES: frozenset[str] = frozenset({"testing", "tools"})
_EXCLUDED_VERIFICATION_TECHS: frozenset[str] = frozenset(
    {"LLM", "OpenAI", "LangChain", "Hugging Face", "MLOps"}
)


def verify_skills(resume: ParsedResume, github: GitHubAnalysis | None) -> list[TechnologyVerification]:
    out: list[TechnologyVerification] = []
    skills = resume.all_skill_names()
    if not skills:
        return out

    repo_hits: dict[str, list[tuple[str, float]]] = {}
    for repo in (github.repos if github else []):
        for tech, conf in repo.tech_hits.items():
            repo_hits.setdefault(tech, []).append((repo.name, conf))

    for skill in skills:
        category = category_of(skill)
        if category in _EXCLUDED_VERIFICATION_CATEGORIES or skill in _EXCLUDED_VERIFICATION_TECHS:
            continue
        evidence: list[str] = []
        conf = 0.0

        hits = repo_hits.get(skill, [])
        if hits:
            best_repo, best_conf = max(hits, key=lambda h: h[1])
            evidence.append(
                f"Referenced in connected repository '{best_repo}' (confidence {round(best_conf * 100)}%)."
            )
            extra = [f"'{r}'" for r, c in hits[1:] if c >= 0.5][:3]
            if extra:
                evidence.append(f"Also present in: {', '.join(extra)}.")
            conf = best_conf
        elif github and github.public_repos > 0:
            if skill in NON_CODE_EVIDENCE_TECHS:
                evidence.append(
                    f"{skill} is a tool/process typically invisible in public repositories; no code evidence was found."
                )
            else:
                evidence.append(f"No public code referencing '{skill}' was found in the {github.public_repos} connected repositories.")
        else:
            evidence.append("No public repository evidence available (GitHub not connected).")

        out.append(
            TechnologyVerification(
                technology=skill,
                category=category,
                confidence=round(conf, 2),
                status=status_from_confidence(conf),
                evidence=evidence,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Project verification
# --------------------------------------------------------------------------- #

def _name_slug(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "", name or "").lower()
    return name.strip()


def _repo_slug(r: RepoAnalysis) -> str:
    return _name_slug(r.name)


def _match_project_to_repo(project: Project, repos: list[RepoAnalysis], github: GitHubAnalysis | None) -> RepoAnalysis | None:
    if not project.name or not repos:
        return None
    slug = _name_slug(project.name)
    # 1) exact github link match
    if project.github_link:
        for r in repos:
            if project.github_link.rstrip("/") == r.html_url.rstrip("/"):
                return r
            if re.search(_name_slug(r.full_name), project.github_link.lower()):
                return r
    # 2) substring containment either way
    for r in repos:
        rs = _repo_slug(r)
        if rs and (rs in slug or slug in rs):
            return r
    # 3) topic / language weak match placeholder (avoid guessing)
    return None


def verify_projects(resume: ParsedResume, github: GitHubAnalysis | None) -> list[ProjectVerification]:
    out: list[ProjectVerification] = []
    repos = github.repos if github else []
    now = datetime.now(timezone.utc)

    for project in resume.projects:
        matched = _match_project_to_repo(project, repos, github)
        evidence: list[str] = []
        score = 0.0
        repo_exists = matched is not None
        deployment = False
        recent = False
        documented = False
        complexity = 0.0

        if matched:
            pushed = _parse_dt(matched.pushed_at)
            recent = bool(pushed and (now - pushed).days <= 180)
            documented = matched.has_readme

            claimed_links = {l for l in (project.github_link, project.live_demo) if l}
            deployment = bool(
                matched.homepage
                or any(cl and re.sub(r"/+$", "", cl.split("://")[-1]) == re.sub(r"/+$", "", (matched.homepage or "").split("://")[-1]) for cl in claimed_links)
                or (recent and matched.homepage is not None)
            )

            complexity = round(
                min(1.0, (
                    min(1.0, matched.commits_count / 150.0) * 0.35
                    + min(1.0, matched.contributors_count / 3.0) * 0.2
                    + min(1.0, len(matched.languages) / 3.0) * 0.2
                    + min(1.0, matched.stars / 20.0) * 0.15
                    + min(1.0, len(matched.topics) / 5.0) * 0.1
                )), 2)

            score = round(
                25 * bool(matched)
                + (20 if deployment else 0)
                + (15 if recent else 0)
                + (15 if documented else 0)
                + complexity * 25,
                1,
            )
            evidence.append(f"Matched to repository '{matched.full_name}'.")
            if deployment:
                evidence.append(f"Deployed publicly ({matched.homepage or 'live link found'}).")
            if recent:
                evidence.append("Repository has commit activity within the last 6 months.")
            if documented:
                evidence.append(f"Documentation present (README quality {round(matched.readme_quality * 100)}%).")
            evidence.append(getattr(matched, "tech_hits", None) and f"Verified tech signals: {', '.join(list(matched.tech_hits)[:5])}" or None)
        else:
            score = 15.0 if project.github_link else 5.0
            if project.github_link:
                evidence.append("A GitHub link is listed on the resume, but no matching repository was found among connected accounts.")
            else:
                evidence.append("No GitHub link on the resume; project content could not be matched to a public repository.")

        evidence = [e for e in evidence if e]
        out.append(
            ProjectVerification(
                project_name=project.name or "Untitled project",
                description=project.description,
                tech_stack=project.tech_stack,
                matched_repo=matched.full_name if matched else None,
                repository_exists=repo_exists,
                deployment_exists=deployment,
                recent_activity=recent,
                documentation_exists=documented,
                architecture_complexity=complexity,
                score=score,
                status=status_from_confidence(score / 100),
                evidence=evidence,
            )
        )
    if not resume.projects:
        out.append(
            ProjectVerification(
                project_name="(no projects listed)",
                score=0.0,
                status=VerificationStatus.no_public_evidence,
                evidence=["The resume does not list any projects to verify."],
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Achievement verification
# --------------------------------------------------------------------------- #

def _number_from_title(title: str) -> int | None:
    m = re.search(r"(\d{2,})", title)
    return int(m.group(1)) if m else None


def verify_achievements(resume: ParsedResume, profiles: list[ConnectedProfile], github: GitHubAnalysis | None) -> list[AchievementVerification]:
    out: list[AchievementVerification] = []
    by_platform = {p.platform: p for p in profiles if p.status == "collected"}

    def plat(pid: str) -> ConnectedProfile | None:
        return by_platform.get(pid)

    for a in resume.achievements:
        title = a.title or ""
        title_lower = title.lower()
        evidence: list[str] = []
        conf = 0.0

        def consider(name: str, value: bool, strength: float, note: str) -> None:
            nonlocal conf
            if value:
                conf = max(conf, strength)
                evidence.append(note)

        if a.type == "hackathon":
            dp = plat("devpost")
            if dp:
                n = int(dp.data.get("hackathons_attended", 0) or 0)
                n_win = len([p for p in dp.data.get("projects", []) if p.get("winning")])
                consider("devpost", True, 0.45, f"Devpost profile shows {n} hackathons attended and {n_win} winning projects.")
            else:
                evidence.append("Devpost not connected; no public hackathon record found.")
            if "winner" in title_lower or "finalist" in title_lower:
                if dp and int((dp.data.get("hackathons_attended") or 0)) > 0:
                    conf = max(conf, 0.3)
                    evidence.append("Winning status could not be independently confirmed from connected platforms.")

        elif a.type == "certification":
            hr = plat("hackerrank")
            if hr and int(hr.data.get("certificates", 0) or 0) > 0:
                consider("cert", True, 0.6, f"HackerRank profile lists {hr.data['certificates']} certificate(s).")
            elif hr:
                evidence.append("HackerRank connected but lists no certifications matching this claim.")
            else:
                evidence.append("No public certification record found on connected platforms.")

        elif a.type in ("coding", "other"):
            coding_data: list[tuple[str, ConnectedProfile]] = []
            for pid in ("leetcode", "codeforces", "codechef", "geeksforgeeks", "hackerrank"):
                p = plat(pid)
                if p:
                    coding_data.append((PLATFORM_BY_ID[pid].label, p))
            if coding_data:
                label, p = coding_data[0]
                claimed = _number_from_title(title_lower)
                for pid in ("leetcode", "codeforces", "codechef", "geeksforgeeks", "hackerrank"):
                    p = plat(pid)
                    if not p:
                        continue
                    solved = p.data.get("total_solved") or p.data.get("problems_solved") or p.data.get("coding_score") or 0
                    if solved and claimed:
                        conf = max(conf, min(1.0, float(solved) / max(claimed, 1)))
                        evidence.append(f"{PLATFORM_BY_ID[pid].label} shows {solved} solved problems vs a claimed ~{claimed}.")
                    elif solved:
                        conf = max(conf, 0.45)
                        evidence.append(f"{PLATFORM_BY_ID[pid].label} shows coding activity ({solved} solved).")
                if not conf:
                    conf = 0.25
                    evidence.append("Coding profiles connected, but no statistic matched the specific claim.")
            else:
                evidence.append("No coding platform connected; this claim has no public verification source.")

        elif a.type == "publication":
            md = plat("medium")
            if md:
                n = int(md.data.get("articles", 0) or 0)
                consider("pub", n > 0, min(0.8, 0.4 + n * 0.05), f"Medium profile lists {n} article(s).")
            else:
                evidence.append("Medium not connected; no public publication record found.")

        elif a.type == "open_source":
            if github:
                consider("oss", github.public_repos > 0 and github.total_forks > 0, 0.55,
                         f"GitHub shows {github.public_repos} public repositories with {github.total_forks} forks, indicating collaborative open-source work.")
                if github.total_stars > 0:
                    conf = max(conf, 0.7)
                    evidence.append(f"Repositories have accumulated {github.total_stars} stars.")
            else:
                evidence.append("GitHub not connected; open-source contributions cannot be verified.")

        elif a.type == "award":
            evidence.append("Awards typically lack a public API source; no independent record was found on connected platforms.")

        else:
            evidence.append("No public evidence source applies to this achievement type.")

        evidence = [e for e in evidence if e]
        status = status_from_confidence(conf)
        out.append(
            AchievementVerification(
                title=a.title,
                type=a.type,
                claimed_platform=a.platform,
                score=round(conf * 100, 1),
                status=status,
                evidence=evidence,
            )
        )
    if not resume.achievements:
        out.append(
            AchievementVerification(
                title="(no achievements listed)", type="other",
                score=0.0, status=VerificationStatus.no_public_evidence,
                evidence=["The resume does not list any achievements to verify."],
            )
        )
    return out