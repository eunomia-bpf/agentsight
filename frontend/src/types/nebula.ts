// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

/** Prepared Agent Nebula document from GET /api/v1/nebula (server-side layout). */

export interface NebulaMeta {
  repository: string;
  source: string;
  window_start_ms: number | null;
  window_end_ms: number | null;
  total_file_events: number;
  total_unique_files: number;
  shown_stars: number;
  shown_frames: number;
  max_stars: number;
  max_frames: number;
  bounding_policy: string;
  empty: boolean;
  empty_reason: string | null;
}

export interface NebulaArea {
  name: string;
  color: string;
  count: number;
}

export interface NebulaStar {
  id: number;
  path: string;
  area: string;
  x: number;
  y: number;
  color: string;
  first_ms: number;
  last_ms: number;
  visits: number;
  birth_frame: number;
}

export interface NebulaActive {
  id: number;
  access: string;
  strength: number;
}

export interface NebulaFrame {
  index: number;
  t_ms: number;
  summary: string;
  active: NebulaActive[];
}

export interface NebulaDocument {
  meta: NebulaMeta;
  areas: NebulaArea[];
  stars: NebulaStar[];
  frames: NebulaFrame[];
}
