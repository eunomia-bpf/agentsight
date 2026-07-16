const DAY_MS = 86_400_000;

const shortPath = (path, limit = 38) => path.length <= limit ? path : `…${path.slice(-(limit - 1))}`;
const fileName = (path) => path.split("/").at(-1) || path;
const humanState = (state) => state.replaceAll("_", " ");

function patternColor(pattern, h) {
  if (pattern === "Supernova") return h.colors.write;
  if (pattern === "Pulsar") return h.colors.commit;
  if (pattern === "White Dwarf") return h.colors.muted;
  if (pattern === "Dayfly") return h.colors.verify;
  return h.colors.read;
}

function cursorMark(cursorMs, h) {
  return {
    silent: true,
    symbol: "none",
    lineStyle: { color: h.colors.text, width: 1, opacity: 0.62 },
    label: { show: false },
    data: [{ xAxis: cursorMs }],
  };
}

const activityPulse = {
  id: "activity-pulse",
  title: "Longitudinal activity pulse",
  note: "Recorded process activity and Git commits share a clock but remain separate evidence layers. The line marks the replay cursor.",
  timeMode: "cursor-marker",
  requirements: ["time_buckets"],
  build(data, cursorMs, h) {
    const buckets = [...data.time_buckets].sort((a, b) => a.ts_ms - b.ts_ms);
    const process = buckets.filter((row) => row.events !== undefined);
    const processPoints = (key) => {
      const points = [];
      process.forEach((row, index) => {
        const previous = process[index - 1];
        if (previous && row.ts_ms - previous.ts_ms > 3_600_000) {
          points.push([previous.ts_ms + 3_600_000, null]);
          if (row.ts_ms - previous.ts_ms > 7_200_000) points.push([row.ts_ms - 3_600_000, null]);
        }
        points.push([row.ts_ms, row[key] ?? 0]);
      });
      return points;
    };
    return {
      ...h.base(),
      grid: { left: 58, right: 22, top: 24, bottom: 58 },
      legend: { bottom: 4, itemWidth: 14, textStyle: { color: h.colors.muted } },
      tooltip: { trigger: "axis", renderMode: "richText" },
      xAxis: { type: "time", ...h.axis() },
      yAxis: { type: "value", name: "observations / hour", ...h.axis() },
      series: [
        {
          name: "recorded reads",
          type: "line",
          smooth: 0.28,
          showSymbol: true,
          symbolSize: 4,
          connectNulls: false,
          areaStyle: { opacity: 0.08 },
          lineStyle: { width: 1.6, color: h.colors.read },
          itemStyle: { color: h.colors.read },
          data: processPoints("read"),
          markLine: cursorMark(cursorMs, h),
        },
        {
          name: "recorded writes",
          type: "line",
          smooth: 0.28,
          showSymbol: true,
          symbolSize: 4,
          connectNulls: false,
          areaStyle: { opacity: 0.08 },
          lineStyle: { width: 1.6, color: h.colors.write },
          itemStyle: { color: h.colors.write },
          data: processPoints("write"),
        },
        {
          name: "Git commits",
          type: "bar",
          barMaxWidth: 9,
          itemStyle: { color: h.colors.commit, opacity: 0.74 },
          data: buckets.map((row) => [row.ts_ms, row.commits ?? 0]),
        },
      ],
    };
  },
};

const observedDays = {
  id: "observed-days",
  title: "Observed source days",
  note: "These are recorded source windows, not a continuous synthetic workload. Hatched bars are right-censored and remain descriptive only.",
  timeMode: "static",
  requirements: ["source_days"],
  build(data, _cursorMs, h) {
    const days = data.source_days;
    const byDay = new Map(days.map((row) => [row.day, row]));
    const datum = (row, value) => ({
      value,
      day: row.day,
      status: row.quantitative_status,
      itemStyle: row.quantitative_status === "right_censored_excluded"
        ? {
            opacity: 0.48,
            borderColor: h.colors.write,
            borderWidth: 1,
            decal: { symbol: "rect", dashArrayX: [1, 0], dashArrayY: [2, 4], rotation: -0.5 },
          }
        : { opacity: 0.88 },
    });
    return {
      ...h.base(),
      grid: { left: 60, right: 22, top: 24, bottom: 84 },
      legend: { bottom: 4, textStyle: { color: h.colors.muted } },
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        formatter(params) {
          const rows = Array.isArray(params) ? params : [params];
          if (rows.length === 0) return "";
          const source = rows[0].data;
          const status = source.status === "right_censored_excluded"
            ? "right-censored · excluded from mature quantitative claims"
            : "mature descriptive window";
          return [source.day, ...rows.map((row) => `${row.marker}${row.seriesName}: ${h.formatCompact(row.value)}`), status].join("\n");
        },
      },
      xAxis: {
        type: "category",
        data: days.map((row) => row.day),
        ...h.axis(),
        axisLabel: {
          color: h.colors.muted,
          formatter(value) {
            return byDay.get(value)?.quantitative_status === "right_censored_excluded"
              ? `${value}\nright-censored`
              : value;
          },
        },
      },
      yAxis: { type: "value", name: "recorded count", ...h.axis() },
      series: [
        {
          name: "path events",
          type: "bar",
          barMaxWidth: 34,
          itemStyle: { color: h.colors.read },
          data: days.map((row) => datum(row, row.events)),
        },
        {
          name: "deduplicated sessions",
          type: "bar",
          barMaxWidth: 34,
          itemStyle: { color: h.colors.verify },
          data: days.map((row) => datum(row, row.sessions)),
        },
        {
          name: "write-path observations",
          type: "bar",
          barMaxWidth: 34,
          itemStyle: { color: h.colors.write },
          data: days.map((row) => datum(row, row.write_event_paths)),
        },
      ],
    };
  },
};

