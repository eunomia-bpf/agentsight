// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { browserRelayRoute, relayNodeSocketId, validRelayToken } from './relay.ts';

test('Node relay socket path accepts only stable Node IDs', () => {
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_0123abcdef'), 'node_0123abcdef');
  assert.equal(relayNodeSocketId('/v1/relay/nodes/not-a-node'), null);
  assert.equal(relayNodeSocketId('/v1/relay/nodes/node_ok/extra'), null);
});

test('browser relay surface is narrow and maps to Node protocol paths', () => {
  const snapshot = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/snapshot?audit_limit=5000&url=http://evil',
  ));
  assert.deepEqual(snapshot, {
    nodeId: 'node_test',
    method: 'GET',
    nodePath: '/api/v1/snapshot?audit_limit=5000',
    statusOnly: false,
  });

  const session = browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/sessions/session-1',
  ));
  assert.deepEqual(session, {
    nodeId: 'node_test',
    method: 'GET',
    nodePath: '/api/v1/sessions/session-1',
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

  assert.equal(browserRelayRoute(new Request(
    'https://controller.example/v1/nodes/node_test/relay/http',
    { method: 'POST' },
  )), null);
});

test('relay tokens use the same Direct bearer shape', () => {
  assert.equal(validRelayToken('a'.repeat(64)), true);
  assert.equal(validRelayToken('short'), false);
  assert.equal(validRelayToken(`${'a'.repeat(63)}!`), false);
});
