// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { NodeOverview } from '@/components/NodeOverview';
import { SessionWorkspace } from '@/components/SessionWorkspace';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { ConnectionDialog } from '@/components/ConnectionDialog';
import { NodeManager } from '@/components/NodeManager';
import { tryNodeTransports } from '@/lib/nodeOpening.mjs';
import {
  CloudSessionExpiredError,
  type CloudIdentity,
  type CloudNode,
  type CloudOrganization,
  acceptOrganizationInvite,
  createOrganization,
  exchangeCloudCode,
  fetchCloudIdentity,
  fetchCloudNodes,
  fetchControllerDirectConfig,
  fetchOrganizations,
  forgetCloudNode,
  forgetControllerDirectConfig,
  loadCloudSession,
  registerControllerNode,
  relayOnline,
  signOutCloud,
} from '@/lib/controllerClient';
import {
  type LocalConnection,
  type NodeClient,
  type NodeTransport,
  detectEmbeddedServer,
  directNodeClient,
  forgetDirectConnection,
  loadDirectConnections,
  pairDirectNode,
  pairDirectNodeFromFragment,
  relayNodeClient,
  saveDirectConnection,
  setDirectCloudSync,
} from '@/lib/nodeClient';
import { AgentSightSnapshot, LiveOverview } from '@/types/event';
import { useTranslation } from '@/i18n';

type AppMode = 'loading' | 'disconnected' | 'directory' | 'live' | 'demo';

const ACTIVE_ORGANIZATION_KEY = 'agentsight.active-organization.v1';
const PENDING_INVITE_KEY = 'agentsight.pending-invite.v1';
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
let cachedLaunchFragment: URLSearchParams | null | undefined;

function consumeLaunchFragment(): URLSearchParams | null {
  if (cachedLaunchFragment !== undefined) return cachedLaunchFragment;
  if (!window.location.hash) return null;
  const params = new URLSearchParams(window.location.hash.slice(1));
  if (!params.get('action')) return null;
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
  cachedLaunchFragment = params;
  return params;
}

function preferredOrganization(organizations: CloudOrganization[], preferredId?: string | null) {
  if (!organizations.length) return null;
  const saved = preferredId || window.localStorage.getItem(ACTIVE_ORGANIZATION_KEY);
  return organizations.find((organization) => organization.id === saved)
    || organizations.find((organization) => organization.kind === 'personal')
    || organizations[0];
}

