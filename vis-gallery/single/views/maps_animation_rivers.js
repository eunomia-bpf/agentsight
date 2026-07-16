const HOUR_MS = 3_600_000;
const WAKE_MS = 6 * HOUR_MS;

const patternColors = {
  Supernova: "#ff6b7a",
  Pulsar: "#f4c95d",
  "White Dwarf": "#90a4be",
  Dayfly: "#bb8fef",
  Nova: "#5dd9c1",
  Fossil: "#3f4b5e",
  Steady: "#4d91c6",
};

function emptyGraphic(message) {
  return [{
    type: "text",
    left: "center",
    top: "middle",
    silent: true,
    style: { text: message, fill: "#71839a", fontSize: 13 },
  }];
}

function visible(data, cursorMs, h) {
  return h.visibleEvents(data, cursorMs);
}

function activePathSet(data, cursorMs, h) {
  return new Set(visible(data, cursorMs, h).map((event) => event.path));
}

function recent(data, cursorMs, h) {
  return visible(data, cursorMs, h)
    .filter((event) => event.ts_ms >= cursorMs - WAKE_MS && event.ts_ms <= cursorMs)
    .sort((a, b) => a.ts_ms - b.ts_ms || a.id.localeCompare(b.id));
}

function decorateTree(node, activePaths) {
  const children = node.children?.map((child) => decorateTree(child, activePaths));
  const highlighted = node.path
    ? activePaths.has(node.path)
    : children?.some((child) => child.__active);
  return {
    ...node,
    children,
    ...(highlighted ? {
      __active: true,
      itemStyle: {
        color: "#216d7a",
        borderColor: "#6ee7da",
        shadowBlur: 8,
        shadowColor: "rgba(110,231,218,.35)",
      },
    } : {}),
  };
}

function endpointFiles(data) {
  return data.files.filter((file) => (
    file.survives_to_head && file.current_path === file.path
  ));
}

function repositoryTreemap(data, cursorMs, h) {
  const tree = decorateTree(data.tree, activePathSet(data, cursorMs, h));
  const rows = tree.children ?? [];
  return {
    ...h.base(),
    graphic: rows.length ? [] : emptyGraphic("No repository paths at the endpoint"),
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row = {} }) => row.path
        ? `${row.path}\n${row.pattern ?? "file"}\n${row.touches ?? 0} recorded touches\n${h.formatCompact(row.value ?? 0)} current bytes`
        : row.name ?? "repository",
    },
    series: [{
      type: "treemap",
      data: rows,
      roam: true,
      nodeClick: "zoomToNode",
      breadcrumb: {
        show: true,
        bottom: 3,
        itemStyle: { color: "#151d2b", borderColor: "#26344b" },
        emphasis: { itemStyle: { color: "#1d293b" } },
      },
      label: { show: true, color: "#e9f1ff", fontSize: 10, overflow: "truncate" },
      upperLabel: { show: true, height: 22, color: "#9fb1c9" },
      itemStyle: { borderColor: "#080c14", borderWidth: 1, gapWidth: 1 },
      levels: [
        { itemStyle: { borderWidth: 0, gapWidth: 2 } },
        { colorSaturation: [0.25, 0.65], itemStyle: { gapWidth: 2 } },
        { colorSaturation: [0.3, 0.75], itemStyle: { gapWidth: 1 } },
      ],
    }],
  };
}

function workspaceConstellation(data, cursorMs, h) {
  const activePaths = activePathSet(data, cursorMs, h);
  return {
    ...h.base(),
    grid: { left: 18, right: 18, top: 18, bottom: 18 },
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row }) => (
        `${row.path}\n${row.pattern}\n${row.touches} touches · risk ${row.risk.toFixed(2)}`
      ),
    },
    series: [{
      name: "repository paths",
      type: "scatter",
      data: data.files.map((file) => {
        const highlighted = activePaths.has(file.path);
        const color = patternColors[file.pattern] ?? "#5f7d9e";
        return {
          value: [file.stable_x, file.stable_y, file.risk_score],
          path: file.path,
          pattern: file.pattern,
          touches: file.touches,
          risk: file.risk_score,
          symbolSize: Math.max(
            3,
            Math.min(28, 3 + Math.sqrt(file.current_bytes || file.churn || 1) / 8),
          ),
          itemStyle: {
            color,
            opacity: highlighted ? 0.95 : 0.14,
            borderColor: highlighted ? "#dffdf8" : "transparent",
            borderWidth: highlighted ? 1 : 0,
            shadowBlur: highlighted ? 12 : 0,
            shadowColor: color,
          },
        };
      }),
      emphasis: { scale: 1.8 },
    }],
  };
}

