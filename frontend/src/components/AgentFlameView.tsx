// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useEffect, useMemo, useState } from 'react';
import { AgentFlameGraph } from '@/components/AgentFlameGraph';
import type { AgentFlameReport } from '@/types/agentflame';
import type { AgentSightSnapshot, SnapshotAuditEvent, SnapshotToolCall } from '@/types/event';
import { fetchAgentFlameArtifactText, fetchAgentFlameReport } from '@/utils/agentflame';
import {
  drilldownMembershipMatchesDisplayMap,
  renderAgentFlameModes,
  type AgentFlameDisplayMapRow,
  type AgentFlameDisplayMode,
  type AgentFlameDrilldownRow,
  type AgentFlameRendererModeResult,
} from '@/utils/agentflameDisplayModes';
import { parseCsvRecords } from '@/utils/csv';

interface AgentFlameViewProps {
  basePath?: string;
  snapshot?: AgentSightSnapshot | null;
}

const ARTIFACTS = [
  { key: 'session_system', label: 'Session system' },
  { key: 'prompt_system', label: 'Prompt system' },
  { key: 'session_token', label: 'Session token' },
  { key: 'prompt_token', label: 'Prompt token' },
  { key: 'llm_token', label: 'LLM token' },
  { key: 'tag_bars', label: 'Tags' },
  { key: 'command_bars', label: 'Commands' },
  { key: 'timeline', label: 'Timeline' },
] as const;

const FLAMEGRAPH_ARTIFACTS = [
  {
    key: 'system_flamegraph',
    label: 'Activity',
    headline: 'Where did observed activity accumulate?',
    question: 'Find the prompts and stack paths containing the most observed activity.',
  },
  {
    key: 'token_flamegraph',
    label: 'Tokens',
    headline: 'Where did token usage accumulate?',
    question: 'Find the prompts, models, and calls containing the most token usage.',
  },
] as const;

function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat().format(value ?? 0);
}

