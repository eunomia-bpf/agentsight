// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  MAX_PENDING_RELAY_REQUESTS,
  NodeRelay,
  RELAY_TIMEOUT_MS,
  browserRelayRoute,
  connectNodeRelay,
  proxyBrowserRelay,
  relayTokenHash,
  relayNodeSocketId,
  validRelayNodeVersion,
  validRelayToken,
} from './relay.ts';
import type { RelayEnv } from './relay.ts';

test('relay waits longer than the Node provider acknowledgement window', () => {
  assert.ok(RELAY_TIMEOUT_MS > 20_000);
  assert.ok(RELAY_TIMEOUT_MS < 30_000);
});

test('relay pending work is capped per Node', () => {
  assert.equal(MAX_PENDING_RELAY_REQUESTS, 64);
});

test('relay pending cap holds across concurrently parsed request bodies', async () => {
  const originalPair = Object.getOwnPropertyDescriptor(globalThis, 'WebSocketRequestResponsePair');
  Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', {
    configurable: true,
    value: class WebSocketRequestResponsePairStub {},
  });
  const envelopes: Array<{ id: string }> = [];
  const socket = {
    readyState: WebSocket.OPEN,
    send(message: string) {
      envelopes.push(JSON.parse(message) as { id: string });
    },
  } as unknown as WebSocket;
  const ctx = {
    setWebSocketAutoResponse() {},
    getWebSockets: () => [socket],
  } as unknown as DurableObjectState;
  const relay = new NodeRelay(ctx, {} as RelayEnv);

  try {
    const requests = Array.from({ length: MAX_PENDING_RELAY_REQUESTS + 1 }, () => relay.fetch(
      new Request('https://relay.internal/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: 'GET', path: '/api/v1/overview' }),
      }),
    ));
    for (let attempt = 0; attempt < 20 && envelopes.length < MAX_PENDING_RELAY_REQUESTS; attempt += 1) {
      await new Promise((resolve) => setImmediate(resolve));
    }
    await new Promise((resolve) => setImmediate(resolve));

    for (const envelope of envelopes) {
      await relay.webSocketMessage(socket, JSON.stringify({
        type: 'response', id: envelope.id, status: 200, body: '{}',
      }));
    }
    const responses = await Promise.all(requests);
    assert.equal(envelopes.length, MAX_PENDING_RELAY_REQUESTS);
    assert.equal(responses.filter((response) => response.status === 200).length, MAX_PENDING_RELAY_REQUESTS);
    assert.equal(responses.filter((response) => response.status === 429).length, 1);
    assert.deepEqual(await responses.find((response) => response.status === 429)?.json(), {
      error: 'relay_busy',
    });
  } finally {
    if (originalPair) {
      Object.defineProperty(globalThis, 'WebSocketRequestResponsePair', originalPair);
    } else {
      Reflect.deleteProperty(globalThis, 'WebSocketRequestResponsePair');
    }
  }
});

test('Node relay socket path accepts only stable Node IDs', () => {
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_0123abcdef'), 'node_0123abcdef');
  assert.equal(relayNodeSocketId('/v1/relay/nodes/not-a-node'), null);
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_ok/extra'), null);
});

test('browser relay parses supported Node paths before semantic authorization', () => {
  const snapshot = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/snapshot?audit_limit=5000',
  ));
  assert.deepEqual(snapshot, {
    nodeId: 'node_test',
    method: 'GET',
    nodePath: '/api/v1/snapshot?audit_limit=5000',
    statusOnly: false,
  });

  const message = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST' },
  ));
  assert.deepEqual(message, {
    nodeId: 'node_test',
    method: 'POST',
    nodePath: '/api/v1/sessions/session-1/messages',
    statusOnly: false,
  });

  assert.deepEqual(browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/status',
  )), {
    nodeId: 'node_test', method: 'GET', nodePath: null, statusOnly: true,
  });
  assert.equal(browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/../capabilities',
    { method: 'POST' },
  )), null);
});