function territoryCartogram(data, cursorMs, h) {
  const activePaths = activePathSet(data, cursorMs, h);
  const groups = new Map();
  endpointFiles(data).forEach((file) => {
    const row = groups.get(file.group) ?? {
      group: file.group,
      files: 0,
      bytes: 0,
      active: 0,
    };
    row.files += 1;
    row.bytes += file.current_bytes;
    row.active += Number(activePaths.has(file.path));
    groups.set(file.group, row);
  });
  const rows = h.rank([...groups.values()], (row) => row.bytes, 16);
  return {
    ...h.base(),
    graphic: rows.length ? [] : emptyGraphic("No endpoint territories"),
    grid: { left: 146, right: 48, top: 50, bottom: 42 },
    legend: {
      top: 0,
      textStyle: { color: h.colors.muted },
      data: ["current bytes", "paths active by cursor"],
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const row = params[0]?.data?.row ?? params[1]?.data?.row;
        return row
          ? `${row.group}\n${row.files} endpoint files\n${h.formatCompact(row.bytes)} current bytes\n${row.active}/${row.files} paths active by cursor`
          : "";
      },
    },
    xAxis: [
      {
        type: "value",
        name: "current bytes",
        ...h.axis(),
        axisLabel: { color: h.colors.muted, formatter: h.formatCompact },
      },
      {
        type: "value",
        name: "active paths",
        min: 0,
        max: 100,
        position: "top",
        ...h.axis(),
        splitLine: { show: false },
        axisLabel: { color: h.colors.muted, formatter: "{value}%" },
      },
    ],
    yAxis: {
      type: "category",
      inverse: true,
      data: rows.map((row) => row.group),
      ...h.axis(),
      axisLabel: { color: h.colors.muted, width: 132, overflow: "truncate" },
    },
    series: [
      {
        name: "current bytes",
        type: "bar",
        barMaxWidth: 14,
        itemStyle: { color: "#315f86", borderRadius: [0, 4, 4, 0] },
        data: rows.map((row) => ({ value: row.bytes, row })),
      },
      {
        name: "paths active by cursor",
        type: "bar",
        xAxisIndex: 1,
        barMaxWidth: 8,
        itemStyle: { color: "#5dd9c1", borderRadius: [0, 4, 4, 0] },
        data: rows.map((row) => ({
          value: (100 * row.active) / Math.max(1, row.files),
          row,
        })),
      },
    ],
  };
}

function agentPathParticles(data, cursorMs, h) {
  const anchors = new Map();
  data.files.forEach((file) => {
    anchors.set(file.path, file);
    if (file.current_path) anchors.set(file.current_path, file);
  });
  const events = recent(data, cursorMs, h).slice(-1800);
  const particles = events.flatMap((event) => {
    const file = anchors.get(event.path);
    if (!file) return [];
    const age = Math.max(0, cursorMs - event.ts_ms) / WAKE_MS;
    return [{
      value: [file.stable_x, file.stable_y, event.ts_ms],
      path: event.path,
      vendor: event.vendor,
      effect: event.effect,
      age,
      symbolSize: event.effect === "write" ? 9 : 5,
      itemStyle: {
        color: h.vendorColor(event.vendor),
        opacity: Math.max(0.06, (1 - age) * 0.78),
        shadowBlur: Math.max(0, (1 - age) * 14),
        shadowColor: h.vendorColor(event.vendor),
      },
    }];
  });
  return {
    ...h.base(),
    graphic: particles.length ? [] : emptyGraphic("No path events in the trailing six hours"),
    grid: { left: 18, right: 18, top: 18, bottom: 18 },
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
        name: "anchors",
        type: "scatter",
        symbolSize: 3,
        itemStyle: { color: "#607086", opacity: 0.24 },
        data: data.files.map((file) => ({
          value: [file.stable_x, file.stable_y],
          path: file.path,
        })),
      },
      {
        name: "recorded path events",
        type: "scatter",
        data: particles,
        emphasis: { scale: 1.65 },
      },
    ],
  };
}

