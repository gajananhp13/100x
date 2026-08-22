"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CandidateReport } from "@/lib/types";
import { Button, Card, Spinner } from "@/components/ui";
import {
  AISummarySection,
  AchievementsSection,
  CodingSection,
  GitHubSection,
  ImprovementsSection,
  OverviewSection,
  ProjectsSection,
  ResumeSummarySection,
  ScoresSection,
  SkillsSection,
  StrengthsSection,
  TechnicalSection,
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
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center">
        <Card className="p-8">
          <div className="text-lg font-semibold text-rose">Report not found</div>
          <p className="mt-2 text-sm text-muted">{error}</p>
          <Link href="/analyze" className="mt-4 inline-block text-sm font-medium text-accent hover:underline">
            ← Run a new verification
          </Link>
        </Card>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="text-center">
          <Spinner size={26} className="text-accent" />
          <p className="mt-3 text-sm text-muted">Loading report…</p>
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
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      {/* header */}
      <div className="no-print sticky top-0 z-40 -mx-4 mb-6 border-b border-line bg-canvas/85 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-ink">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-teal text-[10px] font-bold text-white">
                100
              </span>
              100x Resume
            </Link>
            <span className="hidden text-xs text-muted sm:block">
              Candidate Report · {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>
           <div className="flex items-center gap-2">
            <Link
              href="/hr"
              className="rounded-lg border border-line-strong bg-surface px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:border-ink/30"
            >
              HR ranking
            </Link>
            <Button variant="outline" size="sm" onClick={() => window.print()}>
              Print
            </Button>
            <Button size="sm" onClick={() => window.open(api.pdfUrl(report.report_id), "_blank")}>
              Export PDF ↓
            </Button>
          </div>
        </div>
      </div>

      {/* hero summary strip */}
      <div className="print-flat mb-6 rounded-xl border border-line bg-surface p-5 shadow-[0_1px_2px_rgba(16,24,40,0.04)]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-accent">Candidate Report</div>
            <h1 className="mt-1 text-2xl font-bold text-ink">{name}</h1>
            <div className="mt-1 text-sm text-muted">
              {a.resume.personal.headline ||
                a.resume.experience[0]?.position ||
                "Software candidate"} · Report #{report.report_id}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-[11px] font-medium uppercase tracking-wide text-muted">Overall Score</div>
              <div className={`text-3xl font-bold ${a.overall_score >= 60 ? "text-emerald" : a.overall_score >= 40 ? "text-amber" : "text-rose"}`}>
                {Math.round(a.overall_score)}
              </div>
            </div>
            <div className="flex flex-wrap justify-end gap-1.5" style={{ maxWidth: 240 }}>
              {a.profiles.map((p) => (
                <span key={p.platform} className="rounded-full bg-slate-soft px-2 py-0.5 text-[10px] font-medium text-ink-2">
                  {p.platform_label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* sections */}
      <div className="space-y-8 pb-16">
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
  );
}