const namedSignals = {
  id: "named-signals",
  title: "Named evolution signals",
  note: "Lanza-inspired names make repository shapes discussable. They are heuristic discovery labels, not defect predictions.",
  timeMode: "static",
  requirements: ["files"],
  build(data, _cursorMs, h) {
    const counts = new Map();
    data.files.forEach((file) => counts.set(file.pattern, (counts.get(file.pattern) ?? 0) + 1));
    const rows = [...counts.entries()]
      .map(([name, value]) => ({ name, value, itemStyle: { color: patternColor(name, h) } }))
      .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name));
    return {
      ...h.base(),
      legend: {
        type: "scroll",
        orient: "vertical",
        right: 12,
        top: "middle",
        textStyle: { color: h.colors.muted },
      },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter: (params) => `${params.name}\n${h.formatCompact(params.value)} path records\nheuristic label · not a diagnosis`,
      },
      series: [{
        name: "path records",
        type: "pie",
        radius: ["30%", "70%"],
        center: ["40%", "50%"],
        roseType: "radius",
        minAngle: 5,
        label: { color: h.colors.text, formatter: "{b}\n{c}" },
        labelLine: { lineStyle: { color: h.colors.line } },
        data: rows,
      }],
    };
  },
};

const hotPaths = {
  id: "hot-paths",
  title: "Hot paths in the visible interval",
  note: "Rows require recorded activity by the cursor, then rank matching endpoint path records by heuristic risk. Touches and Git churn remain separate evidence.",
  timeMode: "endpoint-overlay",
  requirements: ["events", "files"],
  build(data, cursorMs, h) {
    const activePaths = new Set(h.visibleEvents(data, cursorMs).map((event) => event.path));
    const files = h.rank(
      data.files.filter((file) => activePaths.has(file.path)),
      (file) => file.risk_score,
      12,
    );
    return {
      ...h.base(),
      grid: { left: 245, right: 92, top: 22, bottom: 48 },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter({ data: row }) {
          return `${row.path}\n${row.pattern} heuristic\nrisk score ${row.value.toFixed(2)}\n${h.formatCompact(row.touches)} recorded touches\n${h.formatCompact(row.churn)} Git churn`;
        },
      },
      xAxis: { type: "value", name: "heuristic risk score", ...h.axis() },
      yAxis: {
        type: "category",
        inverse: true,
        data: files.map((file) => file.path),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: h.colors.muted,
          width: 225,
          overflow: "truncate",
          fontFamily: "ui-monospace, monospace",
          fontSize: 10,
          formatter: (value) => shortPath(value, 36),
        },
      },
      series: [{
        type: "bar",
        barMaxWidth: 20,
        label: {
          show: true,
          position: "right",
          color: h.colors.muted,
          formatter: ({ data: row }) => `${h.formatCompact(row.touches)} touches`,
        },
        data: files.map((file) => ({
          value: file.risk_score,
          path: file.path,
          pattern: file.pattern,
          touches: file.touches,
          churn: file.churn,
          itemStyle: { color: patternColor(file.pattern, h), opacity: 0.82 },
        })),
      }],
    };
  },
};

