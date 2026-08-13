import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import {
  isCurrentSubscriptionWindow, latestSubscriptions, orderedSessions, recordedSessionDetail,
  sessionSnapshot, sessionSubscription, sessionToolCallCount, sessionUsage, snapshotSessions,
} from './sessionData.ts';

const selected = {
  id: 'session-one', agent_type: 'codex', start_timestamp_ms: 100,
  end_timestamp_ms: 200, total_tokens: 10,
  attributes: { session_id: 'raw-one' },
};

function fixture(sessions = [selected, { ...selected, id: 'session-two' }]) {
  return {
    summary: {}, sessions,
    tool_calls: [{ id: 'tool-one', session_id: 'raw-one', timestamp_ms: 150, related_pid: 10 }],
    process_nodes: [
      { id: 'selected-process', pid: 10, root_pid: 10, start_timestamp_ms: 90, end_timestamp_ms: 210 },
      { id: 'foreign-process', pid: 20, root_pid: 20, start_timestamp_ms: 90, end_timestamp_ms: 210 },
    ],
    audit_events: [
      { id: 'selected-event', timestamp_ms: 150, audit_type: 'file', pid: 10 },
      { id: 'reused-pid', timestamp_ms: 250, audit_type: 'file', pid: 10 },
      { id: 'foreign-event', timestamp_ms: 150, audit_type: 'file', pid: 20 },
    ],
    resource_samples: [
      { timestamp_ms: 150, pid: 10, cpu_percent: 2 },
      { timestamp_ms: 250, pid: 10, cpu_percent: 9 },
      { timestamp_ms: 150, pid: 20, cpu_percent: 8 },
    ],
    network_targets: [
      { pid: 10, host: 'selected.example', first_timestamp_ms: 120, last_timestamp_ms: 180 },
      { pid: 10, host: 'reused.example', first_timestamp_ms: 220, last_timestamp_ms: 250 },
      { pid: 20, host: 'foreign.example', first_timestamp_ms: 120, last_timestamp_ms: 180 },
    ],
  };
}

test('session subscription exposes only source-native account capacity metadata', () => {
  assert.deepEqual(sessionSubscription({
    ...selected,
    attributes: {
      ...selected.attributes,
      subscription: {
        provider: 'codex', plan_type: 'pro',
        primary: { used_percent: 77, window_minutes: 10080, resets_at: 1787196841 },
      },
    },
  }), {
    provider: 'codex', plan_type: 'pro',
    primary: { used_percent: 77, window_minutes: 10080, resets_at: 1787196841 },
  });
  assert.equal(sessionSubscription({ ...selected, attributes: { subscription: { used_percent: 1 } } }), null);
});

test('subscription capacity uses the newest source observation and expires after reset', () => {
  const olderRunning = {
    ...selected, id: 'old', end_timestamp_ms: null,
    attributes: { subscription: { provider: 'codex', observed_at: '2026-08-13T09:00:00Z', primary: { used_percent: 10 } } },
  };
  const newerStopped = {
    ...selected, id: 'new',
    attributes: { subscription: { provider: 'codex', observed_at: '2026-08-13T10:00:00Z', primary: { used_percent: 90 } } },
  };
  assert.equal(latestSubscriptions([olderRunning, newerStopped])[0].primary.used_percent, 90);
  assert.equal(isCurrentSubscriptionWindow({ used_percent: 90, resets_at: 100 }, 101), false);
  assert.equal(isCurrentSubscriptionWindow({ used_percent: 90, resets_at: 102 }, 101), true);
});

test('session usage keeps cache tokens for analysis without a hydrated transcript', () => {
  assert.deepEqual(sessionUsage({
    ...selected,
    attributes: { usage: { input_tokens: 3, output_tokens: 4, cache_read_tokens: 20, total_tokens: 27 } },
  }), { input_tokens: 3, output_tokens: 4, cache_read_tokens: 20, total_tokens: 27 });
});

