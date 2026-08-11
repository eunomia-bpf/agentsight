// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import { AgentSightSnapshot } from '@/types/event';
import { deriveSummary } from '@/utils/dashboard';
import { SummaryBand } from './SummaryBand';
import { ActivityChart } from './ActivityChart';
import { TokensPanel } from './TokensPanel';
import { EffectProfile } from './EffectProfile';
import { ResourceShape } from './ResourceShape';
import { FrictionSignals } from './FrictionSignals';

// Sessions is the default operational workspace. The remaining views inspect
// evidence around the selected Node.
export type ViewMode = 'sessions' | 'overview' | 'log' | 'timeline' | 'process-tree' | 'metrics';

interface DashboardProps {
  snapshot: AgentSightSnapshot | null;
  onNavigate: (view: ViewMode) => void;
}

export function Dashboard({ snapshot, onNavigate }: DashboardProps) {
  const { t } = useTranslation();
  const summary = useMemo(() => deriveSummary(snapshot ?? {}), [snapshot]);

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
