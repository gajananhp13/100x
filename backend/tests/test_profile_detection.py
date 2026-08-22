import pytest

from app.core.integrations.detection import detect_all, detect_handle
from app.core.integrations.demo import DEMO_RESUME_TEXT
from app.models.resume import ParsedResume


def _resume(text: str, github: str | None = None, linkedin: str | None = None, portfolio: str | None = None) -> ParsedResume:
    return ParsedResume(
        personal={"github": github, "linkedin": linkedin, "portfolio": portfolio},
        raw_text=text,
    )


def test_detect_github_from_personal_field():
    r = _resume("", github="https://github.com/octo")
    assert detect_handle("github", r) == "octo"


def test_detect_linkedin_from_personal_field():
    r = _resume("", linkedin="https://linkedin.com/in/jane-doe")
    assert detect_handle("linkedin", r) == "jane-doe"


def test_detect_leetcode_shorthand():
    r = _resume("LeetCode profile: leetcode.com/leetuser")
    assert detect_handle("leetcode", r) == "leetuser"


def test_detect_leetcode_u_path():
    r = _resume("LeetCode profile: leetcode.com/u/leetuser")
    assert detect_handle("leetcode", r) == "leetuser"


def test_ignore_generic_page_segments():
    r = _resume("leetcode.com/problems/two-sum github.com/topics/awesome")
    assert detect_handle("leetcode", r) is None
    assert detect_handle("github", r) is None


def test_portfolio_uses_personal_field():
    r = _resume("", portfolio="joedoe.dev")
    assert detect_handle("portfolio", r) == "joedoe.dev"


def test_unknown_platform_returns_none():
    r = _resume("myspace.com/ghost")
    assert detect_handle("myspace", r) is None


def test_detect_all_maps_every_platform():
    text = (
        "github.com/ab | linkedin.com/in/bb | leetcode.com/u/cc | codeforces.com/profile/dd | "
        "codechef.com/users/ee | hackerrank.com/ff | devpost.com/hh | twitch.tv/nope"
    )
    handles = detect_all(_resume(text))
    assert handles["github"] == "ab"
    assert handles["linkedin"] == "bb"
    assert handles["leetcode"] == "cc"
    assert handles["codeforces"] == "dd"
    assert handles["codechef"] == "ee"
    assert handles["hackerrank"] == "ff"
    assert handles["devpost"] == "hh"
    assert "kaggle" not in handles
    assert "medium" not in handles
    assert "devto" not in handles
    assert "hashnode" not in handles
    assert "twitter" not in handles
    assert "twitch" not in handles


def test_detect_strips_handle_decorations():
    r = _resume("github.com/@octo-cat/")
    assert detect_handle("github", r) == "octo-cat"


def test_demo_resume_detects_github_and_linkedin():
    r = ParsedResume(raw_text=DEMO_RESUME_TEXT)
    handles = detect_all(r)
    assert handles.get("github") == "aarav-mehta"
    assert handles.get("linkedin") == "aaravmehta"


def test_no_handles_when_resume_bare():
    r = _resume("Just a plain resume with no links anywhere.")
    assert detect_all(r) == {}