test('session tool-call count prefers the complete aggregate over bounded detail events', () => {
  assert.equal(sessionToolCallCount({ tools: { exec: 1_600, wait: 1_400 }, events: { tools: Array(2_000).fill({}) } }, 9), 3_000);
});

test('session snapshot keeps only explicitly linked rows inside the session time window', () => {
  const scoped = sessionSnapshot(fixture(), selected, null, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['selected-process']);
  assert.deepEqual(scoped.audit_events.map((row) => row.id), ['selected-event']);
  assert.deepEqual(scoped.resource_samples.map((row) => row.cpu_percent), [2]);
  assert.deepEqual(scoped.network_targets.map((row) => row.host), ['selected.example']);
});

test('a one-session snapshot does not claim unrelated process evidence', () => {
  const snapshot = fixture([selected]);
  snapshot.tool_calls = [];
  const scoped = sessionSnapshot(snapshot, selected, null, null);

  assert.equal(scoped.process_nodes.length, 1);
  assert.match(scoped.process_nodes[0].id, /^session-/);
  assert.equal(scoped.audit_events.length, 0);
  assert.equal(scoped.resource_samples.length, 0);
  assert.equal(scoped.network_targets.length, 0);
});

test('session evidence is constrained to the selected PID incarnation', () => {
  const pidReuseSession = { ...selected, end_timestamp_ms: 300 };
  const snapshot = fixture([pidReuseSession]);
  snapshot.tool_calls[0].timestamp_ms = 250;
  snapshot.process_nodes = [
    { id: 'old-pid', pid: 10, root_pid: 10, start_timestamp_ms: 100, end_timestamp_ms: 180 },
    { id: 'selected-pid', pid: 10, root_pid: 10, start_timestamp_ms: 200, end_timestamp_ms: 300 },
  ];
  snapshot.audit_events = [
    { id: 'before-process', timestamp_ms: 150, audit_type: 'file', pid: 10 },
    { id: 'during-process', timestamp_ms: 250, audit_type: 'file', pid: 10 },
  ];
  snapshot.resource_samples = [
    { timestamp_ms: 150, pid: 10, cpu_percent: 1 },
    { timestamp_ms: 250, pid: 10, cpu_percent: 2 },
  ];
  snapshot.network_targets = [
    { pid: 10, host: 'before.example', first_timestamp_ms: 120, last_timestamp_ms: 160 },
    { pid: 10, host: 'during.example', first_timestamp_ms: 220, last_timestamp_ms: 260 },
    { pid: 10, host: 'crosses-incarnations.example', first_timestamp_ms: 170, last_timestamp_ms: 220 },
  ];

  const scoped = sessionSnapshot(snapshot, pidReuseSession, null, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['selected-pid']);
  assert.deepEqual(scoped.audit_events.map((row) => row.id), ['during-process']);
  assert.deepEqual(scoped.resource_samples.map((row) => row.cpu_percent), [2]);
  assert.deepEqual(scoped.network_targets.map((row) => row.host), ['during.example']);
});

test('live session evidence uses the current captured PID incarnation', () => {
  const liveSession = { ...selected, end_timestamp_ms: null };
  const snapshot = fixture([liveSession]);
  snapshot.process_nodes = [
    { id: 'old-pid', pid: 10, root_pid: 10, start_timestamp_ms: 100, end_timestamp_ms: 180 },
    { id: 'current-pid', pid: 10, root_pid: 10, start_timestamp_ms: 200, end_timestamp_ms: null },
  ];
  snapshot.audit_events = [
    { id: 'old-event', timestamp_ms: 150, audit_type: 'file', pid: 10 },
    { id: 'current-event', timestamp_ms: 250, audit_type: 'file', pid: 10 },
  ];
  const live = {
    pid: 10,
    process_details: [{
      pid: 10, ppid: 0, start_timestamp_ms: 200, comm: 'codex', command: 'codex',
    }],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, live, null);

  assert.equal(scoped.process_nodes[0].start_timestamp_ms, 200);
  assert.deepEqual(scoped.audit_events.map((row) => row.id), ['current-event']);
});