test('browser relay preserves a maximally escaped valid session message', async () => {
  const message = '\0'.repeat(65_536);
  const body = JSON.stringify({ message });
  assert.ok(new TextEncoder().encode(body).byteLength > 96 * 1024);
  let relayedBody = '';
  const relay = {
    idFromName: () => ({}) as DurableObjectId,
    get: () => ({
      fetch: async (request: Request) => {
        const input = await request.json() as { body?: string };
        relayedBody = input.body || '';
        return new Response('{}', { status: 200 });
      },
    }) as unknown as DurableObjectStub,
  } as unknown as DurableObjectNamespace;
  const request = new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST', body },
  );
  const route = browserRelayRoute(request);
  assert.ok(route);

  const response = await proxyBrowserRelay(
    request,
    { DB: {} as D1Database, NODE_RELAY: relay },
    route,
  );

  assert.equal(response.status, 200);
  assert.equal(relayedBody, body);
  assert.equal(JSON.parse(relayedBody).message, message);
});

test('browser relay cancels an oversized streaming body without Content-Length', async () => {
  let cancelled = false;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array(300 * 1024));
      controller.enqueue(new Uint8Array(300 * 1024));
    },
    cancel() {
      cancelled = true;
    },
  });
  const request = new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1/messages',
    { method: 'POST', body: stream, duplex: 'half' } as RequestInit & { duplex: 'half' },
  );
  const route = browserRelayRoute(request);
  assert.ok(route);

  const response = await proxyBrowserRelay(
    request,
    { DB: {} as D1Database, NODE_RELAY: {} as DurableObjectNamespace },
    route,
  );

  assert.equal(response.status, 413);
  assert.equal(cancelled, true);
});

test('relay tokens use the same Direct bearer shape', () => {
  assert.equal(validRelayToken('a'.repeat(64)), true);
  assert.equal(validRelayToken('short'), false);
  assert.equal(validRelayToken(`${'a'.repeat(63)}!`), false);
});

test('relay node versions accept release metadata and reject unsafe values', () => {
  assert.equal(validRelayNodeVersion('1.0.23'), true);
  assert.equal(validRelayNodeVersion('1.0.24-rc.1+build'), true);
  assert.equal(validRelayNodeVersion(`1.${'0'.repeat(62)}`), true);
  assert.equal(validRelayNodeVersion(''), false);
  assert.equal(validRelayNodeVersion(' 1.0.23'), false);
  assert.equal(validRelayNodeVersion('1.0.23\r\nX-Injected: yes'), false);
  assert.equal(validRelayNodeVersion(`1.${'0'.repeat(63)}`), false);
});

test('authenticated relay reconnect persists reported version without breaking old Nodes', async () => {
  const token = 'a'.repeat(64);
  const expectedHash = await relayTokenHash(token);
  const updates: unknown[][] = [];
  const db = {
    prepare: (query: string) => ({
      bind: (...values: unknown[]) => ({
        first: async () => ({ relay_token_hash: expectedHash }),
        run: async () => {
          assert.match(query, /version = COALESCE\(\?3, version\)/);
          updates.push(values);
          return { success: true };
        },
      }),
    }),
  } as D1Database;
  const relay = {
    idFromName: () => ({}) as DurableObjectId,
    get: () => ({
      fetch: async () => new Response(null, { status: 200 }),
    }) as unknown as DurableObjectStub,
  } as unknown as DurableObjectNamespace;

  const connect = (version?: string) => connectNodeRelay(new Request(
    'https://controller.example/v1/relay/nodes/node_test',
    { headers: {
      Upgrade: 'websocket', Authorization: `Bearer ${token}`,
      ...(version ? { 'X-AgentSight-Node-Version': version } : {}),
    } },
  ), { DB: db, NODE_RELAY: relay }, 'node_test');

  assert.equal((await connect('1.0.23')).status, 200);
  assert.equal(updates[0][1], 'node_test');
  assert.equal(updates[0][2], '1.0.23');
  assert.equal((await connect()).status, 200);
  assert.equal(updates[1][2], null);
  assert.equal((await connect('invalid version')).status, 400);
  assert.equal(updates.length, 2);
});
