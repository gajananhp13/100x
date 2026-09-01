import Link from "next/link";
import { RadarChart } from "@/components/charts";
import { PlatformIcon } from "@/components/platform-icon";
import { PLATFORM_DEFS, PLATFORM_CATEGORIES } from "@/lib/platforms";
import { Check, ArrowRight, GitBranch, Globe, FileText, Users, Shield, BarChart2, Zap, User, ChevronRight } from "lucide-react";

const STEPS = [
  { n: "01", title: "Upload resume", desc: "Drop a PDF or DOCX. All sections auto-extract: personal details, education, experience, categorised skills, projects, and achievements.", icon: FileText },
  { n: "02", title: "Connect profiles", desc: "Link GitHub and up to 16 other public developer accounts — or load a one-click demo candidate.", icon: User },
  { n: "03", title: "AI parses the resume", desc: "An LLM turns messy resume text into structured, typed fields you can review and correct before verifying.", icon: Zap },
  { n: "04", title: "Collect public evidence", desc: "Real GitHub API data (repos, commits, CI/CD, documentation, languages) plus metrics from every connected platform.", icon: GitBranch },
  { n: "05", title: "Verify every claim", desc: "Projects, skills, technologies and achievements are matched against public evidence with confidence scores.", icon: Shield },
  { n: "06", title: "Generate the report", desc: "A recruiter-ready Candidate Report with radar scores, verification badges, and a professional AI summary. Export as PDF.", icon: BarChart2 },
];

const REPORT_SECTIONS = [
  "Candidate Overview", "Resume Summary", "Skills Breakdown", "Technical Verification",
  "GitHub Analysis", "Coding Platforms", "Project Verification", "Achievement Verification",
  "Strengths", "Improvement Areas", "AI Summary", "Final Scores",
];

const SCORES_PREVIEW: Array<[string, number]> = [
  ["Completeness", 92], ["Credibility", 78], ["Technical", 83], ["GitHub Eng", 74],
  ["Coding", 68], ["Projects", 71], ["Open Source", 66], ["Docs", 81], ["Learning", 77], ["Overall", 76],
];