function durableChangePulse(data, cursorMs, h) {
  const churnByCommit = new Map();
  data.changes.forEach((change) => {
    churnByCommit.set(
      change.commit_id,
      (churnByCommit.get(change.commit_id) ?? 0) + change.additions + change.deletions,
    );
  });
  const commits = data.commits.filter((commit) => commit.committed_at_ms <= cursorMs);
  return {
    ...h.base(),
    graphic: commits.length ? [] : emptyGraphic("No Git commits by this cursor"),
    grid: { left: 54, right: 24, top: 24, bottom: 42 },
    xAxis: {
      type: "time",
      min: data.meta.window_start_ms,
      max: data.meta.window_end_ms,
      ...h.axis(),
    },
    yAxis: { type: "value", name: "changed lines", ...h.axis() },
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row }) => (
        `${row.commit.slice(0, 10)}\n${h.formatCompact(row.value[1])} changed lines${row.merge ? "\nmerge commit" : ""}`
      ),
    },
    series: [{
      name: "Git commits",
      type: "scatter",
      data: commits.map((commit) => {
        const churn = churnByCommit.get(commit.id) ?? 0;
        return {
          value: [commit.committed_at_ms, churn],
          commit: commit.id,
          merge: commit.is_merge,
          symbolSize: Math.min(32, 7 + Math.sqrt(churn)),
          itemStyle: {
            color: commit.is_merge ? "#bb8fef" : h.colors.commit,
            opacity: 0.8,
            shadowBlur: 10,
            shadowColor: commit.is_merge ? "#bb8fef" : h.colors.commit,
          },
        };
      }),
      markLine: {
        silent: true,
        symbol: "none",
        label: { color: h.colors.muted, formatter: "cursor" },
        lineStyle: { color: h.colors.text, opacity: 0.55 },
        data: [{ xAxis: cursorMs }],
      },
    }],
  };
}

function recentWake(data, cursorMs, h) {
  const events = recent(data, cursorMs, h);
  const byPath = new Map();
  events.forEach((event) => {
    const row = byPath.get(event.path) ?? { count: 0, latest: event };
    row.count += 1;
    if (event.ts_ms >= row.latest.ts_ms) row.latest = event;
    byPath.set(event.path, row);
  });
  const rows = h.rank(
    data.files
      .filter((file) => byPath.has(file.path))
      .map((file) => ({ file, ...byPath.get(file.path) })),
    (row) => row.file.touches,
    12,
  );
  return {
    ...h.base(),
    graphic: rows.length ? [] : emptyGraphic("No glowing paths in the trailing six hours"),
    grid: { left: 190, right: 42, top: 18, bottom: 34 },
    xAxis: { type: "value", minInterval: 1, name: "events", ...h.axis() },
    yAxis: {
      type: "category",
      inverse: true,
      data: rows.map((row) => row.file.path),
      ...h.axis(),
      axisLabel: { color: h.colors.muted, width: 176, overflow: "truncate" },
    },
    tooltip: {
      renderMode: "richText",
      formatter: ({ data: row }) => (
        `${row.path}\n${row.value} events in the trailing six hours\nlatest: ${row.vendor} · ${row.effect}`
      ),
    },
    series: [{
      name: "recent path events",
      type: "bar",
      barMaxWidth: 16,
      label: { show: true, position: "right", color: h.colors.text },
      data: rows.map((row) => ({
        value: row.count,
        path: row.file.path,
        vendor: row.latest.vendor,
        effect: row.latest.effect,
        itemStyle: {
          color: h.vendorColor(row.latest.vendor),
          opacity: Math.max(0.25, 1 - (cursorMs - row.latest.ts_ms) / WAKE_MS),
          borderRadius: [0, 5, 5, 0],
        },
      })),
    }],
  };
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
  const rows = [...buckets.values()].sort(
    (a, b) => a[0] - b[0] || a[2].localeCompare(b[2]),
  );
  const vendors = [...new Set(rows.map((row) => row[2]))];
  return {
    ...h.base(),
    color: vendors.map((vendor) => h.vendorColor(vendor)),
    graphic: rows.length ? [] : emptyGraphic("No recorded path activity by this cursor"),
    tooltip: {
      trigger: "axis",
      renderMode: "richText",
      axisPointer: { type: "line" },
    },
    legend: { top: 0, data: vendors, textStyle: { color: h.colors.muted } },
    singleAxis: {
      type: "time",
      min: data.meta.window_start_ms,
      max: data.meta.window_end_ms,
      top: 44,
      bottom: 30,
      ...h.axis(),
    },
    series: [{
      type: "themeRiver",
      data: rows,
      emphasis: {
        itemStyle: { shadowBlur: 16, shadowColor: "rgba(0,0,0,.5)" },
      },
    }],
  };
}

