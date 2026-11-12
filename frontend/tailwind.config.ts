// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    '../ext/web/page.tsx',
    '../ext/web/components/**/*.{js,ts,jsx,tsx,mdx}',
    '../ext/web/lib/**/*.{js,ts,jsx,tsx,mdx}',
    '../ext/web/types/**/*.{js,ts,jsx,tsx,mdx}',
    '../ext/web/utils/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
      },
    },
  },
  plugins: [],
}
export default config
