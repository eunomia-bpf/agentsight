// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
