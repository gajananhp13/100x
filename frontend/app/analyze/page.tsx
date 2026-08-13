"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, runAnalysis } from "@/lib/api";
import { PLATFORM_CATEGORIES, platformById } from "@/lib/platforms";
import type { ConnectedProfile, ParsedResume } from "@/lib/types";
import { Button, Card, Chip, Spinner, cn } from "@/components/ui";
import { PlatformIcon } from "@/components/platform-icon";

type Step = 0 | 1 | 2;

const STAGES_META: Record<string, { label: string; desc: string }> = {
  init: { label: "Starting pipeline", desc: "Preparing the verification run" },
  github: { label: "GitHub analysis", desc: "Repositories, commits, CI/CD, documentation" },
  coding: { label: "Coding platforms", desc: "LeetCode, Codeforces, CodeChef, Kaggle, more" },
  skills: { label: "Skill verification", desc: "Matching technologies against public code" },
  projects: { label: "Project verification", desc: "Matching resume projects to repositories" },
  achievements: { label: "Achievement verification", desc: "Hackathons, certifications, contributions" },
  scoring: { label: "Computing scores", desc: "10 evidence-backed 0–100 scores" },
  summary: { label: "AI candidate summary", desc: "Writing the recruiter summary" },
  done: { label: "Report ready", desc: "Compiling the final report" },
};

