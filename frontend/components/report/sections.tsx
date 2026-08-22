"use client";

import { RadarChart } from "@/components/charts";
import { StatusBadge, Card, Chip, ProgressBar, SectionHeader, Stat } from "@/components/ui";
import { SKILL_CATEGORY_LABELS, STATUS_LABELS } from "@/lib/types";
import type {
  AchievementVerification,
  AnalysisBundle,
  CodingAnalysis,
  CodingPlatformProfile,
  GitHubAnalysis,
  ParsedResume,
  ProjectVerification,
  ScoreItem,
  TechnologyVerification,
} from "@/lib/types";

const toneFor = (v: number) =>
  v >= 80 ? "emerald" : v >= 60 ? "accent" : v >= 40 ? "amber" : "rose";

/* ---------------------------------------------------------------- */
/* 1. Candidate Overview                                            */
/* ---------------------------------------------------------------- */
export function OverviewSection({ a }: { a: AnalysisBundle }) {
  const p = a.resume.personal;
  const edu = a.resume.education[0];
  const links = [
    p.github && { label: "GitHub", href: p.github },
    p.linkedin && { label: "LinkedIn", href: p.linkedin },
    p.portfolio && { label: "Portfolio", href: p.portfolio },
  ].filter(Boolean) as Array<{ label: string; href: string }>;

  return (
    <section>
      <SectionHeader index="1" title="Candidate Overview" />
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold text-ink">{p.name || "Candidate"}</h3>
            {p.headline && <p className="mt-0.5 text-sm text-muted">{p.headline}</p>}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {[p.location, p.email, p.phone].filter(Boolean).map((v) => (
                <Chip key={v}>{v}</Chip>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {links.map((l) => (
              <a
                key={l.label}
                href={l.href}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-accent hover:border-accent/40"
              >
                {l.label} ↗
              </a>
            ))}
          </div>
        </div>

        {edu && (
          <div className="mt-4 rounded-lg bg-slate-soft/60 p-3 text-sm">
            <span className="font-semibold text-ink">{edu.degree || "Degree"}</span>
            {edu.branch && <span> · {edu.branch}</span>}
            {edu.college && <span> · {edu.college}</span>}
            {edu.graduation_year && <span> · grad {edu.graduation_year}</span>}
            {edu.gpa && <span> · GPA {edu.gpa}</span>}
          </div>
        )}

        {a.resume.experience.length > 0 && (
          <div className="mt-4 space-y-3">
            {a.resume.experience.map((e, i) => (
              <div key={i} className="border-l-2 border-line pl-3">
                <div className="text-sm font-semibold text-ink">
                  {e.position || "Position"}
                  {e.company && <span className="text-muted"> · {e.company}</span>}
                </div>
                {e.duration && <div className="text-xs text-muted">{e.duration}</div>}
                {e.technologies.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {e.technologies.slice(0, 8).map((t) => (
                      <Chip key={t}>{t}</Chip>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 2. Resume Summary                                                */
/* ---------------------------------------------------------------- */
export function ResumeSummarySection({ a }: { a: AnalysisBundle }) {
  const p = a.resume.personal;
  const experiences = a.resume.experience;
  const currentExp = experiences.find((e) => e.is_current);
  const pastExps = experiences.filter((e) => !e.is_current);

  const formatExp = (e: { position?: string | null; company?: string | null }) => {
    const pos = e.position || "Unknown Role";
    const comp = e.company;
    return comp ? `${pos} @ ${comp}` : pos;
  };

  const currentBrief = currentExp ? formatExp(currentExp) : null;
  const pastBrief = pastExps.map(formatExp).join("; ");
  const expSummary = currentBrief
    ? `Currently: ${currentBrief}${pastBrief ? `. Past: ${pastBrief}` : ""}`
    : pastBrief || "no experience listed";

  const projectBrief = a.resume.projects.map((pr) => pr.name).filter(Boolean).join("; ") || "no projects listed";
  const achievementCount = a.resume.achievements.length;

  return (
    <section>
      <SectionHeader index="2" title="Resume Summary" subtitle="A plain-language overview of the parsed resume." />
      <Card>
        <p className="text-sm leading-relaxed text-ink-2">
          {p.name || "The candidate"} is a {experiences.length}-position professional ({expSummary}).
          Skills span {Object.values(a.resume.skills).flat().length} technologies. Portfolio projects:{" "}
          {projectBrief}. The resume lists {achievementCount} achievement(s) and{" "}
          {a.resume.education.length} education record(s).
        </p>
      </Card>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 3. Skills Breakdown                                              */
/* ---------------------------------------------------------------- */
export function SkillsSection({ a }: { a: AnalysisBundle }) {
  const entries = (Object.entries(a.resume.skills) as Array<[string, string[]]>).filter(([, v]) => v.length > 0);
  return (
    <section>
      <SectionHeader index="3" title="Skills Breakdown" subtitle="Technologies extracted and categorized from the resume." />
      {entries.length === 0 ? (
        <Card><p className="text-sm text-muted">No skills could be extracted from the resume.</p></Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {entries.map(([key, list]) => (
            <Card key={key} className="flex flex-wrap content-start gap-1.5">
              <div className="w-full text-xs font-semibold uppercase tracking-wide text-muted">
                {SKILL_CATEGORY_LABELS[key] ?? key}
              </div>
              {list.map((s) => (
                <Chip key={s}>{s}</Chip>
              ))}
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 4. Technical Verification                                        */
/* ---------------------------------------------------------------- */
export function TechnicalSection({ a }: { a: AnalysisBundle }) {
  const sv = a.skill_verifications;
  return (
    <section>
      <SectionHeader index="4" title="Technical Verification" subtitle="Every resume skill matched against public code evidence with a confidence score." />
      {sv.length === 0 ? (
        <Card><p className="text-sm text-muted">No skills to verify.</p></Card>
      ) : (
        <Card padded={false} className="divide-y divide-line">
          {sv.map((v) => (
            <details key={v.technology} className="group px-5 py-3">
              <summary className="flex cursor-pointer list-none items-center gap-3">
                <div className="w-40 shrink-0 text-sm font-medium text-ink">{v.technology}</div>
                <div className="hidden w-32 shrink-0 text-xs text-muted sm:block">
                  {SKILL_CATEGORY_LABELS[v.category] ?? v.category.replace("_", " ")}
                </div>
                <div className="min-w-[120px] flex-1">
                  <ProgressBar value={v.confidence * 100} tone={toneFor(v.confidence * 100)} />
                </div>
                <span className="w-20 text-right text-xs font-semibold text-ink-2">
                  {Math.round(v.confidence * 100)}%
                </span>
                <StatusBadge status={v.status} className="hidden sm:inline-flex" />
              </summary>
              <div className="mt-2 space-y-1 pl-[187px]">
                {v.evidence.map((ev, i) => (
                  <p key={i} className="text-xs leading-relaxed text-muted">• {ev}</p>
                ))}
                <p className="text-[11px] uppercase tracking-wide text-slate">
                  {STATUS_LABELS[v.status]} — absence of evidence is never treated as absence of a skill.
                </p>
              </div>
            </details>
          ))}
        </Card>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 5. GitHub Analysis                                               */
/* ---------------------------------------------------------------- */
export function GitHubSection({ g }: { g: GitHubAnalysis | null }) {
  if (!g) {
    return (
      <section>
        <SectionHeader index="5" title="GitHub Analysis" />
        <Card><p className="text-sm text-muted">No GitHub profile was connected, so engineering evidence is unavailable. GitHub is fetched live via the public API.</p></Card>
      </section>
    );
  }
  const subscores: Array<[string, string, number]> = [
    ["Engineering", "Commit depth, activity, language breadth, contributors", g.score_engineering],
    ["Repository Quality", "READMEs, CI/CD, Docker, stars, commit counts", g.score_repo_quality],
    ["Open Source", "Stars, forks, followers, public repositories", g.score_open_source],
    ["Documentation", "README quality + license coverage", g.score_documentation],
  ];
  const langs = Object.entries(g.language_usage);
  return (
    <section>
      <SectionHeader index="5" title="GitHub Analysis" subtitle={`@${g.username} — live or demo data from the connected GitHub profile.`} />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Public repos" value={g.public_repos} />
        <Stat label="Stars" value={g.total_stars} />
        <Stat label="Forks" value={g.total_forks} />
        <Stat label="Followers" value={g.followers} />
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {subscores.map(([label, desc, val]) => (
          <Card key={label}>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-ink">{label}</span>
              <span className="font-semibold text-ink-2">{Math.round(val)}</span>
            </div>
            <ProgressBar value={val} tone={toneFor(val)} className="mt-2" />
            <div className="mt-1.5 text-xs text-muted">{desc} · {g.avg_readme_quality >= 0 ? `README avg ${Math.round(g.avg_readme_quality * 100)}% ` : ""}· CI on {g.repos_with_ci} repos, Docker on {g.repos_with_docker}</div>
          </Card>
        ))}
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {langs.length > 0 && (
          <Card>
            <div className="mb-2 text-sm font-semibold text-ink">Language usage</div>
            <div className="space-y-2">
              {langs.slice(0, 8).map(([lang, pct]) => (
                <div key={lang}>
                  <div className="flex justify-between text-xs">
                    <span className="text-ink-2">{lang}</span>
                    <span className="text-muted">{Math.round(pct * 100)}%</span>
                  </div>
                  <ProgressBar value={pct * 100} className="mt-1" tone="slate" />
                </div>
              ))}
            </div>
          </Card>
        )}
        <Card className="thin-scroll max-h-72 overflow-auto">
          <div className="mb-2 text-sm font-semibold text-ink">Top repositories</div>
          <div className="space-y-2">
            {g.repos.slice(0, 10).map((r) => (
              <div key={r.full_name} className="flex items-center justify-between gap-2 rounded-md bg-slate-soft/50 px-2.5 py-1.5">
                <a href={r.html_url} target="_blank" rel="noreferrer" className="min-w-0 truncate text-xs font-semibold text-accent hover:underline">
                  {r.name}
                </a>
                <div className="flex shrink-0 gap-2 text-[11px] text-muted">
                  {r.stars > 0 && <span>★ {r.stars}</span>}
                  {r.forks > 0 && <span>⑂ {r.forks}</span>}
                  <span>{r.commits_count} commits</span>
                  {r.has_ci && <span className="text-emerald">CI</span>}
                  {r.has_dockerfile && <span className="text-accent">Docker</span>}
                  {r.homepage && <span className="text-teal">deploy</span>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 6. Coding Platform Analysis                                      */
/* ---------------------------------------------------------------- */
export function CodingSection({ c }: { c: CodingAnalysis | null }) {
  if (!c || c.platforms.length === 0) {
    return (
      <section>
        <SectionHeader index="6" title="Coding Platform Analysis" />
        <Card><p className="text-sm text-muted">No coding platform profiles were connected (LeetCode, Codeforces, CodeChef, GeeksforGeeks, HackerRank).</p></Card>
      </section>
    );
  }
  const statText = (s: Record<string, unknown>): string => {
    const parts: string[] = [];
    if (s.total_solved) parts.push(`${s.total_solved} solved`);
    if (s.rating) parts.push(`rating ${s.rating}`);
    if (s.stars && !s.rating) parts.push(`${s.stars}★`);
    if (s.coding_score) parts.push(`score ${s.coding_score}`);
    if (s.problems_solved) parts.push(`${s.problems_solved} solved`);
    if (s.medals) parts.push(`${JSON.stringify(s.medals)} medals`.replace(/[{}"]/g, ""));
    if (s.reputation) parts.push(`rep ${s.reputation}`);
    return parts.join(" · ") || "active";
  };
  return (
    <section>
      <SectionHeader index="6" title="Coding Platform Analysis" subtitle="Aggregated competitive programming and DSA evidence." />
      <div className="grid gap-3 lg:grid-cols-[260px_1fr]">
        <Card className="flex flex-col items-center justify-center">
          <ScoreRingOverlay value={c.problem_solving_score} label="Problem Solving" />
          <p className="mt-2 text-center text-xs leading-relaxed text-muted">{c.explanation}</p>
        </Card>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {c.platforms.map((p) =>
            p.platform === "leetcode" ? (
              <LeetCodeCard key={p.platform} p={p} />
            ) : p.platform === "hackerrank" ? (
              <HackerRankCard key={p.platform} p={p} />
            ) : (
              <Card key={p.platform} className="flex flex-col">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-ink">{p.platform_label}</span>
                  <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline">
                    @{p.handle}
                  </a>
                </div>
                <div className="mt-1.5 text-sm text-muted">{statText(p.stats)}</div>
              </Card>
            )
          )}
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 6a. LeetCode Detailed Card                                       */
/* ---------------------------------------------------------------- */
function LeetCodeCard({ p }: { p: CodingPlatformProfile }) {
  const s = p.stats as Record<string, unknown>;
  const skills = s.skills as
    | { fundamental?: { total: number; topics: Array<{ name: string; solved: number }> }; intermediate?: { total: number; topics: Array<{ name: string; solved: number }> }; advanced?: { total: number; topics: Array<{ name: string; solved: number }> } }
    | undefined;
  const recent = (s.recent_submissions as Array<{ title: string; status: string }>) || [];
  const contestHistory = (s.contest_history as Array<{ title: string; rating: number; ranking: number; total_participants: number; start_time: number }>) || [];

  return (
    <Card className="flex flex-col sm:col-span-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">{p.platform_label}</span>
        <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline">
          @{p.handle}
        </a>
      </div>

      {/* Top-level stats */}
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Solved" value={Number(s.total_solved) || 0} sub={`${Number(s.total_questions) || 0} total`} />
        <Stat label="Contest Rating" value={Number(s.contest_rating) || 0} accent="text-accent" />
        <Stat label="Streak" value={`${Number(s.streak_days) || 0}d`} sub={Number(s.total_active_days) ? `${s.total_active_days} active days` : undefined} />
        <Stat label="Acceptance" value={`${Number(s.acceptance_rate) || 0}%`} />
      </div>

      {/* Difficulty breakdown — circular ring */}
      {(Number(s.easy) || Number(s.medium) || Number(s.hard)) > 0 && (
        <div className="mt-3">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Difficulty Breakdown</div>
          <div className="flex items-center gap-6">
            {/* Ring chart */}
            <DifficultyRing easy={Number(s.easy) || 0} medium={Number(s.medium) || 0} hard={Number(s.hard) || 0} total={Number(s.total_questions) || 0} />
            {/* Legend */}
            <div className="flex flex-col gap-2">
              {[
                { label: "Easy", count: Number(s.easy) || 0, total: Number(s.total_easy) || 0, color: "#0ea371" },
                { label: "Med.", count: Number(s.medium) || 0, total: Number(s.total_medium) || 0, color: "#d97706" },
                { label: "Hard", count: Number(s.hard) || 0, total: Number(s.total_hard) || 0, color: "#e5484d" },
              ].map((d) => (
                <div key={d.label} className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ color: d.color }}>{d.count}</span>
                  <span className="text-xs text-muted">/ {d.total || "—"}</span>
                  <span className="text-xs font-medium text-ink-2">{d.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Contest section */}
      {(Number(s.contest_rating) > 0 || Number(s.attended_contests) > 0) && (
        <div className="mt-4">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Contest</div>
          <div className="rounded-xl border border-line bg-slate-soft/40 p-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              {/* Rating + level */}
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-[11px] font-medium text-muted">Contest Rating</div>
                  <div className="text-2xl font-bold text-ink">{Number(s.contest_rating) || 0}</div>
                </div>
                {typeof s.contest_level === "string" && s.contest_level && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-accent/30 bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent">
                    <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    {String(s.contest_level)}
                  </span>
                )}
              </div>
              {/* Ranking + attended */}
              <div className="flex gap-4">
                {Number(s.global_ranking) > 0 && (
                  <div className="text-right">
                    <div className="text-[11px] font-medium text-muted">Global Ranking</div>
                    <div className="text-sm font-bold text-ink">
                      {Number(s.global_ranking).toLocaleString()}
                      {Number(s.total_participants) > 0 && (
                        <span className="text-xs font-normal text-muted"> / {Number(s.total_participants).toLocaleString()}</span>
                      )}
                    </div>
                    {Number(s.top_percentage) > 0 && (
                      <div className="text-[10px] text-accent">Top {Number(s.top_percentage)}%</div>
                    )}
                  </div>
                )}
                {Number(s.attended_contests) > 0 && (
                  <div className="text-right">
                    <div className="text-[11px] font-medium text-muted">Attended</div>
                    <div className="text-sm font-bold text-ink">{Number(s.attended_contests)}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Rating history mini chart */}
            {contestHistory.length > 1 && (
              <div className="mt-3">
                <ContestRatingChart history={contestHistory} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Skill sections */}
      {skills?.fundamental?.total || skills?.intermediate?.total || skills?.advanced?.total ? (
        <div className="mt-3">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Skill Set</div>
          <div className="grid grid-cols-3 gap-2">
            {([
              { key: "fundamental" as const, label: "Fundamental" },
              { key: "intermediate" as const, label: "Intermediate" },
              { key: "advanced" as const, label: "Advanced" },
            ]).map(({ key, label }) => {
              const sec = skills[key];
              if (!sec || sec.total === 0) return null;
              return (
                <div key={key} className="rounded-lg border border-line bg-slate-soft/40 p-2">
                  <div className="text-[11px] font-semibold text-ink">{label}</div>
                  <div className="text-xs text-muted">{sec.total} solved</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {sec.topics.slice(0, 5).map((t) => (
                      <span key={t.name} className="inline-block rounded-full bg-surface px-2 py-0.5 text-[10px] text-ink-2">
                        {t.name} <span className="text-muted">({t.solved})</span>
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
        <div className="mt-3">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Recent Submissions</div>
          <div className="space-y-1">
            {recent.slice(0, 5).map((sub, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${sub.status === "Accepted" ? "bg-emerald" : sub.status === "Wrong Answer" ? "bg-rose" : "bg-slate"}`} />
                <span className="truncate text-ink-2">{sub.title}</span>
                <span className="shrink-0 text-muted">{sub.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

/* ---------------------------------------------------------------- */
/* Difficulty Ring — multi-segment donut chart                      */
/* ---------------------------------------------------------------- */
function DifficultyRing({ easy, medium, hard, total }: { easy: number; medium: number; hard: number; total: number }) {
  const size = 140;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  const solved = easy + medium + hard;
  const displayTotal = total || solved;

  const segments = [
    { count: easy, color: "#0ea371" },
    { count: medium, color: "#d97706" },
    { count: hard, color: "#e5484d" },
  ];

  let accumulated = 0;

  return (
    <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background track */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e6e8ef" strokeWidth={stroke} />
        {/* Colored segments */}
        {segments.map(({ count, color }) => {
          if (count <= 0) return null;
          const fraction = solved > 0 ? count / solved : 0;
          const segLen = fraction * C;
          const offset = C - accumulated;
          accumulated += segLen;
          return (
            <circle
              key={color}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${segLen} ${C - segLen}`}
              strokeDashoffset={offset}
              style={{ transition: "all 0.7s ease" }}
            />
          );
        })}
      </svg>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-xl font-bold text-ink">
          {solved}<span className="text-sm font-normal text-muted">/{displayTotal}</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-emerald">
          <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Solved
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */
/* Contest Rating History — SVG mini line chart                     */
/* ---------------------------------------------------------------- */
function ContestRatingChart({ history }: { history: Array<{ rating: number; start_time: number }> }) {
  if (history.length < 2) return null;

  const sorted = [...history].sort((a, b) => a.start_time - b.start_time);
  const ratings = sorted.map((h) => h.rating);
  const minR = Math.min(...ratings);
  const maxR = Math.max(...ratings);
  const range = maxR - minR || 1;
  const pad = 8;

  const w = 480;
  const h = 80;
  const chartW = w - pad * 2;
  const chartH = h - pad * 2;

  const points = sorted.map((entry, i) => {
    const x = pad + (i / (sorted.length - 1)) * chartW;
    const y = pad + chartH - ((entry.rating - minR) / range) * chartH;
    return `${x},${y}`;
  });

  const lastRating = ratings[ratings.length - 1];
  const firstYear = new Date(sorted[0].start_time * 1000).getFullYear();
  const lastYear = new Date(sorted[sorted.length - 1].start_time * 1000).getFullYear();

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => (
          <line
            key={frac}
            x1={pad}
            y1={pad + chartH * (1 - frac)}
            x2={w - pad}
            y2={pad + chartH * (1 - frac)}
            stroke="#e6e8ef"
            strokeWidth={0.5}
          />
        ))}
        {/* Line */}
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* End dot */}
        {points.length > 0 && (() => {
          const last = points[points.length - 1].split(",");
          return (
            <circle cx={last[0]} cy={last[1]} r={4} fill="#f59e0b" stroke="white" strokeWidth={2} />
          );
        })()}
      </svg>
      {/* Labels */}
      <div className="flex justify-between px-1 text-[10px] text-muted">
        <span>{firstYear}</span>
        <span className="font-semibold text-ink">{lastRating}</span>
        <span>{lastYear}</span>
      </div>
    </div>
  );
}

function ScoreRingOverlay({ value, label }: { value: number; label: string }) {
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={120} height={120} className="-rotate-90">
        <circle cx={60} cy={60} r={52} fill="none" stroke="#e6e8ef" strokeWidth={9} />
        <circle
          cx={60} cy={60} r={52} fill="none" stroke="#5b5bd6" strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={2 * Math.PI * 52}
          strokeDashoffset={2 * Math.PI * 52 * (1 - Math.min(1, Math.max(0, value)) / 100)}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-bold text-ink">{Math.round(value)}</div>
        <div className="text-[10px] font-medium uppercase tracking-wide text-muted">{label}</div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */
/* 6b. HackerRank Detailed Card                                     */
/* ---------------------------------------------------------------- */
interface HackerRankBadge {
  name: string;
  stars: number;
  level: number;
  icon: string;
  solved: number;
}

function HackerRankCard({ p }: { p: CodingPlatformProfile }) {
  const s = p.stats as Record<string, unknown>;
  const badges = (s.badges as HackerRankBadge[]) || [];
  const totalBadges = Number(s.total_badges) || badges.length;
  const stars = Number(s.stars) || 0;
  const level = Number(s.level) || 0;
  const problemsSolved = Number(s.problems_solved) || 0;
  const practiceScore = Number(s.practice_score) || 0;
  const ranking = Number(s.ranking) || 0;
  const contestCount = Number(s.contest_count) || 0;
  const contestRating = Number(s.contest_rating) || 0;

  return (
    <Card className="flex flex-col sm:col-span-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">{p.platform_label}</span>
        <a href={p.url} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline">
          @{p.handle}
        </a>
      </div>

      {/* Top-level stats */}
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Badges" value={totalBadges} sub={stars > 0 ? `${stars}★ profile` : undefined} />
        <Stat label="Problems Solved" value={problemsSolved} />
        <Stat label="Practice Score" value={practiceScore} accent="text-accent" />
        <Stat label="Best Rank" value={ranking || "—"} sub={contestCount > 0 ? `${contestCount} contest${contestCount === 1 ? "" : "s"}` : undefined} />
      </div>

      {/* Contest rating */}
      {contestRating > 0 && (
        <div className="mt-3">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Contest Rating</div>
          <div className="rounded-lg border border-line bg-slate-soft/40 p-2">
            <span className="text-sm font-semibold text-ink">{contestRating}</span>
          </div>
        </div>
      )}

      {/* Badges with star ratings */}
      {badges.length > 0 && (
        <div className="mt-3">
          <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
            Badges ({badges.length})
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {badges.map((badge, i) => (
              <div
                key={`${badge.name}-${i}`}
                className="rounded-lg border border-line bg-slate-soft/40 p-2.5"
              >
                <div className="flex items-center gap-2">
                  {badge.icon && (
                    <img
                      src={badge.icon}
                      alt={badge.name}
                      className="h-6 w-6 shrink-0 rounded-sm object-contain"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-semibold text-ink">{badge.name}</div>
                    <div className="mt-0.5 flex items-center gap-0.5">
                      {Array.from({ length: 3 }, (_, si) => (
                        <svg
                          key={si}
                          className={`h-3 w-3 ${si < badge.stars ? "text-amber" : "text-line"}`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                      <span className="ml-1 text-[10px] text-muted">{badge.stars}★</span>
                    </div>
                  </div>
                </div>
                {badge.solved > 0 && (
                  <div className="mt-1 text-[10px] text-muted">{badge.solved} solved</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active tracks */}
      {Array.isArray(s.active_tracks) && s.active_tracks.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Active Tracks</div>
          <div className="flex flex-wrap gap-1">
            {s.active_tracks.map((track: string) => (
              <Chip key={track}>{track}</Chip>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

/* ---------------------------------------------------------------- */
/* 7. Project Verification                                          */
/* ---------------------------------------------------------------- */
export function ProjectsSection({ pv }: { pv: ProjectVerification[] }) {
  return (
    <section>
      <SectionHeader index="7" title="Project Verification" subtitle="Every resume project matched against public repositories." />
      {pv.length === 0 ? (
        <Card><p className="text-sm text-muted">No projects to verify.</p></Card>
      ) : (
        <div className="grid gap-3 lg:grid-cols-3">
          {pv.map((p) => (
            <Card key={p.project_name} className="flex flex-col">
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-semibold text-ink">{p.project_name}</h4>
                <StatusBadge status={p.status} />
              </div>
              {p.description && <p className="mt-1 line-clamp-2 text-xs text-muted">{p.description}</p>}
              <div className="mt-3 flex items-center gap-2 text-sm">
                <span className="font-semibold text-ink-2">{Math.round(p.score)}/100</span>
                <ProgressBar value={p.score} tone={toneFor(p.score)} className="flex-1" />
              </div>
              <div className="mt-2 flex flex-wrap gap-1 text-[11px]">
                {p.repository_exists && <Chip className="text-emerald">Repo matched</Chip>}
                {p.deployment_exists && <Chip className="text-teal">Deployed</Chip>}
                {p.recent_activity && <Chip>Active</Chip>}
                {p.documentation_exists && <Chip>Documented</Chip>}
                {!p.repository_exists && <Chip className="text-slate">No public repo</Chip>}
              </div>
              {p.matched_repo && (
                <a href={`https://github.com/${p.matched_repo}`} target="_blank" rel="noreferrer" className="mt-2 text-xs text-accent hover:underline">
                  {p.matched_repo} ↗
                </a>
              )}
              <details className="mt-2">
                <summary className="cursor-pointer text-[11px] font-medium text-muted hover:text-ink">Evidence</summary>
                <ul className="mt-1 space-y-1 text-[11px] leading-relaxed text-muted">
                  {p.evidence.map((ev, i) => (
                    <li key={i}>• {ev}</li>
                  ))}
                </ul>
              </details>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 8. Achievement Verification                                      */
/* ---------------------------------------------------------------- */
export function AchievementsSection({ av }: { av: AchievementVerification[] }) {
  return (
    <section>
      <SectionHeader index="8" title="Achievement Verification" subtitle="Awards, certifications, hackathons and contributions checked against connected platforms." />
      {av.length === 0 ? (
        <Card><p className="text-sm text-muted">No achievements to verify.</p></Card>
      ) : (
        <Card padded={false} className="divide-y divide-line">
          {av.map((a, i) => (
            <div key={i} className="flex items-start gap-3 px-5 py-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-ink">{a.title}</span>
                  <Chip className="text-[10px] uppercase">{a.type}</Chip>
                </div>
                {a.evidence.length > 0 && (
                  <div className="mt-1 space-y-0.5">
                    {a.evidence.map((ev, j) => (
                      <p key={j} className="text-xs leading-relaxed text-muted">• {ev}</p>
                    ))}
                  </div>
                )}
              </div>
              <div className="shrink-0 text-right">
                <StatusBadge status={a.status}/>
              </div>
            </div>
          ))}
        </Card>
      )}
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 9 & 10. Strengths / Improvement Areas                            */
/* ---------------------------------------------------------------- */
export function StrengthsSection({ strengths }: { strengths: string[] }) {
  return (
    <section>
      <SectionHeader index="9" title="Strengths" subtitle="Top engineering strengths backed by public evidence." />
      <Card>
        <ul className="space-y-2">
          {strengths.length === 0 && <li className="text-sm text-muted">No strengths with strong evidence could be inferred.</li>}
          {strengths.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-ink-2">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-soft text-xs text-emerald">✓</span>
              {s}
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

export function ImprovementsSection({ improvements }: { improvements: string[] }) {
  return (
    <section>
      <SectionHeader index="10" title="Improvement Areas" subtitle="Claims with limited or no public evidence — opportunities, not accusations." />
      <Card>
        <ul className="space-y-2">
          {improvements.length === 0 && <li className="text-sm text-muted">No gaps identified.</li>}
          {improvements.map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-ink-2">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-soft text-xs text-amber">!</span>
              {s}
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 11. AI Summary                                                   */
/* ---------------------------------------------------------------- */
export function AISummarySection({ summary }: { summary: Record<string, string> }) {
  const order: Array<[string, string]> = [
    ["technical_strengths", "Technical strengths"],
    ["engineering_profile", "Engineering profile"],
    ["coding_ability", "Coding ability"],
    ["project_quality", "Project quality"],
    ["collaboration_indicators", "Collaboration indicators"],
    ["learning_consistency", "Learning consistency"],
    ["areas_to_improve", "Areas to improve"],
  ];
  return (
    <section>
      <SectionHeader index="11" title="AI Candidate Summary" subtitle="Recruiter-friendly assessment generated from evidence only." />
      <Card>
        <div className="space-y-4">
          {order.map(([key, label]) => (
            summary[key] && (
              <div key={key}>
                <h4 className="mb-1 text-sm font-semibold text-ink">{label}</h4>
                <p className="text-sm leading-relaxed text-ink-2">{summary[key]}</p>
              </div>
            )
          ))}
        </div>
      </Card>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* 12. Final Scores                                                 */
/* ---------------------------------------------------------------- */
export function ScoresSection({ scores, radarItems }: { scores: ScoreItem[]; radarItems: Array<[string, number]> }) {
  return (
    <section>
      <SectionHeader index="12" title="Final Scores" subtitle="Every score is explainable and evidence-backed — 0–100 scale." />
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <Card className="flex flex-col items-center justify-center">
          <div className="mb-2 text-center text-sm font-semibold text-ink">Score radar</div>
          <RadarChart items={radarItems} size={290} labelSize={8.5} />
        </Card>
        <div className="space-y-2">
          {scores.map((s) => (
            <Card key={s.key} padded={false} className="px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="w-44 shrink-0">
                  <div className="text-sm font-medium text-ink">{s.label}</div>
                  <div className="text-lg font-bold text-ink-2">{Math.round(s.value)}</div>
                </div>
                <div className="min-w-0 flex-1">
                  <ProgressBar value={s.value} tone={toneFor(s.value)} />
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">{s.explanation}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}