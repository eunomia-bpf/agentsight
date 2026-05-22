// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next'
import './globals.css'
import { I18nProvider } from '@/i18n'

export const metadata: Metadata = {
  title: 'Agent Tracer Frontend',
  description: 'Frontend for Agent Tracer observability framework',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  )
}