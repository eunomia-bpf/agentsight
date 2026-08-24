// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo, useState } from 'react';
import { ArrowPathIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '@/i18n';
import type { CloudOrganization } from '@/lib/controllerClient';
import {
  filterFleetNodes, fleetSubscriptions, fleetTotals, isRunningSession,
  type FleetNodeSample,
} from '@/lib/fleetData';
import { Subscription } from '@/components/NodeOverview';

type Filter = 'all' | 'running' | 'idle' | 'unreachable';

function count(value: number): string {
  if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return Math.round(value).toLocaleString();
}

function planTitle(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function FleetOverview({
  samples,
  loading,
  error,
  organization,
  onRefresh,
  onOpenNode,
}: {
  samples: FleetNodeSample[];
  loading: boolean;
  error: string;
  organization: CloudOrganization | null;
  onRefresh: () => void;
  onOpenNode: (nodeId: string) => void;
}) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<Filter>('all');
  const totals = useMemo(() => fleetTotals(samples), [samples]);
  const subscriptions = useMemo(() => fleetSubscriptions(samples), [samples]);
  const visible = useMemo(() => filterFleetNodes(samples, filter), [filter, samples]);
  const filters: Array<[Filter, string, number]> = [
    ['all', t('fleet.all'), totals.machines],
    ['running', t('fleet.running'), samples.filter((item) => item.overview?.rows.some(isRunningSession)).length],
    ['idle', t('fleet.idle'), samples.filter((item) => item.state === 'online'
      && !item.overview?.rows.some(isRunningSession)).length],
    ['unreachable', t('fleet.unreachable'), totals.unreachable],
  ];

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <Stat label={t('fleet.machines')} value={`${totals.online}/${totals.machines}`}
          hint={t('fleet.onlineHint')} />
        <Stat label={t('overview.running')} value={String(totals.running)} hint={t('fleet.runningHint')} />
        <Stat label={t('overview.stopped')} value={String(totals.stopped)} hint={t('fleet.stoppedHint')} />
        <Stat label={t('overview.tokens')} value={count(totals.tokens)} hint={t('fleet.tokensHint')} />
        <Stat label={t('overview.cpu')} value={`${totals.cpu.toFixed(1)}%`}
          hint={t('overview.processHint', { count: totals.processes })} />
        <Stat label={t('overview.memory')} value={`${count(totals.rss)} MB`} hint={t('fleet.memoryHint')} />
      </section>

      {error && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {error}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
            <div>
              <h1 className="font-semibold text-slate-950">{t('fleet.title')}</h1>
              <p className="mt-0.5 text-xs text-slate-500">{t('fleet.hint')}</p>
            </div>
            <button type="button" onClick={onRefresh} disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
              <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              {t('nodes.refresh')}
            </button>
          </header>
          <div className="flex flex-wrap gap-2 border-b border-slate-100 px-5 py-3" role="group" aria-label={t('fleet.filters')}>
            {filters.map(([value, label, total]) => (
              <button key={value} type="button" onClick={() => setFilter(value)} aria-pressed={filter === value}
                className={`rounded-full px-3 py-1.5 text-xs font-medium ${filter === value
                  ? 'bg-slate-950 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                {label} <span className="ml-1 tabular-nums opacity-70">{total}</span>
              </button>
            ))}
          </div>
          <div className="grid gap-3 p-4 md:grid-cols-2 2xl:grid-cols-3">
            {visible.map((sample) => <Machine key={sample.node.id} sample={sample} onOpenNode={onOpenNode} />)}
          </div>
          {!loading && visible.length === 0 && (
            <p className="p-12 text-center text-sm text-slate-500">{t('fleet.empty')}</p>
          )}
        </section>

        <aside className="space-y-4">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">{t('overview.subscriptions')}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t('fleet.subscriptionsHint')}</p>
            <div className="mt-4 space-y-4">
              {subscriptions.map((subscription) => (
                <Subscription key={subscription.provider} subscription={subscription} />
              ))}
              {subscriptions.length === 0 && (
                <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">
                  {t('fleet.subscriptionUnavailable')}
                </p>
              )}
            </div>
          </section>
          {organization && (
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="font-semibold text-slate-950">AgentSight</h2>
              <div className="mt-3 rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-400">{t('fleet.organizationPlan')}</div>
                <div className="mt-1 font-semibold text-slate-900">{planTitle(organization.effectivePlan)}</div>
              </div>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

function Machine({ sample, onOpenNode }: {
  sample: FleetNodeSample;
  onOpenNode: (nodeId: string) => void;
}) {
  const { t } = useTranslation();
  const rows = sample.overview?.rows ?? [];
  const running = rows.filter(isRunningSession);
  const stopped = rows.filter((row) => !isRunningSession(row) && !!row.session_id).length;
  const cpu = running.reduce((total, row) => total + row.cpu_percent, 0);
  const rss = running.reduce((total, row) => total + row.rss_mb, 0);
  const plans = rows.flatMap((row) => (row.plan ?? []).filter((step) => step.status !== 'completed'));
  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <button type="button" onClick={() => onOpenNode(sample.node.id)}
        className="block w-full p-4 text-left hover:bg-blue-50/40">
        <div className="flex items-start justify-between gap-3">
          <span className={`rounded-lg p-2 ${sample.state === 'online'
            ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
            <ComputerDesktopIcon className="h-5 w-5" />
          </span>
          <Status state={sample.state} />
        </div>
        <h2 className="mt-3 truncate font-semibold text-slate-950">{sample.node.name}</h2>
        <p className="mt-0.5 truncate text-[11px] text-slate-400">
          {sample.transport ? sample.transport.toUpperCase() : sample.node.id}
          {sample.node.version ? ` · v${sample.node.version.replace(/^v/, '')}` : ''}
        </p>
        {sample.overview ? (
          <>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <Metric label={t('fleet.active')} value={String(running.length)} />
              <Metric label={t('overview.tokens')} value={count(sample.overview.total_tokens)} />
              <Metric label="CPU" value={`${cpu.toFixed(1)}%`} />
            </div>
            <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500">
              <span>{t('fleet.stoppedCount', { count: stopped })}</span>
              <span>{count(rss)} MB RSS</span>
              <span>{new Set(rows.map((row) => row.agent)).size} {t('overview.agents')}</span>
            </div>
            {plans[0] && <p className="mt-3 truncate rounded bg-blue-50 px-2 py-1.5 text-xs text-blue-800">{plans[0].step}</p>}
          </>
        ) : (
          <p className="mt-4 min-h-16 text-sm text-slate-500">
            {sample.state === 'checking' ? t('fleet.checkingDetail') : t('fleet.unreachableDetail')}
          </p>
        )}
      </button>
    </article>
  );
}

function Status({ state }: { state: FleetNodeSample['state'] }) {
  const { t } = useTranslation();
  const style = state === 'online' ? 'bg-emerald-50 text-emerald-700'
    : state === 'checking' ? 'bg-blue-50 text-blue-700' : 'bg-slate-100 text-slate-500';
  return <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${style}`}>{t(`fleet.${state}`)}</span>;
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums tracking-tight text-slate-950">{value}</div>
      <div className="mt-0.5 truncate text-[11px] text-slate-400">{hint}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-2 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-0.5 text-xs font-semibold tabular-nums text-slate-800">{value}</div>
    </div>
  );
}
