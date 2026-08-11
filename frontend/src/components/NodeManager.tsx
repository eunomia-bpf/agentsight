// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useState } from 'react';
import {
  ArrowPathIcon,
  BoltIcon,
  ChartBarIcon,
  CheckIcon,
  CommandLineIcon,
  ComputerDesktopIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import type { CloudIdentity, CloudNode, LocalConnection } from '@/lib/connection';
import { useTranslation } from '@/i18n';

interface NodeManagerProps {
  identity: CloudIdentity;
  nodes: CloudNode[];
  connection: LocalConnection | null;
  connected: boolean;
  loading: boolean;
  error: string;
  modal?: boolean;
  onClose?: () => void;
  onRetry: () => void;
  onRefresh: () => void;
  onForgetNode: (nodeId: string) => void;
  onForgetBrowser: () => void;
  onDemo: () => void;
  onSignOut: () => void;
}

function formatRegisteredAt(value: number, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value * 1000));
}

function endpointLabel(endpoint: string): string {
  try {
    return new URL(endpoint).host;
  } catch {
    return endpoint;
  }
}

export function NodeManager({
  identity,
  nodes,
  connection,
  connected,
  loading,
  error,
  modal = false,
  onClose,
  onRetry,
  onRefresh,
  onForgetNode,
  onForgetBrowser,
  onDemo,
  onSignOut,
}: NodeManagerProps) {
  const { t, locale } = useTranslation();
  const [copied, setCopied] = useState(false);
  const currentCloudNode = connection
    ? nodes.find((node) => node.id === connection.nodeId)
    : null;
  const visibleNodes = connection && !currentCloudNode
    ? [{
      id: connection.nodeId,
      name: connection.nodeName,
      version: connection.version,
      connectionMode: 'direct' as const,
      lastRegisteredAt: 0,
      createdAt: 0,
    }, ...nodes]
    : nodes;

  const copyBindCommand = async () => {
    await navigator.clipboard.writeText('agentsight bind');
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const content = (
    <section className={`overflow-hidden border border-slate-200 bg-white shadow-sm ${modal ? 'rounded-2xl' : 'rounded-xl'}`}>
      <div className="border-b border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 px-6 py-6 text-white sm:px-8">
        <div className="flex items-start justify-between gap-5">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-sm font-semibold ring-1 ring-white/20">
                {(identity.name || identity.email).slice(0, 1).toUpperCase()}
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-200">{t('nodes.account')}</p>
                <h2 className="mt-0.5 text-2xl font-semibold">{t('nodes.title')}</h2>
              </div>
            </div>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300">
              <span className="font-medium text-white">{t('nodes.signedIn', { name: identity.name || identity.email })}</span>{' '}
              {t('nodes.cloudBoundary')}
            </p>
          </div>
          {modal && onClose && (
            <button type="button" onClick={onClose} aria-label="Close Node manager"
              className="rounded-lg p-1.5 text-slate-300 hover:bg-white/10 hover:text-white">
              <XMarkIcon className="h-6 w-6" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-7 p-6 sm:p-8">
        {error && (
          <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <ExclamationTriangleIcon className="h-5 w-5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-slate-950">{t('nodes.machinesTitle')}</h3>
              <p className="mt-1 text-sm text-slate-500">
                {t('nodes.registrationTruth')}
              </p>
            </div>
            <button type="button" onClick={onRefresh} disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
              <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              {t('nodes.refresh')}
            </button>
          </div>

          {visibleNodes.length > 0 ? (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {visibleNodes.map((node) => {
                const isCurrent = connection?.nodeId === node.id;
                const isConnected = isCurrent && connected;
                return (
                  <article key={node.id} className={`rounded-xl border p-4 ${
                    isConnected ? 'border-emerald-200 bg-emerald-50/40' : 'border-slate-200 bg-white'
                  }`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex min-w-0 gap-3">
                        <span className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                          isConnected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                        }`}>
                          <ComputerDesktopIcon className="h-5 w-5" />
                        </span>
                        <div className="min-w-0">
                          <h4 className="truncate font-semibold text-slate-950">{node.name}</h4>
                          <p className="mt-0.5 truncate text-xs text-slate-500">
                            {isCurrent ? endpointLabel(connection.endpoint) : t('nodes.direct')}
                            {node.version ? ` · v${node.version.replace(/^v/, '')}` : ''}
                            {` · ${node.id}`}
                          </p>
                        </div>
                      </div>
                      <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                        isConnected
                          ? 'bg-emerald-100 text-emerald-800'
                          : isCurrent
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-600'
                      }`}>
                        {isConnected ? t('nodes.connected') : isCurrent ? t('nodes.unreachable') : t('nodes.registered')}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3">
                      <p className="text-xs text-slate-500">
                        {isConnected
                          ? t('nodes.currentDetail')
                          : node.lastRegisteredAt
                            ? t('nodes.lastRegistered', { time: formatRegisteredAt(node.lastRegisteredAt, locale) })
                            : t('nodes.registrationUnavailable')}
                      </p>
                      <div className="flex items-center gap-3">
                        {isCurrent && !isConnected && (
                          <button type="button" onClick={onRetry} disabled={loading}
                            className="text-xs font-semibold text-blue-700 hover:text-blue-900 disabled:opacity-50">
                            {t('nodes.retry')}
                          </button>
                        )}
                        {isCurrent && isConnected && modal && onClose && (
                          <button type="button" onClick={onClose}
                            className="text-xs font-semibold text-blue-700 hover:text-blue-900">
                            {t('nodes.openDashboard')}
                          </button>
                        )}
                        <button type="button"
                          onClick={() => { if (window.confirm(t('nodes.removeConfirm', { name: node.name }))) onForgetNode(node.id); }}
                          disabled={loading}
                          className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-red-700 disabled:opacity-50">
                          <TrashIcon className="h-3.5 w-3.5" />
                          {t('nodes.remove')}
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-7 text-center">
              <ComputerDesktopIcon className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-3 font-medium text-slate-800">{t('nodes.emptyTitle')}</p>
              <p className="mt-1 text-sm text-slate-500">{t('nodes.emptyBody')}</p>
            </div>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.35fr_1fr]">
          <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-5">
            <div className="flex items-start gap-3">
              <span className="rounded-lg bg-blue-100 p-2 text-blue-700"><CommandLineIcon className="h-5 w-5" /></span>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-slate-950">{t('nodes.connectTitle')}</h3>
                <p className="mt-1 text-sm leading-5 text-slate-600">
                  {t('nodes.connectBody')}
                </p>
                <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                  <code className="min-w-0 flex-1 overflow-x-auto rounded-lg bg-slate-950 px-3 py-2.5 text-sm text-white">agentsight bind</code>
                  <button type="button" onClick={() => { void copyBindCommand(); }}
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-blue-300 bg-white px-3 py-2 text-sm font-semibold text-blue-800 hover:bg-blue-50">
                    {copied ? <CheckIcon className="h-4 w-4" /> : <CommandLineIcon className="h-4 w-4" />}
                    {copied ? t('nodes.copied') : t('nodes.copy')}
                  </button>
                </div>
                {connection && (
                  <button type="button" onClick={onForgetBrowser}
                    className="mt-3 text-xs font-medium text-slate-500 hover:text-red-700">
                    {t('nodes.forgetBrowser')}
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 p-5">
            <div className="flex items-start gap-3">
              <span className="rounded-lg bg-emerald-50 p-2 text-emerald-700"><ShieldCheckIcon className="h-5 w-5" /></span>
              <div>
                <h3 className="font-semibold text-slate-950">{t('nodes.privateTitle')}</h3>
                <p className="mt-1 text-sm leading-5 text-slate-600">
                  {t('nodes.privateBody')}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-base font-semibold text-slate-950">{t('nodes.valueTitle')}</h3>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: BoltIcon, title: t('nodes.valueActivity'), body: t('nodes.valueActivityBody') },
              { icon: ChartBarIcon, title: t('nodes.valuePerformance'), body: t('nodes.valuePerformanceBody') },
              { icon: CpuChipIcon, title: t('nodes.valueEffects'), body: t('nodes.valueEffectsBody') },
              { icon: ExclamationTriangleIcon, title: t('nodes.valueFriction'), body: t('nodes.valueFrictionBody') },
            ].map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-xl border border-slate-200 p-4">
                <Icon className="h-5 w-5 text-blue-700" />
                <h4 className="mt-3 text-sm font-semibold text-slate-900">{title}</h4>
                <p className="mt-1 text-xs leading-5 text-slate-500">{body}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-5">
          <button type="button" onClick={onDemo}
            className="text-sm font-semibold text-blue-700 hover:text-blue-900">
            {t('nodes.exploreDemo')}
          </button>
          <button type="button" onClick={onSignOut}
            className="text-sm font-medium text-slate-500 hover:text-slate-900">
            {t('nodes.signOut', { email: identity.email })}
          </button>
        </div>
      </div>
    </section>
  );

  if (!modal) return content;
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 px-4 py-8">
      <div role="dialog" aria-modal="true" aria-label="Your AgentSight Nodes" className="mx-auto max-w-5xl">
        {content}
      </div>
    </div>
  );
}