const lineAgePixels = {
  id: "line-age-pixels",
  title: "Current-line age pixels",
  note: "Each cell is one endpoint line colored by Git blame age at the cursor. Highlighted path labels were observed by the cursor; that does not claim agent authorship.",
  timeMode: "endpoint-overlay",
  requirements: ["line_pixels", "events"],
  build(data, cursorMs, h) {
    const activePaths = new Set(h.visibleEvents(data, cursorMs).map((event) => event.path));
    const grouped = new Map();
    data.line_pixels.forEach((pixel) => {
      if (pixel.origin_ms > cursorMs) return;
      const lines = grouped.get(pixel.path) ?? [];
      lines.push(pixel);
      grouped.set(pixel.path, lines);
    });
    const columns = h.rank(
      [...grouped.entries()].map(([path, lines]) => ({
        path,
        lines: lines.sort((a, b) => a.line - b.line),
      })),
      (row) => row.lines.length,
      42,
    );
    const maxRows = Math.max(1, ...columns.map((row) => row.lines.length));
    const heat = columns.flatMap((column, x) => column.lines.map((line, y) => {
      const ageDays = Math.max(0, (cursorMs - line.origin_ms) / DAY_MS);
      const freshness = Math.max(0, 1 - Math.log1p(ageDays) / Math.log(900));
      return {
        value: [x, y, freshness],
        path: column.path,
        line: line.line,
        ageDays,
        author: line.author_label,
        commit: line.origin_commit,
      };
    }));
    return {
      ...h.base(),
      grid: { left: 62, right: 76, top: 102, bottom: 48 },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter({ data: row }) {
          return `${row.path}:${row.line}\n${Math.round(row.ageDays)} days old at cursor\norigin ${row.commit}\n${row.author}`;
        },
      },
      xAxis: {
        type: "category",
        position: "top",
        data: columns.map((row) => row.path),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          interval: 0,
          rotate: 52,
          margin: 8,
          fontFamily: "ui-monospace, monospace",
          fontSize: 9,
          formatter(value) {
            return activePaths.has(value) ? `{active|${shortPath(value, 25)}}` : `{idle|${shortPath(value, 25)}}`;
          },
          rich: {
            active: { color: h.colors.verify, fontWeight: 700 },
            idle: { color: h.colors.muted },
          },
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: Array.from({ length: maxRows }, (_, index) => index + 1),
        ...h.axis(),
        name: "line pixel",
        axisLabel: { color: h.colors.muted, fontSize: 9, interval: Math.max(0, Math.ceil(maxRows / 10) - 1) },
      },
      visualMap: {
        min: 0,
        max: 1,
        dimension: 2,
        orient: "vertical",
        right: 4,
        top: "center",
        text: ["new", "old"],
        textStyle: { color: h.colors.muted, fontSize: 9 },
        inRange: { color: ["#255f87", "#328db3", "#69d1ca", "#f0c66e"] },
      },
      series: [{
        type: "heatmap",
        progressive: 2_000,
        data: heat,
        itemStyle: { borderColor: "rgba(8,12,20,.26)", borderWidth: 0.25 },
        emphasis: { itemStyle: { borderColor: h.colors.text, borderWidth: 1 } },
      }],
    };
  },
};

const touchAssociationLanes = {
  id: "touch-association-lanes",
  title: "Touch and association lanes",
  note: "Blue ticks are recorded reads. Write ticks use green, amber, and red for one, many, and zero Git candidates; candidate state is uncertainty, not provenance.",
  timeMode: "cumulative",
  requirements: ["events", "files"],
  build(data, cursorMs, h) {
    const events = h.visibleEvents(data, cursorMs);
    const activePaths = new Set(events.map((event) => event.path));
    const files = h.rank(
      data.files.filter((file) => activePaths.has(file.path)),
      (file) => file.touches + file.git_changes * 2,
      42,
    );
    const lanePaths = new Set(files.map((file) => file.path));
    const laneEvents = events.filter((event) => lanePaths.has(event.path));
    return {
      ...h.base(),
      grid: { left: 230, right: 24, top: 22, bottom: 62 },
      xAxis: { type: "time", ...h.axis() },
      yAxis: {
        type: "category",
        inverse: true,
        data: files.map((file) => file.path),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: h.colors.muted,
          width: 210,
          overflow: "truncate",
          fontFamily: "ui-monospace, monospace",
          fontSize: 9,
          formatter: (value) => shortPath(value, 34),
        },
      },
      dataZoom: [{ type: "inside", xAxisIndex: 0 }, { type: "slider", xAxisIndex: 0, height: 14, bottom: 8 }],
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter({ data: row }) {
          const association = row.effect === "write" ? `\n${humanState(row.state)} · ${row.candidates} candidate(s)` : "";
          return `${row.path}\n${new Date(row.value[0]).toISOString()}\nrecorded ${row.effect}${association}`;
        },
      },
      series: [{
        name: "process evidence",
        type: "scatter",
        symbolSize: (value) => value[2] === 1 ? 8 : 5,
        data: laneEvents.map((event) => ({
          value: [event.ts_ms, event.path, event.effect === "write" ? 1 : 0],
          path: event.path,
          effect: event.effect,
          state: event.association_state,
          candidates: event.candidate_count,
          itemStyle: {
            color: event.effect === "write" ? h.stateColor(event.association_state) : h.colors.read,
            opacity: event.effect === "write" ? 0.9 : 0.5,
          },
        })),
        markLine: cursorMark(cursorMs, h),
      }],
    };
  },
};

