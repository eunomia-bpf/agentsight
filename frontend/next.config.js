// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// Set NEXT_PUBLIC_BASE_PATH when serving under a sub-path (e.g. "/agentsight"
// for the github.io test deploy). Leave empty when serving at a domain root.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const buildIdInputs = [
  'src',
  '../ext/web',
  'public',
  'package.json',
  'package-lock.json',
  'yarn.lock',
  'postcss.config.mjs',
  'tailwind.config.ts',
  'tsconfig.json',
  'next.config.js',
];

function addPathToHash(hash, filePath) {
  const stat = fs.statSync(filePath);
  if (stat.isDirectory()) {
    for (const name of fs.readdirSync(filePath).sort()) {
      addPathToHash(hash, path.join(filePath, name));
    }
    return;
  }
  if (!stat.isFile()) return;
  const relativePath = path.relative(__dirname, filePath).replace(/\\/g, '/');
  hash.update(relativePath);
  hash.update('\0');
  hash.update(fs.readFileSync(filePath));
  hash.update('\0');
}

function stableBuildId() {
  const hash = crypto.createHash('sha256');
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