function endedCount(row) {
  return row.dead_files ?? Math.max(0, row.born_files - (row.surviving_files ?? 0));
}

function lifetimeCohorts(data, _cursorMs, h) {
  const cohorts = data.survival_cohorts;
  return {
    ...h.base(),
    graphic: cohorts.length ? [] : emptyGraphic("No file-lifetime cohorts"),
    grid: { left: 56, right: 24, top: 42, bottom: 62 },
    legend: { top: 0, textStyle: { color: h.colors.muted } },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const row = params[0]?.data?.row;
        return row
          ? `${row.cohort}\n${row.born_files} born\n${row.surviving_files ?? 0} survive at endpoint\n${endedCount(row)} ended before endpoint`
          : "";
      },
    },
    xAxis: {
      type: "category",
      data: cohorts.map((row) => row.cohort),
      ...h.axis(),
      axisLabel: { color: h.colors.muted, rotate: 35, fontSize: 9 },
    },
    yAxis: { type: "value", name: "file lifetimes", minInterval: 1, ...h.axis() },
    series: [
      {
        name: "survives at endpoint",
        type: "bar",
        stack: "life",
        itemStyle: { color: "#4ab99a" },
        data: cohorts.map((row) => ({ value: row.surviving_files ?? 0, row })),
      },
      {
        name: "ended before endpoint",
        type: "bar",
        stack: "life",
        itemStyle: { color: "#66445a" },
        data: cohorts.map((row) => ({ value: endedCount(row), row })),
      },
    ],
  };
}

function survivalLedger(data, _cursorMs, h) {
  const rows = data.survival_cohorts.slice(-10).reverse().map((row) => ({
    ...row,
    alive: row.surviving_files ?? 0,
    ended: endedCount(row),
  }));
  return {
    ...h.base(),
    graphic: rows.length ? [] : emptyGraphic("No endpoint survival ledger"),
    grid: { left: 76, right: 44, top: 42, bottom: 34 },
    legend: { top: 0, textStyle: { color: h.colors.muted } },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const row = params[0]?.data?.row;
        const rate = row ? (100 * row.alive) / Math.max(1, row.born_files) : 0;
        return row
          ? `${row.cohort}\n${row.alive} alive · ${row.ended} ended\n${rate.toFixed(1)}% survive at endpoint`
          : "";
      },
    },
    xAxis: { type: "value", name: "file lifetimes", minInterval: 1, ...h.axis() },
    yAxis: { type: "category", data: rows.map((row) => row.cohort), ...h.axis() },
    series: [
      {
        name: "alive at endpoint",
        type: "bar",
        stack: "life",
        barMaxWidth: 18,
        itemStyle: { color: "#4ab99a" },
        data: rows.map((row) => ({ value: row.alive, row })),
      },
      {
        name: "ended",
        type: "bar",
        stack: "life",
        barMaxWidth: 18,
        itemStyle: { color: "#66445a" },
        data: rows.map((row) => ({ value: row.ended, row })),
      },
    ],
  };
}

