// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { NodeClient, SessionDetail } from '@/lib/nodeClient';
import type { AgentSightSnapshot, SnapshotSession } from '@/types/event';

type Message = { ts: number; kind: 'user' | 'assistant' | 'tool'; text: string };

function sessionId(session: SnapshotSession): string | null {
  const attrs = session.attributes as { session_id?: unknown } | undefined;
  return typeof attrs?.session_id === 'string' ? attrs.session_id : null;
}

function messages(detail: SessionDetail | null): Message[] {
  if (!detail?.events) return [];
  return [
    ...(detail.events.prompts ?? []).map((item) => ({
      ts: item.ts_ms ?? 0,
      kind: 'user' as const,
      text: item.preview ?? '',
    })),
    ...(detail.events.llm_responses ?? []).map((item) => ({
      ts: item.ts_ms ?? 0,
      kind: 'assistant' as const,
      text: item.preview ?? '',
    })),
    ...(detail.events.tools ?? []).map((item) => ({
      ts: item.ts_ms ?? 0,
      kind: 'tool' as const,
      text: [item.tool_name, item.effect, item.status].filter(Boolean).join(' · '),
    })),
  ].filter((item) => item.text).sort((a, b) => a.ts - b.ts);
}

function isActiveSession(session: SnapshotSession): boolean {
  return session.status === 'running' || session.status === 'active' || !session.end_timestamp_ms;
}

export function SessionConsole({
  snapshot,
  client,
}: {
  snapshot: AgentSightSnapshot;
  client: NodeClient | null;
}) {
  const sessions = useMemo(() => (
    [...(snapshot.sessions ?? [])]
      .filter((session) => sessionId(session))
      .sort((a, b) => Number(isActiveSession(b)) - Number(isActiveSession(a))
        || b.start_timestamp_ms - a.start_timestamp_ms)
  ), [snapshot]);
  const [selected, setSelected] = useState<string>('');
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState('');
  const conversationRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!sessions.some((session) => sessionId(session) === selected)) {
      setSelected(sessionId(sessions[0] ?? {} as SnapshotSession) ?? '');
    }
  }, [sessions, selected]);

  const loadDetail = useCallback(async (quiet = false) => {
    if (!selected || !client) return;
    if (!quiet) setLoadingDetail(true);
    try {
      setDetail(await client.session(selected));
      setError('');
    } finally {
      if (!quiet) setLoadingDetail(false);
    }
  }, [client, selected]);

  useEffect(() => {
    if (!selected || !client) return;
    setDetail(null);
    setError('');
    void loadDetail().catch((cause) => {
      setError(cause instanceof Error ? cause.message : 'Could not load session.');
    });
    const timer = window.setInterval(() => {
      void loadDetail(true).catch(() => undefined);
    }, 2_000);
    return () => window.clearInterval(timer);
  }, [selected, client, loadDetail]);

  const conversation = messages(detail);
  useEffect(() => {
    const element = conversationRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [conversation.length, detail]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = message.trim();
    if (!selected || !text || busy || !client) return;
    setBusy(true);
    setError('');
    try {
      await client.submitMessage(selected, text);
      setMessage('');
      window.setTimeout(() => { void loadDetail(true).catch(() => undefined); }, 350);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not send message.');
    } finally {
      setBusy(false);
    }
  };

  if (sessions.length === 0) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <p className="font-medium text-slate-800">No native agent sessions on this Node yet.</p>
        <p className="mt-1 text-sm text-slate-500">Claude, Codex and Gemini sessions will appear here automatically.</p>
      </section>
    );
  }

  const selectedSession = sessions.find((session) => sessionId(session) === selected);
  const canSend = !!client && !!selectedSession
    && ['claude', 'codex', 'gemini'].includes(selectedSession.agent_type);
  const selectedActive = !!selectedSession && isActiveSession(selectedSession);

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div>
          <h2 className="font-semibold text-slate-950">Sessions</h2>
          <p className="mt-0.5 text-xs text-slate-500">Conversation state from the Node, refreshed every 2 seconds.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {selectedActive && <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />}
          <span>{selectedActive ? 'Live' : 'Recorded'}</span>
          {client && <span className="rounded-full bg-slate-100 px-2 py-1 font-medium uppercase">{client.transport}</span>}
        </div>
      </div>

      <div className="grid min-h-[520px] lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-slate-50/70 p-2 lg:border-b-0 lg:border-r">
          {sessions.map((session) => {
            const id = sessionId(session)!;
            const active = isActiveSession(session);
            return (
              <button key={session.id} type="button" onClick={() => setSelected(id)}
                className={`mb-1 w-full rounded-lg px-3 py-3 text-left transition ${
                  selected === id ? 'bg-white shadow-sm ring-1 ring-slate-200' : 'hover:bg-white'
                }`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold capitalize text-slate-900">{session.agent_type}</span>
                  {active && <span className="h-2 w-2 rounded-full bg-emerald-500" />}
                </div>
                <div className="mt-1 truncate text-xs text-slate-500">{session.model || id}</div>
                {session.total_tokens ? (
                  <div className="mt-1 text-[11px] text-slate-400">{session.total_tokens.toLocaleString()} tokens</div>
                ) : null}
              </button>
            );
          })}
        </aside>

        <div className="flex min-w-0 flex-col bg-white">
          <div ref={conversationRef} className="max-h-[620px] min-h-[420px] flex-1 space-y-3 overflow-y-auto p-5">
            {!client && (
              <p className="py-16 text-center text-sm text-slate-400">Open an online Node to inspect this conversation.</p>
            )}
            {client && loadingDetail && conversation.length === 0 && !error && (
              <p className="py-16 text-center text-sm text-slate-400">Loading conversation…</p>
            )}
            {conversation.map((item, index) => item.kind === 'tool' ? (
              <div key={`${item.ts}-${index}`} className="mx-auto max-w-[90%] rounded-md bg-slate-50 px-3 py-1.5 text-center text-xs text-slate-500">
                {item.text}
              </div>
            ) : (
              <div key={`${item.ts}-${index}`} className={`flex ${item.kind === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[88%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 ${
                  item.kind === 'user'
                    ? 'rounded-br-md bg-slate-950 text-white'
                    : 'rounded-bl-md bg-slate-100 text-slate-800'
                }`}>
                  {item.text}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={submit} className="border-t border-slate-200 bg-white p-4">
            {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
            <div className="flex gap-2">
              <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={2}
                placeholder={canSend ? 'Send a follow-up to this session…' : 'This session is read-only.'}
                disabled={!canSend || busy}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey && canSend && !busy) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
                className="min-h-14 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50" />
              <button type="submit" disabled={!canSend || !message.trim() || busy}
                className="self-end rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40">
                {busy ? 'Sending…' : 'Send'}
              </button>
            </div>
            <p className="mt-2 text-[11px] text-slate-400">Enter to send · Shift+Enter for a new line</p>
          </form>
        </div>
      </div>
    </section>
  );
}
