// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  AgentSightSnapshot,
  SnapshotAuditEvent,
  SnapshotProcessNode,
} from '@/types/event';
import { comparePrompts } from './jsonDiff';
import { auditEventName } from './eventProcessing';

export type TreeEventType = 'prompt' | 'response' | 'ssl' | 'file' | 'process' | 'stdio' | 'system';

export interface PromptDiff {
  diff: string;
  summary: string;
  hasChanges: boolean;
  previousPromptId?: string;
}

export type TreeAuditEvent = SnapshotAuditEvent & { promptDiff?: PromptDiff };

export interface ProcessNode {
  id: string;
  pid: number;
  comm: string;
  ppid?: number;
  startTimestamp?: number;
  endTimestamp?: number;
  children: ProcessNode[];
  events: TreeAuditEvent[];
  timeline: TimelineItem[];
}

export interface TimelineItem {
  type: 'event' | 'process';
  timestamp: number;
  event?: TreeAuditEvent;
  process?: ProcessNode;
}

export function buildProcessTree(snapshot: AgentSightSnapshot | null): ProcessNode[] {
  const processMap = new Map<string, ProcessNode>();
  const nodesByPid = new Map<number, ProcessNode[]>();
  const promptHistoryByProcess = new Map<string, TreeAuditEvent[]>();

  for (const row of snapshot?.process_nodes ?? []) {
    const process = processFromRow(row);
    processMap.set(process.id, process);
    nodesByPid.set(process.pid, [...(nodesByPid.get(process.pid) ?? []), process]);
  }
  nodesByPid.forEach(nodes => nodes.sort((a, b) => firstTimestamp(a) - firstTimestamp(b)));

  for (const row of [...(snapshot?.audit_events ?? [])].sort((a, b) => a.timestamp_ms - b.timestamp_ms)) {
    const process = processForAudit(row, nodesByPid);
    if (!process) continue;

    const event: TreeAuditEvent = { ...row };
    if (treeEventType(event) === 'prompt') {
      const history = promptHistoryByProcess.get(process.id) ?? [];
      const previousPrompt = history[history.length - 1];
      if (previousPrompt) {
        event.promptDiff = {
          ...comparePrompts(eventRaw(previousPrompt), eventRaw(event)),
          previousPromptId: previousPrompt.id,
        };
      }
      promptHistoryByProcess.set(process.id, [...history, event].slice(-10));
    }
    process.events.push(event);
  }

  const childProcesses = new Set<string>();
  processMap.forEach(process => {
    const parent = parentProcess(process, nodesByPid);
    if (!parent) return;
    parent.children.push(process);
    childProcesses.add(process.id);
  });

  processMap.forEach(process => {
    process.events.sort((a, b) => a.timestamp_ms - b.timestamp_ms);
    process.children.sort((a, b) => firstTimestamp(a) - firstTimestamp(b));
    process.timeline = timelineForProcess(process);
  });

  return Array.from(processMap.values())
    .filter(process => !childProcesses.has(process.id))
    .sort((a, b) => firstTimestamp(a) - firstTimestamp(b));
}

export function timelineForProcess(process: ProcessNode): TimelineItem[] {
  return [
    ...process.events.map(event => ({ type: 'event' as const, timestamp: event.timestamp_ms, event })),
    ...process.children.map(child => ({ type: 'process' as const, timestamp: firstTimestamp(child), process: child })),
  ].sort((a, b) => a.timestamp - b.timestamp);
}

export function treeEventType(row: SnapshotAuditEvent): TreeEventType {
  if (row.audit_type === 'llm') return row.action === 'request' ? 'prompt' : 'response';
  if (row.audit_type === 'file') return 'file';
  if (row.audit_type === 'process') return 'process';
  if (row.audit_type === 'stdio') return 'stdio';
  if (row.audit_type === 'system') return 'system';
  return 'ssl';
}

export function eventDetails(row: SnapshotAuditEvent): Record<string, any> {
  return isRecord(row.details) ? row.details : {};
}

export function eventModel(row: SnapshotAuditEvent): string | undefined {
  return row.subject ?? stringValue(eventDetails(row).model);
}

export function eventTarget(row: SnapshotAuditEvent): string | undefined {
  const details = eventDetails(row);
  return row.target ?? stringValue(details.path) ?? stringValue(details.filepath);
}

export function eventSearchText(row: SnapshotAuditEvent): string {
  return [
    row.id,
    row.audit_type,
    row.action,
    row.status,
    row.summary,
    row.comm,
    eventModel(row),
    eventTarget(row),
    JSON.stringify(row.details ?? row),
  ].filter(Boolean).join(' ').toLowerCase();
}

export function eventName(row: SnapshotAuditEvent): string {
  return auditEventName(row);
}

export function eventRaw(row: SnapshotAuditEvent): unknown {
  return row.details ?? row;
}

function processFromRow(row: SnapshotProcessNode): ProcessNode {
  return {
    id: row.id,
    pid: row.pid,
    comm: row.comm ?? row.command ?? 'unknown',
    ppid: row.ppid ?? undefined,
    startTimestamp: row.start_timestamp_ms ?? undefined,
    endTimestamp: row.end_timestamp_ms ?? undefined,
    children: [],
    events: [],
    timeline: [],
  };
}

function processForAudit(
  row: SnapshotAuditEvent,
  nodesByPid: Map<number, ProcessNode[]>,
): ProcessNode | undefined {
  if (typeof row.pid !== 'number') return undefined;
  return lastMatching(
    nodesByPid.get(row.pid),
    process => containsTimestamp(process, row.timestamp_ms),
  );
}

function parentProcess(
  process: ProcessNode,
  nodesByPid: Map<number, ProcessNode[]>,
): ProcessNode | undefined {
  if (!process.ppid) return undefined;
  const start = firstTimestamp(process);
  return lastMatching(
    nodesByPid.get(process.ppid),
    parent => parent.id !== process.id && containsTimestamp(parent, start),
  );
}

function containsTimestamp(process: ProcessNode, timestamp: number): boolean {
  return (process.startTimestamp ?? 0) <= timestamp
    && (process.endTimestamp === undefined || timestamp <= process.endTimestamp);
}

function lastMatching<T>(items: T[] | undefined, predicate: (item: T) => boolean): T | undefined {
  if (!items) return undefined;
  for (let i = items.length - 1; i >= 0; i--) {
    if (predicate(items[i])) return items[i];
  }
  return undefined;
}

function firstTimestamp(process: ProcessNode): number {
  const childStart = process.children.reduce(
    (earliest, child) => Math.min(earliest, firstTimestamp(child)),
    Infinity,
  );
  const eventStart = process.events[0]?.timestamp_ms ?? Infinity;
  const ownStart = process.startTimestamp ?? Infinity;
  const earliest = Math.min(ownStart, eventStart, childStart);
  return earliest === Infinity ? 0 : earliest;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, any> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