export default function AnalyzePage() {
  const router = useRouter();
  const params = useSearchParams();
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

  // ?demo=1 → load demo candidate and run straight to the report
  useEffect(() => {
    if (params.get("demo") === "1" && !startedDemo.current) {
      startedDemo.current = true;
      void loadDemo().then(() => runNow());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

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
      // Auto-detect platform handles straight from the resume — no typing needed.
      try {
        const { handles: found } = await api.detectProfiles(parsed);
        setDetected(found);
        setHandles((h) => ({ ...h, ...found }));
      } catch {
        /* detection is best-effort; manual connect still works */
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const connect = async (platform: string) => {
    const handle = (handles[platform] ?? detected[platform] ?? "")
      .trim()
      .replace(/^@/, "");
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
        setConnectMsg((m) => ({ ...m, _auto: "No platform handles found in this resume — connect manually below." }));
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

  const setPersonal = (key: keyof ParsedResume["personal"], value: string) => {
    if (!resume) return;
    setResume({ ...resume, personal: { ...resume.personal, [key]: value } });
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-ink">
          <Logo /> 100x Resume
        </Link>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={loadDemo} disabled={busy || running}>
            Load demo candidate
          </Button>
          <Link href="/" className="text-sm text-muted hover:text-ink">Cancel</Link>
        </div>
      </div>

      <StepIndicator step={step} running={running} />

      {error && (
        <div className="mb-4 rounded-lg border border-rose/30 bg-rose-soft px-4 py-3 text-sm text-rose">
          {error}
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
        <Card className="p-10 text-center text-sm text-muted">
          Upload a resume first, or load the demo candidate above.
        </Card>
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
        <Card className="p-10 text-center text-sm text-muted">
          Nothing to analyze — go back and upload a resume.
        </Card>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */

function StepIndicator({ step, running }: { step: Step; running: boolean }) {
  const steps = [
    { n: 1, label: "Upload resume" },
    { n: 2, label: "Connect profiles" },
    { n: 3, label: "Analyze & report" },
  ];
  const analyzing = step === 2 && running;
  return (
    <div className="mb-8 flex items-center justify-center gap-2">
      {steps.map((s, i) => {
        const active = i === step;
        const done = i < step;
        return (
          <div key={s.n} className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                  done && "bg-emerald text-white",
                  active && "bg-accent text-white",
                  !done && !active && "border border-line-strong text-muted",
                )}
              >
                {done ? "✓" : s.n}
              </span>
              <span className={cn("text-sm font-medium", active ? "text-ink" : "text-muted")}>
                {s.label}
              </span>
            </div>
            {i < steps.length - 1 && <div className={cn("h-px w-10", done || active ? "bg-accent" : "bg-line")} />}
          </div>
        );
      })}
      {analyzing && <Spinner size={14} className="text-accent" />}
    </div>
  );
}

function UploadStep({ busy, onFile }: { busy: boolean; onFile: (f: File) => void }) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <Card className="p-10 text-center">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const f = e.dataTransfer.files?.[0];
          if (f) void onFile(f);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "grid-backdrop cursor-pointer rounded-xl border-2 border-dashed p-14 transition-colors",
          drag ? "border-accent bg-accent-soft/60" : "border-line-strong hover:border-accent/60",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void onFile(f);
            e.target.value = "";
          }}
        />
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-accent-soft text-2xl">
          📄
        </div>
        <h3 className="mt-4 text-lg font-semibold text-ink">
          {busy ? "Extracting and parsing…" : "Drop your resume here"}
        </h3>
        <p className="mt-1 text-sm text-muted">
          PDF or DOCX, up to 10 MB. Text-based documents only — scanned images are not supported.
        </p>
        <Button className="mt-6" onClick={() => inputRef.current?.click()}>
          {busy ? "Parsing with AI…" : "Choose a file"}
        </Button>
      </div>
      <p className="mt-4 text-xs text-muted">
        Resume is parsed by an AI engine — you can review and correct the extraction on the next step.
      </p>
    </Card>
  );
}

function ConnectStep({
  resume,
  connected,
  detected,
  handles,
  setHandles,
  connecting,
  connect,
  connectMsg,
  autoConnecting,
  autoConnectAll,
  removeSkill,
  onBack,
  onNext,
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
  const allSkills = resume.skills;
  const total = PLATFORM_CATEGORIES.reduce((n, c) => n + c.ids.length, 0);
  const detectedCount = Object.keys(detected).length;

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-muted">
          <span className="font-semibold text-ink">{connected.size}</span> / {total} profiles connected
          {connected.size > 0 && (
            <span className="ml-2 text-xs text-emerald">GitHub (when connected) is fetched live.</span>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>Back to upload</Button>
          <Button size="sm" onClick={onNext}>Continue to analysis →</Button>
        </div>
      </Card>

      {autoConnecting && (
        <Card className="flex items-center gap-2 text-sm text-accent">
          <Spinner size={14} /> Detecting and connecting profiles found in the resume…
        </Card>
      )}

      {Object.keys(connectMsg).length > 0 && (
        <Card className="space-y-1 px-4 py-3 text-xs text-muted">
          {Object.entries(connectMsg).map(([platform, msg]) => (
            <div key={platform}>
              <span className="font-semibold text-ink">
                {platform === "_auto" ? "Auto-connect" : platformById(platform)?.label ?? platform}:
              </span>{" "}
              {msg}
            </div>
          ))}
        </Card>
      )}

      {(detectedCount > 0 || connectMsg._auto) && (
        <Card className="flex flex-wrap items-center gap-2 px-4 py-3">
          <span className="text-xs font-semibold text-ink">
            {detectedCount > 0
              ? `${detectedCount} platform${detectedCount === 1 ? "" : "s"} detected in the resume`
              : "Auto-connect"}
          </span>
          <span className="flex flex-wrap gap-1.5">
            {Object.entries(detected).map(([pid, handle]) => (
              <Chip key={pid} className="gap-1">
                {platformById(pid)?.label ?? pid} · {handle}
              </Chip>
            ))}
          </span>
          {detectedCount > 0 && (
            <Button size="sm" className="ml-auto" onClick={autoConnectAll} disabled={autoConnecting}>
              {autoConnecting ? <><Spinner size={12} /> Connecting…</> : "Auto-connect all"}
            </Button>
          )}
        </Card>
      )}

      {PLATFORM_CATEGORIES.map((cat) => (
        <div key={cat.name}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">{cat.name}</h3>
          <div className="grid gap-2 md:grid-cols-2">
            {cat.ids.map((id) => {
              const def = platformById(id)!;
              const isConnected = connected.has(id);
              const msg = connectMsg[id];
              const detectedHandle = detectHandleFor(resume, detected, id);
              const placeholder = detectedHandle ?? def.handle_placeholder;
              return (
                <Card key={id} padded={false} className="flex items-center gap-3 p-3">
                  <PlatformIcon id={id} label={def.label} size={34} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-ink">{def.label}</span>
                      {detectedHandle && !isConnected && (
                        <span className="rounded-full bg-accent-soft px-1.5 py-px text-[10px] font-semibold text-accent">
                          Detected · {detectedHandle}
                        </span>
                      )}
                      <span
                        className={cn(
                          "rounded-full px-1.5 py-px text-[10px] font-semibold",
                          def.real_api ? "bg-emerald-soft text-emerald" : "bg-slate-soft text-slate",
                        )}
                      >
                        {def.real_api ? "Live API" : "Demo data"}
                      </span>
                    </div>
                    {!isConnected ? (
                      <div className="mt-1.5 flex items-center gap-1.5">
                        <input
                          value={handles[id] ?? ""}
                          onChange={(e) => setHandles((h) => ({ ...h, [id]: e.target.value }))}
                          onKeyDown={(e) => e.key === "Enter" && connect(id)}
                          placeholder={placeholder}
                          className="w-full rounded-md border border-line bg-canvas px-2 py-1 text-xs text-ink outline-none focus:border-accent"
                        />
                        <Button size="sm" onClick={() => connect(id)} disabled={connecting === id}>
                          {connecting === id ? <Spinner size={12} /> : "Connect"}
                        </Button>
                      </div>
                    ) : (
                      <div className="mt-1 flex items-center justify-between text-xs text-emerald">
                        <span>✓ Connected as {handleFor(def.label, handles[id] ?? detectedHandle ?? "profile")}</span>
                        <span className="text-xs text-emerald">Connected</span>
                      </div>
                    )}
                    {msg && !isConnected && <div className="mt-1 text-[11px] text-rose">{msg}</div>}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      ))}

      <Card className="mt-6">
        <h4 className="mb-2 text-sm font-semibold text-ink">Parsed skills — review & remove</h4>
        <div className="flex flex-wrap gap-1.5">
          {(Object.entries(allSkills) as Array<[string, string[]]>).flatMap(([, skills]) =>
            skills.map((s) => (
              <Chip key={s} className="gap-1 pr-1">
                {s}
                <button
                  onClick={() => removeSkill(s)}
                  className="ml-1 rounded-full px-1 text-muted hover:bg-slate-soft hover:text-rose"
                  aria-label={`Remove ${s}`}
                >
                  ×
                </button>
              </Chip>
            )),
          )}
        </div>
      </Card>
    </div>
  );
}

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

function AnalyzeStep({
  resume,
  profiles,
  running,
  stageLog,
  onRun,
  onBack,
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
      <Card className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">Verify {name}</h3>
            <p className="text-sm text-muted">
              {profiles.length} connected profile{profiles.length === 1 ? "" : "s"} ·{" "}
              {resume.projects.length} projects · {skillCount} skills
            </p>
          </div>
          <Button onClick={onRun} disabled={running}>
            {running ? <><Spinner size={14} /> Analyzing…</> : "Run verification"}
          </Button>
        </div>
        {!running && stageLog.length === 0 && (
          <div className="mt-3 text-xs text-muted">
            The pipeline parses nothing twice — it analyzes GitHub repositories, aggregates coding
            platforms, verifies every claim, computes 10 explainable scores and writes the AI summary.
          </div>
        )}
      </Card>

      {stageLog.length > 0 && (
        <Card className="p-2">
          {stageLog.map((s, i) => {
            const meta = STAGES_META[s.stage];
            return (
              <div
                key={i}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs">
                  {s.done ? (
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-soft text-emerald">✓</span>
                  ) : (
                    <Spinner size={16} className="text-accent" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-ink">{meta?.label ?? s.stage}</div>
                  <div className="text-xs text-muted">{meta?.desc ?? s.message}</div>
                </div>
                {s.done && <span className="text-[11px] text-muted">{s.message}</span>}
              </div>
            );
          })}
        </Card>
      )}

      <div className="text-center">
        <Button variant="ghost" size="sm" onClick={onBack} disabled={running}>
          ← Back to profiles
        </Button>
      </div>
    </div>
  );
}

function Logo() {
  return (
    <span className="inline-flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-teal text-[10px] font-bold text-white">
      100
    </span>
  );
}