const pathDayMatrix = {
  id: "path-day-matrix",
  title: "Path × observation-day matrix",
  note: "Brightness combines cumulative recorded touches with endpoint Git churn. The tooltip keeps those evidence layers separate; dark cells mean no compatible observation.",
  timeMode: "mixed-day",
  requirements: ["events", "files", "source_days"],
  build(data, cursorMs, h) {
    const events = h.visibleEvents(data, cursorMs);
    const eventCounts = new Map();
    const byPathDay = new Map();
    events.forEach((event) => {
      eventCounts.set(event.path, (eventCounts.get(event.path) ?? 0) + 1);
      const key = `${event.path}\u0000${event.day}`;
      byPathDay.set(key, (byPathDay.get(key) ?? 0) + 1);
    });
    const files = h.rank(data.files, (file) => (eventCounts.get(file.path) ?? 0) * 5 + file.churn, 55);
    const days = data.source_days.map((row) => row.day);
    const matrix = files.flatMap((file, y) => days.map((day, x) => {
      const cell = file.daily[day] ?? {};
      const touches = byPathDay.get(`${file.path}\u0000${day}`) ?? 0;
      const additions = cell.additions ?? 0;
      const deletions = cell.deletions ?? 0;
      const combined = touches * 4 + additions + deletions;
      return {
        value: [x, y, Math.log1p(combined)],
        path: file.path,
        day,
        pattern: file.pattern,
        touches,
        additions,
        deletions,
      };
    }));
    const cursorDay = h.dateDay(cursorMs);
    return {
      ...h.base(),
      grid: { left: 235, right: 72, top: 62, bottom: 48 },
      xAxis: {
        type: "category",
        position: "top",
        data: days,
        ...h.axis(),
        axisLabel: { color: h.colors.muted, fontSize: 10 },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: files.map((file) => file.path),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: h.colors.muted,
          width: 218,
          overflow: "truncate",
          fontFamily: "ui-monospace, monospace",
          fontSize: 9,
          formatter: (value) => shortPath(value, 36),
        },
      },
      visualMap: {
        min: 0,
        max: Math.max(1, ...matrix.map((row) => row.value[2])),
        orient: "vertical",
        right: 4,
        top: "center",
        text: ["more", "none"],
        textStyle: { color: h.colors.muted, fontSize: 9 },
        inRange: { color: ["#101827", "#174d67", "#2ea6a0", "#f0c66e", "#ff7b72"] },
      },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter({ data: row }) {
          return `${row.path}\n${row.day}\n${row.touches} recorded touches\nGit +${row.additions} /−${row.deletions}\n${row.pattern} heuristic`;
        },
      },
      series: [
        {
          type: "heatmap",
          progressive: 1_000,
          data: matrix,
          itemStyle: { borderColor: "rgba(8,12,20,.38)", borderWidth: 1 },
          emphasis: { itemStyle: { borderColor: h.colors.text, borderWidth: 1 } },
        },
        {
          type: "scatter",
          data: [],
          silent: true,
          tooltip: { show: false },
          markLine: days.includes(cursorDay)
            ? {
                silent: true,
                symbol: "none",
                lineStyle: { color: h.colors.text, width: 1, opacity: 0.72 },
                label: { show: false },
                data: [{ xAxis: cursorDay }],
              }
            : undefined,
        },
      ],
    };
  },
};

