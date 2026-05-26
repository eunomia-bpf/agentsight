// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// Set NEXT_PUBLIC_BASE_PATH when serving under a sub-path (e.g. "/agentsight"
// for the github.io test deploy). Leave empty when serving at a domain root
// (e.g. the Cloudflare Pages production deploy at agentsight.us).
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  distDir: 'dist',
  basePath,
  assetPrefix: basePath || undefined,
}

module.exports = nextConfig