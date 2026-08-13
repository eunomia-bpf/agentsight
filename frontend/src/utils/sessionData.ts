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
  capture_fallback?: unknown;
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

export function isRecordedCaptureSession(session: SnapshotSession): boolean {
  return attributes(session).capture_fallback === true;
}

function recordedCaptureSession(snapshot: AgentSightSnapshot): SnapshotSession | null {
  const hasEvidence = (snapshot.summary?.view_events ?? 0) > 0
    || (snapshot.process_nodes?.length ?? 0) > 0
    || (snapshot.audit_events?.length ?? 0) > 0
    || (snapshot.resource_samples?.length ?? 0) > 0
    || (snapshot.network_targets?.length ?? 0) > 0
    || (snapshot.tool_calls?.length ?? 0) > 0;
  if (!hasEvidence) return null;
  const points = [
    snapshot.summary?.start_timestamp_ms,
    snapshot.summary?.end_timestamp_ms,
    ...(snapshot.audit_events ?? []).map((row) => row.timestamp_ms),
    ...(snapshot.resource_samples ?? []).map((row) => row.timestamp_ms),
    ...(snapshot.process_nodes ?? []).flatMap((row) => [row.start_timestamp_ms, row.end_timestamp_ms]),
  ].filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
  const [start, end] = points.reduce<[number, number]>(
    ([minimum, maximum], value) => [Math.min(minimum, value), Math.max(maximum, value)],
    [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY],
  );
  const boundedStart = Number.isFinite(start) ? start : 0;
  const boundedEnd = Number.isFinite(end) ? end : boundedStart;
  return {
    id: 'capture:recorded',
    agent_type: 'capture',
    start_timestamp_ms: boundedStart,
    end_timestamp_ms: boundedEnd,
    status: 'recorded',
    input_tokens: snapshot.summary?.input_tokens ?? 0,
    output_tokens: snapshot.summary?.output_tokens ?? 0,
    total_tokens: snapshot.summary?.total_tokens ?? 0,
    attributes: {
      session_id: 'capture:recorded',
      display_id: 'Recorded capture',
      prompt_preview: 'Recorded AgentSight capture',
      capture_fallback: true,
    },
  };
}

export function snapshotSessions(
  snapshot: AgentSightSnapshot,
  includeRecordedCapture = false,
): SnapshotSession[] {
  const sessions = snapshot.sessions ?? [];
  const capture = recordedCaptureSession(snapshot);
  if (!sessions.length) return capture ? [capture] : [];
  return includeRecordedCapture && capture ? [...sessions, capture] : sessions;
}

