// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  AgentSightSnapshot,
  SnapshotAuditEvent,
  SnapshotNetworkTarget,
  SnapshotProcessNode,
  SnapshotResourceSample,
  SnapshotSession,
  SnapshotToolCall,
} from '@/types/event';
import { decodeStdioMessage, isStdioSource } from './stdioParser';

export interface DisplayEvent {
  id: string;
  timestamp: number;
  source: string;
  pid: number;
  comm: string;
  data: unknown;
  datetime: Date;
  formattedTime: string;
  sourceColor: string;
  sourceColorClass: string;
  summary: string;
}

interface RawDisplayEvent {
  id: string;
  timestamp: number;
  source: string;
  pid: number;
  comm: string;
  data: unknown;
  summary?: string;
}

const SOURCE_COLORS = [
  '#3B82F6',
  '#10B981',
  '#F59E0B',
  '#8B5CF6',
  '#EF4444',
  '#6366F1',
  '#EC4899',
  '#6B7280',
];

const SOURCE_COLOR_CLASSES = [
  'bg-blue-100 text-blue-800',
  'bg-green-100 text-green-800',
  'bg-yellow-100 text-yellow-800',
  'bg-purple-100 text-purple-800',
  'bg-red-100 text-red-800',
  'bg-indigo-100 text-indigo-800',
  'bg-pink-100 text-pink-800',
  'bg-gray-100 text-gray-800',
];

export function displayEventsFromSnapshot(snapshot: AgentSightSnapshot | null): DisplayEvent[] {
  if (!snapshot) return [];
  return decorateEvents([
    ...(snapshot.audit_events ?? []).map(auditEvent),
    ...(snapshot.process_nodes ?? []).map(processEvent),
    ...(snapshot.network_targets ?? []).map(networkEvent),
    ...(snapshot.resource_samples ?? []).map(resourceEvent),
    ...(snapshot.sessions ?? []).map(sessionEvent),
    ...(snapshot.tool_calls ?? []).map(toolEvent),
  ].sort((a, b) => a.timestamp - b.timestamp));
}

export function auditEventName(row: SnapshotAuditEvent): string {
  if (row.audit_type === 'process') {
    if (row.action === 'exec') return 'EXEC';
    if (row.action === 'exit') return 'EXIT';
    return (row.action ?? 'PROCESS').toUpperCase();
  }
  if (row.audit_type === 'file') return 'FILE_WRITE';
  if (row.audit_type === 'llm') return 'LLM_CALL';
  return row.audit_type.toUpperCase();
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  if (ms < 86400000) return `${(ms / 3600000).toFixed(1)}h`;
  return `${(ms / 86400000).toFixed(1)}d`;
}

export function formatDisplayEventSummary(event: DisplayEvent): string {
  if (isStdioSource(event.source)) {
    const decoded = decodeStdioMessage(event.data);
    return `${event.comm} (${event.pid}) · ${decoded.summary}`;
  }
  return event.summary || `${event.comm} (${event.pid})`;
}

export function filterDisplayEvents(
  events: DisplayEvent[],
  filters: { source?: string; comm?: string; pid?: string; searchTerm?: string },
): DisplayEvent[] {
  const term = filters.searchTerm?.toLowerCase();
  return events.filter(event => {
    if (filters.source && event.source !== filters.source) return false;
    if (filters.comm && event.comm !== filters.comm) return false;
    if (filters.pid && event.pid.toString() !== filters.pid) return false;
    if (!term) return true;
    return [
      event.source,
      event.id,
      event.comm,
      String(event.pid),
      event.summary,
      JSON.stringify(event.data),
    ].join(' ').toLowerCase().includes(term);
  });
}

