// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';
import { CheckCircle2 } from 'lucide-react';
import { comparisonRows } from '../data';
import { Eyebrow, PageShell, PrimaryCta } from '../components';

export const metadata: Metadata = {
  title: 'Compare',
  description:
    'Compare AgentSight with SDK tracing, LLM gateways, and transcript/token tools for AI agent profiling and system-level tracing.',
  alternates: {
    canonical: '/compare/',
  },
};

export default function ComparePage() {
  return (
    <PageShell>
      <section className="bg-white py-16">
        <div className="container-page">
          <Eyebrow>Compare</Eyebrow>
          <h1 className="max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
            AgentSight complements LLM observability by profiling the system effects around the agent.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-slate-600">
            SDK traces, gateways, and local transcripts are useful. They are also incomplete for
            local and closed-source agents that spawn commands, touch files, and make network calls
            outside the framework boundary.
          </p>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-14">
        <div className="container-page overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <div className="min-w-[920px]">
          <div className="grid grid-cols-5 border-b border-slate-200 bg-slate-50 text-sm font-semibold text-ink">
            <div className="p-4">Capability</div>
            <div className="p-4">SDK tracing</div>
            <div className="p-4">LLM gateway</div>
            <div className="p-4">Transcript tools</div>
            <div className="p-4">AgentSight</div>
          </div>
          {comparisonRows.map((row) => (
            <div key={row.feature} className="grid grid-cols-5 border-b border-slate-200 last:border-b-0">
              <div className="p-4 text-sm font-semibold text-ink">{row.feature}</div>
              <div className="p-4 text-sm leading-6 text-slate-600">{row.sdk}</div>
              <div className="p-4 text-sm leading-6 text-slate-600">{row.gateway}</div>
              <div className="p-4 text-sm leading-6 text-slate-600">{row.transcript}</div>
              <div className="bg-blue-50 p-4 text-sm font-medium leading-6 text-blue-900">{row.agentsight}</div>
            </div>
          ))}
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="container-page grid gap-5 md:grid-cols-3">
          {[
            'Use Langfuse, LangSmith, Phoenix, or Datadog for app-level spans, evals, and traces.',
            'Use Helicone or provider gateways for routing, model controls, and provider traffic analytics.',
            'Use AgentSight when the run depends on processes, files, network, resources, and opaque local CLIs.',
          ].map((item) => (
            <div key={item} className="rounded-md border border-slate-200 bg-slatepaper p-5">
              <CheckCircle2 className="h-5 w-5 text-mint" />
              <p className="mt-4 text-sm leading-6 text-slate-700">{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-ink py-16 text-white">
        <div className="container-page grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <h2 className="text-3xl font-semibold">Use the right layer for the question.</h2>
            <p className="mt-3 max-w-2xl text-base leading-7 text-slate-300">
              AgentSight is the system profiling layer for agent runs. It is not a replacement for
              app traces, gateways, or eval platforms.
            </p>
          </div>
          <PrimaryCta />
        </div>
      </section>
    </PageShell>
  );
}
