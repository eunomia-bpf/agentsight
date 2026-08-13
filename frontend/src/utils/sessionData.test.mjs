import assert from 'node:assert/strict';
import test from 'node:test';
import { sessionSnapshot } from './sessionData.ts';

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
