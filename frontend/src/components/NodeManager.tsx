// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  CheckIcon,
  CommandLineIcon,
  ComputerDesktopIcon,
  SignalIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import type { CloudIdentity, CloudNode, LocalConnection } from '@/lib/connection';
import type { NodeTransport } from '@/lib/nodeClient';

interface NodeManagerProps {
  identity: CloudIdentity;
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
  onRefresh: () => void;
  onForgetNode: (nodeId: string) => void;
  onForgetDirect: (nodeId: string) => void;
  onDemo: () => void;
  onSignOut: () => void;
}

function formatSeen(value: number): string {
  if (!value) return 'Not reported yet';
  return new Intl.DateTimeFormat(undefined, {
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
  onRefresh,
  onForgetNode,
  onForgetDirect,
  onDemo,
  onSignOut,
}: NodeManagerProps) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');

  const visibleNodes = useMemo(() => {
    const byId = new Map(nodes.map((node) => [node.id, node]));
    Object.values(connections).forEach((connection) => {
      if (!byId.has(connection.nodeId)) {
        byId.set(connection.nodeId, {
          id: connection.nodeId,
          name: connection.nodeName,
          version: connection.version,
          connectionMode: 'direct',
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

  const content = (
    <section className={`overflow-hidden border border-slate-200 bg-white shadow-sm ${modal ? 'rounded-2xl' : 'rounded-xl'}`}>
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-5 py-5 sm:px-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Machines</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">AgentSight Nodes</h2>
          <p className="mt-1 text-sm text-slate-500">
            Signed in as {identity.name || identity.email}. Direct is preferred; Controller relay is the remote fallback.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={onRefresh} disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {modal && onClose && (
            <button type="button" onClick={onClose} aria-label="Close"
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900">
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </header>

      <div className="space-y-5 p-5 sm:p-6">
        {error && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {error}
          </div>
        )}

        {visibleNodes.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {visibleNodes.map((node) => {
              const direct = connections[node.id];
              const relay = relayStatus[node.id];
              const active = activeNodeId === node.id;
              const opening = loadingNodeId === node.id;
              const online = relay === true || active;
              return (
                <article key={node.id} className={`group relative rounded-xl border transition ${
                  active ? 'border-slate-950 bg-slate-50' : 'border-slate-200 bg-white hover:border-slate-400'
                }`}>
                  <button type="button" onClick={() => onOpenNode(node.id)} disabled={opening}
                    className="block w-full p-4 text-left disabled:cursor-wait">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex min-w-0 items-start gap-3">
                        <span className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                          online ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                        }`}>
                          <ComputerDesktopIcon className="h-5 w-5" />
                        </span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="truncate font-semibold text-slate-950">{node.name}</h3>
                            {online && <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />}
                          </div>
                          <p className="mt-1 truncate text-xs text-slate-500">
                            {direct ? endpointLabel(direct.endpoint) : node.id}
                            {node.version ? ` · v${node.version.replace(/^v/, '')}` : ''}
                          </p>
                        </div>
                      </div>
                      <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                        active ? 'bg-slate-950 text-white'
                          : relay === true ? 'bg-emerald-100 text-emerald-800'
                            : direct ? 'bg-blue-50 text-blue-700'
                              : relay === null ? 'bg-slate-100 text-slate-500'
                                : 'bg-slate-100 text-slate-500'
                      }`}>
                        {opening ? 'Opening…'
                          : active ? `Open · ${activeTransport}`
                            : relay === true ? 'Online'
                              : direct ? 'Direct saved'
                                : relay === null ? 'Checking…'
                                  : 'Offline'}
                      </span>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      {direct && <span className="rounded bg-blue-50 px-2 py-1 text-blue-700">Direct</span>}
                      {relay === true && <span className="rounded bg-emerald-50 px-2 py-1 text-emerald-700">Relay</span>}
                      <span>{node.lastRegisteredAt ? `Seen ${formatSeen(node.lastRegisteredAt)}` : 'Local browser binding'}</span>
                    </div>
                  </button>

                  <div className="flex items-center justify-end gap-3 border-t border-slate-100 px-4 py-2.5">
                    {direct && (
                      <button type="button" onClick={() => onForgetDirect(node.id)} disabled={loading}
                        className="text-xs font-medium text-slate-500 hover:text-slate-900 disabled:opacity-50">
                        Forget direct path
                      </button>
                    )}
                    {nodes.some((item) => item.id === node.id) && (
                      <button type="button" onClick={() => {
                        if (window.confirm(`Remove ${node.name} from this account?`)) onForgetNode(node.id);
                      }} disabled={loading}
                        className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-red-700 disabled:opacity-50">
                        <TrashIcon className="h-3.5 w-3.5" />
                        Remove
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <ComputerDesktopIcon className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-3 font-medium text-slate-800">No Nodes yet</p>
            <p className="mt-1 text-sm text-slate-500">Run the bind command on a machine where your agent runs.</p>
          </div>
        )}

        <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <span className="rounded-lg bg-white p-2 text-slate-700 shadow-sm"><CommandLineIcon className="h-5 w-5" /></span>
            <div>
              <p className="text-sm font-semibold text-slate-900">Add or reconnect a Node</p>
              <p className="mt-0.5 text-xs text-slate-500">Run once on that machine. The Node identity and access bearer survive restarts.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <code className="rounded-lg bg-slate-950 px-3 py-2 text-sm text-white">agentsight bind</code>
            <button type="button" onClick={() => { void copyBindCommand(); }}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              {copyState === 'copied' ? <CheckIcon className="h-4 w-4" /> : <CommandLineIcon className="h-4 w-4" />}
              {copyState === 'copied' ? 'Copied' : copyState === 'failed' ? 'Copy failed' : 'Copy'}
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <SignalIcon className="h-4 w-4" />
            Controller stores identity and Node metadata; runtime evidence stays on the Node.
          </div>
          <div className="flex items-center gap-4">
            <button type="button" onClick={onDemo} className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Demo
            </button>
            <button type="button" onClick={onSignOut} className="text-sm font-medium text-slate-600 hover:text-slate-950">
              Sign out
            </button>
          </div>
        </div>
      </div>
    </section>
  );

  if (!modal) return content;
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 px-4 py-8">
      <div role="dialog" aria-modal="true" aria-label="AgentSight Nodes" className="mx-auto max-w-5xl">
        {content}
      </div>
    </div>
  );
}