test('live session evidence retains completed captured subprocesses', () => {
  const liveSession = { ...selected, end_timestamp_ms: null };
  const snapshot = fixture([liveSession]);
  snapshot.process_nodes = [
    { id: 'root', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 100, end_timestamp_ms: null },
    { id: 'completed-tool', pid: 11, ppid: 10, root_pid: null, start_timestamp_ms: 120, end_timestamp_ms: 160 },
  ];
  snapshot.tool_calls = [
    { id: 'native-tool', session_id: 'raw-one', timestamp_ms: 140, related_pid: null },
    { id: 'capture-tool', session_id: null, timestamp_ms: 140, related_pid: 11 },
  ];
  snapshot.audit_events = [
    { id: 'tool-file', timestamp_ms: 140, audit_type: 'file', pid: 11 },
  ];
  snapshot.resource_samples = [
    { timestamp_ms: 145, pid: 11, cpu_percent: 3 },
  ];
  const live = {
    pid: 10,
    process_details: [{
      pid: 10, ppid: 0, start_timestamp_ms: 100, comm: 'codex', command: 'codex',
    }],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, live, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['live-10', 'completed-tool']);
  assert.deepEqual(scoped.audit_events.map((row) => row.id), ['tool-file']);
  assert.deepEqual(scoped.resource_samples.map((row) => row.cpu_percent), [3]);
});

test('live and captured views do not duplicate the same running subprocess', () => {
  const liveSession = { ...selected, end_timestamp_ms: null };
  const snapshot = fixture([liveSession]);
  snapshot.process_nodes = [
    { id: 'root', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 100, end_timestamp_ms: null },
    { id: 'running-tool', pid: 11, ppid: 10, root_pid: null, start_timestamp_ms: 120, end_timestamp_ms: null },
  ];
  snapshot.tool_calls = [
    { id: 'native-tool', session_id: 'raw-one', timestamp_ms: 140, related_pid: null },
    { id: 'capture-tool', session_id: null, timestamp_ms: 140, related_pid: 11 },
  ];
  const live = {
    pid: 10,
    process_details: [
      { pid: 10, ppid: 0, start_timestamp_ms: 100, comm: 'codex', command: 'codex' },
      { pid: 11, ppid: 10, start_timestamp_ms: 120, comm: 'tool', command: 'tool' },
    ],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, live, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['live-10', 'live-11']);
});

test('live process start time rejects an old captured root when no open row exists', () => {
  const liveSession = { ...selected, end_timestamp_ms: null };
  const snapshot = fixture([liveSession]);
  snapshot.process_nodes = [
    { id: 'old-root', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 100, end_timestamp_ms: 180 },
    { id: 'old-child', pid: 11, ppid: 10, root_pid: null, start_timestamp_ms: 120, end_timestamp_ms: 160 },
  ];
  snapshot.tool_calls[0].related_pid = 11;
  snapshot.tool_calls[0].timestamp_ms = 140;
  snapshot.audit_events = [
    { id: 'old-file', timestamp_ms: 145, audit_type: 'file', pid: 11 },
  ];
  const live = {
    pid: 10,
    process_details: [{
      pid: 10, ppid: 0, start_timestamp_ms: 200, comm: 'codex', command: 'codex',
    }],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, live, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['live-10']);
  assert.deepEqual(scoped.audit_events, []);
});

test('a child that predates the current parent incarnation is not attached by overlap', () => {
  const liveSession = { ...selected, end_timestamp_ms: null };
  const snapshot = fixture([liveSession]);
  snapshot.process_nodes = [
    { id: 'old-root', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 100, end_timestamp_ms: 180 },
    { id: 'new-root', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 200, end_timestamp_ms: null },
    { id: 'overlap-child', pid: 11, ppid: 10, root_pid: null, start_timestamp_ms: 150, end_timestamp_ms: 250 },
  ];
  snapshot.tool_calls[0].related_pid = 10;
  snapshot.tool_calls[0].timestamp_ms = 220;
  snapshot.audit_events = [
    { id: 'old-child-file', timestamp_ms: 160, audit_type: 'file', pid: 11 },
  ];
  const live = {
    pid: 10,
    process_details: [{
      pid: 10, ppid: 0, start_timestamp_ms: 200, comm: 'codex', command: 'codex',
    }],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, live, null);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['live-10']);
  assert.deepEqual(scoped.audit_events, []);
});

