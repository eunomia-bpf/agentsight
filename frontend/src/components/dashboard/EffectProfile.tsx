// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { AgentSightSnapshot } from '@/types/event';
import { deriveEffects, formatInt, shortPath } from '@/utils/dashboard';
import { EVENT_TYPE_COLORS, categoricalColor } from './colors';
import { DashboardPanel, EmptyState, PanelDrillLink, RankedRow, SeverityBadge } from './DashboardPanel';
import { SegmentedBar } from './chartPrimitives';

interface EffectProfileProps {
  snapshot: AgentSightSnapshot;
  onNavigate: (view: ViewMode) => void;
}

export function EffectProfile({ snapshot, onNavigate }: EffectProfileProps) {
  const { t } = useTranslation();
  const effects = useMemo(
    () => deriveEffects(snapshot, EVENT_TYPE_COLORS, categoricalColor),
    [snapshot],
  );

  const action = (
    <div className="flex flex-wrap items-center gap-2">
      {effects.topFiles.length > 0 && (
        <PanelDrillLink label={t('dash.openNebula')} onClick={() => onNavigate('nebula')} />
      )}
      <PanelDrillLink label={t('dash.openTree')} onClick={() => onNavigate('process-tree')} />
    </div>
  );

  if (effects.totalEffects === 0) {
    return (
      <DashboardPanel title={t('dash.effects.title')} subtitle={t('dash.effects.subtitle')} action={action}>
        <EmptyState message={t('dash.empty')} hint={t('dash.emptyEffectsHint')} />
      </DashboardPanel>
    );
  }

  const segments = effects.mix.map((m) => ({ label: m.label, value: m.count, color: m.color }));

  return (
    <DashboardPanel title={t('dash.effects.title')} subtitle={t('dash.effects.subtitle')} action={action}>
      {/* Proportional mix of process / file / network effects */}
      <SegmentedBar segments={segments} height={16} />
      <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-600" style={{ fontVariantNumeric: 'tabular-nums' }}>
        {effects.mix.map((m) => (
          <span key={m.type} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: m.color }} />
            <span className="capitalize">{m.label}</span>
            <span className="font-semibold text-gray-900">{formatInt(m.count)}</span>
          </span>
        ))}
      </div>

      {(effects.processFailures > 0 || effects.networkErrorEvents > 0) && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {effects.processFailures > 0 && (
            <SeverityBadge severity="critical">
              {formatInt(effects.processFailures)} {t('dash.effects.failedExits')}
            </SeverityBadge>
          )}
          {effects.networkErrorEvents > 0 && (
            <SeverityBadge severity="warning">
              {formatInt(effects.networkErrorEvents)} {t('dash.effects.netErrors')}
            </SeverityBadge>
          )}
        </div>
      )}

      <div className="mt-3 grid grid-cols-1 gap-x-4 gap-y-2 md:grid-cols-2">
        <EffectList
          heading={t('dash.effects.topCommands')}
          empty={t('dash.effects.noCommands')}
          rows={effects.topCommands.map((c) => ({
            swatch: c.color,
            label: shortPath(c.label, 42),
            sublabel: c.sublabel,
            count: c.count,
          }))}
        />
        <EffectList
          heading={t('dash.effects.topFiles')}
          empty={t('dash.effects.noFiles')}
          rows={effects.topFiles.map((f) => ({
            swatch: f.color,
            label: shortPath(f.label, 46),
            count: f.count,
          }))}
        />
      </div>

      {effects.topHosts.length > 0 && (
        <EffectList
          className="mt-2 border-t border-gray-100 pt-2"
          heading={t('dash.effects.topHosts')}
          empty=""
          rows={effects.topHosts.map((h) => ({
            swatch: h.color,
            label: shortPath(h.label, 50),
            sublabel: h.sublabel,
            count: h.count,
          }))}
        />
      )}
    </DashboardPanel>
  );
}

function EffectList({
  heading,
  rows,
  empty,
  className = '',
}: {
  heading: string;
  rows: { swatch: string; label: string; sublabel?: string; count: number }[];
  empty: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="mb-0.5 text-[11px] font-medium uppercase tracking-wide text-gray-500">{heading}</div>
      {rows.length === 0 ? (
        <p className="py-1 text-xs text-gray-400">{empty}</p>
      ) : (
        <ol className="divide-y divide-gray-50">
          {rows.map((r, i) => (
            <RankedRow
              key={`${r.label}-${i}`}
              rank={i + 1}
              swatch={r.swatch}
              label={r.label}
              sublabel={r.sublabel}
              count={r.count}
            />
          ))}
        </ol>
      )}
    </div>
  );
}
