export interface AgentFlameWeightedStack {
  stack: string;
  weight: number;
}

export interface AgentFlameCounterSummary {
  total_weight: number;
  unique_stacks: number;
  compression_ratio: number;
  max_stack_reuse: number;
  top: AgentFlameWeightedStack[];
}

export interface AgentFlamePromptTag {
  source: string;
  session_id: string;
  agent_sight_session_id?: string;
  session_tag: string;
  prompt_index: number;
  prompt_tag: string;
  prompt_hash: string;
  preview: string;
}

export interface AgentFlameSession {
  source: string;
  session_id: string;
  agent_sight_session_id?: string;
  session_file: string;
  cwd_hash: string;
  agent_role: string;
  model: string;
  session_tag: string;
  start_ts_ms: number | null;
  prompt_count: number;
  tool_count: number;
  llm_count: number;
  prompts: Array<{
    index: number;
    ts_ms: number | null;
    hash: string;
    tag: string;
    preview: string;
  }>;
}

export interface AgentFlameReport {
  schema_version: number;
  generated_at: string;
  served_from?: string;
  project: {
    name: string;
    root: string;
  };
  inputs: {
    scan_files: number;
    max_sessions: number;
    tag_llm_calls: boolean;
    codex_root: string | null;
    claude_root: string | null;
  };
  llm_tagger: {
    requests: number;
    cache_hits: number;
    llm_calls: number;
    llm_successes: number;
    failures: string[];
  };
  warnings: string[];
  sessions: AgentFlameSession[];
  prompt_tags: AgentFlamePromptTag[];
  summary: {
    session_count: number;
    source_counts: Record<string, number>;
    raw_tool_events: number;
    raw_llm_events: number;
    system: AgentFlameCounterSummary;
    nonsemantic_system: AgentFlameCounterSummary;
    token: AgentFlameCounterSummary;
    dimensions: Record<string, AgentFlameCounterSummary>;
    top_prompt_tags: Array<{ tag: string; count: number }>;
    command_summary: Array<Record<string, string | number>>;
    timeline: Array<{ date: string; sessions: number }>;
    semantic_mixing: {
      nonsemantic: AgentFlameMixingSummary;
      flat: AgentFlameMixingSummary;
    };
  };
  artifacts: Record<string, string>;
}

export interface AgentFlameMixingSummary {
  mixed_buckets: number;
  mixed_weight: number;
  mixed_weight_pct: number;
  examples: Array<{
    kind: string;
    baseline_stack: string;
    weight: number;
    semantic_variant_count: number;
    top_semantic_variants: Array<{ semantic: string; weight: number }>;
  }>;
}
