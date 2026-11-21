import assert from 'node:assert/strict';
import test from 'node:test';
import { eventSpans, formatOffset, packSpans, tickStep } from './eventSpans.ts';

const snapshot = {
  summary: {},
  process_nodes: [
    { id: 'root', pid: 10, start_timestamp_ms: 1_000, end_timestamp_ms: null, comm: 'codex', command: 'codex exec', status: 'running' },
    { id: 'ok', pid: 11, ppid: 10, start_timestamp_ms: 2_000, end_timestamp_ms: 2_500, comm: 'git', command: 'git status', exit_code: 0 },
    { id: 'bad', pid: 12, ppid: 10, start_timestamp_ms: 3_000, end_timestamp_ms: 9_000, comm: 'npm', argv: ['npm', 'run', 'build'], exit_code: 2 },
  ],
  audit_events: [
    { id: 'req-1', timestamp_ms: 1_200, audit_type: 'llm', action: 'request', pid: 10, comm: 'codex', subject: 'gpt-5', summary: 'fix the build', status: 'success' },
    { id: 'res-1', timestamp_ms: 1_900, audit_type: 'llm', action: 'response', pid: 10, comm: 'codex', subject: 'gpt-5', status: 'success' },
    { id: 'req-2', timestamp_ms: 9_500, audit_type: 'llm', action: 'request', pid: 10, comm: 'codex', subject: 'gpt-5', summary: 'unanswered' },
    { id: 'connect', timestamp_ms: 1_100, audit_type: 'network', action: 'connect', target: 'api.openai.com:443', pid: 10, status: 'success' },
  ],
  network_targets: [
    { pid: 12, comm: 'npm', host: 'registry.npmjs.org', path: '/', count: 40, error_count: 2, first_timestamp_ms: 3_100, last_timestamp_ms: 8_000 },
    { pid: 12, comm: 'npm', host: 'mirror.example', path: '/', count: 2, error_count: 2, first_timestamp_ms: 3_200, last_timestamp_ms: 3_900 },
  ],
  tool_calls: [
    { id: 'tool', timestamp_ms: 2_900, start_timestamp_ms: 3_000, duration_ms: 6_000, tool_name: 'exec', status: 'failed', input: { command: ['npm', 'run', 'build'] }, output: { exit_code: 2 }, related_pid: 10 },
    { id: 'pending', timestamp_ms: 9_600, tool_name: 'exec', status: 'running', input: { cmd: 'npm test' }, related_pid: 10 },
  ],
  resource_samples: [{ timestamp_ms: 10_000, pid: 10, cpu_percent: 3 }],
};

function byId(spans, id) {
  const span = spans.find((candidate) => candidate.id === id);
  assert.ok(span, `missing span ${id}`);
  return span;
}

test('commands become spans with exit status, and open commands end at the last capture', () => {
  const spans = eventSpans(snapshot);
  assert.deepEqual(
    { ...byId(spans, 'exec:ok') },
    {
      id: 'exec:ok', kind: 'exec', label: 'git status', detail: 'git · pid 11 · exit 0',
      start: 2_000, end: 2_500, open: false, status: 'success', pid: 11, modelCallId: 'llm:req-1:res-1',
    },
  );
  const failed = byId(spans, 'exec:bad');
  assert.equal(failed.status, 'failed');
  assert.equal(failed.label, 'npm run build');
  const root = byId(spans, 'exec:root');
  assert.equal(root.status, 'running');
  assert.equal(root.open, true);
  assert.equal(root.end, 10_000);
});

test('model calls pair each request with the next response from the same process', () => {
  const spans = eventSpans(snapshot);
  const call = byId(spans, 'llm:req-1:res-1');
  assert.equal(call.start, 1_200);
  assert.equal(call.end, 1_900);
  assert.equal(call.status, 'success');
  assert.equal(call.label, 'fix the build');
  const unanswered = byId(spans, 'llm:req-2');
  assert.equal(unanswered.start, unanswered.end);
  assert.equal(unanswered.status, 'unknown');
});

