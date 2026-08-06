// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { AgentSightSnapshot } from '@/types/event';
import {
  deriveResourceShape,
  formatClock,
  formatDurationMs,
  formatInt,
  type ResourceSeries,
} from '@/utils/dashboard';
import { DashboardPanel, EmptyState, PanelDrillLink, SeverityBadge } from './DashboardPanel';
import { LineArea, type ChartPoint } from './chartPrimitives';

interface ResourceShapeProps {
  snapshot: AgentSightSnapshot;
  onNavigate: (view: ViewMode) => void;
}

function toPoints(series: ResourceSeries, sharedMax?: number): ChartPoint[] {
  const span = Math.max(series.endMs - series.startMs, 1);
  const max = sharedMax ?? Math.max(series.max, 1);
  const denom = Math.max(series.points.length - 1, 1);
  return series.points.map((p, i) => ({
    x: series.points.length > 1 ? (p.ms - series.startMs) / span : i / denom,
    y: Math.min(p.value / max, 1),
    value: p.value,
    label: formatClock(p.ms),
  }));
}

export function ResourceShape({ snapshot, onNavigate }: ResourceShapeProps) {
  const { t } = useTranslation();
  const shape = useMemo(() => deriveResourceShape(snapshot, 50), [snapshot]);

  const action = (
    <PanelDrillLink label={t('dash.openMetrics')} onClick={() => onNavigate('metrics')} />
  );

  if (!shape.cpu && !shape.rss) {
    return (
      <DashboardPanel title={t('dash.resource.title')} subtitle={t('dash.resource.subtitle')} action={action}>
        <EmptyState message={t('dash.empty')} hint={t('dash.emptyResourceHint')} />
      </DashboardPanel>
    );
  }

  const cpuSustained = shape.cpu?.sustainedTail ?? 0;
  const cpuSustainedDuration = shape.cpu ? cpuSustained * estimateSampleStepMs(shape.cpu) : 0;

  return (
    <DashboardPanel title={t('dash.resource.title')} subtitle={t('dash.resource.subtitle')} action={action} bodyClassName="pt-2">
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500" style={{ fontVariantNumeric: 'tabular-nums' }}>
        <span>
          {t('dash.resource.samples')}: <span className="font-medium text-gray-700">{formatInt(shape.sampleCount)}</span>
        </span>
        {shape.processes.length > 0 && (
          <span>
            {t('dash.resource.processes')}: {shape.processes.map((p) => `${p.comm} (${p.count})`).join(', ')}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {shape.cpu && (
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">
                {t('dash.resource.cpu')}
              </span>
              <div className="flex items-center gap-2 text-[11px]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {cpuSustained >= 2 && (
                  <SeverityBadge severity={cpuSustained >= 4 ? 'critical' : 'warning'}>
                    {t('dash.resource.sustainedCpu', { count: cpuSustained })}
                  </SeverityBadge>
                )}
                <span className="text-gray-400">
                  {t('dash.resource.peak')} {shape.cpu.max.toFixed(0)}% · {t('dash.resource.avg')} {shape.cpu.mean.toFixed(0)}%
                </span>
              </div>
            </div>
            <LineArea
              points={toPoints(shape.cpu)}
              color="#0072B2"
              height={132}
              formatValue={(v) => `${v.toFixed(0)}%`}
              ariaLabel={t('dash.resource.cpu')}
            />
          </div>
        )}

        {shape.rss && (
          <div>
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">
                {t('dash.resource.memory')}
              </span>
              <span className="text-[11px] text-gray-400" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {t('dash.resource.peak')} {formatInt(shape.rss.max)} MB · {t('dash.resource.avg')} {formatInt(shape.rss.mean)} MB
              </span>
            </div>
            <LineArea
              points={toPoints(shape.rss)}
              color="#9268C4"
              height={132}
              formatValue={(v) => `${formatInt(v)} MB`}
              ariaLabel={t('dash.resource.memory')}
            />
          </div>
        )}
      </div>

      {cpuSustainedDuration > 0 && (
        <p className="mt-2 text-[11px] text-gray-400">
          {t('dash.resource.sustainedNote', { dur: formatDurationMs(cpuSustainedDuration) })}
        </p>
      )}
    </DashboardPanel>
  );
}

function estimateSampleStepMs(series: ResourceSeries): number {
  if (series.points.length < 2) return 1000;
  return Math.max(
    1,
    (series.endMs - series.startMs) / Math.max(series.points.length - 1, 1),
  );
}
