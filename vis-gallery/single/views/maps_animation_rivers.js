import { repositoryNebula } from "./repository_nebula.js";

const HOUR_MS = 3_600_000;
const WAKE_MS = 6 * HOUR_MS;
const ATTENTION_MS = 30 * 60_000;
const ATTENTION_HALF_LIFE_MS = 5 * 60_000;
const TREEMAP_PATH_LIMIT = 700;

const patternColors = {
  Supernova: "#ff6b7a",
  Pulsar: "#f4c95d",
  "White Dwarf": "#90a4be",
  Dayfly: "#bb8fef",
  Nova: "#5dd9c1",
  Fossil: "#3f4b5e",
  Steady: "#4d91c6",
};
const lifeColors = ["#4ab99a", "#66445a"];
const actionColors = {
  read: "#67dff1",
  write: "#ff7b72",
  test: "#65d69e",
  other: "#f4c95d",
};

const chart = (h, rows, empty, option) => h.withEmpty(
  { ...h.base(), ...option }, rows.length, empty,
);
const grid = (left = 56, right = 24, top = 42, bottom = 42) => (
  { left, right, top, bottom }
);
const legend = (h, data) => ({ top: 0, data, textStyle: { color: h.colors.muted } });
const categoryAxis = (h, data, extra = {}) => ({
  type: "category", data, ...h.axis(), ...extra,
});
const valueAxis = (h, name, extra = {}) => ({
  type: "value", name, ...h.axis(), ...extra,
});
const bar = (name, color, rows, value, extra = {}) => ({
  name, type: "bar", itemStyle: { color },
  data: rows.map((row) => ({ value: value(row), row })), ...extra,
});
const axisTooltip = (formatter) => ({
  trigger: "axis", axisPointer: { type: "shadow" }, formatter,
});

const visible = (data, cursorMs, h) => h.visibleEvents(data, cursorMs);
const activePathSet = (data, cursorMs, h) => (
  new Set(visible(data, cursorMs, h).map((event) => event.path))
);
const recent = (data, cursorMs, h) => visible(data, cursorMs, h)
  .filter((event) => event.ts_ms >= cursorMs - WAKE_MS && event.ts_ms <= cursorMs)
  .sort((a, b) => a.ts_ms - b.ts_ms || a.id.localeCompare(b.id));
const endpointFiles = (data) => data.files.filter(
  (file) => file.survives_to_head && file.current_path === file.path,
);
const endedCount = (row) => (
  row.dead_files ?? Math.max(0, row.born_files - (row.surviving_files ?? 0))
);

function attentionByPath(data, cursorMs) {
  const attention = new Map();
  for (const event of data.events ?? []) {
    const age = cursorMs - event.ts_ms;
    if (age < 0 || age > ATTENTION_MS) continue;
    const previous = attention.get(event.path);
    if (previous && previous.ts_ms > event.ts_ms) continue;
    attention.set(event.path, {
      ts_ms: event.ts_ms,
      effect: event.effect,
      action: event.action,
      vendor: event.vendor,
      age,
      strength: 2 ** (-age / ATTENTION_HALF_LIFE_MS),
    });
  }
  return attention;
}

function observedState(data, cursorMs) {
  const files = new Map(data.files.map((file) => [file.path, file]));
  const paths = new Map();
  const visits = new Map();
  const first = new Map();
  const last = new Map();
  for (const event of data.events ?? []) {
    if (event.ts_ms > cursorMs) break;
    const weight = event.effect === "write" ? 2 : 1;
    visits.set(event.path, (visits.get(event.path) ?? 0) + weight);
    if (!first.has(event.path)) first.set(event.path, event);
    last.set(event.path, event);
    const file = files.get(event.path);
    paths.set(event.path, Math.max(1, Number(file?.current_bytes) || Number(file?.churn) || 1));
  }
  return { paths, visits, first, last };
}

function groupForPath(path) {
  const parts = path.split("/");
  if (parts.length === 1) return ["(root)"];
  return parts.slice(0, Math.min(2, parts.length - 1));
}

function materializeTree(node) {
  const children = [...node.children.values()]
    .map(materializeTree)
    .sort((left, right) => left.name.localeCompare(right.name));
  delete node.children;
  if (children.length) {
    node.children = children;
    node.value = children.reduce((sum, child) => sum + (child.value ?? 0), 0);
    if (children.some((child) => child.__active)) node.__active = true;
  }
  if (node.__active && !node.path) {
    node.itemStyle = { borderColor: "#dffdf8", borderWidth: 1 };
  }
  return node;
}

