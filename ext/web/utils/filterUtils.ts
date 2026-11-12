// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import {
  ProcessNode,
  TreeAuditEvent,
  eventModel,
  eventSearchText,
  eventTarget,
  timelineForProcess,
  treeEventType,
} from './eventParsers';
import { ProcessTreeFilters } from '@/components/process-tree/ProcessTreeFilters';

export function extractFilterOptions(processTree: ProcessNode[]) {
  const eventTypes = new Set<string>();
  const models = new Set<string>();
  const sources = new Set<string>();
  const commands = new Set<string>();

  visitProcesses(processTree, process => {
    if (process.comm) commands.add(process.comm);
    process.events.forEach(event => {
      eventTypes.add(treeEventType(event));
      sources.add(event.audit_type);
      const model = eventModel(event);
      if (model && model !== 'Unknown Model') models.add(model);
    });
  });

  return {
    eventTypes: Array.from(eventTypes).sort(),
    models: Array.from(models).sort(),
    sources: Array.from(sources).sort(),
    commands: Array.from(commands).sort(),
  };
}

export function filterProcessTree(processTree: ProcessNode[], filters: ProcessTreeFilters): ProcessNode[] {
  return processTree.flatMap(process => {
    const events = process.events.filter(event => eventMatches(event, process.comm, filters));
    const children = filterProcessTree(process.children, filters);
    if (events.length === 0 && children.length === 0) return [];
    const filtered = { ...process, events, children };
    return [{ ...filtered, timeline: timelineForProcess(filtered) }];
  });
}

export function getTotalEventCount(processTree: ProcessNode[]): number {
  let count = 0;
  visitProcesses(processTree, process => {
    count += process.events.length;
  });
  return count;
}

export function createDefaultFilters(): ProcessTreeFilters {
  return {
    eventTypes: [],
    models: [],
    sources: [],
    commands: [],
    searchText: '',
    timeRange: {},
  };
}

function eventMatches(event: TreeAuditEvent, comm: string, filters: ProcessTreeFilters): boolean {
  const type = treeEventType(event);
  const model = eventModel(event);
  const searchText = filters.searchText.toLowerCase();
  if (filters.eventTypes.length > 0 && !filters.eventTypes.includes(type)) return false;
  if (filters.sources.length > 0 && !filters.sources.includes(event.audit_type)) return false;
  if (filters.commands.length > 0 && (!comm || !filters.commands.includes(comm))) return false;
  if (filters.models.length > 0 && (!model || !filters.models.includes(model))) return false;
  if (filters.timeRange.start && event.timestamp_ms < filters.timeRange.start) return false;
  if (filters.timeRange.end && event.timestamp_ms > filters.timeRange.end) return false;
  if (searchText && ![
    comm,
    eventModel(event),
    eventTarget(event),
    eventSearchText(event),
  ].filter(Boolean).join(' ').toLowerCase().includes(searchText)) return false;
  return true;
}

function visitProcesses(processes: ProcessNode[], visit: (process: ProcessNode) => void) {
  processes.forEach(process => {
    visit(process);
    visitProcesses(process.children, visit);
  });
}
