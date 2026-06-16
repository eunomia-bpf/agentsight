export type AgentFlameDisplayMode = 'raw' | 'display' | 'pending';

export interface AgentFlameDisplayMapRow {
  dimension: string;
  raw_tag: string;
  active_display_tag: string;
  support: number | string;
  requires_review?: boolean | string;
  is_long_tail?: boolean | string;
  candidate_display_tag?: string;
  candidate_source?: string;
  candidate_state?: string;
  governance_action?: string;
  active_source?: string;
}

export interface AgentFlameDrilldownRow {
  dimension: string;
  active_display_tag: string;
  support: number | string;
  raw_tag_count: number | string;
  raw_tags: string;
  review_required_rows?: number | string;
  review_required_support?: number | string;
  candidate_rows?: number | string;
  active_merge_rows?: number | string;
  top_processes?: string;
  top_effects?: string;
  top_paths?: string;
  top_context_tags?: string;
}

export interface AgentFlameRendererBucket {
  mode: AgentFlameDisplayMode;
  dimension: string;
  displayTag: string;
  support: number;
  rawTagCount: number;
  rawTags: Array<{ tag: string; support: number }>;
  candidateRows: number;
  reviewRequiredRows: number;
  reviewRequiredSupport: number;
  activeMergeRows: number;
  hasPendingOverlay: boolean;
  topProcesses?: string;
  topEffects?: string;
}

export interface AgentFlameRendererModeResult {
  mode: AgentFlameDisplayMode;
  bucketCount: number;
  totalSupport: number;
  candidateOverlayRows: number;
  reviewRequiredRows: number;
  reviewRequiredSupport: number;
  activeMergeRows: number;
  hiddenOtherRows: number;
  buckets: AgentFlameRendererBucket[];
}

