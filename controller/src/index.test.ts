// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  allowedReturnTo, decryptDirectConfig, deleteOwnedNode, directConfigNodeIdFromPath,
  encryptDirectConfig, githubApiHeaders, nodeIdFromPath, normalizeDirectEndpoint,
  oauthStartAllowed, sha256Base64Url, validNodeId,
} from './index.ts';

test('PKCE challenge matches RFC 7636 example', async () => {
  const verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk';
  assert.equal(
    await sha256Base64Url(verifier),
    'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
  );
});

test('OAuth return URL stays on the hosted app origin', () => {
  const app = 'https://app.agentsight.us';
  assert.equal(allowedReturnTo('https://app.agentsight.us/tree', app), `${app}/`);
  assert.equal(allowedReturnTo('https://evil.example/', app), `${app}/`);
  assert.equal(allowedReturnTo('not a URL', app), `${app}/`);
});

test('control plane accepts only stable AgentSight Node IDs', () => {
  assert.equal(validNodeId('node_0123abcdef'), true);
  assert.equal(validNodeId('../../node_secret'), false);
  assert.equal(validNodeId('machine'), false);
});

test('Node deletion paths accept one validated Node ID only', () => {
  assert.equal(nodeIdFromPath('/v1/nodes/node_0123abcdef'), 'node_0123abcdef');
  assert.equal(nodeIdFromPath('/v1/nodes/../../secret'), null);
  assert.equal(nodeIdFromPath('/v1/nodes/not-a-node'), null);
  assert.equal(nodeIdFromPath('/v1/nodes/node_ok/extra'), null);
});

test('Direct config paths and endpoints are narrowly normalized', () => {
  assert.equal(
    directConfigNodeIdFromPath('/v1/nodes/node_0123abcdef/direct'),
    'node_0123abcdef',
  );
  assert.equal(directConfigNodeIdFromPath('/v1/nodes/../../secret/direct'), null);
  assert.equal(normalizeDirectEndpoint('https://lab.example:7395/path?q=1#fragment'), 'https://lab.example:7395');
  assert.equal(normalizeDirectEndpoint('https://user:pass@lab.example'), null);
  assert.equal(normalizeDirectEndpoint('file:///tmp/socket'), null);
});

test('Direct config is encrypted and bound to its owner and Node', async () => {
  const master = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';
  const config = {
    v: 1 as const,
    endpoint: 'https://lab.example',
    accessKey: 'a'.repeat(64),
  };
  const encrypted = await encryptDirectConfig(master, 'user_owner', 'node_lab', config);
  assert.equal(encrypted.ciphertext.includes(config.accessKey), false);
  assert.deepEqual(
    await decryptDirectConfig(master, 'user_owner', 'node_lab', encrypted),
    config,
  );
  await assert.rejects(
    decryptDirectConfig(master, 'user_other', 'node_lab', encrypted),
  );
});

test('Node deletion is scoped to both Node ID and owner', async () => {
  let query = '';
  let bindings: unknown[] = [];
  const db = {
    prepare(value: string) {
      query = value;
      return {
        bind(...values: unknown[]) {
          bindings = values;
          return { run: async () => ({}) };
        },
      };
    },
  };
  await deleteOwnedNode(db, 'node_lab123', 'user_owner456');
  assert.match(query, /WHERE id = \?1 AND owner_user_id = \?2/);
  assert.deepEqual(bindings, ['node_lab123', 'user_owner456']);
});

test('GitHub API requests identify the control plane client', () => {
  const headers = githubApiHeaders('test-token');
  assert.equal(headers.Authorization, 'Bearer test-token');
  assert.equal(headers['User-Agent'], 'AgentSight-Control');
  assert.equal(headers['X-GitHub-Api-Version'], '2022-11-28');
});

test('rejected client requests do not consume the location OAuth bucket', async () => {
  let locationCalls = 0;
  const rejected = { limit: async () => ({ success: false }) };
  const location = {
    limit: async () => {
      locationCalls += 1;
      return { success: true };
    },
  };
  assert.equal(await oauthStartAllowed(rejected, location, '192.0.2.1'), false);
  assert.equal(locationCalls, 0);

  const accepted = { limit: async () => ({ success: true }) };
  assert.equal(await oauthStartAllowed(accepted, location, '192.0.2.2'), true);
  assert.equal(locationCalls, 1);
});
