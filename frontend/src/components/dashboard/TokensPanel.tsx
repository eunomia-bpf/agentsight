// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { ViewMode } from './Dashboard';
import { AgentSightSnapshot } from '@/types/event';
import {
  deriveTokenComposition,
  formatInt,
  formatTokens,
  type TokenPart,
} from '@/utils/dashboard';
import { TOKEN_COLORS, categoricalColor } from './colors';
import { DashboardPanel, EmptyState, PanelDrillLink, RankedRow } from './DashboardPanel';
import { Legend, SegmentedBar } from './chartPrimitives';

interface TokensPanelProps {
  snapshot: AgentSightSnapshot;
  llmCalls: number;
  onNavigate: (view: ViewMode) => void;
}

const PART_KEYS: TokenPart['key'][] = ['cache_read', 'cache_creation', 'input', 'output'];

export function TokensPanel({ snapshot, llmCalls, onNavigate }: TokensPanelProps) {
  const { t } = useTranslation();
  const comp = useMemo(() => deriveTokenComposition(snapshot, TOKEN_COLORS), [snapshot]);

  // Model API endpoints: hosts from network_targets that read like an LLM
  // provider (heuristic on host only; no invented classification).
  const apiHosts = useMemo(() => {
    const targets = snapshot.network_targets ?? [];
    const byHost = new Map<string, number>();
    for (const tg of targets) {
      const host = tg.host ?? '';
      const looksLikeApi =
        /api\.|llm|openai|anthropic|xai|groq|mistral|deepseek|together|fireworks|cohere|googleapis|generativelanguage/i.test(
          host,
        );
      if (!looksLikeApi) continue;
      byHost.set(host, (byHost.get(host) ?? 0) + (tg.count ?? 0));
    }
    return Array.from(byHost.entries()).sort((a, b) => b[1] - a[1]).slice(0, 4);
  }, [snapshot]);

  const action = (
    <PanelDrillLink label={t('dash.openLogs')} onClick={() => onNavigate('log')} />
  );

  if (comp.models.length === 0 && llmCalls === 0) {
    return (
      <DashboardPanel title={t('dash.tokens.title')} subtitle={t('dash.tokens.subtitle')} action={action}>
        <EmptyState message={t('dash.empty')} hint={t('dash.emptyTokensHint')} />
      </DashboardPanel>
    );
  }

  const partLegend = PART_KEYS.filter((k) => (comp.partsTotals[k] ?? 0) > 0).map((k) => ({
    label: labelForPart(k),
    color: TOKEN_COLORS[k],
    value: formatTokens(comp.partsTotals[k] ?? 0),
  }));

  return (
    <DashboardPanel title={t('dash.tokens.title')} subtitle={t('dash.tokens.subtitle')} action={action}>
      {/* Grand totals */}
      <div className="mb-3 grid grid-cols-3 gap-2">
        <div className="rounded-md border border-gray-100 bg-gray-50/60 px-3 py-2">
          <div className="text-lg font-semibold text-gray-900" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {formatTokens(comp.grandTotal)}
          </div>
          <div className="text-[11px] uppercase tracking-wide text-gray-500">{t('dash.tokens.totalTokens')}</div>
        </div>
        <div className="rounded-md border border-gray-100 bg-gray-50/60 px-3 py-2">
          <div className="text-lg font-semibold text-gray-900" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {formatInt(llmCalls)}
          </div>
          <div className="text-[11px] uppercase tracking-wide text-gray-500">{t('dash.tokens.modelCalls')}</div>
        </div>
        <div className="rounded-md border border-gray-100 bg-gray-50/60 px-3 py-2">
          <div className="text-lg font-semibold text-gray-900" style={{ fontVariantNumeric: 'tabular-nums' }}>
            {comp.models.length}
          </div>
          <div className="text-[11px] uppercase tracking-wide text-gray-500">{t('dash.tokens.models')}</div>
        </div>
      </div>

      {/* Per-model composition */}
      <div className="mb-2">
        <Legend items={partLegend} />
      </div>

      <ul className="space-y-2">
        {comp.models.map((m) => {
          const segments = PART_KEYS.filter((k) => m.parts.find((p) => p.key === k)).map((k) => {
            const p = m.parts.find((pp) => pp.key === k)!;
            return { label: labelForPart(k), value: p.value, color: p.color };
          });
          const pct = comp.grandTotal > 0 ? (m.total / comp.grandTotal) * 100 : 0;
          return (
            <li key={m.model} className="space-y-1">
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className="truncate font-medium text-gray-800" title={m.model}>
                  <span
                    className="mr-1.5 inline-block h-2 w-2 align-middle rounded-sm"
                    style={{ background: categoricalColor(m.model) }}
                  />
                  {m.model}
                </span>
                <span className="shrink-0 text-gray-500" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  {formatTokens(m.total)} <span className="text-gray-400">· {pct.toFixed(0)}%</span>
                </span>
              </div>
              <SegmentedBar segments={segments} height={12} />
            </li>
          );
        })}
      </ul>

      {apiHosts.length > 0 && (
        <div className="mt-3 border-t border-gray-100 pt-2">
          <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-gray-500">
            {t('dash.tokens.apiEndpoints')}
          </div>
          <ul className="divide-y divide-gray-50">
            {apiHosts.map(([host, count]) => (
              <RankedRow
                key={host}
                swatch={categoricalColor(host)}
                label={host}
                count={count}
                countLabel={t('dash.tokens.requests')}
              />
            ))}
          </ul>
        </div>
      )}

      <p className="mt-3 text-[11px] text-gray-400">{t('dash.tokens.noCostNote')}</p>
    </DashboardPanel>
  );
}

function labelForPart(key: TokenPart['key']): string {
  switch (key) {
    case 'input':
      return 'Input';
    case 'output':
      return 'Output';
    case 'cache_creation':
      return 'Cache write';
    case 'cache_read':
      return 'Cache read';
  }
}
