// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { loadLocalConnection } from '@/lib/connection';
import type { AgentSightSnapshot, SnapshotSession } from '@/types/event';

type SessionDetail = {
  session_id: string;
  agent_type: string;
  model?: string | null;
  cwd?: string | null;
  events?: {
    prompts?: Array<{ ts_ms?: number | null; preview?: string }>;
    llm_responses?: Array<{ ts_ms?: number | null; preview?: string; response_phase?: string }>;
    tools?: Array<{ ts_ms?: number | null; tool_name?: string; effect?: string; status?: string }>;
  };
};

type Message = { ts: number; kind: 'user' | 'assistant' | 'tool'; text: string };
type LocalFetchInit = RequestInit & { targetAddressSpace?: 'local' };

function sessionId(session: SnapshotSession): string | null {
  const attrs = session.attributes as { session_id?: unknown } | undefined;
  return typeof attrs?.session_id === 'string' ? attrs.session_id : null;
}

async function nodeFetch(input: string, init: RequestInit = {}) {
  try {
    return await fetch(input, { ...init, mode: 'cors', cache: 'no-store' });
  } catch (error) {
    const options: LocalFetchInit = { ...init, mode: 'cors', cache: 'no-store' };
    options.targetAddressSpace = 'local';
    try {
      return await fetch(input, options);
    } catch {
      throw error;
    }
  }
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

export function SessionConsole({ snapshot }: { snapshot: AgentSightSnapshot }) {
  const sessions = useMemo(
    () => (snapshot.sessions ?? []).filter((session) => sessionId(session)),
    [snapshot],
  );
  const [selected, setSelected] = useState<string>('');
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessions.some((session) => sessionId(session) === selected)) {
      setSelected(sessionId(sessions[0] ?? {} as SnapshotSession) ?? '');
    }
  }, [sessions, selected]);

  const loadDetail = useCallback(async () => {
    if (!selected) return;
    const connection = loadLocalConnection();
    if (!connection) return;
    const headers: HeadersInit = connection.accessToken
      ? { Authorization: `Bearer ${connection.accessToken}` }
      : {};
    const response = await nodeFetch(
      `${connection.endpoint}/api/v1/sessions/${encodeURIComponent(selected)}`,
      { headers },
    );
    if (!response.ok) throw new Error(`Session returned ${response.status}.`);
    setDetail(await response.json() as SessionDetail);
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    setDetail(null);
    setError('');
    void loadDetail().catch((cause) => {
      setError(cause instanceof Error ? cause.message : 'Could not load session.');
    });
    const timer = window.setInterval(() => {
      void loadDetail().catch(() => undefined);
    }, 2_000);
    return () => window.clearInterval(timer);
  }, [selected, loadDetail]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = message.trim();
    if (!selected || !text || busy) return;
    const connection = loadLocalConnection();
    if (!connection?.accessToken) {
      setError('Reconnect this Node with agentsight bind before sending messages.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const response = await nodeFetch(
        `${connection.endpoint}/api/v1/sessions/${encodeURIComponent(selected)}/messages`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${connection.accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: text }),
        },
      );
      if (!response.ok) {
        const body = await response.json().catch(() => ({})) as { error?: string };
        throw new Error(body.error || `Message submit failed (${response.status}).`);
      }
      setMessage('');
      window.setTimeout(() => { void loadDetail().catch(() => undefined); }, 500);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not send message.');
    } finally {
      setBusy(false);
    }
  };

  if (sessions.length === 0) return null;
  const selectedSession = sessions.find((session) => sessionId(session) === selected);
  const canSend = !!selectedSession && ['claude', 'codex', 'gemini'].includes(selectedSession.agent_type);
  const conversation = messages(detail);

  return (
    <section className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-md">
      <div className="border-b border-gray-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-gray-900">Agent sessions</h2>
        <p className="mt-1 text-xs text-gray-500">Native conversation history with direct follow-up messaging.</p>
      </div>
      <div className="grid min-h-[360px] md:grid-cols-[240px_1fr]">
        <div className="border-b border-gray-100 bg-gray-50 p-2 md:border-b-0 md:border-r">
          {sessions.map((session) => {
            const id = sessionId(session)!;
            return (
              <button key={session.id} type="button" onClick={() => setSelected(id)}
                className={`mb-1 w-full rounded-md px-3 py-2 text-left ${selected === id ? 'bg-white shadow-sm' : 'hover:bg-white'}`}>
                <div className="text-sm font-medium text-gray-900">{session.agent_type}</div>
                <div className="truncate text-xs text-gray-500">{session.model || id}</div>
              </button>
            );
          })}
        </div>
        <div className="flex min-w-0 flex-col">
          <div className="max-h-[460px] flex-1 space-y-3 overflow-y-auto p-4">
            {conversation.length === 0 && !error && (
              <p className="py-10 text-center text-sm text-gray-400">Loading conversation…</p>
            )}
            {conversation.map((item, index) => item.kind === 'tool' ? (
              <div key={`${item.ts}-${index}`} className="text-center text-xs text-gray-400">{item.text}</div>
            ) : (
              <div key={`${item.ts}-${index}`} className={`flex ${item.kind === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${
                  item.kind === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'
                }`}>
                  {item.text}
                </div>
              </div>
            ))}
          </div>
          <form onSubmit={submit} className="border-t border-gray-100 p-3">
            {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
            <div className="flex gap-2">
              <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={2}
                placeholder={canSend ? 'Send a follow-up to this session…' : 'Messaging is not supported for this agent yet.'}
                disabled={!canSend || busy}
                className="min-h-12 flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 disabled:bg-gray-50" />
              <button type="submit" disabled={!canSend || !message.trim() || busy}
                className="self-end rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">
                {busy ? 'Sending…' : 'Send'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
