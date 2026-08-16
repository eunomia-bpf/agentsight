// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.dirname(here);
const require = createRequire(import.meta.url);
const config = require('../next.config.js');

test('stable build ID includes web extension source but ignores node_modules', async () => {
  const ignoredProbe = path.join(frontend, 'node_modules', '.agentsight-build-id-probe');
  const includedProbe = path.join(frontend, '..', 'ext', 'web', 'components', '.agentsight-build-id-probe');
  const baseline = await config.generateBuildId();

  try {
    fs.writeFileSync(ignoredProbe, 'ignored');
    assert.equal(await config.generateBuildId(), baseline);

    fs.writeFileSync(includedProbe, 'included');
    assert.notEqual(await config.generateBuildId(), baseline);
  } finally {
    fs.rmSync(ignoredProbe, { force: true });
    fs.rmSync(includedProbe, { force: true });
  }
});
