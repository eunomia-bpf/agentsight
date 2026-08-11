// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogView } from '@/components/log/LogView';
import { Timeline as TimelineView } from '@/components/timeline/Timeline';
import { ProcessTreeView } from '@/components/ProcessTreeView';
import { ResourceMetricsView } from '@/components/ResourceMetricsView';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { ConnectionDialog } from '@/components/ConnectionDialog';
import { Dashboard, type ViewMode } from '@/components/dashboard/Dashboard';
import { useTranslation } from '@/i18n';
import {
  type CloudIdentity,
  type LocalConnection,
  consumeLaunchFragment,
  exchangeCloudCode,
  exchangeLocalPairing,
  fetchCloudIdentity,
  fetchLocalSnapshot,
  loadCloudSession,
  loadLocalConnection,
  registerCloudNode,
  saveLocalConnection,
  signOutCloud,
} from '@/lib/connection';
import { AgentSightSnapshot } from '@/types/event';
import { displayEventsFromSnapshot } from '@/utils/eventProcessing';

type AppMode = 'loading' | 'disconnected' | 'live' | 'demo';

function viewModeFromPath(pathname: string): ViewMode {
  const path = pathname.replace(/\/$/, '');
  if (path === '/logs') return 'log';
  if (path === '/tree') return 'process-tree';
  if (path === '/metrics') return 'metrics';
  if (path === '/timeline') return 'timeline';
  return 'overview';
}

