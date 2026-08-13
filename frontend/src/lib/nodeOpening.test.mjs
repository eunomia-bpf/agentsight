// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { shouldConfigureDirect, tryNodeTransports } from './nodeOpening.mjs';

test('a fresh browser opens an account-saved Direct config before showing setup', () => {
  assert.equal(shouldConfigureDirect(false, true, false), false);
  assert.equal(shouldConfigureDirect(false, true, true), false);
});

test('Direct setup is shown only when no usable transport is known', () => {
  assert.equal(shouldConfigureDirect(false, false, false), true);
  assert.equal(shouldConfigureDirect(true, false, false), false);
  assert.equal(shouldConfigureDirect(false, false, true), false);
});

test('a stale local Direct falls back to the account-saved Direct before relay', async () => {
  const attempted = [];
  const result = await tryNodeTransports([
    { transport: 'local-direct', open: async () => { attempted.push('local-direct'); throw new Error('stale'); } },
    { transport: 'account-direct', open: async () => { attempted.push('account-direct'); } },
    { transport: 'relay', open: async () => { attempted.push('relay'); } },
  ]);

  assert.deepEqual(attempted, ['local-direct', 'account-direct']);
  assert.equal(result.transport, 'account-direct');
  assert.equal(result.failures.length, 1);
});

test('relay is attempted after both Direct paths fail', async () => {
  const attempted = [];
  const fail = (transport) => async () => { attempted.push(transport); throw new Error(`${transport} failed`); };
  const result = await tryNodeTransports([
    { transport: 'local-direct', open: fail('local-direct') },
    { transport: 'account-direct', open: fail('account-direct') },
    { transport: 'relay', open: async () => { attempted.push('relay'); } },
  ]);

  assert.deepEqual(attempted, ['local-direct', 'account-direct', 'relay']);
  assert.equal(result.transport, 'relay');
  assert.equal(result.failures.length, 2);
});
