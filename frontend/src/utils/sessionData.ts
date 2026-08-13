// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { SessionDetail } from '@/lib/nodeClient';
import type {
  AgentSightSnapshot,
  CodingPlanStep,
  LiveOverview,
  LiveSession,
  SnapshotAuditEvent,
  SnapshotProcessNode,
  SnapshotSession,
} from '@/types/event';

type SessionAttributes = {
  session_id?: unknown;
  display_id?: unknown;
  prompt_preview?: unknown;
  cwd?: unknown;
  last_message_at?: unknown;
  plan?: unknown;
};

function attributes(session: SnapshotSession): SessionAttributes {
  return session.attributes && typeof session.attributes === 'object'
    ? session.attributes as SessionAttributes
    : {};
}

export function rawSessionId(session: SnapshotSession): string {
  const value = attributes(session).session_id;
  return typeof value === 'string' && value ? value : session.id;
}

export function displaySessionId(session: SnapshotSession): string {
  const value = attributes(session).display_id;
  return typeof value === 'string' && value ? value : rawSessionId(session);
}

export function sessionPrompt(session: SnapshotSession): string {
  const value = attributes(session).prompt_preview;
  return typeof value === 'string' ? value : '';
}

export function sessionWorkspace(session: SnapshotSession): string {
  const value = attributes(session).cwd;
  return typeof value === 'string' ? value : '';
}

export function sessionLastMessage(session: SnapshotSession): string | null {
  const value = attributes(session).last_message_at;
  return typeof value === 'string' ? value : null;
}

export function sessionPlan(
  session: SnapshotSession,
  detail?: SessionDetail | null,
  live?: LiveSession | null,
): CodingPlanStep[] {
  const source = detail?.events?.plan
    ?? (live?.plan?.length ? live.plan : attributes(session).plan);
  if (!Array.isArray(source)) return [];
  return source.filter((item): item is CodingPlanStep => (
    !!item && typeof item === 'object'
      && typeof (item as CodingPlanStep).step === 'string'
      && typeof (item as CodingPlanStep).status === 'string'
  ));
}

export function liveRowForSession(
  overview: LiveOverview | null,
  session: SnapshotSession,
): LiveSession | null {
  const rawId = rawSessionId(session);
  const displayId = displaySessionId(session);
  return overview?.rows.find((row) => (
    row.session_id === rawId || row.session === displayId || row.session === session.id
  )) ?? null;
}

export function isRunningSession(row: LiveSession | null): boolean {
  return typeof row?.pid === 'number' && row.pid > 0;
}

export type SessionActivityState = 'running' | 'recent' | 'stopped';

export function sessionActivityState(
  session: SnapshotSession,
  live: LiveSession | null,
): SessionActivityState {
  if (isRunningSession(live)) return 'running';
  const last = sessionLastMessage(session)
    ? Date.parse(sessionLastMessage(session)!)
    : (session.end_timestamp_ms ?? session.start_timestamp_ms);
  return Number.isFinite(last) && Date.now() - last < 3 * 60_000 ? 'recent' : 'stopped';
}

export function orderedSessions(
  snapshot: AgentSightSnapshot,
  overview: LiveOverview | null,
): SnapshotSession[] {
  return [...(snapshot.sessions ?? [])].sort((left, right) => {
    const live = Number(isRunningSession(liveRowForSession(overview, right)))
      - Number(isRunningSession(liveRowForSession(overview, left)));
    if (live) return live;
    return (right.end_timestamp_ms ?? right.start_timestamp_ms)
      - (left.end_timestamp_ms ?? left.start_timestamp_ms);
  });
}

