"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { PlatformIcon } from "@/components/platform-icon";
import { platformById } from "@/lib/platforms";
import type { ParsedResume, ResumeBatchCandidate, ResumeBatchResult } from "@/lib/types";
import { Button, Card, Chip, ScoreRing, Spinner, cn } from "@/components/ui";

type Phase = "upload" | "parsed" | "results";
type Busy = "parse" | "connect" | "validate" | null;

function flattenSkills(resume: ParsedResume): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const list of Object.values(resume.skills)) {
    for (const s of list) {
      if (s && !seen.has(s.toLowerCase())) {
        seen.add(s.toLowerCase());
        out.push(s);
      }
    }
  }
  return out;
}

export default function HrPage() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [candidates, setCandidates] = useState<ResumeBatchCandidate[]>([]);
  const [results, setResults] = useState<ResumeBatchResult | null>(null);
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectMsg, setConnectMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    setPendingFiles((prev) => [...prev, ...Array.from(files)]);
    setError(null);
  }, []);

  const removePending = (i: number) =>
    setPendingFiles((prev) => prev.filter((_, idx) => idx !== i));

  const parse = async () => {
    if (pendingFiles.length === 0) return;
    setBusy("parse");
    setError(null);
    try {
      const res = await api.uploadResumeBatch(pendingFiles);
      if (res.failed > 0 && res.processed === 0) {
        setError(res.errors.map((e) => `${e.filename}: ${e.detail}`).join(" · "));
        return;
      }
      setCandidates(res.candidates);
      setPhase("parsed");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(null);
    }
  };

  const connectAll = async () => {
    if (candidates.length === 0) return;
    setBusy("connect");
    setError(null);
    setConnectMsg(null);
    try {
      const res = await api.connectBatchProfiles(
        candidates.map((c) => ({ index: c.index, filename: c.filename, resume: c.resume })),
      );
      const byIndex = new Map(res.candidates.map((c) => [c.index, c]));
      setCandidates((prev) =>
        prev.map((c) => {
          const updated = byIndex.get(c.index);
          return updated ? { ...c, profiles: updated.profiles, detected: updated.detected } : c;
        }),
      );
      const total = res.candidates.reduce((n, c) => n + (c.profiles?.length ?? 0), 0);
      setConnectMsg(
        total > 0
          ? `Connected ${total} profile(s) across ${res.candidates.filter((c) => (c.profiles?.length ?? 0) > 0).length} resume(s).`
          : "No social/developer profiles were detected in these resumes.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not connect profiles");
    } finally {
      setBusy(null);
    }
  };

  const validate = async () => {
    if (candidates.length === 0) return;
    setBusy("validate");
    setError(null);
    try {
      const res = await api.analyzeBatch(
        candidates.map((c) => ({
          index: c.index,
          filename: c.filename,
          resume: c.resume,
          profiles: c.profiles ?? [],
        })),
      );
      setResults(res);
      setPhase("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setBusy(null);
    }
  };

  const reset = () => {
    setPhase("upload");
    setPendingFiles([]);
    setCandidates([]);
    setResults(null);
    setConnectMsg(null);
    setError(null);
  };

  const connectedCount = candidates.reduce((n, c) => n + (c.profiles?.length ?? 0), 0);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-ink">
          <Logo /> 100x Resume
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/analyze" className="text-muted hover:text-ink">Single candidate</Link>
          <Link href="/hr" className="font-medium text-accent hover:underline">HR ranking</Link>
        </nav>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-ink">HR · Candidate Ranking</h1>
        <p className="mt-1 text-sm text-muted">
          Upload multiple resumes, connect every detected social/developer profile, then run validation
          to rank all candidates by their evidence-backed score.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-rose/30 bg-rose-soft px-4 py-3 text-sm text-rose">
          {error}
        </div>
      )}

      {phase === "upload" && (
        <UploadStep
          files={pendingFiles}
          busy={busy === "parse"}
          onAdd={addFiles}
          onRemove={removePending}
          onParse={parse}
          inputRef={inputRef}
        />
      )}

      {phase === "parsed" && (
        <div className="space-y-4">
          <Card className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-muted">
              <span className="font-semibold text-ink">{candidates.length}</span> resume(s) parsed
              {connectedCount > 0 && (
                <span className="ml-2 text-xs text-emerald">· {connectedCount} profiles connected</span>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={reset}>Start over</Button>
              <Button
                variant="outline"
                size="sm"
                onClick={connectAll}
                disabled={busy === "connect" || busy === "validate"}
              >
                {busy === "connect" ? <><Spinner size={12} /> Connecting…</> : "Connect all social media for all resumes"}
              </Button>
              <Button
                size="sm"
                onClick={validate}
                disabled={busy === "connect" || busy === "validate"}
              >
                {busy === "validate" ? <><Spinner size={12} /> Validating…</> : "Run validation"}
              </Button>
            </div>
          </Card>

          {connectMsg && (
            <Card className="px-4 py-3 text-xs text-emerald">{connectMsg}</Card>
          )}

          <div className="grid gap-3 md:grid-cols-2">
            {candidates.map((c) => {
              const skills = flattenSkills(c.resume);
              return (
                <Card key={c.index}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-ink">
                        {c.resume.personal.name || "Unnamed candidate"}
                      </div>
                      <div className="truncate text-xs text-muted">{c.filename}</div>
                    </div>
                    <Chip className="shrink-0">{c.resume.personal.headline || "Candidate"}</Chip>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {skills.slice(0, 8).map((s) => (
                      <Chip key={s}>{s}</Chip>
                    ))}
                    {skills.length > 8 && <Chip>+{skills.length - 8}</Chip>}
                  </div>
                  {c.profiles && c.profiles.length > 0 && (
                    <div className="mt-2 flex flex-wrap items-center gap-1.5">
                      {c.profiles.map((p) => (
                        <span
                          key={p.platform}
                          className="inline-flex items-center gap-1 rounded-full bg-slate-soft px-2 py-0.5 text-[10px] font-medium text-ink-2"
                        >
                          <PlatformIcon id={p.platform} label={p.platform_label} size={12} />
                          {platformById(p.platform)?.label ?? p.platform} · {p.handle}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {phase === "results" && results && (
        <ResultsTable results={results} onReset={reset} />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */

function UploadStep({
  files,
  busy,
  onAdd,
  onRemove,
  onParse,
  inputRef,
}: {
  files: File[];
  busy: boolean;
  onAdd: (files: FileList | null) => void;
  onRemove: (i: number) => void;
  onParse: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}) {
  const [drag, setDrag] = useState(false);

  return (
    <Card className="p-6">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          onAdd(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "grid-backdrop cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors",
          drag ? "border-accent bg-accent-soft/60" : "border-line-strong hover:border-accent/60",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          multiple
          className="hidden"
          onChange={(e) => {
            onAdd(e.target.files);
            e.target.value = "";
          }}
        />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-accent-soft text-2xl">
          📄
        </div>
        <h3 className="mt-4 text-lg font-semibold text-ink">
          {busy ? "Extracting and parsing…" : "Drop multiple resumes here"}
        </h3>
        <p className="mt-1 text-sm text-muted">
          PDF or DOCX, up to 10 MB each. Select several to rank a whole applicant pool at once.
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">
            {files.length} file(s) selected
          </div>
          <div className="flex flex-wrap gap-2">
            {files.map((f, i) => (
              <span
                key={`${f.name}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink"
              >
                {f.name}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(i);
                  }}
                  className="rounded-full px-1 text-muted hover:bg-slate-soft hover:text-rose"
                  aria-label={`Remove ${f.name}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <Button className="mt-4" onClick={onParse} disabled={busy}>
            {busy ? <><Spinner size={12} /> Parsing…</> : `Parse ${files.length} resume(s)`}
          </Button>
        </div>
      )}
    </Card>
  );
}

function ResultsTable({ results, onReset }: { results: ResumeBatchResult; onReset: () => void }) {
  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-muted">
          <span className="font-semibold text-ink">{results.candidates.length}</span> candidate(s)
          ranked by overall score
          {results.failed > 0 && (
            <span className="ml-2 text-xs text-rose">· {results.failed} failed</span>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onReset}>Start over</Button>
      </Card>

      {results.errors.length > 0 && (
        <Card className="space-y-1 px-4 py-3 text-xs text-rose">
          {results.errors.map((e, i) => (
            <div key={i}>
              {e.filename}: {e.detail}
            </div>
          ))}
        </Card>
      )}

      <Card padded={false} className="overflow-hidden">
        <div className="hidden grid-cols-[56px_1fr_120px_1fr_110px] gap-3 border-b border-line px-4 py-3 text-xs font-semibold uppercase tracking-wider text-muted md:grid">
          <div>Rank</div>
          <div>Candidate</div>
          <div>Overall</div>
          <div>Key scores</div>
          <div className="text-right">Report</div>
        </div>
        {results.candidates.map((c) => {
          const tone = (c.overall_score ?? 0) >= 60 ? "emerald" : (c.overall_score ?? 0) >= 40 ? "amber" : "slate";
          const topScores = (c.scores ?? [])
            .filter((s) => s.key in SCORE_RANK_TONE)
            .slice(0, 4);
          return (
            <div
              key={c.report_id ?? c.index}
              className="grid grid-cols-1 gap-3 border-b border-line px-4 py-3 last:border-0 md:grid-cols-[56px_1fr_120px_1fr_110px] md:items-center"
            >
              <div className="flex items-center gap-2 md:block">
                <span className="text-xs text-muted md:hidden">Rank </span>
                <span className="text-lg font-bold text-ink">#{c.rank}</span>
              </div>

              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-ink">
                  {c.candidate_name || "Candidate"}
                </div>
                <div className="truncate text-xs text-muted">{c.filename}</div>
              </div>

              <div className="flex items-center gap-3">
                <ScoreRing value={c.overall_score ?? 0} size={56} stroke={6} tone={tone} />
              </div>

              <div className="flex flex-wrap gap-1.5">
                {topScores.map((s) => (
                  <Chip key={s.key}>{s.label.replace(/ Score$/, "")} {Math.round(s.value)}</Chip>
                ))}
              </div>

              <div className="text-right">
                {c.report_id ? (
                  <Link
                    href={`/report/${c.report_id}`}
                    className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent-strong"
                  >
                    View →
                  </Link>
                ) : (
                  <span className="text-xs text-muted">—</span>
                )}
              </div>
            </div>
          );
        })}
      </Card>
    </div>
  );
}

const SCORE_RANK_TONE = {
  resume_completeness: true,
  resume_credibility: true,
  technical_skills: true,
  project_quality: true,
};

function Logo() {
  return (
    <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-teal text-[10px] font-bold text-white">
      100
    </span>
  );
}