function decorateEvents(events: RawDisplayEvent[]): DisplayEvent[] {
  const colorBySource = new Map<string, string>();
  const classBySource = new Map<string, string>();
  let colorIndex = 0;

  return events.map(event => {
    if (!colorBySource.has(event.source)) {
      colorBySource.set(event.source, SOURCE_COLORS[colorIndex % SOURCE_COLORS.length]);
      classBySource.set(event.source, SOURCE_COLOR_CLASSES[colorIndex % SOURCE_COLOR_CLASSES.length]);
      colorIndex++;
    }
    const datetime = new Date(event.timestamp);
    return {
      ...event,
      datetime,
      formattedTime: `${datetime.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })}.${datetime.getMilliseconds().toString().padStart(3, '0')}`,
      sourceColor: colorBySource.get(event.source) || SOURCE_COLORS[0],
      sourceColorClass: classBySource.get(event.source) || SOURCE_COLOR_CLASSES[0],
      summary: event.summary || `${event.comm} (${event.pid})`,
    };
  });
}

function auditEvent(row: SnapshotAuditEvent): RawDisplayEvent {
  const details = isRecord(row.details) ? row.details : {};
  const target = row.target ?? stringValue(details.path) ?? stringValue(details.filepath);
  return {
    id: row.id,
    timestamp: row.timestamp_ms,
    source: row.audit_type,
    pid: row.pid ?? 0,
    comm: row.comm ?? row.subject ?? '',
    summary: row.summary || [row.action, target].filter(Boolean).join(' '),
    data: {
      ...details,
      event: auditEventName(row),
      audit_type: row.audit_type,
      action: row.action,
      target,
      status: row.status,
      subject: row.subject,
      filename: row.audit_type === 'process' ? target : details.filename,
      filepath: row.audit_type === 'file' ? target : details.filepath,
      path: row.audit_type === 'file' ? target : details.path,
    },
  };
}

function processEvent(row: SnapshotProcessNode): RawDisplayEvent {
  return {
    id: `process-node-${row.id}`,
    timestamp: row.start_timestamp_ms ?? row.end_timestamp_ms ?? 0,
    source: 'process_node',
    pid: row.pid,
    comm: row.comm ?? row.command ?? '',
    summary: row.command ?? row.comm ?? `process ${row.pid}`,
    data: row,
  };
}

function networkEvent(row: SnapshotNetworkTarget, index: number): RawDisplayEvent {
  const target = `${row.host}${row.path ?? ''}`;
  return {
    id: `network-${row.pid ?? 0}-${row.host}-${row.path ?? ''}-${index}`,
    timestamp: row.last_timestamp_ms ?? row.first_timestamp_ms ?? 0,
    source: 'network',
    pid: row.pid ?? 0,
    comm: row.comm ?? '',
    summary: `${target} (${row.count ?? 0})`,
    data: { ...row, event: 'NETWORK_TARGET' },
  };
}

function resourceEvent(row: SnapshotResourceSample, index: number): RawDisplayEvent {
  return {
    id: `resource-${row.pid ?? 0}-${row.timestamp_ms}-${index}`,
    timestamp: row.timestamp_ms,
    source: 'system',
    pid: row.pid ?? 0,
    comm: row.comm ?? '',
    summary: `cpu ${row.cpu_percent ?? 0}% rss ${row.rss_mb ?? 0}MB`,
    data: {
      event: 'RESOURCE_SAMPLE',
      cpu: { percent: row.cpu_percent ?? 0 },
      memory: { rss_mb: row.rss_mb ?? 0 },
    },
  };
}

function sessionEvent(row: SnapshotSession): RawDisplayEvent {
  return {
    id: `session-${row.id}`,
    timestamp: row.end_timestamp_ms ?? row.start_timestamp_ms,
    source: 'session',
    pid: 0,
    comm: row.agent_type,
    summary: `${row.agent_type} ${row.status ?? ''}`.trim(),
    data: { ...(isRecord(row.attributes) ? row.attributes : {}), event: 'SESSION', ...row },
  };
}

function toolEvent(row: SnapshotToolCall): RawDisplayEvent {
  return {
    id: `tool-${row.id}`,
    timestamp: row.timestamp_ms,
    source: 'tool',
    pid: row.related_pid ?? 0,
    comm: row.tool_name ?? 'tool',
    summary: `${row.tool_name ?? 'tool'} ${row.status ?? ''}`.trim(),
    data: { event: 'TOOL_CALL', ...row },
  };
}

function stringValue(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, any> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
