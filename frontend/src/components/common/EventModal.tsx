// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { ProcessedEvent } from '@/types/event';
import { decodeStdioMessage, formatStdioExpandedContent, isStdioSource } from '@/utils/stdioParser';
import { useTranslation } from '@/i18n';

interface EventModalProps {
  event: ProcessedEvent | null;
  onClose: () => void;
  title?: string;
}

export function EventModal({ event, onClose, title }: EventModalProps) {
  const { t } = useTranslation();

  if (!event) return null;

  const decodedStdio = isStdioSource(event.source) ? decodeStdioMessage(event.data) : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              {title || t('modal.eventDetails')}
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
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.id')}</label>
                <div className="text-sm text-gray-900 font-mono">{event.id}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.source')}</label>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${event.sourceColorClass}`}>
                  {event.source}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.process')}</label>
                <div className="text-sm text-gray-900">{event.comm}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.pid')}</label>
                <div className="text-sm text-gray-900 font-mono">{event.pid}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.time')}</label>
                <div className="text-sm text-gray-900">{event.formattedTime}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.timestamp')}</label>
                <div className="text-sm text-gray-900">{event.datetime.toLocaleString()}</div>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.unixTimestamp')}</label>
                <div className="text-sm text-gray-900 font-mono">{event.timestamp}</div>
              </div>
            </div>

            {decodedStdio && (
              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-2">{t('modal.decodedStdio')}</h3>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.direction')}</label>
                    <div className="text-sm text-gray-900">{decodedStdio.direction || 'UNKNOWN'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.fdRole')}</label>
                    <div className="text-sm text-gray-900">{decodedStdio.fdRole}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.kind')}</label>
                    <div className="text-sm text-gray-900">{decodedStdio.kind}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.messageId')}</label>
                    <div className="text-sm text-gray-900 font-mono">{decodedStdio.id || 'n/a'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.method')}</label>
                    <div className="text-sm text-gray-900">{decodedStdio.method || 'n/a'}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t('modal.tool')}</label>
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
              <h3 className="font-medium text-gray-900 mb-2">{t('modal.rawData')}</h3>
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
