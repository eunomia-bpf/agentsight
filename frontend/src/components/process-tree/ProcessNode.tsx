'use client';

import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon, CpuChipIcon } from '@heroicons/react/24/outline';
import { ProcessNode as ProcessNodeType, ParsedEvent, TimelineItem } from '@/utils/eventParsers';
import { UnifiedBlock } from './UnifiedBlock';
import { adaptEventToUnifiedBlock } from './BlockAdapters';

interface ProcessNodeProps {
  process: ProcessNodeType;
  depth: number;
  expandedProcesses: Set<number>;
  expandedEvents: Set<string>;
  onToggleProcess: (pid: number) => void;
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
  const isExpanded = expandedProcesses.has(process.pid);
  const hasChildren = process.children.length > 0;
  const hasEvents = process.events.length > 0;
  const indent = depth * 24;

  // Count events by type
  const eventCounts = process.events.reduce((counts, event) => {
    counts[event.type] = (counts[event.type] || 0) + 1;
    return counts;
  }, {} as Record<string, number>);

  // Get event badges
  const getEventBadges = () => {
    const badges = [];
    if (eventCounts.prompt) {
      badges.push(
        <span key="prompt" className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-semibold">
          {eventCounts.prompt} prompt{eventCounts.prompt !== 1 ? 's' : ''}
        </span>
      );
    }
    if (eventCounts.response) {
      badges.push(
        <span key="response" className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-semibold">
          {eventCounts.response} response{eventCounts.response !== 1 ? 's' : ''}
        </span>
      );
    }
    if (eventCounts.ssl) {
      badges.push(
        <span key="ssl" className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
          {eventCounts.ssl} SSL
        </span>
      );
    }
    if (eventCounts.file) {
      badges.push(
        <span key="file" className="px-2 py-1 bg-cyan-100 text-cyan-800 text-xs rounded-full">
          {eventCounts.file} file{eventCounts.file !== 1 ? 's' : ''}
        </span>
      );
    }
    if (eventCounts.process) {
      badges.push(
        <span key="process" className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
          {eventCounts.process} process
        </span>
      );
    }
    return badges;
  };

  const renderEvent = (event: ParsedEvent) => {
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

  const renderTimelineItem = (item: TimelineItem, index: number) => {
    if (item.type === 'event' && item.event) {
      return renderEvent(item.event);
    } else if (item.type === 'process' && item.process) {
      return (
        <ProcessNode
          key={item.process.pid}
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
    <div className="select-none">
      {/* Process Header */}
      <div
        className="flex items-center py-3 px-4 hover:bg-gray-50 cursor-pointer border-l-2 border-indigo-200 rounded-r-lg transition-colors"
        style={{ marginLeft: `${indent}px` }}
        onClick={() => onToggleProcess(process.pid)}
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
            
            {/* Event badges */}
            <div className="flex items-center space-x-2 flex-wrap">
              {getEventBadges()}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded Content - Timeline View */}
      {isExpanded && (
        <div style={{ marginLeft: `${indent + 32}px` }} className="mt-1 mb-2">
          {process.timeline.length > 0 && (
            <div className="space-y-1">
              {process.timeline.map((item, index) => renderTimelineItem(item, index))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}