const associationStateMatrix = {
  id: "association-state-matrix",
  title: "Association-state matrix",
  note: "Missing and ambiguous links are first-class evidence gaps. Green, amber, red, and gray mean one, many, zero candidates, and not eligible—never authorship or agent quality.",
  timeMode: "cumulative",
  requirements: ["events", "files"],
  build(data, cursorMs, h) {
    const events = h.visibleEvents(data, cursorMs);
    const groupCounts = new Map();
    data.files.forEach((file) => groupCounts.set(file.group, (groupCounts.get(file.group) ?? 0) + 1));
    const groups = h.rank(
      [...groupCounts.entries()].map(([group, count]) => ({ group, count })),
      (row) => row.count,
      24,
    ).map((row) => row.group);
    const states = ["not_eligible", "no_candidate", "unique_candidate", "ambiguous_candidates"];
    const counts = new Map();
    events.forEach((event) => {
      const key = `${event.group}\u0000${event.association_state}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    });
    const maxCount = Math.max(1, ...counts.values());
    const cells = groups.flatMap((group, y) => states.map((state, x) => {
      const count = counts.get(`${group}\u0000${state}`) ?? 0;
      return {
        value: [x, y, count],
        group,
        state,
        itemStyle: {
          color: h.stateColor(state),
          borderColor: h.colors.line,
          borderWidth: 1,
        },
      };
    }));
    return {
      ...h.base(),
      grid: { left: 180, right: 26, top: 28, bottom: 82 },
      xAxis: {
        type: "category",
        data: states.map(humanState),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: h.colors.muted, rotate: 24, fontSize: 10 },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: groups,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: h.colors.muted,
          width: 162,
          overflow: "truncate",
          fontFamily: "ui-monospace, monospace",
          fontSize: 9,
          formatter: (value) => shortPath(value, 27),
        },
      },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter: ({ data: row }) => `${row.group}\n${humanState(row.state)}: ${row.value[2]}\ncandidate state · not provenance`,
      },
      visualMap: {
        show: false,
        min: 0,
        max: maxCount,
        dimension: 2,
        inRange: { opacity: [0.08, 1] },
      },
      series: [{
        type: "heatmap",
        data: cells,
        label: {
          show: true,
          color: h.colors.text,
          fontSize: 9,
          formatter: ({ value }) => value[2] === 0 ? "" : String(value[2]),
        },
        emphasis: { itemStyle: { borderColor: h.colors.text, borderWidth: 1 } },
      }],
    };
  },
};

const namedSignalGrid = {
  id: "named-signal-grid",
  title: "Named signals worth inspecting",
  note: "Top endpoint path records are positioned by recorded touches and Git churn. Bubble size is heuristic risk; named patterns invite inspection rather than diagnose defects.",
  timeMode: "static",
  requirements: ["files"],
  build(data, _cursorMs, h) {
    const files = h.rank(data.files, (file) => file.risk_score, 18);
    const groups = new Map();
    files.forEach((file) => {
      const rows = groups.get(file.pattern) ?? [];
      rows.push(file);
      groups.set(file.pattern, rows);
    });
    return {
      ...h.base(),
      grid: { left: 74, right: 28, top: 28, bottom: 76 },
      legend: { type: "scroll", bottom: 4, textStyle: { color: h.colors.muted } },
      xAxis: {
        type: "value",
        name: "recorded touches · log scale",
        ...h.axis(),
        axisLabel: { color: h.colors.muted, formatter: (value) => h.formatCompact(Math.expm1(value)) },
      },
      yAxis: {
        type: "value",
        name: "Git churn · log scale",
        ...h.axis(),
        axisLabel: { color: h.colors.muted, formatter: (value) => h.formatCompact(Math.expm1(value)) },
      },
      tooltip: {
        trigger: "item",
        renderMode: "richText",
        formatter({ data: row }) {
          return `${row.path}\n${row.pattern} heuristic\n${h.formatCompact(row.touches)} recorded touches\n${h.formatCompact(row.churn)} Git churn\nrisk score ${row.risk.toFixed(2)}`;
        },
      },
      series: [...groups.entries()].map(([pattern, rows]) => ({
        name: pattern,
        type: "scatter",
        symbolSize: (value) => 8 + Math.sqrt(Math.max(0, value[2])) * 3,
        itemStyle: { color: patternColor(pattern, h), opacity: 0.82 },
        label: {
          show: true,
          position: "right",
          color: h.colors.text,
          fontFamily: "ui-monospace, monospace",
          fontSize: 9,
          formatter: ({ data: row }) => fileName(row.path),
        },
        labelLayout: { hideOverlap: true },
        data: rows.map((file) => ({
          value: [Math.log1p(file.touches), Math.log1p(file.churn), file.risk_score],
          path: file.path,
          pattern: file.pattern,
          touches: file.touches,
          churn: file.churn,
          risk: file.risk_score,
        })),
      })),
    };
  },
};

export const views = [
  activityPulse,
  observedDays,
  namedSignals,
  hotPaths,
  lineAgePixels,
  touchAssociationLanes,
  pathDayMatrix,
  associationStateMatrix,
  namedSignalGrid,
];
