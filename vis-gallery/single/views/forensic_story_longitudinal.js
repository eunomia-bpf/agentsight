const fileName = (path) => path.split("/").at(-1) || path;

function riskColor(risk, minimum, maximum) {
  if (!Number.isFinite(risk) || maximum <= minimum) return "hsl(95 60% 41%)";
  const low = Math.log1p(Math.max(0, minimum));
  const high = Math.log1p(Math.max(0, maximum));
  const t = Math.max(0, Math.min(1, (Math.log1p(Math.max(0, risk)) - low) / (high - low)));
  return `hsl(${190 - t * 170} 60% ${31 + t * 20}%)`;
}

function graphOption(edges, directed, h) {
  const rows = edges.slice(0, 180);
  const weights = new Map();
  for (const edge of rows) {
    weights.set(edge.source, (weights.get(edge.source) || 0) + edge.count);
    weights.set(edge.target, (weights.get(edge.target) || 0) + edge.count);
  }
  const nodes = [...weights.entries()].map(([path, weight]) => ({
    id: path,
    name: fileName(path),
    path,
    value: weight,
    symbolSize: Math.max(7, Math.min(25, 6 + Math.sqrt(weight) * 2.2)),
  }));
  return {
    ...h.base(),
    graphic: nodes.length ? [] : [{
      type: "text",
      left: "center",
      top: "middle",
      silent: true,
      style: {
        text: directed ? "No read-before-write sequence by this cursor" : "No Git co-change edges",
        fill: h.colors.muted,
        fontSize: 13,
      },
    }],
    tooltip: {
      trigger: "item",
      renderMode: "richText",
      formatter: (params) => {
        const row = params.data;
        if (row.source !== undefined) {
          const qualifier = directed
            ? "ordered read before write; not causality"
            : "same-commit correlation; not causality";
          return `${row.source}\n→ ${row.target}\n${row.value} observations\n${qualifier}`;
        }
        return `${row.path}\n${row.value} incident edge weight`;
      },
    },
    series: [{
      type: "graph",
      layout: "circular",
      roam: true,
      circular: { rotateLabel: false },
      data: nodes,
      links: rows.map((edge) => ({
        source: edge.source,
        target: edge.target,
        value: edge.count,
        semantics: edge.semantics,
        lineStyle: { width: Math.max(0.5, Math.min(5, Math.sqrt(edge.count) * 0.65)) },
      })),
      edgeSymbol: directed ? ["none", "arrow"] : ["none", "none"],
      edgeSymbolSize: directed ? 7 : 0,
      label: { show: true, position: "right", color: h.colors.text, fontSize: 8 },
      itemStyle: { color: "#4c83a6", borderColor: "#9fc8df", borderWidth: 0.5 },
      lineStyle: {
        color: directed ? "#d69b62" : "#56718b",
        curveness: directed ? 0.18 : 0.08,
        opacity: 0.48,
      },
      emphasis: { focus: "adjacency", lineStyle: { opacity: 0.9 } },
    }],
  };
}

function hourlyBuckets(events, verifications) {
  const rows = new Map();
  const ensure = (ts) => {
    const hour = Math.floor(ts / 3_600_000) * 3_600_000;
    if (!rows.has(hour)) rows.set(hour, { ts_ms: hour, read: 0, write: 0, verify: 0 });
    return rows.get(hour);
  };
  for (const event of events) {
    const row = ensure(event.ts_ms);
    if (event.effect === "read") row.read += 1;
    if (event.effect === "write") row.write += 1;
  }
  for (const event of verifications) ensure(event.ts_ms).verify += 1;
  return [...rows.values()].sort((a, b) => a.ts_ms - b.ts_ms);
}

function gapAware(rows, key) {
  const points = [];
  rows.forEach((row, index) => {
    const previous = rows[index - 1];
    if (previous && row.ts_ms - previous.ts_ms > 3_600_000) {
      points.push([previous.ts_ms + 3_600_000, null]);
      if (row.ts_ms - previous.ts_ms > 7_200_000) points.push([row.ts_ms - 3_600_000, null]);
    }
    points.push([row.ts_ms, row[key]]);
  });
  return points;
}

