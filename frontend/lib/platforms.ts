import type { PlatformDef } from "./types";

export const PLATFORM_DEFS: PlatformDef[] = [
  { id: "github", label: "GitHub", icon: "gh", url_template: "https://github.com/{handle}", handle_placeholder: "username", real_api: true },
  { id: "gitlab", label: "GitLab", icon: "gl", url_template: "https://gitlab.com/{handle}", handle_placeholder: "username", real_api: false },
  { id: "bitbucket", label: "Bitbucket", icon: "bb", url_template: "https://bitbucket.org/{handle}", handle_placeholder: "workspace", real_api: false },
  { id: "linkedin", label: "LinkedIn", icon: "li", url_template: "https://linkedin.com/in/{handle}", handle_placeholder: "public profile id", real_api: true },
  { id: "portfolio", label: "Portfolio Website", icon: "pf", url_template: "https://{handle}", handle_placeholder: "example.com", real_api: false },
  { id: "devpost", label: "Devpost", icon: "dp", url_template: "https://devpost.com/{handle}", handle_placeholder: "username", real_api: false },
  { id: "leetcode", label: "LeetCode", icon: "lc", url_template: "https://leetcode.com/u/{handle}/", handle_placeholder: "username", real_api: true },
  { id: "interviewbit", label: "InterviewBit", icon: "ib", url_template: "https://www.interviewbit.com/profile/{handle}/", handle_placeholder: "username", real_api: true },
  { id: "codeforces", label: "Codeforces", icon: "cf", url_template: "https://codeforces.com/profile/{handle}", handle_placeholder: "handle", real_api: false },
  { id: "codechef", label: "CodeChef", icon: "cc", url_template: "https://codechef.com/users/{handle}", handle_placeholder: "username", real_api: false },
  { id: "geeksforgeeks", label: "GeeksforGeeks", icon: "gg", url_template: "https://auth.geeksforgeeks.org/user/{handle}", handle_placeholder: "username", real_api: false },
  { id: "hackerrank", label: "HackerRank", icon: "hr", url_template: "https://hackerrank.com/{handle}", handle_placeholder: "username", real_api: true },
  { id: "stackoverflow", label: "Stack Overflow", icon: "so", url_template: "https://stackoverflow.com/users/{handle}", handle_placeholder: "user id", real_api: false },
];

export const PLATFORM_CATEGORIES: Array<{ name: string; ids: string[] }> = [
  { name: "Code Hosting", ids: ["github", "gitlab", "bitbucket"] },
  { name: "Professional & Social", ids: ["linkedin", "portfolio"] },
  { name: "Coding & Competitions", ids: ["leetcode", "interviewbit", "codeforces", "codechef", "geeksforgeeks", "hackerrank", "stackoverflow"] },
  { name: "Hackathons", ids: ["devpost"] },
];

export const platformById = (id: string) => PLATFORM_DEFS.find((p) => p.id === id);