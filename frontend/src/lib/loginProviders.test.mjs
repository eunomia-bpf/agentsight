// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';

const supported = ['github', 'google'];

function visibleProviderState(configured) {
  return Object.fromEntries(supported.map((provider) => [provider, configured.includes(provider)]));
}

test('supported sign-in providers remain visible when one is unconfigured', () => {
  assert.deepEqual(visibleProviderState(['github']), { github: true, google: false });
});

test('supported sign-in providers remain visible when Controller reports none', () => {
  assert.deepEqual(visibleProviderState([]), { github: false, google: false });
});
