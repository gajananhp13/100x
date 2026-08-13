"""One module per platform — each defines its own PlatformDef (DEF) and
*Integration class. Real platforms (GitHub, LeetCode) collect live data with an
offline simulation fallback; the rest are deterministic simulations.

Adding a real API for any platform means editing only that platform's file.
"""

from __future__ import annotations

from ..base import PlatformDef, PlatformIntegration
from .bitbucket import BitbucketIntegration, DEF as BITBUCKET_DEF
from .codechef import CodeChefIntegration, DEF as CODECHEF_DEF
from .codeforces import CodeforcesIntegration, DEF as CODEFORCES_DEF
from .devpost import DevpostIntegration, DEF as DEVPOST_DEF
from .devto import DevtoIntegration, DEF as DEVTO_DEF
from .geeksforgeeks import GeeksforGeeksIntegration, DEF as GEEKSFORGEEKS_DEF
from .github import GitHubIntegration, DEF as GITHUB_DEF
from .gitlab import GitLabIntegration, DEF as GITLAB_DEF
from .hackerrank import HackerRankIntegration, DEF as HACKERRANK_DEF
from .hashnode import HashnodeIntegration, DEF as HASHNODE_DEF
from .interviewbit import InterviewBitIntegration, DEF as INTERVIEWBIT_DEF
from .kaggle import KaggleIntegration, DEF as KAGGLE_DEF
from .leetcode import LeetCodeIntegration, DEF as LEETCODE_DEF
from .linkedin import LinkedInIntegration, DEF as LINKEDIN_DEF
from .medium import MediumIntegration, DEF as MEDIUM_DEF
from .portfolio import PortfolioIntegration, DEF as PORTFOLIO_DEF
from .stackoverflow import StackOverflowIntegration, DEF as STACKOVERFLOW_DEF
from .twitter import TwitterIntegration, DEF as TWITTER_DEF

# Catalog order drives the connect UI
PLATFORMS: list[PlatformDef] = [
    GITHUB_DEF,
    GITLAB_DEF,
    BITBUCKET_DEF,
    LINKEDIN_DEF,
    PORTFOLIO_DEF,
    DEVPOST_DEF,
    KAGGLE_DEF,
    LEETCODE_DEF,
    INTERVIEWBIT_DEF,
    CODEFORCES_DEF,
    CODECHEF_DEF,
    GEEKSFORGEEKS_DEF,
    HACKERRANK_DEF,
    STACKOVERFLOW_DEF,
    MEDIUM_DEF,
    HASHNODE_DEF,
    DEVTO_DEF,
    TWITTER_DEF,
]

_INTEGRATION_CLASSES = (
    GitHubIntegration,
    GitLabIntegration,
    BitbucketIntegration,
    LinkedInIntegration,
    PortfolioIntegration,
    DevpostIntegration,
    KaggleIntegration,
    LeetCodeIntegration,
    InterviewBitIntegration,
    CodeforcesIntegration,
    CodeChefIntegration,
    GeeksforGeeksIntegration,
    HackerRankIntegration,
    StackOverflowIntegration,
    MediumIntegration,
    HashnodeIntegration,
    DevtoIntegration,
    TwitterIntegration,
)

INTEGRATIONS: dict[str, type[PlatformIntegration]] = {
    cls.platform_id: cls for cls in _INTEGRATION_CLASSES
}

__all__ = [
    "BitbucketIntegration",
    "CodeChefIntegration",
    "CodeforcesIntegration",
    "DevpostIntegration",
    "DevtoIntegration",
    "GeeksforGeeksIntegration",
    "GitHubIntegration",
    "GitLabIntegration",
    "HackerRankIntegration",
    "HashnodeIntegration",
    "InterviewBitIntegration",
    "INTEGRATIONS",
    "KaggleIntegration",
    "LeetCodeIntegration",
    "LinkedInIntegration",
    "MediumIntegration",
    "PLATFORMS",
    "PortfolioIntegration",
    "StackOverflowIntegration",
    "TwitterIntegration",
]
