// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Metadata } from 'next';
import {
  Boxes,
  Clock3,
  FileWarning,
  GitPullRequest,
  Network,
  SquareTerminal,
  Workflow,
} from 'lucide-react';
import { Eyebrow, PageShell, PrimaryCta } from '../components';

export const metadata: Metadata = {
  title: 'Use Cases',
  description:
    'Use AgentSight to profile slow AI agent runs, review AI-generated PRs, trace closed-source agent CLIs, audit MCP tools, and investigate risky file or network behavior.',
  alternates: {
    canonical: '/use-cases/',
  },
};

const cases = [
  {
    id: 'slow-runs',
    title: 'Profile slow or expensive agent runs',
    pain: 'The agent ran for 25 minutes and burned through tokens, but the transcript does not explain where the time went.',
    outcome:
      'Break the run down by model calls, shell time, repeated scans, long-running subprocesses, network waits, CPU, and memory.',
    signals: ['LLM turns and token volume', 'Repeated file reads', 'Failed commands and retries', 'CPU and memory samples'],
    icon: Clock3,
  },
  {
    id: 'pr-review',
    title: 'Review AI-generated PRs faster',
    pain: 'A diff tells you what changed, not how the agent got there or whether it actually ran the checks it claimed.',
    outcome:
      'Attach a run profile to an AI-generated PR with commands, tests, failures, touched files, network calls, and run cost.',
    signals: ['Commands and exit status', 'Files written and deleted', 'Test retries', 'Repo-external access'],
    icon: GitPullRequest,
  },
  {
    id: 'closed-source',
    title: 'Trace closed-source agent CLIs',
    pain: 'Claude Code, Codex, Gemini CLI, and other agents expose different logs and hooks, and some behavior happens in child processes.',
    outcome:
      'Trace the agent process tree from outside the application without SDKs, proxies, or vendor-specific integrations.',
    signals: ['Process lineage', 'TLS model traffic', 'Shell commands', 'Network destinations'],
    icon: SquareTerminal,
  },
  {
    id: 'insight-artifacts',
    title: 'Generate shareable insight pages',
    pain: 'Raw traces are too detailed for reviewers, managers, or tool authors. They need findings, evidence, and next actions in one page.',
    outcome:
      'Use an AgentSight skill to drive the profiling workflow and guide the agent from raw evidence to a self-contained HTML artifact.',
    signals: ['Profiling playbook', 'Tool selection', 'Severity-ranked findings', 'Public redaction mode'],
    icon: Workflow,
  },
  {
    id: 'tool-audit',
    title: 'Audit MCP servers, skills, and plugins',
    pain: 'A tool says it is read-only, but the interesting question is what it does during a real agent run.',
    outcome:
      'Run tools under system-level tracing and inspect file writes, child processes, external calls, and token impact.',
    signals: ['Tool-triggered process spawns', 'File writes', 'External endpoints', 'Token and time impact'],
    icon: Boxes,
  },
  {
    id: 'incident',
    title: 'Find the moment an agent run went wrong',
    pain: 'A repo or environment is broken after a long session, and the final transcript is too coarse to identify the turning point.',
    outcome:
      'Use the timeline to inspect the prompt, command, process, file operation, and network event around the failure.',
    signals: ['Timeline by event type', 'File delete and truncate events', 'Failed command clusters', 'Network calls before failure'],
    icon: FileWarning,
  },
  {
    id: 'network',
    title: 'Inspect unexpected network behavior',
    pain: 'Agent tools can run package managers, scripts, browsers, and cloud CLIs. Not every connection is visible in an LLM trace.',
    outcome:
      'Attribute network endpoints back to the agent process family and inspect them alongside the prompt and command context.',
    signals: ['Destination hosts and ports', 'Process attribution', 'LLM provider traffic', 'Unexpected external calls'],
    icon: Network,
  },
];

export default function UseCasesPage() {
  return (
    <PageShell>
      <section className="bg-white py-16">
        <div className="container-page">
          <Eyebrow>Use cases</Eyebrow>
          <h1 className="max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
            AgentSight is for the moments when an agent run becomes too expensive, slow, risky, or hard to review.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-slate-600">
            Start from a real run, not a synthetic dashboard. AgentSight gives you a system-level profile
            and skillset you can use for debugging, review, tool evaluation, and incident investigation.
          </p>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-slatepaper py-14">
        <div className="container-page grid gap-5">
          {cases.map((item) => {
            const Icon = item.icon;
            return (
              <article id={item.id} key={item.id} className="scroll-mt-24 rounded-lg border border-slate-200 bg-white p-6">
                <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
                  <div>
                    <Icon className="h-7 w-7 text-river" />
                    <h2 className="mt-4 text-2xl font-semibold text-ink">{item.title}</h2>
                  </div>
                  <div className="grid gap-5 md:grid-cols-2">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wide text-ember">Pain</div>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{item.pain}</p>
                    </div>
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wide text-mint">Profile outcome</div>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{item.outcome}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex flex-wrap gap-2">
                  {item.signals.map((signal) => (
                    <span key={signal} className="rounded-md border border-slate-200 bg-slatepaper px-3 py-1 text-xs font-medium text-slate-700">
                      {signal}
                    </span>
                  ))}
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="container-page grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <h2 className="text-3xl font-semibold text-ink">Try the run viewer first.</h2>
            <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
              The live demo uses a recorded Claude Code session. The reference docs stay on Eunomia
              for install, runtime, Docker, and OpenTelemetry details.
            </p>
          </div>
          <PrimaryCta />
        </div>
      </section>
    </PageShell>
  );
}
