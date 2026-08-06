// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// Pure aggregation helpers for the overview dashboard. Every value here is
// derived solely from the materialized-view snapshot served by the collector
// (see Snapshot in agentsight-capture/src/model.rs). Nothing is invented: if a
// panel cannot be computed from the rows the collector emits, it is left empty.
//
// Ground truth of available rows: summary, token_summary[], network_targets[],
// process_nodes[], audit_events[], resource_samples[], sessions[], tool_calls[].
//   - audit_events carry: audit_type in {process, file, llm, network},
//     action in {exec, exit, write, request, response, call}, status, target,
//     summary, pid, comm, timestamp_ms, details.
//   - token_summary is grouped by model and carries input/output/cache_creation/
//     cache_read/total tokens plus a `calls` count.
//   - resource_samples carry cpu_percent and rss_mb per (pid, comm, timestamp).

import {
  AgentSightSnapshot,
  SnapshotAuditEvent,
  SnapshotSession,
} from '@/types/event';

// ---------------------------------------------------------------------------
// Formatting helpers (tabular numerals are applied at the component layer).
// ---------------------------------------------------------------------------

export function formatTokens(n: number): string {
  if (!Number.isFinite(n) || n === 0) return '0';
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(Math.round(n));
}

export function formatInt(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

export function formatDurationMs(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return '0s';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = s / 60;
  if (m < 60) return `${m.toFixed(1)}m`;
  const h = m / 60;
  return `${h.toFixed(1)}h`;
}

export function formatClock(ms: number | null | undefined): string {
  if (ms == null || !Number.isFinite(ms)) return '—';
  return new Date(ms).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// Shorten a path for dense lists: keep the basename and a hint of the parent.
export function shortPath(p: string, max = 48): string {
  if (!p) return '';
  if (p.length <= max) return p;
  const base = p.split('/').pop() ?? p;
  if (base.length >= max - 3) return `…${base.slice(-(max - 1))}`;
  const head = p.slice(0, max - base.length - 3);
  return `${head}…/${base}`;
}

// ---------------------------------------------------------------------------
// Session-span / KPI summary band.
// ---------------------------------------------------------------------------

export interface DashboardSummary {
  startMs: number | null;
  endMs: number | null;
  durationMs: number;
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheCreationTokens: number;
  llmCalls: number;
  processExecs: number;
  processFailures: number;
  filesTouched: number;
  networkEndpoints: number;
  toolCalls: number;
  sessionCount: number;
  primaryAgent: string | null;
  primaryModel: string | null;
  cwd: string | null;
  hasFailures: boolean;
}

function num(v: unknown): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : 0;
}

export function deriveSummary(snapshot: AgentSightSnapshot): DashboardSummary {
  const summary = snapshot.summary ?? {};
  const tokenSummary = snapshot.token_summary ?? [];
  const audit = snapshot.audit_events ?? [];
  const sessions = snapshot.sessions ?? [];

  const inputTokens = tokenSummary.reduce((s, r) => s + num(r.input_tokens), 0);
  const outputTokens = tokenSummary.reduce((s, r) => s + num(r.output_tokens), 0);
  const cacheRead = tokenSummary.reduce((s, r) => s + num(r.cache_read_tokens), 0);
  const cacheCreation = tokenSummary.reduce(
    (s, r) => s + num(r.cache_creation_tokens),
    0,
  );

  const processExecs = audit.filter(
    (e) => e.audit_type === 'process' && e.action === 'exec',
  ).length;
  const processFailures = audit.filter(
    (e) => e.audit_type === 'process' && e.action === 'exit' && e.status === 'failure',
  ).length;
  const fileTargets = new Set(
    audit
      .filter((e) => e.audit_type === 'file')
      .map((e) => e.target)
      .filter((t): t is string => !!t),
  );

  const start = (summary.start_timestamp_ms as number | undefined) ?? null;
  const end = (summary.end_timestamp_ms as number | undefined) ?? null;
  const durationMs =
    start != null && end != null && end > start ? end - start : 0;

  const primary = pickPrimarySession(sessions);

  return {
    startMs: start,
    endMs: end,
    durationMs,
    totalTokens: num(summary.total_tokens),
    inputTokens,
    outputTokens,
    cacheReadTokens: cacheRead,
    cacheCreationTokens: cacheCreation,
    llmCalls: num(summary.llm_calls),
    processExecs,
    processFailures,
    filesTouched: fileTargets.size,
    networkEndpoints: (snapshot.network_targets ?? []).length,
    toolCalls: (snapshot.tool_calls ?? []).length,
    sessionCount: num(summary.sessions) || sessions.length,
    primaryAgent: primary?.agent_type ?? null,
    primaryModel: primary?.model ?? null,
    cwd: sessionCwd(primary),
    hasFailures: processFailures > 0,
  };
}

function pickPrimarySession(sessions: SnapshotSession[]): SnapshotSession | null {
  if (sessions.length === 0) return null;
  // Pick the session with the most tokens; fall back to the latest start.
  return [...sessions].sort((a, b) => {
    const tok = num(b.total_tokens) - num(a.total_tokens);
    if (tok !== 0) return tok;
    return num(b.start_timestamp_ms) - num(a.start_timestamp_ms);
  })[0];
}

function sessionCwd(session: SnapshotSession | null): string | null {
  if (!session) return null;
  const attrs = session.attributes as Record<string, unknown> | undefined;
  const cwd = attrs?.cwd;
  return typeof cwd === 'string' && cwd.length > 0 ? cwd : null;
}

// ---------------------------------------------------------------------------
// Activity over time (stacked area). The session "shape": when was it busy,
// and with what. Drives the clickable strip that jumps into the timeline.
// ---------------------------------------------------------------------------

export interface ActivityBucket {
  startMs: number;
  endMs: number;
  // Count per audit_type within this bucket. Keys not present are zero.
  counts: Record<string, number>;
  total: number;
}

export interface ActivitySeries {
  startMs: number;
  endMs: number;
  spanMs: number;
  bucketMs: number;
  buckets: ActivityBucket[];
  types: string[]; // present, ordered by first appearance then fixed palette order
  maxBucketTotal: number;
  total: number;
}

const TYPE_DISPLAY_ORDER = ['llm', 'process', 'file', 'network', 'system', 'tool', 'session'];

export function deriveActivity(
  snapshot: AgentSightSnapshot,
  bucketCount = 48,
): ActivitySeries | null {
  const events = (snapshot.audit_events ?? []).filter(
    (e) => Number.isFinite(e.timestamp_ms) && e.timestamp_ms > 0,
  );
  if (events.length === 0) return null;

  const timestamps = events.map((e) => e.timestamp_ms);
  const startMs = Math.min(...timestamps);
  const endMs = Math.max(...timestamps);
  const spanMs = Math.max(endMs - startMs, 1);
  const bucketMs = spanMs / Math.max(bucketCount, 1);

  const buckets: ActivityBucket[] = Array.from({ length: bucketCount }, (_, i) => ({
    startMs: startMs + i * bucketMs,
    endMs: startMs + (i + 1) * bucketMs,
    counts: {},
    total: 0,
  }));

  for (const e of events) {
    let idx = Math.floor((e.timestamp_ms - startMs) / bucketMs);
    if (idx < 0) idx = 0;
    if (idx >= bucketCount) idx = bucketCount - 1;
    const b = buckets[idx];
    b.counts[e.audit_type] = (b.counts[e.audit_type] ?? 0) + 1;
    b.total += 1;
  }

  const present = new Set(events.map((e) => e.audit_type));
  const types = [
    ...TYPE_DISPLAY_ORDER.filter((t) => present.has(t)),
    ...Array.from(present).filter((t) => !TYPE_DISPLAY_ORDER.includes(t)).sort(),
  ];
  const maxBucketTotal = Math.max(1, ...buckets.map((b) => b.total));

  return {
    startMs,
    endMs,
    spanMs,
    bucketMs,
    buckets,
    types,
    maxBucketTotal,
    total: events.length,
  };
}

// ---------------------------------------------------------------------------
// Tokens by model. The "where did the tokens go" question.
// Cost is intentionally NOT derived: the collector emits no price field.
// ---------------------------------------------------------------------------

export interface TokenPart {
  key: 'input' | 'output' | 'cache_creation' | 'cache_read';
  label: string;
  value: number;
  color: string;
}

export interface TokenModel {
  model: string;
  calls: number;
  total: number;
  parts: TokenPart[];
}

export interface TokenComposition {
  models: TokenModel[];
  grandTotal: number;
  partsTotals: Record<TokenPart['key'], number>;
}

const TOKEN_PART_LABELS: Record<TokenPart['key'], string> = {
  input: 'Input',
  output: 'Output',
  cache_creation: 'Cache write',
  cache_read: 'Cache read',
};

export function deriveTokenComposition(
  snapshot: AgentSightSnapshot,
  tokenColors: Record<TokenPart['key'], string>,
): TokenComposition {
  const rows = snapshot.token_summary ?? [];
  const models: TokenModel[] = rows
    .map((r) => {
      const input = num(r.input_tokens);
      const output = num(r.output_tokens);
      const cacheCreation = num(r.cache_creation_tokens);
      const cacheRead = num(r.cache_read_tokens);
      const total = input + output + cacheCreation + cacheRead;
      const allParts: TokenPart[] = [
        { key: 'input', label: TOKEN_PART_LABELS.input, value: input, color: tokenColors.input },
        { key: 'output', label: TOKEN_PART_LABELS.output, value: output, color: tokenColors.output },
        { key: 'cache_creation', label: TOKEN_PART_LABELS.cache_creation, value: cacheCreation, color: tokenColors.cache_creation },
        { key: 'cache_read', label: TOKEN_PART_LABELS.cache_read, value: cacheRead, color: tokenColors.cache_read },
      ];
      const parts = allParts.filter((p) => p.value > 0);
      return {
        model: r.group || 'unknown',
        calls: num(r.calls),
        total,
        parts,
      };
    })
    .filter((m) => m.total > 0)
    .sort((a, b) => b.total - a.total);

  const partsTotals: Record<TokenPart['key'], number> = {
    input: 0,
    output: 0,
    cache_creation: 0,
    cache_read: 0,
  };
  for (const m of models) {
    for (const p of m.parts) partsTotals[p.key] += p.value;
  }
  const grandTotal = models.reduce((s, m) => s + m.total, 0);

  return { models, grandTotal, partsTotals };
}

// ---------------------------------------------------------------------------
// Effect profile: processes / files / network. The layer that distinguishes
// AgentSight from an application-level tracer.
// ---------------------------------------------------------------------------

export interface EffectItem {
  label: string;
  sublabel?: string;
  count: number;
  color: string;
}

export interface EffectProfile {
  processExecs: number;
  processExits: number;
  processFailures: number;
  fileEvents: number;
  uniqueFiles: number;
  networkEvents: number;
  networkErrorEvents: number;
  topCommands: EffectItem[];
  topFiles: EffectItem[];
  topHosts: EffectItem[];
  // Relative mix used for the summary segmented bar.
  mix: { type: string; label: string; count: number; color: string }[];
  totalEffects: number;
}

function commandLabel(e: SnapshotAuditEvent): string {
  const details = e.details as Record<string, unknown> | undefined;
  const full = details?.full_command;
  if (typeof full === 'string' && full.length > 0) return full;
  if (typeof e.target === 'string' && e.target.length > 0) return e.target;
  return e.comm ?? e.subject ?? 'process';
}

export function deriveEffects(
  snapshot: AgentSightSnapshot,
  eventColors: Record<string, string>,
  pickColor: (name: string) => string,
): EffectProfile {
  const audit = snapshot.audit_events ?? [];
  const networkTargets = snapshot.network_targets ?? [];

  const processExecs = audit.filter(
    (e) => e.audit_type === 'process' && e.action === 'exec',
  );
  const processExits = audit.filter(
    (e) => e.audit_type === 'process' && e.action === 'exit',
  );
  const processFailures = processExits.filter((e) => e.status === 'failure');
  const fileEvents = audit.filter((e) => e.audit_type === 'file');
  const fileTargets = new Set(
    fileEvents.map((e) => e.target).filter((t): t is string => !!t),
  );

  const topCommands = topItems(
    processExecs.map((e) => ({ key: commandLabel(e), sub: e.comm ?? undefined })),
    6,
  ).map((it) => ({ ...it, color: pickColor(it.label) }));

  const topFiles = topItems(
    fileEvents.map((e) => ({ key: e.target ?? e.summary ?? 'file', sub: undefined })),
    6,
  ).map((it) => ({ ...it, color: pickColor(it.label) }));

  const hostAgg = new Map<
    string,
    { count: number; errors: number; paths: Set<string> }
  >();
  for (const t of networkTargets) {
    const key = t.host;
    const entry = hostAgg.get(key) ?? { count: 0, errors: 0, paths: new Set<string>() };
    entry.count += num(t.count);
    entry.errors += num(t.error_count);
    if (t.path) entry.paths.add(t.path);
    hostAgg.set(key, entry);
  }
  const topHosts: EffectItem[] = Array.from(hostAgg.entries())
    .map(([key, v]) => ({
      label: key,
      sublabel: v.paths.size > 1 ? `${v.paths.size} endpoints` : (Array.from(v.paths)[0] ?? undefined),
      count: v.count,
      color: pickColor(key),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const counts = {
    process: processExecs.length,
    file: fileEvents.length,
    network: networkTargets.reduce((s, t) => s + num(t.count), 0),
  };
  const mix = [
    { type: 'process', label: 'Processes', count: counts.process, color: eventColors.process ?? pickColor('process') },
    { type: 'file', label: 'Files', count: counts.file, color: eventColors.file ?? pickColor('file') },
    { type: 'network', label: 'Network', count: counts.network, color: eventColors.network ?? pickColor('network') },
  ];
  const totalEffects = mix.reduce((s, m) => s + m.count, 0);

  return {
    processExecs: processExecs.length,
    processExits: processExits.length,
    processFailures: processFailures.length,
    fileEvents: fileEvents.length,
    uniqueFiles: fileTargets.size,
    networkEvents: counts.network,
    networkErrorEvents: networkTargets.reduce((s, t) => s + num(t.error_count), 0),
    topCommands,
    topFiles,
    topHosts,
    mix,
    totalEffects,
  };
}

function topItems(
  entries: { key: string; sub?: string }[],
  limit: number,
): { label: string; sublabel?: string; count: number }[] {
  const map = new Map<string, { count: number; sub?: string }>();
  for (const e of entries) {
    const entry = map.get(e.key) ?? { count: 0, sub: e.sub };
    entry.count += 1;
    if (!entry.sub && e.sub) entry.sub = e.sub;
    map.set(e.key, entry);
  }
  return Array.from(map.entries())
    .map(([key, v]) => ({ label: key, sublabel: v.sub, count: v.count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

// ---------------------------------------------------------------------------
// Resource shape over time. A flat sustained CPU tail is the signature of a
// retry loop; it reads instantly from a sparkline and is invisible in a total.
// ---------------------------------------------------------------------------

export interface ResourcePoint {
  ms: number;
  value: number;
}

export interface ResourceSeries {
  points: ResourcePoint[];
  max: number;
  mean: number;
  last: number | null;
  startMs: number;
  endMs: number;
  // Consecutive samples above `sustainThreshold` (a tail indicator). 0 if none.
  sustainedTail: number;
}

export interface ResourceShape {
  cpu: ResourceSeries | null;
  rss: ResourceSeries | null;
  sampleCount: number;
  processes: { comm: string; count: number }[];
}

export function deriveResourceShape(
  snapshot: AgentSightSnapshot,
  cpuSustain = 50,
): ResourceShape {
  const samples = (snapshot.resource_samples ?? [])
    .filter((s) => Number.isFinite(s.timestamp_ms))
    .slice()
    .sort((a, b) => a.timestamp_ms - b.timestamp_ms);

  const processes = topItems(
    samples.map((s) => ({ key: s.comm ?? String(s.pid ?? 'unknown') })),
    4,
  ).map((p) => ({ comm: p.label, count: p.count }));

  const cpu = buildSeries(
    samples.map((s) => ({ ms: s.timestamp_ms, value: s.cpu_percent ?? null })),
    cpuSustain,
  );
  const rss = buildSeries(
    samples.map((s) => ({ ms: s.timestamp_ms, value: s.rss_mb ?? null })),
    null,
  );

  return {
    cpu,
    rss,
    sampleCount: samples.length,
    processes,
  };
}

function buildSeries(
  raw: { ms: number; value: number | null }[],
  sustainThreshold: number | null,
): ResourceSeries | null {
  const points = raw
    .filter((p) => p.value != null && Number.isFinite(p.value))
    .map((p) => ({ ms: p.ms, value: p.value as number }));
  if (points.length === 0) return null;
  const values = points.map((p) => p.value);
  const max = Math.max(...values);
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  const last = values.length > 0 ? values[values.length - 1] : null;

  let sustainedTail = 0;
  if (sustainThreshold != null) {
    let run = 0;
    for (const p of points) {
      if (p.value >= sustainThreshold) {
        run += 1;
        sustainedTail = Math.max(sustainedTail, run);
      } else {
        run = 0;
      }
    }
  }

  return {
    points,
    max,
    mean,
    last,
    startMs: points[0].ms,
    endMs: points[points.length - 1].ms,
    sustainedTail,
  };
}

// ---------------------------------------------------------------------------
// Friction signals. All derived from rows the collector actually emits.
// ---------------------------------------------------------------------------

export type FrictionSeverity = 'critical' | 'warning' | 'info';

export interface FrictionSignal {
  id: string;
  severity: FrictionSeverity;
  category: string;
  title: string;
  detail?: string;
  count: number;
}

export interface FrictionResult {
  signals: FrictionSignal[];
  // Computed gaps between consecutive LLM requests, for the timing view.
  maxLlmGapMs: number;
  llmGapCount: number;
}

export function deriveFriction(snapshot: AgentSightSnapshot): FrictionResult {
  const audit = snapshot.audit_events ?? [];
  const tools = snapshot.tool_calls ?? [];
  const sessions = snapshot.sessions ?? [];
  const signals: FrictionSignal[] = [];

  // 1. Failing process exits.
  const failingExits = audit.filter(
    (e) => e.audit_type === 'process' && e.action === 'exit' && e.status === 'failure',
  );
  // 1. Failing process exits. Prefer the command over the raw exit summary so
  // the row reads "rg" rather than "exit code 1 (12ms)".
  for (const e of failingExits) {
    const cmd = commandLabel(e);
    signals.push({
      id: `fail-${e.id}`,
      severity: 'critical',
      category: 'Failing command',
      title: cmd,
      detail: e.summary || (e.comm && e.comm !== cmd ? e.comm : undefined),
      count: 1,
    });
  }

  // 2. Repeated identical commands (same full_command executed > 1).
  const execs = audit.filter((e) => e.audit_type === 'process' && e.action === 'exec');
  const cmdGroups = new Map<string, number>();
  for (const e of execs) {
    const key = commandLabel(e);
    cmdGroups.set(key, (cmdGroups.get(key) ?? 0) + 1);
  }
  for (const [cmd, count] of Array.from(cmdGroups.entries()).sort((a, b) => b[1] - a[1])) {
    if (count >= 2) {
      signals.push({
        id: `repeat-cmd-${cmd}`,
        severity: count >= 4 ? 'warning' : 'info',
        category: 'Repeated command',
        title: cmd,
        count,
      });
    }
  }

  // 3. Repeated identical tool calls (same tool name + serialized input).
  const toolGroups = new Map<string, { name: string; count: number }>();
  for (const t of tools) {
    const name = t.tool_name ?? 'tool';
    const inputKey = stableKey(t.input);
    const key = `${name}::${inputKey}`;
    const entry = toolGroups.get(key) ?? { name, count: 0 };
    entry.count += 1;
    toolGroups.set(key, entry);
  }
  for (const [, v] of Array.from(toolGroups.entries()).sort((a, b) => b[1].count - a[1].count)) {
    if (v.count >= 2) {
      signals.push({
        id: `repeat-tool-${v.name}-${v.count}`,
        severity: v.count >= 4 ? 'warning' : 'info',
        category: 'Repeated tool call',
        title: v.name,
        count: v.count,
      });
    }
  }

  // 4. Long gaps between consecutive LLM requests (a stuck / waiting session).
  const llmReqs = audit
    .filter((e) => e.audit_type === 'llm' && e.action === 'request')
    .map((e) => e.timestamp_ms)
    .filter((t) => Number.isFinite(t))
    .sort((a, b) => a - b);
  let maxGap = 0;
  let gapCount = 0;
  const gapThreshold = 5000;
  for (let i = 1; i < llmReqs.length; i += 1) {
    const gap = llmReqs[i] - llmReqs[i - 1];
    if (gap > maxGap) maxGap = gap;
    if (gap >= gapThreshold) gapCount += 1;
  }
  if (llmReqs.length >= 2) {
    if (gapCount > 0) {
      signals.push({
        id: 'llm-gap',
        severity: maxGap >= 15000 ? 'warning' : 'info',
        category: 'Think-time gap',
        title: `${gapCount} gap${gapCount > 1 ? 's' : ''} between model calls ≥ 5s`,
        detail: `Longest gap ${formatDurationMs(maxGap)}`,
        count: gapCount,
      });
    }
    // Always expose the max gap timing to the panel, even when not flagged.
  }

  // 5. Abnormal session end. "observed" is the default non-terminal state for
  // eBPF-captured sessions and carries no signal, so we deliberately ignore it
  // and only flag genuinely terminal/anomalous states (or a broken clock).
  const ABNORMAL_STATUS = ['failed', 'error', 'aborted', 'crashed', 'cancelled', 'canceled'];
  for (const s of sessions) {
    const status = (s.status ?? '').toLowerCase();
    const start = num(s.start_timestamp_ms);
    const end = num(s.end_timestamp_ms);
    if (status && ABNORMAL_STATUS.includes(status)) {
      signals.push({
        id: `session-status-${s.id}`,
        severity: 'critical',
        category: 'Session end',
        title: `Session status: ${status}`,
        detail: s.agent_type || undefined,
        count: 1,
      });
    } else if (end > 0 && start > 0 && end < start) {
      signals.push({
        id: `session-clock-${s.id}`,
        severity: 'warning',
        category: 'Session clock',
        title: 'Session end precedes start',
        count: 1,
      });
    }
  }

  // De-duplicate by id and rank by severity then count.
  const seen = new Set<string>();
  const order: Record<FrictionSeverity, number> = { critical: 0, warning: 1, info: 2 };
  const unique = signals
    .filter((s) => (seen.has(s.id) ? false : (seen.add(s.id), true)))
    .sort((a, b) => {
      if (order[a.severity] !== order[b.severity]) return order[a.severity] - order[b.severity];
      return b.count - a.count;
    });

  return { signals: unique, maxLlmGapMs: maxGap, llmGapCount: gapCount };
}

function stableKey(value: unknown): string {
  if (value == null) return '';
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

// ---------------------------------------------------------------------------
// Sessions list (informational). The merged snapshot cannot be reliably sliced
// per-session because process/file audit rows carry no session_id, so this is a
// context list, not a filter. Honest about that limitation in the panel copy.
// ---------------------------------------------------------------------------

export interface SessionSummary {
  id: string;
  agentType: string;
  model: string | null;
  status: string;
  totalTokens: number;
  startMs: number;
  durationMs: number;
  cwd: string | null;
}

export function deriveSessions(snapshot: AgentSightSnapshot): SessionSummary[] {
  const sessions = snapshot.sessions ?? [];
  return sessions.map((s) => ({
    id: s.id,
    agentType: s.agent_type,
    model: s.model ?? null,
    status: s.status ?? 'unknown',
    totalTokens: num(s.total_tokens),
    startMs: num(s.start_timestamp_ms),
    durationMs:
      s.end_timestamp_ms != null && (s.end_timestamp_ms as number) > s.start_timestamp_ms
        ? (s.end_timestamp_ms as number) - s.start_timestamp_ms
        : 0,
    cwd: sessionCwd(s),
  }));
}
