"use client";

import { RadarChart } from "@/components/charts";
import { Chip, ProgressBar, SectionHeader, ScoreRing, StatCard, StatusIndicator } from "@/components/ui";
import { SKILL_CATEGORY_LABELS, STATUS_LABELS } from "@/lib/types";
import type {
  AchievementVerification, AnalysisBundle, CodingAnalysis, CodingPlatformProfile,
  GitHubAnalysis, ParsedResume, ProjectVerification, ScoreItem, TechnologyVerification,
} from "@/lib/types";
import { ExternalLink, ChevronDown } from "lucide-react";

/* ── helpers ── */
const INDIGO = "#4f46e5";
const GREEN  = "#16a34a";
const AMBER  = "#d97706";
const MUTED  = "#a1a1aa";

/* ─────────────────────────────────────────────────────────────────── */
/* 1. Candidate Overview                                               */
/* ─────────────────────────────────────────────────────────────────── */
export function OverviewSection({ a }: { a: AnalysisBundle }) {
  const p = a.resume.personal;
  const edu = a.resume.education[0];
  const links = [
    p.github    && { label: "GitHub",    href: p.github },
    p.linkedin  && { label: "LinkedIn",  href: p.linkedin },
    p.portfolio && { label: "Portfolio", href: p.portfolio },
  ].filter(Boolean) as Array<{ label: string; href: string }>;

  return (
    <section>
      <SectionHeader index="1" title="Candidate Overview" />
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-6">
        {/* Top row */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold tracking-tight text-[#09090b]">{p.name || "Candidate"}</h3>
            {p.headline && (
              <p className="mt-0.5 text-sm text-[#71717a]">{p.headline}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {[p.location, p.email, p.phone].filter(Boolean).map((v) => (
                <Chip key={v}>{v}</Chip>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {links.map((l) => (
              <a
                key={l.label}
                href={l.href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] px-3 py-1.5 text-xs font-medium text-[#52525b] transition-colors hover:border-[#4f46e5]/40 hover:text-[#4f46e5]"
              >
                {l.label}
                <ExternalLink className="h-3 w-3" />
              </a>
            ))}
          </div>
        </div>

        {/* Education */}
        {edu && (
          <div className="mt-4 rounded-lg bg-[#f4f4f5] px-4 py-3 text-sm">
            <span className="font-semibold text-[#09090b]">{edu.degree || "Degree"}</span>
            {edu.branch     && <span className="text-[#71717a]"> · {edu.branch}</span>}
            {edu.college    && <span className="text-[#71717a]"> · {edu.college}</span>}
            {edu.graduation_year && <span className="text-[#71717a]"> · {edu.graduation_year}</span>}
            {edu.gpa        && <span className="text-[#71717a]"> · GPA {edu.gpa}</span>}
          </div>
        )}

        {/* Experience */}
        {a.resume.experience.length > 0 && (
          <div className="mt-4 space-y-3">
            {a.resume.experience.map((e, i) => (
              <div key={i} className="flex gap-3">
                <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#4f46e5]" />
                <div>
                  <div className="text-sm font-semibold text-[#09090b]">
                    {e.position || "Position"}
                    {e.company && (
                      <span className="font-normal text-[#71717a]"> · {e.company}</span>
                    )}
                  </div>
                  {e.duration && (
                    <div className="text-xs text-[#a1a1aa]">{e.duration}</div>
                  )}
                  {e.technologies.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {e.technologies.slice(0, 8).map((t) => (
                        <Chip key={t}>{t}</Chip>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 2. Resume Summary                                                   */
/* ─────────────────────────────────────────────────────────────────── */
export function ResumeSummarySection({ a }: { a: AnalysisBundle }) {
  const p = a.resume.personal;
  const experiences = a.resume.experience;
  const currentExp = experiences.find((e) => e.is_current);
  const pastExps = experiences.filter((e) => !e.is_current);

  const fmt = (e: { position?: string | null; company?: string | null }) =>
    e.company ? `${e.position || "Role"} @ ${e.company}` : (e.position || "Unknown Role");

  const expSummary = currentExp
    ? `Currently: ${fmt(currentExp)}${pastExps.length ? `. Past: ${pastExps.map(fmt).join("; ")}` : ""}`
    : pastExps.map(fmt).join("; ") || "no experience listed";

  const projectBrief = a.resume.projects.map((pr) => pr.name).filter(Boolean).join("; ") || "no projects listed";

  return (
    <section>
      <SectionHeader index="2" title="Resume Summary" subtitle="A plain-language overview of the parsed resume." />
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-6">
        <p className="text-sm leading-7 text-[#52525b]">
          <span className="font-semibold text-[#09090b]">{p.name || "The candidate"}</span> is a{" "}
          {experiences.length}-position professional ({expSummary}). Skills span{" "}
          {Object.values(a.resume.skills).flat().length} technologies. Portfolio projects:{" "}
          {projectBrief}. The resume lists {a.resume.achievements.length} achievement(s) and{" "}
          {a.resume.education.length} education record(s).
        </p>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 3. Skills Breakdown                                                 */
/* ─────────────────────────────────────────────────────────────────── */
export function SkillsSection({ a }: { a: AnalysisBundle }) {
  const entries = (Object.entries(a.resume.skills) as Array<[string, string[]]>).filter(([, v]) => v.length > 0);
  return (
    <section>
      <SectionHeader index="3" title="Skills Breakdown" subtitle="Technologies extracted and categorised from the resume." />
      {entries.length === 0 ? (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">
          No skills could be extracted from the resume.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {entries.map(([key, list]) => (
            <div key={key} className="rounded-xl border border-[#e4e4e7] bg-white p-4">
              <div className="mb-2.5 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">
                {SKILL_CATEGORY_LABELS[key] ?? key}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {list.map((s) => <Chip key={s}>{s}</Chip>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 4. Technical Verification                                           */
/* ─────────────────────────────────────────────────────────────────── */
export function TechnicalSection({ a }: { a: AnalysisBundle }) {
  const sv = a.skill_verifications;
  return (
    <section>
      <SectionHeader
        index="4"
        title="Technical Verification"
        subtitle="Every resume skill matched against public code evidence with a confidence score."
      />
      {sv.length === 0 ? (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">
          No skills to verify.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-[#e4e4e7] bg-white">
          {sv.map((v, i) => (
            <details key={v.technology} className="group border-b border-[#f0f0f2] last:border-0">
              <summary className="flex cursor-pointer list-none items-center gap-3 px-5 py-3 transition-colors hover:bg-[#fafafa]">
                <div className="w-36 shrink-0 text-sm font-semibold text-[#09090b]">{v.technology}</div>
                <div className="hidden w-32 shrink-0 text-xs text-[#a1a1aa] sm:block">
                  {SKILL_CATEGORY_LABELS[v.category] ?? v.category.replace("_", " ")}
                </div>
                <div className="min-w-[100px] flex-1">
                  <ProgressBar value={v.confidence * 100} height={4} />
                </div>
                <span className="w-12 shrink-0 text-right text-xs font-bold text-[#52525b]">
                  {Math.round(v.confidence * 100)}%
                </span>
                <div className="hidden sm:block">
                  <StatusIndicator status={v.status} label />
                </div>
                <ChevronDown className="h-4 w-4 shrink-0 text-[#a1a1aa] transition-transform group-open:rotate-180" />
              </summary>
              <div className="border-t border-[#f0f0f2] bg-[#f4f4f5] px-5 py-3 pl-[196px]">
                <ul className="space-y-1">
                  {v.evidence.map((ev, j) => (
                    <li key={j} className="text-xs leading-relaxed text-[#52525b]">· {ev}</li>
                  ))}
                </ul>
                <p className="mt-2 text-[10px] font-semibold uppercase tracking-wider text-[#a1a1aa]">
                  {STATUS_LABELS[v.status]} — absence of evidence is never treated as absence of skill.
                </p>
              </div>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 5. GitHub Analysis                                                  */
/* ─────────────────────────────────────────────────────────────────── */
export function GitHubSection({ g }: { g: GitHubAnalysis | null }) {
  if (!g) {
    return (
      <section>
        <SectionHeader index="5" title="GitHub Analysis" />
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">
          No GitHub profile was connected. GitHub is fetched live via the public API.
        </div>
      </section>
    );
  }

  const subscores: Array<[string, string, number]> = [
    ["Engineering",       "Commit depth, activity, language breadth, contributors",    g.score_engineering],
    ["Repository Quality","READMEs, CI/CD, Docker, stars, commit counts",              g.score_repo_quality],
    ["Open Source",       "Stars, forks, followers, public repositories",              g.score_open_source],
    ["Documentation",     "README quality + license coverage",                         g.score_documentation],
  ];
  const langs = Object.entries(g.language_usage);

  return (
    <section>
      <SectionHeader
        index="5"
        title="GitHub Analysis"
        subtitle={`@${g.username} — live or demo data from the connected GitHub profile.`}
      />

      {/* Stat row */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Public repos" value={g.public_repos} />
        <StatCard label="Stars" value={g.total_stars} />
        <StatCard label="Forks" value={g.total_forks} />
        <StatCard label="Followers" value={g.followers} />
      </div>

      {/* Subscores */}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {subscores.map(([label, desc, val]) => (
          <div key={label} className="rounded-xl border border-[#e4e4e7] bg-white p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[#09090b]">{label}</span>
              <span className="text-lg font-bold text-[#09090b]">{Math.round(val)}</span>
            </div>
            <ProgressBar value={val} className="mt-2" height={5} />
            <p className="mt-2 text-xs leading-relaxed text-[#71717a]">{desc}</p>
          </div>
        ))}
      </div>

      {/* Languages + Repos */}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {langs.length > 0 && (
          <div className="rounded-xl border border-[#e4e4e7] bg-white p-4">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Language usage</div>
            <div className="space-y-2.5">
              {langs.slice(0, 8).map(([lang, pct]) => (
                <div key={lang}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="font-medium text-[#52525b]">{lang}</span>
                    <span className="text-[#a1a1aa]">{Math.round(pct * 100)}%</span>
                  </div>
                  <ProgressBar value={pct * 100} height={4} color={INDIGO} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="thin-scroll max-h-72 overflow-auto rounded-xl border border-[#e4e4e7] bg-white p-4">
          <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Top repositories</div>
          <div className="space-y-1.5">
            {g.repos.slice(0, 10).map((r) => (
              <div key={r.full_name} className="flex items-center justify-between gap-2 rounded-lg bg-[#f4f4f5] px-3 py-2">
                <a
                  href={r.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="min-w-0 truncate text-xs font-semibold text-[#4f46e5] hover:underline"
                >
                  {r.name}
                </a>
                <div className="flex shrink-0 items-center gap-2 text-[11px] text-[#a1a1aa]">
                  {r.stars > 0   && <span>★ {r.stars}</span>}
                  {r.forks > 0   && <span>⑂ {r.forks}</span>}
                  <span>{r.commits_count}c</span>
                  {r.has_ci        && <span className="font-semibold text-[#16a34a]">CI</span>}
                  {r.has_dockerfile && <span className="font-semibold text-[#4f46e5]">Docker</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 6. Coding Platform Analysis                                         */
/* ─────────────────────────────────────────────────────────────────── */
export function CodingSection({ c }: { c: CodingAnalysis | null }) {
  if (!c || c.platforms.length === 0) {
    return (
      <section>
        <SectionHeader index="6" title="Coding Platform Analysis" />
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">
          No coding platform profiles were connected (LeetCode, Codeforces, CodeChef, GeeksforGeeks, HackerRank).
        </div>
      </section>
    );
  }

  const statText = (s: Record<string, unknown>): string => {
    const parts: string[] = [];
    if (s.total_solved)  parts.push(`${s.total_solved} solved`);
    if (s.rating)        parts.push(`rating ${s.rating}`);
    if (s.stars && !s.rating) parts.push(`${s.stars}★`);
    if (s.coding_score)  parts.push(`score ${s.coding_score}`);
    if (s.problems_solved && !s.total_solved) parts.push(`${s.problems_solved} solved`);
    if (s.reputation)    parts.push(`rep ${s.reputation}`);
    return parts.join(" · ") || "active";
  };

  return (
    <section>
      <SectionHeader index="6" title="Coding Platform Analysis" subtitle="Aggregated competitive programming and DSA evidence." />
      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <div className="flex flex-col items-center justify-center rounded-xl border border-[#e4e4e7] bg-white p-6">
          <ScoreRingOverlay value={c.problem_solving_score} label="Problem Solving" />
          <p className="mt-3 text-center text-xs leading-relaxed text-[#71717a]">{c.explanation}</p>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {c.platforms.map((p) =>
            p.platform === "leetcode" ? (
              <LeetCodeCard key={p.platform} p={p} />
            ) : p.platform === "hackerrank" ? (
              <HackerRankCard key={p.platform} p={p} />
            ) : (
              <div key={p.platform} className="rounded-xl border border-[#e4e4e7] bg-white p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[#09090b]">{p.platform_label}</span>
                  <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-[#4f46e5] hover:underline">
                    @{p.handle}
                  </a>
                </div>
                <div className="mt-1.5 text-sm text-[#71717a]">{statText(p.stats)}</div>
              </div>
            ),
          )}
        </div>
      </div>
    </section>
  );
}

/* ── LeetCode card ── */
function LeetCodeCard({ p }: { p: CodingPlatformProfile }) {
  const s = p.stats as Record<string, unknown>;
  const skills = s.skills as {
    fundamental?: { total: number; topics: Array<{ name: string; solved: number }> };
    intermediate?: { total: number; topics: Array<{ name: string; solved: number }> };
    advanced?: { total: number; topics: Array<{ name: string; solved: number }> };
  } | undefined;
  const recent = (s.recent_submissions as Array<{ title: string; status: string }>) || [];
  const contestHistory = (s.contest_history as Array<{ title: string; rating: number; ranking: number; total_participants: number; start_time: number }>) || [];

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-[#e4e4e7] bg-white p-5 sm:col-span-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-[#09090b]">{p.platform_label}</span>
        <a href={p.url} target="_blank" rel="noreferrer" className="text-xs font-medium text-[#4f46e5] hover:underline">
          @{p.handle}
        </a>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatCard label="Solved"          value={Number(s.total_solved) || 0}       sub={`/ ${Number(s.total_questions) || 0}`} />
        <StatCard label="Contest rating"  value={Number(s.contest_rating) || 0} />
        <StatCard label="Streak"          value={`${Number(s.streak_days) || 0}d`}  sub={s.total_active_days ? `${s.total_active_days} active` : undefined} />
        <StatCard label="Acceptance"      value={`${Number(s.acceptance_rate) || 0}%`} />
      </div>

      {/* Difficulty ring */}
      {(Number(s.easy) || Number(s.medium) || Number(s.hard)) > 0 && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Difficulty Breakdown</div>
          <div className="flex items-center gap-6">
            <DifficultyRing
              easy={Number(s.easy) || 0}
              medium={Number(s.medium) || 0}
              hard={Number(s.hard) || 0}
              total={Number(s.total_questions) || 0}
            />
            <div className="flex flex-col gap-2">
              {[
                { label: "Easy", count: Number(s.easy) || 0, total: Number(s.total_easy) || 0, color: "#0ea371" },
                { label: "Med.",  count: Number(s.medium) || 0, total: Number(s.total_medium) || 0, color: "#d97706" },
                { label: "Hard", count: Number(s.hard) || 0, total: Number(s.total_hard) || 0, color: "#e5484d" },
              ].map((d) => (
                <div key={d.label} className="flex items-center gap-2">
                  <span className="text-base font-bold" style={{ color: d.color }}>{d.count}</span>
                  <span className="text-xs text-[#a1a1aa]">/ {d.total || "—"}</span>
                  <span className="text-xs font-medium text-[#52525b]">{d.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Contest */}
      {(Number(s.contest_rating) > 0 || Number(s.attended_contests) > 0) && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Contest</div>
          <div className="rounded-xl border border-[#e4e4e7] bg-[#f4f4f5] p-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-[10px] font-semibold text-[#a1a1aa]">Rating</div>
                  <div className="text-2xl font-bold text-[#09090b]">{Number(s.contest_rating) || 0}</div>
                </div>
                {typeof s.contest_level === "string" && s.contest_level && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#eef2ff] px-2.5 py-1 text-xs font-bold text-[#4f46e5]">
                    {String(s.contest_level)}
                  </span>
                )}
              </div>
              <div className="flex gap-5">
                {Number(s.global_ranking) > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-[#a1a1aa]">Global rank</div>
                    <div className="text-sm font-bold text-[#09090b]">
                      {Number(s.global_ranking).toLocaleString()}
                      {Number(s.total_participants) > 0 && (
                        <span className="text-xs font-normal text-[#a1a1aa]"> / {Number(s.total_participants).toLocaleString()}</span>
                      )}
                    </div>
                    {Number(s.top_percentage) > 0 && (
                      <div className="text-[10px] font-semibold text-[#4f46e5]">Top {Number(s.top_percentage)}%</div>
                    )}
                  </div>
                )}
                {Number(s.attended_contests) > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-[#a1a1aa]">Attended</div>
                    <div className="text-sm font-bold text-[#09090b]">{Number(s.attended_contests)}</div>
                  </div>
                )}
              </div>
            </div>
            {contestHistory.length > 1 && (
              <div className="mt-3">
                <ContestRatingChart history={contestHistory} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Skills */}
      {(skills?.fundamental?.total || skills?.intermediate?.total || skills?.advanced?.total) ? (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Skill Set</div>
          <div className="grid grid-cols-3 gap-2">
            {(["fundamental", "intermediate", "advanced"] as const).map((key) => {
              const sec = skills[key];
              if (!sec || sec.total === 0) return null;
              const labels: Record<string, string> = { fundamental: "Fundamental", intermediate: "Intermediate", advanced: "Advanced" };
              return (
                <div key={key} className="rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] p-3">
                  <div className="text-xs font-bold text-[#52525b]">{labels[key]}</div>
                  <div className="text-xs text-[#a1a1aa]">{sec.total} solved</div>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {sec.topics.slice(0, 5).map((t) => (
                      <span key={t.name} className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-[#52525b]">
                        {t.name} ({t.solved})
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Recent submissions */}
      {recent.length > 0 && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Recent submissions</div>
          <div className="space-y-1">
            {recent.slice(0, 5).map((sub, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span
                  className="inline-block h-2 w-2 shrink-0 rounded-full"
                  style={{ background: sub.status === "Accepted" ? "#16a34a" : sub.status === "Wrong Answer" ? "#dc2626" : "#a1a1aa" }}
                />
                <span className="flex-1 truncate text-[#52525b]">{sub.title}</span>
                <span className="shrink-0 text-[#a1a1aa]">{sub.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Difficulty ring ── */
function DifficultyRing({ easy, medium, hard, total }: { easy: number; medium: number; hard: number; total: number }) {
  const size = 130;
  const stroke = 11;
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const solved = easy + medium + hard;
  const displayTotal = total || solved;

  const segments = [
    { count: easy,   color: "#0ea371" },
    { count: medium, color: "#d97706" },
    { count: hard,   color: "#e5484d" },
  ];

  let acc = 0;
  return (
    <div className="relative inline-flex shrink-0 items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f0f0f2" strokeWidth={stroke} />
        {segments.map(({ count, color }) => {
          if (count <= 0) return null;
          const frac = solved > 0 ? count / solved : 0;
          const len = frac * C;
          const offset = C - acc;
          acc += len;
          return (
            <circle key={color} cx={size / 2} cy={size / 2} r={r} fill="none"
              stroke={color} strokeWidth={stroke} strokeLinecap="round"
              strokeDasharray={`${len} ${C - len}`} strokeDashoffset={offset}
              style={{ transition: "all 0.7s ease" }}
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-xl font-bold text-[#09090b]">
          {solved}<span className="text-sm font-normal text-[#a1a1aa]">/{displayTotal}</span>
        </div>
        <div className="text-[10px] font-semibold text-[#16a34a]">Solved</div>
      </div>
    </div>
  );
}

/* ── Contest rating history ── */
function ContestRatingChart({ history }: { history: Array<{ rating: number; start_time: number }> }) {
  if (history.length < 2) return null;
  const sorted = [...history].sort((a, b) => a.start_time - b.start_time);
  const ratings = sorted.map((h) => h.rating);
  const minR = Math.min(...ratings);
  const maxR = Math.max(...ratings);
  const range = maxR - minR || 1;
  const pad = 8;
  const w = 480; const h = 72;
  const cW = w - pad * 2; const cH = h - pad * 2;
  const pts = sorted.map((entry, i) => {
    const x = pad + (i / (sorted.length - 1)) * cW;
    const y = pad + cH - ((entry.rating - minR) / range) * cH;
    return `${x},${y}`;
  });
  const last = pts[pts.length - 1].split(",");
  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
        {[0, 0.5, 1].map((f) => (
          <line key={f} x1={pad} y1={pad + cH * (1 - f)} x2={w - pad} y2={pad + cH * (1 - f)} stroke="#e4e4e7" strokeWidth={0.5} />
        ))}
        <polyline points={pts.join(" ")} fill="none" stroke="#f59e0b" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={last[0]} cy={last[1]} r={4} fill="#f59e0b" stroke="white" strokeWidth={2} />
      </svg>
      <div className="flex justify-between px-1 text-[10px] text-[#a1a1aa]">
        <span>{new Date(sorted[0].start_time * 1000).getFullYear()}</span>
        <span className="font-bold text-[#09090b]">{ratings[ratings.length - 1]}</span>
        <span>{new Date(sorted[sorted.length - 1].start_time * 1000).getFullYear()}</span>
      </div>
    </div>
  );
}

function ScoreRingOverlay({ value, label }: { value: number; label: string }) {
  const size = 120; const stroke = 9; const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const color = value >= 70 ? GREEN : value >= 40 ? AMBER : MUTED;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#f0f0f2" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={C}
          strokeDashoffset={C * (1 - Math.min(1, Math.max(0, value / 100)))}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-bold" style={{ color }}>{Math.round(value)}</div>
        <div className="text-[9px] font-bold uppercase tracking-wide text-[#a1a1aa]">{label}</div>
      </div>
    </div>
  );
}

/* ── HackerRank ── */
interface HackerRankBadge { name: string; stars: number; level: number; icon: string; solved: number; }

function HackerRankCard({ p }: { p: CodingPlatformProfile }) {
  const s = p.stats as Record<string, unknown>;
  const badges = (s.badges as HackerRankBadge[]) || [];
  const totalBadges = Number(s.total_badges) || badges.length;
  const stars = Number(s.stars) || 0;
  const problemsSolved = Number(s.problems_solved) || 0;
  const practiceScore = Number(s.practice_score) || 0;
  const ranking = Number(s.ranking) || 0;
  const contestCount = Number(s.contest_count) || 0;
  const contestRating = Number(s.contest_rating) || 0;

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-[#e4e4e7] bg-white p-5 sm:col-span-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-[#09090b]">{p.platform_label}</span>
        <a href={p.url} target="_blank" rel="noreferrer" className="text-xs font-medium text-[#4f46e5] hover:underline">
          @{p.handle}
        </a>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatCard label="Badges"          value={totalBadges}     sub={stars > 0 ? `${stars}★` : undefined} />
        <StatCard label="Problems solved" value={problemsSolved} />
        <StatCard label="Practice score"  value={practiceScore} />
        <StatCard label="Best rank"       value={ranking || "—"}  sub={contestCount > 0 ? `${contestCount} contests` : undefined} />
      </div>

      {contestRating > 0 && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Contest rating</div>
          <span className="text-2xl font-bold text-[#09090b]">{contestRating}</span>
        </div>
      )}

      {badges.length > 0 && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Badges ({badges.length})</div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {badges.map((badge, i) => (
              <div key={`${badge.name}-${i}`} className="rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] p-2.5">
                <div className="flex items-center gap-2">
                  {badge.icon && (
                    <img src={badge.icon} alt={badge.name} className="h-6 w-6 shrink-0 rounded object-contain"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  )}
                  <div className="min-w-0">
                    <div className="truncate text-xs font-semibold text-[#09090b]">{badge.name}</div>
                    <div className="flex items-center gap-0.5 mt-0.5">
                      {Array.from({ length: 3 }, (_, si) => (
                        <svg key={si} className="h-3 w-3" fill={si < badge.stars ? "#d97706" : "#e4e4e7"} viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                  </div>
                </div>
                {badge.solved > 0 && <div className="mt-1 text-[10px] text-[#a1a1aa]">{badge.solved} solved</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(s.active_tracks) && s.active_tracks.length > 0 && (
        <div>
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Active tracks</div>
          <div className="flex flex-wrap gap-1.5">
            {(s.active_tracks as string[]).map((track) => <Chip key={track}>{track}</Chip>)}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 7. Project Verification                                             */
/* ─────────────────────────────────────────────────────────────────── */
export function ProjectsSection({ pv }: { pv: ProjectVerification[] }) {
  return (
    <section>
      <SectionHeader index="7" title="Project Verification" subtitle="Every resume project matched against public repositories." />
      {pv.length === 0 ? (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">No projects to verify.</div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-3">
          {pv.map((p) => (
            <div key={p.project_name} className="flex flex-col rounded-xl border border-[#e4e4e7] bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-bold text-[#09090b]">{p.project_name}</h4>
                <StatusIndicator status={p.status} label />
              </div>
              {p.description && (
                <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-[#71717a]">{p.description}</p>
              )}

              <div className="mt-3 flex items-center gap-2">
                <ProgressBar value={p.score} className="flex-1" height={5} />
                <span className="shrink-0 text-xs font-bold text-[#52525b]">{Math.round(p.score)}</span>
              </div>

              <div className="mt-2.5 flex flex-wrap gap-1">
                {p.repository_exists  && <Chip tone="success">Repo matched</Chip>}
                {p.deployment_exists  && <Chip tone="brand">Deployed</Chip>}
                {p.recent_activity    && <Chip>Active</Chip>}
                {p.documentation_exists && <Chip>Documented</Chip>}
                {!p.repository_exists && <Chip className="text-[#a1a1aa]">No public repo</Chip>}
              </div>

              {p.matched_repo && (
                <a
                  href={`https://github.com/${p.matched_repo}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-[#4f46e5] hover:underline"
                >
                  {p.matched_repo} <ExternalLink className="h-3 w-3" />
                </a>
              )}

              <details className="mt-2 text-xs">
                <summary className="cursor-pointer font-medium text-[#a1a1aa] hover:text-[#52525b]">Evidence</summary>
                <ul className="mt-1 space-y-0.5 text-[#71717a]">
                  {p.evidence.map((ev, i) => <li key={i}>· {ev}</li>)}
                </ul>
              </details>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 8. Achievement Verification                                         */
/* ─────────────────────────────────────────────────────────────────── */
export function AchievementsSection({ av }: { av: AchievementVerification[] }) {
  return (
    <section>
      <SectionHeader
        index="8"
        title="Achievement Verification"
        subtitle="Awards, certifications, hackathons and contributions checked against connected platforms."
      />
      {av.length === 0 ? (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-5 text-sm text-[#71717a]">No achievements to verify.</div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-[#e4e4e7] bg-white">
          {av.map((a, i) => (
            <div
              key={i}
              className="flex items-start gap-4 border-b border-[#f0f0f2] px-5 py-4 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-[#09090b]">{a.title}</span>
                  <Chip className="text-[10px] uppercase">{a.type}</Chip>
                </div>
                {a.evidence.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {a.evidence.map((ev, j) => (
                      <li key={j} className="text-xs leading-relaxed text-[#71717a]">· {ev}</li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="shrink-0">
                <StatusIndicator status={a.status} label />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 9. Strengths                                                        */
/* ─────────────────────────────────────────────────────────────────── */
export function StrengthsSection({ strengths }: { strengths: string[] }) {
  return (
    <section>
      <SectionHeader index="9" title="Strengths" subtitle="Top engineering strengths backed by public evidence." />
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-5">
        {strengths.length === 0 ? (
          <p className="text-sm text-[#71717a]">No strengths with strong evidence could be inferred.</p>
        ) : (
          <ul className="space-y-2.5">
            {strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#f0fdf4]">
                  <span className="text-[10px] font-bold text-[#16a34a]">✓</span>
                </span>
                <span className="text-sm leading-relaxed text-[#52525b]">{s}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 10. Improvement Areas                                               */
/* ─────────────────────────────────────────────────────────────────── */
export function ImprovementsSection({ improvements }: { improvements: string[] }) {
  return (
    <section>
      <SectionHeader
        index="10"
        title="Improvement Areas"
        subtitle="Claims with limited or no public evidence — opportunities, not accusations."
      />
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-5">
        {improvements.length === 0 ? (
          <p className="text-sm text-[#71717a]">No gaps identified.</p>
        ) : (
          <ul className="space-y-2.5">
            {improvements.map((s, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#fffbeb]">
                  <span className="text-[10px] font-bold text-[#d97706]">!</span>
                </span>
                <span className="text-sm leading-relaxed text-[#52525b]">{s}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 11. AI Summary                                                      */
/* ─────────────────────────────────────────────────────────────────── */
const AI_SUMMARY_ORDER: Array<[string, string]> = [
  ["technical_strengths",     "Technical strengths"],
  ["engineering_profile",     "Engineering profile"],
  ["coding_ability",          "Coding ability"],
  ["project_quality",         "Project quality"],
  ["collaboration_indicators","Collaboration indicators"],
  ["learning_consistency",    "Learning consistency"],
  ["areas_to_improve",        "Areas to improve"],
];

export function AISummarySection({ summary }: { summary: Record<string, string> }) {
  return (
    <section>
      <SectionHeader index="11" title="AI Candidate Summary" subtitle="Recruiter-friendly assessment generated from evidence only." />
      <div className="overflow-hidden rounded-xl border border-[#e4e4e7] bg-white">
        {AI_SUMMARY_ORDER.map(([key, label], i) =>
          summary[key] ? (
            <div
              key={key}
              className="border-b border-[#f0f0f2] px-6 py-4 last:border-0"
            >
              <h4 className="mb-1.5 text-xs font-bold uppercase tracking-widest text-[#4f46e5]">{label}</h4>
              <p className="text-sm leading-7 text-[#52525b]">{summary[key]}</p>
            </div>
          ) : null,
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* 12. Final Scores                                                    */
/* ─────────────────────────────────────────────────────────────────── */
export function ScoresSection({ scores, radarItems }: { scores: ScoreItem[]; radarItems: Array<[string, number]> }) {
  return (
    <section>
      <SectionHeader index="12" title="Final Scores" subtitle="Every score is explainable and evidence-backed — 0–100 scale." />
      <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
        {/* Radar */}
        <div className="flex flex-col items-center justify-center rounded-xl border border-[#e4e4e7] bg-white p-5">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa]">Score Radar</div>
          <RadarChart items={radarItems} size={270} labelSize={8.5} />
        </div>

        {/* Score list */}
        <div className="space-y-2">
          {scores.map((s) => {
            const color =
              s.value >= 70 ? GREEN :
              s.value >= 40 ? AMBER :
                              MUTED;
            return (
              <div key={s.key} className="flex items-center gap-4 rounded-xl border border-[#e4e4e7] bg-white px-5 py-4">
                <div className="flex w-40 shrink-0 flex-col">
                  <span className="text-sm font-semibold text-[#09090b]">{s.label}</span>
                  <span className="text-2xl font-bold" style={{ color }}>{Math.round(s.value)}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <ProgressBar value={s.value} height={6} />
                  <p className="mt-2 text-xs leading-relaxed text-[#71717a]">{s.explanation}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