export function recordedSessionDetail(
  snapshot: AgentSightSnapshot,
  session: SnapshotSession,
): SessionDetail {
  const detailText = (event: SnapshotAuditEvent) => {
    if (event.details && typeof event.details === 'object') {
      const text = (event.details as { text_content?: unknown }).text_content;
      if (typeof text === 'string' && text) return text;
    }
    return event.summary || '';
  };
  const llm = (snapshot.audit_events ?? []).filter((event) => event.audit_type === 'llm');
  return {
    session_id: rawSessionId(session),
    agent_type: session.agent_type,
    events: {
      prompts: llm.filter((event) => event.action === 'request').map((event) => ({
        ts_ms: event.timestamp_ms, text: detailText(event), preview: event.summary || '',
      })),
      llm_responses: llm.filter((event) => event.action === 'response').map((event) => ({
        ts_ms: event.timestamp_ms, text: detailText(event), preview: event.summary || '',
      })),
    },
  };
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
  return [...snapshotSessions(snapshot, overview === null)].sort((left, right) => {
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
  if (isRecordedCaptureSession(session)) {
    return { ...snapshot, sessions: [session] };
  }
  const sessionStart = session.start_timestamp_ms;
  const parsedLast = sessionLastMessage(session) ? Date.parse(sessionLastMessage(session)!) : NaN;
  const sessionEnd = isRunningSession(live)
    ? Date.now()
    : (session.end_timestamp_ms ?? (Number.isFinite(parsedLast) ? parsedLast : sessionStart));
  const atSessionTime = (timestamp?: number | null) => (
    timestamp != null && timestamp >= sessionStart && timestamp <= sessionEnd
  );
  const processContains = (process: SnapshotProcessNode, timestamp: number) => (
    timestamp >= Math.max(sessionStart, process.start_timestamp_ms ?? sessionStart)
      && timestamp <= Math.min(sessionEnd, process.end_timestamp_ms ?? sessionEnd)
  );
  const processOverlaps = (
    process: SnapshotProcessNode,
    start: number,
    end: number,
  ) => (
    Math.min(sessionEnd, process.end_timestamp_ms ?? sessionEnd) >= start
      && Math.max(sessionStart, process.start_timestamp_ms ?? sessionStart) <= end
  );
  const captureRows = snapshot.process_nodes ?? [];
  const liveProcesses: SnapshotProcessNode[] = (live?.process_details ?? []).map((process) => {
    const captured = captureRows
      .filter((candidate) => candidate.pid === process.pid && candidate.end_timestamp_ms == null)
      .sort((left, right) => (
        (right.start_timestamp_ms ?? 0) - (left.start_timestamp_ms ?? 0)
      ))[0];
    return {
      ...captured,
      id: `live-${process.pid}`,
      pid: process.pid,
      ppid: process.ppid || null,
      root_pid: live?.pid ?? process.pid,
      start_timestamp_ms: captured?.start_timestamp_ms ?? session.start_timestamp_ms,
      end_timestamp_ms: null,
      comm: process.comm,
      command: process.command,
      cwd: process.cwd,
      status: 'running',
    };
  });
  const rawId = rawSessionId(session);
  const tools = (snapshot.tool_calls ?? []).filter((tool) => (
    tool.session_id === session.id || tool.session_id === rawId
  ));
  const captureRoots = tools.flatMap((tool) => {
    if (tool.related_pid == null || !atSessionTime(tool.timestamp_ms)) return [];
    const related = captureRows.filter((process) => (
      (process.pid === tool.related_pid || process.root_pid === tool.related_pid)
        && processContains(process, tool.timestamp_ms)
    ));
    return related.map((process) => {
      const rootPid = process.root_pid ?? process.pid;
      const root = captureRows.find((candidate) => (
        candidate.pid === rootPid && processContains(candidate, tool.timestamp_ms)
      )) ?? process;
      return {
        pid: rootPid,
        start: Math.max(sessionStart, root.start_timestamp_ms ?? sessionStart),
        end: Math.min(sessionEnd, root.end_timestamp_ms ?? sessionEnd),
      };
    });
  });
  const capturedProcesses = captureRows.filter((process) => captureRoots.some((root) => (
    (process.pid === root.pid || process.root_pid === root.pid)
      && processOverlaps(process, root.start, root.end)
  )));
  const processNodes = liveProcesses.length ? [
    ...liveProcesses,
    ...capturedProcesses.filter((captured) => {
      const currentRoot = liveProcesses.find((liveProcess) => (
        (captured.root_pid ?? captured.pid) === liveProcess.pid
      ));
      if (!currentRoot || (captured.start_timestamp_ms ?? sessionStart)
        < (currentRoot.start_timestamp_ms ?? sessionStart)) return false;
      return !(captured.pid === currentRoot.pid
        && captured.end_timestamp_ms == null
        && captured.start_timestamp_ms === currentRoot.start_timestamp_ms);
    }),
  ] : capturedProcesses;
  const keepPidAt = (pid: number | null | undefined, timestamp: number) => (
    pid != null && processNodes.some((process) => (
      process.pid === pid && processContains(process, timestamp)
    ))
  );
  const keepPidRange = (
    pid?: number | null,
    first?: number | null,
    last?: number | null,
  ) => {
    if (pid == null || (first == null && last == null)) return false;
    const start = first ?? last!;
    const end = last ?? first!;
    if (!atSessionTime(start) || !atSessionTime(end)) return false;
    return processNodes.some((process) => (
      process.pid === pid && processContains(process, start) && processContains(process, end)
    ));
  };
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
      ...(snapshot.audit_events ?? []).filter((event) => (
        keepPidAt(event.pid, event.timestamp_ms)
      )),
      ...nativeEvents(session, detail, virtualPid),
    ],
    resource_samples: (snapshot.resource_samples ?? []).filter((sample) => (
      keepPidAt(sample.pid, sample.timestamp_ms)
    )),
    network_targets: (snapshot.network_targets ?? []).filter((target) => (
      keepPidRange(target.pid, target.first_timestamp_ms, target.last_timestamp_ms)
    )),
    tool_calls: detail?.events?.tools?.length ? [] : tools,
  };
}
