// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';
import Image from 'next/image';
import {
  ArrowRight,
  BadgeCheck,
  Cpu,
  FileText,
  GitPullRequest,
  Network,
  ShieldAlert,
  SquareTerminal,
} from 'lucide-react';
import { CommandBlock, Eyebrow, PageShell, PrimaryCta, TextLink } from './components';
import { artifactFlow, heroStats, quickstart, signalPillars, trustSignals, useCases } from './data';

export const metadata: Metadata = {
  alternates: {
    canonical: '/',
  },
};

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'AgentSight',
  applicationCategory: 'DeveloperApplication',
  operatingSystem: 'Linux',
  description:
    'System-level profiling/tracing tools and skills for AI agents, powered by eBPF. Helps agents understand time, tokens, commands, files, network calls, and system resources without SDKs.',
  url: 'https://agentsight.us/',
  codeRepository: 'https://github.com/eunomia-bpf/agentsight',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
  publisher: {
    '@type': 'Organization',
    name: 'Eunomia',
    url: 'https://eunomia.dev/',
  },
};

export default function Home() {
  return (
    <PageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <section className="border-b border-slate-200 bg-white">
        <div className="container-page grid gap-12 py-16 lg:grid-cols-[1.02fr_0.98fr] lg:items-center lg:py-20">
          <div>
            <Eyebrow>System-level AI agent profiling</Eyebrow>
            <h1 className="max-w-4xl text-5xl font-semibold leading-[1.02] tracking-normal text-ink sm:text-6xl">
              Let your agents profile AI agents like programs.
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
              System-level profiling/tracing tools and skills for Claude Code, Codex, and other
              local agents. Understand where time, tokens, commands, files, network calls, and
              system resources go, without SDKs.
            </p>
            <div className="mt-8">
              <PrimaryCta />
            </div>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {heroStats.map((stat) => (
                <div key={stat.label} className="rounded-md border border-slate-200 bg-slatepaper px-4 py-3">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{stat.label}</div>
                  <div className="mt-1 text-sm font-semibold text-ink">{stat.value}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-950 shadow-soft">
              <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  <Cpu className="h-4 w-4 text-emerald-300" />
                  AgentSight live sessions
                </div>
                <div className="rounded-md bg-emerald-400/10 px-2 py-1 text-xs font-medium text-emerald-200">
                  recorded demo
                </div>
              </div>
              <Image
                src="/images/top-mode-demo.png"
                alt="AgentSight top mode live session view"
                width={2266}
                height={1034}
                className="h-auto w-full"
                priority
              />
            </div>
            <CommandBlock commands={quickstart} />
          </div>
        </div>
      </section>

      <section className="bg-slatepaper py-14">
        <div className="container-page">
          <div className="grid gap-4 md:grid-cols-3">
            {trustSignals.map((signal) => {
              const Icon = signal.icon;
              return (
                <div key={signal.label} className="flex items-start gap-3 rounded-md border border-slate-200 bg-white p-4">
                  <Icon className="mt-0.5 h-5 w-5 text-mint" />
                  <div>
                    <div className="text-sm font-semibold text-ink">{signal.label}</div>
                    <div className="mt-1 text-sm text-slate-600">{signal.value}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="container-page">
          <div className="max-w-3xl">
            <Eyebrow>What AgentSight profiles</Eyebrow>
            <h2 className="text-3xl font-semibold text-ink sm:text-4xl">
              One run profile for the parts normal LLM traces miss.
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              Application traces are useful when you own the agent code. AgentSight focuses on the
              system boundary: the child processes, file operations, network destinations, resources,
              and model traffic that shape the actual run.
            </p>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {signalPillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div key={pillar.label} className="rounded-md border border-slate-200 bg-slatepaper p-5">
                  <Icon className="h-6 w-6 text-river" />
                  <h3 className="mt-4 text-lg font-semibold text-ink">{pillar.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{pillar.value}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-16">
        <div className="container-page grid gap-10 lg:grid-cols-[0.92fr_1.08fr] lg:items-start">
          <div>
            <Eyebrow>Semantic gap</Eyebrow>
            <h2 className="text-3xl font-semibold text-ink sm:text-4xl">
              Traditional observability cannot parse what an agent was trying to do.
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              AI agents execute unpredictable actions that break the assumptions of static
              dashboards. The hard problem is not collecting more telemetry. The hard problem is
              connecting natural language intent to low-level OS side effects.
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-xl font-semibold text-ink">Observer-agent workflow</h3>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              AgentSight gives an independent observer agent the system-level tools and skills it
              needs to correlate prompts, model calls, commands, files, network, and resources. The
              output is not just a raw trace; it is a causally linked run profile, report, or Agent
              Flamegraph that explains where the run went.
            </p>
            <div className="mt-5 grid gap-3 text-sm text-slate-700">
              {[
                'Prompt intent and agent decisions',
                'LLM traffic, tokens, and model calls',
                'Processes, commands, files, network, CPU, and memory',
                'Skill-guided analysis artifacts for humans and agents',
              ].map((item) => (
                <div key={item} className="rounded-md border border-slate-200 bg-slatepaper px-4 py-3">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-16">
        <div className="container-page grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <Eyebrow>High-pain workflows</Eyebrow>
            <h2 className="text-3xl font-semibold text-ink sm:text-4xl">
              Built for runs that are slow, expensive, risky, or hard to review.
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              The best first use is not another dashboard. It is a profile you can open after a real
              agent run and use to answer why the run was costly, where it stalled, or what happened
              around a failure.
            </p>
            <div className="mt-6">
              <TextLink href="/use-cases/">Explore use cases</TextLink>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {useCases.map((item) => {
              const Icon = item.icon;
              return (
                <a
                  key={item.title}
                  href={item.href}
                  className="group rounded-md border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300"
                >
                  <Icon className="h-6 w-6 text-ember" />
                  <h3 className="mt-4 text-lg font-semibold text-ink">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
                  <div className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-river group-hover:text-blue-700">
                    Read more
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="container-page">
          <div className="grid gap-10 lg:grid-cols-[1fr_1fr] lg:items-center">
            <div>
              <Eyebrow>Sample run profile</Eyebrow>
              <h2 className="text-3xl font-semibold text-ink sm:text-4xl">
                Turn a long agent session into a compact profile.
              </h2>
              <p className="mt-4 text-base leading-7 text-slate-600">
                Use AgentSight during a coding run, then inspect a saved SQLite session, live UI, or
                exported snapshot. The product page links to the app demo; the reference docs stay on
                Eunomia.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  href="https://app.agentsight.us/"
                  className="inline-flex items-center gap-2 rounded-md bg-river px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                >
                  <FileText className="h-4 w-4" />
                  Open demo
                </a>
                <a
                  href="https://eunomia.dev/agentsight/"
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-ink hover:border-slate-400"
                >
                  Read docs
                </a>
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slatepaper p-4">
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  { label: 'Commands executed', value: '37', icon: SquareTerminal },
                  { label: 'Files touched', value: '124', icon: FileText },
                  { label: 'Network destinations', value: '6', icon: Network },
                  { label: 'Risk flags', value: '2', icon: ShieldAlert },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.label} className="rounded-md border border-slate-200 bg-white p-4">
                      <Icon className="h-5 w-5 text-river" />
                      <div className="mt-4 text-3xl font-semibold text-ink">{item.value}</div>
                      <div className="mt-1 text-sm text-slate-600">{item.label}</div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
                <div className="text-sm font-semibold text-ink">Run timeline highlights</div>
                <div className="mt-4 grid gap-3 text-sm text-slate-600">
                  <div className="flex items-center gap-3">
                    <BadgeCheck className="h-4 w-4 text-mint" />
                    Claude Code launched, model calls captured, process family attached.
                  </div>
                  <div className="flex items-center gap-3">
                    <GitPullRequest className="h-4 w-4 text-river" />
                    Test command failed twice before the final passing run.
                  </div>
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="h-4 w-4 text-ember" />
                    Two repo-external file reads flagged for review.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-16">
        <div className="container-page grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <Eyebrow>Skills and artifacts</Eyebrow>
            <h2 className="text-3xl font-semibold text-ink sm:text-4xl">
              Skills are the control surface, not the afterthought.
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              AgentSight is designed so agents can drive profiling work themselves. Skills tell the
              agent which profiling tools to run, which evidence to collect, which metrics to rank,
              what to redact, and how to turn the trace into a useful artifact. The eBPF tools and
              the skills are co-equal parts of the product.
            </p>
          </div>
          <div className="grid gap-4">
            {artifactFlow.map((step, index) => (
              <div key={step.title} className="rounded-md border border-slate-200 bg-white p-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-ink text-sm font-semibold text-white">
                    {index + 1}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-ink">{step.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-ink py-16 text-white">
        <div className="container-page grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <h2 className="text-3xl font-semibold">Start with a recorded run.</h2>
            <p className="mt-3 max-w-2xl text-base leading-7 text-slate-300">
              Use the app demo, then run AgentSight around a local agent when you are ready to profile
              your own workflow.
            </p>
          </div>
          <PrimaryCta />
        </div>
      </section>
    </PageShell>
  );
}
