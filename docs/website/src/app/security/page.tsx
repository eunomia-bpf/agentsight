// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';
import { securityPoints } from '../data';
import { Eyebrow, PageShell, PrimaryCta } from '../components';

export const metadata: Metadata = {
  title: 'Security and Privacy',
  description:
    'How AgentSight handles local data, Linux/eBPF privileges, targeted tracing, and OpenTelemetry export for AI agent profiling.',
  alternates: {
    canonical: '/security/',
  },
};

const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'Does AgentSight require root?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Live eBPF capture requires elevated privileges on Linux. With record commands, the monitored agent can still run as the normal user while the probes are elevated.',
      },
    },
    {
      '@type': 'Question',
      name: 'Where does captured data go?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'AgentSight records sessions locally by default. Captured data can include prompts, responses, paths, headers, and network targets, so teams should treat saved traces as sensitive.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is AgentSight an LLM gateway?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'No. AgentSight does not require routing provider traffic through a gateway. It profiles AI agent runs from the system boundary using eBPF, process tracing, and TLS traffic tracing.',
      },
    },
  ],
};

export default function SecurityPage() {
  return (
    <PageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <section className="bg-white py-16">
        <div className="container-page">
          <Eyebrow>Security and privacy</Eyebrow>
          <h1 className="max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
            AgentSight is powerful because it observes sensitive boundaries. Treat the traces accordingly.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-slate-600">
            System-level profiling can capture prompts, responses, paths, headers, commands, network
            destinations, and resource data. The product is designed for local-first workflows and
            explicit exports, not hidden hosted collection.
          </p>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-14">
        <div className="container-page grid gap-4 md:grid-cols-2">
          {securityPoints.map((point) => {
            const Icon = point.icon;
            return (
              <div key={point.title} className="rounded-md border border-slate-200 bg-white p-6">
                <Icon className="h-6 w-6 text-river" />
                <h2 className="mt-4 text-xl font-semibold text-ink">{point.title}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">{point.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="container-page">
          <div className="max-w-3xl">
            <h2 className="text-3xl font-semibold text-ink">Operational notes</h2>
            <div className="mt-6 grid gap-4 text-sm leading-6 text-slate-700">
              <p>
                AgentSight needs Linux eBPF support and elevated privileges for live capture. This is
                the tradeoff that makes external process, file, network, and TLS boundary profiling possible.
              </p>
              <p>
                Saved sessions should be handled like logs containing source code, prompts, headers,
                local paths, and infrastructure metadata. Use local storage, redaction, or controlled export
                workflows before sharing reports.
              </p>
              <p>
                The live demo at app.agentsight.us uses a recorded sample session. It is separate from
                this product site so the marketing page remains static, crawlable, and easy to deploy.
              </p>
            </div>
          </div>
          <div className="mt-10">
            <PrimaryCta />
          </div>
        </div>
      </section>
    </PageShell>
  );
}