test('a nested live root remains a boundary when capture start is missing', () => {
  const liveSession = { ...selected, start_timestamp_ms: 150, end_timestamp_ms: null };
  const nestedSession = {
    ...selected, id: 'session-two', end_timestamp_ms: null,
    attributes: { session_id: 'raw-two' },
  };
  const snapshot = fixture([liveSession, nestedSession]);
  snapshot.process_nodes = [
    { id: 'root-a', pid: 10, ppid: null, root_pid: null, start_timestamp_ms: 100, end_timestamp_ms: null },
    { id: 'root-b', pid: 20, ppid: 10, root_pid: null, start_timestamp_ms: null, end_timestamp_ms: null },
    { id: 'b-tool', pid: 21, ppid: 20, root_pid: null, start_timestamp_ms: 200, end_timestamp_ms: null },
  ];
  snapshot.tool_calls = [
    { id: 'native-b-tool', session_id: 'raw-two', timestamp_ms: 210, related_pid: null },
    { id: 'capture-b-tool', session_id: null, timestamp_ms: 210, related_pid: 21 },
  ];
  snapshot.audit_events = [
    { id: 'b-secret', timestamp_ms: 210, audit_type: 'file', pid: 21 },
  ];
  const overview = {
    rows: [
      {
        session_id: 'raw-one', session: 'session-one', pid: 10,
        process_details: [{ pid: 10, ppid: 0, start_timestamp_ms: 100 }],
      },
      {
        session_id: 'raw-two', session: 'session-two', pid: 20,
        process_details: [
          { pid: 20, ppid: 10, start_timestamp_ms: 120 },
          { pid: 21, ppid: 20, start_timestamp_ms: 130 },
        ],
      },
    ],
  };

  const scoped = sessionSnapshot(snapshot, liveSession, overview.rows[0], null, overview);

  assert.deepEqual(scoped.process_nodes.map((row) => row.id), ['live-10']);
  assert.deepEqual(scoped.audit_events, []);
});

test('the recorded demo retains a full-capture session for legacy evidence views', () => {
  const sample = JSON.parse(readFileSync(
    new URL('../../../docs/sample-snapshot.json', import.meta.url), 'utf8',
  ));
  const capture = snapshotSessions(sample, true).find((session) => session.id === 'capture:recorded');
  assert.ok(capture);

  const scoped = sessionSnapshot(sample, capture, null, recordedSessionDetail(sample, capture));

  assert.equal(scoped.process_nodes.length, sample.process_nodes.length);
  assert.equal(scoped.audit_events.length, sample.audit_events.length);
  assert.equal(scoped.resource_samples.length, sample.resource_samples.length);
  assert.equal(scoped.network_targets.length, sample.network_targets.length);
  assert.equal(scoped.tool_calls.length, sample.tool_calls.length);
});

test('live overview keeps a recorded-capture fallback for unassigned evidence', () => {
  const snapshot = fixture();
  const sessions = orderedSessions(snapshot, { rows: [], total_tokens: 0 });

  assert.ok(sessions.some((session) => session.id === 'capture:recorded'));
});

test('pure agent-native evidence does not create a duplicate recorded capture', () => {
  const snapshot = {
    summary: { view_events: 5, total_tokens: 10 },
    sessions: [selected],
    tool_calls: [{
      id: 'native-tool', session_id: 'raw-one', timestamp_ms: 150, related_pid: null,
    }],
    process_nodes: [], audit_events: [], resource_samples: [], network_targets: [],
  };

  assert.deepEqual(snapshotSessions(snapshot, true).map((session) => session.id), ['session-one']);
});
