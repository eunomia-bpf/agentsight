// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { allowedReturnTo, sha256Base64Url, validNodeId } from './index.ts';

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
