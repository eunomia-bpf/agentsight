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
