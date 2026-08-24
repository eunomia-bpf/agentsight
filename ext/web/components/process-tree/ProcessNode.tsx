// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { ChevronDownIcon, ChevronRightIcon, CpuChipIcon } from '@heroicons/react/24/outline';
import { ProcessNode as ProcessNodeType, TimelineItem, TreeAuditEvent, treeEventType } from '@/utils/eventParsers';
import { UnifiedBlock } from './UnifiedBlock';
import { adaptEventToUnifiedBlock } from './BlockAdapters';
import { useTranslation } from '@/i18n';

interface ProcessNodeProps {
  process: ProcessNodeType;
  depth: number;
  expandedProcesses: Set<string>;
  expandedEvents: Set<string>;
  onToggleProcess: (id: string) => void;
  onToggleEvent: (eventId: string) => void;
}

export function ProcessNode({
  process,
  depth,
  expandedProcesses,
  expandedEvents,
  onToggleProcess,
  onToggleEvent
}: ProcessNodeProps) {
  const { t } = useTranslation();
  const isExpanded = expandedProcesses.has(process.id);
  const hasChildren = process.children.length > 0;
  const hasEvents = process.events.length > 0;
  const indent = depth * 24;

  const eventCounts = process.events.reduce((counts, event) => {
    const type = treeEventType(event);
    counts[type] = (counts[type] || 0) + 1;
    return counts;
  }, {} as Record<string, number>);

  const getEventBadges = () => {
    return [
      ['prompt', 'bg-blue-100 text-blue-800 font-semibold', (count: number) => t(count === 1 ? 'badge.prompt_one' : 'badge.prompt_other', { count })],
      ['response', 'bg-green-100 text-green-800 font-semibold', (count: number) => t(count === 1 ? 'badge.response_one' : 'badge.response_other', { count })],
      ['ssl', 'bg-orange-100 text-orange-800', (count: number) => t('badge.ssl', { count })],
      ['file', 'bg-cyan-100 text-cyan-800', (count: number) => t(count === 1 ? 'badge.file_one' : 'badge.file_other', { count })],
      ['process', 'bg-purple-100 text-purple-800', (count: number) => t('badge.process', { count })],
      ['stdio', 'bg-indigo-100 text-indigo-800', (count: number) => t('badge.stdio', { count })],
    ].flatMap(([type, className, label]) => {
      const count = eventCounts[type as string];
      return count ? [(
        <span key={type as string} className={`px-2 py-1 text-xs rounded-full ${className}`}>
          {(label as (count: number) => string)(count)}
        </span>
      )] : [];
    });
  };

  const renderEvent = (event: TreeAuditEvent) => {
    const isEventExpanded = expandedEvents.has(event.id);
    const unifiedBlockData = adaptEventToUnifiedBlock(event);
    
    return (
      <UnifiedBlock
        key={event.id}
        data={unifiedBlockData}
        isExpanded={isEventExpanded}
        onToggle={() => onToggleEvent(event.id)}
      />
    );
  };

  const renderTimelineItem = (item: TimelineItem) => {
    if (item.type === 'event' && item.event) {
      return renderEvent(item.event);
    } else if (item.type === 'process' && item.process) {
      return (
        <ProcessNode
          key={item.process.id}
          process={item.process}
          depth={depth + 1}
          expandedProcesses={expandedProcesses}
          expandedEvents={expandedEvents}
          onToggleProcess={onToggleProcess}
          onToggleEvent={onToggleEvent}
        />
      );
    }
    return null;
  };

  return (
    <div>
      <div
        className="select-none flex items-center py-3 px-4 hover:bg-gray-50 cursor-pointer border-l-2 border-indigo-200 rounded-r-lg transition-colors"
        style={{ marginLeft: `${indent}px` }}
        onClick={() => onToggleProcess(process.id)}
      >
        <div className="flex items-center flex-1">
          {hasChildren || hasEvents ? (
            isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 text-gray-500 mr-3 flex-shrink-0" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-gray-500 mr-3 flex-shrink-0" />
            )
          ) : (
            <div className="w-7 mr-3" />
          )}
          
          <div className="flex items-center space-x-3 flex-1">
            <CpuChipIcon className="h-5 w-5 text-indigo-600 flex-shrink-0" />
            
            <div className="flex items-center space-x-2 min-w-0">
              <span className="text-sm text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                PID {process.pid}
              </span>
              <span className="font-semibold text-gray-900 text-lg">
                [{process.comm}]
              </span>
              {process.ppid && (
                <span className="text-xs text-gray-400">
                  ← {process.ppid}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2 flex-wrap">
              {getEventBadges()}
            </div>
          </div>
        </div>
      </div>

      {isExpanded && (
        <div style={{ marginLeft: `${indent + 32}px` }} className="mt-1 mb-2">
          {process.timeline.length > 0 && (
            <div className="space-y-1">
              {process.timeline.map(item => renderTimelineItem(item))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
