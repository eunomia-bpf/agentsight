// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from '@/i18n';
import type { AgentSightSnapshot } from '@/types/event';
import { formatDuration } from '@/utils/eventProcessing';
import {
  EVENT_SPAN_KINDS,
  type EventSpan,
  type EventSpanKind,
  type EventSpanStatus,
  eventSpans,
  formatOffset,
  packSpans,
  tickStep,
} from '@/utils/eventSpans';

const BAR_TONES: Record<EventSpanStatus, string> = {
  success: 'bg-emerald-500',
  failed: 'bg-red-500',
  running: 'bg-blue-500',
  unknown: 'bg-slate-400',
};

const BADGE_TONES: Record<EventSpanStatus, string> = {
  success: 'bg-emerald-50 text-emerald-700',
  failed: 'bg-red-50 text-red-700',
  running: 'bg-blue-50 text-blue-700',
  unknown: 'bg-slate-100 text-slate-600',
};

const TABLE_LIMIT = 300;
const MIN_BAR_PERCENT = 0.4;

export function SessionEvents({ snapshot, captureEnd }: {
  snapshot: AgentSightSnapshot;
  /** Latest moment of the whole capture, which a session-scoped snapshot may not carry. */
  captureEnd?: number | null;
}) {
  const { t } = useTranslation();
  const spans = useMemo(() => eventSpans(snapshot, { captureEnd }), [captureEnd, snapshot]);
  const rowIds = useMemo(() => new Map(spans.map((span, index) => [span.id, `event-row-${index}`])), [spans]);
  const [sandboxId, setSandboxId] = useState('');
  const sandboxes = snapshot.sandboxes ?? [];
  const scopedSpans = spans.filter((span) => !sandboxId || span.sandboxId === sandboxId);
  const [hidden, setHidden] = useState<EventSpanKind[]>([]);
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const range = useMemo(() => {
    const start = spans.reduce((value, span) => Math.min(value, span.start), Number.POSITIVE_INFINITY);
    const end = spans.reduce((value, span) => Math.max(value, span.end), Number.NEGATIVE_INFINITY);
    return Number.isFinite(start) ? { start, length: Math.max(1, end - start) } : { start: 0, length: 1 };
  }, [spans]);

  const visible = scopedSpans.filter((span) => (
    !hidden.includes(span.kind) && (!failuresOnly || span.status === 'failed')
  ));
  // Pack bars by the box they are drawn in: short spans get a minimum width
  // and spans at the right edge are pulled left, so pack those bounds.
  const minWidth = range.length * MIN_BAR_PERCENT / 100;
  const latestStart = range.start + range.length - minWidth;
  const groups = [...new Set(visible.map((span) => span.sandboxId ?? ''))].flatMap((id) => EVENT_SPAN_KINDS
    .map((kind) => ({
      id, kind,
      rows: packSpans(visible.filter((span) => span.kind === kind && (span.sandboxId ?? '') === id).map((span) => {
        const start = Math.min(span.start, latestStart);
        return { span, start, end: Math.max(span.end, start + minWidth) };
      }), range.length * 0.002),
    }))
    .filter((group) => group.rows.length > 0));
  const step = tickStep(range.length);
  const ticks = Array.from({ length: Math.floor(range.length / step) + 1 }, (_, index) => index * step);
  const percent = (value: number) => value / range.length * 100;
  const tableRows = showAll ? visible : visible.slice(0, TABLE_LIMIT);

  useEffect(() => {
    if (sandboxId && !snapshot.sandboxes?.some((sandbox) => sandbox.id === sandboxId)) setSandboxId('');
  }, [sandboxId, snapshot.sandboxes]);

  useEffect(() => {
    if (selected) document.getElementById(rowIds.get(selected) ?? '')?.scrollIntoView({ block: 'nearest' });
  }, [rowIds, selected, showAll]);

  const select = (span: EventSpan) => {
    setHidden((current) => current.filter((kind) => kind !== span.kind));
    setSelected(span.id);
    if (visible.indexOf(span) >= TABLE_LIMIT) setShowAll(true);
  };
  const toggleKind = (kind: EventSpanKind) => setHidden((current) => (
    current.includes(kind) ? current.filter((item) => item !== kind) : [...current, kind]
  ));

  if (!spans.length) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">{t('events.empty')}</p>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      {sandboxes.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-semibold text-slate-950">{t('sandbox.title')}</h2>
            {sandboxes.length > 1 && (
              <label className="text-xs text-slate-600">{t('sandbox.filter')}
                <select aria-label={t('sandbox.filter')} value={sandboxId} onChange={(event) => setSandboxId(event.target.value)}
                  className="ml-2 rounded border border-slate-300 bg-white p-1">
                  <option value="">{t('sandbox.all')}</option>
                  {sandboxes.map((sandbox) => <option key={sandbox.id} value={sandbox.id}>{sandbox.name || sandbox.id}</option>)}
                </select>
              </label>
            )}
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {sandboxes.filter((sandbox) => !sandboxId || sandbox.id === sandboxId).map((sandbox) => (
              <div key={sandbox.id} data-testid="sandbox-header" className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                <h3 className="font-medium text-slate-950">{sandbox.name || sandbox.cgroup_path || sandbox.id}</h3>
                <p className="mt-1">{[sandbox.image, sandbox.runtime, `pidns ${sandbox.pidns}`].filter(Boolean).join(' · ')}</p>
                <p className="mt-1">{t('sandbox.lifetime')}: {formatOffset(sandbox.first_seen_ms - range.start)} → {formatOffset((sandbox.end_timestamp_ms ?? sandbox.last_seen_ms) - range.start)}
                  {' · '}{formatDuration(Math.max(0, (sandbox.end_timestamp_ms ?? sandbox.last_seen_ms) - sandbox.first_seen_ms))}
                  {' · '}{sandbox.exit_code != null ? t('sandbox.exited', { code: sandbox.exit_code }) : t('sandbox.observed')}</p>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {EVENT_SPAN_KINDS.map((kind) => {
          const ofKind = scopedSpans.filter((span) => span.kind === kind);
          const failed = ofKind.filter((span) => span.status === 'failed').length;
          const active = !hidden.includes(kind);
          return (
            <button key={kind} type="button" aria-pressed={active} onClick={() => toggleKind(kind)}
              className={`rounded-xl border px-4 py-3 text-left shadow-sm transition ${
                active ? 'border-slate-200 bg-white' : 'border-dashed border-slate-200 bg-slate-50 opacity-60'
              }`}>
              <div className="text-xs font-medium text-slate-500">{t(`events.kind.${kind}`)}</div>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-semibold tabular-nums text-slate-950">{ofKind.length}</span>
                {failed > 0 && (
                  <span className="text-xs font-medium text-red-700">{t('events.failedCount', { count: failed })}</span>
                )}
              </div>
            </button>
          );
        })}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="font-semibold text-slate-950">{t('events.title')}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t('events.hint')}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3 text-xs">
            <span className="tabular-nums text-slate-500">
              {t('events.range', { duration: formatDuration(Math.round(range.length)) })}
            </span>
            <label className="flex cursor-pointer items-center gap-1.5 text-slate-700">
              <input type="checkbox" checked={failuresOnly} onChange={(event) => setFailuresOnly(event.target.checked)}
                className="h-3.5 w-3.5 rounded border-slate-300" />
              {t('events.failuresOnly')}
            </label>
          </div>
        </div>

        {groups.length === 0 ? (
          <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-500">{t('events.noMatch')}</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <div className="min-w-[640px]">
              <div className="flex">
                <div className="w-28 shrink-0" />
                <div className="relative h-5 flex-1 border-b border-slate-200">
                  {ticks.map((tick) => (
                    <span key={tick} className="absolute bottom-1 -translate-x-1/2 text-[10px] tabular-nums text-slate-400"
                      style={{ left: `${percent(tick)}%` }}>
                      {formatOffset(tick)}
                    </span>
                  ))}
                </div>
              </div>
              {groups.map((group, index) => (
                <div key={`${group.id}:${group.kind}`} className="flex border-b border-slate-100 py-2 last:border-b-0">
                  <div className="w-28 shrink-0 pr-3 pt-0.5 text-xs font-medium text-slate-600">
                    {group.id && (index === 0 || groups[index - 1].id !== group.id) && <div className="mb-1 truncate text-slate-950">{sandboxes.find((sandbox) => sandbox.id === group.id)?.name || group.id}</div>}
                    {t(`events.kind.${group.kind}`)}
                  </div>
                  <div className="relative flex-1">
                    {ticks.map((tick) => (
                      <span key={tick} aria-hidden className="absolute inset-y-0 w-px bg-slate-100"
                        style={{ left: `${percent(tick)}%` }} />
                    ))}
                    {group.rows.map((row, rowIndex) => (
                      <div key={rowIndex} className="relative h-5">
                        {row.map(({ span, start, end }) => (
                          <button key={span.id} type="button" onClick={() => select(span)}
                            aria-pressed={selected === span.id}
                            aria-label={`${span.label} · ${t(`events.status.${span.status}`)}`}
                            title={spanTitle(span, range.start, t(`events.status.${span.status}`), t('events.open'))}
                            className={`absolute top-1 h-3 rounded-sm ${BAR_TONES[span.status]} ${
                              span.open ? 'opacity-60' : ''
                            } ${selected === span.id ? 'ring-2 ring-slate-900 ring-offset-1' : 'hover:brightness-110'}`}
                            style={{ left: `${percent(start - range.start)}%`, width: `${percent(end - start)}%` }} />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-100 px-5 py-3 font-semibold text-slate-950">{t('events.table')}</h2>
        <div className="max-h-[480px] overflow-auto">
          <table className="w-full min-w-[720px] text-left text-xs">
            <thead className="sticky top-0 bg-slate-50 text-[10px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-5 py-2 font-medium">{t('events.column.kind')}</th>
                <th className="px-3 py-2 font-medium">{t('events.column.event')}</th>
                <th className="px-3 py-2 text-right font-medium">{t('events.column.start')}</th>
                <th className="px-3 py-2 text-right font-medium">{t('events.column.duration')}</th>
                <th className="px-3 py-2 font-medium">{t('events.column.status')}</th>
                <th className="px-5 py-2 text-right font-medium">{t('events.column.pid')}</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((span) => (
                <tr key={span.id} id={rowIds.get(span.id)} tabIndex={0} aria-selected={selected === span.id}
                  onClick={() => setSelected(span.id)}
                  onKeyDown={(event) => {
                    if (event.key !== 'Enter' && event.key !== ' ') return;
                    event.preventDefault();
                    setSelected(span.id);
                  }}
                  className={`cursor-pointer border-t border-slate-100 focus:outline-none focus-visible:bg-slate-50 ${
                    selected === span.id ? 'bg-blue-50' : 'hover:bg-slate-50'
                  }`}>
                  <td className="whitespace-nowrap px-5 py-2 text-slate-500">{t(`events.kind.${span.kind}`)}</td>
                  <td className="max-w-md px-3 py-2">
                    <div className="truncate font-medium text-slate-900" title={span.label}>{span.label}</div>
                    {span.detail && <div className="truncate text-[11px] text-slate-400">{span.detail}</div>}
                    {span.modelCallId && (
                      <a href={`#${rowIds.get(span.modelCallId)}`} className="text-[11px] text-blue-600 hover:underline"
                        title={t('sandbox.inference')} onClick={(event) => {
                          event.stopPropagation();
                          setSandboxId(''); setFailuresOnly(false); setShowAll(true);
                          const call = spans.find((candidate) => candidate.id === span.modelCallId);
                          if (call) select(call);
                        }}>{t('sandbox.modelCall')}</a>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-slate-600">
                    {formatOffset(span.start - range.start)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-slate-900">
                    {span.end > span.start ? `${formatDuration(Math.round(span.end - span.start))}${span.open ? '+' : ''}` : '—'}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${BADGE_TONES[span.status]}`}>
                      {t(`events.status.${span.status}`)}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-5 py-2 text-right tabular-nums text-slate-500">{span.pid ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!showAll && visible.length > TABLE_LIMIT && (
          <button type="button" onClick={() => setShowAll(true)}
            className="w-full border-t border-slate-100 py-2 text-xs font-medium text-blue-600 hover:bg-slate-50">
            {t('events.showAll', { count: visible.length })}
          </button>
        )}
      </section>
    </div>
  );
}

function spanTitle(span: EventSpan, origin: number, status: string, openLabel: string): string {
  const duration = span.end > span.start ? formatDuration(Math.round(span.end - span.start)) : '—';
  return [
    span.label,
    `${formatOffset(span.start - origin)} · ${duration} · ${status}${span.open ? ` (${openLabel})` : ''}`,
    span.detail,
  ].filter(Boolean).join('\n');
}
