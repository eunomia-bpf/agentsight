// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ProcessTreeView } from '@/components/ProcessTreeView';
import { SessionAnalysis } from '@/components/SessionAnalysis';
import { SessionConsole } from '@/components/SessionConsole';
import { type NodeClient, type SessionDetail } from '@/lib/nodeClient';
import { useTranslation } from '@/i18n';
import type { AgentSightSnapshot, CodingPlanStep, LiveOverview, SnapshotSession } from '@/types/event';
import { displayEventsFromSnapshot } from '@/utils/eventProcessing';
import {
  displaySessionId,
  isRunningSession,
  isRecordedCaptureSession,
  liveRowForSession,
  rawSessionId,
  recordedSessionDetail,
  sessionActivityState,
  sessionPlan,
  sessionPrompt,
  sessionSnapshot,
  sessionWorkspace,
} from '@/utils/sessionData';

type SessionTab = 'conversation' | 'process' | 'analysis';

function compact(value: number | null | undefined): string {
  const number = value ?? 0;
  if (number >= 1_000_000_000) return `${(number / 1_000_000_000).toFixed(1)}B`;
  if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
  if (number >= 1_000) return `${(number / 1_000).toFixed(1)}k`;
  return Math.round(number).toLocaleString();
}

export function SessionWorkspace({
  snapshot,
  overview,
  session,
  client,
  onBack,
}: {
  snapshot: AgentSightSnapshot;
  overview: LiveOverview | null;
  session: SnapshotSession;
  client: NodeClient | null;
  onBack: () => void;
}) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<SessionTab>('conversation');
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const nextRequest = useRef(0);
  const activeRequest = useRef(0);
  const sessionId = rawSessionId(session);
  const recordedPrompt = sessionPrompt(session);
  const recordedWorkspace = sessionWorkspace(session);
  const recordedPlanKey = JSON.stringify(sessionPlan(session));
  const live = liveRowForSession(overview, session);
  const running = isRunningSession(live);
  const liveVersion = live?.last_message_at ?? null;
  const activityState = sessionActivityState(session, live);
  const recordedCapture = isRecordedCaptureSession(session);
  const recordedDetail = useMemo(
    () => recordedCapture ? recordedSessionDetail(snapshot, session) : null,
    [recordedCapture, session, snapshot],
  );

  const loadDetail = useCallback(async (quiet = false): Promise<SessionDetail | null> => {
    if (!client || recordedCapture) {
      const next = recordedDetail ?? {
        session_id: sessionId,
        agent_type: session.agent_type,
        model: session.model,
        cwd: recordedWorkspace,
        events: {
          prompts: recordedPrompt
            ? [{ ts_ms: session.start_timestamp_ms, text: recordedPrompt, preview: recordedPrompt }]
            : [],
          plan: JSON.parse(recordedPlanKey) as CodingPlanStep[],
        },
      };
      setDetail(next);
      setDetailError('');
      return next;
    }
    if (activeRequest.current !== 0) return null;
    const request = ++nextRequest.current;
    activeRequest.current = request;
    if (!quiet) setLoading(true);
    try {
      const next = await client.session(sessionId);
      if (activeRequest.current === request) {
        setDetail(next);
        setDetailError('');
      }
      return next;
    } catch (cause) {
      if (!quiet && activeRequest.current === request) {
        setDetailError(cause instanceof Error ? cause.message : t('sessions.loadFailed'));
      }
      return null;
    } finally {
      if (activeRequest.current === request) {
        activeRequest.current = 0;
        if (!quiet) setLoading(false);
      }
    }
  }, [client, recordedCapture, recordedDetail, recordedPlanKey, recordedPrompt, recordedWorkspace,
    session.agent_type, session.model, session.start_timestamp_ms, sessionId, t]);

  useEffect(() => {
    activeRequest.current = 0;
    setDetail(null);
    setDetailError('');
    setTab('conversation');
  }, [sessionId]);

  useEffect(() => {
    void loadDetail();
  }, [client, loadDetail, sessionId]);

  useEffect(() => {
    if (client && document.visibilityState !== 'hidden') void loadDetail(true);
  }, [client, liveVersion, loadDetail]);

  const scopedSnapshot = useMemo(
    () => sessionSnapshot(snapshot, session, live, detail, overview),
    [detail, live, overview, session, snapshot],
  );
  const events = useMemo(() => displayEventsFromSnapshot(scopedSnapshot), [scopedSnapshot]);
  const plan = sessionPlan(session, detail, live);
  const currentPlan = plan.find((step) => step.status === 'in_progress');
  const peakCpu = (scopedSnapshot.resource_samples ?? [])
    .reduce((peak, sample) => Math.max(peak, sample.cpu_percent ?? 0), 0);
  const peakRss = (scopedSnapshot.resource_samples ?? [])
    .reduce((peak, sample) => Math.max(peak, sample.rss_mb ?? 0), 0);

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0">
            <button type="button" onClick={onBack}
              className="text-sm font-medium text-slate-500 hover:text-slate-950">
              ← {t('sessionDetail.back')}
            </button>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold capitalize tracking-tight text-slate-950">
                {session.agent_type}
              </h1>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-[11px] font-medium ${
                running ? 'bg-emerald-50 text-emerald-700'
                  : activityState === 'recent' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-500'
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${
                  running ? 'bg-emerald-500' : activityState === 'recent' ? 'bg-amber-500' : 'bg-slate-400'
                }`} />
                {t(`overview.${activityState}`)}
              </span>
              {session.model && <span className="text-xs text-slate-400">{session.model}</span>}
            </div>
            <p className="mt-2 max-w-3xl truncate text-sm font-medium text-slate-700">
              {currentPlan?.step || sessionPrompt(session) || live?.command || displaySessionId(session)}
            </p>
            <p className="mt-1 truncate text-xs text-slate-400">
              {sessionWorkspace(session) || live?.workspace || rawSessionId(session)}
            </p>
          </div>
          <div className="grid shrink-0 grid-cols-2 gap-2 sm:grid-cols-4">
            <Metric label={t('overview.tokens')} value={compact(session.total_tokens)} />
            <Metric label={running ? t('sessionDetail.cpuNow') : t('sessionDetail.cpuPeak')}
              value={running ? `${live!.cpu_percent.toFixed(1)}%` : peakCpu ? `${peakCpu.toFixed(1)}%` : '—'} />
            <Metric label={running ? t('sessionDetail.rssNow') : t('sessionDetail.rssPeak')}
              value={running ? `${compact(live!.rss_mb)} MB` : peakRss ? `${compact(peakRss)} MB` : '—'} />
            <Metric label={t('overview.processes')}
              value={String(running ? live!.processes : (scopedSnapshot.process_nodes?.length ?? 0))} />
          </div>
        </div>

        {plan.length > 0 && (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-400">
              {t('sessionDetail.plan')}
            </div>
            <div className="flex flex-wrap gap-2">
              {plan.map((step, index) => (
                <span key={`${step.step}-${index}`} className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs ${
                  step.status === 'completed'
                    ? 'bg-emerald-50 text-emerald-700 line-through'
                    : step.status === 'in_progress'
                      ? 'bg-blue-50 font-medium text-blue-700'
                      : 'bg-slate-100 text-slate-600'
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${
                    step.status === 'completed' ? 'bg-emerald-500'
                      : step.status === 'in_progress' ? 'bg-blue-500' : 'bg-slate-400'
                  }`} />
                  {step.step}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      <nav role="tablist" aria-label={t('sessionDetail.views')}
        className="flex gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
        {(['conversation', 'process', 'analysis'] as SessionTab[]).map((item) => (
          <button key={item} type="button" role="tab" aria-selected={tab === item}
            aria-controls={`session-panel-${item}`} onClick={() => setTab(item)}
            className={`whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === item ? 'bg-slate-950 text-white' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-950'
            }`}>
            {t(`sessionDetail.${item}`)}
          </button>
        ))}
      </nav>

      <div id={`session-panel-${tab}`} role="tabpanel">
        {tab === 'conversation' ? (
          <SessionConsole session={session} detail={detail} client={recordedCapture ? null : client} loading={loading}
            detailError={detailError} onReload={loadDetail} />
        ) : tab === 'process' ? (
          <ProcessTreeView snapshot={scopedSnapshot} />
        ) : (
          <SessionAnalysis snapshot={scopedSnapshot} session={session} detail={detail} events={events} />
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-24 rounded-lg bg-slate-50 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-0.5 font-semibold tabular-nums text-slate-900">{value}</div>
    </div>
  );
}
