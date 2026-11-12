// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useState, useMemo } from 'react';
import { AgentSightSnapshot } from '@/types/event';
import { buildProcessTree, ProcessNode as ProcessNodeType } from '@/utils/eventParsers';
import { ProcessNode } from './process-tree/ProcessNode';
import { ProcessTreeFiltersComponent, ProcessTreeFilters } from './process-tree/ProcessTreeFilters';
import {
  extractFilterOptions,
  filterProcessTree,
  getTotalEventCount,
  createDefaultFilters
} from '@/utils/filterUtils';
import { useTranslation } from '@/i18n';

interface ProcessTreeViewProps {
  snapshot: AgentSightSnapshot | null;
}

export function ProcessTreeView({ snapshot }: ProcessTreeViewProps) {
  const { t } = useTranslation();
  const [expandedProcesses, setExpandedProcesses] = useState<Set<string>>(new Set());
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<ProcessTreeFilters>(createDefaultFilters());

  const processTree = useMemo(() => {
    return buildProcessTree(snapshot);
  }, [snapshot]);

  const filterOptions = useMemo(() => {
    return extractFilterOptions(processTree);
  }, [processTree]);

  const filteredProcessTree = useMemo(() => {
    return filterProcessTree(processTree, filters);
  }, [processTree, filters]);

  const totalEvents = useMemo(() => getTotalEventCount(processTree), [processTree]);
  const filteredEvents = useMemo(() => getTotalEventCount(filteredProcessTree), [filteredProcessTree]);

  const toggleProcessExpansion = (id: string) => {
    const newExpanded = new Set(expandedProcesses);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedProcesses(newExpanded);
  };

  const toggleEventExpansion = (eventId: string) => {
    const newExpanded = new Set(expandedEvents);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedEvents(newExpanded);
  };


  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="border-b border-gray-200 p-4">
        <h2 className="text-lg font-semibold text-gray-900">{t('processTree.title')}</h2>
        <p className="text-sm text-gray-600 mt-1">
          {t('processTree.subtitle')}
        </p>
      </div>

      {/* Filters */}
      <ProcessTreeFiltersComponent
        filters={filters}
        onFiltersChange={setFilters}
        availableOptions={filterOptions}
        totalEvents={totalEvents}
        filteredEvents={filteredEvents}
      />

      <div className="p-4">
        {filteredProcessTree.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {totalEvents === 0 ? (
              t('processTree.noProcesses')
            ) : (
              t('processTree.noMatch')
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredProcessTree.map(process => (
              <ProcessNode
                key={process.id}
                process={process}
                depth={0}
                expandedProcesses={expandedProcesses}
                expandedEvents={expandedEvents}
                onToggleProcess={toggleProcessExpansion}
                onToggleEvent={toggleEventExpansion}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
