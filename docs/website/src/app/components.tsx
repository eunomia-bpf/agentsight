// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import Link from 'next/link';
import { ArrowRight, BookOpen, Github, PlayCircle, SquareTerminal } from 'lucide-react';
import { navItems } from './data';

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-slatepaper/92 backdrop-blur">
      <div className="container-page flex min-h-16 items-center justify-between gap-4 py-3">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ink text-sm font-bold text-white">
            AS
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-wide text-ink">AgentSight</div>
            <div className="text-xs text-slate-500">by Eunomia</div>
          </div>
        </Link>
        <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex">
          {navItems.map((item) =>
            item.href.startsWith('http') ? (
              <a key={item.href} href={item.href} target="_blank" rel="noopener noreferrer" className="hover:text-ink">
                {item.label}
              </a>
            ) : (
              <Link key={item.href} href={item.href} className="hover:text-ink">
                {item.label}
              </Link>
            ),
          )}
        </nav>
        <div className="flex items-center gap-2">
          <a
            href="https://app.agentsight.us/"
            className="hidden items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-ink shadow-sm hover:border-slate-400 md:flex"
          >
            <PlayCircle className="h-4 w-4" />
            Demo
          </a>
          <a
            href="https://github.com/eunomia-bpf/agentsight"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700"
          >
            <Github className="h-4 w-4" />
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-page grid gap-8 py-10 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="text-sm font-semibold uppercase tracking-wide text-ink">AgentSight by Eunomia</div>
          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">
            System-level profiling/tracing tools and skills for AI agents, powered by eBPF.
          </p>
        </div>
        <div>
          <div className="text-sm font-semibold text-ink">Product</div>
          <div className="mt-3 grid gap-2 text-sm text-slate-600">
            <Link href="/use-cases/" className="hover:text-ink">Use cases</Link>
            <Link href="/compare/" className="hover:text-ink">Compare</Link>
            <a href="https://app.agentsight.us/" className="hover:text-ink">Live demo</a>
          </div>
        </div>
        <div>
          <div className="text-sm font-semibold text-ink">Resources</div>
          <div className="mt-3 grid gap-2 text-sm text-slate-600">
            <a href="https://eunomia.dev/agentsight/" className="hover:text-ink">Documentation</a>
            <a href="https://github.com/eunomia-bpf/agentsight" className="hover:text-ink">GitHub</a>
            <a href="/llms.txt" className="hover:text-ink">llms.txt</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main>{children}</main>
      <SiteFooter />
    </>
  );
}

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 inline-flex rounded-md border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-700">
      {children}
    </div>
  );
}

export function PrimaryCta() {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <a
        href="https://app.agentsight.us/"
        className="inline-flex items-center justify-center gap-2 rounded-md bg-river px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
      >
        <PlayCircle className="h-4 w-4" />
        Try live demo
      </a>
      <a
        href="https://eunomia.dev/agentsight/"
        className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-ink shadow-sm hover:border-slate-400"
      >
        <BookOpen className="h-4 w-4" />
        Read docs
      </a>
    </div>
  );
}

export function CommandBlock({ commands }: { commands: string[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-800 bg-slate-950 shadow-soft">
      <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-3 text-xs text-slate-400">
        <SquareTerminal className="h-4 w-4" />
        Quick start
      </div>
      <pre className="code-scroll overflow-x-auto p-4 text-sm leading-7 text-slate-100">
        {commands.map((command) => `$ ${command}`).join('\n')}
      </pre>
    </div>
  );
}

export function TextLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="inline-flex items-center gap-1 font-semibold text-river hover:text-blue-700">
      {children}
      <ArrowRight className="h-4 w-4" />
    </Link>
  );
}
