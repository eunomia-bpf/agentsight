// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogView } from '@/components/log/LogView';
import { Timeline as TimelineView } from '@/components/timeline/Timeline';
import { ProcessTreeView } from '@/components/ProcessTreeView';
import { ResourceMetricsView } from '@/components/ResourceMetricsView';
import { SessionConsole } from '@/components/SessionConsole';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { ConnectionDialog } from '@/components/ConnectionDialog';
import { NodeManager } from '@/components/NodeManager';
import { Dashboard, type ViewMode } from '@/components/dashboard/Dashboard';
import {
  CloudSessionExpiredError,
  type CloudIdentity,
  type CloudNode,
  type LocalConnection,
  clearLocalConnection,
  consumeLaunchFragment,
  detectEmbeddedServer,
  exchangeCloudCode,
  exchangeLocalPairing,
  fetchCloudIdentity,
  fetchCloudNodes,
  forgetCloudNode,
  loadCloudSession,
  loadLocalConnection,
  saveLocalConnection,
  signOutCloud,
} from '@/lib/connection';
import {
  type NodeClient,
  type NodeTransport,
  directNodeClient,
  forgetDirectConnection,
  loadDirectConnections,
  probeDirectConnection,
  registerControllerNode,
  relayNodeClient,
  relayOnline,
  saveDirectConnection,
} from '@/lib/nodeClient';
import { AgentSightSnapshot } from '@/types/event';
import { displayEventsFromSnapshot } from '@/utils/eventProcessing';

type AppMode = 'loading' | 'disconnected' | 'directory' | 'live' | 'demo';

function viewModeFromPath(pathname: string): ViewMode {
  const path = pathname.replace(/\/$/, '');
  if (path === '/overview') return 'overview';
  if (path === '/logs') return 'log';
  if (path === '/tree') return 'process-tree';
  if (path === '/metrics') return 'metrics';
  if (path === '/timeline') return 'timeline';
  return 'sessions';
}

