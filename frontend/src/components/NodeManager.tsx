// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  CheckIcon,
  CommandLineIcon,
  ComputerDesktopIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import type { CloudNode, LocalConnection } from '@/lib/connection';
import { directCloudSyncEnabled, type NodeTransport } from '@/lib/nodeClient';
import { shouldConfigureDirect } from '@/lib/nodeOpening.mjs';
import { useTranslation } from '@/i18n';

interface NodeManagerProps {
  nodes: CloudNode[];
  connections: Record<string, LocalConnection>;
  relayStatus: Record<string, boolean | null>;
  activeNodeId?: string | null;
  activeTransport?: NodeTransport | null;
  loadingNodeId?: string | null;
  loading: boolean;
  error: string;
  modal?: boolean;
  onClose?: () => void;
  onOpenNode: (nodeId: string) => void;
  onConnectDirect: (
    nodeId: string,
    endpoint: string,
    bootstrapToken: string,
    saveToAccount: boolean,
  ) => Promise<boolean>;
  onRefresh: () => void;
  onForgetNode: (nodeId: string) => void;
  onForgetDirect: (nodeId: string) => void;
  onForgetCloudDirect: (nodeId: string) => void;
  onDemo: () => void;
  onSignOut: () => void;
}

function formatSeen(value: number, locale: string): string {
  if (!value) return 'Not reported yet';
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
  nodes,
  connections,
  relayStatus,
  activeNodeId,
  activeTransport,
  loadingNodeId,
  loading,
  error,
  modal = false,
  onClose,
  onOpenNode,
  onConnectDirect,
  onRefresh,
  onForgetNode,
  onForgetDirect,
  onForgetCloudDirect,
  onDemo,
  onSignOut,
}: NodeManagerProps) {
  const { locale, t } = useTranslation();
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');
  const [directEditorNodeId, setDirectEditorNodeId] = useState<string | null>(null);
  const [directEndpoint, setDirectEndpoint] = useState('');
  const [directBootstrapKey, setDirectBootstrapKey] = useState('');
  const [directConnecting, setDirectConnecting] = useState(false);
  const [saveToAccount, setSaveToAccount] = useState(false);

  const visibleNodes = useMemo(() => {
    const byId = new Map(nodes.map((node) => [node.id, node]));
    Object.values(connections).forEach((connection) => {
      if (!byId.has(connection.nodeId)) {
        byId.set(connection.nodeId, {
          id: connection.nodeId,
          organizationId: '',
          name: connection.nodeName,
          version: connection.version,
          connectionMode: 'direct',
          hasDirectConfig: false,
          lastRegisteredAt: 0,
          createdAt: 0,
        });
      }
    });
    return Array.from(byId.values());
  }, [connections, nodes]);

  const copyBindCommand = async () => {
    try {
      await navigator.clipboard.writeText('agentsight bind');
      setCopyState('copied');
    } catch {
      setCopyState('failed');
    }
    window.setTimeout(() => setCopyState('idle'), 1800);
  };

  const editDirect = (nodeId: string) => {
    const direct = connections[nodeId];
    const node = visibleNodes.find((item) => item.id === nodeId);
    setDirectEditorNodeId(nodeId);
    setDirectEndpoint(direct?.endpoint || '');
    setSaveToAccount(Boolean(node?.hasDirectConfig) || directCloudSyncEnabled(nodeId));
    // Saved Direct credentials are scoped capabilities. Re-pairing deliberately
    // asks for the bootstrap key again rather than persisting root authority.
    setDirectBootstrapKey('');
  };

  const closeDirectEditor = () => {
    setDirectEditorNodeId(null);
    setDirectEndpoint('');
    setDirectBootstrapKey('');
  };

  const submitDirect = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!directEditorNodeId || directConnecting) return;
    setDirectConnecting(true);
    try {
      if (await onConnectDirect(directEditorNodeId, directEndpoint, directBootstrapKey, saveToAccount)) {
        closeDirectEditor();
      }
    } finally {
      setDirectConnecting(false);
    }
  };

  const content = (
    <section className={`overflow-hidden border border-slate-200 bg-white shadow-sm ${modal ? 'rounded-2xl' : 'rounded-xl'}`}>
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{t('app.nodes')}</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">{t('nodes.title')}</h2>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={onRefresh} disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            {t('nodes.refresh')}
          </button>
          {modal && onClose && (
            <button type="button" onClick={onClose} aria-label={t('nodes.close')}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900">
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </header>

      <div className="min-w-0 space-y-5 p-5 sm:p-6">
        {error && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {error}
          </div>
        )}

        {visibleNodes.length ? (
          <div className="grid min-w-0 gap-3 md:grid-cols-2">
            {visibleNodes.map((node) => {
              const direct = connections[node.id];
              const relay = relayStatus[node.id];
              const active = activeNodeId === node.id;
              const opening = loadingNodeId === node.id;
              const online = relay === true || active;
              const cloudManaged = nodes.some((item) => item.id === node.id);
              const editingDirect = directEditorNodeId === node.id;
              const openOrConfigure = () => {
                if (shouldConfigureDirect(Boolean(direct), node.hasDirectConfig, relay === true)) editDirect(node.id);
                else onOpenNode(node.id);
              };
              return (
                <article key={node.id} className={`group relative min-w-0 overflow-hidden rounded-xl border transition ${
                  active ? 'border-slate-950 bg-slate-50' : 'border-slate-200 bg-white hover:border-slate-400'
                }`}>
                  <button type="button" onClick={openOrConfigure} disabled={loading || directConnecting}
                    className="block min-w-0 w-full p-4 text-left disabled:cursor-wait">
                    <div className="flex min-w-0 items-start justify-between gap-3 sm:gap-4">
                      <div className="flex min-w-0 flex-1 items-start gap-3">
                        <span className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                          online ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                        }`}>
                          <ComputerDesktopIcon className="h-5 w-5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex min-w-0 items-center gap-2">
                            <h3 className="truncate font-semibold text-slate-950">{node.name}</h3>
                            {online && <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />}
                          </div>
                          <p className="mt-1 truncate text-xs text-slate-500">
                            {direct ? endpointLabel(direct.endpoint) : node.id}
                            {node.version ? ` · v${node.version.replace(/^v/, '')}` : ''}
                          </p>
                        </div>
                      </div>
                      <span className={`max-w-[42%] shrink truncate rounded-full px-2 py-1 text-[11px] font-medium sm:max-w-none sm:shrink-0 sm:px-2.5 sm:text-xs ${
                        active ? 'bg-slate-950 text-white'
                          : relay === true ? 'bg-emerald-100 text-emerald-800'
                            : direct ? 'bg-blue-50 text-blue-700'
                              : relay === null ? 'bg-slate-100 text-slate-500'
                                : 'bg-slate-100 text-slate-500'
                      }`}>
                        {opening ? t('nodes.opening')
                          : active ? t('nodes.openTransport', { transport: activeTransport || '' })
                            : relay === true ? t('nodes.online')
                              : direct ? t('nodes.directSaved')
                                : relay === null ? t('nodes.checking')
                                  : t('nodes.noTransport')}
                      </span>
                    </div>

                    <div className="mt-4 flex min-w-0 flex-wrap items-center gap-2 text-xs text-slate-500">
                      {direct && <span className="rounded bg-blue-50 px-2 py-1 text-blue-700">Direct</span>}
                      {node.hasDirectConfig && (
                        <span className="rounded bg-violet-50 px-2 py-1 text-violet-700">{t('nodes.accountSavedDirect')}</span>
                      )}
                      {relay === true && <span className="rounded bg-emerald-50 px-2 py-1 text-emerald-700">{t('nodes.relay')}</span>}
                      <span className="min-w-0">{node.lastRegisteredAt
                        ? t('nodes.seen', { time: formatSeen(node.lastRegisteredAt, locale) })
                        : t('nodes.localBinding')}</span>
                    </div>
                  </button>

                  <div className="grid grid-cols-1 gap-2 border-t border-slate-100 px-4 py-3 sm:flex sm:flex-wrap sm:items-center sm:justify-end sm:gap-3 sm:py-2.5">
                    <button type="button" onClick={() => editingDirect ? closeDirectEditor() : editDirect(node.id)}
                      disabled={loading || directConnecting}
                      className="inline-flex w-full items-center justify-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 hover:text-blue-900 disabled:opacity-50 sm:w-auto sm:py-1">
                      <CommandLineIcon className="h-3.5 w-3.5 shrink-0" />
                      <span className="whitespace-nowrap">{editingDirect ? t('nodes.cancelDirect') : direct ? t('nodes.repairDirect') : t('nodes.connectDirect')}</span>
                    </button>
                    {direct && (
                      <button type="button" onClick={() => onForgetDirect(node.id)} disabled={loading || directConnecting}
                        className="w-full rounded-md px-2 py-1.5 text-center text-xs font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50 sm:w-auto sm:py-1">
                        {t('nodes.forgetDirect')}
                      </button>
                    )}
                    {node.hasDirectConfig && (
                      <button type="button" onClick={() => onForgetCloudDirect(node.id)}
                        disabled={loading || directConnecting}
                        className="w-full rounded-md px-2 py-1.5 text-xs font-medium text-slate-500 hover:text-red-700 disabled:opacity-50 sm:w-auto sm:py-1">
                        {t('nodes.removeAccountDirect')}
                      </button>
                    )}
                    {cloudManaged && (
                      <button type="button" onClick={() => {
                        if (window.confirm(t('nodes.removeOrganizationConfirm', { name: node.name }))) onForgetNode(node.id);
                      }} disabled={loading || directConnecting}
                        className="inline-flex w-full items-center justify-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium text-slate-500 hover:bg-red-50 hover:text-red-700 disabled:opacity-50 sm:w-auto sm:py-1">
                        <TrashIcon className="h-3.5 w-3.5 shrink-0" />
                        {t('nodes.remove')}
                      </button>
                    )}
                  </div>

                  {editingDirect && (
                    <form onSubmit={(event) => { void submitDirect(event); }}
                      className="min-w-0 space-y-3 border-t border-slate-100 bg-slate-50 px-4 py-4">
                      <div className="min-w-0">
                        <label className="text-xs font-medium text-slate-700" htmlFor={`direct-endpoint-${node.id}`}>{t('nodes.directUrl')}</label>
                        <input id={`direct-endpoint-${node.id}`} type="url" required value={directEndpoint}
                          onChange={(event) => setDirectEndpoint(event.target.value)}
                          placeholder="http://192.168.1.20:7395"
                          spellCheck={false} autoCapitalize="none" autoCorrect="off"
                          className="mt-1 min-w-0 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500" />
                      </div>
                      <div className="min-w-0">
                        <label className="text-xs font-medium text-slate-700" htmlFor={`direct-key-${node.id}`}>{t('nodes.bootstrapKey')}</label>
                        <input id={`direct-key-${node.id}`} type="password" required value={directBootstrapKey}
                          onChange={(event) => setDirectBootstrapKey(event.target.value)}
                          placeholder={t('nodes.bootstrapPlaceholder')}
                          spellCheck={false} autoCapitalize="none" autoCorrect="off"
                          className="mt-1 min-w-0 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 outline-none focus:border-blue-500" />
                      </div>
                      <label className="flex items-start gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs text-slate-600">
                        <input type="checkbox" checked={saveToAccount}
                          onChange={(event) => setSaveToAccount(event.target.checked)}
                          className="mt-0.5 h-4 w-4 rounded border-slate-300" />
                        <span>{t('nodes.saveAccountDirect')}</span>
                      </label>
                      <button type="submit" disabled={directConnecting || loading}
                        className="w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 sm:w-auto">
                        {directConnecting ? t('nodes.pairing') : t('nodes.pairConnect')}
                      </button>
                    </form>
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <ComputerDesktopIcon className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-3 font-medium text-slate-800">{t('nodes.emptyShort')}</p>
            <p className="mt-1 text-sm text-slate-500">{t('nodes.emptyBind')}</p>
          </div>
        )}

        <div className="flex min-w-0 flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <span className="shrink-0 rounded-lg bg-white p-2 text-slate-700 shadow-sm"><CommandLineIcon className="h-5 w-5" /></span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900">{t('nodes.addReconnect')}</p>
              <p className="mt-0.5 text-xs text-slate-500">
                {t('nodes.bindHelp')}
              </p>
            </div>
          </div>
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <code className="max-w-full overflow-x-auto rounded-lg bg-slate-950 px-3 py-2 text-sm text-white">agentsight bind</code>
            <button type="button" onClick={() => { void copyBindCommand(); }}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              {copyState === 'copied' ? <CheckIcon className="h-4 w-4" /> : <CommandLineIcon className="h-4 w-4" />}
              {copyState === 'copied' ? t('nodes.copied') : copyState === 'failed' ? t('nodes.copyFailed') : t('nodes.copy')}
            </button>
          </div>
        </div>

        <div className="flex justify-end gap-4 border-t border-slate-200 pt-4">
          <div className="flex items-center gap-4">
            <button type="button" onClick={onDemo} className="text-sm font-medium text-slate-600 hover:text-slate-950">
              {t('nodes.demo')}
            </button>
            <button type="button" onClick={onSignOut} className="text-sm font-medium text-slate-600 hover:text-slate-950">
              {t('app.signOut')}
            </button>
          </div>
        </div>
      </div>
    </section>
  );

  if (!modal) return content;
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 px-4 py-8">
      <div role="dialog" aria-modal="true" aria-label={t('nodes.title')} className="mx-auto min-w-0 max-w-5xl">
        {content}
      </div>
    </div>
  );
}
