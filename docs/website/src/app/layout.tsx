// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://agentsight.us'),
  title: {
    default: 'AgentSight by Eunomia: AI Agent Profiling Tools and Skills',
    template: '%s | AgentSight by Eunomia',
  },
  description:
    'System-level profiling/tracing tools and skills for Claude Code, Codex, and other local agents. Understand time, tokens, commands, files, network calls, and system resources without SDKs.',
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: 'AgentSight by Eunomia: AI Agent Profiling Tools and Skills',
    description:
      'System-level profiling/tracing tools and skills for Claude Code, Codex, and other local agents. No SDKs.',
    url: 'https://agentsight.us/',
    siteName: 'AgentSight',
    type: 'website',
    images: ['/images/top-mode-demo.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AgentSight by Eunomia',
    description: 'System-level profiling/tracing tools and skills for AI agents, powered by eBPF.',
    images: ['/images/top-mode-demo.png'],
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
