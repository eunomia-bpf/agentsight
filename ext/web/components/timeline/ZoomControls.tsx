// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useTranslation } from '@/i18n';

interface ZoomControlsProps {
  zoomLevel: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  onScrollLeft?: () => void;
  onScrollRight?: () => void;
}

export function ZoomControls({
  zoomLevel,
  onZoomIn,
  onZoomOut,
  onReset,
  onScrollLeft,
  onScrollRight
}: ZoomControlsProps) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <button
          onClick={onZoomOut}
          className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          title={t('timeline.zoomOut')}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6" />
          </svg>
        </button>
        <span className="text-sm text-gray-600 font-mono min-w-[4rem] text-center">
          {Math.round(zoomLevel * 100)}%
        </span>
        <button
          onClick={onZoomIn}
          className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          title={t('timeline.zoomIn')}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v6m3-3H9" />
          </svg>
        </button>
        <button
          onClick={onReset}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          title={t('timeline.resetZoom')}
        >
          {t('timeline.reset')}
        </button>
      </div>
      
      {/* Scroll Controls - Only show when zoomed and handlers provided */}
      {zoomLevel > 1 && onScrollLeft && onScrollRight && (
        <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 rounded-md">
          <button
            onClick={onScrollLeft}
            className="p-1 hover:bg-gray-200 rounded-sm transition-colors"
            title={t('timeline.scrollLeft')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-xs text-gray-600 px-2">{t('timeline.scroll')}</span>
          <button
            onClick={onScrollRight}
            className="p-1 hover:bg-gray-200 rounded-sm transition-colors"
            title={t('timeline.scrollRight')}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}