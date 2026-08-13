// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { Timeline } from '@/components/timeline/Timeline';
import type { SessionDetail } from '@/lib/nodeClient';
import { useTranslation } from '@/i18n';
import type { AgentSightSnapshot, SnapshotSession } from '@/types/event';
import { type DisplayEvent, formatDuration } from '@/utils/eventProcessing';
import { sessionToolCallCount, sessionUsage } from '@/utils/sessionData';

function compact(value: number | null | undefined): string {
  const number = value ?? 0;
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)}B`;
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
  if (number >= 1_000) return `${(number / 1_000).toFixed(1)}k`;
  return Math.round(number).toLocaleString();
}

export function SessionAnalysis({ snapshot, session, detail, events }: {
  snapshot: AgentSightSnapshot;
  session: SnapshotSession;
  detail: SessionDetail | null;
  events: DisplayEvent[];
}) {
  const { t } = useTranslation();
  const usage = detail?.usage ?? sessionUsage(session);
  const tokenParts = [
    [t('analysis.input'), usage.input_tokens ?? 0],
    [t('analysis.output'), usage.output_tokens ?? 0],
    [t('analysis.cacheRead'), usage.cache_read_tokens ?? 0],
    [t('analysis.cacheWrite'), usage.cache_creation_tokens ?? 0],
  ].filter((part): part is [string, number] => Number(part[1]) > 0);
  const tokenTotal = usage.total_tokens || tokenParts.reduce((total, [, value]) => total + value, 0);
  const modelUsage = Object.entries(detail?.model_usage ?? {})
    .filter(([, value]) => (value.total_tokens ?? 0) > 0)
    .sort((left, right) => (right[1].total_tokens ?? 0) - (left[1].total_tokens ?? 0));
  const toolEvents = detail?.events?.tools ?? [];
  const snapshotTools = snapshot.tool_calls ?? [];
  const toolCounts = Object.entries(detail?.tools ?? [...toolEvents, ...snapshotTools]
    .reduce<Record<string, number>>((counts, tool) => {
      const name = tool.tool_name || ('category' in tool ? tool.category : null) || 'tool';
      counts[name] = (counts[name] ?? 0) + 1;
      return counts;
    }, {})).sort((left, right) => right[1] - left[1]);
  const toolFailures = (toolEvents.length ? toolEvents : snapshotTools)
    .filter((tool) => /fail|error|blocked/i.test(tool.status ?? '')).length;
  const processFailures = (snapshot.process_nodes ?? []).filter((process) => (
    process.exit_code != null && process.exit_code !== 0
  )).length;
  const networkErrors = (snapshot.network_targets ?? []).reduce((total, target) => total + (target.error_count ?? 0), 0);
  const samples = snapshot.resource_samples ?? [];
  const averageCpu = samples.length
    ? samples.reduce((total, sample) => total + (sample.cpu_percent ?? 0), 0) / samples.length : 0;
  const peakCpu = samples.reduce((peak, sample) => Math.max(peak, sample.cpu_percent ?? 0), 0);
  const peakRss = samples.reduce((peak, sample) => Math.max(peak, sample.rss_mb ?? 0), 0);
  const duration = detail?.duration_ms || Math.max(0,
    (session.end_timestamp_ms ?? Date.now()) - session.start_timestamp_ms);
  const failures = toolFailures + processFailures + networkErrors;
  const llmTurns = detail?.events?.llm_responses?.length
    || (snapshot.audit_events ?? []).filter((event) => event.audit_type === 'llm' && event.action === 'response').length;
  const toolCallCount = sessionToolCallCount(detail, snapshotTools.length);
  const fileCount = Object.keys(detail?.files ?? {}).length
    || new Set((snapshot.audit_events ?? [])
      .filter((event) => event.audit_type === 'file')
      .map((event) => event.target).filter(Boolean)).size;

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label={t('analysis.duration')} value={formatDuration(duration)} />
        <Metric label={t('analysis.llmTurns')} value={String(llmTurns)} />
        <Metric label={t('analysis.toolCalls')} value={String(toolCallCount)} />
        <Metric label={t('analysis.failures')} value={String(failures)} tone={failures ? 'red' : 'green'} />
      </section>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title={t('analysis.tokenUsage')} hint={t('analysis.tokenUsageHint')}>
          <div className="space-y-3">
            {tokenParts.map(([label, value]) => (
              <Bar key={label} label={label} value={value} total={tokenTotal} />
            ))}
            {tokenParts.length === 0 && <Empty>{t('analysis.noUsage')}</Empty>}
            {modelUsage.length > 0 && (
              <div className="border-t border-slate-100 pt-3">
                <div className="mb-2 text-[10px] font-medium uppercase tracking-wide text-slate-400">
                  {t('analysis.models')}
                </div>
                {modelUsage.slice(0, 4).map(([model, value]) => (
                  <div key={model} className="flex justify-between gap-3 py-1 text-xs">
                    <span className="truncate text-slate-600">{model}</span>
                    <span className="tabular-nums text-slate-900">{compact(value.total_tokens)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Panel>

        <Panel title={t('analysis.execution')} hint={t('analysis.executionHint')}>
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label={t('analysis.files')} value={String(fileCount)} />
            <MiniMetric label={t('analysis.network')} value={String(snapshot.network_targets?.length ?? 0)} />
            <MiniMetric label={t('analysis.processes')} value={String(snapshot.process_nodes?.length ?? 0)} />
            <MiniMetric label={t('analysis.failedActions')} value={String(failures)} />
          </div>
          {toolCounts.length > 0 && (
            <div className="mt-3 border-t border-slate-100 pt-3">
              {toolCounts.slice(0, 5).map(([tool, count]) => (
                <div key={tool} className="flex justify-between gap-3 py-1 text-xs">
                  <span className="truncate text-slate-600">{tool}</span>
                  <span className="tabular-nums text-slate-900">{count}</span>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title={t('analysis.resources')} hint={t('analysis.resourcesHint')}>
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label={t('analysis.averageCpu')} value={samples.length ? `${averageCpu.toFixed(1)}%` : '—'} />
            <MiniMetric label={t('analysis.peakCpu')} value={samples.length ? `${peakCpu.toFixed(1)}%` : '—'} />
            <MiniMetric label={t('analysis.peakRss')} value={samples.length ? `${compact(peakRss)} MB` : '—'} />
            <MiniMetric label={t('analysis.samples')} value={String(samples.length)} />
          </div>
          <div className={`mt-3 rounded-lg px-3 py-2 text-xs ${
            failures ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-700'
          }`}>
            {failures
              ? t('analysis.attention', { count: failures })
              : t('analysis.healthy')}
          </div>
        </Panel>
      </div>

      <Timeline events={events} />
    </div>
  );
}

function Metric({ label, value, tone = 'slate' }: { label: string; value: string; tone?: 'slate' | 'red' | 'green' }) {
  const valueTone = tone === 'red' ? 'text-red-700' : tone === 'green' ? 'text-emerald-700' : 'text-slate-950';
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${valueTone}`}>{value}</div>
    </div>
  );
}

function Panel({ title, hint, children }: { title: string; hint: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">{title}</h2>
      <p className="mt-0.5 text-xs text-slate-500">{hint}</p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 font-semibold tabular-nums text-slate-900">{value}</div>
    </div>
  );
}

function Bar({ label, value, total }: { label: string; value: number; total: number }) {
  const width = total > 0 ? Math.max(2, value / total * 100) : 0;
  return (
    <div>
      <div className="flex justify-between gap-3 text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="tabular-nums text-slate-900">{compact(value)}</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(100, width)}%` }} />
      </div>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">{children}</p>;
}
