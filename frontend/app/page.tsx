import Link from "next/link";
import { RadarChart } from "@/components/charts";
import { PlatformIcon } from "@/components/platform-icon";
import { PLATFORM_DEFS } from "@/lib/platforms";

const STEPS = [
  {
    n: "01",
    title: "Upload resume",
    desc: "Drop a PDF or DOCX. All sections are auto-extracted: personal details, education, experience, categorized skills, projects, and achievements.",
  },
  {
    n: "02",
    title: "Connect profiles",
    desc: "Link GitHub and up to 16 other public developer and professional accounts — or load a one-click demo candidate.",
  },
  {
    n: "03",
    title: "AI parses the resume",
    desc: "An LLM turns messy resume text into structured, typed fields you can review and correct before verifying.",
  },
  {
    n: "04",
    title: "Collect public evidence",
    desc: "Real GitHub API data (repos, commits, CI/CD, documentation, languages) plus metrics from every connected platform.",
  },
  {
    n: "05",
    title: "Verify every claim",
    desc: "Projects, skills, technologies and achievements are matched against public evidence with confidence scores.",
  },
  {
    n: "06",
    title: "Generate the report",
    desc: "A recruiter-ready Candidate Report with radar scores, verification badges, and a professional AI summary. Export as PDF.",
  },
];

const REPORT_SECTIONS = [
  "Candidate Overview",
  "Resume Summary",
  "Skills Breakdown",
  "Technical Verification",
  "GitHub Analysis",
  "Coding Platform Analysis",
  "Project Verification",
  "Achievement Verification",
  "Strengths",
  "Improvement Areas",
  "AI Summary",
  "Final Scores",
];

const SCORES_PREVIEW: Array<[string, number]> = [
  ["Completeness", 92],
  ["Credibility", 78],
  ["Technical", 83],
  ["GitHub Eng", 74],
  ["Coding", 68],
  ["Projects", 71],
  ["Open Source", 66],
  ["Docs", 81],
  ["Learning", 77],
  ["Overall", 76],
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Logo />
            <span className="font-semibold tracking-tight">100x Resume</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-muted md:flex">
            <a href="#how" className="hover:text-ink">How it works</a>
            <a href="#platforms" className="hover:text-ink">Platforms</a>
            <a href="#report" className="hover:text-ink">The report</a>
          </nav>
          <Link
            href="/analyze"
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-strong"
          >
            Start verification
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="grid-backdrop relative border-b border-line">
        <div className="mx-auto max-w-6xl px-4 py-16 text-center sm:py-24">
          <span className="inline-flex items-center rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-muted">
            AI Candidate Verification · Not an ATS
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-ink sm:text-6xl">
            Verify any developer resume with{" "}
            <span className="bg-gradient-to-r from-accent to-teal bg-clip-text text-transparent">
              public evidence
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted">
            Upload a resume, connect developer profiles, and get a recruiter-ready Candidate Report that
            verifies projects, skills and achievements against what is actually public — never guessing,
            never accusing.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/analyze"
              className="rounded-lg bg-accent px-6 py-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-accent-strong"
            >
              Upload a resume
            </Link>
            <Link
              href="/analyze?demo=1"
              className="rounded-lg border border-line-strong bg-surface px-6 py-3 text-sm font-medium text-ink transition-colors hover:border-ink/30"
            >
              Run the instant demo →
            </Link>
          </div>
          <p className="mt-4 text-xs text-muted">
            17 supported platforms · Real GitHub API · PDF export · Works fully offline
          </p>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="mx-auto max-w-6xl px-4 py-16">
        <div className="mb-10 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-ink">How it works</h2>
          <p className="mt-2 text-muted">Six steps from resume to an evidence-backed verdict.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-xl border border-line bg-surface p-5">
              <div className="text-xs font-bold tracking-wider text-accent">{s.n}</div>
              <h3 className="mt-1.5 font-semibold text-ink">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Platforms */}
      <section id="platforms" className="border-y border-line bg-surface/60">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <div className="mb-10 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-ink">Connect every public profile</h2>
            <p className="mt-2 text-muted">
              GitHub is fetched live via the public API. Every other platform has a demo-data engine today
              and a modular integration point for a real API later.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {PLATFORM_DEFS.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-3 rounded-lg border border-line bg-surface px-3 py-2.5"
              >
                <PlatformIcon id={p.id} label={p.label} size={28} />
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-ink">{p.label}</div>
                  <div className="text-[11px] text-muted">{p.real_api ? "Live API" : "Demo engine"}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Report */}
      <section id="report" className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-ink">
              A premium, recruiter-ready Candidate Report
            </h2>
            <p className="mt-3 text-muted">
              Twelve sections with visualizations — radar charts, progress bars, verification badges and
              confidence scores — every number backed by an explanation and public evidence.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {REPORT_SECTIONS.map((s) => (
                <span
                  key={s}
                  className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink-2"
                >
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-6 rounded-lg border border-line bg-surface p-4 text-sm text-muted">
              <span className="font-semibold text-ink">Always human-first:&nbsp;</span>
              every claim returns one of{" "}
              <span className="text-emerald">Verified</span>,{" "}
              <span className="text-teal">Strong Evidence</span>,{" "}
              <span className="text-amber">Partial Evidence</span>,{" "}
              <span className="text-orange">Limited Evidence</span> or{" "}
              <span className="text-slate">No Public Evidence Found</span>. The platform never labels a
              candidate dishonest — it simply reports what is publicly verifiable.
            </div>
          </div>
          <div className="flex justify-center">
            <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm">
              <div className="mb-3 text-center text-sm font-semibold text-ink">Final scores · radar</div>
              <RadarChart items={SCORES_PREVIEW} size={320} labelSize={9} />
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-line py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm text-muted sm:flex-row">
          <div className="flex items-center gap-2">
            <Logo small />
            <span className="font-medium text-ink">100x Resume</span>
          </div>
          <p>Evidence-based candidate verification · Made for recruiters and engineering teams</p>
        </div>
      </footer>
    </div>
  );
}

function Logo({ small = false }: { small?: boolean }) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-lg bg-gradient-to-br from-accent to-teal font-bold text-white ${
        small ? "h-6 w-6 text-xs" : "h-7 w-7 text-sm"
      }`}
    >
      100
    </span>
  );
}