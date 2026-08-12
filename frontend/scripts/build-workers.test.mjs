// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

test('Workers build installs the protocol crate minimum Rust toolchain when cargo is absent', () => {
  const source = readFileSync(new URL('./build-workers.mjs', import.meta.url), 'utf8');
  assert.match(source, /process\.env\.WORKERS_CI !== '1'/);
  assert.match(source, /agentsight-protocol\/Cargo\.toml/);
  assert.match(source, /rust-version/);
  assert.match(source, /--profile minimal/);
  assert.match(source, /wasm32-unknown-unknown/);
});
