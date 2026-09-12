// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const target = path.join(frontend, 'node_modules');
const link = path.resolve(frontend, '..', 'ext', 'web', 'node_modules');

if (!fs.existsSync(target)) {
  throw new Error(`frontend dependencies are missing at ${target}; run npm ci first`);
}

try {
  const existing = fs.lstatSync(link);
  if (!existing.isSymbolicLink()) {
    throw new Error(`${link} exists but is not a dependency link`);
  }
  if (fs.realpathSync(link) === fs.realpathSync(target)) process.exit(0);
  fs.unlinkSync(link);
} catch (error) {
  if (error?.code !== 'ENOENT') throw error;
}

fs.symlinkSync(target, link, process.platform === 'win32' ? 'junction' : 'dir');