function matureDayRows(data, events, verifications) {
  return data.source_days
    .filter((row) => row.quantitative_status === "mature_descriptive")
    .map((source) => {
      const dayEvents = events.filter((event) => event.day === source.day);
      return {
        day: source.day,
        read: dayEvents.filter((event) => event.effect === "read").length,
        write: dayEvents.filter((event) => event.effect === "write").length,
        verify: verifications.filter((event) => event.day === source.day).length,
      };
    });
}

export const views = [
  {
    id: "hotspot-treemap",
    title: "Hotspot investment map",
    note: "Area is endpoint file size; color is a heuristic blend of Git churn and recorded attention. Cursor-visible attention is an overlay, not a defect prediction.",
    timeMode: "endpoint-overlay",
    requirements: ["files", "events"],
    build(data, cursorMs, h) {
      const active = new Set(h.visibleEvents(data, cursorMs).map((event) => event.path));
      const files = h.rank(
        data.files.filter((file) => file.survives_to_head && file.path === file.current_path),
        (file) => file.risk_score,
        90,
      );
      const risks = files.map((file) => file.risk_score).filter(Number.isFinite);
      const minimum = risks.length ? Math.min(...risks) : 0;
      const maximum = risks.length ? Math.max(...risks) : 1;
      return {
        ...h.base(),
        tooltip: {
          renderMode: "richText",
          formatter: ({ data: row }) => `${row.path}\nrisk ${row.risk.toFixed(2)}\n${row.touches} recorded touches · ${row.churn} Git churn`,
        },
        series: [{
          type: "treemap",
          roam: true,
          breadcrumb: { show: false },
          data: files.map((file) => ({
            name: fileName(file.path),
            path: file.path,
            value: Math.max(1, file.current_bytes),
            risk: file.risk_score,
            churn: file.churn,
            touches: file.touches,
            itemStyle: {
              color: riskColor(file.risk_score, minimum, maximum),
              opacity: active.has(file.path) ? 0.96 : 0.32,
            },
          })),
          label: { color: "#f2f5fb", fontSize: 9 },
          itemStyle: { borderColor: "#080c14", gapWidth: 1 },
        }],
      };
    },
  },
  {
    id: "git-cochange-network",
    title: "Git co-change network",
    note: "Edges mean files changed in the same Git commit. This is durable-history correlation, not runtime, semantic, or causal dependency.",
    timeMode: "static",
    requirements: ["cochange_edges"],
    build(data, _cursorMs, h) {
      return graphOption(data.cochange_edges, false, h);
    },
  },
  {
    id: "read-before-write-network",
    title: "Read-before-write network",
    note: "A directed edge records temporal order inside a session. It is not a causal edge and does not prove that a read informed a write.",
    timeMode: "cumulative",
    requirements: ["events"],
    build(data, cursorMs, h) {
      return graphOption(h.orderedEdges(h.visibleEvents(data, cursorMs)), true, h);
    },
  },
  {
    id: "session-storylines",
    title: "Session journeys through repository territory",
    note: "Each pseudonymous agent session is a trajectory across top-level path groups. The story is observed navigation, not intent reconstruction.",
    timeMode: "cumulative",
    requirements: ["sessions", "events", "meta"],
    build(data, cursorMs, h) {
      const events = h.visibleEvents(data, cursorMs);
      const active = new Set(events.map((event) => event.session_id));
      const sessions = h.rank(data.sessions.filter((session) => active.has(session.id)), (session) => session.tool_events, 28);
      const groups = [...new Set(events.map((event) => event.group))].slice(0, 22);
      return {
        ...h.base(),
        grid: { left: 155, right: 22, top: 24, bottom: 44 },
        xAxis: { type: "time", min: data.meta.window_start_ms, max: data.meta.window_end_ms, ...h.axis() },
        yAxis: {
          type: "category",
          data: groups,
          axisLabel: { color: h.colors.muted, width: 142, overflow: "truncate", fontSize: 9 },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        dataZoom: [{ type: "inside" }],
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ data: row }) => `${row.session}\n${row.path}`,
        },
        series: sessions.map((session) => ({
          name: session.id,
          type: "line",
          showSymbol: true,
          symbolSize: 5,
          connectNulls: false,
          lineStyle: { width: 1.4, color: h.vendorColor(session.vendor), opacity: 0.55 },
          itemStyle: { color: h.vendorColor(session.vendor) },
          data: events
            .filter((event) => event.session_id === session.id && groups.includes(event.group))
            .sort((a, b) => a.ts_ms - b.ts_ms || a.id.localeCompare(b.id))
            .map((event) => ({ value: [event.ts_ms, event.group], session: session.id, path: event.path })),
        })),
      };
    },
  },
  {
    id: "git-ownership-flow",
    title: "Durable Git authorship × directory",
    note: "Left nodes are Git author labels, not agent vendors. Agent-native vendor identity remains a separate process layer and is never inferred from authorship.",
    timeMode: "static",
    requirements: ["ownership"],
    build(data, _cursorMs, h) {
      const rows = h.rank(data.ownership, (row) => row.churn, 30);
      const names = [...new Set(rows.flatMap((row) => [`author:${row.author}`, `group:${row.group}`]))];
      return {
        ...h.base(),
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ data: row }) => row.source
            ? `${row.source.slice(7)}\n→ ${row.target.slice(6)}\n${row.value} Git churn`
            : `${row.name.startsWith("author:") ? "Git author" : "directory"}: ${row.name.split(":").slice(1).join(":")}`,
        },
        series: [{
          type: "sankey",
          nodeAlign: "justify",
          data: names.map((name) => ({
            name,
            itemStyle: { color: name.startsWith("author:") ? "#7b93ad" : "#2c6e73" },
          })),
          links: rows.map((row) => ({ source: `author:${row.author}`, target: `group:${row.group}`, value: row.churn })),
          lineStyle: { color: "gradient", opacity: 0.28 },
          label: {
            color: h.colors.text,
            fontSize: 9,
            formatter: ({ name }) => name.split(":").slice(1).join(":"),
          },
        }],
      };
    },
  },
  {
    id: "trajectory-cast",
    title: "Visible trajectory cast",
    note: "Pseudonymous agent sessions ranked by native tool-event count; bar color represents the agent vendor, never a Git author label.",
    timeMode: "endpoint-overlay",
    requirements: ["sessions", "events"],
    build(data, cursorMs, h) {
      const active = new Set(h.visibleEvents(data, cursorMs).map((event) => event.session_id));
      const sessions = h.rank(data.sessions.filter((session) => active.has(session.id)), (session) => session.tool_events, 28).reverse();
      return {
        ...h.base(),
        grid: { left: 190, right: 28, top: 18, bottom: 42 },
        xAxis: { type: "value", name: "native tool events", ...h.axis() },
        yAxis: {
          type: "category",
          data: sessions.map((session) => session.id),
          axisLabel: { color: h.colors.muted, width: 178, overflow: "truncate", fontSize: 9 },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ data: row }) => `${row.session}\nagent vendor: ${row.vendor}\n${row.value} native tool events`,
        },
        series: [{
          type: "bar",
          barMaxWidth: 18,
          data: sessions.map((session) => ({
            value: session.tool_events,
            session: session.id,
            vendor: session.vendor,
            itemStyle: { color: h.vendorColor(session.vendor), opacity: 0.82 },
          })),
        }],
      };
    },
  },
  {
    id: "activity-punch-card",
    title: "Activity punch card",
    note: "UTC clock-hour rhythm across real observation days. Sparse and right-censored days remain visible; absent hours are not interpolated.",
    timeMode: "mixed-day",
    requirements: ["source_days", "events", "verification_events"],
    build(data, cursorMs, h) {
      const events = h.visibleEvents(data, cursorMs);
      const verifications = h.visibleVerifications(data, cursorMs);
      const days = data.source_days.map((row) => row.day);
      const values = days.flatMap((day, dayIndex) => Array.from({ length: 24 }, (_, hour) => [
        hour,
        dayIndex,
        events.filter((event) => event.day === day && new Date(event.ts_ms).getUTCHours() === hour).length
          + verifications.filter((event) => event.day === day && new Date(event.ts_ms).getUTCHours() === hour).length,
      ]));
      return {
        ...h.base(),
        grid: { left: 92, right: 24, top: 24, bottom: 48 },
        xAxis: { type: "category", data: Array.from({ length: 24 }, (_, hour) => hour), name: "UTC hour", ...h.axis() },
        yAxis: { type: "category", data: days, ...h.axis() },
        visualMap: {
          min: 0,
          max: Math.max(1, ...values.map((row) => row[2])),
          show: false,
          inRange: { color: ["#101827", "#235d78", "#5bd2b7", "#f4c95d"] },
        },
        tooltip: {
          position: "top",
          renderMode: "richText",
          formatter: ({ data: row }) => `${days[row[1]]} ${String(row[0]).padStart(2, "0")}:00 UTC\n${row[2]} observations`,
        },
        series: [{ type: "heatmap", data: values, label: { show: true, color: "#dce8f7", fontSize: 9 } }],
      };
    },
  },
  {
    id: "agent-vitals",
    title: "Agent vital signs",
    note: "Hourly read, write, and verify traces break across unobserved gaps. They reveal longitudinal shape; they are not a success score.",
    timeMode: "cumulative",
    requirements: ["events", "verification_events"],
    build(data, cursorMs, h) {
      const rows = hourlyBuckets(h.visibleEvents(data, cursorMs), h.visibleVerifications(data, cursorMs));
      const definitions = [
        ["read", h.colors.read],
        ["write", h.colors.write],
        ["verify", h.colors.verify],
      ];
      return {
        ...h.base(),
        grid: { left: 52, right: 22, top: 26, bottom: 52 },
        legend: { bottom: 2, textStyle: { color: h.colors.muted } },
        xAxis: { type: "time", ...h.axis() },
        yAxis: { type: "value", name: "observations / hour", ...h.axis() },
        tooltip: { trigger: "axis", renderMode: "richText" },
        series: definitions.map(([key, color], index) => ({
          name: key,
          type: "line",
          showSymbol: false,
          connectNulls: false,
          lineStyle: { color, width: 1.5 },
          itemStyle: { color },
          areaStyle: { color, opacity: 0.06 },
          data: gapAware(rows, key),
          ...(index === 0 ? {
            markLine: {
              silent: true,
              symbol: "none",
              lineStyle: { color: "#f6f8ff", width: 1, opacity: 0.5 },
              data: [{ xAxis: cursorMs, name: "cursor" }],
            },
          } : {}),
        })),
      };
    },
  },
  {
    id: "vendor-semantic-flow",
    title: "Agent vendor → semantic unit flow",
    note: "Flow width counts recorded path events. Vendor is the agent-native history source; semantic unit is observed effect, not inferred intent.",
    timeMode: "cumulative",
    requirements: ["events"],
    build(data, cursorMs, h) {
      const events = h.visibleEvents(data, cursorMs);
      const vendors = [...new Set(events.map((event) => event.vendor))].sort();
      const effects = [...new Set(events.map((event) => event.effect))].sort();
      const vendorNodes = vendors.map((vendor) => ({
        name: `vendor:${vendor}`,
        itemStyle: { color: h.vendorColor(vendor) },
      }));
      const effectNodes = effects.map((effect) => ({ name: `effect:${effect}`, itemStyle: { color: "#2c6e73" } }));
      const links = vendors.flatMap((vendor) => effects.map((effect) => ({
        source: `vendor:${vendor}`,
        target: `effect:${effect}`,
        value: events.filter((event) => event.vendor === vendor && event.effect === effect).length,
      }))).filter((row) => row.value > 0);
      return {
        ...h.base(),
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ data: row }) => row.source
            ? `${row.source.slice(7)} agent history\n→ ${row.target.slice(7)}\n${row.value} path observations`
            : row.name.replace(":", ": "),
        },
        series: [{
          type: "sankey",
          data: [...vendorNodes, ...effectNodes],
          links,
          lineStyle: { color: "gradient", opacity: 0.35 },
          label: {
            color: h.colors.text,
            fontSize: 10,
            formatter: ({ name }) => name.split(":").slice(1).join(":"),
          },
        }],
      };
    },
  },
  {
    id: "verification-lag",
    title: "Write-to-next-verify lag",
    note: "Each dot is an observed write followed by the next verification event in the same session. Missing dots remain missing; order does not prove coverage.",
    timeMode: "cumulative",
    requirements: ["events", "verification_events"],
    build(data, cursorMs, h) {
      const events = h.visibleEvents(data, cursorMs);
      const verifications = h.visibleVerifications(data, cursorMs);
      const writes = events.filter((event) => event.effect === "write").slice(-250);
      const points = writes.flatMap((write) => {
        const next = verifications.find((event) => event.session_id === write.session_id && event.ts_ms >= write.ts_ms);
        return next ? [{
          value: [write.ts_ms, (next.ts_ms - write.ts_ms) / 60_000],
          session: write.session_id,
          path: write.path,
          verifyAction: next.action,
        }] : [];
      });
      return {
        ...h.base(),
        grid: { left: 54, right: 18, top: 20, bottom: 46 },
        xAxis: { type: "time", ...h.axis() },
        yAxis: { type: "value", name: "minutes", ...h.axis() },
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ data: row }) => `${row.path}\n${row.value[1].toFixed(2)} min to next verify\n${row.session}\nverification action: ${row.verifyAction}`,
        },
        series: [{
          type: "scatter",
          symbolSize: 7,
          itemStyle: { color: h.colors.verify, opacity: 0.65 },
          data: points,
        }],
      };
    },
  },
  {
    id: "session-receipt",
    title: "Completed sessions in the visible interval",
    note: "Reported token units are summed only for sessions fully visible by the cursor. Native counters may be cumulative or implausible; no cost conversion is attempted.",
    timeMode: "cumulative",
    requirements: ["meta", "sessions", "events", "verification_events"],
    build(data, cursorMs, h) {
      const events = h.visibleEvents(data, cursorMs);
      const verifications = h.visibleVerifications(data, cursorMs);
      const active = new Set(events.map((event) => event.session_id));
      const completed = data.sessions.filter((session) => active.has(session.id)
        && session.started_at_ms !== null
        && session.ended_at_ms !== null
        && session.started_at_ms >= data.meta.window_start_ms
        && session.ended_at_ms <= cursorMs);
      const values = [
        events.length,
        events.filter((event) => event.effect === "write").length,
        verifications.length,
        completed.reduce((sum, session) => sum + session.reported_tokens, 0),
        completed.length,
      ];
      const labels = ["path observations", "writes", "verification events", "reported token units", "completed sessions"];
      return {
        ...h.base(),
        grid: { left: 170, right: 78, top: 22, bottom: 38 },
        xAxis: { type: "log", min: 1, ...h.axis(), axisLabel: { color: h.colors.muted, formatter: (value) => h.formatCompact(value) } },
        yAxis: { type: "category", data: labels, ...h.axis() },
        tooltip: {
          trigger: "item",
          renderMode: "richText",
          formatter: ({ dataIndex }) => `${labels[dataIndex]}\n${values[dataIndex].toLocaleString("en")}`,
        },
        series: [{
          type: "bar",
          barMaxWidth: 24,
          label: {
            show: true,
            position: "right",
            color: h.colors.text,
            formatter: ({ dataIndex }) => h.formatCompact(values[dataIndex]),
          },
          data: values.map((value, index) => ({
            value: Math.max(1, value),
            actualValue: value,
            itemStyle: { color: index === 3 ? "#f4c95d" : "#4c83a6", opacity: 0.8 },
          })),
        }],
      };
    },
  },
  {
    id: "mature-day-comparison",
    title: "Mature observation days, side by side",
    note: "A normalized silhouette compares only mature days' observed event mix. Right-censored days are excluded rather than imputed.",
    timeMode: "mixed-day",
    requirements: ["source_days", "events", "verification_events"],
    build(data, cursorMs, h) {
      const rows = matureDayRows(data, h.visibleEvents(data, cursorMs), h.visibleVerifications(data, cursorMs));
      const effects = [
        ["read", h.colors.read],
        ["write", h.colors.write],
        ["verify", h.colors.verify],
      ];
      return {
        ...h.base(),
        grid: { left: 102, right: 24, top: 34, bottom: 56 },
        legend: { bottom: 2, textStyle: { color: h.colors.muted } },
        xAxis: { type: "value", min: 0, max: 100, name: "% observed mix", ...h.axis() },
        yAxis: { type: "category", data: rows.map((row) => row.day), ...h.axis() },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          renderMode: "richText",
          formatter: (params) => {
            const index = params[0]?.dataIndex ?? 0;
            const row = rows[index];
            return `${row.day}\nread ${row.read}\nwrite ${row.write}\nverify ${row.verify}\nmature descriptive day`;
          },
        },
        series: effects.map(([effect, color]) => ({
          name: effect,
          type: "bar",
          stack: "mix",
          barMaxWidth: 38,
          itemStyle: { color, opacity: 0.8 },
          data: rows.map((row) => {
            const total = row.read + row.write + row.verify;
            return total ? (100 * row[effect]) / total : 0;
          }),
        })),
      };
    },
  },
];
