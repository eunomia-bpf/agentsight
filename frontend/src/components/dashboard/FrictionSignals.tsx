// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { AgentSightSnapshot } from '@/types/event';
import {
  deriveFriction,
  formatDurationMs,
  type FrictionSeverity,
  type FrictionSignal,
} from '@/utils/dashboard';
import {
  DashboardPanel,
  EmptyState,
  PanelDrillLink,
  SeverityBadge,
} from './DashboardPanel';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ClockIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

interface FrictionSignalsProps {
  snapshot: AgentSightSnapshot;
  onNavigate: (view: ViewMode) => void;
}

const SEVERITY_ICON: Record<FrictionSeverity, typeof ExclamationTriangleIcon> = {
  critical: ExclamationTriangleIcon,
  warning: ArrowTrendingDownIcon,
  info: InformationCircleIcon,
};

const SEVERITY_ICON_CLASS: Record<FrictionSeverity, string> = {
  critical: 'text-red-500',
  warning: 'text-amber-500',
  info: 'text-blue-400',
};

export function FrictionSignals({ snapshot, onNavigate }: FrictionSignalsProps) {
  const { t } = useTranslation();
  const result = useMemo(() => deriveFriction(snapshot), [snapshot]);

  const action = (
    <PanelDrillLink label={t('dash.openLogs')} onClick={() => onNavigate('log')} />
  );

  if (result.signals.length === 0) {
    return (
      <DashboardPanel title={t('dash.friction.title')} subtitle={t('dash.friction.subtitle')} action={action}>
        <div className="flex flex-col items-center py-6 text-center">
          <InformationCircleIcon className="h-8 w-8 text-green-500" />
          <p className="mt-2 text-sm text-gray-600">{t('dash.friction.none')}</p>
          {result.maxLlmGapMs > 0 && (
            <p className="mt-1 text-xs text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
              {t('dash.friction.maxGap', { gap: formatDurationMs(result.maxLlmGapMs) })}
            </p>
          )}
        </div>
      </DashboardPanel>
    );
  }

  return (
    <DashboardPanel title={t('dash.friction.title')} subtitle={t('dash.friction.subtitle')} action={action}>
      <ul className="space-y-1.5">
        {result.signals.map((s) => (
          <FrictionRow key={s.id} signal={s} />
        ))}
      </ul>
      {result.maxLlmGapMs > 0 && (
        <p className="mt-2 text-[11px] text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {t('dash.friction.maxGap', { gap: formatDurationMs(result.maxLlmGapMs) })}
        </p>
      )}
    </DashboardPanel>
  );
}

function FrictionRow({ signal }: { signal: FrictionSignal }) {
  const Icon = iconFor(signal);
  const IconBase = SEVERITY_ICON[signal.severity];
  return (
    <li className="flex items-start gap-2 rounded-md border border-gray-100 bg-gray-50/50 px-2.5 py-1.5">
      <IconBase className={`mt-0.5 h-4 w-4 shrink-0 ${SEVERITY_ICON_CLASS[signal.severity]}`} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">
            {signal.category}
          </span>
          <SeverityBadge severity={signal.severity}>
            {signal.count > 1 ? `×${signal.count}` : signal.severity}
          </SeverityBadge>
        </div>
        <div className="mt-0.5 break-words text-xs font-medium text-gray-800" title={signal.title}>
          {signal.title}
        </div>
        {signal.detail && <div className="text-[11px] text-gray-400">{signal.detail}</div>}
      </div>
      <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gray-300" />
    </li>
  );
}

// A secondary icon that hints at the signal kind, independent of severity color.
function iconFor(signal: FrictionSignal): typeof ExclamationTriangleIcon {
  if (signal.category === 'Repeated command' || signal.category === 'Repeated tool call') {
    return ArrowPathIcon;
  }
  if (signal.category === 'Think-time gap') {
    return ClockIcon;
  }
  return ExclamationTriangleIcon;
}
