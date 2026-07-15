export type Vendor = "claude" | "codex" | "gemini" | string;
export type AssociationState =
  | "no_candidate"
  | "unique_candidate"
  | "ambiguous_candidates"
  | "not_eligible";

export interface GalleryMeta {
  repository: string;
  root_id: string;
  endpoint_revision: string;
  window_start_ms: number;
  window_end_ms: number;
  source: string;
  association_mode: string;
  association_caveat: string;
  reported_token_caveat: string;
  right_censored_days: string[];
  missing_cells: Array<{ cell: string; status: string; reason: string }>;
}

export interface SourceDay {
  day: string;
  sessions: number;
  events: number;
  path_events: number;
  write_event_paths: number;
  quantitative_status: "mature_descriptive" | "right_censored_excluded";
}

export interface GallerySession {
  id: string;
  vendor: Vendor;
  model: string;
  started_at_ms: number | null;
  ended_at_ms: number | null;
  tool_events: number;
  reported_tokens: number;
  days: string[];
}

export interface GalleryEvent {
  id: string;
  event_id: string;
  session_id: string;
  vendor: Vendor;
  model: string;
  ts_ms: number;
  day: string;
  action: string;
  category: string;
  effect: string;
  status: string;
  prompt_index: number;
  path: string;
  group: string;
  association_state: AssociationState;
  candidate_count: number;
  evidence_bin: string | null;
  exact_hunk: boolean;
}

export interface TimeBucket {
  ts_ms: number;
  events?: number;
  read?: number;
  write?: number;
  test?: number;
  process?: number;
  network?: number;
  repo?: number;
  commits?: number;
  merges?: number;
  additions?: number;
  deletions?: number;
  reported_tokens?: number;
}

export interface GalleryFile {
  path: string;
  group: string;
  extension: string;
  lifetime_id: string | null;
  birth_ms: number;
  death_ms: number | null;
  survives_to_head: boolean;
  current_path: string | null;
  current_bytes: number;
  touches: number;
  read_events: number;
  write_events: number;
  verify_events: number;
  other_events: number;
  git_changes: number;
  additions: number;
  deletions: number;
  churn: number;
  net_lines: number;
  risk_score: number;
  pattern: string;
  vendors: string[];
  sessions: string[];
  authors: string[];
  first_event_ms: number | null;
  last_event_ms: number | null;
  daily: Record<string, Record<string, number>>;
  association_states: Record<string, number>;
  effect_counts: Record<string, number>;
  stable_x: number;
  stable_y: number;
}

export interface TreeNode {
  name: string;
  path?: string;
  value: number;
  touches?: number;
  risk_score?: number;
  pattern?: string;
  children?: TreeNode[];
}

export interface GitCommit {
  id: string;
  parents: string[];
  committed_at_ms: number;
  author_label: string;
  is_merge: boolean;
}

export interface GitChange {
  id: string;
  commit_id: string;
  committed_at_ms: number;
  status: string;
  old_path: string | null;
  path: string;
  additions: number;
  deletions: number;
  lifetime_id: string;
  is_merge: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  count: number;
  semantics: string;
  vendors?: Record<string, number>;
}

export interface LinePixel {
  path: string;
  line: number;
  origin_commit: string;
  origin_ms: number;
  author_label: string;
}

export interface SurvivalCohort {
  cohort: string;
  born_files: number;
  surviving_files?: number;
  dead_files?: number;
  surviving_bytes?: number;
}

export interface OwnershipRow {
  author: string;
  group: string;
  changes: number;
  churn: number;
}

export interface GalleryData {
  schema: string;
  meta: GalleryMeta;
  source_days: SourceDay[];
  summary: Record<string, number>;
  sessions: GallerySession[];
  events: GalleryEvent[];
  time_buckets: TimeBucket[];
  files: GalleryFile[];
  tree: TreeNode;
  commits: GitCommit[];
  changes: GitChange[];
  cochange_edges: GraphEdge[];
  line_pixels: LinePixel[];
  survival_cohorts: SurvivalCohort[];
  ownership: OwnershipRow[];
}

export type FamilyId =
  | "overview"
  | "pixel"
  | "matrix"
  | "map"
  | "animation"
  | "river"
  | "forensic"
  | "storylines"
  | "longitudinal";

export interface ViewState {
  family: FamilyId;
  cursorMs: number;
  rangeStartMs: number;
  rangeEndMs: number;
  playing: boolean;
  speedHoursPerSecond: number;
  vendors: Set<string>;
  associationStates: Set<string>;
  selectedPath: string | null;
  selectedSession: string | null;
}