function growthTree(data, cursorMs, attention) {
  const { paths: state } = observedState(data, cursorMs);
  for (const [path] of attention) {
    if (!state.has(path)) state.set(path, 1);
  }
  const files = new Map(data.files.map((file) => [file.path, file]));
  const ranked = [...state].sort((left, right) => {
    const leftFocus = attention.has(left[0]) ? 1e15 : 0;
    const rightFocus = attention.has(right[0]) ? 1e15 : 0;
    return rightFocus + right[1] - leftFocus - left[1] || left[0].localeCompare(right[0]);
  });
  const selected = new Set(ranked.slice(0, TREEMAP_PATH_LIMIT).map(([path]) => path));
  const rows = ranked.filter(([path]) => selected.has(path)).map(([path, value]) => {
    const file = files.get(path);
    const focus = attention.get(path);
    const color = actionColors[focus?.effect] ?? patternColors[file?.pattern] ?? "#4d91c6";
    return {
      path, value, name: path.split("/").at(-1), pattern: file?.pattern,
      touches: file?.touches ?? 0, measure: "observed working bytes",
      __active: Boolean(focus), attention: focus,
      ...(focus && { itemStyle: {
        color, opacity: 0.35 + 0.65 * focus.strength,
        borderColor: "#dffdf8", borderWidth: 1,
        shadowBlur: 12 * focus.strength, shadowColor: color,
      } }),
    };
  });
  const aggregates = new Map();
  for (const [path, value] of ranked.slice(TREEMAP_PATH_LIMIT)) {
    const group = groupForPath(path).join("/");
    const row = aggregates.get(group) ?? { value: 0, count: 0 };
    row.value += value;
    row.count += 1;
    aggregates.set(group, row);
  }
  for (const [group, aggregate] of aggregates) {
    rows.push({
      path: null, treePath: `${group}/(other files)`, name: `other ${aggregate.count} files`,
      value: aggregate.value, aggregate: true, measure: "observed working bytes",
    });
  }
  const root = { name: "repository", children: new Map() };
  for (const row of rows) {
    const path = row.treePath ?? row.path;
    const parts = path.split("/");
    let node = root;
    for (const part of parts.slice(0, -1)) {
      if (!node.children.has(part)) node.children.set(part, { name: part, children: new Map() });
      node = node.children.get(part);
    }
    node.children.set(parts.at(-1), { ...row, children: new Map() });
  }
  return materializeTree(root);
}

function repositoryTreemap(data, cursorMs, h) {
  const attention = attentionByPath(data, cursorMs);
  const tree = growthTree(data, cursorMs, attention);
  const rows = tree.children ?? [];
  return chart(h, rows, "No repository paths at the endpoint", {
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row = {} }) => row.path
        ? `${row.path}\n${row.pattern ?? "file"}\n${row.touches ?? 0} recorded touches\n${h.formatCompact(row.value ?? 0)} ${row.measure ?? "current bytes"}${row.attention ? `\n${row.attention.vendor} ${row.attention.effect} · ${Math.round(row.attention.age / 60_000)} min ago` : ""}`
        : row.aggregate
          ? `${row.name}\n${h.formatCompact(row.value ?? 0)} ${row.measure}`
        : row.name ?? "repository",
    },
    series: [{
      type: "treemap", data: rows, roam: true, nodeClick: "zoomToNode",
      breadcrumb: {
        show: true, bottom: 3,
        itemStyle: { color: "#151d2b", borderColor: "#26344b" },
        emphasis: { itemStyle: { color: "#1d293b" } },
      },
      label: { show: true, color: "#e9f1ff", fontSize: 10, overflow: "truncate" },
      upperLabel: { show: true, height: 22, color: "#9fb1c9" },
      itemStyle: { borderColor: "#080c14", borderWidth: 1, gapWidth: 1 },
      animationDurationUpdate: 220,
      levels: [
        { itemStyle: { borderWidth: 0, gapWidth: 2 } },
        { colorSaturation: [0.25, 0.65], itemStyle: { gapWidth: 2 } },
        { colorSaturation: [0.3, 0.75], itemStyle: { gapWidth: 1 } },
      ],
    }],
  });
}

