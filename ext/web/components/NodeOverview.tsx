// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/i18n';
import type { CloudOrganization } from '@/lib/controllerClient';
import type {
  AgentSightSnapshot, LiveOverview, LiveSession, SnapshotSession, SourceSubscription, SubscriptionWindow,
} from '@/types/event';
import {
  displaySessionId,
  isRunningSession,
  isCurrentSubscriptionWindow,
  isRecordedCaptureSession,
  liveRowForSession,
  latestSubscriptions,
  orderedSessions,
  sessionActivityState,
  sessionLastMessage,
  sessionPlan,
  sessionPrompt,
  sessionWorkspace,
} from '@/utils/sessionData';

function count(value: number | null | undefined): string {
  const number = value ?? 0;
  if (Math.abs(number) >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(number) >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
  if (Math.abs(number) >= 1_000) return `${(number / 1_000).toFixed(1)}k`;
  return Math.round(number).toLocaleString();
}

function relativeTime(value: string | number | null): string {
  if (!value) return '—';
  const timestamp = typeof value === 'number' ? value : Date.parse(value);
  if (!Number.isFinite(timestamp)) return '—';
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  return `${Math.floor(seconds / 86400)}d`;
}

function currentWork(session: SnapshotSession, live: LiveSession | null): string {
  const active = sessionPlan(session, null, live).find((step) => step.status === 'in_progress');
  return active?.step || sessionPrompt(session) || live?.command || displaySessionId(session);
}

function title(value: string): string {
  if (value.toLowerCase() === 'prolite') return 'Pro Lite';
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function windowLabel(window: SubscriptionWindow): string {
  const minutes = window.window_minutes ?? 0;
  if (minutes >= 1440 && minutes % 1440 === 0) return `${minutes / 1440}d`;
  if (minutes >= 60 && minutes % 60 === 0) return `${minutes / 60}h`;
  return minutes ? `${minutes}m` : '';
}

function resetIn(timestampSeconds?: number | null): string {
  if (!timestampSeconds) return '—';
  const seconds = Math.max(0, timestampSeconds - Date.now() / 1000);
  if (seconds === 0) return 'now';
  if (seconds < 3600) return `${Math.ceil(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.ceil(seconds / 3600)}h`;
  return `${Math.ceil(seconds / 86400)}d`;
}

export function NodeOverview({
  snapshot,
  overview,
  organization,
  onOpenSession,
}: {
  snapshot: AgentSightSnapshot;
  overview: LiveOverview | null;
  organization: CloudOrganization | null;
  onOpenSession: (sessionId: string) => void;
}) {
  const { t } = useTranslation();
  const liveAvailable = overview !== null;
  const sessions = useMemo(() => orderedSessions(snapshot, overview), [overview, snapshot]);
  const liveRows = overview?.rows.filter(isRunningSession) ?? [];
  const running = liveRows.length;
  const stopped = sessions.filter((session) => (
    !isRecordedCaptureSession(session)
      && sessionActivityState(session, liveRowForSession(overview, session)) === 'stopped'
  )).length;
  const cpu = liveRows.reduce((total, row) => total + row.cpu_percent, 0);
  const rss = liveRows.reduce((total, row) => total + row.rss_mb, 0);
  const processes = liveRows.reduce((total, row) => total + row.processes, 0);
  const tokenTotal = overview?.total_tokens ?? snapshot.summary?.total_tokens
    ?? sessions.reduce((total, session) => total + (session.total_tokens ?? 0), 0);
  const pendingPlans = sessions.flatMap((session) => (
    isRecordedCaptureSession(session) ? [] : sessionPlan(session, null, liveRowForSession(overview, session))
      .filter((step) => step.status !== 'completed')
      .map((step) => ({ session, step, live: liveRowForSession(overview, session) }))
  ));
  const subscriptions = useMemo(() => latestSubscriptions(sessions), [sessions]);
  const matchedRawIds = new Set(sessions.map((session) => liveRowForSession(overview, session)?.session_id));
  const unmatched = (overview?.rows ?? []).filter((row) => (
    isRunningSession(row) && (!row.session_id || !matchedRawIds.has(row.session_id))
  ));

  return (
    <div className="space-y-4">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Stat label={t('overview.running')} value={liveAvailable ? String(running) : '—'}
          tone={liveAvailable ? 'emerald' : 'slate'}
          hint={liveAvailable ? t('overview.runningHint') : t('overview.liveUnavailable')} />
        <Stat label={t('overview.stopped')} value={String(stopped)} hint={t('overview.stoppedHint')} />
        <Stat label={t('overview.tokens')} value={count(tokenTotal)} hint={t('overview.tokensHint')} />
        <Stat label={t('overview.cpu')} value={liveAvailable ? `${cpu.toFixed(1)}%` : '—'}
          hint={liveAvailable ? t('overview.processHint', { count: processes }) : t('overview.liveUnavailable')} />
        <Stat label={t('overview.memory')} value={liveAvailable ? `${count(rss)} MB` : '—'}
          hint={liveAvailable ? t('overview.currentRss') : t('overview.liveUnavailable')} />
      </section>

      {(overview?.failures.length ?? 0) > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {overview?.failures.join(' · ')}
        </div>
      )}

      {!liveAvailable && (
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          {t('overview.liveUnavailableDetail')}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
            <div>
              <h2 className="font-semibold text-slate-950">{t('overview.sessions')}</h2>
              <p className="mt-0.5 text-xs text-slate-500">{t('overview.sessionsHint')}</p>
            </div>
            <span className="text-xs tabular-nums text-slate-400">{sessions.length + unmatched.length}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-5 py-2.5 font-medium">{t('overview.state')}</th>
                  <th scope="col" className="px-3 py-2.5 font-medium">{t('overview.agentProcess')}</th>
                  <th scope="col" className="px-3 py-2.5 font-medium">{t('overview.currentWork')}</th>
                  <th scope="col" className="px-3 py-2.5 text-right font-medium">{t('overview.usage')}</th>
                  <th scope="col" className="px-3 py-2.5 text-right font-medium">CPU</th>
                  <th scope="col" className="px-3 py-2.5 text-right font-medium">RSS</th>
                  <th scope="col" className="px-5 py-2.5 text-right font-medium">{t('overview.lastSeen')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sessions.map((session) => {
                  const live = liveRowForSession(overview, session);
                  const state = sessionActivityState(session, live);
                  const runningSession = state === 'running';
                  return (
                    <tr key={session.id} className="group hover:bg-blue-50/40">
                      <td className="px-5 py-3">
                        {isRecordedCaptureSession(session)
                          ? <span className="text-xs font-medium text-slate-500">{t('sessionDetail.recordedCapture')}</span>
                          : <State state={state} />}
                      </td>
                      <td className="px-3 py-3">
                        <button type="button" onClick={() => onOpenSession(session.id)}
                          className="font-semibold capitalize text-slate-900 hover:text-blue-700">
                          {isRecordedCaptureSession(session)
                            ? t('sessionDetail.recordedCapture') : session.agent_type}
                        </button>
                        <div className="max-w-44 truncate text-[11px] text-slate-400">
                          {[live?.pid ? `PID ${live.pid}` : '', session.model || displaySessionId(session)]
                            .filter(Boolean).join(' · ')}
                        </div>
                      </td>
                      <td className="max-w-[420px] px-3 py-3">
                        <button type="button" onClick={() => onOpenSession(session.id)}
                          className="block w-full truncate text-left font-medium text-slate-700 group-hover:text-slate-950">
                          {currentWork(session, live)}
                        </button>
                        <div className="truncate text-[11px] text-slate-400">
                          {sessionWorkspace(session) || live?.workspace || displaySessionId(session)}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-600">
                        {isRecordedCaptureSession(session) ? '—' : (
                          <>
                            <div>{count(session.total_tokens)}</div>
                            <div className="text-[10px] text-slate-400">
                              {tokenTotal > 0
                                ? t('overview.nodeShare', { percent: ((session.total_tokens ?? 0) / tokenTotal * 100).toFixed(1) })
                                : t('overview.notAttributed')}
                            </div>
                          </>
                        )}
                      </td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-600">
                        {runningSession ? `${live!.cpu_percent.toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-3 py-3 text-right tabular-nums text-slate-600">
                        {runningSession ? `${count(live!.rss_mb)} MB` : '—'}
                      </td>
                      <td className="px-5 py-3 text-right text-xs tabular-nums text-slate-400">
                        {relativeTime(live?.last_message_at || sessionLastMessage(session)
                          || session.end_timestamp_ms || session.start_timestamp_ms)}
                      </td>
                    </tr>
                  );
                })}
                {unmatched.map((row) => (
                  <tr key={`${row.pid}-${row.session}`} className="bg-slate-50/50">
                    <td className="px-5 py-3"><State state="running" /></td>
                    <td className="px-3 py-3 font-semibold capitalize text-slate-900">{row.agent}</td>
                    <td className="max-w-[420px] px-3 py-3">
                      <div className="truncate font-medium text-slate-700">{row.command}</div>
                      <div className="truncate text-[11px] text-slate-400">{row.workspace || `PID ${row.pid}`}</div>
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-slate-400">—</td>
                    <td className="px-3 py-3 text-right tabular-nums text-slate-600">{row.cpu_percent.toFixed(1)}%</td>
                    <td className="px-3 py-3 text-right tabular-nums text-slate-600">{count(row.rss_mb)} MB</td>
                    <td className="px-5 py-3 text-right text-xs text-slate-400">{t('overview.unmatched')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {sessions.length === 0 && unmatched.length === 0 && (
            <p className="p-10 text-center text-sm text-slate-500">{t('overview.empty')}</p>
          )}
        </section>

        <div className="space-y-4">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">{t('overview.subscriptions')}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t('overview.subscriptionsHint')}</p>
            <div className="mt-4 space-y-4">
              {subscriptions.map((subscription) => (
                <Subscription key={subscription.provider} subscription={subscription} />
              ))}
              {organization && (
                <div className="rounded-lg bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-slate-800">AgentSight</span>
                    <span className="text-xs font-medium text-slate-500">
                      {title(organization.effectivePlan)}
                    </span>
                  </div>
                  <div className={`mt-2 text-sm font-semibold ${
                    organization.effectivePlan === 'unlimited' ? 'text-emerald-700' : 'text-slate-600'
                  }`}>
                    {organization.effectivePlan === 'unlimited'
                      ? t('overview.unlimitedRemaining') : t('overview.capacityNotReported')}
                  </div>
                  <p className="mt-0.5 text-[11px] text-slate-400">{t('overview.agentSightCapacity')}</p>
                </div>
              )}
              {subscriptions.length === 0 && !organization && (
                <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">
                  {t('overview.subscriptionUnavailable')}
                </p>
              )}
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">{t('overview.plan')}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t('overview.planHint')}</p>
            <div className="mt-4 space-y-3">
              {pendingPlans.slice(0, 8).map(({ session, step, live }, index) => (
                <button key={`${session.id}-${index}`} type="button" onClick={() => onOpenSession(session.id)}
                  className="flex w-full gap-3 rounded-lg border border-slate-100 p-3 text-left hover:border-blue-200 hover:bg-blue-50/40">
                  <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${
                    step.status === 'in_progress' ? 'bg-blue-500' : 'border-2 border-slate-300'
                  }`} />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-slate-800">{step.step}</span>
                    <span className="mt-0.5 block truncate text-[11px] capitalize text-slate-400">
                      {session.agent_type} · {step.status.replace('_', ' ')}
                      {isRunningSession(live) ? ` · ${t('overview.running')}` : ''}
                    </span>
                  </span>
                </button>
              ))}
              {pendingPlans.length === 0 && (
                <p className="rounded-lg bg-slate-50 px-3 py-5 text-center text-sm text-slate-500">
                  {t('overview.noPlan')}
                </p>
              )}
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">{t('overview.resources')}</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="CPU" value={liveAvailable ? `${cpu.toFixed(1)}%` : '—'} />
              <Metric label="RSS" value={liveAvailable ? `${count(rss)} MB` : '—'} />
              <Metric label={t('overview.processes')} value={liveAvailable ? String(processes) : '—'} />
              <Metric label={t('overview.agents')}
                value={liveAvailable ? String(new Set(liveRows.map((row) => row.agent)).size) : '—'} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, hint, tone = 'slate' }: {
  label: string; value: string; hint: string; tone?: 'slate' | 'emerald';
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        {tone === 'emerald' && <span aria-hidden="true" className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />}
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold tabular-nums tracking-tight text-slate-950">{value}</div>
      <div className="mt-0.5 truncate text-[11px] text-slate-400">{hint}</div>
    </div>
  );
}

function State({ state }: { state: 'running' | 'recent' | 'stopped' }) {
  const { t } = useTranslation();
  const running = state === 'running';
  const recent = state === 'recent';
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-[11px] font-medium ${
      running ? 'bg-emerald-50 text-emerald-700'
        : recent ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-500'
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        running ? 'bg-emerald-500' : recent ? 'bg-amber-500' : 'bg-slate-400'
      }`} />
      {t(`overview.${state}`)}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 font-semibold tabular-nums text-slate-900">{value}</div>
    </div>
  );
}

export function Subscription({ subscription }: { subscription: SourceSubscription }) {
  const { t } = useTranslation();
  const windows = [subscription.primary, subscription.secondary]
    .filter((window): window is SubscriptionWindow => !!window && isCurrentSubscriptionWindow(window));
  const expired = [subscription.primary, subscription.secondary]
    .some((window) => !!window && window.used_percent != null && !isCurrentSubscriptionWindow(window));
  return (
    <div className="rounded-lg border border-slate-100 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-slate-800">{title(subscription.provider)}</span>
        <span className="text-xs font-medium text-slate-500">
          {subscription.plan_type ? title(subscription.plan_type) : subscription.limit_name || t('overview.subscription')}
        </span>
      </div>
      <div className="mt-3 space-y-3">
        {windows.map((window, index) => {
          const used = Math.min(100, Math.max(0, window.used_percent ?? 0));
          const remaining = Math.max(0, 100 - used);
          return (
            <div key={`${window.window_minutes}-${index}`}>
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>{windowLabel(window) || t('overview.usageWindow')}</span>
                <span>{t('overview.remaining', { percent: remaining.toFixed(0) })}</span>
              </div>
              <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={used}
                aria-label={`${title(subscription.provider)} ${windowLabel(window) || t('overview.usageWindow')}`}
                className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div className={`h-full rounded-full ${used >= 90 ? 'bg-red-500' : used >= 70 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  style={{ width: `${used}%` }} />
              </div>
              <div className="mt-1 text-right text-[10px] text-slate-400">
                {t('overview.resetsIn', { time: resetIn(window.resets_at) })}
              </div>
            </div>
          );
        })}
        {windows.length === 0 && subscription.credits?.unlimited && (
          <div className="text-sm font-semibold text-emerald-700">{t('overview.unlimitedRemaining')}</div>
        )}
        {windows.length === 0 && expired && !subscription.credits?.unlimited && (
          <div className="text-sm text-slate-500">{t('overview.capacityExpired')}</div>
        )}
        {windows.length === 0 && !expired && !subscription.credits?.unlimited && (
          <div className="text-sm text-slate-500">{t('overview.capacityNotReported')}</div>
        )}
      </div>
    </div>
  );
}
