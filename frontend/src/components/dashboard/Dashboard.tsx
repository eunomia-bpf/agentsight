// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import { AgentSightSnapshot } from '@/types/event';
import { deriveSessions, deriveSummary, formatDurationMs } from '@/utils/dashboard';
import { DashboardPanel, RankedRow } from './DashboardPanel';
import { SummaryBand } from './SummaryBand';
import { ActivityChart } from './ActivityChart';
import { TokensPanel } from './TokensPanel';
import { EffectProfile } from './EffectProfile';
import { ResourceShape } from './ResourceShape';
import { FrictionSignals } from './FrictionSignals';
import { categoricalColor } from './colors';

// Re-exported so panel drill-down callbacks stay typed against the app shell's
// view switcher in page.tsx.
export type ViewMode = 'overview' | 'log' | 'timeline' | 'process-tree' | 'metrics';

interface DashboardProps {
  snapshot: AgentSightSnapshot | null;
  onNavigate: (view: ViewMode) => void;
}

export function Dashboard({ snapshot, onNavigate }: DashboardProps) {
  const { t } = useTranslation();
  const summary = useMemo(() => deriveSummary(snapshot ?? {}), [snapshot]);
  const sessions = useMemo(() => deriveSessions(snapshot ?? {}), [snapshot]);

  if (!snapshot) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-12 text-center shadow-md">
        <p className="text-gray-500">{t('app.noEventsLoaded')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <SummaryBand summary={summary} onNavigate={onNavigate} />

      {sessions.length > 1 && (
        <DashboardPanel
          title={t('dash.sessions.title')}
          subtitle={t('dash.sessions.subtitle')}
          bodyClassName="pt-2"
        >
          <ul className="divide-y divide-gray-50">
            {sessions.map((s) => (
              <RankedRow
                key={s.id}
                swatch={categoricalColor(s.id)}
                label={`${s.agentType} · ${s.model ?? '—'}`}
                sublabel={`${formatDurationMs(s.durationMs)} · ${s.status}`}
                count={s.totalTokens}
                countLabel={s.totalTokens > 0 ? t('dash.sessions.tokens') : undefined}
              />
            ))}
          </ul>
          <p className="mt-2 text-[11px] text-gray-400">{t('dash.sessions.note')}</p>
        </DashboardPanel>
      )}

      <ActivityChart snapshot={snapshot} onNavigate={onNavigate} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TokensPanel snapshot={snapshot} llmCalls={summary.llmCalls} onNavigate={onNavigate} />
        <EffectProfile snapshot={snapshot} onNavigate={onNavigate} />
        <ResourceShape snapshot={snapshot} onNavigate={onNavigate} />
        <FrictionSignals snapshot={snapshot} onNavigate={onNavigate} />
      </div>
    </div>
  );
}
