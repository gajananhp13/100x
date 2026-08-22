// TypeScript mirror of the backend Pydantic models (backend/app/models/*).

export type VerificationStatus =
  | "verified"
  | "strong_evidence"
  | "partial_evidence"
  | "limited_evidence"
  | "no_public_evidence";

export interface PersonalDetails {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  portfolio?: string | null;
  github?: string | null;
  linkedin?: string | null;
  headline?: string | null;
}

export interface Education {
  college?: string | null;
  degree?: string | null;
  branch?: string | null;
  graduation_year?: string | null;
  gpa?: string | null;
}

export interface Experience {
  company?: string | null;
  position?: string | null;
  duration?: string | null;
  is_current?: boolean;
  responsibilities: string[];
  technologies: string[];
}

export interface SkillsBreakdown {
  programming_languages: string[];
  frontend: string[];
  backend: string[];
  databases: string[];
  devops: string[];
  cloud: string[];
  ai_ml: string[];
  mobile: string[];
  tools: string[];
  testing: string[];
  other: string[];
}

export interface Project {
  name?: string | null;
  description?: string | null;
  tech_stack: string[];
  features: string[];
  github_link?: string | null;
  live_demo?: string | null;
  apis_used: string[];
  database?: string | null;
  deployment?: string | null;
}

export interface Achievement {
  type: string;
  title: string;
  description?: string | null;
  platform?: string | null;
  date?: string | null;
}

export interface ParsedResume {
  personal: PersonalDetails;
  education: Education[];
  experience: Experience[];
  skills: SkillsBreakdown;
  projects: Project[];
  achievements: Achievement[];
  raw_text: string;
}

export interface ConnectedProfile {
  platform: string;
  platform_label: string;
  handle: string;
  profile_url?: string | null;
  status: "collected" | "failed" | "pending";
  collected_at?: string | null;
  error?: string | null;
  data: Record<string, unknown>;
}

export interface TechnologyVerification {
  technology: string;
  category: string;
  confidence: number;
  status: VerificationStatus;
  evidence: string[];
}

export interface RepoAnalysis {
  name: string;
  full_name: string;
  description?: string | null;
  html_url: string;
  homepage?: string | null;
  stars: number;
  forks: number;
  watchers: number;
  open_issues: number;
  language?: string | null;
  languages: Record<string, number>;
  license_name?: string | null;
  topics: string[];
  created_at?: string | null;
  pushed_at?: string | null;
  has_readme: boolean;
  readme_quality: number;
  has_ci: boolean;
  has_dockerfile: boolean;
  commits_count: number;
  contributors_count: number;
  open_prs: number;
  is_fork: boolean;
  tech_hits: Record<string, number>;
}

export interface GitHubAnalysis {
  username: string;
  avatar_url?: string | null;
  public_repos: number;
  total_stars: number;
  total_forks: number;
  followers: number;
  following: number;
  account_created_at?: string | null;
  language_usage: Record<string, number>;
  repos: RepoAnalysis[];
  repos_with_ci: number;
  repos_with_docker: number;
  repos_with_readme: number;
  avg_readme_quality: number;
  avg_commits_per_repo: number;
  score_engineering: number;
  score_repo_quality: number;
  score_open_source: number;
  score_documentation: number;
}

export interface CodingPlatformProfile {
  platform: string;
  platform_label: string;
  handle: string;
  url: string;
  stats: Record<string, unknown>;
}

export interface CodingAnalysis {
  platforms: CodingPlatformProfile[];
  problem_solving_score: number;
  explanation: string;
}

export interface ProjectVerification {
  project_name: string;
  description?: string | null;
  tech_stack: string[];
  matched_repo?: string | null;
  repository_exists: boolean;
  deployment_exists: boolean;
  recent_activity: boolean;
  documentation_exists: boolean;
  architecture_complexity: number;
  score: number;
  status: VerificationStatus;
  evidence: string[];
}

export interface AchievementVerification {
  title: string;
  type: string;
  claimed_platform?: string | null;
  score: number;
  status: VerificationStatus;
  evidence: string[];
}

export interface ScoreItem {
  key: string;
  label: string;
  value: number;
  explanation: string;
}

export interface AnalysisBundle {
  resume: ParsedResume;
  profiles: ConnectedProfile[];
  github?: GitHubAnalysis | null;
  coding?: CodingAnalysis | null;
  skill_verifications: TechnologyVerification[];
  project_verifications: ProjectVerification[];
  achievement_verifications: AchievementVerification[];
  strengths: string[];
  improvements: string[];
  ai_summary: Record<string, string>;
  scores: ScoreItem[];
  overall_score: number;
}

export interface CandidateReport {
  report_id: string;
  generated_at: string;
  analysis: AnalysisBundle;
}

export interface PlatformDef {
  id: string;
  label: string;
  icon: string;
  url_template: string;
  handle_placeholder: string;
  real_api: boolean;
}

export interface PlatformCategory {
  name: string;
  platforms: PlatformDef[];
}

export interface PlatformsResponse {
  categories: Record<string, PlatformDef[]>;
  platforms: PlatformDef[];
}

/** A single resume inside an HR batch (multi-resume ranking flow). */
export interface ResumeBatchCandidate {
  index: number;
  filename: string;
  resume: ParsedResume;
  text_preview?: string;
  profiles?: ConnectedProfile[];
  detected?: Record<string, string>;
  report_id?: string;
  candidate_name?: string;
  overall_score?: number;
  rank?: number;
  scores?: ScoreItem[];
}

/** Server response for batch upload and batch validate. */
export interface ResumeBatchResult {
  processed: number;
  failed: number;
  candidates: ResumeBatchCandidate[];
  errors: Array<{ filename: string; detail: string }>;
}

/** Server response for batch connect. */
export interface ResumeBatchConnectResult {
  candidates: ResumeBatchCandidate[];
}

export const SKILL_CATEGORY_LABELS: Record<string, string> = {
  programming_languages: "Programming Languages",
  frontend: "Frontend",
  backend: "Backend",
  databases: "Databases",
  devops: "DevOps",
  cloud: "Cloud",
  ai_ml: "AI / ML",
  mobile: "Mobile",
  tools: "Tools",
  testing: "Testing",
  other: "Other",
};

export const STATUS_LABELS: Record<VerificationStatus, string> = {
  verified: "Verified",
  strong_evidence: "Strong Evidence",
  partial_evidence: "Partial Evidence",
  limited_evidence: "Limited Evidence",
  no_public_evidence: "No Public Evidence",
};