function artifactUrl(basePath: string, relative: string): string {
  const encoded = relative.split('/').map(encodeURIComponent).join('/');
  return `${basePath}/api/v1/agentflame/artifacts/${encoded}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function detailString(row: SnapshotAuditEvent, key: string): string | undefined {
  if (!isRecord(row.details)) return undefined;
  const value = row.details[key];
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function toolSessionId(row: SnapshotToolCall): string | undefined {
  return row.session_id ?? undefined;
}

interface CorrelationRow {
  tag: string;
  sessions: number;
  toolCalls: number;
  auditEvents: number;
  processEvents: number;
  fileEvents: number;
  networkEvents: number;
  llmEvents: number;
  pids: number;
}

interface CorrelationSummary {
  matchedSessions: number;
  matchedToolCalls: number;
  matchedAuditEvents: number;
  matchedNetworkTargets: number;
  rows: CorrelationRow[];
}

function promptTagAt(reportSession: AgentFlameReport['sessions'][number], timestampMs: number | null | undefined): string {
  const fallback = reportSession.session_tag || 'session';
  if (!timestampMs || reportSession.prompts.length === 0) return fallback;
  let tag = reportSession.prompts[0]?.tag || fallback;
  for (const prompt of reportSession.prompts) {
    if (prompt.ts_ms && prompt.ts_ms <= timestampMs) {
      tag = prompt.tag || tag;
    } else if (prompt.ts_ms && prompt.ts_ms > timestampMs) {
      break;
    }
  }
  return tag || fallback;
}

function buildCorrelation(report: AgentFlameReport, snapshot: AgentSightSnapshot | null | undefined): CorrelationSummary | null {
  if (!snapshot) return null;

  const sessionById = new Map<string, AgentFlameReport['sessions'][number]>();
  for (const session of report.sessions) {
    sessionById.set(session.session_id, session);
    if (session.agent_sight_session_id) {
      sessionById.set(session.agent_sight_session_id, session);
    }
  }

  const mutable = new Map<string, {
    sessionIds: Set<string>;
    toolCalls: number;
    auditEvents: number;
    processEvents: number;
    fileEvents: number;
    networkEvents: number;
    llmEvents: number;
    pids: Set<number>;
  }>();

  const ensure = (tag: string) => {
    const key = tag || 'session';
    let row = mutable.get(key);
    if (!row) {
      row = {
        sessionIds: new Set<string>(),
        toolCalls: 0,
        auditEvents: 0,
        processEvents: 0,
        fileEvents: 0,
        networkEvents: 0,
        llmEvents: 0,
        pids: new Set<number>(),
      };
      mutable.set(key, row);
    }
    return row;
  };

  const pidToTag = new Map<number, string>();
  const eventIdToTag = new Map<string, string>();
  const matchedSessionIds = new Set<string>();
  let matchedToolCalls = 0;

  for (const row of snapshot.sessions ?? []) {
    const reportSession = sessionById.get(row.id);
    if (!reportSession) continue;
    ensure(reportSession.session_tag).sessionIds.add(reportSession.session_id);
    matchedSessionIds.add(reportSession.session_id);
  }

  for (const tool of snapshot.tool_calls ?? []) {
    const sessionId = toolSessionId(tool);
    const reportSession = sessionId ? sessionById.get(sessionId) : undefined;
    if (!reportSession) continue;
    const tag = promptTagAt(reportSession, tool.start_timestamp_ms ?? tool.timestamp_ms);
    const bucket = ensure(tag);
    bucket.sessionIds.add(reportSession.session_id);
    matchedSessionIds.add(reportSession.session_id);
    bucket.toolCalls += 1;
    matchedToolCalls += 1;
    if (tool.related_pid) {
      bucket.pids.add(tool.related_pid);
      pidToTag.set(tool.related_pid, tag);
    }
    if (tool.related_event_id) {
      eventIdToTag.set(tool.related_event_id, tag);
    }
  }

  let matchedAuditEvents = 0;
  for (const audit of snapshot.audit_events ?? []) {
    const sessionId = detailString(audit, 'session_id');
    const session = sessionId ? sessionById.get(sessionId) : undefined;
    const tag = session
      ? promptTagAt(session, audit.timestamp_ms)
      : eventIdToTag.get(audit.id) ?? (audit.pid ? pidToTag.get(audit.pid) : undefined);
    if (!tag) continue;
    const bucket = ensure(tag);
    matchedAuditEvents += 1;
    bucket.auditEvents += 1;
    if (audit.pid) bucket.pids.add(audit.pid);
    if (audit.audit_type === 'process') bucket.processEvents += 1;
    if (audit.audit_type === 'file') bucket.fileEvents += 1;
    if (audit.audit_type === 'network') bucket.networkEvents += 1;
    if (audit.audit_type === 'llm') bucket.llmEvents += 1;
  }

  let matchedNetworkTargets = 0;
  for (const target of snapshot.network_targets ?? []) {
    if (!target.pid) continue;
    const tag = pidToTag.get(target.pid);
    if (!tag) continue;
    const bucket = ensure(tag);
    bucket.networkEvents += target.count ?? 1;
    bucket.pids.add(target.pid);
    matchedNetworkTargets += 1;
  }

  const rows = Array.from(mutable.entries()).map(([tag, row]) => ({
    tag,
    sessions: row.sessionIds.size,
    toolCalls: row.toolCalls,
    auditEvents: row.auditEvents,
    processEvents: row.processEvents,
    fileEvents: row.fileEvents,
    networkEvents: row.networkEvents,
    llmEvents: row.llmEvents,
    pids: row.pids.size,
  })).sort((a, b) => (
    (b.auditEvents + b.toolCalls + b.networkEvents)
    - (a.auditEvents + a.toolCalls + a.networkEvents)
  ));

  return {
    matchedSessions: matchedSessionIds.size,
    matchedToolCalls,
    matchedAuditEvents,
    matchedNetworkTargets,
    rows,
  };
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  );
}

function BarList({ rows }: { rows: Array<{ tag: string; count: number }> }) {
  const max = Math.max(1, ...rows.map(row => row.count));
  return (
    <div className="space-y-2">
      {rows.slice(0, 12).map(row => (
        <div key={row.tag} className="grid grid-cols-[8rem_1fr_3rem] items-center gap-3 text-sm">
          <div className="font-medium text-gray-700 truncate" title={row.tag}>{row.tag}</div>
          <div className="h-3 rounded bg-gray-100 overflow-hidden">
            <div
              className="h-full bg-blue-600"
              style={{ width: `${Math.max(3, (row.count / max) * 100)}%` }}
            />
          </div>
          <div className="text-right text-gray-500">{row.count}</div>
        </div>
      ))}
    </div>
  );
}

function toDisplayMapRows(rows: Record<string, string>[]): AgentFlameDisplayMapRow[] {
  return rows
    .filter(row => row.dimension && row.raw_tag && row.active_display_tag)
    .map(row => ({
      dimension: row.dimension,
      raw_tag: row.raw_tag,
      active_display_tag: row.active_display_tag,
      support: row.support || '0',
      requires_review: row.requires_review,
      is_long_tail: row.is_long_tail,
      candidate_display_tag: row.candidate_display_tag,
      candidate_source: row.candidate_source,
      candidate_state: row.candidate_state,
      governance_action: row.governance_action,
      active_source: row.active_source,
    }));
}

function toDrilldownRows(rows: Record<string, string>[]): AgentFlameDrilldownRow[] {
  return rows
    .filter(row => row.dimension && row.active_display_tag)
    .map(row => ({
      dimension: row.dimension,
      active_display_tag: row.active_display_tag,
      support: row.support || '0',
      raw_tag_count: row.raw_tag_count || '0',
      raw_tags: row.raw_tags || '',
      review_required_rows: row.review_required_rows,
      review_required_support: row.review_required_support,
      candidate_rows: row.candidate_rows,
      active_merge_rows: row.active_merge_rows,
      top_processes: row.top_processes,
      top_effects: row.top_effects,
      top_paths: row.top_paths,
      top_context_tags: row.top_context_tags,
    }));
}

function DisplayModePanel({
  result,
  selectedMode,
  onModeChange,
  membershipMatches,
}: {
  result: AgentFlameRendererModeResult;
  selectedMode: AgentFlameDisplayMode;
  onModeChange: (mode: AgentFlameDisplayMode) => void;
  membershipMatches: boolean;
}) {
  return (
    <div
      className="bg-white rounded-lg shadow-md p-4"
      data-agentflame-display-panel="true"
      data-display-mode={selectedMode}
      data-bucket-count={result.bucketCount}
      data-total-support={result.totalSupport}
      data-candidate-overlay-rows={result.candidateOverlayRows}
      data-review-required-rows={result.reviewRequiredRows}
      data-membership-matches={String(membershipMatches)}
    >
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Display modes</h3>
        <div className="inline-flex overflow-hidden rounded-lg border border-gray-200 bg-white">
          {(['raw', 'display', 'pending'] as AgentFlameDisplayMode[]).map(mode => (
            <button
              key={mode}
              type="button"
              data-agentflame-display-mode-button={mode}
              aria-pressed={selectedMode === mode}
              onClick={() => onModeChange(mode)}
              className={`border-r border-gray-200 px-4 py-2 text-sm last:border-r-0 ${
                selectedMode === mode ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
        {[
          ['Mode', selectedMode],
          ['Buckets', formatNumber(result.bucketCount)],
          ['Support', formatNumber(result.totalSupport)],
          ['Candidates', formatNumber(result.candidateOverlayRows)],
          ['Review rows', formatNumber(result.reviewRequiredRows)],
        ].map(([label, value]) => (
          <div key={label} className="border-b border-gray-100 pb-2">
            <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
            <div className="mt-1 text-lg font-semibold text-gray-900">{value}</div>
          </div>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-3 py-2">Rank</th>
              <th className="px-3 py-2">Dimension</th>
              <th className="px-3 py-2">Tag</th>
              <th className="px-3 py-2 text-right">Support</th>
              <th className="px-3 py-2 text-right">Raw tags</th>
              <th className="px-3 py-2 text-right">Pending</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {result.buckets.slice(0, 10).map((bucket, index) => (
              <tr key={`${bucket.mode}-${bucket.dimension}-${bucket.displayTag}-${index}`}>
                <td className="px-3 py-2 text-gray-600">{index + 1}</td>
                <td className="px-3 py-2 text-gray-600">{bucket.dimension}</td>
                <td className="px-3 py-2 font-medium text-gray-900">{bucket.displayTag}</td>
                <td className="px-3 py-2 text-right text-gray-700">{formatNumber(bucket.support)}</td>
                <td className="px-3 py-2 text-right text-gray-700">{formatNumber(bucket.rawTagCount)}</td>
                <td className="px-3 py-2 text-right text-gray-700">
                  {bucket.hasPendingOverlay ? formatNumber(bucket.candidateRows + bucket.reviewRequiredRows) : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AgentFlameView({ basePath = '', snapshot = null }: AgentFlameViewProps) {
  const [report, setReport] = useState<AgentFlameReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedArtifact, setSelectedArtifact] = useState<string>('session_system');
  const [selectedFlamegraph, setSelectedFlamegraph] = useState<string>('system_flamegraph');
  const [displayMode, setDisplayMode] = useState<AgentFlameDisplayMode>('display');
  const [displayRows, setDisplayRows] = useState<AgentFlameDisplayMapRow[] | null>(null);
  const [drilldownRows, setDrilldownRows] = useState<AgentFlameDrilldownRow[] | null>(null);
  const [displayModeError, setDisplayModeError] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchAgentFlameReport(basePath)
      .then(next => {
        if (!cancelled) setReport(next);
      })
      .catch(() => {
        if (!cancelled) setReport(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [basePath]);

  useEffect(() => {
    let cancelled = false;
    const displayMapPath = report?.artifacts.active_display_map;
    const drilldownPath = report?.artifacts.display_drilldown;
    setDisplayRows(null);
    setDrilldownRows(null);
    setDisplayModeError('');
    if (!displayMapPath || !drilldownPath) return () => {
      cancelled = true;
    };

    Promise.all([
      fetchAgentFlameArtifactText(basePath, displayMapPath),
      fetchAgentFlameArtifactText(basePath, drilldownPath),
    ])
      .then(([displayCsv, drilldownCsv]) => {
        if (cancelled) return;
        setDisplayRows(toDisplayMapRows(parseCsvRecords(displayCsv)));
        setDrilldownRows(toDrilldownRows(parseCsvRecords(drilldownCsv)));
      })
      .catch(error => {
        if (!cancelled) setDisplayModeError(error instanceof Error ? error.message : 'display artifact unavailable');
      });
    return () => {
      cancelled = true;
    };
  }, [basePath, report]);

  const artifactChoices = useMemo(() => {
    if (!report) return [];
    return ARTIFACTS.filter(item => Boolean(report.artifacts[item.key]));
  }, [report]);

  const flamegraphChoices = useMemo(() => {
    if (!report) return [];
    return FLAMEGRAPH_ARTIFACTS
      .filter(item => Boolean(report.artifacts[item.key]))
      .map(item => ({ ...item, path: report.artifacts[item.key] }));
  }, [report]);

  const activeArtifact = useMemo(() => {
    if (!report || artifactChoices.length === 0) return null;
    const choice = artifactChoices.find(item => item.key === selectedArtifact) ?? artifactChoices[0];
    return {
      label: choice.label,
      path: report.artifacts[choice.key],
    };
  }, [artifactChoices, report, selectedArtifact]);

  const correlation = useMemo(() => {
    return report ? buildCorrelation(report, snapshot) : null;
  }, [report, snapshot]);

  const displayModeResult = useMemo(() => {
    if (!displayRows || !drilldownRows) return null;
    const membershipMatches = drilldownMembershipMatchesDisplayMap(displayRows, drilldownRows);
    if (!membershipMatches) return { membershipMatches, modes: null };
    return { membershipMatches, modes: renderAgentFlameModes(displayRows, drilldownRows) };
  }, [displayRows, drilldownRows]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-b-2 border-blue-600" />
        <p className="text-gray-500">Loading AgentFlame report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-xl font-semibold text-gray-900">AgentFlame</h2>
        <p className="mt-2 text-sm text-gray-600">
          No local report was found at <code>.agentsight/agentflame/latest/agentflame.json</code>.
        </p>
        <pre className="mt-4 overflow-x-auto rounded-md bg-gray-900 px-4 py-3 text-sm text-green-400">
          PYTHONPATH=agentflame python3 -m agentflame --project-root . --out .agentsight/agentflame/latest
        </pre>
      </div>
    );
  }

  const summary = report.summary;
  const promptCount = report.sessions.reduce((sum, session) => sum + session.prompt_count, 0);
  const dashboard = report.artifacts.dashboard;
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">AgentFlame</h2>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
              <span>{report.project.name}</span>
              <span>{new Date(report.generated_at).toLocaleString()}</span>
              <span>Local aggregate profile</span>
            </div>
          </div>
          {dashboard && (
            <a
              href={artifactUrl(basePath, dashboard)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center rounded-md border border-blue-300 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
            >
              Open dashboard
            </a>
          )}
        </div>
      </div>

      <AgentFlameGraph
        basePath={basePath}
        choices={flamegraphChoices}
        selectedKey={selectedFlamegraph}
        onSelect={setSelectedFlamegraph}
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Sessions" value={formatNumber(summary.session_count)} />
        <StatCard label="Prompts" value={formatNumber(promptCount)} />
        <StatCard label="Tool events" value={formatNumber(summary.raw_tool_events)} />
        <StatCard label="Token total" value={formatNumber(summary.token.total_weight)} />
      </div>

      {correlation && (
        <details className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-gray-700">
            Captured evidence by prompt ({formatNumber(correlation.matchedAuditEvents)} events)
          </summary>
          <div className="border-t border-gray-100 p-4">
            <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Snapshot correlation</h3>
              <div className="mt-1 text-sm text-gray-500">
                {formatNumber(correlation.matchedSessions)} sessions, {formatNumber(correlation.matchedToolCalls)} tool calls, {formatNumber(correlation.matchedAuditEvents)} audit events, {formatNumber(correlation.matchedNetworkTargets)} network targets matched
              </div>
            </div>
          </div>
          {correlation.rows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                  <tr>
                    <th className="px-3 py-2">Tag</th>
                    <th className="px-3 py-2 text-right">Tools</th>
                    <th className="px-3 py-2 text-right">Audit</th>
                    <th className="px-3 py-2 text-right">Process</th>
                    <th className="px-3 py-2 text-right">Files</th>
                    <th className="px-3 py-2 text-right">Network</th>
                    <th className="px-3 py-2 text-right">LLM</th>
                    <th className="px-3 py-2 text-right">PIDs</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {correlation.rows.slice(0, 12).map(row => (
                    <tr key={row.tag}>
                      <td className="px-3 py-2 font-medium text-gray-900">{row.tag}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.toolCalls}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.auditEvents}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.processEvents}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.fileEvents}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.networkEvents}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.llmEvents}</td>
                      <td className="px-3 py-2 text-right text-gray-700">{row.pids}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              No snapshot events matched the AgentFlame session ids in this report.
            </p>
          )}
          </div>
        </details>
      )}

      {displayModeResult?.modes && (
        <details className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-gray-700">
            Label detail and pending mappings
          </summary>
          <div className="border-t border-gray-100 p-4">
            <DisplayModePanel
              result={displayModeResult.modes[displayMode]}
              selectedMode={displayMode}
              onModeChange={setDisplayMode}
              membershipMatches={displayModeResult.membershipMatches}
            />
          </div>
        </details>
      )}

      {displayModeError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {displayModeError}
        </div>
      )}

      {artifactChoices.length > 0 && <details className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-gray-700">
          Supporting charts ({artifactChoices.length})
        </summary>
        <div className="border-t border-gray-100 p-4">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Supporting views</h3>
            <p className="mt-1 text-sm text-gray-500">Use these charts after the flamegraph identifies a branch worth explaining.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {artifactChoices.map(choice => (
              <button
                key={choice.key}
                onClick={() => setSelectedArtifact(choice.key)}
                className={`rounded-md px-3 py-1 text-sm transition-colors ${
                  (activeArtifact?.path === report.artifacts[choice.key])
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {choice.label}
              </button>
            ))}
          </div>
        </div>
          {activeArtifact && (
          <div className="overflow-x-auto rounded-md border border-gray-200 bg-gray-50">
            <img
              src={artifactUrl(basePath, activeArtifact.path)}
              alt={activeArtifact.label}
              className="min-w-[900px] max-w-none"
            />
          </div>
          )}
        </div>
      </details>}

      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Top prompt tags</h3>
        <BarList rows={summary.top_prompt_tags} />
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Commands and effects</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-3 py-2">Agent</th>
                  <th className="px-3 py-2">Command</th>
                  <th className="px-3 py-2">Effect</th>
                  <th className="px-3 py-2 text-right">Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {summary.command_summary.slice(0, 12).map((row, index) => (
                  <tr key={`${row.agent}-${row.cmd}-${row.effect}-${index}`}>
                    <td className="px-3 py-2 text-gray-600">{row.agent}</td>
                    <td className="px-3 py-2 font-mono text-xs text-gray-700">{row.cmd}</td>
                    <td className="px-3 py-2 text-gray-600">{row.effect}</td>
                    <td className="px-3 py-2 text-right text-gray-900">{row.count}</td>
                  </tr>
                ))}
              </tbody>
          </table>
        </div>
      </div>

      {report.warnings.length > 0 && (
        <div className="bg-amber-50 rounded-lg border border-amber-200 p-4 text-sm text-amber-800">
          <div className="font-semibold">Warnings</div>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {report.warnings.slice(0, 6).map(warning => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
