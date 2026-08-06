// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// Shared color system for the dashboard.
//
// Design rules (see overview-dashboard design brief):
//  - Categorical hues are assigned in a fixed order tied to the entity, never
//    cycled by render order. `categoricalColor` hashes the entity name so the
//    same model / host / command always lands on the same hue.
//  - Semantic colors (good / warning / critical) are reserved for state and are
//    kept out of the categorical set so state never collides with a series.
//  - The categorical palette is tuned to be distinguishable for deuteranopia /
//    protanopia (Okabe-Ito adjacent) and to read on the light surface the rest
//    of the app uses. Color is never the only encoding — callers pair every
//    chart with a legend and direct labels where there is room.

// Okabe-Ito-adjacent hues, ordered for maximum adjacent contrast. Used for
// arbitrary categorical series (models, hosts, commands, ...).
export const CATEGORICAL_PALETTE = [
  '#0072B2', // blue
  '#E69F00', // orange
  '#009E73', // bluish green
  '#CC79A7', // reddish purple
  '#56B4E9', // sky blue
  '#D55E00', // vermillion
  '#9268C4', // soft violet
  '#7F7F7F', // gray
] as const;

// Fixed mapping for event-type categories. Stable across sessions and renders.
export const EVENT_TYPE_COLORS: Record<string, string> = {
  llm: '#0072B2', // blue
  process: '#9268C4', // violet
  file: '#56B4E9', // sky blue
  network: '#009E73', // bluish green
  system: '#E69F00', // orange
  tool: '#CC79A7', // reddish purple
  session: '#3B5BA5', // indigo
  process_node: '#9268C4',
  other: '#7F7F7F',
};

// Token-component colors. These are the parts of a per-model token stack.
export const TOKEN_COLORS = {
  input: '#0072B2', // blue
  output: '#009E73', // bluish green
  cache_creation: '#E69F00', // orange
  cache_read: '#9268C4', // violet
} as const;

// Semantic state colors — reserved for good / warning / critical state.
export const SEMANTIC_COLORS = {
  good: '#16A34A',
  warning: '#D97706',
  critical: '#DC2626',
} as const;

// Map an arbitrary categorical name to a stable palette index via a string
// hash. Same name -> same hue, every render, independent of input order.
export function categoricalColor(name: string): string {
  return CATEGORICAL_PALETTE[categoricalIndex(name)];
}

export function categoricalIndex(name: string): number {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % CATEGORICAL_PALETTE.length;
}

export function eventTypeColor(type: string): string {
  return EVENT_TYPE_COLORS[type] ?? EVENT_TYPE_COLORS.other;
}