function territoryCartogram(data, cursorMs, h) {
  const activePaths = activePathSet(data, cursorMs, h);
  const groups = new Map();
  endpointFiles(data).forEach((file) => {
    const row = groups.get(file.group) ?? { group: file.group, files: 0, bytes: 0, active: 0 };
    row.files += 1;
    row.bytes += file.current_bytes;
    row.active += Number(activePaths.has(file.path));
    groups.set(file.group, row);
  });
  const rows = h.rank([...groups.values()], (row) => row.bytes, 16);
  const names = ["current bytes", "paths active by cursor"];
  return chart(h, rows, "No endpoint territories", {
    grid: grid(146, 48, 50, 42), legend: legend(h, names),
    tooltip: axisTooltip((params) => {
      const row = params[0]?.data?.row ?? params[1]?.data?.row;
      return row ? `${row.group}\n${row.files} endpoint files\n${h.formatCompact(row.bytes)} current bytes\n${row.active}/${row.files} paths active by cursor` : "";
    }),
    xAxis: [
      valueAxis(h, "current bytes", { axisLabel: { color: h.colors.muted, formatter: h.formatCompact } }),
      valueAxis(h, "active paths", {
        min: 0, max: 100, position: "top", splitLine: { show: false },
        axisLabel: { color: h.colors.muted, formatter: "{value}%" },
      }),
    ],
    yAxis: categoryAxis(h, rows.map((row) => row.group), {
      inverse: true, axisLabel: { color: h.colors.muted, width: 132, overflow: "truncate" },
    }),
    series: [
      bar(names[0], "#315f86", rows, (row) => row.bytes, {
        barMaxWidth: 14, itemStyle: { color: "#315f86", borderRadius: [0, 4, 4, 0] },
      }),
      bar(names[1], "#5dd9c1", rows, (row) => 100 * row.active / Math.max(1, row.files), {
        xAxisIndex: 1, barMaxWidth: 8,
        itemStyle: { color: "#5dd9c1", borderRadius: [0, 4, 4, 0] },
      }),
    ],
  });
}

function agentPathParticles(data, cursorMs, h) {
  const anchors = new Map();
  data.files.forEach((file) => {
    anchors.set(file.path, file);
    if (file.current_path) anchors.set(file.current_path, file);
  });
  const particles = recent(data, cursorMs, h).slice(-1800).flatMap((event) => {
    const file = anchors.get(event.path);
    if (!file) return [];
    const age = Math.max(0, cursorMs - event.ts_ms) / WAKE_MS;
    const color = h.vendorColor(event.vendor);
    return [{
      value: [file.stable_x, file.stable_y, event.ts_ms],
      path: event.path, vendor: event.vendor, effect: event.effect, age,
      symbolSize: event.effect === "write" ? 9 : 5,
      itemStyle: {
        color, opacity: Math.max(0.06, (1 - age) * 0.78),
        shadowBlur: Math.max(0, (1 - age) * 14), shadowColor: color,
      },
    }];
  });
  const anchorRows = h.rank(
    data.files,
    (file) => file.current_bytes + file.risk_score * 100,
    450,
  );
  return chart(h, particles, "No path events in the trailing six hours", {
    grid: grid(18, 18, 18, 18),
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row, seriesName }) => seriesName === "anchors"
        ? row.path
        : `${row.path}\n${row.vendor} · ${row.effect}\n${Math.round(row.age * 360)} min before cursor`,
    },
    series: [
      {
        name: "anchors", type: "scatter", symbolSize: 3,
        itemStyle: { color: "#607086", opacity: 0.24 },
        data: particles.length
          ? anchorRows.map((file) => ({ value: [file.stable_x, file.stable_y], path: file.path }))
          : [],
      },
      { name: "recorded path events", type: "scatter", data: particles, emphasis: { scale: 1.65 } },
    ],
  });
}

function durableChangePulse(data, _cursorMs, h) {
  const churnByCommit = new Map();
  data.changes.forEach((change) => churnByCommit.set(
    change.commit_id,
    (churnByCommit.get(change.commit_id) ?? 0) + change.additions + change.deletions,
  ));
  const commits = data.commits.filter((commit) => (
    commit.committed_at_ms >= data.meta.window_start_ms
    && commit.committed_at_ms <= data.meta.window_end_ms
  ));
  const points = commits.map((commit) => {
    const churn = churnByCommit.get(commit.id) ?? 0;
    const color = commit.is_merge ? "#bb8fef" : h.colors.commit;
    return {
      value: [commit.committed_at_ms, churn], commit: commit.id, merge: commit.is_merge,
      symbolSize: Math.min(32, 7 + Math.sqrt(churn)),
      itemStyle: { color, opacity: 0.8, shadowBlur: 10, shadowColor: color },
    };
  });
  return chart(h, commits, "No Git commits in this interval", {
    grid: grid(54, 24, 24, 42),
    xAxis: valueAxis(h, undefined, {
      type: "time", min: data.meta.window_start_ms, max: data.meta.window_end_ms,
    }),
    yAxis: valueAxis(h, "changed lines"),
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row }) => `${row.commit.slice(0, 10)}\n${h.formatCompact(row.value[1])} changed lines${row.merge ? "\nmerge commit" : ""}`,
    },
    series: [{ name: "Git commits", type: "scatter", data: points }],
  });
}

