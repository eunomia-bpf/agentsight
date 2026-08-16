// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
const textExtensions = new Set([
  '.css', '.html', '.js', '.json', '.jsonc', '.jsx', '.lock', '.md', '.mjs',
  '.scss', '.svg', '.toml', '.ts', '.tsx', '.txt', '.xml', '.yaml', '.yml',
]);
const buildIdInputs = [
  'src', '../ext/web/ext.toml', '../ext/web/page.tsx', '../ext/web/components',
  '../ext/web/lib', '../ext/web/types', '../ext/web/utils',
  'public', 'package.json', 'package-lock.json',
  'yarn.lock', 'postcss.config.mjs', 'tailwind.config.ts', 'tsconfig.json', 'next.config.js',
];

function addPathToHash(hash, filePath) {
  const stat = fs.statSync(filePath);
  if (stat.isDirectory()) {
    for (const name of fs.readdirSync(filePath).sort()) addPathToHash(hash, path.join(filePath, name));
    return;
  }
  if (!stat.isFile()) return;
  hash.update(path.relative(__dirname, filePath).replace(/\\/g, '/'));
  hash.update('\0');
  const contents = fs.readFileSync(filePath);
  hash.update(textExtensions.has(path.extname(filePath).toLowerCase())
    ? Buffer.from(contents.toString('utf8').replace(/\r\n/g, '\n'))
    : contents);
  hash.update('\0');
}

function stableBuildId() {
  const hash = crypto.createHash('sha256');
  hash.update('NEXT_PUBLIC_BASE_PATH\0');
  hash.update(basePath);
  hash.update('\0');
  for (const input of buildIdInputs) {
    const filePath = path.join(__dirname, input);
    if (fs.existsSync(filePath)) addPathToHash(hash, filePath);
  }
  return `agentsight-${hash.digest('hex').slice(0, 16)}`;
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  distDir: 'dist',
  basePath,
  assetPrefix: basePath || undefined,
  generateBuildId: async () => stableBuildId(),
}

module.exports = nextConfig
