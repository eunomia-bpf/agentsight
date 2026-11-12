// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { CloudNode } from '@/lib/controllerClient';
import type { NodeTransport } from '@/lib/nodeClient';
import type { LiveOverview, SourceSubscription } from '@/types/event';
import { isRunningSession } from './sessionState.mjs';

export { isRunningSession } from './sessionState.mjs';

export type FleetNodeState = 'online' | 'checking' | 'unreachable';

export interface FleetNodeSample {
  node: CloudNode;
  state: FleetNodeState;
  overview: LiveOverview | null;
  transport?: NodeTransport;
  error?: string;
  updatedAt?: number;
}

export interface FleetTotals {
  machines: number;
  online: number;
  unreachable: number;
  running: number;
  stopped: number;
  tokens: number;
  cpu: number;
  rss: number;
  processes: number;
}

export function fleetTotals(samples: FleetNodeSample[]): FleetTotals {
  return samples.reduce<FleetTotals>((total, sample) => {
    total.machines += 1;
    if (sample.state === 'online' && sample.overview) {
      total.online += 1;
      total.tokens += sample.overview.total_tokens ?? 0;
      sample.overview.rows.forEach((row) => {
        if (isRunningSession(row)) {
          total.running += 1;
          total.cpu += row.cpu_percent;
          total.rss += row.rss_mb;
          total.processes += row.processes;
        } else if (row.session_id) {
          total.stopped += 1;
        }
      });
    } else if (sample.state === 'unreachable') {
      total.unreachable += 1;
    }
    return total;
  }, {
    machines: 0, online: 0, unreachable: 0, running: 0, stopped: 0,
    tokens: 0, cpu: 0, rss: 0, processes: 0,
  });
}
function subscriptionObservedAt(subscription: SourceSubscription): number {
  const parsed = Date.parse(subscription.observed_at || '');
  return Number.isFinite(parsed) ? parsed : 0;
}

export function fleetSubscriptions(samples: FleetNodeSample[]): SourceSubscription[] {
  const latest = new Map<string, SourceSubscription>();
  samples.forEach((sample) => sample.overview?.rows.forEach((row) => {
    const subscription = row.subscription;
    if (!subscription?.provider) return;
    const current = latest.get(subscription.provider);
    if (!current || subscriptionObservedAt(subscription) > subscriptionObservedAt(current)) {
      latest.set(subscription.provider, subscription);
    }
  }));
  return Array.from(latest.values()).sort((a, b) => a.provider.localeCompare(b.provider));
}

export function filterFleetNodes(
  samples: FleetNodeSample[],
  filter: 'all' | 'running' | 'idle' | 'unreachable',
): FleetNodeSample[] {
  return samples.filter((sample) => {
    if (filter === 'all') return true;
    if (filter === 'unreachable') return sample.state === 'unreachable';
    if (sample.state !== 'online' || !sample.overview) return false;
    const running = sample.overview.rows.some(isRunningSession);
    return filter === 'running' ? running : !running;
  });
}