function pathForViewMode(mode: ViewMode): string {
  if (mode === 'sessions') return '/sessions';
  if (mode === 'log') return '/logs';
  if (mode === 'process-tree') return '/tree';
  if (mode === 'metrics') return '/metrics';
  if (mode === 'timeline') return '/timeline';
  return '/overview';
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

export default function Home() {
  const [snapshot, setSnapshot] = useState<AgentSightSnapshot | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('sessions');
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<AppMode>('loading');
  const [activeClient, setActiveClient] = useState<NodeClient | null>(null);
  const [identity, setIdentity] = useState<CloudIdentity | null>(null);
  const [cloudNodes, setCloudNodes] = useState<CloudNode[]>([]);
  const [directConnections, setDirectConnections] = useState<Record<string, LocalConnection>>({});
  const [relayStatus, setRelayStatus] = useState<Record<string, boolean | null>>({});
  const [nodeError, setNodeError] = useState('');
  const [nodesLoading, setNodesLoading] = useState(false);
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [embeddedMode, setEmbeddedMode] = useState(false);

  const displayEvents = useMemo(() => displayEventsFromSnapshot(snapshot), [snapshot]);
  const eventCount = displayEvents.length;
  const activeTransport: NodeTransport | null = activeClient?.transport ?? null;

  const handleCloudError = useCallback((cause: unknown, fallback: string) => {
    const message = cause instanceof Error ? cause.message : fallback;
    if (cause instanceof CloudSessionExpiredError) {
      setIdentity(null);
      setCloudNodes([]);
      setRelayStatus({});
      setNodeError('');
      setMode((current) => current === 'live' ? current : 'disconnected');
      setError(message);
      return;
    }
    setNodeError(message);
  }, []);

  const activateClient = useCallback(async (client: NodeClient) => {
    setSyncing(true);
    setError('');
    try {
      const nextSnapshot = await client.snapshot();
      setActiveClient(client);
      setSnapshot(nextSnapshot);
      setMode('live');
      setViewMode('sessions');
      setDialogOpen(false);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not reach the AgentSight Node.');
      return false;
    } finally {
      setSyncing(false);
    }
  }, []);

  const syncData = useCallback(async () => {
    if (!activeClient) return;
    setSyncing(true);
    setError('');
    try {
      setSnapshot(await activeClient.snapshot());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not refresh this Node.');
    } finally {
      setSyncing(false);
    }
  }, [activeClient]);

  const refreshRelayStatuses = useCallback(async (nodes: CloudNode[], token: string) => {
    setRelayStatus(Object.fromEntries(nodes.map((node) => [node.id, null])));
    await Promise.all(nodes.map(async (node) => {
      const online = await relayOnline(token, node.id).catch(() => false);
      setRelayStatus((current) => ({ ...current, [node.id]: online }));
    }));
  }, []);

  const refreshCloudNodes = useCallback(async (token = loadCloudSession()) => {
    if (!token) return;
    setNodesLoading(true);
    try {
      const nodes = await fetchCloudNodes(token);
      setCloudNodes(nodes);
      setNodeError('');
      void refreshRelayStatuses(nodes, token);
    } catch (cause) {
      handleCloudError(cause, 'Could not load your Nodes.');
    } finally {
      setNodesLoading(false);
    }
  }, [handleCloudError, refreshRelayStatuses]);

  const openNode = useCallback(async (nodeId: string) => {
    setLoadingNodeId(nodeId);
    setNodeError('');
    const direct = directConnections[nodeId];
    let directFailure: unknown = null;

    if (direct) {
      try {
        const client = directNodeClient(direct);
        const nextSnapshot = await client.snapshot();
        setActiveClient(client);
        setSnapshot(nextSnapshot);
        setMode('live');
        setViewMode('sessions');
        setDialogOpen(false);
        setError('');
        setLoadingNodeId(null);
        return;
      } catch (cause) {
        directFailure = cause;
      }
    }

    const token = loadCloudSession();
    const cloudNode = cloudNodes.find((node) => node.id === nodeId);
    const relay = relayStatus[nodeId];
    if (token && cloudNode && relay === true) {
      try {
        const client = relayNodeClient(cloudNode, token);
        const nextSnapshot = await client.snapshot();
        setRelayStatus((current) => ({ ...current, [nodeId]: true }));
        setActiveClient(client);
        setSnapshot(nextSnapshot);
        setMode('live');
        setViewMode('sessions');
        setDialogOpen(false);
        setError('');
        setLoadingNodeId(null);
        return;
      } catch (cause) {
        setRelayStatus((current) => ({ ...current, [nodeId]: false }));
        const relayMessage = cause instanceof Error ? cause.message : 'Controller relay is unavailable.';
        const directMessage = directFailure instanceof Error ? ` Direct failed: ${directFailure.message}` : '';
        setNodeError(`${relayMessage}${directMessage}`);
      }
    } else if (directFailure instanceof Error) {
      setNodeError(`Direct failed: ${directFailure.message} Relay is unavailable; edit the Direct URL or access key.`);
    } else if (cloudNode) {
      setNodeError(relay === null
        ? 'No Direct path is saved for this browser. Relay is still being checked; configure Direct to connect by IP or URL without relay.'
        : 'No reachable transport. Configure a Direct URL and access key, or bring Controller relay online.');
    } else {
      setNodeError('This Node is not reachable from this browser. Configure a Direct URL and access key.');
    }
    setLoadingNodeId(null);
  }, [cloudNodes, directConnections, relayStatus]);

  const connectDirect = useCallback(async (
    nodeId: string,
    endpoint: string,
    accessToken: string,
  ): Promise<boolean> => {
    setLoadingNodeId(nodeId);
    setNodeError('');
    try {
      const connection = await probeDirectConnection(endpoint, accessToken);
      if (connection.nodeId !== nodeId) {
        setNodeError(
          `That Direct URL belongs to ${connection.nodeName} (${connection.nodeId}), not the selected Node (${nodeId}).`,
        );
        return false;
      }
      const opened = await activateClient(directNodeClient(connection));
      if (!opened) return false;
      saveDirectConnection(connection);
      setDirectConnections(loadDirectConnections());
      const cloudToken = loadCloudSession();
      if (cloudToken) {
        void registerControllerNode(cloudToken, connection).catch(() => undefined);
      }
      return true;
    } catch (cause) {
      setNodeError(cause instanceof Error ? cause.message : 'Could not connect to that Direct Node URL.');
      return false;
    } finally {
      setLoadingNodeId(null);
    }
  }, [activateClient]);

  const enterDemo = useCallback(async () => {
    setSyncing(true);
    setError('');
    try {
      const response = await fetch(`${basePath}/sample-snapshot.json`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status}`);
      setSnapshot(await response.json() as AgentSightSnapshot);
      setActiveClient(null);
      setViewMode('overview');
      setMode('demo');
      setDialogOpen(false);
    } catch {
      setError('The recorded demo could not be loaded.');
      setMode(identity ? 'directory' : 'disconnected');
    } finally {
      setSyncing(false);
    }
  }, [identity]);

  const signOut = useCallback(() => {
    const token = loadCloudSession();
    const wasRelay = activeClient?.transport === 'relay';
    setIdentity(null);
    setCloudNodes([]);
    setRelayStatus({});
    setNodeError('');
    setDialogOpen(false);
    if (wasRelay) {
      setActiveClient(null);
      setSnapshot(null);
      setMode('disconnected');
    }
    void signOutCloud(token);
  }, [activeClient]);

  const forgetNode = useCallback(async (nodeId: string) => {
    const token = loadCloudSession();
    if (!token) return;
    setNodesLoading(true);
    setNodeError('');
    try {
      await forgetCloudNode(token, nodeId);
      setCloudNodes((current) => current.filter((node) => node.id !== nodeId));
      setRelayStatus((current) => {
        const next = { ...current };
        delete next[nodeId];
        return next;
      });
      if (activeClient?.nodeId === nodeId && activeClient.transport === 'relay') {
        setActiveClient(null);
        setSnapshot(null);
        setMode('directory');
      }
    } catch (cause) {
      handleCloudError(cause, 'Could not remove this Node.');
    } finally {
      setNodesLoading(false);
    }
  }, [activeClient, handleCloudError]);

  const forgetDirect = useCallback((nodeId: string) => {
    forgetDirectConnection(nodeId);
    const legacy = loadLocalConnection();
    if (legacy?.nodeId === nodeId) clearLocalConnection();
    setDirectConnections(loadDirectConnections());
  }, []);

  useEffect(() => {
    let cancelled = false;
    const initialize = async () => {
      setSyncing(true);
      try {
        const launch = consumeLaunchFragment();
        if (launch?.get('action') === 'bind') {
          const bound = await exchangeLocalPairing(launch);
          if (cancelled) return;
          setEmbeddedMode(bound.endpoint === window.location.origin);
          saveLocalConnection(bound);
          saveDirectConnection(bound);
          setDirectConnections(loadDirectConnections());
          const cloudToken = loadCloudSession();
          await activateClient(directNodeClient(bound));
          if (cloudToken) {
            try {
              setIdentity(await fetchCloudIdentity(cloudToken));
              await registerControllerNode(cloudToken, bound);
              const nodes = await fetchCloudNodes(cloudToken);
              if (!cancelled) {
                setCloudNodes(nodes);
                void refreshRelayStatuses(nodes, cloudToken);
              }
            } catch (cause) {
              handleCloudError(cause, 'Could not register this Node.');
            }
          }
          return;
        }

        const embedded = await detectEmbeddedServer();
        if (cancelled) return;
        if (embedded) {
          setEmbeddedMode(true);
          if (embedded.authorizationRequired) {
            setMode('disconnected');
            return;
          }
          await activateClient(directNodeClient(embedded.connection));
          return;
        }

        if (launch?.get('action') === 'auth-error') {
          const reason = launch.get('error') || 'sign_in_failed';
          setError(reason.endsWith('_login_not_configured')
            ? 'This sign-in provider is not configured yet.'
            : 'AgentSight sign-in failed. Please try again.');
        }

        let cloudToken = loadCloudSession();
        if (launch?.get('action') === 'auth' && launch.get('code')) {
          try {
            cloudToken = await exchangeCloudCode(launch.get('code')!);
          } catch (cause) {
            cloudToken = null;
            setError(cause instanceof Error ? cause.message : 'Sign-in failed.');
          }
        }

        const legacy = loadLocalConnection();
        if (legacy) saveDirectConnection(legacy);
        const directs = loadDirectConnections();
        setDirectConnections(directs);

        let localLoaded = false;
        if (legacy) {
          try {
            const client = directNodeClient(legacy);
            const nextSnapshot = await client.snapshot();
            if (!cancelled) {
              setActiveClient(client);
              setSnapshot(nextSnapshot);
              setMode('live');
              setViewMode('sessions');
              localLoaded = true;
            }
          } catch {
            // A saved Direct path is only an optimization. Login can recover
            // the same Node through Controller relay from a fresh network.
          }
        }

        if (cloudToken) {
          try {
            const me = await fetchCloudIdentity(cloudToken);
            if (!cancelled) setIdentity(me);
            if (legacy && localLoaded) await registerControllerNode(cloudToken, legacy);
            const nodes = await fetchCloudNodes(cloudToken);
            if (!cancelled) {
              setCloudNodes(nodes);
              void refreshRelayStatuses(nodes, cloudToken);
              if (!localLoaded) setMode('directory');
            }
          } catch (cause) {
            if (!cancelled) handleCloudError(cause, 'Sign-in failed.');
          }
        } else if (!localLoaded && !cancelled) {
          setMode('disconnected');
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : 'AgentSight could not initialize.');
          setMode(loadCloudSession() ? 'directory' : 'disconnected');
        }
      } finally {
        if (!cancelled) setSyncing(false);
      }
    };
    void initialize();
    return () => { cancelled = true; };
  }, [activateClient, handleCloudError, refreshRelayStatuses]);

  useEffect(() => { setViewMode(viewModeFromPath(window.location.pathname)); }, []);

  useEffect(() => {
    const handleLaunchFragment = () => {
      const action = new URLSearchParams(window.location.hash.slice(1)).get('action');
      if (action === 'bind' || action === 'auth' || action === 'auth-error') window.location.reload();
    };
    window.addEventListener('hashchange', handleLaunchFragment);
    return () => { window.removeEventListener('hashchange', handleLaunchFragment); };
  }, []);

  const selectViewMode = (nextMode: ViewMode) => {
    setViewMode(nextMode);
    window.history.replaceState(null, '', `${basePath}${pathForViewMode(nextMode)}`);
  };

  const isDemo = mode === 'demo';
  const isLive = mode === 'live';
  const workspaceVisible = isLive || isDemo;

  const nodeManager = identity ? (
    <NodeManager identity={identity} nodes={cloudNodes} connections={directConnections}
      relayStatus={relayStatus} activeNodeId={activeClient?.nodeId} activeTransport={activeTransport}
      loadingNodeId={loadingNodeId} loading={syncing || nodesLoading} error={nodeError}
      onOpenNode={(nodeId) => { void openNode(nodeId); }} onConnectDirect={connectDirect}
      onRefresh={() => { void refreshCloudNodes(); }}
      onForgetNode={(nodeId) => { void forgetNode(nodeId); }} onForgetDirect={forgetDirect}
      onDemo={() => { void enterDemo(); }} onSignOut={signOut} />
  ) : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      {mode === 'disconnected' && !identity && (
        <ConnectionDialog error={error || nodeError} busy={syncing}
          allowSignIn={!embeddedMode} canClose={false}
          onDemo={() => { void enterDemo(); }} />
      )}

      {identity && dialogOpen && (
        <NodeManager identity={identity} nodes={cloudNodes} connections={directConnections}
          relayStatus={relayStatus} activeNodeId={activeClient?.nodeId} activeTransport={activeTransport}
          loadingNodeId={loadingNodeId} loading={syncing || nodesLoading} error={nodeError} modal
          onClose={() => setDialogOpen(false)}
          onOpenNode={(nodeId) => { void openNode(nodeId); }} onConnectDirect={connectDirect}
          onRefresh={() => { void refreshCloudNodes(); }}
          onForgetNode={(nodeId) => { void forgetNode(nodeId); }} onForgetDirect={forgetDirect}
          onDemo={() => { void enterDemo(); }} onSignOut={signOut} />
      )}

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <a href="/" className="text-lg font-semibold tracking-tight">AgentSight</a>
            {activeClient && isLive && (
              <span className="flex min-w-0 items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-700">
                <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                <span className="max-w-48 truncate font-medium">{activeClient.nodeName}</span>
                <span className="uppercase text-slate-400">{activeClient.transport}</span>
              </span>
            )}
            {isDemo && <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700">Recorded demo</span>}
          </div>
          <div className="flex items-center gap-3">
            {identity && (
              <button type="button" onClick={() => setDialogOpen(true)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                Machines
              </button>
            )}
            {!embeddedMode && !identity && mode !== 'loading' && workspaceVisible && (
              <button type="button" onClick={() => setMode('disconnected')}
                className="text-sm font-medium text-slate-600 hover:text-slate-950">Sign in</button>
            )}
            {identity && <span className="hidden text-xs text-slate-400 sm:inline">{identity.name || identity.email}</span>}
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] px-4 py-5 sm:px-6 lg:px-8">
        {mode === 'loading' ? (
          <div className="rounded-xl border border-slate-200 bg-white p-16 text-center shadow-sm">
            <div className="mx-auto h-9 w-9 animate-spin rounded-full border-b-2 border-slate-900" />
            <p className="mt-4 text-sm text-slate-500">Opening AgentSight…</p>
          </div>
        ) : identity && mode === 'directory' ? nodeManager : workspaceVisible ? (
          <div className="space-y-4">
            <section className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <span className="font-semibold text-slate-900">
                  {isLive ? activeClient?.nodeName : 'Recorded demo'}
                </span>
                <span className="text-slate-400">{eventCount.toLocaleString()} events</span>
                {snapshot?.sessions?.length ? <span className="text-slate-400">{snapshot.sessions.length} sessions</span> : null}
                {syncing && <span className="text-blue-600">Refreshing…</span>}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <nav className="flex flex-wrap rounded-lg bg-slate-100 p-1">
                  {(['sessions', 'overview', 'timeline', 'process-tree', 'log', 'metrics'] as ViewMode[]).map((item) => (
                    <button key={item} type="button" onClick={() => selectViewMode(item)}
                      disabled={item === 'sessions' && !isLive}
                      className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition ${
                        viewMode === item ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900'
                      } disabled:cursor-not-allowed disabled:opacity-40`}>
                      {item === 'process-tree' ? 'Processes' : item === 'log' ? 'Events' : item}
                    </button>
                  ))}
                </nav>
                {isLive && (
                  <button type="button" onClick={() => { void syncData(); }} disabled={syncing}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                    Refresh
                  </button>
                )}
              </div>
            </section>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
            )}

            {snapshot ? (
              viewMode === 'sessions' && isLive ? (
                <SessionConsole snapshot={snapshot} client={activeClient} />
              ) : viewMode === 'overview' ? (
                <Dashboard snapshot={snapshot} onNavigate={selectViewMode} />
              ) : viewMode === 'log' ? (
                <LogView events={displayEvents} />
              ) : viewMode === 'timeline' ? (
                <TimelineView events={displayEvents} />
              ) : viewMode === 'process-tree' ? (
                <ProcessTreeView snapshot={snapshot} />
              ) : (
                <ResourceMetricsView samples={snapshot.resource_samples ?? []} />
              )
            ) : (
              <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-sm">
                <p className="text-slate-500">No Node data loaded.</p>
              </div>
            )}
          </div>
        ) : identity ? nodeManager : null}
      </main>
    </div>
  );
}
