// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type {
  AgentSightSnapshot,
  SnapshotAuditEvent,
  SnapshotNetworkTarget,
  SnapshotProcessNode,
  SnapshotToolCall,
} from '@/types/event';

export type EventSpanKind = 'sandbox' | 'exec' | 'llm' | 'network' | 'http' | 'tool';
export type EventSpanStatus = 'success' | 'failed' | 'running' | 'unknown';

export const EVENT_SPAN_KINDS: EventSpanKind[] = ['sandbox', 'exec', 'network', 'http', 'llm', 'tool'];

export interface EventSpan {
  id: string;
  kind: EventSpanKind;
  label: string;
  detail: string;
  start: number;
  end: number;
  /** The capture never saw this span finish; `end` is the last captured moment. */
  open: boolean;
  status: EventSpanStatus;
  pid: number | null;
  sandboxId?: string;
  /** Temporal inference within the session, never a proven causal edge. */
  modelCallId?: string;
  aggregated?: boolean;
}

export interface EventSpanOptions {
  /**
   * Latest moment the capture covers. Spans the capture never saw finish end
   * here; it defaults to the latest timestamp in the snapshot itself.
   */
  captureEnd?: number | null;
}

/**
 * Turn one snapshot into timed spans: commands from process lifetimes, model
 * calls from request/response pairs, network endpoints from their first and
 * last request, and tool calls from their reported start and end.
 */
export function eventSpans(snapshot: AgentSightSnapshot, options: EventSpanOptions = {}): EventSpan[] {
  const captureEnd = Math.max(latestTimestamp(snapshot), options.captureEnd ?? 0);
  const audit = snapshot.audit_events ?? [];
  const spans: EventSpan[] = [
    ...(snapshot.sandboxes ?? []).map((sandbox): EventSpan => ({
      id: `sandbox:${sandbox.id}`, kind: 'sandbox', label: sandbox.name || sandbox.cgroup_path || sandbox.id,
      detail: [sandbox.image, sandbox.runtime, `pidns ${sandbox.pidns}`].filter(Boolean).join(' · '),
      start: sandbox.first_seen_ms,
      end: sandbox.end_timestamp_ms ?? sandbox.last_seen_ms,
      open: sandbox.end_timestamp_ms == null,
      status: sandbox.exit_code == null ? 'unknown' : sandbox.exit_code === 0 ? 'success' : 'failed',
      pid: null, sandboxId: sandbox.id,
    })),
    ...(snapshot.process_nodes ?? []).flatMap((process) => processSpan(process, captureEnd)),
    ...llmSpans(audit),
    ...(snapshot.network_targets ?? []).filter((target) => !audit.some((row) =>
      row.audit_type === 'network' && row.action?.startsWith('http_') && row.pid === target.pid
      && row.sandbox_id === target.sandbox_id && row.target?.includes(target.host + (target.path ?? '')),
    )).flatMap(networkSpan),
    ...httpSpans(audit),
    ...audit.filter((event) => event.audit_type === 'network' && !event.action?.startsWith('http_')).map(connectSpan),
    ...(snapshot.tool_calls ?? []).map((tool) => toolSpan(tool, captureEnd)),
    ...audit.filter(isTranscriptTool).map(transcriptToolSpan),
  ].sort((left, right) => left.start - right.start || left.end - right.end || left.id.localeCompare(right.id));
  const processes = snapshot.process_nodes ?? [];
  const processAt = (pid: number | null, at: number) => processes.filter((p) => p.pid === pid
    && (p.start_timestamp_ms ?? 0) <= at && (p.end_timestamp_ms ?? Infinity) >= at)
    .sort((a, b) => (b.start_timestamp_ms ?? 0) - (a.start_timestamp_ms ?? 0))[0];
  const family = (span: EventSpan) => {
    let process = processAt(span.pid, span.start);
    const seen = new Set<number>();
    while (process?.ppid && !seen.has(process.pid)) {
      seen.add(process.pid);
      const parent = processAt(process.ppid, span.start);
      if (!parent) break;
      process = parent;
    }
    return process?.root_pid ?? process?.pid ?? span.pid;
  };
  for (const span of spans) {
    const sandbox = span.sandboxId ?? processAt(span.pid, span.start)?.sandbox_id;
    if (sandbox) span.sandboxId = sandbox;
  }
  const calls = spans.filter((span) => span.kind === 'llm');
  for (const span of spans) {
    if (!['exec', 'http', 'network'].includes(span.kind) || span.aggregated) continue;
    const call = calls.filter((call) => !call.open && call.end <= span.start
      && (snapshot.sessions?.length === 1 || (family(call) != null && family(call) === family(span))))
      .sort((a, b) => b.end - a.end || b.start - a.start)[0];
    if (call) span.modelCallId = call.id;
  }
  return spans;
}

