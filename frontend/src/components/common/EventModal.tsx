// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { ProcessedEvent } from '@/types/event';
import { decodeStdioMessage, formatStdioExpandedContent, isStdioSource } from '@/utils/stdioParser';

interface EventModalProps {
  event: ProcessedEvent | null;
  onClose: () => void;
  title?: string;
}

export function EventModal({ event, onClose, title = 'Event Details' }: EventModalProps) {
  if (!event) return null;

  const decodedStdio = isStdioSource(event.source) ? decodeStdioMessage(event.data) : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ID</label>
                <div className="text-sm text-gray-900 font-mono">{event.id}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${event.sourceColorClass}`}>
                  {event.source}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Process</label>
                <div className="text-sm text-gray-900">{event.comm}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">PID</label>
                <div className="text-sm text-gray-900 font-mono">{event.pid}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                <div className="text-sm text-gray-900">{event.formattedTime}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timestamp</label>
                <div className="text-sm text-gray-900">{event.datetime.toLocaleString()}</div>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Unix Timestamp</label>
                <div className="text-sm text-gray-900 font-mono">{event.timestamp}</div>
              </div>
            </div>

            {decodedStdio && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-2">Decoded Stdio</h3>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Direction</label>
                    <div className="text-sm text-gray-900">{decodedStdio.direction || 'UNKNOWN'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">FD Role</label>
                    <div className="text-sm text-gray-900">{decodedStdio.fdRole}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Kind</label>
                    <div className="text-sm text-gray-900">{decodedStdio.kind}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Message ID</label>
                    <div className="text-sm text-gray-900 font-mono">{decodedStdio.id || 'n/a'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                    <div className="text-sm text-gray-900">{decodedStdio.method || 'n/a'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tool</label>
                    <div className="text-sm text-gray-900">{decodedStdio.toolName || 'n/a'}</div>
                  </div>
                </div>
                <div className="bg-indigo-50 rounded-md p-3 max-h-64 overflow-y-auto">
                  <pre className="text-sm text-gray-800 font-mono whitespace-pre-wrap">
                    {formatStdioExpandedContent(decodedStdio)}
                  </pre>
                </div>
              </div>
            )}

            {/* Raw Data */}
            <div className="border-t pt-4">
              <h3 className="font-medium text-gray-900 mb-2">Raw Data</h3>
              <div className="bg-gray-50 rounded-md p-3 max-h-64 overflow-y-auto">
                <pre className="text-sm text-gray-800 font-mono whitespace-pre-wrap">
                  {JSON.stringify(event.data, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
