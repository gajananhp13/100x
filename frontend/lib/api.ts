import type { ParsedResume, ConnectedProfile, PlatformsResponse } from "./types";

async function json<T>(promise: Promise<Response>): Promise<T> {
  const res = await promise;
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () =>
    json<{ status: string; ai_provider: string; openai_reachable: boolean }>(
      fetch("/api/health"),
    ),

  platforms: () =>
    json<PlatformsResponse>(fetch("/api/integrations/platforms")),

  uploadResume: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return json<{ message: string; filename: string; char_count: number; text: string; text_preview: string }>(
      fetch("/api/resume/upload", { method: "POST", body: fd }),
    );
  },

  parseResume: (text: string) =>
    json<ParsedResume>(
      fetch("/api/resume/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      }),
    ),

  connectProfile: (platform: string, handle: string, resume?: ParsedResume) =>
    json<{ profile: ConnectedProfile | null; message: string }>(
      fetch("/api/integrations/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, handle, simulate: false, resume }),
      }),
    ),

  /** Auto-detect platform handles inside the resume — no user input needed. */
  detectProfiles: (resume: ParsedResume) =>
    json<{ handles: Record<string, string> }>(
      fetch("/api/integrations/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume }),
      }),
    ),

  /** Detect + connect every platform whose handle appears in the resume. */
  autoConnect: (resume: ParsedResume) =>
    json<{ message: string; handles: Record<string, string>; profiles: ConnectedProfile[]; skipped: string[] }>(
      fetch("/api/integrations/auto-connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume, simulate: false }),
      }),
    ),

  loadDemo: () =>
    json<{ message: string; candidate_name: string; resume: ParsedResume; profiles: ConnectedProfile[]; simulated: boolean }>(
      fetch("/api/integrations/demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }),
    ),

  getReport: (reportId: string) =>
    json<import("./types").CandidateReport>(fetch(`/api/report/${reportId}`)),

  pdfUrl: (reportId: string) => `/api/report/${reportId}/pdf`,
};

/**
 * Stream the analysis pipeline via SSE (server-sent events over a POST body
 * stream) and report every stage event. Resolves with the report_id.
 */
export async function runAnalysis(
  resume: ParsedResume,
  profiles: ConnectedProfile[],
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<string> {
  const res = await fetch("/api/analysis/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume, profiles }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Analysis failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let reportId = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let event = "";
      let data = "";
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7).trim();
        else if (line.startsWith("data: ")) data = line.slice(6).trim();
      }
      if (!data) continue;
      let parsed: Record<string, unknown>;
      try {
        parsed = JSON.parse(data);
      } catch {
        continue;
      }
      if (event === "complete" && typeof parsed.report_id === "string") {
        reportId = parsed.report_id;
      }
      onEvent(event, parsed);
    }
  }
  if (!reportId) throw new Error("The analysis finished without a report id.");
  return reportId;
}