const HOUR = 3_600_000;
const DAY = 24 * HOUR;
const start = Date.UTC(2026, 6, 1);
const end = start + 3 * DAY;
const days = [0, 1, 2].map((offset) => new Date(start + offset * DAY).toISOString().slice(0, 10));

const definitions = [
  ["src/main.rs", "src", "Pulsar", 8_400, 24, 180],
  ["src/lib.rs", "src", "Supernova", 12_600, 18, 620],
  ["tests/smoke.rs", "tests", "Steady", 4_200, 12, 90],
  ["docs/guide.md", "docs", "Nova", 6_100, 8, 70],
  ["src/retired.rs", "src", "Dayfly", 0, 4, 35],
];

const events = [
  [0, "session-claude", "claude", "read", "src/main.rs", "not_eligible"],
  [2, "session-claude", "claude", "read", "src/lib.rs", "not_eligible"],
  [3, "session-claude", "claude", "write", "src/lib.rs", "unique_candidate"],
  [8, "session-codex", "codex", "read", "tests/smoke.rs", "not_eligible"],
  [9, "session-codex", "codex", "write", "src/main.rs", "ambiguous_candidates"],
  [27, "session-codex", "codex", "read", "docs/guide.md", "not_eligible"],
  [29, "session-gemini", "gemini", "write", "docs/guide.md", "no_candidate"],
  [34, "session-gemini", "gemini", "read", "src/lib.rs", "not_eligible"],
  [52, "session-claude", "claude", "read", "src/main.rs", "not_eligible"],
  [69, "session-claude", "claude", "write", "tests/smoke.rs", "not_eligible"],
].map(([hour, session_id, vendor, effect, path, association_state], index) => ({
  id: `event-${index + 1}`,
  event_id: `source-${index + 1}`,
  session_id,
  vendor,
  model: `${vendor}-test`,
  ts_ms: start + hour * HOUR,
  day: new Date(start + hour * HOUR).toISOString().slice(0, 10),
  action: effect === "write" ? "edit" : "read_file",
  category: "filesystem",
  effect,
  status: "success",
  prompt_index: Math.floor(index / 2),
  path,
  group: path.split("/")[0],
  association_state,
  candidate_count: association_state === "ambiguous_candidates" ? 2 : Number(association_state === "unique_candidate"),
  evidence_bin: association_state === "not_eligible" ? null : "same-day",
  exact_hunk: association_state === "unique_candidate",
}));

const verification_events = [
  [4, "session-claude", "claude"],
  [10, "session-codex", "codex"],
  [31, "session-gemini", "gemini"],
  [70, "session-claude", "claude"],
].map(([hour, session_id, vendor], index) => ({
  id: `verify-${index + 1}`,
  session_id,
  vendor,
  ts_ms: start + hour * HOUR,
  day: new Date(start + hour * HOUR).toISOString().slice(0, 10),
  action: "test",
  status: "success",
}));

const changes = definitions.flatMap(([path], index) => index === 4 ? [] : [{
  id: `change-${index + 1}`,
  commit_id: `commit-${index + 1}`,
  committed_at_ms: start + (5 + index * 13) * HOUR,
  status: index === 3 ? "A" : "M",
  old_path: null,
  path,
  additions: 25 + index * 40,
  deletions: 8 + index * 9,
  lifetime_id: `life-${index + 1}`,
  is_merge: false,
}]);

const files = definitions.map(([path, group, pattern, current_bytes, touches, churn], index) => {
  const survives = index !== 4;
  return {
    path,
    group,
    extension: path.slice(path.lastIndexOf(".")),
    lifetime_id: `life-${index + 1}`,
    lifetime_ids: [`life-${index + 1}`],
    birth_ms: start - (90 - index * 18) * DAY,
    death_ms: survives ? null : start + DAY,
    survives_to_head: survives,
    current_path: survives ? path : null,
    current_bytes,
    touches,
    read_events: Math.max(1, touches - 3),
    write_events: Math.min(3, touches),
    verify_events: 0,
    other_events: 0,
    git_changes: 2 + index,
    additions: Math.round(churn * 0.7),
    deletions: Math.round(churn * 0.3),
    vendors: ["claude", "codex"],
    sessions: ["session-claude", "session-codex"],
    authors: [`author-${(index % 3) + 1}`],
    first_event_ms: start + HOUR,
    last_event_ms: start + (52 + index) * HOUR,
    daily: Object.fromEntries(days.map((day, dayIndex) => [day, {
      touches: dayIndex === index % 3 ? Math.max(1, Math.round(touches / 2)) : 0,
      additions: dayIndex === index % 3 ? Math.round(churn * 0.7) : 0,
      deletions: dayIndex === index % 3 ? Math.round(churn * 0.3) : 0,
    }])),
    association_states: { not_eligible: Math.max(1, touches - 2), unique_candidate: 1 },
    effect_counts: { read: Math.max(1, touches - 3), write: Math.min(3, touches) },
    churn,
    net_lines: Math.round(churn * 0.4),
    risk_score: Number((Math.log1p(touches) * Math.log1p(churn)).toFixed(4)),
    pattern,
    stable_x: 0.12 + index * 0.19,
    stable_y: 0.18 + ((index * 0.31) % 0.68),
  };
});