test('a call seen both as traffic and as a transcript row appears once', () => {
  const transcript = [
    { id: 'native-prompt-0', timestamp_ms: 1_200, audit_type: 'llm', action: 'request', pid: 10, comm: 'codex', summary: 'fix the build', status: 'observed' },
    { id: 'native-response-0', timestamp_ms: 1_900, audit_type: 'llm', action: 'response', pid: 10, comm: 'codex', status: 'observed' },
  ];
  const calls = eventSpans({ ...snapshot, audit_events: [...transcript, ...snapshot.audit_events] })
    .filter((span) => span.kind === 'llm' && span.start === 1_200);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].status, 'success');

  const nativeOnly = eventSpans({ summary: {}, audit_events: transcript }).filter((span) => span.kind === 'llm');
  assert.deepEqual(nativeOnly.map((span) => [span.start, span.end, span.status]), [[1_200, 1_900, 'success']]);
});

test('captured calls pair by call identity, even when calls overlap', () => {
  const captured = (id, timestamp_ms, status = 'observed') => ({
    id, timestamp_ms, audit_type: 'llm', action: id.split('-').pop(), status,
    pid: 10, comm: 'codex', subject: 'gpt-5', summary: id,
  });
  const spans = eventSpans({
    summary: {},
    audit_events: [
      captured('audit-llm-a-request', 1_000),
      captured('audit-llm-b-request', 1_100),
      captured('audit-llm-b-call', 1_500, 'success'),
      captured('audit-llm-a-call', 2_500, 'failure'),
    ],
  });
  assert.deepEqual(
    spans.map((span) => [span.label, span.start, span.end, span.status]),
    [['audit-llm-a-request', 1_000, 2_500, 'failed'], ['audit-llm-b-request', 1_100, 1_500, 'success']],
  );
});

test('identical calls from different processes stay separate', () => {
  const pair = (pid) => [
    { id: `req-${pid}`, timestamp_ms: 1_000, audit_type: 'llm', action: 'request', pid, comm: 'agent', summary: 'same' },
    { id: `res-${pid}`, timestamp_ms: 2_000, audit_type: 'llm', action: 'response', pid, comm: 'agent' },
  ];
  const spans = eventSpans({ summary: {}, audit_events: [...pair(10), ...pair(11)] });
  assert.deepEqual(spans.map((span) => span.pid), [10, 11]);
});

test('agent-native tool rows become tool spans', () => {
  const [tool] = eventSpans({
    summary: {},
    audit_events: [{
      id: 'native-tool-0', timestamp_ms: 5_000, audit_type: 'system', action: 'call', pid: 10,
      status: 'completed', details: { tool_name: 'shell', command: 'pytest -q' },
    }],
  });
  assert.equal(tool.kind, 'tool');
  assert.equal(tool.label, 'shell · pytest -q');
  assert.equal(tool.status, 'success');
});

test('an unfinished observed process stays open until the capture end passed in', () => {
  const [span] = eventSpans(
    { summary: {}, process_nodes: [{ id: 'p', pid: 3, start_timestamp_ms: 1_000, end_timestamp_ms: null, status: 'observed' }] },
    { captureEnd: 20_000 },
  );
  assert.equal(span.open, true);
  assert.equal(span.status, 'running');
  assert.equal(span.end, 20_000);
});

test('network endpoints span their first and last request and report errors', () => {
  const spans = eventSpans(snapshot);
  const endpoint = spans.find((span) => span.label === 'registry.npmjs.org/');
  assert.equal(endpoint.start, 3_100);
  assert.equal(endpoint.end, 8_000);
  assert.equal(endpoint.status, 'success');
  assert.equal(endpoint.detail, '40 requests · 2 errors · npm · pid 12');
  assert.equal(spans.find((span) => span.label === 'mirror.example/').status, 'failed');
  assert.equal(byId(spans, 'network:connect').label, 'connect api.openai.com:443');
});

test('tool calls use their reported start and duration', () => {
  const tool = byId(eventSpans(snapshot), 'tool:tool');
  assert.equal(tool.label, 'exec · npm run build');
  assert.equal(tool.start, 3_000);
  assert.equal(tool.end, 9_000);
  assert.equal(tool.status, 'failed');
  assert.equal(tool.detail, 'exit 2 · pid 10');
  const pending = byId(eventSpans(snapshot), 'tool:pending');
  assert.equal(pending.label, 'exec · npm test');
  assert.equal(pending.open, true);
  assert.equal(pending.end, 10_000);
});

test('spans are ordered by start time', () => {
  const starts = eventSpans(snapshot).map((span) => span.start);
  assert.deepEqual(starts, [...starts].sort((left, right) => left - right));
});

