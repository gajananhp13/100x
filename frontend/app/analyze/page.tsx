"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, runAnalysis } from "@/lib/api";
import { PLATFORM_CATEGORIES, platformById } from "@/lib/platforms";
import type { ConnectedProfile, ParsedResume } from "@/lib/types";
import { Button, Card, Chip, Spinner, SectionHeader, StatCard, StatusIndicator, Input } from "@/components/ui";
import { cn } from "@/lib/cn";
import { PlatformIcon } from "@/components/platform-icon";
import { ChevronLeft, ChevronRight, Check, Plus, X, Search, Sparkles, FileText, AlertCircle } from "lucide-react";

type Step = 0 | 1 | 2;

const STAGES_META: Record<string, { label: string; desc: string }> = {
  init:         { label: "Starting pipeline",         desc: "Preparing the verification run" },
  github:       { label: "GitHub analysis",           desc: "Repositories, commits, CI/CD, documentation" },
  coding:       { label: "Coding platforms",          desc: "LeetCode, Codeforces, CodeChef, more" },
  skills:       { label: "Skill verification",        desc: "Matching technologies against public code" },
  projects:     { label: "Project verification",      desc: "Matching resume projects to repositories" },
  achievements: { label: "Achievement verification",  desc: "Hackathons, certifications, contributions" },
  scoring:      { label: "Computing scores",          desc: "10 evidence-backed 0–100 scores" },
  summary:      { label: "AI candidate summary",      desc: "Writing the recruiter summary" },
  done:         { label: "Report ready",              desc: "Compiling the final report" },
};

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(0);
  const [resume, setResume] = useState<ParsedResume | null>(null);
  const [profiles, setProfiles] = useState<ConnectedProfile[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stageLog, setStageLog] = useState<Array<{ stage: string; message: string; done: boolean }>>([]);
  const [running, setRunning] = useState(false);
  const [handles, setHandles] = useState<Record<string, string>>({});
  const [detected, setDetected] = useState<Record<string, string>>({});
  const [connecting, setConnecting] = useState<string | null>(null);
  const [connectMsg, setConnectMsg] = useState<Record<string, string>>({});
  const [autoConnecting, setAutoConnecting] = useState(false);
  const startedDemo = useRef(false);

  const connected = new Set(profiles.filter((p) => p.status === "collected").map((p) => p.platform));

  const loadDemo = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const demo = await api.loadDemo();
      setResume(demo.resume);
      setProfiles(demo.profiles);
      setFileName("demo-resume (simulated)");
      setStep(1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo load failed");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (window.location.search.includes("demo=1") && !startedDemo.current) {
      startedDemo.current = true;
      void loadDemo().then(() => runNow());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runNow = useCallback(async () => {
    if (!resume) return;
    setRunning(true);
    setError(null);
    setStageLog([{ stage: "init", message: STAGES_META.init.label, done: false }]);
    try {
      const reportId = await runAnalysis(resume, profiles, (event, data) => {
        if (event === "stage") {
          setStageLog((prev) => {
            const stage = String(data.stage ?? "done");
            const next = prev.map((s) => ({ ...s, done: true }));
            next.push({ stage, message: String(data.message ?? STAGES_META[stage]?.label ?? stage), done: false });
            return next;
          });
        }
      });
      router.push(`/report/${reportId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
      setRunning(false);
    }
  }, [resume, profiles, router]);

  const onFile = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const uploaded = await api.uploadResume(file);
      const parsed = await api.parseResume(uploaded.text);
      setResume(parsed);
      setFileName(uploaded.filename);
      setStep(1);
      try {
        const { handles: found } = await api.detectProfiles(parsed);
        setDetected(found);
        setHandles((h) => ({ ...h, ...found }));
      } catch { /* best-effort */ }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const connect = async (platform: string) => {
    const handle = (handles[platform] ?? detected[platform] ?? "").trim().replace(/^@/, "");
    if (!handle || !resume) return;
    setConnecting(platform);
    setError(null);
    try {
      const res = await api.connectProfile(platform, handle, resume);
      setConnectMsg((m) => ({ ...m, [platform]: res.message }));
      setProfiles((prev) => {
        const rest = prev.filter((p) => p.platform !== platform);
        return res.profile ? [...rest, res.profile] : rest;
      });
    } catch (e) {
      setConnectMsg((m) => ({ ...m, [platform]: e instanceof Error ? e.message : "Connection failed" }));
    } finally {
      setConnecting(null);
    }
  };

  const autoConnectAll = async () => {
    if (!resume) return;
    setAutoConnecting(true);
    setError(null);
    try {
      const res = await api.autoConnect(resume);
      setDetected(res.handles);
      setHandles((h) => ({ ...h, ...res.handles }));
      setProfiles((prev) => {
        const rest = prev.filter((p) => !res.profiles.some((np) => np.platform === p.platform));
        return [...rest, ...res.profiles];
      });
      if (res.profiles.length > 0) {
        setConnectMsg((m) => ({
          ...m,
          ...Object.fromEntries(res.profiles.map((p) => [p.platform, "Auto-connected from resume."])),
        }));
      } else {
        setConnectMsg((m) => ({ ...m, _auto: "No platform handles found — connect manually below." }));
      }
    } catch (e) {
      setConnectMsg((m) => ({ ...m, _auto: e instanceof Error ? e.message : "Auto-connect failed" }));
    } finally {
      setAutoConnecting(false);
    }
  };

  const removeSkill = (skill: string) => {
    if (!resume) return;
    const next: ParsedResume["skills"] = { ...resume.skills };
    for (const key of Object.keys(next) as Array<keyof ParsedResume["skills"]>) {
      next[key] = next[key].filter((s) => s !== skill);
    }
    setResume({ ...resume, skills: next });
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-4 py-6">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-[#09090b]">
          <LogoMark /> 100x Resume
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/hr" className="hidden text-sm text-[#71717a] transition-colors hover:text-[#09090b] sm:block">
            HR ranking
          </Link>
          <Button variant="ghost" size="sm" onClick={loadDemo} disabled={busy || running}>
            <Sparkles className="h-3.5 w-3.5" /> Demo
          </Button>
          <Link href="/" className="text-sm text-[#71717a] transition-colors hover:text-[#09090b]">Cancel</Link>
        </div>
      </header>

      <StepIndicator step={step} running={running} />

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-sm text-[#dc2626]" role="alert">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {step === 0 && <UploadStep busy={busy} onFile={onFile} />}

      {step === 1 && resume && (
        <ConnectStep
          resume={resume}
          connected={connected}
          detected={detected}
          handles={handles}
          setHandles={setHandles}
          connecting={connecting}
          connect={connect}
          connectMsg={connectMsg}
          autoConnecting={autoConnecting}
          autoConnectAll={autoConnectAll}
          removeSkill={removeSkill}
          onBack={() => setStep(0)}
          onNext={() => setStep(2)}
        />
      )}

      {step === 1 && !resume && (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-10 text-center text-sm text-[#71717a]">
          Upload a resume first, or load the demo candidate above.
        </div>
      )}

      {step === 2 && resume && (
        <AnalyzeStep
          resume={resume}
          profiles={profiles}
          running={running}
          stageLog={stageLog}
          onRun={runNow}
          onBack={() => setStep(1)}
        />
      )}

      {step === 2 && !resume && (
        <div className="rounded-xl border border-[#e4e4e7] bg-white p-10 text-center text-sm text-[#71717a]">
          Nothing to analyze — go back and upload a resume.
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Step Indicator                                                      */
/* ─────────────────────────────────────────────────────────────────── */
function StepIndicator({ step, running }: { step: Step; running: boolean }) {
  const steps = [
    { n: 1, label: "Upload resume" },
    { n: 2, label: "Connect profiles" },
    { n: 3, label: "Analyze & report" },
  ];
  return (
    <div className="mb-8 flex items-center justify-center">
      {steps.map((s, i) => {
        const active = i === step;
        const done = i < step;
        return (
          <div key={s.n} className="flex items-center">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold transition-all",
                  done  && "bg-[#16a34a] text-white",
                  active && "bg-[#4f46e5] text-white shadow-sm shadow-[#4f46e5]/30",
                  !done && !active && "border border-[#e4e4e7] bg-white text-[#a1a1aa]",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : s.n}
              </span>
              <span
                className={cn(
                  "hidden text-sm font-medium sm:block",
                  active ? "text-[#09090b]" : "text-[#a1a1aa]",
                )}
              >
                {s.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={cn("mx-3 h-px w-10", done ? "bg-[#4f46e5]" : "bg-[#e4e4e7]")} />
            )}
          </div>
        );
      })}
      {running && <Spinner size={15} className="ml-4" />}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Upload Step                                                         */
/* ─────────────────────────────────────────────────────────────────── */
function UploadStep({ busy, onFile }: { busy: boolean; onFile: (f: File) => void }) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files?.[0]; if (f) void onFile(f); }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "cursor-pointer rounded-xl border-2 border-dashed p-16 text-center transition-all duration-150",
          drag
            ? "border-[#4f46e5] bg-[#eef2ff]"
            : "border-[#e4e4e7] bg-white hover:border-[#4f46e5]/50 hover:bg-[#fafafa]",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) void onFile(f); e.target.value = ""; }}
        />
        <div
          className={cn(
            "mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl transition-colors",
            drag ? "bg-[#4f46e5] text-white" : "bg-[#f4f4f5] text-[#71717a]",
          )}
        >
          <FileText className="h-7 w-7" />
        </div>
        <h3 className="text-base font-semibold text-[#09090b]">
          {busy ? "Extracting and parsing…" : "Drop your resume here"}
        </h3>
        <p className="mt-1.5 text-sm text-[#71717a]">
          PDF or DOCX · up to 10 MB · text-based only
        </p>
        <Button className="mt-6" disabled={busy}>
          {busy ? <><Spinner size={14} /> Parsing with AI…</> : <><Plus className="h-4 w-4" /> Choose a file</>}
        </Button>
      </div>
      <p className="text-center text-xs text-[#a1a1aa]">
        Resume is parsed by an LLM — review and correct the extraction on the next step.
      </p>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Connect Step                                                        */
/* ─────────────────────────────────────────────────────────────────── */
function ConnectStep({
  resume, connected, detected, handles, setHandles, connecting, connect,
  connectMsg, autoConnecting, autoConnectAll, removeSkill, onBack, onNext,
}: {
  resume: ParsedResume;
  connected: Set<string>;
  detected: Record<string, string>;
  handles: Record<string, string>;
  setHandles: (updater: (prev: Record<string, string>) => Record<string, string>) => void;
  connecting: string | null;
  connect: (platform: string) => void;
  connectMsg: Record<string, string>;
  autoConnecting: boolean;
  autoConnectAll: () => void;
  removeSkill: (skill: string) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const total = PLATFORM_CATEGORIES.reduce((n, c) => n + c.ids.length, 0);
  const detectedCount = Object.keys(detected).length;

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e4e4e7] bg-white p-4">
        <div className="text-sm text-[#71717a]">
          <span className="font-semibold text-[#09090b]">{connected.size}</span>
          <span className="text-[#a1a1aa]"> / {total}</span> profiles connected
          {connected.size > 0 && (
            <span className="ml-2 text-xs font-medium text-[#16a34a]">· GitHub fetched live</span>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={onBack}>
            <ChevronLeft className="h-3.5 w-3.5" /> Back
          </Button>
          <Button size="sm" onClick={onNext}>
            Continue <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Auto-connect banner */}
      {detectedCount > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[#c7d2fe] bg-[#eef2ff] px-4 py-3">
          <Sparkles className="h-4 w-4 shrink-0 text-[#4f46e5]" />
          <span className="text-sm font-medium text-[#4f46e5]">
            {detectedCount} platform{detectedCount === 1 ? "" : "s"} detected in resume
          </span>
          <div className="flex flex-wrap gap-1">
            {Object.entries(detected).map(([pid, handle]) => (
              <Chip key={pid} tone="brand">
                {platformById(pid)?.label ?? pid} · {handle}
              </Chip>
            ))}
          </div>
          <Button size="sm" className="ml-auto" onClick={autoConnectAll} disabled={autoConnecting}>
            {autoConnecting ? <><Spinner size={12} /> Connecting…</> : "Auto-connect all"}
          </Button>
        </div>
      )}

      {autoConnecting && (
        <div className="flex items-center gap-2 rounded-xl border border-[#e4e4e7] bg-white px-4 py-3 text-sm text-[#71717a]">
          <Spinner size={14} /> Detecting and connecting profiles…
        </div>
      )}

      {Object.keys(connectMsg).length > 0 && (
        <div className="space-y-1 rounded-xl border border-[#e4e4e7] bg-white px-4 py-3 text-xs text-[#71717a]">
          {Object.entries(connectMsg).map(([platform, msg]) => (
            <div key={platform}>
              <span className="font-semibold text-[#09090b]">
                {platform === "_auto" ? "Auto-connect" : platformById(platform)?.label ?? platform}:
              </span>{" "}
              {msg}
            </div>
          ))}
        </div>
      )}

      {/* Platform grids */}
      {PLATFORM_CATEGORIES.map((cat) => (
        <div key={cat.name}>
          <h3 className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-widest text-[#a1a1aa]">
            {cat.name}
          </h3>
          <div className="grid gap-2 md:grid-cols-2">
            {cat.ids.map((id) => {
              const def = platformById(id)!;
              const isConnected = connected.has(id);
              const msg = connectMsg[id];
              const detectedHandle = detectHandleFor(resume, detected, id);
              return (
                <div
                  key={id}
                  className={cn(
                    "flex items-center gap-3 rounded-xl border p-3 transition-colors",
                    isConnected
                      ? "border-[#bbf7d0] bg-[#f0fdf4]"
                      : "border-[#e4e4e7] bg-white",
                  )}
                >
                  <PlatformIcon id={id} label={def.label} size={32} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold text-[#09090b]">{def.label}</span>
                      {detectedHandle && !isConnected && (
                        <span className="rounded-full bg-[#eef2ff] px-2 py-0.5 text-[10px] font-semibold text-[#4f46e5]">
                          {detectedHandle}
                        </span>
                      )}
                      <span
                        className={cn(
                          "ml-auto rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                          def.real_api
                            ? "bg-[#f0fdf4] text-[#16a34a]"
                            : "bg-[#f4f4f5] text-[#a1a1aa]",
                        )}
                      >
                        {def.real_api ? "Live" : "Demo"}
                      </span>
                    </div>

                    {isConnected ? (
                      <div className="mt-0.5 flex items-center gap-1 text-xs font-medium text-[#16a34a]">
                        <Check className="h-3 w-3" strokeWidth={3} />
                        Connected as {handleFor(def.label, handles[id] ?? detectedHandle ?? "profile")}
                      </div>
                    ) : (
                      <div className="mt-1.5 flex items-center gap-1.5">
                        <Input
                          value={handles[id] ?? ""}
                          onChange={(e) => setHandles((h) => ({ ...h, [id]: e.target.value }))}
                          onKeyDown={(e) => e.key === "Enter" && connect(id)}
                          placeholder={detectedHandle ?? def.handle_placeholder}
                          className="h-7 text-xs"
                        />
                        <Button
                          size="sm"
                          onClick={() => connect(id)}
                          disabled={connecting === id || !handles[id]?.trim()}
                          className="h-7 shrink-0 px-2.5 text-xs"
                        >
                          {connecting === id ? <Spinner size={11} /> : "Connect"}
                        </Button>
                      </div>
                    )}
                    {msg && !isConnected && (
                      <div className="mt-1 text-[11px] text-[#dc2626]">{msg}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Skills review */}
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-4">
        <h4 className="mb-3 text-sm font-semibold text-[#09090b]">Parsed skills — review & remove</h4>
        <div className="flex flex-wrap gap-1.5">
          {(Object.entries(resume.skills) as Array<[string, string[]]>).flatMap(([, skills]) =>
            skills.map((s) => (
              <Chip key={s} removable onRemove={() => removeSkill(s)}>
                {s}
              </Chip>
            )),
          )}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Analyze Step                                                        */
/* ─────────────────────────────────────────────────────────────────── */
function AnalyzeStep({
  resume, profiles, running, stageLog, onRun, onBack,
}: {
  resume: ParsedResume;
  profiles: ConnectedProfile[];
  running: boolean;
  stageLog: Array<{ stage: string; message: string; done: boolean }>;
  onRun: () => void;
  onBack: () => void;
}) {
  const name = resume.personal.name ?? "Candidate";
  const skillCount = Object.values(resume.skills).flat().length;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#e4e4e7] bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-[#09090b]">Verify {name}</h3>
            <p className="mt-0.5 text-sm text-[#71717a]">
              {profiles.length} profile{profiles.length !== 1 ? "s" : ""} connected ·{" "}
              {resume.projects.length} projects · {skillCount} skills
            </p>
          </div>
          <Button onClick={onRun} disabled={running}>
            {running ? (
              <><Spinner size={14} /> Analyzing…</>
            ) : (
              <><Search className="h-4 w-4" /> Run verification</>
            )}
          </Button>
        </div>
        {!running && stageLog.length === 0 && (
          <p className="mt-3 text-xs leading-relaxed text-[#a1a1aa]">
            The pipeline analyses GitHub repositories, aggregates coding platforms, verifies every
            claim, computes 10 explainable scores and writes the AI summary.
          </p>
        )}
      </div>

      {stageLog.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[#e4e4e7] bg-white">
          {stageLog.map((s, i) => {
            const meta = STAGES_META[s.stage];
            const isActive = !s.done && i === stageLog.length - 1;
            return (
              <div
                key={i}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 text-sm transition-colors",
                  isActive && "bg-[#eef2ff]",
                  i < stageLog.length - 1 && "border-b border-[#f0f0f2]",
                )}
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg">
                  {s.done ? (
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#f0fdf4]">
                      <Check className="h-3.5 w-3.5 text-[#16a34a]" strokeWidth={3} />
                    </span>
                  ) : (
                    <Spinner size={15} />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className={cn("font-medium", isActive ? "text-[#4f46e5]" : "text-[#09090b]")}>
                    {meta?.label ?? s.stage}
                  </div>
                  <div className="text-xs text-[#71717a]">{meta?.desc ?? s.message}</div>
                </div>
                {s.done && (
                  <span className="shrink-0 text-[11px] text-[#a1a1aa]">{s.message}</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="text-center">
        <Button variant="ghost" size="sm" onClick={onBack} disabled={running}>
          <ChevronLeft className="h-3.5 w-3.5" /> Back to profiles
        </Button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────── */
/* Helpers                                                             */
/* ─────────────────────────────────────────────────────────────────── */
function detectHandleFor(resume: ParsedResume, detected: Record<string, string>, platformId: string): string {
  if (detected[platformId]) return detected[platformId];
  if (platformId === "github" && resume.personal.github) {
    const m = resume.personal.github.match(/github\.com\/([^/]+)/i);
    if (m) return m[1];
  }
  if (platformId === "linkedin" && resume.personal.linkedin) {
    const m = resume.personal.linkedin.match(/linkedin\.com\/in\/([^/]+)/i);
    if (m) return m[1];
  }
  if (platformId === "portfolio" && resume.personal.portfolio) {
    return resume.personal.portfolio.replace(/^https?:\/\//, "");
  }
  return "";
}

function handleFor(label: string, handle: string): string {
  return label === "X (Twitter)" ? `@${handle}` : handle;
}

function LogoMark() {
  return (
    <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#4f46e5] text-[11px] font-bold text-white">
      100
    </span>
  );
}
