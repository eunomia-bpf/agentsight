// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { delimiter, join } from 'node:path';
import { spawnSync } from 'node:child_process';

const cargoBin = join(homedir(), '.cargo', 'bin');
const env = { ...process.env, PATH: `${cargoBin}${delimiter}${process.env.PATH || ''}` };

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { env, stdio: 'inherit', ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

function available(command) {
  const result = spawnSync(command, ['--version'], {
    env,
    stdio: 'ignore',
    shell: process.platform === 'win32',
  });
  return !result.error && result.status === 0;
}

if (!available('cargo')) {
  if (!process.argv.includes('--workers-ci')) {
    throw new Error('cargo is required to build the AgentSight browser protocol');
  }
  const manifest = readFileSync('../agentsight-protocol/Cargo.toml', 'utf8');
  const rustVersion = manifest.match(/^rust-version\s*=\s*"([^"]+)"/m)?.[1];
  if (!rustVersion || !/^\d+\.\d+(?:\.\d+)?$/.test(rustVersion)) {
    throw new Error('agentsight-protocol does not declare a valid rust-version');
  }
  run('sh', [
    '-c',
    `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain ${rustVersion}`,
  ]);
}

if (available('rustup')) run('rustup', ['target', 'add', 'wasm32-unknown-unknown']);
if (!available('npm') && available('pnpm')) {
  run('pnpm', [
    'dlx', 'wasm-pack@0.15.0', 'build', '../agentsight-protocol',
    '--target', 'web', '--out-dir', '../frontend/src/generated/agentsight-protocol', '--no-pack',
  ], { shell: process.platform === 'win32' });
  run('pnpm', ['exec', 'next', 'build'], { shell: process.platform === 'win32' });
} else {
  run('npm', ['run', 'build:wasm'], { shell: process.platform === 'win32' });
  run('npm', ['exec', '--', 'next', 'build'], { shell: process.platform === 'win32' });
}
