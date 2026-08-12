// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { shouldConfigureDirect } from './nodeOpening.ts';

test('a fresh browser opens an account-saved Direct config before showing setup', () => {
  assert.equal(shouldConfigureDirect(false, true, false), false);
  assert.equal(shouldConfigureDirect(false, true, true), false);
});

test('Direct setup is shown only when no usable transport is known', () => {
  assert.equal(shouldConfigureDirect(false, false, false), true);
  assert.equal(shouldConfigureDirect(true, false, false), false);
  assert.equal(shouldConfigureDirect(false, false, true), false);
});
