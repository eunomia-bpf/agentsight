/**
 * AgentSight backend API client
 *
 * When the frontend is served by agentsight itself (embedded mode), the API
 * is on the same host/port as the page — use window.location.origin.
 * Otherwise fall back to REACT_APP_API_BASE or localhost:7396 for local dev.
 */

const API_BASE: string = (() => {
  // Explicit override via env var (set at build time for non-embedded deployments)
  if (typeof process !== 'undefined' && (process.env as any).REACT_APP_API_BASE) {
    return (process.env as any).REACT_APP_API_BASE as string;
  }
  // In a real browser context, use the same origin so it works on any host/port
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    return window.location.origin;
  }
  // Fallback for local dev (webpack-dev-server on :3000 → backend on :7396)
  return 'http://localhost:7396';
})();

// ─── Types mirroring backend response structs ────────────────────────────────

export interface SessionSummary {
  session_id: string;
  trace_count: number;
  first_seen_ns: number;
  last_seen_ns: number;
  total_input_tokens: number;
  total_output_tokens: number;
  model: string | null;
  agent_name: string | null;
}

export interface TraceSummary {
  trace_id: string;
  call_count: number;
  total_input_tokens: number;
  total_output_tokens: number;
  start_ns: number;
  end_ns: number | null;
  model: string | null;
  /** First user_query recorded in this trace (best-effort) */
  user_query: string | null;
}

export interface TraceEventDetail {
  id: number;
  call_id: string | null;
  start_timestamp_ns: number;
  end_timestamp_ns: number | null;
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  /** Raw JSON string — parse before use */
  input_messages: string | null;
  /** Raw JSON string — parse before use */
  output_messages: string | null;
  /** Raw JSON string — parse before use */
  system_instructions: string | null;
  agent_name: string | null;
  process_name: string | null;
  pid: number | null;
  /** The user query that triggered this LLM call */
  user_query: string | null;
  /** Raw full event JSON — fallback when output_messages is null */
  event_json: string | null;
}

// ─── Internal helpers ────────────────────────────────────────────────────────

async function apiFetch<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${url} -> ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * List sessions within a nanosecond time range.
 * Defaults to the last 24 h when omitted.
 */
export async function fetchSessions(
  startNs?: number,
  endNs?: number
): Promise<SessionSummary[]> {
  const params = new URLSearchParams();
  if (startNs !== undefined) params.set('start_ns', String(startNs));
  if (endNs !== undefined) params.set('end_ns', String(endNs));
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<SessionSummary[]>(`${API_BASE}/api/sessions${qs}`);
}

/**
 * List all trace IDs within a session, with per-trace token stats.
 */
export async function fetchTraces(sessionId: string): Promise<TraceSummary[]> {
  return apiFetch<TraceSummary[]>(
    `${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}/traces`
  );
}

/**
 * Fetch detailed LLM call events for a single trace.
 */
export async function fetchTraceDetail(traceId: string): Promise<TraceEventDetail[]> {
  return apiFetch<TraceEventDetail[]>(
    `${API_BASE}/api/traces/${encodeURIComponent(traceId)}`
  );
}

// ─── Agent-name & time-series APIs ───────────────────────────────────────────

/**
 * Fetch distinct agent names observed within the given time range.
 */
export async function fetchAgentNames(
  startNs?: number,
  endNs?: number
): Promise<string[]> {
  const params = new URLSearchParams();
  if (startNs !== undefined) params.set('start_ns', String(startNs));
  if (endNs !== undefined) params.set('end_ns', String(endNs));
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<string[]>(`${API_BASE}/api/agent-names${qs}`);
}

export interface TimeseriesBucket {
  bucket_start_ns: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface ModelTimeseriesBucket {
  bucket_start_ns: number;
  model: string;
  total_tokens: number;
}

export interface TimeseriesResponse {
  token_series: TimeseriesBucket[];
  model_series: ModelTimeseriesBucket[];
}

/**
 * Fetch time-bucketed token stats and per-model breakdowns.
 */
export async function fetchTimeseries(
  startNs: number,
  endNs: number,
  agentName?: string,
  buckets = 30
): Promise<TimeseriesResponse> {
  const params = new URLSearchParams({
    start_ns: String(startNs),
    end_ns: String(endNs),
    buckets: String(buckets),
  });
  if (agentName) params.set('agent_name', agentName);
  return apiFetch<TimeseriesResponse>(`${API_BASE}/api/timeseries?${params.toString()}`);
}

// ─── ATIF export APIs ────────────────────────────────────────────────────────

import type { AtifDocument, AgentHealthResponse } from '../types';

/**
 * Export a single trace as an ATIF v1.6 trajectory document.
 */
export async function fetchAtifByTrace(traceId: string): Promise<AtifDocument> {
  return apiFetch<AtifDocument>(
    `${API_BASE}/api/export/atif/trace/${encodeURIComponent(traceId)}`
  );
}

/**
 * Export a full session (all traces) as an ATIF v1.6 trajectory document.
 */
export async function fetchAtifBySession(sessionId: string): Promise<AtifDocument> {
  return apiFetch<AtifDocument>(
    `${API_BASE}/api/export/atif/session/${encodeURIComponent(sessionId)}`
  );
}

// ─── Agent health API ─────────────────────────────────────────────────────────

/**
 * Fetch the current health status of all discovered agent processes.
 */
export async function fetchAgentHealth(): Promise<AgentHealthResponse> {
  return apiFetch<AgentHealthResponse>(`${API_BASE}/api/agent-health`);
}

/**
 * Acknowledge and remove an offline agent by PID.
 */
export async function deleteAgentHealth(pid: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/agent-health/${pid}`, { method: 'DELETE' });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`DELETE /api/agent-health/${pid} -> ${res.status}: ${text}`);
  }
}

/**
 * Kill and re-launch a hung agent process.
 * Returns the new PID on success.
 */
export async function restartAgentHealth(pid: number): Promise<{ ok: boolean; new_pid: number; cmd: string[] }> {
  const res = await fetch(`${API_BASE}/api/agent-health/${pid}/restart`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`POST /api/agent-health/${pid}/restart -> ${res.status}: ${body.error ?? res.statusText}`);
  }
  return body;
}