function pathForViewMode(mode: ViewMode): string {
  if (mode === 'log') return '/logs';
  if (mode === 'process-tree') return '/tree';
  if (mode === 'metrics') return '/metrics';
  if (mode === 'timeline') return '/timeline';
  return '/overview';
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

export default function Home() {
  const { t } = useTranslation();
  const [snapshot, setSnapshot] = useState<AgentSightSnapshot | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string>('');
  const [mode, setMode] = useState<AppMode>('loading');
  const [connection, setConnection] = useState<LocalConnection | null>(null);
  const [identity, setIdentity] = useState<CloudIdentity | null>(null);

  const displayEvents = useMemo(() => displayEventsFromSnapshot(snapshot), [snapshot]);
  const eventCount = displayEvents.length;

  const loadNodeData = useCallback(async (target: LocalConnection) => {
    setSyncing(true);
    setError('');

    try {
      setSnapshot(await fetchLocalSnapshot(target));
      setMode('live');
    } catch (cause) {
      setConnection(null);
      setMode('disconnected');
      setError(cause instanceof Error ? cause.message : 'Could not reach the AgentSight Node.');
    } finally {
      setSyncing(false);
    }
  }, []);

  const syncData = useCallback(async () => {
    if (connection) await loadNodeData(connection);
  }, [connection, loadNodeData]);

  const enterDemo = useCallback(async () => {
    setSyncing(true);
    setError('');
    try {
      const response = await fetch(`${basePath}/sample-snapshot.json`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`${response.status}`);
      setSnapshot(await response.json() as AgentSightSnapshot);
      setMode('demo');
    } catch {
      setError('The recorded demo could not be loaded.');
      setMode('disconnected');
    } finally {
      setSyncing(false);
    }
  }, []);

  const signOut = useCallback(() => {
    const token = loadCloudSession();
    setIdentity(null);
    void signOutCloud(token);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const initialize = async () => {
      setSyncing(true);
      try {
        const launch = consumeLaunchFragment();
        if (launch?.get('action') === 'auth-error') {
          const reason = launch.get('error') || 'sign_in_failed';
          setError(reason.endsWith('_login_not_configured')
            ? 'This sign-in provider is not configured yet.'
            : 'AgentSight sign-in failed. Please try again.');
        }
        if (launch?.get('action') === 'bind') {
          const bound = await exchangeLocalPairing(launch);
          if (cancelled) return;
          saveLocalConnection(bound);
          setConnection(bound);
          const cloudToken = loadCloudSession();
          await loadNodeData(bound);
          if (cloudToken) {
            try {
              setIdentity(await fetchCloudIdentity(cloudToken));
              await registerCloudNode(cloudToken, bound);
            } catch (cause) {
              setError(cause instanceof Error ? cause.message : 'Could not register this Node.');
            }
          }
          return;
        }

        let cloudToken = loadCloudSession();
        if (launch?.get('action') === 'auth' && launch.get('code')) {
          cloudToken = await exchangeCloudCode(launch.get('code')!);
        }
        if (cloudToken) {
          try {
            const me = await fetchCloudIdentity(cloudToken);
            if (!cancelled) setIdentity(me);
          } catch (cause) {
            cloudToken = null;
            if (!cancelled) setError(cause instanceof Error ? cause.message : 'Sign-in failed.');
          }
        }

        const saved = loadLocalConnection();
        if (saved) {
          if (cancelled) return;
          setConnection(saved);
          await loadNodeData(saved);
          if (cloudToken) {
            try {
              await registerCloudNode(cloudToken, saved);
            } catch (cause) {
              if (!cancelled) {
                setError(cause instanceof Error ? cause.message : 'Could not register this Node.');
              }
            }
          }
        } else if (!cancelled) {
          setMode('disconnected');
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : 'AgentSight could not initialize.');
          setMode('disconnected');
        }
      } finally {
        if (!cancelled) setSyncing(false);
      }
    };
    void initialize();
    return () => { cancelled = true; };
  }, [loadNodeData]);

  useEffect(() => { setViewMode(viewModeFromPath(window.location.pathname)); }, []);

  const selectViewMode = (mode: ViewMode) => {
    setViewMode(mode);
    window.history.replaceState(null, '', `${basePath}${pathForViewMode(mode)}`);
  };

  const isDemo = mode === 'demo';
  const isLive = mode === 'live';

  return (
    <div className="min-h-screen bg-gray-50">
      {mode === 'disconnected' && (
        <ConnectionDialog error={error} busy={syncing} identity={identity}
          onDemo={() => { void enterDemo(); }} onSignOut={signOut} />
      )}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium uppercase tracking-wide text-gray-500">
                {isDemo ? 'Recorded demo' : isLive ? 'Local Node · Direct' : 'No device bound'}
              </span>
              {isDemo && (
                <a
                  href="https://agentsight.us/"
                  className="text-sm font-medium text-blue-700 hover:text-blue-900"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Product site
                </a>
              )}
            </div>
            <h1 className="text-3xl font-bold text-gray-900">{t('app.title')}</h1>
            <p className="mt-1 text-gray-600">{isDemo ? 'Explore a recorded Claude Code session.' : t('app.subtitle')}</p>
          </div>
          <div className="flex items-center justify-start gap-3 lg:justify-end">
            {identity && (
              <>
                <span className="text-sm text-slate-600" title={identity.email}>
                  Signed in as {identity.name || identity.email}
                </span>
                <button type="button" onClick={signOut}
                  className="text-sm font-medium text-slate-600 hover:text-slate-900">
                  Sign out
                </button>
              </>
            )}
            <LanguageSwitcher />
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{t('app.eventsLoaded', { count: eventCount })}</span>
                </div>
                {syncing && (
                  <div className="flex items-center text-sm text-blue-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    {t('app.syncing')}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2 lg:gap-4">
                <div className="flex flex-wrap rounded-lg border border-gray-200 p-1">
                  {(['overview', 'timeline', 'process-tree', 'log', 'metrics'] as ViewMode[]).map(m => (
                    <button key={m} onClick={() => selectViewMode(m)}
                      className={`px-3 py-1 text-sm rounded-md transition-colors ${
                        viewMode === m ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                      }`}>
                      {m === 'overview' ? t('app.overview')
                        : m === 'log' ? t('app.logView')
                        : m === 'timeline' ? t('app.timelineView')
                        : m === 'process-tree' ? t('app.processTree')
                        : t('app.metrics')}
                    </button>
                  ))}
                </div>

                {isLive && (
                  <>
                    <button onClick={syncData} disabled={syncing}
                      className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors border border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed">
                      {t('app.syncData')}
                    </button>
                    <button onClick={() => { setSnapshot(null); setError(''); }}
                      className="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors">
                      {t('app.clearData')}
                    </button>
                  </>
                )}
              </div>
            </div>

            {error && mode !== 'disconnected' && !isDemo && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {eventCount > 0 ? (
            viewMode === 'overview' ? (
              <Dashboard snapshot={snapshot} onNavigate={selectViewMode} />
            ) : viewMode === 'log' ? (
              <LogView events={displayEvents} />
            ) : viewMode === 'timeline' ? (
              <TimelineView events={displayEvents} />
            ) : viewMode === 'process-tree' ? (
              <ProcessTreeView snapshot={snapshot} />
            ) : (
              <ResourceMetricsView samples={snapshot?.resource_samples ?? []} />
            )
          ) : (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <div className="text-gray-500">
                {syncing ? (
                  <div className="flex flex-col items-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                    <p className="text-lg">{t('app.loadingEvents')}</p>
                  </div>
                ) : (
                  <>
                    <p className="text-lg mb-4">{t('app.noEventsLoaded')}</p>
                    {connection ? (
                      <button onClick={syncData}
                        className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                        {t('app.syncFromServer')}
                      </button>
                    ) : identity ? (
                      <div>
                        <p className="mb-3 text-sm">No device is bound to this browser yet.</p>
                        <code className="rounded bg-slate-950 px-3 py-2 text-sm text-white">agentsight bind</code>
                        <button onClick={() => { void enterDemo(); }}
                          className="ml-3 rounded border border-blue-300 px-3 py-2 text-sm text-blue-700 hover:bg-blue-50">
                          Explore demo
                        </button>
                      </div>
                    ) : null}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
