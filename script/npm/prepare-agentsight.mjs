// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { cpSync, existsSync, mkdirSync, rmSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const frontendDist = resolve(root, 'frontend/dist');
const packageWeb = resolve(root, 'package/npm/agentsight/web');

if (!existsSync(resolve(frontendDist, 'index.html'))) {
  console.error('Missing frontend/dist/index.html.');
  console.error('Run: npm ci --prefix frontend');
  console.error('Run: node frontend/scripts/prepare-sample.mjs');
  console.error('Run: npm run build --prefix frontend');
  process.exit(1);
}

rmSync(packageWeb, { recursive: true, force: true });
mkdirSync(packageWeb, { recursive: true });
cpSync(frontendDist, packageWeb, { recursive: true });

console.log(`Prepared npm AgentSight Web assets -> ${packageWeb}`);