function nativeEvents(
  session: SnapshotSession,
  detail: SessionDetail | null,
  pid: number,
): SnapshotAuditEvent[] {
  const events = detail?.events;
  if (!events) return [];
  const fallback = session.start_timestamp_ms;
  return [
    ...(events.prompts ?? []).map((event, index): SnapshotAuditEvent => ({
      id: `native-prompt-${index}`,
      timestamp_ms: event.ts_ms ?? fallback + index,
      audit_type: 'llm',
      action: 'request',
      pid,
      comm: session.agent_type,
      status: 'observed',
      summary: event.preview || event.text || 'User prompt',
      details: { text_content: event.text || event.preview || '', task_path: event.task_path ?? [] },
    })),
    ...(events.llm_responses ?? []).map((event, index): SnapshotAuditEvent => ({
      id: `native-response-${index}`,
      timestamp_ms: event.ts_ms ?? fallback + index,
      audit_type: 'llm',
      action: 'response',
      pid,
      comm: session.agent_type,
      subject: event.model,
      status: 'observed',
      summary: event.preview || event.text || 'Agent response',
      details: {
        text_content: event.text || event.preview || '',
        response_phase: event.response_phase,
        task_path: event.task_path ?? [],
      },
    })),
    ...(events.tools ?? []).map((event, index): SnapshotAuditEvent => ({
      id: `native-tool-${index}`,
      timestamp_ms: event.ts_ms ?? fallback + index,
      audit_type: 'system',
      action: event.effect || 'call',
      pid,
      comm: session.agent_type,
      subject: event.tool_name,
      status: event.status || 'observed',
      summary: [event.tool_name, event.command].filter(Boolean).join(' · '),
      details: {
        tool_name: event.tool_name,
        category: event.category,
        command: event.command,
        task_path: event.task_path ?? [],
      },
    })),
  ];
}

export function sessionSnapshot(
  snapshot: AgentSightSnapshot,
  session: SnapshotSession,
  live: LiveSession | null,
  detail: SessionDetail | null,
): AgentSightSnapshot {
  const liveProcesses: SnapshotProcessNode[] = (live?.process_details ?? []).map((process) => ({
    id: `live-${process.pid}`,
    pid: process.pid,
    ppid: process.ppid || null,
    root_pid: live?.pid ?? process.pid,
    start_timestamp_ms: session.start_timestamp_ms,
    end_timestamp_ms: null,
    comm: process.comm,
    command: process.command,
    cwd: process.cwd,
    status: 'running',
  }));
  const pids = new Set(liveProcesses.map((process) => process.pid));
  const capturedProcesses = (snapshot.process_nodes ?? []).filter((process) => (
    pids.has(process.pid) || (process.root_pid != null && pids.has(process.root_pid))
  ));
  const processNodes = liveProcesses.length ? liveProcesses : capturedProcesses;
  const attributedPids = new Set(processNodes.map((process) => process.pid));
  const onlySession = (snapshot.sessions ?? []).length === 1;
  const keepPid = (pid?: number | null) => onlySession || (pid != null && attributedPids.has(pid));
  const virtualPid = live?.pid ?? processNodes[0]?.pid ?? 0;
  const processTree = processNodes.length ? processNodes : [{
    id: `session-${session.id}`,
    pid: virtualPid,
    ppid: null,
    root_pid: virtualPid,
    start_timestamp_ms: session.start_timestamp_ms,
    end_timestamp_ms: session.end_timestamp_ms,
    comm: session.agent_type,
    command: displaySessionId(session),
    status: isRunningSession(live) ? 'running' : 'recorded',
  }];
  const rawId = rawSessionId(session);
  const tools = (snapshot.tool_calls ?? []).filter((tool) => (
    tool.session_id === session.id || tool.session_id === rawId
  ));

  return {
    ...snapshot,
    summary: {
      ...snapshot.summary,
      sessions: 1,
      input_tokens: session.input_tokens ?? 0,
      output_tokens: session.output_tokens ?? 0,
      total_tokens: session.total_tokens ?? 0,
      start_timestamp_ms: session.start_timestamp_ms,
      end_timestamp_ms: session.end_timestamp_ms,
    },
    token_summary: [],
    sessions: [session],
    process_nodes: processTree,
    audit_events: [
      ...(snapshot.audit_events ?? []).filter((event) => keepPid(event.pid)),
      ...nativeEvents(session, detail, virtualPid),
    ],
    resource_samples: (snapshot.resource_samples ?? []).filter((sample) => keepPid(sample.pid)),
    network_targets: (snapshot.network_targets ?? []).filter((target) => keepPid(target.pid)),
    tool_calls: detail ? [] : tools,
  };
}