const endpointLeaves = files.filter((file) => file.survives_to_head).map((file) => ({
  name: file.path.split("/").at(-1),
  path: file.path,
  value: file.current_bytes,
  touches: file.touches,
  risk_score: file.risk_score,
  pattern: file.pattern,
}));

export const fixtureData = {
  schema: "agentsight.gallery.v1",
  meta: {
    repository: "fixture-repository",
    root_id: "fixture-root",
    endpoint_revision: "0123456789abcdef0123456789abcdef01234567",
    window_start_ms: start,
    window_end_ms: end,
    source: "generated test fixture",
    association_mode: "descriptive_only",
    association_caveat: "Candidates are uncertain visual evidence, not authorship or provenance.",
    reported_token_caveat: "Counters are reported units.",
    right_censored_days: [days[2]],
    missing_cells: [],
  },
  summary: {
    sessions: 3,
    path_event_rows: events.length,
    path_records: files.length,
    git_lifetimes: files.length,
    path_records_with_lifetime: files.length,
    commits: changes.length,
    changes: changes.length,
    line_pixels: 24,
  },
  source_days: days.map((day, index) => ({
    day,
    sessions: new Set(events.filter((event) => event.day === day).map((event) => event.session_id)).size,
    events: events.filter((event) => event.day === day).length + verification_events.filter((event) => event.day === day).length,
    path_events: events.filter((event) => event.day === day).length,
    write_event_paths: events.filter((event) => event.day === day && event.effect === "write").length,
    verification_events: verification_events.filter((event) => event.day === day).length,
    quantitative_status: index === 2 ? "right_censored_excluded" : "mature_descriptive",
  })),
  sessions: [
    ["session-claude", "claude", 0, 71, 4_200],
    ["session-codex", "codex", 7, 30, 3_100],
    ["session-gemini", "gemini", 26, 36, 2_400],
  ].map(([id, vendor, first, last, reported_tokens]) => ({
    id, vendor, model: `${vendor}-test`, started_at_ms: start + first * HOUR,
    ended_at_ms: start + last * HOUR,
    tool_events: events.filter((event) => event.session_id === id).length,
    reported_tokens,
    days: [...new Set(events.filter((event) => event.session_id === id).map((event) => event.day))],
  })),
  events,
  verification_events,
  time_buckets: [0, 3, 8, 27, 34, 52, 69].map((hour) => ({
    ts_ms: start + hour * HOUR,
    events: events.filter((event) => Math.floor((event.ts_ms - start) / HOUR) === hour).length,
    read: events.filter((event) => event.ts_ms === start + hour * HOUR && event.effect === "read").length,
    write: events.filter((event) => event.ts_ms === start + hour * HOUR && event.effect === "write").length,
    commits: changes.filter((change) => Math.abs(change.committed_at_ms - (start + hour * HOUR)) < 3 * HOUR).length,
  })),
  files,
  tree: {
    name: "repository",
    value: endpointLeaves.reduce((sum, leaf) => sum + leaf.value, 0),
    children: ["src", "tests", "docs"].map((group) => ({
      name: group,
      value: endpointLeaves.filter((leaf) => leaf.path.startsWith(`${group}/`)).reduce((sum, leaf) => sum + leaf.value, 0),
      children: endpointLeaves.filter((leaf) => leaf.path.startsWith(`${group}/`)),
    })),
  },
  commits: changes.map((change, index) => ({
    id: change.commit_id,
    committed_at_ms: change.committed_at_ms,
    author_label: `author-${(index % 3) + 1}`,
    is_merge: false,
  })),
  changes,
  cochange_edges: [
    { source: "src/main.rs", target: "src/lib.rs", count: 5, semantics: "same-commit correlation; not causal coupling" },
    { source: "src/lib.rs", target: "tests/smoke.rs", count: 3, semantics: "same-commit correlation; not causal coupling" },
  ],
  line_pixels: endpointLeaves.flatMap((leaf, fileIndex) => Array.from({ length: 6 }, (_, lineIndex) => ({
    path: leaf.path,
    line: lineIndex + 1,
    origin_commit: `commit-${(fileIndex % changes.length) + 1}`,
    origin_ms: start - (lineIndex + fileIndex * 2) * DAY,
    author_label: `author-${(lineIndex % 3) + 1}`,
  }))),
  survival_cohorts: ["2026-02", "2026-03", "2026-04", "2026-05"].map((cohort, index) => ({
    cohort, born_files: 4 + index, surviving_files: 3 + index, dead_files: 1, surviving_bytes: 8_000 + index * 4_000,
  })),
  ownership: files.filter((file) => file.survives_to_head).map((file, index) => ({
    author: `author-${(index % 3) + 1}`, group: file.group, changes: 2 + index, churn: file.churn,
  })),
};
