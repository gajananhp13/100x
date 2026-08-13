"""Deterministic heuristic resume parser (used by the mock AI engine).

Extracts structured information from plain resume text using section detection
and pattern matching. Designed to be deterministic (same text -> same output) so
tests and the demo flow are reproducible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ...models.resume import (
    Achievement,
    Education,
    Experience,
    ParsedResume,
    PersonalDetails,
    Project,
    SkillsBreakdown,
)
from .skills_kb import ALIASES, CATEGORY_LABELS, NAME_ONLY_TECHNOLOGIES, detect_skills_in_text

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(?:\+?\d[\s\-()]?){9,15}\d")
LINKEDIN_RE = re.compile(r"(?:linkedin\.com/in/|linkedin\.com/)([\w-]+)", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:github\.com/)([\w-]+)", re.IGNORECASE)
PORTFOLIO_RE = re.compile(r"((?:https?://|www\.)[\w.\-]+\.[a-zA-Z]{2,}(?:/[\w\-./]*)?)")
LINE_BULLET = re.compile(r"^\s*(?:[•·▪-]|\d+[.)]|o)\s*")
TECH_BRACKET = re.compile(r"\[([^\]]*)\]")

SECTION_KEYWORDS: dict[str, list[str]] = {
    "skills": ["technical skills", "skills & tools", "skills", "technologies", "tech stack", "tools & technologies", "core competencies", "skills and expertise"],
    "experience": ["professional experience", "work experience", "experience", "employment history", "work history", "professional summary"],
    "education": ["education", "academic background", "qualification"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "project experience"],
    "achievements": ["achievements", "awards", "certifications", "certificates", "hackathon", "hackathons", "publications", "honors", "honours", "extracurricular", "open source", "open-source", "accomplishments"],
    "summary": ["summary", "profile", "about me", "objective", "career objective", "professional summary"],
    "links": ["links", "contact", "contact information", "find me", "profiles"],
}

COMPANY_KEYWORDS = ("technologies", "technology", "ltd", "llc", "inc", "corp", "corp.", "private limited",
                    "pvt", "limited", "company", "google", "amazon", "microsoft", "meta", "apple",
                    "netflix", "uber", "flipkart", "swiggy", "zomato", "infosys", "tcs", "wipro",
                    "accenture", "cognizant", "capgemini", "delloite", "paypal", "stripe", "shopify",
                    "airbnb", "linkedin", "atlassian", "salesforce", "adobe", "oracle", "ibm", "nvidia",
                    "intel", "qualcomm", "cisco", "vmware", "dell", "hp", "lenskart", "razorpay", "cred",
                    "chargebee", "zoho", "freshworks", "browserstack", "atlan", "postman", "fractal")

EDU_DEGREE_KEYWORDS = ("b.tech", "b.e", "m.tech", "m.e", "mba", "msc", "m.sc", "bsc", "b.sc", "bba",
                       "bca", "mca", "phd", "m.s", "b.s", "diploma", "b.des", "m.des", "b.arch", "m.arch",
                       "m.s.c", "b.tech", "mtech", "btech", "integrated m.tech", "b.e.", "bachelor of",
                       "master of", "doctor of")
EDU_COLLEGE_KEYWORDS = ("university", "institute", "college", "iit", "nit", "iiit", "bits", "school of",
                        "academy", "faculty of", "nsit", "dce", "vit", "amity", "manipal", "srm", "jntu",
                        "anna university", "vtu", "gtu", "pune university", "mumbai university")
EDU_BRANCH_KEYWORDS = ("computer science", "computer engineering", "computer science and engineering",
                       "cse", "information technology", "cse", "ece", "electronics", "mechanical",
                       "civil", "electrical", "data science", "it engineering", "software engineering",
                       "artificial intelligence", "computer applications")

HACKATHON_KEYWORDS = ("hackathon", "hack night", "build-a-thon")
CERT_KEYWORDS = ("certificate", "certified", "certification", "credential", "aws certified", "google certified")
AWARD_KEYWORDS = ("award", "won", "winner", "1st place", "2nd place", "3rd place", "finalist", "dean's list", "scholarship")
PUB_KEYWORDS = ("publication", "published", "paper", "journal", "conference paper", "arxiv", "research paper", "patent")
OSS_KEYWORDS = ("open source", "open-source", "contributor", "gsoc", "google summer of code", "pull request")
CODING_KEYWORDS = ("leetcode", "codeforces", "codechef", "hackerrank", "gfg", "geeksforgeeks", "kaggle", "hackerearth")

LINE_IS_HEADER = re.compile(r"^[A-Z][A-Z0-9 &/+.\-]{2,}[:\s]*$|^(EDUCATION|EXPERIENCE|SKILLS|PROJECTS|ACHIEVEMENTS|CERTIFICATIONS|AWARDS|HACKATHONS|PUBLICATIONS)$", re.IGNORECASE)


def _is_header(line: str) -> bool:
    return bool(LINE_IS_HEADER.match(line)) and len(line.split()) <= 6


def _attribute_section(lines: list[str]) -> dict[str, list[int]]:
    """Heuristically split resume lines into sections by header detection."""
    sections: dict[str, list[int]] = {
        "summary": [], "experience": [], "education": [], "skills": [],
        "projects": [], "achievements": [], "links": [], "unknown": [],
    }
    current = "unknown"
    for idx, line in enumerate(lines):
        lowered = line.lower()
        matched = None
        for sec, kws in SECTION_KEYWORDS.items():
            if any(kw in lowered for kw in kws) and len(lowered) < 60 and _is_header(line):
                matched = sec
                break
        if matched:
            current = matched
            continue
        sections[current].append(idx)
    return sections


@dataclass
class _Extraction:
    personal: PersonalDetails = field(default_factory=PersonalDetails)
    education: list[Education] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    skills: SkillsBreakdown = field(default_factory=SkillsBreakdown)
    projects: list[Project] = field(default_factory=list)
    achievements: list[Achievement] = field(default_factory=list)


def _extract_personal(lines: list[str], sections: dict[str, list[int]]) -> PersonalDetails:
    pd = PersonalDetails()
    window = lines[:min(len(lines), 25)]
    for line in window:
        if not pd.name and re.match(r"^[A-Z][A-Za-z]+ [A-Za-z]+", line) and len(line) < 45 and not LINE_BULLET.match(line):
            pd.name = line.strip()
    text = "\n".join(lines)
    m = EMAIL_RE.search(text)
    if m:
        pd.email = m.group(0)
    m = PHONE_RE.search(text)
    if m and 9 <= len(re.sub(r"\D", "", m.group(0))) <= 13:
        pd.phone = m.group(0)
    m = LINKEDIN_RE.search(text)
    if m:
        pd.linkedin = f"https://linkedin.com/in/{m.group(1)}"
    m = GITHUB_RE.search(text)
    if m:
        handle = m.group(1).rstrip("/")
        pd.github = f"https://github.com/{handle}"
    m = PORTFOLIO_RE.search(text)
    if m:
        url = m.group(1).rstrip(".,;")
        lower = url.lower()
        is_known_platform = any(
            dom in lower
            for dom in (
                "linkedin", "github", "gitlab", "bitbucket", "leetcode", "codeforces",
                "codechef", "hackerrank", "kaggle", "devpost", "dev.to", "medium",
                "hashnode", "stackoverflow", "geeksforgeeks", "interviewbit",
                "twitter", "x.com",
            )
        )
        if not is_known_platform and not pd.portfolio:
            pd.portfolio = url
    # location guess: look for line like "City, State" or "City, Country"
    for line in window:
        if "," in line and len(line) < 45 and not pd.location and not any(k in line.lower() for k in
                ("http", "@", "correctiv", "|", "phone", "linkedin", "github", "email")):
            candidate = line.strip()
            if 3 < len(candidate) < 40 and not re.match(r"^[A-Z]{2,}$", candidate.strip().replace(",", "")):
                pd.location = candidate
    return pd


def _segment_assign(edu: Education, seg: str) -> None:
    """Assign an education segment on a single line by keyword matching."""
    seg = seg.strip().rstrip(",.")
    lowered = seg.lower()
    branch_match = None
    if not edu.degree and any(k in lowered for k in EDU_DEGREE_KEYWORDS):
        edu.degree = seg
        # "M.Tech in Computer Science" -> branch is the part after "in "
        in_idx = None
        for kw in (" in ", " in "):
            ix = lowered.find(" in ")
            if ix >= 0 and ix < len(seg) - 4:
                in_idx = ix
                break
        if in_idx is not None:
            branch_match = seg[in_idx + 4:].strip()
    if not edu.college:
        for k in EDU_COLLEGE_KEYWORDS:
            if k in lowered:
                edu.college = seg
                break
    if branch_match:
        edu.branch = branch_match or None
    if not edu.branch:
        for k in EDU_BRANCH_KEYWORDS:
            if k in lowered and not any(d in lowered for d in EDU_DEGREE_KEYWORDS):
                edu.branch = seg.replace("in", "", 1).strip()
                break


def _extract_education(lines: list[str], section_idx: list[int]) -> list[Education]:
    out: list[Education] = []
    if not section_idx:
        return out
    blocks: list[list[str]] = []
    current: list[str] = []
    for i in section_idx:
        line = lines[i]
        looks_new = any(k in line.lower() for k in EDU_COLLEGE_KEYWORDS) and (not current or len(current) >= 2)
        if looks_new and current:
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)
    for blk in blocks:
        edu = Education()
        for line in blk:
            lowered = line.lower()
            # multi-field single line: "B.Tech in CSE, NIT, 2022, CGPA 8.7"
            if "," in line and len(line) > 40 and not edu.college:
                for seg in line.split(","):
                    if seg.strip():
                        _segment_assign(edu, seg)
            else:
                _segment_assign(edu, line)
            m = re.search(r"\b(19|20)\d{2}\b", line)
            if m and not edu.graduation_year:
                edu.graduation_year = m.group(0)
            gp = re.search(r"(?:cgpa|gpa)[\s:/-]*([0-9]+(?:\.[0-9]+)?)", lowered)
            if gp and not edu.gpa:
                edu.gpa = gp.group(1)
        if edu.college or edu.degree or edu.branch or edu.graduation_year:
            out.append(edu)
    return out


def _extract_experience(lines: list[str], section_idx: list[int]) -> list[Experience]:
    out: list[Experience] = []
    if not section_idx:
        return out
    current: Experience | None = None
    for i in section_idx:
        line = lines[i].strip()
        lowered = line.lower()
        is_header_like = _is_header(line)
        has_company = any(k in lowered for k in COMPANY_KEYWORDS)
        has_date = bool(re.search(r"\b(19|20)\d{2}\b", line))
        has_position_word = any(w in lowered for w in ("developer", "engineer", "intern", "analyst", "sde",
                                                       "manager", "consultant", "trainee", "architect", "lead",
                                                       "specialist", "associate", "founder"))
        # Start a new role when line looks like a role header (company or position and short).
        if (has_company or has_position_word) and len(line) < 90 and (has_date or current is None):
            if current and (current.company or current.position):
                out.append(current)
            current = Experience()
            current.company = line if has_company and not has_position_word else None
            current.position = line if has_position_word else None
            if current.company is None and current.position is None:
                current.position = line
            dm = re.findall(r"\b(19|20)\d{2}\b", line)
            if dm:
                current.duration = " – ".join(dm) if len(dm) > 1 else f"{dm[0]} – present"
            continue
        if current is not None:
            # split company|position style
            if current.position and not current.company and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                current.position, current.company = parts[0], parts[1]
                continue
            if LINE_BULLET.match(line):
                current.responsibilities.append(LINE_BULLET.sub("", line).strip())
            else:
                for tech in detect_skills_in_text(line):
                    if tech not in current.technologies:
                        current.technologies.append(tech)
    if current and (current.company or current.position):
        out.append(current)
    return out


def _extract_skills(lines: list[str], section_idx: list[int], full_text: str) -> SkillsBreakdown:
    sb = SkillsBreakdown()
    blob = "\n".join(lines[i] for i in section_idx)
    skill_tokens = detect_skills_in_text(blob if len(blob) > 20 else full_text)
    if not skill_tokens:
        skill_tokens = detect_skills_in_text(full_text)
    seen: set[str] = set()
    for name in skill_tokens:
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        cat = _category_of(name)
        getattr(sb, cat).append(name)
    return sb


def _category_of(name: str) -> str:
    from .skills_kb import CANONICAL_CATEGORY, NAME_ONLY_TECHNOLOGIES as _not
    if name in CANONICAL_CATEGORY:
        return CANONICAL_CATEGORY[name]
    if name in NAME_ONLY_TECHNOLOGIES:
        return NAME_ONLY_TECHNOLOGIES[name]
    return "other"


FIELD_PREFIXES = (
    "description:", "features:", "tech stack:", "technologies:", "technical stack:",
    "github:", "github link:", "live:", "live demo:", "demo:", "apis:", "apis used:",
    "api:", "database:", "db:", "deployment:", "deployed:", "stacks:",
)

PROJECT_TITLE_MARK = re.compile(r"^\s*(?:\[?\d+\]?|[*•▪])\s*[—-]?\s*")


def _field_prefix(line: str) -> str | None:
    lowered = line.lower().strip()
    for p in FIELD_PREFIXES:
        if lowered.startswith(p):
            return p.rstrip(":").strip()
    return None


def _extract_projects(lines: list[str], section_idx: list[int]) -> list[Project]:
    out: list[Project] = []
    if not section_idx:
        return out
    current: Project | None = None
    for i in section_idx:
        raw = lines[i].strip()
        clean = PROJECT_TITLE_MARK.sub("", raw).strip()
        prefix = _field_prefix(raw if raw else clean)
        is_title = prefix is None and len(clean) > 1 and len(clean) < 100 and not (
            any(k in clean.lower() for k in ("http://", "https://")) and not clean.lower().startswith("http")
        )
        if is_title and current is not None:
            out.append(current)
            current = None
        if current is None:
            if not is_title:
                continue
            current = Project()
            name: str = clean
            # "Name — subtitle" style: keep only the short leading name
            for sep in (" — ", " – ", " - ", "|"):
                if sep in name:
                    head = name.split(sep)[0].strip()
                    if 1 < len(head) <= 45 and head[0].isupper():
                        name = head
                    break
            current.name = name
            if "[" in raw and "]" in raw:
                bracket = re.search(r"\[([^\]]*)\]", raw)
                if bracket and "," in bracket.group(1):
                    current.tech_stack = [t.strip().strip("[]") for t in bracket.group(1).split(",") if t.strip()]
            continue
        # attribute field lines to current project
        if prefix == "description":
            current.description = raw.split(":", 1)[1].strip() or None
        elif prefix == "features":
            rest = raw.split(":", 1)[1].strip()
            current.features = [f.strip() for f in re.split(r"[;,]", rest) if f.strip()]
        elif prefix in ("tech stack", "technologies", "technical stack", "stacks", "tech"):
            rest = raw.split(":", 1)[1].strip()
            current.tech_stack = [t.strip().strip("[]") for t in re.split(r"[;,]", rest) if t.strip()]
        elif prefix in ("github", "github link"):
            current.github_link = re.search(r"https?://[^\s]+", raw)
            current.github_link = current.github_link.group(0) if current.github_link else None
        elif prefix in ("live", "live demo", "demo"):
            m = re.search(r"https?://[^\s]+", raw)
            if m:
                current.live_demo = m.group(0)
        elif prefix in ("apis", "apis used", "api"):
            rest = raw.split(":", 1)[1].strip()
            current.apis_used = [a.strip() for a in re.split(r"[;,]", rest) if a.strip()]
        elif prefix in ("database", "db"):
            current.database = raw.split(":", 1)[1].strip() or None
        elif prefix == "deployment":
            current.deployment = raw.split(":", 1)[1].strip() or None
        else:
            m = TECH_BRACKET.search(raw)
            if m and "," in m.group(1):
                current.tech_stack = [t.strip() for t in m.group(1).split(",") if t.strip()]
            gh = re.search(r"github\.com/[\w./-]+", raw, re.IGNORECASE)
            if gh and not current.github_link:
                current.github_link = gh.group(0)
            dm = re.search(r"https?://[^\s]+", raw)
            if dm and "github.com" not in dm.group(0) and not current.live_demo:
                current.live_demo = dm.group(0)
            for t in detect_skills_in_text(raw):
                if t not in current.tech_stack:
                    current.tech_stack.append(t)
    if current is not None and current.name:
        out.append(current)
    return out


def _extract_achievements(lines: list[str], section_idx: list[int]) -> list[Achievement]:
    out: list[Achievement] = []
    for i in section_idx:
        line = lines[i].strip()
        if not line or LINE_IS_HEADER.match(line):
            continue
        clean = LINE_BULLET.sub("", line).strip() or line.strip()
        lowered = clean.lower()
        kind = "other"
        if any(k in lowered for k in HACKATHON_KEYWORDS):
            kind = "hackathon"
        elif any(k in lowered for k in CERT_KEYWORDS):
            kind = "certification"
        elif any(k in lowered for k in AWARD_KEYWORDS):
            kind = "award"
        elif any(k in lowered for k in PUB_KEYWORDS):
            kind = "publication"
        elif any(k in lowered for k in OSS_KEYWORDS):
            kind = "open_source"
        elif any(k in lowered for k in CODING_KEYWORDS):
            kind = "coding"
        if len(clean) < 3:
            continue
        out.append(Achievement(type=kind, title=clean[:120], description=clean if len(clean) > 60 else None, date=None))
    return out


def parse_resume_heuristic(text: str) -> ParsedResume:
    raw_lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in raw_lines if ln]
    sections = _attribute_section(lines)
    extract = _Extraction()

    extract.personal = _extract_personal(lines, sections)
    extract.education = _extract_education(lines, sections["education"])
    extract.experience = _extract_experience(lines, sections["experience"])
    extract.skills = _extract_skills(lines, sections["skills"], text)
    extract.projects = _extract_projects(lines, sections["projects"])
    extract.achievements = _extract_achievements(lines, sections["achievements"])

    resume = ParsedResume(
        personal=extract.personal,
        education=extract.education,
        experience=extract.experience,
        skills=extract.skills,
        projects=extract.projects,
        achievements=extract.achievements,
        raw_text=text,
    )
    return resume