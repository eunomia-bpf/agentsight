// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogView } from '@/components/log/LogView';
import { Timeline as TimelineView } from '@/components/timeline/Timeline';
import { ProcessTreeView } from '@/components/ProcessTreeView';
import { ResourceMetricsView } from '@/components/ResourceMetricsView';
import { AgentFlameView } from '@/components/AgentFlameView';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { useTranslation } from '@/i18n';
import { AgentSightSnapshot } from '@/types/event';
import { displayEventsFromSnapshot } from '@/utils/eventProcessing';

type ViewMode = 'log' | 'timeline' | 'process-tree' | 'metrics' | 'agentflame';
type AppMode = 'loading' | 'live' | 'demo';

function viewModeFromPath(pathname: string): ViewMode {
  const path = pathname.replace(/\/$/, '');
  if (path === '/logs') return 'log';
  if (path === '/tree') return 'process-tree';
  if (path === '/metrics') return 'metrics';
  if (path === '/agentflame') return 'agentflame';
  return 'timeline';
}

function pathForViewMode(mode: ViewMode): string {
  if (mode === 'log') return '/logs';
  if (mode === 'process-tree') return '/tree';
  if (mode === 'metrics') return '/metrics';
  if (mode === 'agentflame') return '/agentflame';
  return '/timeline';
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const FEATURES = [
  { img: 'demo-timeline.png', title: 'Timeline View', desc: 'LLM calls, process spawns, file ops, and network events on a unified timeline.' },
  { img: 'demo-tree.png', title: 'Process Tree', desc: 'Hierarchical process tree with AI prompts, tool calls, and file mutations.' },
  { img: 'demo-metrics.png', title: 'Resource Metrics', desc: 'Real-time CPU and memory monitoring for agent processes.' },
  { img: 'top-mode-demo.png', title: 'Live Sessions', desc: 'top-like ranked view of active agent sessions.' },
];

function DemoBanner({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between text-sm">
      <span className="text-blue-800">
        Viewing a recorded <strong>Claude Code</strong> session.{' '}
        <a href="https://github.com/eunomia-bpf/agentsight" className="underline hover:text-blue-900" target="_blank" rel="noopener noreferrer">
          Install AgentSight
        </a>{' '}to monitor your own agents.
      </span>
      <button onClick={onDismiss} className="ml-4 text-blue-400 hover:text-blue-600">&times;</button>
    </div>
  );
}

function LandingHero() {
  const [copied, setCopied] = useState(false);
  const installCmd = 'cargo install agentsight && sudo agentsight top';

  const copy = () => {
    navigator.clipboard.writeText(installCmd).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">AgentSight</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-2">
            Your local-first <code className="text-sm bg-gray-100 px-1.5 py-0.5 rounded">perf</code> / <code className="text-sm bg-gray-100 px-1.5 py-0.5 rounded">top</code> / <code className="text-sm bg-gray-100 px-1.5 py-0.5 rounded">strace</code> for AI agents
          </p>
          <p className="text-gray-500">
            See what agents actually do to your machine. Zero instrumentation required.
          </p>
        </div>

        <div className="flex justify-center mb-8">
          <div className="bg-gray-900 rounded-lg px-5 py-3 flex items-center gap-3 max-w-lg w-full">
            <code className="text-green-400 text-sm flex-1 overflow-x-auto whitespace-nowrap">$ {installCmd}</code>
            <button onClick={copy} className="text-gray-400 hover:text-white text-xs shrink-0 transition-colors">
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>

        <div className="flex justify-center gap-3 mb-12">
          <a href="https://github.com/eunomia-bpf/agentsight" target="_blank" rel="noopener noreferrer"
            className="px-5 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-medium">
            GitHub
          </a>
          <a href="https://eunomia.dev/agentsight/" target="_blank" rel="noopener noreferrer"
            className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
            Documentation
          </a>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map(f => (
            <div key={f.img} className="bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
              <img src={`${basePath}/images/${f.img}`} alt={f.title} className="w-full h-36 object-cover object-top" loading="lazy" />
              <div className="p-3">
                <h3 className="font-semibold text-sm text-gray-900">{f.title}</h3>
                <p className="text-xs text-gray-500 mt-1">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-10">
          <p className="text-sm text-gray-400">Interactive demo below — a real recorded Claude Code session</p>
          <div className="mt-2 text-gray-300">&#8595;</div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const { t } = useTranslation();
  const [snapshot, setSnapshot] = useState<AgentSightSnapshot | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string>('');
  const [mode, setMode] = useState<AppMode>('loading');
  const [bannerDismissed, setBannerDismissed] = useState(false);

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
      // No backend — load static demo snapshot
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
      {isDemo && <LandingHero />}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {!isDemo && (
          <div className="text-center mb-8">
            <div className="flex justify-end mb-4">
              <LanguageSwitcher />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('app.title')}</h1>
            <p className="text-gray-600">{t('app.subtitle')}</p>
          </div>
        )}

        {isDemo && !bannerDismissed && <DemoBanner onDismiss={() => setBannerDismissed(true)} />}

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
                  {(['log', 'timeline', 'process-tree', 'metrics', 'agentflame'] as ViewMode[]).map(m => (
                    <button key={m} onClick={() => selectViewMode(m)}
                      className={`px-3 py-1 text-sm rounded-md transition-colors ${
                        viewMode === m ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                      }`}>
                      {m === 'log' ? t('app.logView')
                        : m === 'timeline' ? t('app.timelineView')
                        : m === 'process-tree' ? t('app.processTree')
                        : m === 'metrics' ? t('app.metrics')
                        : t('app.agentFlame')}
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

          {viewMode === 'agentflame' ? (
            <AgentFlameView basePath={basePath} snapshot={snapshot} />
          ) : eventCount > 0 ? (
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
