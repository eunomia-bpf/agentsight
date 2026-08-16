// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { NodeRequestError, type NodeClient, type SessionDetail } from '@/lib/nodeClient';
import type { SnapshotSession } from '@/types/event';
import { useTranslation } from '@/i18n';
import { rawSessionId } from '@/utils/sessionData';

type Message = { ts: number; kind: 'user' | 'assistant'; text: string };

function messages(detail: SessionDetail | null): Message[] {
  if (!detail?.events) return [];
  return [
    ...(detail.events.prompts ?? []).map((item) => ({
      ts: item.ts_ms ?? 0,
      kind: 'user' as const,
      text: item.text || item.preview || '',
    })),
    ...(detail.events.llm_responses ?? []).map((item) => ({
      ts: item.ts_ms ?? 0,
      kind: 'assistant' as const,
      text: item.text || item.preview || '',
    })),
  ].filter((item) => item.text).sort((a, b) => a.ts - b.ts);
}

export function SessionConsole({
  session,
  detail,
  client,
  loading,
  detailError,
  onReload,
}: {
  session: SnapshotSession;
  detail: SessionDetail | null;
  client: NodeClient | null;
  loading: boolean;
  detailError: string;
  onReload: (quiet?: boolean) => Promise<SessionDetail | null>;
}) {
  const { t } = useTranslation();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [writeBlocked, setWriteBlocked] = useState('');
  const conversationRef = useRef<HTMLDivElement | null>(null);
  const stickToBottom = useRef(true);
  const refreshGeneration = useRef(0);
  const conversation = messages(detail);

  useEffect(() => {
    const element = conversationRef.current;
    if (element && stickToBottom.current) element.scrollTop = element.scrollHeight;
  }, [conversation.length, detail]);

  useEffect(() => {
    refreshGeneration.current += 1;
    setMessage('');
    setBusy(false);
    setError('');
    setWriteBlocked('');
    stickToBottom.current = true;
  }, [session.id]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = message.trim();
    if (!text || busy || !client || writeBlocked) return;
    const generation = ++refreshGeneration.current;
    const responseCount = detail?.events?.llm_responses?.length ?? 0;
    setBusy(true);
    setError('');
    try {
      await client.submitMessage(rawSessionId(session), text);
      setMessage('');
      setBusy(false);
      stickToBottom.current = true;
      for (const delay of [350, 650, 1_000, 1_500, 2_500, 4_000, 6_000, 8_000, 10_000, 12_000, 15_000]) {
        await new Promise((resolve) => window.setTimeout(resolve, delay));
        if (refreshGeneration.current !== generation) return;
        const next = await onReload(true);
        if ((next?.events?.llm_responses?.length ?? 0) > responseCount) break;
      }
    } catch (cause) {
      if (refreshGeneration.current !== generation) return;
      const reason = cause instanceof Error ? cause.message : 'Could not send message.';
      if (cause instanceof NodeRequestError
          && cause.status === 409
          && reason.includes('running outside AgentSight')) {
        setWriteBlocked(
          t('sessions.writeBlocked'),
        );
      }
      setError(reason);
    } finally {
      if (refreshGeneration.current === generation) setBusy(false);
    }
  };

  const canSend = !!client && !!detail && !writeBlocked
    && ['claude', 'codex', 'gemini'].includes(session.agent_type);

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div ref={conversationRef}
        onScroll={(event) => {
          const element = event.currentTarget;
          stickToBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 80;
        }}
        className="max-h-[680px] min-h-[460px] space-y-3 overflow-y-auto p-5">
        {loading && conversation.length === 0 && !detailError && (
          <p className="py-16 text-center text-sm text-slate-400">{t('sessions.loading')}</p>
        )}
        {!loading && !detailError && conversation.length === 0 && (
          <p className="py-16 text-center text-sm text-slate-400">{t('sessions.noConversation')}</p>
        )}
        {detailError && (
          <div className="mx-auto max-w-xl rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {detailError}
          </div>
        )}
        {conversation.map((item, index) => (
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
        {writeBlocked && (
          <p className="mb-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            {writeBlocked}
          </p>
        )}
        {error && !writeBlocked && <p className="mb-2 text-xs text-red-600">{error}</p>}
        <div className="flex gap-2">
          <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={2}
            placeholder={canSend ? t('sessions.followUp') : t('sessions.readOnly')}
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
            {busy ? t('sessions.sending') : t('sessions.send')}
          </button>
        </div>
        <p className="mt-2 text-[11px] text-slate-400">{t('sessions.sendHint')}</p>
      </form>
    </section>
  );
}