function recentWake(data, cursorMs, h) {
  const byPath = new Map();
  recent(data, cursorMs, h).forEach((event) => {
    const row = byPath.get(event.path) ?? { count: 0, latest: event };
    row.count += 1;
    if (event.ts_ms >= row.latest.ts_ms) row.latest = event;
    byPath.set(event.path, row);
  });
  const rows = h.rank(
    data.files.filter((file) => byPath.has(file.path)).map((file) => ({ file, ...byPath.get(file.path) })),
    (row) => row.file.touches, 12,
  );
  return chart(h, rows, "No glowing paths in the trailing six hours", {
    grid: grid(190, 42, 18, 34),
    xAxis: valueAxis(h, "events", { minInterval: 1 }),
    yAxis: categoryAxis(h, rows.map((row) => row.file.path), {
      inverse: true, axisLabel: { color: h.colors.muted, width: 176, overflow: "truncate" },
    }),
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row }) => `${row.path}\n${row.value} events in the trailing six hours\nlatest: ${row.vendor} · ${row.effect}`,
    },
    series: [{
      name: "recent path events", type: "bar", barMaxWidth: 16,
      label: { show: true, position: "right", color: h.colors.text },
      data: rows.map((row) => ({
        value: row.count, path: row.file.path,
        vendor: row.latest.vendor, effect: row.latest.effect,
        itemStyle: {
          color: h.vendorColor(row.latest.vendor),
          opacity: Math.max(0.25, 1 - (cursorMs - row.latest.ts_ms) / WAKE_MS),
          borderRadius: [0, 5, 5, 0],
        },
      })),
    }],
  });
}

function agentActivityRiver(data, cursorMs, h) {
  const buckets = new Map();
  visible(data, cursorMs, h).forEach((event) => {
    const hour = Math.floor(event.ts_ms / HOUR_MS) * HOUR_MS;
    const key = `${hour}\u0000${event.vendor}`;
    const row = buckets.get(key) ?? [hour, 0, event.vendor];
    row[1] += 1;
    buckets.set(key, row);
  });
  const rows = [...buckets.values()].sort((a, b) => a[0] - b[0] || a[2].localeCompare(b[2]));
  const vendors = [...new Set(rows.map((row) => row[2]))];
  return chart(h, rows, "No recorded path activity by this cursor", {
    color: vendors.map((vendor) => h.vendorColor(vendor)),
    tooltip: { trigger: "axis", renderMode: "richText", axisPointer: { type: "line" } },
    legend: legend(h, vendors),
    singleAxis: {
      type: "time", min: data.meta.window_start_ms, max: data.meta.window_end_ms,
      top: 44, bottom: 30, ...h.axis(),
    },
    series: [{
      type: "themeRiver", data: rows,
      emphasis: { itemStyle: { shadowBlur: 16, shadowColor: "rgba(0,0,0,.5)" } },
    }],
  });
}

function lifetimeCohorts(data, _cursorMs, h) {
  const rows = data.survival_cohorts;
  const names = ["survives at endpoint", "ended before endpoint"];
  return chart(h, rows, "No file-lifetime cohorts", {
    grid: grid(56, 24, 42, 62), legend: legend(h, names),
    tooltip: axisTooltip((params) => {
      const row = params[0]?.data?.row;
      return row ? `${row.cohort}\n${row.born_files} born\n${row.surviving_files ?? 0} survive at endpoint\n${endedCount(row)} ended before endpoint` : "";
    }),
    xAxis: categoryAxis(h, rows.map((row) => row.cohort), {
      axisLabel: { color: h.colors.muted, rotate: 35, fontSize: 9 },
    }),
    yAxis: valueAxis(h, "file lifetimes", { minInterval: 1 }),
    series: names.map((name, index) => bar(
      name, lifeColors[index], rows,
      index ? endedCount : (row) => row.surviving_files ?? 0,
      { stack: "life" },
    )),
  });
}