/** Greedily pack intervals into rows so that no two intervals in a row overlap. */
export function packSpans<T extends { start: number; end: number }>(spans: T[], minGap = 0): T[][] {
  const rows: { end: number; spans: T[] }[] = [];
  const ordered = [...spans].sort((left, right) => left.start - right.start || right.end - left.end);
  for (const span of ordered) {
    const row = rows.find((candidate) => candidate.end + minGap <= span.start);
    if (row) {
      row.spans.push(span);
      row.end = Math.max(row.end, span.end);
    } else {
      rows.push({ end: span.end, spans: [span] });
    }
  }
  return rows.map((row) => row.spans);
}

/** Format an offset from the start of the timeline, e.g. `+42.5s` or `+3:07`. */
export function formatOffset(ms: number): string {
  const value = Math.max(0, ms);
  if (value < 60_000) return `+${(value / 1000).toFixed(1)}s`;
  const totalSeconds = Math.floor(value / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return hours
    ? `+${hours}:${String(minutes).padStart(2, '0')}:${seconds}`
    : `+${minutes}:${seconds}`;
}

/** Pick a round tick step so the axis shows at most `maxTicks` intervals. */
export function tickStep(rangeMs: number, maxTicks = 6): number {
  const steps = [
    1_000, 2_000, 5_000, 10_000, 15_000, 30_000,
    60_000, 120_000, 300_000, 600_000, 900_000, 1_800_000,
    3_600_000, 7_200_000, 21_600_000, 43_200_000, 86_400_000,
  ];
  return steps.find((step) => rangeMs / step <= maxTicks) ?? Math.ceil(rangeMs / maxTicks);
}

function processSpan(process: SnapshotProcessNode, captureEnd: number): EventSpan[] {
  const start = process.start_timestamp_ms ?? process.end_timestamp_ms;
  if (start == null) return [];
  // No end timestamp means the capture never saw the process exit, whatever
  // its status says (the capture reports a plain exec as "observed").
  const open = process.end_timestamp_ms == null;
  const end = Math.max(start, open ? captureEnd : process.end_timestamp_ms!);
  const reported = textStatus(process.status);
  const status: EventSpanStatus = process.exit_code != null
    ? (process.exit_code === 0 ? 'success' : 'failed')
    : reported && reported !== 'unknown' ? reported : open ? 'running' : 'unknown';
  return [{
    id: `exec:${process.id}`,
    kind: 'exec',
    label: (process.argv && process.argv.length > 1 ? process.argv.join(' ') : process.command) || process.argv?.join(' ') || process.comm || `pid ${process.pid}`,
    detail: [
      process.comm,
      `pid ${process.pid}`,
      process.exit_code != null ? `exit ${process.exit_code}` : null,
    ].filter(Boolean).join(' · '),
    start,
    end,
    open,
    status,
    pid: process.pid,
    ...(process.sandbox_id ? { sandboxId: process.sandbox_id } : {}),
  }];
}

// Captured rows carry their call identity: `audit-<call>-request` belongs to
// the `audit-<call>-call` (or `-response`) row of the same call.
const CALL_ROW = /^audit-(.+)-(request|response|call)$/;

function llmSpans(events: SnapshotAuditEvent[]): EventSpan[] {
  const rows = events
    .filter((event) => event.audit_type === 'llm')
    .sort((left, right) => left.timestamp_ms - right.timestamp_ms);
  const spans: EventSpan[] = [];
  const requests = new Map<string, SnapshotAuditEvent>();
  const byProcess = new Map<string, SnapshotAuditEvent[]>();
  for (const event of rows) {
    const call = CALL_ROW.exec(event.id);
    if (call?.[2] === 'request') {
      requests.set(call[1], event);
    } else if (call) {
      const request = requests.get(call[1]);
      requests.delete(call[1]);
      spans.push(request ? llmSpan(request, event) : llmSpan(event, null));
    } else {
      const key = `${event.pid ?? ''}:${event.comm ?? ''}`;
      const sameProcess = byProcess.get(key);
      if (sameProcess) sameProcess.push(event);
      else byProcess.set(key, [event]);
    }
  }
  for (const request of requests.values()) spans.push(llmSpan(request, null));

  // Rows without a call identity, such as agent-native transcript rows, pair
  // each request with the next response from the same process.
  for (const sameProcess of byProcess.values()) {
    const pending: SnapshotAuditEvent[] = [];
    for (const event of sameProcess) {
      if (event.action === 'request') {
        pending.push(event);
        continue;
      }
      const index = pending.findIndex((request) => (
        !request.subject || !event.subject || request.subject === event.subject
      ));
      if ((event.action === 'response' || event.action === 'call') && index >= 0) {
        spans.push(llmSpan(pending.splice(index, 1)[0], event));
      } else {
        spans.push(llmSpan(event, null));
      }
    }
    for (const request of pending) spans.push(llmSpan(request, null));
  }

  // A session view can hold the same call twice: once as captured traffic and
  // once as an agent-native transcript row. Keep one span per call.
  const unique = new Map<string, EventSpan>();
  for (const span of spans) {
    const key = `${span.pid ?? ''}|${span.start}|${span.end}|${span.label}`;
    const current = unique.get(key);
    if (!current || (current.status === 'unknown' && span.status !== 'unknown')) unique.set(key, span);
  }
  return [...unique.values()];
}

function llmSpan(first: SnapshotAuditEvent, response: SnapshotAuditEvent | null): EventSpan {
  const duration = response ? null : numberValue(first.details, 'duration_ms') ?? numberValue(first.details, 'latency_ms');
  const end = response?.timestamp_ms ?? first.timestamp_ms + Math.max(0, duration ?? 0);
  const model = response?.subject || first.subject;
  const reported = textStatus(response?.status ?? first.status);
  // A response that came back means the call completed, even when the source
  // only reports that it was observed.
  const status = response && (reported == null || reported === 'unknown') ? 'success' : reported ?? 'unknown';
  return {
    id: `llm:${first.id}${response ? `:${response.id}` : ''}`,
    kind: 'llm',
    label: first.summary || response?.summary || model || 'model call',
    detail: [model, first.comm, first.pid != null ? `pid ${first.pid}` : null].filter(Boolean).join(' · '),
    start: first.timestamp_ms,
    end: Math.max(first.timestamp_ms, end),
    open: !response && first.action === 'request' && duration == null,
    status,
    pid: first.pid ?? null,
    ...(first.sandbox_id ? { sandboxId: first.sandbox_id } : {}),
  };
}

function networkSpan(target: SnapshotNetworkTarget, index: number): EventSpan[] {
  const start = target.first_timestamp_ms ?? target.last_timestamp_ms;
  if (start == null) return [];
  const errors = target.error_count ?? 0;
  const requests = target.count ?? 0;
  return [{
    id: `network:${target.pid ?? ''}:${target.host}:${target.path ?? ''}:${index}`,
    kind: 'http',
    aggregated: true,
    ...(target.sandbox_id ? { sandboxId: target.sandbox_id } : {}),
    label: `${target.host}${target.path ?? ''}`,
    detail: [
      `${requests} ${requests === 1 ? 'request' : 'requests'}`,
      errors ? `${errors} ${errors === 1 ? 'error' : 'errors'}` : null,
      target.comm,
      target.pid != null ? `pid ${target.pid}` : null,
    ].filter(Boolean).join(' · '),
    start,
    end: Math.max(start, target.last_timestamp_ms ?? start),
    open: false,
    // The window aggregates many requests; it failed only when every request did.
    status: requests > 0 && errors >= requests ? 'failed' : 'success',
    pid: target.pid ?? null,
  }];
}

function httpSpans(events: SnapshotAuditEvent[]): EventSpan[] {
  const pending = new Map<string, SnapshotAuditEvent[]>();
  const spans: EventSpan[] = [];
  for (const event of events.filter((row) => row.audit_type === 'network' && row.action?.startsWith('http_'))
    .sort((a, b) => a.timestamp_ms - b.timestamp_ms)) {
    const details = isRecord(event.details) ? event.details : {};
    const endpoint = event.target?.replace(/^\S+\s+/, '');
    const identity = details.http_exchange_id ?? `${event.pid}:${details.tid ?? ''}:${endpoint}`;
    const key = `${event.sandbox_id ?? ''}:${identity}`;
    if (event.action === 'http_request') {
      pending.set(key, [...(pending.get(key) ?? []), event]);
    } else {
      const request = pending.get(key)?.shift();
      const span = connectSpan(request ?? event);
      span.kind = 'http';
      span.label = (request ?? event).target || span.label;
      span.end = event.timestamp_ms;
      span.status = textStatus(event.status) ?? 'unknown';
      spans.push(span);
    }
  }
  for (const requests of pending.values()) for (const request of requests) {
    const span = connectSpan(request);
    span.kind = 'http';
    span.label = request.target || span.label;
    spans.push(span);
  }
  return spans;
}

function connectSpan(event: SnapshotAuditEvent): EventSpan {
  return {
    id: `network:${event.id}`,
    kind: 'network',
    label: [event.action, event.target].filter(Boolean).join(' ') || event.summary || 'network',
    detail: [event.comm, event.pid != null ? `pid ${event.pid}` : null].filter(Boolean).join(' · '),
    start: event.timestamp_ms,
    end: event.timestamp_ms,
    open: false,
    status: textStatus(event.status) ?? 'unknown',
    pid: event.pid ?? null,
    ...(event.sandbox_id ? { sandboxId: event.sandbox_id } : {}),
  };
}

function toolSpan(tool: SnapshotToolCall, captureEnd: number): EventSpan {
  const start = tool.start_timestamp_ms ?? tool.timestamp_ms;
  const reportedEnd = tool.end_timestamp_ms
    ?? (tool.duration_ms != null ? start + tool.duration_ms : null);
  const status = textStatus(tool.status) ?? 'unknown';
  const open = reportedEnd == null && status === 'running';
  return {
    id: `tool:${tool.id}`,
    kind: 'tool',
    label: [tool.tool_name || 'tool', toolArgument(tool.input)].filter(Boolean).join(' · '),
    detail: [
      exitCode(tool.output) != null ? `exit ${exitCode(tool.output)}` : null,
      tool.related_pid != null ? `pid ${tool.related_pid}` : null,
    ].filter(Boolean).join(' · '),
    start,
    end: Math.max(start, reportedEnd ?? (open ? captureEnd : start)),
    open,
    status,
    pid: tool.related_pid ?? null,
  };
}

// Agent-native session detail turns its tool calls into `system` audit rows
// that carry the tool name and a time, without a duration.
function isTranscriptTool(event: SnapshotAuditEvent): boolean {
  return event.audit_type === 'system' && isRecord(event.details) && typeof event.details.tool_name === 'string';
}

function transcriptToolSpan(event: SnapshotAuditEvent): EventSpan {
  const details = event.details as Record<string, unknown>;
  return {
    id: `tool:${event.id}`,
    kind: 'tool',
    label: [String(details.tool_name), toolArgument(details)].filter(Boolean).join(' · '),
    detail: event.pid != null ? `pid ${event.pid}` : '',
    start: event.timestamp_ms,
    end: event.timestamp_ms,
    open: false,
    status: textStatus(event.status) ?? 'unknown',
    pid: event.pid ?? null,
    ...(event.sandbox_id ? { sandboxId: event.sandbox_id } : {}),
  };
}

function toolArgument(input: unknown): string | null {
  if (!isRecord(input)) return null;
  for (const key of ['command', 'cmd', 'path', 'file_path', 'query', 'pattern', 'url']) {
    const value = input[key];
    if (typeof value === 'string' && value) return value;
    if (Array.isArray(value) && value.every((item) => typeof item === 'string')) return value.join(' ');
  }
  return null;
}

function exitCode(output: unknown): number | null {
  return numberValue(output, 'exit_code');
}

function textStatus(value?: string | null): EventSpanStatus | null {
  const text = (value ?? '').toLowerCase();
  if (!text) return null;
  if (/fail|error|denied|blocked|kill|timeout|abort/.test(text)) return 'failed';
  if (/running|pending|progress|started/.test(text)) return 'running';
  if (/success|ok|complete|done|exited/.test(text)) return 'success';
  return 'unknown';
}

function latestTimestamp(snapshot: AgentSightSnapshot): number {
  let latest = Number.NEGATIVE_INFINITY;
  const see = (value?: number | null) => {
    if (typeof value === 'number' && Number.isFinite(value) && value > latest) latest = value;
  };
  see(snapshot.summary?.end_timestamp_ms);
  for (const row of snapshot.process_nodes ?? []) { see(row.start_timestamp_ms); see(row.end_timestamp_ms); }
  for (const row of snapshot.audit_events ?? []) see(row.timestamp_ms);
  for (const row of snapshot.tool_calls ?? []) { see(row.timestamp_ms); see(row.end_timestamp_ms); }
  for (const row of snapshot.network_targets ?? []) { see(row.first_timestamp_ms); see(row.last_timestamp_ms); }
  for (const row of snapshot.resource_samples ?? []) see(row.timestamp_ms);
  for (const row of snapshot.sessions ?? []) { see(row.start_timestamp_ms); see(row.end_timestamp_ms); }
  return Number.isFinite(latest) ? latest : 0;
}

function numberValue(value: unknown, key: string): number | null {
  if (!isRecord(value)) return null;
  const number = value[key];
  return typeof number === 'number' && Number.isFinite(number) ? number : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