export default function Home() {
  const { t } = useTranslation();
  const [snapshot, setSnapshot] = useState<AgentSightSnapshot | null>(null);
  const [overview, setOverview] = useState<LiveOverview | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<AppMode>('loading');
  const [activeClient, setActiveClient] = useState<NodeClient | null>(null);
  const [identity, setIdentity] = useState<CloudIdentity | null>(null);
  const [organizations, setOrganizations] = useState<CloudOrganization[]>([]);
  const [activeOrganizationId, setActiveOrganizationId] = useState<string | null>(null);
  const [cloudNodes, setCloudNodes] = useState<CloudNode[]>([]);
  const [directConnections, setDirectConnections] = useState<Record<string, LocalConnection>>({});
  const [relayStatus, setRelayStatus] = useState<Record<string, boolean | null>>({});
  const [nodeError, setNodeError] = useState('');
  const [nodesLoading, setNodesLoading] = useState(false);
  const [loadingNodeId, setLoadingNodeId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [embeddedMode, setEmbeddedMode] = useState(false);
  const [organizationDialogOpen, setOrganizationDialogOpen] = useState(false);
  const [organizationName, setOrganizationName] = useState('');

  const eventCount = snapshot?.summary?.view_events ?? snapshot?.audit_events?.length ?? 0;
  const activeTransport: NodeTransport | null = activeClient?.transport ?? null;
  const activeOrganization = useMemo(
    () => organizations.find((organization) => organization.id === activeOrganizationId) || null,
    [activeOrganizationId, organizations],
  );

  const clearCloudState = useCallback(() => {
    setIdentity(null);
    setOrganizations([]);
    setActiveOrganizationId(null);
    setCloudNodes([]);
    setRelayStatus({});
  }, []);

  const handleCloudError = useCallback((cause: unknown, fallback: string) => {
    const message = cause instanceof Error ? cause.message : fallback;
    if (cause instanceof CloudSessionExpiredError) {
      clearCloudState();
      setNodeError('');
      setMode((current) => current === 'live' ? current : 'disconnected');
      setError(message);
      return;
    }
    setNodeError(message);
  }, [clearCloudState]);

  const activateClient = useCallback(async (client: NodeClient) => {
    setSyncing(true);
    setError('');
    try {
      const [nextSnapshot, nextOverview] = await Promise.all([
        client.snapshot(),
        client.overview().catch(() => null),
      ]);
      setActiveClient(client);
      setSnapshot(nextSnapshot);
      setOverview(nextOverview);
      setMode('live');
      const requested = new URLSearchParams(window.location.search).get('session');
      setSelectedSessionId(requested && nextSnapshot.sessions?.some((session) => session.id === requested)
        ? requested : null);
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
      const [nextSnapshot, nextOverview] = await Promise.all([
        activeClient.snapshot(),
        activeClient.overview().catch(() => null),
      ]);
      setSnapshot(nextSnapshot);
      setOverview(nextOverview);
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

  const loadCloudDirectory = useCallback(async (token: string): Promise<CloudOrganization | null> => {
    const me = await fetchCloudIdentity(token);
    let nextOrganizations = await fetchOrganizations(token);
    let selected = preferredOrganization(nextOrganizations);
    const pendingInvite = window.localStorage.getItem(PENDING_INVITE_KEY);
    if (pendingInvite) {
      const joined = await acceptOrganizationInvite(token, pendingInvite);
      window.localStorage.removeItem(PENDING_INVITE_KEY);
      nextOrganizations = await fetchOrganizations(token);
      selected = preferredOrganization(nextOrganizations, joined);
    }
    setIdentity(me);
    setOrganizations(nextOrganizations);
    setActiveOrganizationId(selected?.id || null);
    if (selected) window.localStorage.setItem(ACTIVE_ORGANIZATION_KEY, selected.id);
    return selected;
  }, []);

  const refreshCloudNodes = useCallback(async (
    token = loadCloudSession(),
    organizationId = activeOrganizationId,
  ) => {
    if (!token || !organizationId) return;
    setNodesLoading(true);
    try {
      const nodes = await fetchCloudNodes(token, organizationId);
      setCloudNodes(nodes);
      setNodeError('');
      void refreshRelayStatuses(nodes, token);
    } catch (cause) {
      handleCloudError(cause, 'Could not load this organization’s Nodes.');
    } finally {
      setNodesLoading(false);
    }
  }, [activeOrganizationId, handleCloudError, refreshRelayStatuses]);

  const openNode = useCallback(async (nodeId: string) => {
    setLoadingNodeId(nodeId);
    setNodeError('');
    const direct = directConnections[nodeId];
    const token = loadCloudSession();
    const cloudNode = cloudNodes.find((node) => node.id === nodeId);
    const relay = relayStatus[nodeId];
    const attempts = [];
    if (direct) {
      attempts.push({
        transport: 'local-direct',
        open: async () => {
          if (!await activateClient(directNodeClient(direct))) throw new Error('Local Direct path is unavailable.');
        },
      });
    }
    if (token && cloudNode?.hasDirectConfig) {
      attempts.push({
        transport: 'account-direct',
        open: async () => {
          const saved = await fetchControllerDirectConfig(token, cloudNode);
          const pairing = await pairDirectNode(saved.endpoint, saved.bootstrapToken);
          const verified = pairing.connection;
          if (verified.nodeId !== nodeId) throw new Error('Saved Direct config belongs to another Node.');
          saveDirectConnection(verified);
          setDirectConnections(loadDirectConnections());
          if (!await activateClient(directNodeClient(verified))) {
            throw new Error('Account-saved Direct path is unavailable.');
          }
        },
      });
    }
    if (token && cloudNode && relay === true) {
      attempts.push({
        transport: 'relay',
        open: async () => {
          if (!await activateClient(relayNodeClient(cloudNode, token))) {
            throw new Error('Controller relay is unavailable.');
          }
          setRelayStatus((current) => ({ ...current, [nodeId]: true }));
        },
      });
    }

    const result = await tryNodeTransports(attempts);
    if (result.transport) {
      setLoadingNodeId(null);
      return;
    }
    const relayFailure = result.failures.find(({ transport }) => transport === 'relay')?.cause;
    const directFailure = [...result.failures].reverse()
      .find(({ transport }) => transport !== 'relay')?.cause;
    if (relayFailure) {
      setRelayStatus((current) => ({ ...current, [nodeId]: false }));
      const directMessage = directFailure instanceof Error ? ` Direct failed: ${directFailure.message}` : '';
      setNodeError(`${relayFailure instanceof Error ? relayFailure.message : 'Controller relay is unavailable.'}${directMessage}`);
    } else if (directFailure instanceof Error) {
      setNodeError(`Direct failed: ${directFailure.message} Relay is unavailable; re-pair this Node to refresh its capability.`);
    } else if (cloudNode) {
      setNodeError(relay === null
        ? 'No Direct path is saved for this browser. Relay is still being checked.'
        : 'No reachable transport. Re-pair Direct or bring Controller relay online.');
    } else {
      setNodeError('This Node is not reachable from this browser. Pair it with agentsight bind.');
    }
    setLoadingNodeId(null);
  }, [activateClient, cloudNodes, directConnections, relayStatus]);

  const connectDirect = useCallback(async (
    nodeId: string,
    endpoint: string,
    bootstrapToken: string,
    saveToAccount: boolean,
  ): Promise<boolean> => {
    setLoadingNodeId(nodeId);
    setNodeError('');
    try {
      const pairing = await pairDirectNode(endpoint, bootstrapToken);
      const connection = pairing.connection;
      if (connection.nodeId !== nodeId) {
        setNodeError(`That Direct URL belongs to ${connection.nodeName} (${connection.nodeId}), not ${nodeId}.`);
        return false;
      }
      if (!await activateClient(directNodeClient(connection))) return false;
      saveDirectConnection(connection);
      setDirectConnections(loadDirectConnections());
      setDirectCloudSync(connection.nodeId, saveToAccount);
      const cloudToken = loadCloudSession();
      if (cloudToken && activeOrganizationId) {
        try {
          await registerControllerNode(
            cloudToken, activeOrganizationId, connection, pairing.bootstrapToken, saveToAccount,
          );
          if (!saveToAccount) await forgetControllerDirectConfig(cloudToken, connection.nodeId);
          await refreshCloudNodes(cloudToken, activeOrganizationId);
        } catch (cause) {
          setNodeError(`Direct connected, but account sync failed: ${
            cause instanceof Error ? cause.message : 'Controller request failed.'
          }`);
        }
      }
      return true;
    } catch (cause) {
      setNodeError(cause instanceof Error ? cause.message : 'Could not connect to that Direct Node URL.');
      return false;
    } finally {
      setLoadingNodeId(null);
    }
  }, [activateClient, activeOrganizationId, refreshCloudNodes]);

  const forgetCloudDirect = useCallback(async (nodeId: string) => {
    const token = loadCloudSession();
    if (!token) return;
    setNodesLoading(true);
    setNodeError('');
    try {
      await forgetControllerDirectConfig(token, nodeId);
      setDirectCloudSync(nodeId, false);
      setCloudNodes((current) => current.map((node) => (
        node.id === nodeId ? { ...node, hasDirectConfig: false } : node
      )));
    } catch (cause) {
      handleCloudError(cause, 'Could not remove the account-saved Direct config.');
    } finally {
      setNodesLoading(false);
    }
  }, [handleCloudError]);

  const enterDemo = useCallback(async () => {
    setSyncing(true);
    setError('');
    try {
      const response = await fetch(`${basePath}/sample-snapshot.json`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status}`);
      setSnapshot(await response.json() as AgentSightSnapshot);
      setOverview(null);
      setActiveClient(null);
      setSelectedSessionId(null);
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
    clearCloudState();
    setNodeError('');
    setDialogOpen(false);
    if (wasRelay) {
      setActiveClient(null);
      setSnapshot(null);
      setOverview(null);
      setMode('disconnected');
    }
    void signOutCloud(token);
  }, [activeClient, clearCloudState]);

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
        setOverview(null);
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
    setDirectConnections(loadDirectConnections());
  }, []);

  const switchOrganization = useCallback((organizationId: string) => {
    setActiveOrganizationId(organizationId);
    window.localStorage.setItem(ACTIVE_ORGANIZATION_KEY, organizationId);
    setCloudNodes([]);
    setRelayStatus({});
    setNodeError('');
    if (activeClient?.transport === 'relay') {
      setActiveClient(null);
      setSnapshot(null);
      setOverview(null);
      setMode('directory');
    }
    void refreshCloudNodes(loadCloudSession(), organizationId);
  }, [activeClient, refreshCloudNodes]);

  const createTeam = useCallback(async (name: string) => {
    const token = loadCloudSession();
    if (!token || !name.trim()) return;
    setNodesLoading(true);
    try {
      const organization = await createOrganization(token, name.trim());
      setOrganizations((current) => [...current, organization]);
      switchOrganization(organization.id);
      setOrganizationDialogOpen(false);
      setOrganizationName('');
    } catch (cause) {
      handleCloudError(cause, 'Could not create organization.');
    } finally {
      setNodesLoading(false);
    }
  }, [handleCloudError, switchOrganization]);

  useEffect(() => {
    let cancelled = false;
    const initialize = async () => {
      setSyncing(true);
      let localLoaded = false;
      try {
        const launch = consumeLaunchFragment();
        if (launch?.get('action') === 'invite' && launch.get('token')) {
          window.localStorage.setItem(PENDING_INVITE_KEY, launch.get('token')!);
        }

        if (launch?.get('action') === 'bind') {
          const pairing = await pairDirectNodeFromFragment(launch);
          const bound = pairing.connection;
          if (cancelled) return;
          setEmbeddedMode(bound.endpoint === window.location.origin);
          saveDirectConnection(bound);
          setDirectConnections(loadDirectConnections());
          localLoaded = await activateClient(directNodeClient(bound));
          const cloudToken = loadCloudSession();
          if (cloudToken) {
            try {
              const selected = await loadCloudDirectory(cloudToken);
              if (selected) {
                await registerControllerNode(cloudToken, selected.id, bound, pairing.bootstrapToken);
                const nodes = await fetchCloudNodes(cloudToken, selected.id);
                if (!cancelled) {
                  setCloudNodes(nodes);
                  void refreshRelayStatuses(nodes, cloudToken);
                }
              }
            } catch (cause) {
              if (!cancelled) handleCloudError(cause, 'Direct mode is active, but cloud coordination is unavailable.');
            }
          }
          return;
        }

        const embedded = await detectEmbeddedServer();
        if (cancelled) return;
        if (embedded) {
          setEmbeddedMode(true);
          if (embedded.authorizationRequired) setMode('disconnected');
          else await activateClient(directNodeClient(embedded.connection));
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

        const directs = loadDirectConnections();
        setDirectConnections(directs);
        const preferredDirect = Object.values(directs)[0];
        if (preferredDirect) {
          try {
            localLoaded = await activateClient(directNodeClient(preferredDirect));
          } catch {
            localLoaded = false;
          }
        }

        if (cloudToken) {
          try {
            const selected = await loadCloudDirectory(cloudToken);
            if (selected) {
              const nodes = await fetchCloudNodes(cloudToken, selected.id);
              if (!cancelled) {
                setCloudNodes(nodes);
                void refreshRelayStatuses(nodes, cloudToken);
              }
            }
            if (!localLoaded && !cancelled) setMode('directory');
          } catch (cause) {
            if (!cancelled) {
              handleCloudError(cause, 'Cloud coordination is unavailable.');
              if (!localLoaded) setMode(cause instanceof CloudSessionExpiredError ? 'disconnected' : 'directory');
            }
          }
        } else if (!localLoaded && !cancelled) {
          if (window.localStorage.getItem(PENDING_INVITE_KEY)) {
            setError('Sign in first to accept your AgentSight organization invitation.');
          }
          setMode('disconnected');
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : 'AgentSight could not initialize.');
          if (!localLoaded) setMode(loadCloudSession() ? 'directory' : 'disconnected');
        }
      } finally {
        if (!cancelled) setSyncing(false);
      }
    };
    void initialize();
    return () => { cancelled = true; };
  }, [activateClient, handleCloudError, loadCloudDirectory, refreshRelayStatuses]);

  useEffect(() => {
    if (mode !== 'live' || !activeClient) return;
    let cancelled = false;
    let overviewRefreshing = false;
    let snapshotRefreshing = false;
    const refreshOverview = async () => {
      if (overviewRefreshing || document.visibilityState === 'hidden') return;
      overviewRefreshing = true;
      try {
        const next = await activeClient.overview();
        if (!cancelled) setOverview(next);
      } catch {
        // Retain the last good top sample; manual refresh reports Node errors.
      } finally {
        overviewRefreshing = false;
      }
    };
    const refreshSnapshot = async () => {
      if (snapshotRefreshing || document.visibilityState === 'hidden') return;
      snapshotRefreshing = true;
      try {
        const next = await activeClient.snapshot();
        if (!cancelled) setSnapshot(next);
      } catch {
        // Keep the current session index until the next bounded refresh.
      } finally {
        snapshotRefreshing = false;
      }
    };
    const overviewTimer = window.setInterval(() => { void refreshOverview(); }, 3_000);
    const snapshotTimer = window.setInterval(() => { void refreshSnapshot(); }, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(overviewTimer);
      window.clearInterval(snapshotTimer);
    };
  }, [activeClient, mode]);

  useEffect(() => {
    const handleLaunchFragment = () => {
      const action = new URLSearchParams(window.location.hash.slice(1)).get('action');
      if (action === 'bind' || action === 'auth' || action === 'auth-error' || action === 'invite') {
        window.location.reload();
      }
    };
    window.addEventListener('hashchange', handleLaunchFragment);
    return () => { window.removeEventListener('hashchange', handleLaunchFragment); };
  }, []);

  const openSession = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    window.history.replaceState(null, '', `${basePath}/?session=${encodeURIComponent(sessionId)}`);
  };

  const closeSession = () => {
    setSelectedSessionId(null);
    window.history.replaceState(null, '', `${basePath}/`);
  };

  const isDemo = mode === 'demo';
  const isLive = mode === 'live';
  const workspaceVisible = isLive || isDemo;
  const selectedSession = snapshot?.sessions?.find((session) => session.id === selectedSessionId) ?? null;

  const nodeManager = identity ? (
    <NodeManager nodes={cloudNodes} connections={directConnections}
      relayStatus={relayStatus} activeNodeId={activeClient?.nodeId} activeTransport={activeTransport}
      loadingNodeId={loadingNodeId} loading={syncing || nodesLoading} error={nodeError}
      onOpenNode={(nodeId) => { void openNode(nodeId); }} onConnectDirect={connectDirect}
      onRefresh={() => { void refreshCloudNodes(); }}
      onForgetNode={(nodeId) => { void forgetNode(nodeId); }} onForgetDirect={forgetDirect}
      onForgetCloudDirect={(nodeId) => { void forgetCloudDirect(nodeId); }}
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
        <NodeManager nodes={cloudNodes} connections={directConnections}
          relayStatus={relayStatus} activeNodeId={activeClient?.nodeId} activeTransport={activeTransport}
          loadingNodeId={loadingNodeId} loading={syncing || nodesLoading} error={nodeError} modal
          onClose={() => setDialogOpen(false)}
          onOpenNode={(nodeId) => { void openNode(nodeId); }} onConnectDirect={connectDirect}
          onRefresh={() => { void refreshCloudNodes(); }}
          onForgetNode={(nodeId) => { void forgetNode(nodeId); }} onForgetDirect={forgetDirect}
          onForgetCloudDirect={(nodeId) => { void forgetCloudDirect(nodeId); }}
          onDemo={() => { void enterDemo(); }} onSignOut={signOut} />
      )}

      {identity && organizationDialogOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 px-4">
          <form onSubmit={(event) => {
            event.preventDefault();
            void createTeam(organizationName);
          }} className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-slate-950">{t('app.createOrganization')}</h2>
            <label htmlFor="organization-name" className="mt-4 block text-sm font-medium text-slate-700">
              {t('app.organizationName')}
            </label>
            <input id="organization-name" autoFocus required maxLength={80} value={organizationName}
              onChange={(event) => setOrganizationName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-blue-500" />
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => { setOrganizationDialogOpen(false); setOrganizationName(''); }}
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">
                {t('app.cancel')}
              </button>
              <button type="submit" disabled={nodesLoading || !organizationName.trim()}
                className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
                {nodesLoading ? t('app.creating') : t('app.create')}
              </button>
            </div>
          </form>
        </div>
      )}

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <a href="/" className="text-lg font-semibold tracking-tight">AgentSight</a>
            {identity && activeOrganization && (
              <div className="flex items-center gap-2">
                <select value={activeOrganization.id} onChange={(event) => switchOrganization(event.target.value)}
                  className="max-w-48 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700">
                  {organizations.map((organization) => (
                    <option key={organization.id} value={organization.id}>
                      {organization.name} · {organization.effectivePlan}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={() => setOrganizationDialogOpen(true)}
                  className="hidden text-xs font-medium text-slate-500 hover:text-slate-900 sm:inline">
                  {t('app.addOrganization')}
                </button>
              </div>
            )}
            {activeClient && isLive && (
              <span className="flex min-w-0 items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-700">
                <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
                <span className="max-w-48 truncate font-medium">{activeClient.nodeName}</span>
                <span className="uppercase text-slate-400">{activeClient.transport}</span>
              </span>
            )}
            {isDemo && <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700">{t('app.recordedDemo')}</span>}
          </div>
          <div className="flex items-center gap-3">
            {identity && (
              <button type="button" onClick={() => setDialogOpen(true)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                {t('app.nodes')}
              </button>
            )}
            {!embeddedMode && !identity && mode !== 'loading' && workspaceVisible && (
              <button type="button" onClick={() => setMode('disconnected')}
                className="text-sm font-medium text-slate-600 hover:text-slate-950">{t('app.signIn')}</button>
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
            <p className="mt-4 text-sm text-slate-500">{t('app.opening')}</p>
          </div>
        ) : identity && mode === 'directory' ? nodeManager : workspaceVisible ? (
          <div className="space-y-4">
            <section className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <span className="font-semibold text-slate-900">
                  {isLive ? activeClient?.nodeName : t('app.recordedDemo')}
                </span>
                <span className="text-slate-400">{t('app.eventCount', { count: eventCount.toLocaleString() })}</span>
                {snapshot?.sessions?.length ? <span className="text-slate-400">{t('app.sessionCount', { count: snapshot.sessions.length })}</span> : null}
                {syncing && <span className="text-blue-600">{t('app.refreshing')}</span>}
              </div>

              {isLive && (
                <button type="button" onClick={() => { void syncData(); }} disabled={syncing}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                  {t('nodes.refresh')}
                </button>
              )}
            </section>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
            )}

            {snapshot ? (
              selectedSession ? (
                <SessionWorkspace snapshot={snapshot} overview={overview} session={selectedSession}
                  client={activeClient} onBack={closeSession} />
              ) : (
                <NodeOverview snapshot={snapshot} overview={overview} onOpenSession={openSession} />
              )
            ) : (
              <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-sm">
                <p className="text-slate-500">{t('app.noNodeData')}</p>
              </div>
            )}
          </div>
        ) : identity ? nodeManager : null}
      </main>
    </div>
  );
}