test('packing keeps overlapping spans on separate rows', () => {
  const span = (id, start, end) => ({ id, start, end });
  const rows = packSpans([span('a', 0, 10), span('b', 5, 8), span('c', 10, 12), span('d', 11, 20)]);
  assert.deepEqual(rows.map((row) => row.map((item) => item.id)), [['a', 'c'], ['b', 'd']]);
  const spaced = packSpans([span('a', 0, 10), span('c', 10, 12)], 1);
  assert.deepEqual(spaced.map((row) => row.map((item) => item.id)), [['a'], ['c']]);
});

test('axis helpers format offsets and choose round steps', () => {
  assert.equal(formatOffset(42_500), '+42.5s');
  assert.equal(formatOffset(187_000), '+3:07');
  assert.equal(formatOffset(3_725_000), '+1:02:05');
  assert.equal(tickStep(600_000), 120_000);
  assert.equal(tickStep(4_000), 1_000);
});

test('sandbox grouping preserves namespace lifetimes, HTTP requests and inferred model links', () => {
  const spans = eventSpans({
    ...snapshot, sessions: [{ id: 's' }],
    sandboxes: [
      { id: 'a', name: 'worker', pidns: 100, first_seen_ms: 900, last_seen_ms: 10_000 },
      { id: 'b', name: 'build', pidns: 200, first_seen_ms: 2_000, last_seen_ms: 9_000, end_timestamp_ms: 9_000, exit_code: 2 },
    ],
    process_nodes: snapshot.process_nodes.map((p) => ({ ...p, sandbox_id: p.pid === 10 ? 'a' : 'b' })),
    audit_events: [...snapshot.audit_events,
      { id: 'http-req', pid: 11, sandbox_id: 'b', timestamp_ms: 2_100, audit_type: 'network', action: 'http_request', target: 'GET example.org/', details: { http_exchange_id: 'x' } },
      { id: 'http-res', pid: 11, sandbox_id: 'b', timestamp_ms: 2_300, audit_type: 'network', action: 'http_response', target: 'HTTP example.org/', status: 'success', details: { http_exchange_id: 'x' } },
    ],
  });
  assert.equal(byId(spans, 'sandbox:a').open, true);
  assert.equal(byId(spans, 'sandbox:b').status, 'failed');
  assert.equal(byId(spans, 'exec:bad').sandboxId, 'b');
  const http = byId(spans, 'network:http-req');
  assert.equal(http.kind, 'http');
  assert.equal(http.end - http.start, 200);
  assert.equal(http.modelCallId, 'llm:req-1:res-1');
  assert.equal(http.sandboxId, 'b');
  assert.ok(spans.filter((s) => s.aggregated).every((s) => !s.modelCallId));
});

test('temporal links exclude future, unfinished and unrelated-session model calls', () => {
  const spans = eventSpans({ ...snapshot,
    process_nodes: snapshot.process_nodes.map((p) => ({ ...p, ppid: null, root_pid: p.pid })),
    sessions: [{ id: 'one' }, { id: 'two' }],
  });
  assert.equal(byId(spans, 'exec:ok').modelCallId, undefined);
  assert.equal(byId(spans, 'network:connect').modelCallId, undefined);
});

test('HTTP rows without exchange ids pair despite method labels and keep failure status', () => {
  const spans = eventSpans({ audit_events: [
    { id: 'req', pid: 1, timestamp_ms: 100, audit_type: 'network', action: 'http_request', target: 'GET example.org/health' },
    { id: 'res', pid: 1, timestamp_ms: 150, audit_type: 'network', action: 'http_response', target: 'HTTP example.org/health', status: 'failure' },
  ] });
  assert.equal(spans.length, 1);
  assert.equal(spans[0].label, 'GET example.org/health');
  assert.equal(spans[0].end - spans[0].start, 50);
  assert.equal(spans[0].status, 'failed');
});

test('unfinished calls are not the inferred cause of later commands', () => {
  const spans = eventSpans({ ...snapshot, process_nodes: [...snapshot.process_nodes,
    { id: 'late', pid: 10, start_timestamp_ms: 9_600, end_timestamp_ms: 9_700, command: 'later' },
  ] });
  assert.equal(byId(spans, 'exec:late').modelCallId, 'llm:req-1:res-1');
});
