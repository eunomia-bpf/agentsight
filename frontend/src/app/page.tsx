// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogView } from '@/components/log/LogView';
import { Timeline as TimelineView } from '@/components/timeline/Timeline';
import { ProcessTreeView } from '@/components/ProcessTreeView';
import { ResourceMetricsView } from '@/components/ResourceMetricsView';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { useTranslation } from '@/i18n';
import { AgentSightSnapshot } from '@/types/event';
import { displayEventsFromSnapshot } from '@/utils/eventProcessing';

type ViewMode = 'log' | 'timeline' | 'process-tree' | 'metrics';
type AppMode = 'loading' | 'live' | 'demo';

function viewModeFromPath(pathname: string): ViewMode {
  const path = pathname.replace(/\/$/, '');
  if (path === '/logs') return 'log';
  if (path === '/tree') return 'process-tree';
  if (path === '/metrics') return 'metrics';
  return 'timeline';
}

function pathForViewMode(mode: ViewMode): string {
  if (mode === 'log') return '/logs';
  if (mode === 'process-tree') return '/tree';
  if (mode === 'metrics') return '/metrics';
  return '/timeline';
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

export default function Home() {
  const { t } = useTranslation();
  const [snapshot, setSnapshot] = useState<AgentSightSnapshot | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string>('');
  const [mode, setMode] = useState<AppMode>('loading');

  const displayEvents = useMemo(() => displayEventsFromSnapshot(snapshot), [snapshot]);
  const eventCount = displayEvents.length;

  const syncData = useCallback(async () => {
    setSyncing(true);
    setError('');

    try {
      const response = await fetch(`${basePath}/api/v1/snapshot?audit_limit=50000`);
      if (!response.ok) throw new Error(`${response.status}`);
      setSnapshot(await response.json() as AgentSightSnapshot);
      setMode('live');
    } catch {
      // No backend, load static demo snapshot.
      try {
        const demo = await fetch(`${basePath}/sample-snapshot.json`);
        if (demo.ok) {
          setSnapshot(await demo.json() as AgentSightSnapshot);
        }
      } catch { /* no demo data either */ }
      setMode('demo');
    } finally {
      setSyncing(false);
    }
  }, []);

  useEffect(() => { void syncData(); }, [syncData]);
  useEffect(() => { setViewMode(viewModeFromPath(window.location.pathname)); }, []);

  const selectViewMode = (mode: ViewMode) => {
    setViewMode(mode);
    window.history.replaceState(null, '', `${basePath}${pathForViewMode(mode)}`);
  };

  const isDemo = mode === 'demo';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium uppercase tracking-wide text-gray-500">
                {isDemo ? 'Recorded demo' : 'Live view'}
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
          <div className="flex justify-start lg:justify-end">
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
                  {(['log', 'timeline', 'process-tree', 'metrics'] as ViewMode[]).map(m => (
                    <button key={m} onClick={() => selectViewMode(m)}
                      className={`px-3 py-1 text-sm rounded-md transition-colors ${
                        viewMode === m ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                      }`}>
                      {m === 'log' ? t('app.logView')
                        : m === 'timeline' ? t('app.timelineView')
                        : m === 'process-tree' ? t('app.processTree')
                        : t('app.metrics')}
                    </button>
                  ))}
                </div>

                {!isDemo && (
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

            {error && !isDemo && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
                {error}
              </div>
            )}
          </div>

          {eventCount > 0 ? (
            viewMode === 'log' ? (
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
                    <button onClick={syncData}
                      className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                      {t('app.syncFromServer')}
                    </button>
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
