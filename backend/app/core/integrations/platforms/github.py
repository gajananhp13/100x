"""GitHub integration — live public API plus an offline simulation.

Fetches user profile, repositories, languages, commit activity, PR/issue
counts, README presence/quality signals, CI/CD workflows, Dockerfiles and
licenses via api.github.com. Works unauthenticated (60 req/hr) or with a
GITHUB_TOKEN (5,000 req/hr) set in the environment.

Per-repo enrichment is best-effort: GitHub returns 409 for empty repos
(no commits), so a single edge-case repo never fails the whole profile.
"""

from __future__ import annotations

import os
import random
import re

import httpx

from ....models.resume import ParsedResume
from ..base import PlatformDef, ProfileCollectError
from .mixin import SimulatedPlatformMixin

DEF = PlatformDef("github", "GitHub", "gh", "https://github.com/{handle}", "username", True)

API = "https://api.github.com"
PER_PAGE = 100


class GitHubIntegration(SimulatedPlatformMixin):
    platform_id = "github"
    platform_label = "GitHub"
    real_api = True

    def __init__(
        self,
        token: str | None = None,
        transport: httpx.BaseTransport | None = None,
        simulate: bool = False,
    ) -> None:
        super().__init__(simulate=simulate)
        self.token = token or os.getenv("GITHUB_TOKEN") or ""
        self._transport = transport
        self._headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "100xResume",
            **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
        }

    # ------------------------------------------------------------------ #
    # Live API helpers
    # ------------------------------------------------------------------ #

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        with httpx.Client(timeout=20, headers=self._headers, transport=self._transport) as client:
            resp = client.get(f"{API}{path}", params=params or {})
            if resp.status_code == 403:
                raise ProfileCollectError(
                    "GitHub rate limit reached. Add GITHUB_TOKEN to the backend .env for a higher quota."
                )
            if resp.status_code == 404:
                raise ProfileCollectError("GitHub user not found — check the username.")
            if resp.status_code == 401:
                raise ProfileCollectError("GitHub token is invalid.")
            if resp.status_code >= 400:
                raise ProfileCollectError(f"GitHub API error {resp.status_code}.")
            try:
                return resp.json()
            except ValueError as e:
                # e.g. empty body / HTML error page with a 200 status
                raise ProfileCollectError(
                    f"GitHub API returned an invalid (non-JSON) response for {path}. "
                    "Try again in a moment or add GITHUB_TOKEN to backend/.env."
                ) from e

    def _get_list(self, path: str, max_pages: int = 3) -> list[dict]:
        out: list[dict] = []
        page = 1
        while page <= max_pages:
            chunk = self._get(path, {"per_page": PER_PAGE, "page": page})
            if not isinstance(chunk, list) or not chunk:
                break
            out.extend(chunk)
            if len(chunk) < PER_PAGE:
                break
            page += 1
        return out

    def _repo_tree(self, repo_full: str, branch: str) -> set[str]:
        """Full recursive tree of file paths (limit to a sane size)."""
        paths: set[str] = set()
        try:
            tree = self._get(f"/repos/{repo_full}/git/trees/{branch}?recursive=1")
            if isinstance(tree, dict) and isinstance(tree.get("tree"), list):
                paths = {t.get("path", "") for t in tree["tree"] if t.get("type") == "blob"}
        except ProfileCollectError:
            pass
        return paths

    def _readme_quality(self, repo_full: str) -> tuple[bool, float]:
        """README presence + heuristic quality 0..1."""
        try:
            with httpx.Client(
                timeout=20,
                headers={**self._headers, "Accept": "application/vnd.github.raw+json"},
                transport=self._transport,
            ) as client:
                resp = client.get(f"{API}/repos/{repo_full}/readme")
            if resp.status_code == 404:
                return False, 0.0
            if resp.status_code >= 400:
                raise ProfileCollectError(f"GitHub API error {resp.status_code}.")
            text = resp.text
            if text:
                text = text.lower()
                checks = {
                    "length": len(text) > 400,
                    "overview": bool(text.strip()),
                    "sections": sum(1 for s in ("##", "###", "getting started", "usage", "install", "license", "contributing", "api", "setup") if s in text) >= 2,
                    "code_blocks": "```" in text or "```bash" in text or "npm install" in text or "pip install" in text,
                    "badges": "![image]" in text or "img.shields.io" in text,
                    "links": "http" in text,
                }
                score = sum(checks.values()) / len(checks)
                return True, score
        except ProfileCollectError:
            pass
        return False, 0.0

    # ------------------------------------------------------------------ #
    # Live collection
    # ------------------------------------------------------------------ #

    def _collect_real(self, handle: str, context: dict | None = None) -> dict:
        handle = handle.strip().lstrip("@")
        if not handle or "/" in handle:
            raise ProfileCollectError("Enter a valid GitHub username (no URL).")

        user = self._get(f"/users/{handle}")
        if not isinstance(user, dict):
            raise ProfileCollectError("GitHub user not found.")
        if user.get("type") == "Organization":
            raise ProfileCollectError("Use a personal GitHub account, not an organization.")

        repos = [
            r for r in self._get_list(f"/users/{handle}/repos", max_pages=3)
            if isinstance(r, dict) and not r.get("fork") and not r.get("private")
        ]

        repo_detail: list[dict] = []
        total_commits = 0
        total_forks = 0
        total_stars = 0
        repos_with_ci = 0
        repos_with_docker = 0
        repos_with_readme = 0
        readme_sum = 0.0
        language_totals: dict[str, int] = {}

        for r in repos[:12]:
            full = r["full_name"]
            branch = r.get("default_branch") or "main"
            paths: set[str] = set()
            try:
                paths = self._repo_tree(full, branch)
            except Exception:
                pass
            readme_ok, readme_q = self._readme_quality(full)
            languages: dict[str, float] = {}
            try:
                lang_resp = self._get(f"/repos/{full}/languages")
                if isinstance(lang_resp, dict):
                    languages = lang_resp
                    for lang, bytes_count in lang_resp.items():
                        language_totals[lang] = language_totals.get(lang, 0) + int(bytes_count)
            except ProfileCollectError:
                pass  # enrichment is best-effort; never fail the whole profile

            ci = any(p.lower().startswith(".github/workflows/") for p in paths)
            docker = any(("dockerfile" in p.lower() or "docker-compose" in p.lower()) for p in paths)

            # tech evidence scan: file signatures + language boost + description match
            from ...ai.skills_kb import SKILLS, file_signature_hits

            tech_hits: dict[str, float] = {}
            for sd in SKILLS:
                hits = file_signature_hits(sd.name, paths)
                if hits:
                    tech_hits[sd.name] = round(min(1.0, 0.85 + 0.08 * min(3, len(hits))), 2)
            lang_boost = {
                "Python": {"Python"},
                "Java": {"Java"},
                "JavaScript": {"JavaScript", "Node.js"},
                "TypeScript": {"TypeScript", "React", "Next.js", "Redux"},
                "Go": {"Go"},
                "C++": {"C++"},
                "C": {"C"},
                "Ruby": {"Ruby"},
                "PHP": {"PHP"},
                "Rust": {"Rust"},
            }
            for lang, techs in lang_boost.items():
                if r.get("language") == lang:
                    for t in techs:
                        tech_hits[t] = max(tech_hits.get(t, 0.0), 0.35)
            desc = (r.get("description") or "").lower()
            for sd in SKILLS:
                if sd.name in tech_hits:
                    continue
                if any(p.lower() in desc for p in sd.resume_patterns):
                    tech_hits[sd.name] = max(tech_hits.get(sd.name, 0.0), 0.25)

            commits_count = 0
            try:
                # Empty repos (no commits) return 409 on /commits — skip, don't fail
                commits = self._get_list(f"/repos/{full}/commits", max_pages=1)
                commits_count = len(commits) if isinstance(commits, list) else 0
            except ProfileCollectError:
                pass
            total_commits += commits_count
            contributors = 0
            try:
                contribs = self._get_list(f"/repos/{full}/contributors", max_pages=1)
                contributors = len(contribs) if isinstance(contribs, list) else 0
            except ProfileCollectError:
                pass
            open_prs = 0
            try:
                prs = self._get(f"/repos/{full}/pulls", {"state": "open", "per_page": 1})
                if isinstance(prs, list):
                    open_prs = len(prs)
            except ProfileCollectError:
                pass

            if ci:
                repos_with_ci += 1
            if docker:
                repos_with_docker += 1
            if readme_ok:
                repos_with_readme += 1
                readme_sum += readme_q
            total_forks += r.get("forks_count", 0) or 0
            total_stars += r.get("stargazers_count", 0) or 0

            repo_detail.append({
                "name": r.get("name"),
                "full_name": full,
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "homepage": r.get("homepage"),
                "stars": r.get("stargazers_count", 0) or 0,
                "forks": r.get("forks_count", 0) or 0,
                "watchers": r.get("watchers_count", 0) or 0,
                "open_issues": r.get("open_issues_count", 0) or 0,
                "language": r.get("language"),
                "languages": languages,
                "license_name": (r.get("license") or {}).get("spdx_id") or (r.get("license") or {}).get("name"),
                "topics": r.get("topics", []) or [],
                "created_at": r.get("created_at"),
                "pushed_at": r.get("pushed_at"),
                "has_readme": readme_ok,
                "readme_quality": round(readme_q, 2),
                "has_ci": ci,
                "has_dockerfile": docker,
                "commits_count": commits_count,
                "contributors_count": contributors,
                "open_prs": open_prs,
                "is_fork": bool(r.get("fork")),
                "tech_hits": tech_hits,
            })

        total_language_bytes = sum(language_totals.values()) or 1
        language_usage = {lang: round(bytes_count / total_language_bytes, 3) for lang, bytes_count in sorted(language_totals.items(), key=lambda kv: -kv[1])}

        repo_count = len(repo_detail)
        return {
            "_source": "github-api",
            "username": handle,
            "avatar_url": user.get("avatar_url"),
            "public_repos": user.get("public_repos", repo_count),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "account_created_at": user.get("created_at"),
            "bio": user.get("bio"),
            "location": user.get("location"),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits_fetched": total_commits,
            "repos_with_ci": repos_with_ci,
            "repos_with_docker": repos_with_docker,
            "repos_with_readme": repos_with_readme,
            "avg_readme_quality": round(readme_sum / repo_count, 2) if repo_count else 0.0,
            "language_usage": language_usage,
            "repos": repo_detail,
            "_rate_limit_hint": "Unauthenticated GitHub API (60 req/hr) — set GITHUB_TOKEN in backend/.env for 5,000 req/hr.",
        }

    # ------------------------------------------------------------------ #
    # Offline simulation (demo candidate)
    # ------------------------------------------------------------------ #

    def _simulate(
        self,
        rng: random.Random,
        level: float,
        resume: ParsedResume | None,
        handle: str = "demo",
    ) -> dict:
        """Simulated GitHub profile with the exact shape the real API returns."""
        skills = resume.all_skill_names() if resume else []
        projects = [p for p in ((resume.projects or []) if resume else []) if p.name][:3]

        def tech_hits_for(repo_skills: list[str], strength: float = 0.9) -> dict[str, float]:
            return {s: round(min(1.0, strength), 2) for s in repo_skills}

        def slug(name: str) -> str:
            return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

        repos: list[dict] = []
        n = rng.randint(4, 9)
        used_names = set()
        # repo names aligned with resume projects (for a consistent demo story)
        aligned = 0
        for p in projects:
            base = slug(p.name) or f"project-{aligned + 1}"
            used_names.add(base)
            stars = rng.randint(0, 60)
            forks = rng.randint(0, 12)
            lang = (p.tech_stack[0] if p.tech_stack else "Python").split()[0]
            repo_skills = p.tech_stack or skills[:3]
            repos.append({
                "name": base,
                "full_name": f"demo/{base}",
                "description": (p.description or p.name)[:120],
                "html_url": f"https://github.com/demo/{base}",
                "homepage": f"https://{base}.vercel.app" if rng.random() < 0.6 else None,
                "stars": stars,
                "forks": forks,
                "watchers": rng.randint(0, 5),
                "open_issues": rng.randint(0, 8),
                "language": lang,
                "languages": {lang: rng.randint(20000, 90000)},
                "license_name": rng.choice(["MIT", "Apache-2.0", "MIT", "GPL-3.0", None]),
                "topics": [s.lower().replace(" ", "-") for s in skills[:3]],
                "created_at": f"2024-{rng.randint(1, 12):02d}-01T10:00:00Z",
                "pushed_at": f"2026-0{rng.randint(1, 8):02d}-15T10:00:00Z",
                "has_readme": True,
                "readme_quality": round(rng.uniform(0.5, 0.95), 2),
                "has_ci": rng.random() < 0.7,
                "has_dockerfile": rng.random() < 0.5,
                "commits_count": rng.randint(20, 220),
                "contributors_count": rng.randint(1, 4),
                "open_prs": rng.randint(0, 5),
                "is_fork": False,
                "tech_hits": tech_hits_for(repo_skills),
            })
            aligned += 1
        # filler repos
        filler = ["portfolio-site", "algo-solutions", "notes-api", "devops-lab", "cli-utils", "ml-experiments", "system-design"]
        for i in range(n - aligned):
            name = filler[i % len(filler)]
            if name in used_names:
                continue
            used_names.add(name)
            repos.append({
                "name": name,
                "full_name": f"demo/{name}",
                "description": rng.choice(["A personal project", "Learning repo", "Side experiment", None]),
                "html_url": f"https://github.com/demo/{name}",
                "homepage": f"https://{name}.netlify.app" if rng.random() < 0.4 else None,
                "stars": rng.randint(0, 40),
                "forks": rng.randint(0, 8),
                "watchers": rng.randint(0, 4),
                "open_issues": rng.randint(0, 10),
                "language": rng.choice(["Python", "TypeScript", "Java", "Go", "JavaScript", "C++"]),
                "languages": {},
                "license_name": rng.choice(["MIT", "MIT", "Apache-2.0", None, None]),
                "topics": [],
                "created_at": f"2023-{rng.randint(1, 12):02d}-01T10:00:00Z",
                "pushed_at": f"2026-0{rng.randint(1, 8):02d}-10T10:00:00Z",
                "has_readme": rng.random() < 0.8,
                "readme_quality": round(rng.uniform(0.2, 0.9), 2),
                "has_ci": rng.random() < 0.5,
                "has_dockerfile": rng.random() < 0.35,
                "commits_count": rng.randint(10, 150),
                "contributors_count": rng.randint(1, 3),
                "open_prs": rng.randint(0, 4),
                "is_fork": False,
                "tech_hits": tech_hits_for(skills[:2], strength=0.75) if rng.random() < 0.7 else {},
            })
        total_stars = sum(r["stars"] for r in repos)
        total_forks = sum(r["forks"] for r in repos)
        return {
            "_source": "mock",
            "username": handle,
            "avatar_url": f"https://ui-avatars.com/api/?name={handle[:2].upper()}&background=6d5efc&color=fff",
            "public_repos": len(repos),
            "followers": rng.randint(5, 90),
            "following": rng.randint(20, 200),
            "account_created_at": f"20{rng.randint(15, 19)}-06-15T00:00:00Z",
            "bio": "Software developer building things",
            "location": None,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits_fetched": sum(r["commits_count"] for r in repos),
            "repos_with_ci": sum(1 for r in repos if r["has_ci"]),
            "repos_with_docker": sum(1 for r in repos if r["has_dockerfile"]),
            "repos_with_readme": sum(1 for r in repos if r["has_readme"]),
            "avg_readme_quality": round(sum(r["readme_quality"] for r in repos) / max(len(repos), 1), 2),
            "language_usage": {"Python": 0.3, "TypeScript": 0.4, "Java": 0.3},
            "repos": repos,
            "_rate_limit_hint": "Demo data — simulated GitHub profile.",
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def validate(self, handle: str) -> tuple[bool, str]:
        """Cheap existence check used by the connect UI."""
        try:
            user = self._get(f"/users/{handle.strip().lstrip('@')}")
            return isinstance(user, dict), "ok"
        except ProfileCollectError as e:
            return False, str(e)


def is_github_rate_limited() -> bool:
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{API}/rate_limit",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "100xResume"},
            )
            data = resp.json()
            remaining = data.get("resources", {}).get("core", {}).get("remaining", 0)
            return int(remaining) < 5
    except Exception:
        return False
