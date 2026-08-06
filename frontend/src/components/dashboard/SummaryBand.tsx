// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { DashboardSummary } from '@/utils/dashboard';
import { formatClock, formatDurationMs, formatInt, formatTokens, shortPath } from '@/utils/dashboard';
import { KpiTile, SeverityBadge } from './DashboardPanel';
import {
  CpuChipIcon,
  CommandLineIcon,
  DocumentTextIcon,
  GlobeAltIcon,
  Cog6ToothIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';

interface SummaryBandProps {
  summary: DashboardSummary;
  onNavigate: (view: ViewMode) => void;
}

export function SummaryBand({ summary, onNavigate }: SummaryBandProps) {
  const { t } = useTranslation();

  const identity = [
    summary.primaryAgent,
    summary.primaryModel,
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-md">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">{t('dash.title')}</h2>
            <SeverityBadge severity={summary.hasFailures ? 'critical' : 'good'}>
              {summary.hasFailures ? t('dash.healthNeedsAttention') : t('dash.healthOk')}
            </SeverityBadge>
            {summary.sessionCount > 1 && (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600">
                {t('dash.sessionCount', { count: summary.sessionCount })}
              </span>
            )}
          </div>
          {identity && <p className="mt-0.5 truncate text-sm text-gray-600" title={identity}>{identity}</p>}
          <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-0.5 text-xs text-gray-500" style={{ fontVariantNumeric: 'tabular-nums' }}>
            <span>
              <span className="font-medium text-gray-700">{formatDurationMs(summary.durationMs)}</span>{' '}
              {t('dash.duration')}
            </span>
            <span>
              {formatClock(summary.startMs)} – {formatClock(summary.endMs)}
            </span>
            {summary.cwd && (
              <span className="truncate" title={summary.cwd}>
                {t('dash.cwd')} {shortPath(summary.cwd, 56)}
              </span>
            )}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {summary.filesTouched > 0 && (
            <button
              type="button"
              onClick={() => onNavigate('nebula')}
              className="rounded-md border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-medium text-teal-800 hover:bg-teal-100"
            >
              {t('dash.openNebula')}
            </button>
          )}
          <button
            type="button"
            onClick={() => onNavigate('log')}
            className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            {t('dash.viewLogs')}
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <KpiTile
          label={t('dash.kpi.tokens')}
          value={formatTokens(summary.totalTokens)}
          hint={`${formatTokens(summary.inputTokens)} in / ${formatTokens(summary.outputTokens)} out`}
        />
        <KpiTile
          label={t('dash.kpi.llmCalls')}
          value={formatInt(summary.llmCalls)}
          hint={summary.cacheReadTokens > 0 ? `${formatTokens(summary.cacheReadTokens)} cache read` : undefined}
        />
        <KpiTile
          label={t('dash.kpi.processes')}
          value={formatInt(summary.processExecs)}
          tone={summary.processFailures > 0 ? 'critical' : 'default'}
          hint={summary.processFailures > 0 ? `${summary.processFailures} failed` : undefined}
        />
        <KpiTile label={t('dash.kpi.files')} value={formatInt(summary.filesTouched)} />
        <KpiTile label={t('dash.kpi.network')} value={formatInt(summary.networkEndpoints)} />
        <KpiTile label={t('dash.kpi.tools')} value={formatInt(summary.toolCalls)} />
      </div>

      <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-gray-500 sm:hidden">
        {/* Compact icon legend for the KPI row on very small screens */}
        <span className="flex items-center gap-1"><BoltIcon className="h-3 w-3" /> {t('dash.kpi.tokens')}</span>
        <span className="flex items-center gap-1"><CpuChipIcon className="h-3 w-3" /> {t('dash.kpi.llmCalls')}</span>
        <span className="flex items-center gap-1"><CommandLineIcon className="h-3 w-3" /> {t('dash.kpi.processes')}</span>
        <span className="flex items-center gap-1"><DocumentTextIcon className="h-3 w-3" /> {t('dash.kpi.files')}</span>
        <span className="flex items-center gap-1"><GlobeAltIcon className="h-3 w-3" /> {t('dash.kpi.network')}</span>
        <span className="flex items-center gap-1"><Cog6ToothIcon className="h-3 w-3" /> {t('dash.kpi.tools')}</span>
      </div>
    </section>
  );
}
