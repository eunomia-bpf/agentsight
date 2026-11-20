// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type {
  AgentSightSnapshot,
  SnapshotAuditEvent,
  SnapshotNetworkTarget,
  SnapshotProcessNode,
  SnapshotToolCall,
} from '@/types/event';

export type EventSpanKind = 'exec' | 'llm' | 'network' | 'tool';
export type EventSpanStatus = 'success' | 'failed' | 'running' | 'unknown';

export const EVENT_SPAN_KINDS: EventSpanKind[] = ['exec', 'llm', 'network', 'tool'];

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
}

/**
 * Turn one snapshot into timed spans: commands from process lifetimes, model
 * calls from request/response pairs, network endpoints from their first and
 * last request, and tool calls from their reported start and end.
 *
 * Spans the capture never saw finish end at the latest timestamp in the
 * snapshot, so a recorded session keeps its own time range.
 */
export function eventSpans(snapshot: AgentSightSnapshot): EventSpan[] {
  const captureEnd = latestTimestamp(snapshot);
  return [
    ...(snapshot.process_nodes ?? []).flatMap((process) => processSpan(process, captureEnd)),
    ...llmSpans(snapshot.audit_events ?? []),
    ...(snapshot.network_targets ?? []).flatMap(networkSpan),
    ...(snapshot.audit_events ?? []).filter((event) => event.audit_type === 'network').map(connectSpan),
    ...(snapshot.tool_calls ?? []).map((tool) => toolSpan(tool, captureEnd)),
  ].sort((left, right) => left.start - right.start || left.end - right.end || left.id.localeCompare(right.id));
}

/** Greedily pack spans into rows so that no two spans in a row overlap. */
export function packSpans(spans: EventSpan[], minGap = 0): EventSpan[][] {
  const rows: { end: number; spans: EventSpan[] }[] = [];
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
  const open = process.end_timestamp_ms == null;
  const end = Math.max(start, open ? captureEnd : process.end_timestamp_ms!);
  const status: EventSpanStatus = process.exit_code != null
    ? (process.exit_code === 0 ? 'success' : 'failed')
    : textStatus(process.status) ?? (open ? 'running' : 'unknown');
  return [{
    id: `exec:${process.id}`,
    kind: 'exec',
    label: process.command || process.argv?.join(' ') || process.comm || `pid ${process.pid}`,
    detail: [
      process.comm,
      `pid ${process.pid}`,
      process.exit_code != null ? `exit ${process.exit_code}` : null,
    ].filter(Boolean).join(' · '),
    start,
    end,
    open: open && status === 'running',
    status,
    pid: process.pid,
  }];
}

function llmSpans(events: SnapshotAuditEvent[]): EventSpan[] {
  const byProcess = new Map<string, SnapshotAuditEvent[]>();
  for (const event of events) {
    if (event.audit_type !== 'llm') continue;
    const key = `${event.pid ?? ''}:${event.comm ?? ''}`;
    const rows = byProcess.get(key);
    if (rows) rows.push(event);
    else byProcess.set(key, [event]);
  }

  const spans: EventSpan[] = [];
  for (const rows of byProcess.values()) {
    const pending: SnapshotAuditEvent[] = [];
    for (const event of [...rows].sort((left, right) => left.timestamp_ms - right.timestamp_ms)) {
      if (event.action === 'request') {
        pending.push(event);
        continue;
      }
      if (event.action === 'response') {
        const index = pending.findIndex((request) => (
          !request.subject || !event.subject || request.subject === event.subject
        ));
        if (index >= 0) {
          const [request] = pending.splice(index, 1);
          spans.push(llmSpan(request, event));
          continue;
        }
      }
      spans.push(llmSpan(event, null));
    }
    for (const request of pending) spans.push(llmSpan(request, null));
  }

  // A session view can hold the same call twice: once as captured traffic and
  // once as an agent-native transcript row. Keep one span per call.
  const unique = new Map<string, EventSpan>();
  for (const span of spans) {
    const key = `${span.start}|${span.end}|${span.label}`;
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
    open: false,
    status,
    pid: first.pid ?? null,
  };
}

function networkSpan(target: SnapshotNetworkTarget, index: number): EventSpan[] {
  const start = target.first_timestamp_ms ?? target.last_timestamp_ms;
  if (start == null) return [];
  const errors = target.error_count ?? 0;
  const requests = target.count ?? 0;
  return [{
    id: `network:${target.pid ?? ''}:${target.host}:${target.path ?? ''}:${index}`,
    kind: 'network',
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
    status: errors ? 'failed' : 'success',
    pid: target.pid ?? null,
  }];
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