const TRUST_METRICS = [
  { label: "Platforms supported", value: "17" },
  { label: "GitHub API", value: "Live" },
  { label: "Export formats", value: "PDF, JSON" },
  { label: "No signup required", value: "✓" },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#fafafa]">
      {/* ── Nav ── */}
      <header className="sticky top-0 z-40 border-b border-[#e4e4e7] bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2.5">
            <LogoMark />
            <span className="text-sm font-semibold tracking-tight text-[#09090b]">100x Resume</span>
          </div>
          <nav className="hidden items-center gap-7 text-sm text-[#71717a] md:flex">
            <a href="#how" className="transition-colors hover:text-[#09090b]">How it works</a>
            <a href="#platforms" className="transition-colors hover:text-[#09090b]">Platforms</a>
            <a href="#report" className="transition-colors hover:text-[#09090b]">The report</a>
            <Link href="/hr" className="transition-colors hover:text-[#09090b]">HR ranking</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/analyze?demo=1" className="hidden text-sm font-medium text-[#71717a] transition-colors hover:text-[#09090b] sm:block">
              View demo
            </Link>
            <Link
              href="/analyze"
              className="inline-flex h-9 items-center rounded-lg bg-[#4f46e5] px-4 text-sm font-medium text-white transition-colors hover:bg-[#4338ca]"
            >
              Start for free
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden border-b border-[#e4e4e7] bg-white">
        {/* subtle grid bg */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage: "linear-gradient(#09090b 1px, transparent 1px), linear-gradient(90deg, #09090b 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        {/* indigo glow top-right */}
        <div className="pointer-events-none absolute -right-48 -top-48 h-[700px] w-[700px] rounded-full bg-[#4f46e5]/6 blur-3xl" />

        <div className="relative mx-auto max-w-5xl px-6 pb-24 pt-20 text-center">
          <a
            href="#how"
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#e4e4e7] bg-[#f4f4f5] px-3.5 py-1 text-xs font-medium text-[#52525b] transition-colors hover:border-[#4f46e5]/30 hover:bg-[#eef2ff] hover:text-[#4f46e5]"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#4f46e5]" />
            AI Candidate Verification · Not an ATS
            <ChevronRight className="h-3 w-3" />
          </a>

          <h1 className="mx-auto max-w-3xl text-5xl font-bold tracking-[-0.03em] text-[#09090b] sm:text-6xl">
            Verify any developer{" "}
            <span className="bg-gradient-to-br from-[#4f46e5] to-[#7c3aed] bg-clip-text text-transparent">
              resume with evidence
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-[#71717a]">
            Upload a resume, connect developer profiles, and get a recruiter-ready Candidate Report
            that verifies projects, skills and achievements against what is actually public.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/analyze"
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-[#4f46e5] px-6 text-sm font-semibold text-white shadow-sm transition-all hover:bg-[#4338ca] hover:shadow-md"
            >
              Upload a resume
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/analyze?demo=1"
              className="inline-flex h-11 items-center gap-2 rounded-lg border border-[#e4e4e7] bg-white px-6 text-sm font-semibold text-[#09090b] transition-all hover:border-[#4f46e5]/50 hover:shadow-sm"
            >
              Run instant demo
            </Link>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
            {TRUST_METRICS.map((m) => (
              <div key={m.label} className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-[#09090b]">{m.value}</span>
                <span className="text-[#a1a1aa]">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how" className="mx-auto w-full max-w-7xl px-6 py-24">
        <div className="mb-14 text-center">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-[#4f46e5]">How it works</p>
          <h2 className="text-3xl font-bold tracking-tight text-[#09090b] sm:text-4xl">
            From resume to evidence-backed report
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-base text-[#71717a]">
            Six deterministic steps — no black-box scoring, every number explained.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((s, idx) => {
            const Icon = s.icon;
            return (
              <div
                key={s.n}
                className="group relative rounded-xl border border-[#e4e4e7] bg-white p-6 transition-all duration-200 hover:border-[#4f46e5]/40 hover:shadow-md"
              >
                {/* connector line (desktop) */}
                {idx < STEPS.length - 1 && (
                  <span className="absolute -right-2.5 top-8 hidden h-px w-5 bg-[#e4e4e7] lg:block" />
                )}
                <div className="mb-4 flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#eef2ff] text-[#4f46e5] transition-colors group-hover:bg-[#4f46e5] group-hover:text-white">
                    <Icon className="h-4.5 w-4.5" strokeWidth={2} />
                  </span>
                  <span className="font-mono text-xs font-bold tracking-wider text-[#a1a1aa]">{s.n}</span>
                </div>
                <h3 className="text-sm font-semibold text-[#09090b]">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-[#71717a]">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Platforms ── */}
      <section id="platforms" className="border-y border-[#e4e4e7] bg-[#f4f4f5]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="mb-14 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-[#4f46e5]">Integrations</p>
            <h2 className="text-3xl font-bold tracking-tight text-[#09090b] sm:text-4xl">
              Connect every public profile
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-base text-[#71717a]">
              GitHub is fetched live via the public API. Every other platform has a demo-data engine
              today and a modular integration point for a real API later.
            </p>
          </div>
          <div className="space-y-10">
            {PLATFORM_CATEGORIES.map(({ name, ids }) => (
              <div key={name}>
                <h3 className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-[#a1a1aa]">
                  {name}
                </h3>
                <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">
                  {ids.map((id) => {
                    const p = PLATFORM_DEFS.find((d) => d.id === id);
                    if (!p) return null;
                    return (
                      <div
                        key={p.id}
                        className="flex items-center gap-2.5 rounded-lg border border-[#e4e4e7] bg-white px-3 py-2.5 transition-all hover:border-[#4f46e5]/40 hover:shadow-sm"
                      >
                        <PlatformIcon id={p.id} label={p.label} size={26} />
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium text-[#09090b]">{p.label}</div>
                          <div className="text-[10px] font-medium text-[#a1a1aa]">
                            {p.real_api ? (
                              <span className="text-[#16a34a]">Live API</span>
                            ) : "Demo engine"}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── The Report ── */}
      <section id="report" className="mx-auto w-full max-w-7xl px-6 py-24">
        <div className="grid items-center gap-16 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-[#4f46e5]">The report</p>
            <h2 className="text-3xl font-bold tracking-tight text-[#09090b] sm:text-4xl">
              A premium, recruiter-ready{" "}
              <span className="bg-gradient-to-br from-[#4f46e5] to-[#7c3aed] bg-clip-text text-transparent">
                Candidate Report
              </span>
            </h2>
            <p className="mt-4 text-base leading-relaxed text-[#71717a]">
              Twelve sections with visualisations — radar charts, progress bars, verification badges and
              confidence scores — every number backed by an explanation and public evidence.
            </p>

            <div className="mt-7 flex flex-wrap gap-1.5">
              {REPORT_SECTIONS.map((s) => (
                <span
                  key={s}
                  className="inline-flex items-center gap-1 rounded-md border border-[#e4e4e7] bg-[#f4f4f5] px-2.5 py-1 text-xs font-medium text-[#52525b]"
                >
                  <Check className="h-3 w-3 text-[#4f46e5]" strokeWidth={3} />
                  {s}
                </span>
              ))}
            </div>

            <div className="mt-8 rounded-xl border border-[#e4e4e7] bg-[#f4f4f5] p-4 text-sm">
              <p className="font-semibold text-[#09090b]">Always human-first</p>
              <p className="mt-1 leading-relaxed text-[#71717a]">
                Every claim returns one of{" "}
                <span className="font-semibold text-[#16a34a]">Verified</span>,{" "}
                <span className="font-semibold text-[#4f46e5]">Strong Evidence</span>,{" "}
                <span className="font-semibold text-[#d97706]">Partial Evidence</span>,{" "}
                <span className="font-semibold text-[#d97706]">Limited Evidence</span> or{" "}
                <span className="font-semibold text-[#a1a1aa]">No Public Evidence Found</span>.
                The platform never labels a candidate dishonest.
              </p>
            </div>
          </div>

          <div className="flex justify-center lg:justify-end">
            <div className="w-full max-w-sm rounded-2xl border border-[#e4e4e7] bg-white p-6 shadow-sm">
              <div className="mb-1 text-center text-xs font-semibold uppercase tracking-widest text-[#a1a1aa]">
                Score Radar Preview
              </div>
              <RadarChart items={SCORES_PREVIEW} size={300} labelSize={9} />
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="border-t border-[#e4e4e7] bg-[#4f46e5]">
        <div className="mx-auto flex max-w-4xl flex-col items-center px-6 py-16 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Ready to verify your first candidate?
          </h2>
          <p className="mt-3 text-base text-indigo-200">
            Upload a resume and get a full report in under 2 minutes. No account needed.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/analyze"
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-white px-6 text-sm font-semibold text-[#4f46e5] transition-all hover:bg-[#eef2ff] hover:shadow-md"
            >
              Get started free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/hr"
              className="inline-flex h-11 items-center gap-2 rounded-lg border border-white/30 px-6 text-sm font-semibold text-white transition-all hover:bg-white/10"
            >
              <Users className="h-4 w-4" /> HR ranking mode
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[#e4e4e7] bg-white">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-[#71717a] sm:flex-row">
          <div className="flex items-center gap-2.5">
            <LogoMark small />
            <span className="font-semibold text-[#09090b]">100x Resume</span>
          </div>
          <p className="text-center text-xs text-[#a1a1aa]">
            Evidence-based candidate verification · Built for recruiters and engineering teams
          </p>
          <div className="flex items-center gap-5 text-xs">
            <Link href="/analyze" className="transition-colors hover:text-[#09090b]">Analyze</Link>
            <Link href="/hr" className="transition-colors hover:text-[#09090b]">HR Ranking</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function LogoMark({ small = false }: { small?: boolean }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-lg bg-[#4f46e5] font-bold text-white ${
        small ? "h-6 w-6 text-[10px]" : "h-8 w-8 text-xs"
      }`}
    >
      100
    </span>
  );
}
