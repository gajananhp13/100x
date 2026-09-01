"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { PlatformIcon } from "@/components/platform-icon";
import { platformById } from "@/lib/platforms";
import type { ParsedResume, ResumeBatchCandidate, ResumeBatchResult } from "@/lib/types";
import { Button, Chip, ScoreRing, Spinner } from "@/components/ui";
import { cn } from "@/lib/cn";
import {
  Upload, FileText, X, ArrowRight, RotateCcw, Users, Link2, Trophy,
  AlertCircle, Check, Send, Sparkles, Bot,
} from "lucide-react";

/* ─────────────────────────────────────────────────────────────────── */
/* Types                                                               */
/* ─────────────────────────────────────────────────────────────────── */
type Phase = "upload" | "parsed" | "results";
type Busy  = "parse" | "connect" | "validate" | null;
type ChatMessage = { role: "user" | "assistant"; text: string };

/* ─────────────────────────────────────────────────────────────────── */
/* Helpers                                                             */
/* ─────────────────────────────────────────────────────────────────── */
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

/* ─────────────────────────────────────────────────────────────────── */
/* AI chat filter                                                      */
/* ─────────────────────────────────────────────────────────────────── */
const SUGGESTIONS = [
  "Show me resumes trusted with JavaScript and TypeScript",
  "Who has GitHub connected?",
  "Filter candidates with React and Node.js",
  "Show top ranked with open source contributions",
  "Who has LeetCode connected?",
];

const FILTER_STOP = new Set([
  "me","show","filter","give","list","find","with","and","or","the","who","has","have",
  "a","an","for","of","in","on","at","to","trusted","resumes","candidates","resume",
  "candidate","top","ranked","using","candidates","some","all","only",
]);

