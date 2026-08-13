// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import {
  allowedReturnTo, decryptDirectConfig, directConfigNodeIdFromPath, encryptDirectConfig,
  githubApiHeaders, nodeIdFromPath, normalizeDirectEndpoint, oauthStartAllowed,
  publicPricing, roleAllows, sha256Base64Url, validNodeId,
} from './index.ts';
import {
  planAllowsManagedConnectivity,
  planAllowsMultipleMembers,
  relayAction,
} from './access.ts';

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
  assert.equal(
    allowedReturnTo(
      'https://controller-agentsight-domain-agentsight.yunwei356.workers.dev/sessions',
      app,
      'https://controller-agentsight-domain-agentsight.yunwei356.workers.dev',
    ),
    'https://controller-agentsight-domain-agentsight.yunwei356.workers.dev/',
  );
  assert.equal(allowedReturnTo('https://evil.example/', app), `${app}/`);
  assert.equal(allowedReturnTo('not a URL', app), `${app}/`);
});

test('Controller accepts only stable AgentSight Node IDs', () => {
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

test('built-in roles grant semantic actions instead of HTTP routes', () => {
  assert.equal(roleAllows('viewer', 'session.read'), true);
  assert.equal(roleAllows('viewer', 'session.message'), false);
  assert.equal(roleAllows('operator', 'session.message'), true);
  assert.equal(roleAllows('operator', 'node.manage'), false);
  assert.equal(roleAllows('admin', 'node.manage'), true);
  assert.equal(roleAllows('admin', 'billing.manage'), false);
  assert.equal(roleAllows('owner', 'billing.manage'), true);
});

test('pricing catalog matches launch prices and contributor boundary', () => {
  const pricing = publicPricing();
  const plans = Object.fromEntries(pricing.plans.map((plan) => [plan.id, plan]));
  assert.equal(plans.free.monthly_cents, 0);
  assert.equal(plans.pro.monthly_cents, 500);
  assert.equal(plans.pro.annual_cents, 4900);
  assert.equal(plans.team.monthly_cents, 1000);
  assert.equal(plans.team.per_seat, true);
  assert.equal(plans.enterprise.custom, true);
  assert.equal(pricing.contributor_benefit.entitlement, 'pro_lifetime');
  assert.equal(pricing.contributor_benefit.includes_team, false);
});

test('plan gates separate local, managed personal, and multi-member use', () => {
  assert.equal(planAllowsManagedConnectivity('free'), false);
  assert.equal(planAllowsManagedConnectivity('pro'), true);
  assert.equal(planAllowsMultipleMembers('pro'), false);
  assert.equal(planAllowsMultipleMembers('team'), true);
  assert.equal(planAllowsMultipleMembers('enterprise'), true);
});

test('relay protocol routes map to the same semantic permissions as direct', () => {
  assert.equal(relayAction('GET', '/api/v1/snapshot?audit_limit=100', false), 'evidence.read');
  assert.equal(relayAction('GET', '/api/v1/sessions/s-1', false), 'session.read');
  assert.equal(relayAction('POST', '/api/v1/sessions/s-1/messages', false), 'session.message');
  assert.equal(relayAction('GET', null, true), 'node.read');
});

test('GitHub API requests identify the Controller client', () => {
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