function survivalLedger(data, _cursorMs, h) {
  const rows = data.survival_cohorts.slice(-10).reverse().map((row) => ({
    ...row, alive: row.surviving_files ?? 0, ended: endedCount(row),
  }));
  const names = ["alive at endpoint", "ended"];
  return chart(h, rows, "No endpoint survival ledger", {
    grid: grid(76, 44, 42, 34), legend: legend(h, names),
    tooltip: axisTooltip((params) => {
      const row = params[0]?.data?.row;
      const rate = row ? 100 * row.alive / Math.max(1, row.born_files) : 0;
      return row ? `${row.cohort}\n${row.alive} alive · ${row.ended} ended\n${rate.toFixed(1)}% survive at endpoint` : "";
    }),
    xAxis: valueAxis(h, "file lifetimes", { minInterval: 1 }),
    yAxis: categoryAxis(h, rows.map((row) => row.cohort), { inverse: true }),
    series: names.map((name, index) => bar(
      name, lifeColors[index], rows, (row) => row[index ? "ended" : "alive"],
      { stack: "life", barMaxWidth: 18 },
    )),
  });
}

function gitSediment(data, _cursorMs, h) {
  const rows = data.source_days.map((sourceDay) => {
    const changes = data.changes.filter((row) => h.dateDay(row.committed_at_ms) === sourceDay.day);
    return {
      day: sourceDay.day,
      added: changes.reduce((sum, row) => sum + row.additions, 0),
      deleted: changes.reduce((sum, row) => sum + row.deletions, 0),
      sourceStatus: sourceDay.quantitative_status,
    };
  });
  const names = ["additions", "deletions"];
  return chart(h, rows, "No observed source days", {
    grid: grid(94, 40, 42, 38), legend: legend(h, names),
    tooltip: axisTooltip((params) => {
      const row = params[0]?.data?.row;
      return row ? `${row.day}\n+${row.added} additions\n−${row.deleted} deletions\nsource day: ${row.sourceStatus}` : "";
    }),
    xAxis: valueAxis(h, "changed lines", {
      axisLabel: { color: h.colors.muted, formatter: (value) => h.formatCompact(Math.abs(value)) },
    }),
    yAxis: categoryAxis(h, rows.map((row) => row.day), { inverse: true }),
    series: [
      bar(names[0], "#4ab99a", rows, (row) => row.added, {
        itemStyle: { color: "#4ab99a", borderRadius: [0, 4, 4, 0] },
      }),
      bar(names[1], "#ff7b72", rows, (row) => -row.deleted, {
        itemStyle: { color: "#ff7b72", borderRadius: [4, 0, 0, 4] },
      }),
    ],
  });
}

export const views = [
  ["repository-treemap", "Agent-observed repository treemap", "Files appear on their first recorded Agent access. Reads and writes glow for 30 minutes with a five-minute half-life; Git does not drive the layout.", "endpoint-overlay", ["files", "events"], repositoryTreemap],
  ["workspace-constellation", "Repository Nebula", "The first frame is empty. Git-tracked repository context fades in at low brightness while files emerge on real Agent events from path-near neighbors; recent reads, writes, and command-associated effects pulse and decay without edges.", "endpoint-overlay", ["files", "events"], repositoryNebula],
  ["territory-cartogram", "Territories under attention", "Endpoint repository size and cursor-visible attention remain separate scales.", "endpoint-overlay", ["files", "events"], territoryCartogram],
  ["agent-path-particles", "Agent–path particle field", "Recorded reads and writes glow around stable path anchors for the trailing six hours; trails are not ownership or causality.", "trailing-6h", ["files", "events"], agentPathParticles],
  ["durable-change-pulse", "Durable Git reference", "A frozen Git-only reference. Dynamic Agent views use commit time solely for an outer-border flash.", "static", ["commits", "changes"], durableChangePulse],
  ["recent-wake", "Paths still glowing", "A six-hour tail makes recent bursts readable without implying that quiet paths disappeared.", "trailing-6h", ["files", "events"], recentWake],
  ["agent-activity-river", "Agent activity river", "River width is hourly recorded path activity by native-history vendor through the cursor, not durable authorship.", "cumulative", ["events"], agentActivityRiver],
  ["lifetime-cohorts", "File-lifetime cohorts", "Birth and survival come from first-parent Git history and are measured at the frozen endpoint.", "static", ["survival_cohorts"], lifetimeCohorts],
  ["survival-ledger", "The repository keeps and forgets", "A compact endpoint ledger separates cohort survival from process attention.", "static", ["survival_cohorts"], survivalLedger],
  ["git-sediment", "Observed-day Git sediment", "Adds and deletes are actual Git changes on observed source days, independent of event-to-Git candidates.", "static", ["source_days", "changes"], gitSediment],
].map(([id, title, note, timeMode, requirements, build, playbackMoments]) => (
  { id, title, note, timeMode, requirements, build, ...(playbackMoments && { playbackMoments }) }
));
