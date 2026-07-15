// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { readFileSync, writeFileSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const cargoToml = readFileSync(resolve(root, 'collector/Cargo.toml'), 'utf8');
const match = cargoToml.match(/^version = "([^"]+)"/m);

if (!match) {
  console.error('Could not read package version from collector/Cargo.toml');
  process.exit(1);
}

const version = match[1];
const scopedPath = resolve(root, 'package/npm/agentsight/package.json');

function updatePackage(filePath, update) {
  const json = JSON.parse(readFileSync(filePath, 'utf8'));
  update(json);
  writeFileSync(filePath, `${JSON.stringify(json, null, 2)}\n`);
}

updatePackage(scopedPath, (json) => {
  json.version = version;
});

console.log(`Synced npm package versions to ${version}`);
