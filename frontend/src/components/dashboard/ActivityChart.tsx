// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { AgentSightSnapshot } from '@/types/event';
import { deriveActivity, formatClock, formatDurationMs, formatInt } from '@/utils/dashboard';
import { eventTypeColor } from './colors';
import { DashboardPanel, EmptyState, PanelDrillLink } from './DashboardPanel';
import { Legend, StackedArea, type StackedLayer } from './chartPrimitives';

interface ActivityChartProps {
  snapshot: AgentSightSnapshot;
  onNavigate: (view: ViewMode) => void;
}

export function ActivityChart({ snapshot, onNavigate }: ActivityChartProps) {
  const { t } = useTranslation();
  const series = useMemo(() => deriveActivity(snapshot, 48), [snapshot]);

  const action = (
    <PanelDrillLink label={t('dash.openTimeline')} onClick={() => onNavigate('timeline')} />
  );

  if (!series) {
    return (
      <DashboardPanel title={t('dash.activity.title')} subtitle={t('dash.activity.subtitle')} action={action}>
        <EmptyState message={t('dash.empty')} hint={t('dash.emptyActivityHint')} />
      </DashboardPanel>
    );
  }

  const layers: StackedLayer[] = series.types.map((type) => ({
    key: type,
    label: type,
    color: eventTypeColor(type),
  }));
  const values = series.types.map((type) => series.buckets.map((b) => b.counts[type] ?? 0));

  const labelFor = (bucketIdx: number) => {
    const b = series.buckets[bucketIdx];
    return `${formatClock(b.startMs)} – ${formatClock(b.endMs)}`;
  };

  const legendItems = layers.map((l) => ({
    label: l.label,
    color: l.color,
    value: `${values[layers.indexOf(l)].reduce((s, v) => s + v, 0)}`,
  }));

  return (
    <DashboardPanel
      title={t('dash.activity.title')}
      subtitle={t('dash.activity.subtitle')}
      action={action}
      bodyClassName="pt-2"
    >
      <div className="mb-2 flex items-center justify-between">
        <Legend items={legendItems} />
        <span className="text-xs text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
          {formatInt(series.total)} {t('dash.activity.eventsOver')} {formatDurationMs(series.spanMs)}
        </span>
      </div>
      <StackedArea
        layers={layers}
        values={values}
        bucketCount={series.buckets.length}
        height={128}
        formatBucketLabel={labelFor}
        ariaLabel={t('dash.activity.title')}
      />
      <div className="mt-1 flex justify-between text-[11px] text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
        <span>{formatClock(series.startMs)}</span>
        <span>{formatClock(series.endMs)}</span>
      </div>
    </DashboardPanel>
  );
}
