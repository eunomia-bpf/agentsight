const DAY_MS = 86_400_000;
const HOUR_MS = 3_600_000;

export const colors = {
  background: "#070b12",
  panel: "#0d1521",
  line: "rgba(135,160,190,.18)",
  text: "#dce8f7",
  muted: "#71839a",
  read: "#62cfe8",
  write: "#ff826d",
  verify: "#64d6a7",
  commit: "#efd265",
  claude: "#b9a8ff",
  codex: "#55d7b5",
  gemini: "#66a7ef",
};

export function base() {
  return {
    backgroundColor: "transparent",
    animation: false,
    textStyle: { color: colors.text, fontFamily: "Inter, system-ui, sans-serif" },
    tooltip: {
      trigger: "item",
      renderMode: "richText",
      backgroundColor: "#0b121c",
      borderColor: "rgba(135,160,190,.28)",
      textStyle: { color: colors.text, fontSize: 11 },
    },
  };
}

export function axis() {
  return {
    axisLine: { lineStyle: { color: colors.line } },
    axisTick: { show: false },
    axisLabel: { color: colors.muted, fontSize: 10 },
    splitLine: { lineStyle: { color: "rgba(135,160,190,.10)" } },
    nameTextStyle: { color: colors.muted, fontSize: 10 },
  };
}

export function withEmpty(option, hasData, message) {
  if (hasData) return { ...option, graphic: option.graphic ?? [] };
  const {
    xAxis: _xAxis, yAxis: _yAxis, singleAxis: _singleAxis,
    series: _series, legend: _legend, visualMap: _visualMap,
    dataZoom: _dataZoom, ...shell
  } = option;
  return {
    ...shell,
    graphic: [{
      type: "text", left: "center", top: "middle", silent: true,
      style: { text: message, fill: colors.muted, fontSize: 13 },
    }],
  };
}

export function visibleEvents(data, cursorMs) {
  const start = data.meta?.window_start_ms ?? Number.NEGATIVE_INFINITY;
  const end = Math.min(cursorMs, data.meta?.window_end_ms ?? cursorMs);
  return (data.events ?? []).filter((event) => event.ts_ms >= start && event.ts_ms <= end);
}

export function visibleVerifications(data, cursorMs) {
  const start = data.meta?.window_start_ms ?? Number.NEGATIVE_INFINITY;
  const end = Math.min(cursorMs, data.meta?.window_end_ms ?? cursorMs);
  return (data.verification_events ?? []).filter((event) => event.ts_ms >= start && event.ts_ms <= end);
}

export function rank(rows, score, limit) {
  return [...rows].sort((left, right) => score(right) - score(left)).slice(0, limit);
}

export function dateDay(value) {
  return new Date(value).toISOString().slice(0, 10);
}

export function formatCompact(value) {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value ?? 0);
}

export function vendorColor(vendor) {
  return colors[vendor] ?? `hsl(${stableUnit(vendor) * 360} 62% 62%)`;
}

export function stateColor(state) {
  return {
    unique_candidate: colors.verify,
    ambiguous_candidates: "#e8a95f",
    no_candidate: "#ff7180",
    not_eligible: "#68778c",
  }[state] ?? colors.muted;
}

export function stableUnit(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 0xffffffff;
}

export function hourFloor(value) {
  return Math.floor(value / HOUR_MS) * HOUR_MS;
}

export function dayFloor(value) {
  return Math.floor(value / DAY_MS) * DAY_MS;
}

export function orderedEdges(events) {
  const bySession = new Map();
  for (const event of events) {
    const rows = bySession.get(event.session_id) ?? [];
    rows.push(event);
    bySession.set(event.session_id, rows);
  }
  const counts = new Map();
  for (const rows of bySession.values()) {
    rows.sort((a, b) => a.ts_ms - b.ts_ms || a.id.localeCompare(b.id));
    const reads = [];
    for (const row of rows) {
      if (row.effect === "read") reads.push(row);
      if (row.effect !== "write") continue;
      for (const read of reads.slice(-8)) {
        if (read.path === row.path) continue;
        const key = `${read.path}\u0000${row.path}`;
        const current = counts.get(key) ?? { source: read.path, target: row.path, count: 0 };
        current.count += 1;
        counts.set(key, current);
      }
    }
  }
  return [...counts.values()].sort((a, b) => b.count - a.count).slice(0, 300);
}

export const helpers = {
  colors,
  base,
  axis,
  withEmpty,
  visibleEvents,
  visibleVerifications,
  rank,
  dateDay,
  formatCompact,
  vendorColor,
  stateColor,
  stableUnit,
  hourFloor,
  dayFloor,
  orderedEdges,
};