function applyFilter(pool: ResumeBatchCandidate[], query: string): ResumeBatchCandidate[] {
  if (!query.trim()) return pool;
  const q = query.toLowerCase();

  const tokens = q
    .split(/[\s,+&]+/)
    .map(t => t.replace(/[^a-z0-9#.+]/g, ""))
    .filter(t => t.length >= 2 && !FILTER_STOP.has(t));

  return pool.filter(c => {
    const skills  = Object.values(c.resume.skills).flat().map(s => s.toLowerCase());
    const techs   = [
      ...c.resume.experience.flatMap(e => e.technologies.map(t => t.toLowerCase())),
      ...c.resume.projects.flatMap(p => p.tech_stack.map(t => t.toLowerCase())),
    ];
    const platforms = (c.profiles ?? []).map(p => p.platform.toLowerCase());
    const all = [...skills, ...techs, ...platforms];

    // "trusted / verified" → exclude suspicious resumes
    if ((q.includes("trusted") || q.includes("verified")) && c.integrity?.is_suspicious) return false;

    // explicit platform checks
    if (q.includes("github")   && !platforms.includes("github"))   return false;
    if (q.includes("leetcode") && !platforms.includes("leetcode")) return false;
    if (q.includes("open source")) {
      const hasOSS = c.resume.achievements.some(a => a.type === "open_source");
      if (!hasOSS && !platforms.includes("github")) return false;
    }

    // remaining tokens must all match at least one skill/tech
    const techTokens = tokens.filter(t => !["github","leetcode","open","source"].includes(t));
    return techTokens.length === 0 || techTokens.every(tok =>
      all.some(s => s.includes(tok) || tok.includes(s))
    );
  });
}

/* ─────────────────────────────────────────────────────────────────── */
/* RankingChat component                                               */
/* ─────────────────────────────────────────────────────────────────── */
function RankingChat({
  candidates,
  results,
  onFilter,
}: {
  candidates: ResumeBatchCandidate[];
  results: ResumeBatchResult | null;
  onFilter: (filtered: ResumeBatchCandidate[] | null) => void;
}) {
  const [input, setInput]       = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const textareaRef             = useRef<HTMLTextAreaElement>(null);

  const pool = results?.candidates.length ? results.candidates : candidates;
  const hasData = pool.length > 0;

  const submit = (query: string) => {
    const q = query.trim();
    if (!q) return;

    const filtered = applyFilter(pool, q);
    const isAll = filtered.length === pool.length;

    const reply = !hasData
      ? "Upload and validate resumes first, then I can filter them for you."
      : filtered.length === 0
      ? "No candidates matched that filter. Try different keywords."
      : isAll
      ? `Showing all ${pool.length} candidate(s) — query matched everyone or no filters applied.`
      : `Found ${filtered.length} of ${pool.length} candidate(s) matching "${q}".`;

    setMessages(prev => [
      ...prev,
      { role: "user",      text: q },
      { role: "assistant", text: reply },
    ]);
    onFilter(isAll || !hasData ? null : filtered);
    setInput("");
  };

  const clear = () => {
    setMessages([]);
    onFilter(null);
    setInput("");
  };

  return (
    <div className="mb-6 overflow-hidden rounded-xl border border-[#e4e4e7] bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-[#f0f0f2] px-4 py-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#eef2ff]">
          <Bot className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-sm font-semibold text-[#09090b]">Filter candidates with AI</span>
          <span className="ml-2 text-xs text-[#a1a1aa]">Ask in plain English</span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clear}
            className="shrink-0 text-xs font-medium text-[#a1a1aa] transition-colors hover:text-[#09090b]"
          >
            Clear filter
          </button>
        )}
      </div>

      {/* Message thread */}
      {messages.length > 0 && (
        <div className="max-h-44 overflow-y-auto px-4 py-3 space-y-2.5">
          {messages.map((m, i) => (
            <div key={i} className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}>
              {m.role === "assistant" && (
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#eef2ff]">
                  <Sparkles className="h-3 w-3 text-[#4f46e5]" />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[82%] rounded-xl px-3 py-2 text-sm leading-relaxed",
                  m.role === "user"
                    ? "bg-[#4f46e5] text-white"
                    : "bg-[#f4f4f5] text-[#52525b]",
                )}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suggestion chips — only when no conversation yet */}
      {messages.length === 0 && (
        <div className="flex flex-wrap gap-1.5 px-4 py-3">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="inline-flex items-center gap-1 rounded-full border border-[#e4e4e7] bg-[#f4f4f5] px-2.5 py-1 text-xs font-medium text-[#52525b] transition-all hover:border-[#4f46e5]/40 hover:bg-[#eef2ff] hover:text-[#4f46e5]"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2 border-t border-[#f0f0f2] px-3 py-2.5">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(input);
            }
          }}
          placeholder='e.g. "Show me resumes trusted with JavaScript and TypeScript"'
          className="flex-1 resize-none rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] px-3 py-2 text-sm text-[#09090b] placeholder:text-[#a1a1aa] transition-all focus:border-[#4f46e5] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#4f46e5]/20"
          style={{ minHeight: 36, maxHeight: 120 }}
        />
        <button
          onClick={() => submit(input)}
          disabled={!input.trim()}
          aria-label="Send"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#4f46e5] text-white transition-all hover:bg-[#4338ca] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Main page                                                           */
/* ─────────────────────────────────────────────────────────────────── */
export default function HrPage() {
  const [phase, setPhase]               = useState<Phase>("upload");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [candidates, setCandidates]     = useState<ResumeBatchCandidate[]>([]);
  const [results, setResults]           = useState<ResumeBatchResult | null>(null);
  const [busy, setBusy]                 = useState<Busy>(null);
  const [error, setError]               = useState<string | null>(null);
  const [connectMsg, setConnectMsg]     = useState<string | null>(null);
  const [filteredCandidates, setFilteredCandidates] = useState<ResumeBatchCandidate[] | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    setPendingFiles(prev => [...prev, ...Array.from(files)]);
    setError(null);
  }, []);

  const removePending = (i: number) =>
    setPendingFiles(prev => prev.filter((_, idx) => idx !== i));

  const parse = async () => {
    if (pendingFiles.length === 0) return;
    setBusy("parse");
    setError(null);
    try {
      const res = await api.uploadResumeBatch(pendingFiles);
      if (res.failed > 0 && res.processed === 0) {
        setError(res.errors.map(e => `${e.filename}: ${e.detail}`).join(" · "));
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
        candidates.map(c => ({ index: c.index, filename: c.filename, resume: c.resume })),
      );
      const byIndex = new Map(res.candidates.map(c => [c.index, c]));
      setCandidates(prev =>
        prev.map(c => {
          const updated = byIndex.get(c.index);
          return updated ? { ...c, profiles: updated.profiles, detected: updated.detected } : c;
        }),
      );
      const total = res.candidates.reduce((n, c) => n + (c.profiles?.length ?? 0), 0);
      setConnectMsg(
        total > 0
          ? `Connected ${total} profile(s) across ${res.candidates.filter(c => (c.profiles?.length ?? 0) > 0).length} resume(s).`
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
        candidates.map(c => ({
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
    setFilteredCandidates(null);
  };

  const connectedCount = candidates.reduce((n, c) => n + (c.profiles?.length ?? 0), 0);

  // What to show in results/parsed views (filtered or full)
  const displayCandidates = filteredCandidates ?? candidates;
  const displayResults    = filteredCandidates && results
    ? { ...results, candidates: filteredCandidates as typeof results.candidates }
    : results;

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6 py-6">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-[#09090b]">
          <LogoMark /> 100x Resume
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/analyze" className="text-[#71717a] transition-colors hover:text-[#09090b]">Single candidate</Link>
          <Link href="/hr" className="font-medium text-[#4f46e5]">HR ranking</Link>
        </nav>
      </header>

      {/* Page title */}
      <div className="mb-6">
        <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-[#4f46e5]">HR Mode</div>
        <h1 className="text-2xl font-bold tracking-tight text-[#09090b]">Candidate Ranking</h1>
        <p className="mt-1.5 max-w-xl text-sm text-[#71717a]">
          Upload multiple resumes, connect every detected profile, then run validation to rank all
          candidates by their evidence-backed score.
        </p>
      </div>

      {/* ── AI chat filter ── */}
      <RankingChat
        candidates={candidates}
        results={results}
        onFilter={setFilteredCandidates}
      />

      {/* Error */}
      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#dc2626]" role="alert">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Phases */}
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
          {/* Action bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e4e4e7] bg-white p-4">
            <div className="text-sm text-[#71717a]">
              <span className="font-semibold text-[#09090b]">
                {filteredCandidates ? `${filteredCandidates.length} of ` : ""}
                {candidates.length}
              </span>
              {" "}resume(s) parsed
              {connectedCount > 0 && (
                <span className="ml-2 text-xs font-medium text-[#16a34a]">· {connectedCount} profiles connected</span>
              )}
              {filteredCandidates && (
                <span className="ml-2 text-xs font-medium text-[#4f46e5]">· filtered</span>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" size="sm" onClick={reset}>
                <RotateCcw className="h-3.5 w-3.5" /> Start over
              </Button>
              <Button
                variant="secondary" size="sm"
                onClick={connectAll}
                disabled={busy === "connect" || busy === "validate"}
              >
                {busy === "connect"
                  ? <><Spinner size={12} /> Connecting…</>
                  : <><Link2 className="h-3.5 w-3.5" /> Connect profiles</>}
              </Button>
              <Button
                size="sm"
                onClick={validate}
                disabled={busy === "connect" || busy === "validate"}
              >
                {busy === "validate"
                  ? <><Spinner size={12} /> Validating…</>
                  : <><Trophy className="h-3.5 w-3.5" /> Run validation</>}
              </Button>
            </div>
          </div>

          {connectMsg && (
            <div className="flex items-center gap-2 rounded-xl border border-[#bbf7d0] bg-[#f0fdf4] px-4 py-3 text-sm">
              <Check className="h-4 w-4 text-[#16a34a] shrink-0" />
              <span className="text-[#71717a]">{connectMsg}</span>
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-2">
            {displayCandidates.map(c => {
              const skills = flattenSkills(c.resume);
              return (
                <div key={c.index} className="rounded-xl border border-[#e4e4e7] bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="truncate text-sm font-semibold text-[#09090b]">
                          {c.resume.personal.name || "Unnamed candidate"}
                        </div>
                        {c.integrity?.is_suspicious && (
                          <Chip tone="error">⚠ manipulation</Chip>
                        )}
                      </div>
                      <div className="truncate text-xs text-[#a1a1aa]">{c.filename}</div>
                    </div>
                    {c.resume.personal.headline && (
                      <Chip className="shrink-0">{c.resume.personal.headline}</Chip>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {skills.slice(0, 8).map(s => <Chip key={s}>{s}</Chip>)}
                    {skills.length > 8 && <Chip tone="brand">+{skills.length - 8}</Chip>}
                  </div>
                  {c.profiles && c.profiles.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {c.profiles.map(p => (
                        <span
                          key={p.platform}
                          className="inline-flex items-center gap-1 rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] px-2 py-1 text-[11px] font-medium text-[#52525b]"
                        >
                          <PlatformIcon id={p.platform} label={p.platform_label} size={11} />
                          {platformById(p.platform)?.label ?? p.platform} · {p.handle}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {phase === "results" && displayResults && (
        <ResultsTable
          results={displayResults}
          totalCount={results?.candidates.length ?? 0}
          isFiltered={!!filteredCandidates}
          onReset={reset}
        />
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Upload Step                                                         */
/* ─────────────────────────────────────────────────────────────────── */
function UploadStep({
  files, busy, onAdd, onRemove, onParse, inputRef,
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
    <div className="space-y-4">
      <div
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); onAdd(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "cursor-pointer rounded-xl border-2 border-dashed p-14 text-center transition-all",
          drag ? "border-[#4f46e5] bg-[#eef2ff]" : "border-[#e4e4e7] bg-white hover:border-[#4f46e5]/50",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          multiple
          className="hidden"
          onChange={e => { onAdd(e.target.files); e.target.value = ""; }}
        />
        <div className={cn("mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl transition-colors",
          drag ? "bg-[#4f46e5] text-white" : "bg-[#f4f4f5] text-[#71717a]")}>
          <Upload className="h-7 w-7" />
        </div>
        <h3 className="text-base font-semibold text-[#09090b]">
          {busy ? "Extracting and parsing…" : "Drop multiple resumes here"}
        </h3>
        <p className="mt-1.5 text-sm text-[#71717a]">
          PDF or DOCX · up to 10 MB each · select several to rank an entire applicant pool
        </p>
      </div>

      {files.length > 0 && (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-4">
          <div className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-[#a1a1aa]">
            {files.length} file(s) selected
          </div>
          <div className="flex flex-wrap gap-2">
            {files.map((f, i) => (
              <span key={`${f.name}-${i}`} className="inline-flex items-center gap-1.5 rounded-lg border border-[#e4e4e7] bg-[#f4f4f5] px-3 py-1.5 text-sm text-[#09090b]">
                <FileText className="h-3.5 w-3.5 text-[#a1a1aa]" />
                {f.name}
                <button
                  onClick={e => { e.stopPropagation(); onRemove(i); }}
                  className="ml-0.5 rounded p-0.5 text-[#a1a1aa] transition-colors hover:text-[#dc2626]"
                  aria-label={`Remove ${f.name}`}
                >
                  <X className="h-3 w-3" strokeWidth={2.5} />
                </button>
              </span>
            ))}
          </div>
          <Button className="mt-4" onClick={onParse} disabled={busy}>
            {busy
              ? <><Spinner size={14} /> Parsing…</>
              : <><Users className="h-4 w-4" /> Parse {files.length} resume(s)</>}
          </Button>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Results Table                                                       */
/* ─────────────────────────────────────────────────────────────────── */
function ResultsTable({
  results, totalCount, isFiltered, onReset,
}: {
  results: ResumeBatchResult;
  totalCount: number;
  isFiltered: boolean;
  onReset: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e4e4e7] bg-white p-4">
        <div className="text-sm text-[#71717a]">
          <span className="font-semibold text-[#09090b]">
            {isFiltered ? `${results.candidates.length} of ${totalCount}` : results.candidates.length}
          </span>
          {" "}candidate(s) ranked by overall score
          {isFiltered && <span className="ml-2 text-xs font-medium text-[#4f46e5]">· filtered</span>}
          {results.failed > 0 && (
            <span className="ml-2 text-xs text-[#dc2626]">· {results.failed} failed</span>
          )}
        </div>
        <Button variant="secondary" size="sm" onClick={onReset}>
          <RotateCcw className="h-3.5 w-3.5" /> Start over
        </Button>
      </div>

      {results.errors.length > 0 && (
        <div className="space-y-1 rounded-xl border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#dc2626]">
          {results.errors.map((e, i) => (
            <div key={i} className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span><span className="font-medium">{e.filename}:</span> {e.detail}</span>
            </div>
          ))}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-[#e4e4e7] bg-white">
        {/* Header */}
        <div className="hidden grid-cols-[56px_1fr_100px_1fr_110px] gap-4 border-b border-[#f0f0f2] bg-[#f4f4f5] px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[#a1a1aa] md:grid">
          <div>Rank</div>
          <div>Candidate</div>
          <div>Score</div>
          <div>Key metrics</div>
          <div className="text-right">Report</div>
        </div>

        {results.candidates.map((c, rowIdx) => {
          const topScores = (c.scores ?? [])
            .filter(s => SCORE_RANK_KEYS.includes(s.key))
            .slice(0, 4);
          return (
            <div
              key={c.report_id ?? c.index}
              className={cn(
                "grid grid-cols-1 gap-3 px-5 py-4 transition-colors hover:bg-[#fafafa] md:grid-cols-[56px_1fr_100px_1fr_110px] md:items-center",
                rowIdx < results.candidates.length - 1 && "border-b border-[#f0f0f2]",
              )}
            >
              <div>
                <span className={cn(
                  "inline-flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold",
                  rowIdx === 0 && "bg-[#fbbf24] text-white",
                  rowIdx === 1 && "bg-[#a1a1aa] text-white",
                  rowIdx === 2 && "bg-[#92400e] text-white",
                  rowIdx > 2  && "bg-[#f4f4f5] text-[#52525b]",
                )}>
                  #{c.rank}
                </span>
              </div>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-[#09090b]">
                    {c.candidate_name || "Candidate"}
                  </span>
                  {c.integrity?.is_suspicious && (
                    <Chip tone="error" className="text-[9px]">⚠ manipulation</Chip>
                  )}
                </div>
                <div className="truncate text-xs text-[#a1a1aa]">{c.filename}</div>
              </div>

              <div>
                <ScoreRing value={c.overall_score ?? 0} size={52} stroke={5} />
              </div>

              <div className="flex flex-wrap gap-1.5">
                {topScores.map(s => (
                  <Chip key={s.key} className="text-[11px]">
                    {s.label.replace(/ Score$/, "")} {Math.round(s.value)}
                  </Chip>
                ))}
              </div>

              <div className="text-right">
                {c.report_id ? (
                  <Link
                    href={`/report/${c.report_id}`}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#4f46e5] px-3.5 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-[#4338ca]"
                  >
                    View report <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                ) : (
                  <span className="text-xs text-[#a1a1aa]">—</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const SCORE_RANK_KEYS = ["resume_completeness", "resume_credibility", "technical_skills", "project_quality"];

function LogoMark() {
  return (
    <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#4f46e5] text-[11px] font-bold text-white">
      100
    </span>
  );
}
