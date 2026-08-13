import {
  siGithub,
  siGitlab,
  siBitbucket,
  siDevpost,
  siKaggle,
  siLeetcode,
  siCodeforces,
  siCodechef,
  siGeeksforgeeks,
  siHackerrank,
  siStackoverflow,
  siMedium,
  siHashnode,
  siDevdotto,
  siX,
} from "simple-icons";
import { cn } from "./ui";

const BRAND_BG: Record<string, string> = {
  github: "#0d1117",
  gitlab: "#fc6d26",
  bitbucket: "#0052cc",
  linkedin: "#0a66c2",
  portfolio: "#5b5bd6",
  devpost: "#003e54",
  kaggle: "#20beff",
  leetcode: "#ffa116",
  interviewbit: "#0076d2",
  codeforces: "#1f8acb",
  codechef: "#5B4638",
  geeksforgeeks: "#2f8d46",
  hackerrank: "#1ba94c",
  stackoverflow: "#f48024",
  medium: "#000000",
  hashnode: "#2962ff",
  devto: "#0a0a0a",
  twitter: "#000000",
};

const SI_ICONS: Record<string, { path: string; hex: string }> = {
  github: siGithub,
  gitlab: siGitlab,
  bitbucket: siBitbucket,
  devpost: siDevpost,
  kaggle: siKaggle,
  leetcode: siLeetcode,
  codeforces: siCodeforces,
  codechef: siCodechef,
  geeksforgeeks: siGeeksforgeeks,
  hackerrank: siHackerrank,
  stackoverflow: siStackoverflow,
  medium: siMedium,
  hashnode: siHashnode,
  devto: siDevdotto,
  twitter: siX,
};

const FALLBACK_INITIALS: Record<string, string> = {
  linkedin: "in",
  interviewbit: "IB",
  portfolio: "Pf",
};

const DARK_LOGO_PLATFORMS = new Set(["kaggle"]);

export function PlatformIcon({
  id,
  label,
  size = 36,
  className,
}: {
  id: string;
  label: string;
  size?: number;
  className?: string;
}) {
  const bg = BRAND_BG[id] ?? "#e6e8ef";
  const icon = SI_ICONS[id];

  if (icon) {
    const fill = DARK_LOGO_PLATFORMS.has(id) ? "#000000" : "#ffffff";
    return (
      <span
        className={cn("inline-flex shrink-0 items-center justify-center rounded-lg", className)}
        style={{ width: size, height: size, backgroundColor: bg }}
        title={label}
        aria-hidden
      >
        <svg
          viewBox="0 0 24 24"
          width={size * 0.55}
          height={size * 0.55}
          fill={fill}
          xmlns="http://www.w3.org/2000/svg"
          style={{ display: "block" }}
        >
          <path d={icon.path} />
        </svg>
      </span>
    );
  }

  const initials = FALLBACK_INITIALS[id] ?? id.slice(0, 2).toUpperCase();
  const fg = id === "kaggle" || id === "leetcode" ? "#0b0f19" : "#ffffff";
  return (
    <span
      className={cn("inline-flex shrink-0 items-center justify-center rounded-lg font-bold", className)}
      style={{ width: size, height: size, backgroundColor: bg, color: fg, fontSize: size * 0.34 }}
      title={label}
      aria-hidden
    >
      {initials}
    </span>
  );
}
