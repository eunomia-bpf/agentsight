// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useEffect, useMemo, useState } from 'react';
import { DisplayEvent, filterDisplayEvents } from '@/utils/eventProcessing';
import { EventFilters } from '@/components/common/EventFilters';
import { EventModal } from '@/components/common/EventModal';
import { LogList } from './LogList';
import { useTranslation } from '@/i18n';

interface LogViewProps {
  events: DisplayEvent[];
  initialSearchTerm?: string;
}

export function LogView({ events, initialSearchTerm = '' }: LogViewProps) {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedComm, setSelectedComm] = useState<string>('');
  const [selectedPid, setSelectedPid] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<DisplayEvent | null>(null);

  useEffect(() => { setSearchTerm(initialSearchTerm); }, [initialSearchTerm]);

  // Filter events based on search, source, comm, and pid
  const filteredEvents = useMemo(() => {
    return filterDisplayEvents(events, {
      source: selectedSource,
      comm: selectedComm,
      pid: selectedPid,
      searchTerm
    });
  }, [events, searchTerm, selectedSource, selectedComm, selectedPid]);

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Filters */}
      <div className="border-b border-gray-200 p-4">
        <EventFilters
          events={events}
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

      {/* Event details modal */}
      <EventModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={t('log.eventDetails')}
      />
    </div>
  );
}
