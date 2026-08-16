// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export interface SnapshotSummary {
  source?: string;
  view_events?: number;
  llm_calls?: number;
  token_usage_rows?: number;
  audit_events?: number;
  sessions?: number;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  start_timestamp_ms?: number | null;
  end_timestamp_ms?: number | null;
  audit_limit?: number;
}

export interface SnapshotTokenSummary {
  group: string;
  input_tokens?: number;
  output_tokens?: number;
  cache_creation_tokens?: number;
  cache_read_tokens?: number;
  total_tokens?: number;
  calls?: number;
}

export interface SnapshotNetworkTarget {
  pid?: number | null;
  comm?: string | null;
  host: string;
  path?: string | null;
  count?: number;
  error_count?: number;
  first_timestamp_ms?: number | null;
  last_timestamp_ms?: number | null;
}

export interface SnapshotAuditEvent {
  id: string;
  timestamp_ms: number;
  audit_type: string;
  pid?: number | null;
  comm?: string | null;
  subject?: string | null;
  action?: string | null;
  target?: string | null;
  status?: string | null;
  summary?: string | null;
  details?: unknown;
}

export interface SnapshotProcessNode {
  id: string;
  pid: number;
  ppid?: number | null;
  root_pid?: number | null;
  start_timestamp_ms?: number | null;
  end_timestamp_ms?: number | null;
  comm?: string | null;
  command?: string | null;
  argv?: string[];
  cwd?: string | null;
  exit_code?: number | null;
  status?: string | null;
}

export interface SnapshotResourceSample {
  timestamp_ms: number;
  pid?: number | null;
  comm?: string | null;
  cpu_percent?: number | null;
  rss_mb?: number | null;
}

export interface SnapshotSession {
  id: string;
  agent_type: string;
  start_timestamp_ms: number;
  end_timestamp_ms?: number | null;
  status?: string;
  model?: string | null;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  attributes?: unknown;
}

export interface CodingPlanStep {
  step: string;
  status: string;
}

export interface SubscriptionWindow {
  used_percent?: number | null;
  window_minutes?: number | null;
  resets_at?: number | null;
}

export interface SourceSubscription {
  provider: string;
  observed_at?: string | null;
  plan_type?: string | null;
  limit_name?: string | null;
  primary?: SubscriptionWindow | null;
  secondary?: SubscriptionWindow | null;
  credits?: { unlimited?: boolean | null } | null;
}

export interface TokenUsage {
  input_tokens?: number;
  output_tokens?: number;
  cache_creation_tokens?: number;
  cache_read_tokens?: number;
  total_tokens?: number;
}

export interface LiveProcess {
  pid: number;
  ppid: number;
  start_timestamp_ms?: number | null;
  comm: string;
  command: string;
  cwd?: string | null;
  cpu_percent: number;
  rss_mb: number;
}

export interface LiveSession {
  session_id?: string | null;
  session: string;
  agent: string;
  pid?: number | null;
  model?: string | null;
  age_s?: number | null;
  cpu_percent: number;
  rss_mb: number;
  processes: number;
  tokens?: number | null;
  tools: number;
  execs: number;
  failures: number;
  files: number;
  network: number;
  trace: string;
  command: string;
  workspace?: string | null;
  last_message_at?: string | null;
  process_details: LiveProcess[];
  plan: CodingPlanStep[];
  subscription?: SourceSubscription | null;
}

export interface LiveOverview {
  mode: string;
  total_tokens: number;
  rows: LiveSession[];
  failures: string[];
  notes: string[];
}

export interface SnapshotToolCall {
  id: string;
  session_id?: string | null;
  timestamp_ms: number;
  tool_name?: string | null;
  status?: string | null;
  input?: unknown;
  output?: unknown;
  related_pid?: number | null;
}

export interface AgentSightSnapshot {
  schema_version?: number;
  generated_at?: string;
  summary?: SnapshotSummary;
  token_summary?: SnapshotTokenSummary[];
  network_targets?: SnapshotNetworkTarget[];
  process_nodes?: SnapshotProcessNode[];
  audit_events?: SnapshotAuditEvent[];
  resource_samples?: SnapshotResourceSample[];
  sessions?: SnapshotSession[];
  tool_calls?: SnapshotToolCall[];
}
