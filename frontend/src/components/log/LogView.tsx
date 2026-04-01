// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useState, useMemo } from 'react';
import { Event, ProcessedEvent } from '@/types/event';
import { processEvents, filterEvents } from '@/utils/eventProcessing';
import { EventFilters } from '@/components/common/EventFilters';
import { EventModal } from '@/components/common/EventModal';
import { LogList } from './LogList';
import { useTranslation } from '@/i18n';

interface LogViewProps {
  events: Event[];
}

export function LogView({ events }: LogViewProps) {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedComm, setSelectedComm] = useState<string>('');
  const [selectedPid, setSelectedPid] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<ProcessedEvent | null>(null);

  // Process events with additional metadata
  const processedEvents = useMemo(() => processEvents(events), [events]);

  // Filter events based on search, source, comm, and pid
  const filteredEvents = useMemo(() => {
    return filterEvents(processedEvents, {
      source: selectedSource,
      comm: selectedComm,
      pid: selectedPid,
      searchTerm
    });
  }, [processedEvents, searchTerm, selectedSource, selectedComm, selectedPid]);

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Filters */}
      <div className="border-b border-gray-200 p-4">
        <EventFilters
          events={processedEvents}
          selectedSource={selectedSource}
          selectedComm={selectedComm}
          selectedPid={selectedPid}
          searchTerm={searchTerm}
          onSourceChange={setSelectedSource}
          onCommChange={setSelectedComm}
          onPidChange={setSelectedPid}
          onSearchChange={setSearchTerm}
          showSearch={true}
        />
      </div>

      {/* Events List */}
      <div className="max-h-96 overflow-y-auto">
        <LogList
          events={filteredEvents}
          onEventClick={setSelectedEvent}
        />
      </div>

      {/* Event Details Modal */}
      <EventModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={t('log.eventDetails')}
      />
    </div>
  );
}