function gitSediment(data, _cursorMs, h) {
  const rows = data.source_days.map((sourceDay) => {
    const changes = data.changes.filter(
      (change) => h.dateDay(change.committed_at_ms) === sourceDay.day,
    );
    return {
      day: sourceDay.day,
      added: changes.reduce((sum, row) => sum + row.additions, 0),
      deleted: changes.reduce((sum, row) => sum + row.deletions, 0),
      sourceStatus: sourceDay.quantitative_status,
    };
  });
  return {
    ...h.base(),
    graphic: rows.length ? [] : emptyGraphic("No observed source days"),
    grid: { left: 94, right: 40, top: 42, bottom: 38 },
    legend: { top: 0, textStyle: { color: h.colors.muted } },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const row = params[0]?.data?.row;
        return row
          ? `${row.day}\n+${row.added} additions\n−${row.deleted} deletions\nsource day: ${row.sourceStatus}`
          : "";
      },
    },
    xAxis: {
      type: "value",
      name: "changed lines",
      ...h.axis(),
      axisLabel: {
        color: h.colors.muted,
        formatter: (value) => h.formatCompact(Math.abs(value)),
      },
    },
    yAxis: { type: "category", data: rows.map((row) => row.day), ...h.axis() },
    series: [
      {
        name: "additions",
        type: "bar",
        itemStyle: { color: "#4ab99a", borderRadius: [0, 4, 4, 0] },
        data: rows.map((row) => ({ value: row.added, row })),
      },
      {
        name: "deletions",
        type: "bar",
        itemStyle: { color: "#ff7b72", borderRadius: [4, 0, 0, 4] },
        data: rows.map((row) => ({ value: -row.deleted, row })),
      },
    ],
  };
}

export const views = [
  {
    id: "repository-treemap",
    title: "Stable repository treemap",
    note: "Area is current Git blob size. Cursor playback overlays recorded attention without changing endpoint geometry.",
    timeMode: "endpoint-overlay",
    requirements: ["tree", "events"],
    build: repositoryTreemap,
  },
  {
    id: "workspace-constellation",
    title: "Stable workspace constellation",
    note: "Every path has deterministic coordinates. The cursor changes salience, not geography.",
    timeMode: "endpoint-overlay",
    requirements: ["files", "events"],
    build: workspaceConstellation,
  },
  {
    id: "territory-cartogram",
    title: "Territories under attention",
    note: "Endpoint repository size and cursor-visible attention remain separate scales.",
    timeMode: "endpoint-overlay",
    requirements: ["files", "events"],
    build: territoryCartogram,
  },
  {
    id: "agent-path-particles",
    title: "Agent–path particle field",
    note: "Recorded reads and writes glow around stable path anchors for the trailing six hours; trails are not ownership or causality.",
    timeMode: "trailing-6h",
    requirements: ["files", "events"],
    build: agentPathParticles,
  },
  {
    id: "durable-change-pulse",
    title: "Durable-change pulse",
    note: "Git commits accumulate on their own lane through the cursor; nearby process events are not commit attribution.",
    timeMode: "cumulative",
    requirements: ["commits", "changes"],
    build: durableChangePulse,
  },
  {
    id: "recent-wake",
    title: "Paths still glowing",
    note: "A six-hour tail makes recent bursts readable without implying that quiet paths disappeared.",
    timeMode: "trailing-6h",
    requirements: ["files", "events"],
    build: recentWake,
  },
  {
    id: "agent-activity-river",
    title: "Agent activity river",
    note: "River width is cumulative recorded path activity by native-history vendor, not durable authorship.",
    timeMode: "cumulative",
    requirements: ["events"],
    build: agentActivityRiver,
  },
  {
    id: "lifetime-cohorts",
    title: "File-lifetime cohorts",
    note: "Birth and survival come from first-parent Git history and are measured at the frozen endpoint.",
    timeMode: "static",
    requirements: ["survival_cohorts"],
    build: lifetimeCohorts,
  },
  {
    id: "survival-ledger",
    title: "The repository keeps and forgets",
    note: "A compact endpoint ledger separates cohort survival from process attention.",
    timeMode: "static",
    requirements: ["survival_cohorts"],
    build: survivalLedger,
  },
  {
    id: "git-sediment",
    title: "Observed-day Git sediment",
    note: "Adds and deletes are actual Git changes on observed source days, independent of event-to-Git candidates.",
    timeMode: "static",
    requirements: ["source_days", "changes"],
    build: gitSediment,
  },
];
