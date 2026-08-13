"""Auto-detect platform handles from a parsed resume.

When a resume already mentions profile URLs (GitHub, LinkedIn, LeetCode, ...),
integrations can be connected without any manual input: this module extracts
the handle for every platform directly from the parsed personal fields and the
resume body, and the auto-connect endpoint collects those profiles in one call.
"""

from __future__ import annotations

import re

from ...models.resume import ParsedResume

# platform id -> (regex, capture group) with the group holding the handle.
# LeetCode lists a fallback shorthand matcher (leetcode.com/<user>) separately.
_PATTERNS: dict[str, tuple[str, int]] = {
    "github": (r"github\.com\/@?([a-z0-9][a-z0-9-]{0,38})", 1),
    "gitlab": (r"gitlab\.com\/([a-z0-9][a-z0-9._-]{0,38})", 1),
    "bitbucket": (r"bitbucket\.org\/(?:workspaces\/)?([a-z0-9][a-z0-9._-]{0,38})", 1),
    "linkedin": (r"linkedin\.com\/in\/([a-z0-9][a-z0-9._-]{0,90})", 1),
    "devpost": (r"devpost\.com\/([a-z0-9][a-z0-9-]{0,38})", 1),
    "kaggle": (r"kaggle\.com\/([a-z0-9][a-z0-9-]{0,38})", 1),
    "leetcode": (r"leetcode\.com\/u\/([a-z0-9][a-z0-9_-]{0,38})", 1),
    "interviewbit": (r"interviewbit\.com\/profile\/([a-z0-9][a-z0-9._-]{0,50})", 1),
    "codeforces": (r"codeforces\.com\/profile\/([a-z0-9][a-z0-9_.-]{0,38})", 1),
    "codechef": (r"codechef\.com\/users\/([a-z0-9][a-z0-9._-]{0,38})", 1),
    "geeksforgeeks": (r"(?:auth\.)?geeksforgeeks\.org\/user\/([a-z0-9][a-z0-9._-]{0,50})", 1),
    "hackerrank": (r"hackerrank\.com\/([a-z0-9][a-z0-9._-]{0,38})", 1),
    "stackoverflow": (r"stackoverflow\.com\/users\/(\d+)(?:\/[a-z0-9-]+)?", 1),
    "medium": (r"medium\.com\/@([a-z0-9][a-z0-9._-]{0,50})", 1),
    "hashnode": (r"hashnode\.(?:com|dev)\/@([a-z0-9][a-z0-9._-]{0,50})", 1),
    "devto": (r"dev\.to\/([a-z0-9][a-z0-9-]{0,38})", 1),
    "twitter": (r"(?:twitter\.com|x\.com)\/([a-z0-9_]{1,15})", 1),
}

# Text-based fallback patterns: match platform name followed by a handle-like handle string.
# This catches cases where the platform is mentioned in the resume (e.g. "LeetCode aarav-mehta",
# "CodeChef 3-star rating 1740") without a URL.
_TEXT_PATTERNS: dict[str, tuple[str, int]] = {
    "leetcode": (r"leetcode\s+([a-z0-9][a-z0-9_-]{0,38})", 1),
    "codechef": (r"codechef\s+([a-z0-9][a-z0-9._-]{0,38})", 1),
    "kaggle": (r"kaggle\s+([a-z0-9][a-z0-9_-]{0,38})", 1),
    "hackerrank": (r"hackerrank\s+([a-z0-9][a-z0-9._-]{0,38})", 1),
}

# fallback shorthand patterns tried when the canonical URL form is absent
_SHORTHAND: dict[str, tuple[str, int]] = {
    "leetcode": (r"(?:leetcode\.com\/)(?!u\/)([a-z0-9][a-z0-9_-]{1,38})", 1),
}

# generic page segments that never identify a person
_BLOCKED: dict[str, set[str]] = {
    "github": {"topics", "settings", "login", "signup", "explore", "collections", "search", "features", "sponsors", "new", "orgs"},
    "leetcode": {"problems", "problemset", "contest", "contests", "explore", "studyplan", "discuss", "interview", "store", "submissions"},
    "hackerrank": {"dashboard", "profile", "domains", "skills", "events", "careers", "contests", "challenges", "login", "signup"},
    "devpost": {"software", "devpost", "api", "challenges", "about", "legal", "terms", "profile"},
    "kaggle": {"c", "competitions", "datasets", "models", "code", "discussion", "learn", "docs"},
    "devto": {"sign_in", "sign-up", "settings", "new", "top", "feed", "latest", "tags", "podcasts", "videos", "about", "search"},
    "twitter": {"home", "explore", "settings", "search", "i", "hashtag", "notifications", "login", "signup", "share", "intent", "tweet", "messages", "x"},
    "medium": {"login", "sign-up", "about", "create", "settings", "topics", "newsletters", "privacy", "me", "search"},
    "stackoverflow": {"questions", "tags", "users", "jobs", "search"},
}


def _normalize(handle: str) -> str:
    """Strip URL decorations: @ prefix, trailing slashes/punctuation."""
    return handle.strip().strip("@/").rstrip(".,;").strip()


def _clean(handle: str, platform_id: str) -> str:
    handle = _normalize(handle)
    if not handle or len(handle) < 2:
        return ""
    if handle in _BLOCKED.get(platform_id, ()):
        return ""
    return handle


def _text_sources(resume: ParsedResume) -> list[str]:
    """Ordered list of strings to scan for profile links."""
    p = resume.personal
    out: list[str] = [p.name, p.headline, p.email, p.location,
                      p.github, p.linkedin, p.portfolio, resume.raw_text]
    for proj in resume.projects or []:
        out += [proj.github_link, proj.live_demo, proj.description, proj.name]
    for a in resume.achievements or []:
        out += [a.title, a.description]
    return [s for s in out if s]


def detect_handle(platform_id: str, resume: ParsedResume) -> str | None:
    """Return the handle for `platform_id` found in `resume`, or None.

    Searches the structured personal fields first (the parser already extracts
    github/linkedin/portfolio URLs), then scans the whole resume body.
    """
    if platform_id == "portfolio":
        url = (resume.personal.portfolio or "").strip()
        return _clean(url, "portfolio") or None

    entry = _PATTERNS.get(platform_id)
    if entry:
        pattern, group = entry
        for source in _text_sources(resume):
            m = re.search(pattern, source, re.IGNORECASE)
            if m:
                handle = _clean(m.group(group), platform_id)
                if handle:
                    return handle

    # Fallback: try text-based platform name + handle matching (e.g. "LeetCode aaravmehta")
    text_pattern = re.compile(rf"{platform_id}\s+([a-z0-9][a-z0-9_-]{0,38})", re.IGNORECASE)
    for source in _text_sources(resume):
        m = text_pattern.search(source)
        if m:
            handle = _clean(m.group(1), platform_id)
            if handle:
                return handle

    # Also try leetcode.com/username (without /u/ segment) as a shorthand
    if platform_id == "leetcode":
        short_pattern = re.compile(r"(?:leetcode\.com\/)(?!u\/)([a-z0-9][a-z0-9_-]{1,38})", re.IGNORECASE)
        for source in _text_sources(resume):
            m = short_pattern.search(source)
            if m:
                handle = _clean(m.group(1), platform_id)
                if handle:
                    return handle

    return None


def detect_all(resume: ParsedResume) -> dict[str, str]:
    """Map of platform id -> handle for every platform detectable in the resume."""
    handles: dict[str, str] = {}
    for platform_id in [*_PATTERNS, "portfolio"]:
        handle = detect_handle(platform_id, resume)
        if handle:
            handles[platform_id] = handle
    return handles