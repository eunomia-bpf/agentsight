// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ink: '#13202f',
        slatepaper: '#f6f8fb',
        river: '#2563eb',
        mint: '#0f9f6e',
        ember: '#b45309',
      },
      boxShadow: {
        soft: '0 18px 60px rgba(20, 32, 47, 0.12)',
      },
    },
  },
  plugins: [],
};

export default config;
