"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CandidateReport } from "@/lib/types";
import { Button, ScoreRing, Spinner } from "@/components/ui";
import { Printer, Download, ArrowLeft, FileX, ExternalLink } from "lucide-react";
import {
  AISummarySection, AchievementsSection, CodingSection, GitHubSection,
  ImprovementsSection, OverviewSection, ProjectsSection, ResumeSummarySection,
  ScoresSection, SkillsSection, StrengthsSection, TechnicalSection,
} from "./sections";

export default function ReportView({ reportId }: { reportId: string }) {
  const [report, setReport] = useState<CandidateReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getReport(reportId)
      .then((r) => !cancelled && setReport(r))
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : "Failed to load the report"));
    return () => { cancelled = true; };
  }, [reportId]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#fafafa] px-6">
        <div className="w-full max-w-md rounded-2xl border border-[#e4e4e7] bg-white p-10 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[#fef2f2]">
            <FileX className="h-6 w-6 text-[#dc2626]" />
          </div>
          <h2 className="mt-4 text-lg font-semibold text-[#09090b]">Report not found</h2>
          <p className="mt-2 text-sm text-[#71717a]">{error}</p>
          <Link
            href="/analyze"
            className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-[#4f46e5] transition-colors hover:text-[#4338ca]"
          >
            <ArrowLeft className="h-4 w-4" /> Run a new verification
          </Link>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#fafafa]">
        <div className="text-center">
          <Spinner size={28} />
          <p className="mt-3 text-sm text-[#71717a]">Loading report…</p>
        </div>
      </div>
    );
  }

  const a = report.analysis;
  const name = a.resume.personal.name || "Candidate";
  const radarItems: Array<[string, number]> = a.scores.map((s) => [
    s.label.replace(/ Score$/, ""),
    s.value,
  ]);

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* ── Sticky header ── */}
      <header className="no-print sticky top-0 z-40 border-b border-[#e4e4e7] bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-[#09090b]">
              <LogoMark /> 100x Resume
            </Link>
            <span className="hidden h-4 w-px bg-[#e4e4e7] sm:block" />
            <span className="hidden text-xs text-[#a1a1aa] sm:block">
              Candidate Report · {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/hr"
              className="hidden h-8 items-center rounded-lg border border-[#e4e4e7] px-3 text-sm font-medium text-[#52525b] transition-colors hover:border-[#d4d4d8] hover:text-[#09090b] sm:inline-flex"
            >
              HR ranking
            </Link>
            <Button variant="secondary" size="sm" onClick={() => window.print()}>
              <Printer className="h-3.5 w-3.5" /> Print
            </Button>
            <Button size="sm" onClick={() => window.open(api.pdfUrl(report.report_id), "_blank")}>
              <Download className="h-3.5 w-3.5" /> Export PDF
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl px-6 py-8">
        {/* ── Hero strip ── */}
        <div className="print-flat mb-8 overflow-hidden rounded-2xl border border-[#e4e4e7] bg-white shadow-sm">
          {/* Top accent bar */}
          <div className="h-1 w-full bg-gradient-to-r from-[#4f46e5] via-[#7c3aed] to-[#6366f1]" />
          <div className="flex flex-wrap items-center justify-between gap-6 p-6">
            <div>
              <div className="mb-1 text-[10px] font-bold uppercase tracking-widest text-[#4f46e5]">
                Candidate Report
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-[#09090b]">{name}</h1>
              <p className="mt-1 text-sm text-[#71717a]">
                {a.resume.personal.headline ||
                  a.resume.experience[0]?.position ||
                  "Software candidate"}
                <span className="mx-2 text-[#d4d4d8]">·</span>
                <span className="font-mono text-xs text-[#a1a1aa]">#{report.report_id.slice(0, 8)}</span>
              </p>

              {/* Profile chips */}
              {a.profiles.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {a.profiles.map((p) => (
                    <span
                      key={p.platform}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] px-2 py-0.5 text-[11px] font-medium text-[#52525b]"
                    >
                      {p.platform_label}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Score ring */}
            <div className="flex shrink-0 flex-col items-center">
              <ScoreRing value={a.overall_score} size={92} stroke={7} />
              <div className="mt-1.5 text-xs font-semibold text-[#a1a1aa]">Overall Score</div>
            </div>
          </div>
        </div>

        {/* ── Sections ── */}
        <div className="space-y-10 pb-20">
          <OverviewSection a={a} />
          <ResumeSummarySection a={a} />
          <SkillsSection a={a} />
          <TechnicalSection a={a} />
          <GitHubSection g={a.github ?? null} />
          <CodingSection c={a.coding ?? null} />
          <ProjectsSection pv={a.project_verifications} />
          <AchievementsSection av={a.achievement_verifications} />
          <StrengthsSection strengths={a.strengths} />
          <ImprovementsSection improvements={a.improvements} />
          <AISummarySection summary={a.ai_summary} />
          <ScoresSection scores={a.scores} radarItems={radarItems} />
        </div>
      </div>
    </div>
  );
}

function LogoMark() {
  return (
    <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#4f46e5] text-[11px] font-bold text-white">
      100
    </span>
  );
}
