// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveControllerUrl } from './controllerOrigin.mjs';

test('hosted production uses the production Controller', () => {
  assert.equal(
    resolveControllerUrl(undefined, undefined, {
      hostname: 'app.agentsight.us', origin: 'https://app.agentsight.us',
    }),
    'https://control.agentsight.us',
  );
});

test('the Cloudflare preview remains isolated on its own Worker', () => {
  assert.equal(
    resolveControllerUrl(undefined, undefined, {
      hostname: 'agentsight-preview.yunwei356.workers.dev',
      origin: 'https://agentsight-preview.yunwei356.workers.dev',
    }),
    'https://agentsight-preview.yunwei356.workers.dev',
  );
});

test('a self-hosted override takes precedence and is normalized', () => {
  assert.equal(
    resolveControllerUrl('https://controller.example/', undefined, {
      hostname: 'agentsight-preview.yunwei356.workers.dev',
      origin: 'https://agentsight-preview.yunwei356.workers.dev',
    }),
    'https://controller.example',
  );
});
