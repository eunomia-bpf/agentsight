// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.dirname(here);
const require = createRequire(import.meta.url);
const config = require('../next.config.js');

test('stable build ID is line-ending independent and ignores node_modules', async () => {
  const ignoredProbe = path.join(frontend, 'node_modules', '.agentsight-build-id-probe');
  const includedProbe = path.join(frontend, '..', 'ext', 'web', 'components', '.agentsight-build-id-probe.txt');
  const baseline = await config.generateBuildId();

  try {
    fs.writeFileSync(ignoredProbe, 'ignored');
    assert.equal(await config.generateBuildId(), baseline);

    fs.writeFileSync(includedProbe, 'line one\nline two\n');
    const lfBuildId = await config.generateBuildId();
    assert.notEqual(lfBuildId, baseline);

    fs.writeFileSync(includedProbe, 'line one\r\nline two\r\n');
    assert.equal(await config.generateBuildId(), lfBuildId);
  } finally {
    fs.rmSync(ignoredProbe, { force: true });
    fs.rmSync(includedProbe, { force: true });
  }
});

test('stable build ID includes the public base path', async () => {
  const alternateBasePath = process.env.NEXT_PUBLIC_BASE_PATH === '/build-id-test'
    ? '/build-id-alternate'
    : '/build-id-test';
  const result = spawnSync(
    process.execPath,
    ['-e', "require('./next.config.js').generateBuildId().then((id) => process.stdout.write(id))"],
    {
      cwd: frontend,
      env: { ...process.env, NEXT_PUBLIC_BASE_PATH: alternateBasePath },
      encoding: 'utf8',
    },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.notEqual(result.stdout, await config.generateBuildId());
});
