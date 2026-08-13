// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { filterFleetNodes, fleetSubscriptions, fleetTotals } from './fleetData.ts';

const node = (id) => ({
  id, organizationId: 'org', name: id, version: '1', connectionMode: 'relay',
  hasDirectConfig: false, lastRegisteredAt: 1, createdAt: 1,
});

const sample = (id, state, overview) => ({ node: node(id), state, overview });

test('fleet totals aggregate only reachable Node overviews', () => {
  const totals = fleetTotals([
    sample('a', 'online', {
      total_tokens: 100, rows: [
        { pid: 10, processes: 2, cpu_percent: 3.5, rss_mb: 40 },
        { pid: null, processes: 0, cpu_percent: 0, rss_mb: 0, session_id: 'stopped' },
      ],
    }),
    sample('b', 'unreachable', null),
    sample('c', 'checking', null),
  ]);

  assert.deepEqual(totals, {
    machines: 3, online: 1, unreachable: 1, running: 1, stopped: 1,
    tokens: 100, cpu: 3.5, rss: 40, processes: 2,
  });
});

test('fleet subscription capacity uses the newest source observation across Nodes', () => {
  const subscription = (used, observed_at) => ({
    provider: 'codex', observed_at, primary: { used_percent: used },
  });
  const subscriptions = fleetSubscriptions([
    sample('a', 'online', { total_tokens: 0, rows: [{ subscription: subscription(80, '2026-08-13T10:00:00Z') }] }),
    sample('b', 'online', { total_tokens: 0, rows: [{ subscription: subscription(20, '2026-08-13T11:00:00Z') }] }),
  ]);

  assert.equal(subscriptions[0].primary.used_percent, 20);
});

test('fleet filters separate running, idle, and unreachable machines', () => {
  const samples = [
    sample('running', 'online', { total_tokens: 0, rows: [{ pid: 10, processes: 0 }] }),
    sample('idle', 'online', { total_tokens: 0, rows: [
      { pid: 0, processes: 1 }, { pid: null, processes: 0, session_id: 'history' },
    ] }),
    sample('offline', 'unreachable', null),
  ];

  assert.deepEqual(filterFleetNodes(samples, 'running').map((item) => item.node.id), ['running']);
  assert.deepEqual(filterFleetNodes(samples, 'idle').map((item) => item.node.id), ['idle']);
  assert.deepEqual(filterFleetNodes(samples, 'unreachable').map((item) => item.node.id), ['offline']);
});
