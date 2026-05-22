// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import React from 'react';
import { useTranslation } from '@/i18n';

interface UploadPanelProps {
  logContent: string;
  loading: boolean;
  error: string;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onTextPaste: (content: string) => void;
  onParseLog: () => void;
}

export function UploadPanel({
  logContent,
  loading,
  error,
  onFileUpload,
  onTextPaste,
  onParseLog
}: UploadPanelProps) {
  const { t } = useTranslation();
  const sampleLogPath = 'collector/ssl.log';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        {t('upload.title')}
      </h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('upload.chooseFile')}
          </label>
          <input
            type="file"
            accept=".log,.txt,.json"
            onChange={onFileUpload}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        
        <div className="text-center text-gray-500">
          <span>{t('upload.or')}</span>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('upload.pasteContent')}
          </label>
          <textarea
            placeholder={t('upload.pastePlaceholder', { path: sampleLogPath })}
            className="w-full h-32 p-3 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            onChange={(e) => onTextPaste(e.target.value)}
            value={logContent}
          />
        </div>
      </div>

      {/* Parse Button */}
      {logContent && !loading && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={onParseLog}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {t('upload.parseLog')}
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="text-red-700 text-sm">{error}</div>
        </div>
      )}

      {loading && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">{t('upload.parsing')}</span>
        </div>
      )}
    </div>
  );
}