function asNumber(value: number | string | null | undefined): number {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0;
  if (value === null || value === undefined || value === '') return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function asBool(value: boolean | string | null | undefined): boolean {
  if (typeof value === 'boolean') return value;
  if (value === null || value === undefined) return false;
  return ['true', '1', 'yes', 'y'].includes(String(value).trim().toLowerCase());
}

function parseRawTags(text: string): Array<{ tag: string; support: number }> {
  return String(text || '')
    .split(';')
    .map(part => part.trim())
    .filter(Boolean)
    .map(part => {
      const at = part.lastIndexOf('=');
      if (at <= 0) return null;
      const tag = part.slice(0, at).trim();
      const support = asNumber(part.slice(at + 1).trim());
      return tag ? { tag, support } : null;
    })
    .filter((row): row is { tag: string; support: number } => row !== null);
}

function keyFor(dimension: string, tag: string): string {
  return `${dimension}\u0000${tag}`;
}

function countHiddenOther(tags: string[]): number {
  return tags.filter(tag => ['other', 'others'].includes(tag.toLowerCase())).length;
}

function sortBuckets(buckets: AgentFlameRendererBucket[]): AgentFlameRendererBucket[] {
  return [...buckets].sort((left, right) => (
    right.support - left.support
    || left.dimension.localeCompare(right.dimension)
    || left.displayTag.localeCompare(right.displayTag)
  ));
}

export function drilldownMembershipMatchesDisplayMap(
  displayRows: AgentFlameDisplayMapRow[],
  drilldownRows: AgentFlameDrilldownRow[],
): boolean {
  const expected = new Map<string, Map<string, number>>();
  for (const row of displayRows) {
    const key = keyFor(row.dimension, row.active_display_tag);
    let group = expected.get(key);
    if (!group) {
      group = new Map<string, number>();
      expected.set(key, group);
    }
    group.set(row.raw_tag, (group.get(row.raw_tag) ?? 0) + asNumber(row.support));
  }

  const seen = new Set<string>();
  for (const row of drilldownRows) {
    const key = keyFor(row.dimension, row.active_display_tag);
    const expectedGroup = expected.get(key);
    if (!expectedGroup || seen.has(key)) return false;
    seen.add(key);
    const actualRows = parseRawTags(row.raw_tags);
    if (actualRows.length !== expectedGroup.size) return false;
    let actualSupport = 0;
    for (const actual of actualRows) {
      actualSupport += actual.support;
      if (expectedGroup.get(actual.tag) !== actual.support) return false;
    }
    if (actualSupport !== asNumber(row.support)) return false;
    if (actualRows.length !== asNumber(row.raw_tag_count)) return false;
  }
  return seen.size === expected.size;
}

export function renderAgentFlameMode(
  mode: AgentFlameDisplayMode,
  displayRows: AgentFlameDisplayMapRow[],
  drilldownRows: AgentFlameDrilldownRow[],
): AgentFlameRendererModeResult {
  const totalSupport = displayRows.reduce((sum, row) => sum + asNumber(row.support), 0);
  const reviewRows = displayRows.filter(row => asBool(row.requires_review));
  const candidateRows = displayRows.filter(row => Boolean(row.candidate_display_tag));
  const activeMergeRows = displayRows.filter(row => row.raw_tag !== row.active_display_tag);
  const drilldownByKey = new Map(
    drilldownRows.map(row => [keyFor(row.dimension, row.active_display_tag), row]),
  );

  let buckets: AgentFlameRendererBucket[];
  if (mode === 'raw') {
    buckets = displayRows.map(row => ({
      mode,
      dimension: row.dimension,
      displayTag: row.raw_tag,
      support: asNumber(row.support),
      rawTagCount: 1,
      rawTags: [{ tag: row.raw_tag, support: asNumber(row.support) }],
      candidateRows: 0,
      reviewRequiredRows: 0,
      reviewRequiredSupport: 0,
      activeMergeRows: 0,
      hasPendingOverlay: false,
    }));
  } else {
    buckets = drilldownRows.map(row => {
      const rawTags = parseRawTags(row.raw_tags);
      return {
        mode,
        dimension: row.dimension,
        displayTag: row.active_display_tag,
        support: asNumber(row.support),
        rawTagCount: asNumber(row.raw_tag_count),
        rawTags,
        candidateRows: mode === 'pending' ? asNumber(row.candidate_rows) : 0,
        reviewRequiredRows: mode === 'pending' ? asNumber(row.review_required_rows) : 0,
        reviewRequiredSupport: mode === 'pending' ? asNumber(row.review_required_support) : 0,
        activeMergeRows: asNumber(row.active_merge_rows),
        hasPendingOverlay: mode === 'pending' && (
          asNumber(row.candidate_rows) > 0 || asNumber(row.review_required_rows) > 0
        ),
        topProcesses: row.top_processes,
        topEffects: row.top_effects,
      };
    });
  }

  const hiddenOtherRows = mode === 'raw'
    ? countHiddenOther(displayRows.map(row => row.raw_tag))
    : countHiddenOther(Array.from(drilldownByKey.values()).map(row => row.active_display_tag));

  return {
    mode,
    bucketCount: buckets.length,
    totalSupport,
    candidateOverlayRows: mode === 'pending' ? candidateRows.length : 0,
    reviewRequiredRows: mode === 'pending' ? reviewRows.length : 0,
    reviewRequiredSupport: mode === 'pending'
      ? reviewRows.reduce((sum, row) => sum + asNumber(row.support), 0)
      : 0,
    activeMergeRows: mode === 'raw' ? 0 : activeMergeRows.length,
    hiddenOtherRows,
    buckets: sortBuckets(buckets),
  };
}

export function renderAgentFlameModes(
  displayRows: AgentFlameDisplayMapRow[],
  drilldownRows: AgentFlameDrilldownRow[],
): Record<AgentFlameDisplayMode, AgentFlameRendererModeResult> {
  return {
    raw: renderAgentFlameMode('raw', displayRows, drilldownRows),
    display: renderAgentFlameMode('display', displayRows, drilldownRows),
    pending: renderAgentFlameMode('pending', displayRows, drilldownRows),
  };
}
