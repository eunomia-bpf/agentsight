const ATTENTION_MS = 30 * 60_000;
const ATTENTION_HALF_LIFE_MS = 5 * 60_000;
const BIRTH_TRAVEL_MS = 3 * 60_000;
const WRITE_RIPPLE_MS = 3 * 60_000;
const CONTEXT_REVEAL_MS = 15 * 60_000;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

const modelCache = new WeakMap();

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

function hashUnit(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 0xffffffff;
}

function pathParts(path) {
  return path.split("/").filter(Boolean);
}

function parentDirectory(path) {
  return pathParts(path).slice(0, -1).join("/");
}

function topDirectory(path) {
  const parts = pathParts(path);
  return parts.length > 1 ? parts[0] : "(root)";
}

function directoryGroup(path) {
  const directories = pathParts(path).slice(0, -1);
  if (!directories.length) return "(root)";
  return directories.slice(0, Math.min(2, directories.length)).join("/");
}

function extension(path) {
  const name = pathParts(path).at(-1) ?? "";
  const index = name.lastIndexOf(".");
  return index > 0 ? name.slice(index).toLowerCase() : "(none)";
}

function commonDirectoryDepth(left, right) {
  const leftParts = pathParts(left).slice(0, -1);
  const rightParts = pathParts(right).slice(0, -1);
  let depth = 0;
  while (depth < leftParts.length && depth < rightParts.length && leftParts[depth] === rightParts[depth]) {
    depth += 1;
  }
  return depth;
}

function isCurrentTracked(file) {
  return Boolean(file.survives_to_head && file.current_path === file.path);
}

function hasTrackedLifetime(file) {
  return Boolean(file.tracked || file.lifetime_id || file.lifetime_ids?.length);
}

export function gitScopedNebulaFiles(data) {
  const byPath = new Map((data.files ?? []).map((file) => [file.path, { ...file }]));
  const observed = new Set(allAgentEvents(data).flatMap(eventPaths));
  for (const lifetime of data.file_lifetimes ?? []) {
    for (const path of lifetime.paths ?? []) {
      const file = byPath.get(path) ?? { path };
      Object.assign(file, {
        lifetime_id: lifetime.id,
        lifetime_ids: [lifetime.id],
        survives_to_head: lifetime.survives_to_head,
        current_path: lifetime.current_path,
        birth_ms: lifetime.birth_ms,
        death_ms: lifetime.death_ms,
      });
      byPath.set(path, file);
    }
  }
  for (const path of observed) {
    if (!byPath.has(path)) byPath.set(path, { path, observed_untracked: true });
  }
  return [...byPath.values()]
    .filter((file) => isCurrentTracked(file) || hasTrackedLifetime(file) || observed.has(file.path))
    .sort((left, right) => left.path.localeCompare(right.path));
}

function eventPaths(event) {
  return [...new Set(event.paths ?? (event.path ? [event.path] : []))];
}

function allAgentEvents(data) {
  const source = data.agent_events?.length ? data.agent_events : (data.events ?? []).map((event) => ({
    ...event,
    kind: event.kind ?? "tool",
    paths: eventPaths(event),
    write_paths: event.effect === "write" ? eventPaths(event) : [],
    process_chain: [],
    domains: [],
    durable_changes: [],
  }));
  return [...source].sort((left, right) => left.ts_ms - right.ts_ms || left.id.localeCompare(right.id));
}

function pathTouches(events) {
  return events.flatMap((event) => {
    const writePaths = new Set(event.write_paths ?? []);
    return eventPaths(event).map((path) => ({
      ...event,
      id: `${event.id}:${path}`,
      source_event_id: event.id,
      path,
      effect: writePaths.has(path) || (!event.write_paths?.length && event.effect === "write")
        ? "write" : event.effect === "write" ? "read" : event.effect,
    }));
  }).sort((left, right) => left.ts_ms - right.ts_ms || left.id.localeCompare(right.id));
}

function groupHue(group) {
  const top = group.split("/")[0];
  const base = (184 + 211 * hashUnit(top)) % 360;
  const inheritedShift = group === top ? 0 : (hashUnit(group) - 0.5) * 22;
  return Math.round((base + inheritedShift + 360) % 360);
}

function groupColor(group, lightness = 64, saturation = 72) {
  return `hsl(${groupHue(group)} ${saturation}% ${lightness}%)`;
}

function radialCloud(group, alpha) {
  const hue = groupHue(group);
  return {
    type: "radial", x: 0.5, y: 0.5, r: 0.5,
    colorStops: [
      { offset: 0, color: `hsla(${hue}, 82%, 64%, ${alpha})` },
      { offset: 0.36, color: `hsla(${hue}, 78%, 58%, ${alpha * 0.68})` },
      { offset: 0.72, color: `hsla(${hue}, 72%, 50%, ${alpha * 0.22})` },
      { offset: 1, color: `hsla(${hue}, 68%, 42%, 0)` },
    ],
  };
}

function buildGroupLayout(files) {
  const groups = new Map();
  for (const file of files) {
    const group = directoryGroup(file.path);
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(file);
  }
  for (const rows of groups.values()) rows.sort((left, right) => left.path.localeCompare(right.path));

  const topCounts = new Map();
  for (const [group, rows] of groups) {
    const top = group.split("/")[0];
    topCounts.set(top, (topCounts.get(top) ?? 0) + rows.length);
  }
  const tops = [...topCounts]
    .sort((left, right) => left[0].localeCompare(right[0]));
  const nonRootTotal = tops.reduce((sum, [id, count]) => sum + (id === "(root)" ? 0 : count), 0) || 1;
  const sectors = new Map();
  let angleCursor = -Math.PI / 2;
  for (const [id, count] of tops) {
    if (id === "(root)") continue;
    const span = 2 * Math.PI * count / nonRootTotal;
    sectors.set(id, { start: angleCursor, end: angleCursor + span, count });
    angleCursor += span;
  }
  const targets = new Map();
  for (const [top, sector] of sectors) {
    const children = [...groups]
      .filter(([group]) => group.split("/")[0] === top)
      .sort((left, right) => left[0].localeCompare(right[0]));
    let childCursor = sector.start;
    for (const [group, rows] of children) {
      const childSpan = (sector.end - sector.start) * rows.length / sector.count;
      const margin = Math.min(0.035, childSpan * 0.08);
      const start = childCursor + margin;
      const end = childCursor + childSpan - margin;
      rows.forEach((file, index) => {
        const angularUnit = rows.length <= 1 ? 0.5 : (index + 0.5) / rows.length;
        const jitter = (hashUnit(`${file.path}:angle`) - 0.5) / Math.max(3, rows.length);
        const angle = start + (end - start) * clamp(angularUnit + jitter, 0.02, 0.98);
        const radialUnit = (index * 0.61803398875 + hashUnit(`${group}:radius`)) % 1;
        const radius = 0.085 + 0.46 * Math.sqrt(0.08 + 0.92 * radialUnit);
        const wobble = (hashUnit(`${file.path}:wobble`) - 0.5) * 0.018;
        targets.set(file.path, [
          clamp(0.5 + 0.88 * (radius + wobble) * Math.cos(angle), 0.025, 0.975),
          clamp(0.5 + 0.78 * (radius + wobble) * Math.sin(angle), 0.04, 0.96),
        ]);
      });
      childCursor += childSpan;
    }
  }
  const rootRows = groups.get("(root)") ?? [];
  rootRows.forEach((file, index) => {
    const angle = index * GOLDEN_ANGLE + 2 * Math.PI * hashUnit(`${file.path}:root`);
    const radius = 0.018 + 0.075 * Math.sqrt((index + 0.5) / Math.max(1, rootRows.length));
    targets.set(file.path, [0.5 + radius * Math.cos(angle), 0.5 + 0.82 * radius * Math.sin(angle)]);
  });
  return { groups, targets };
}

function birthScore(path, candidate, event, lastSeen) {
  const sameParent = parentDirectory(path) === parentDirectory(candidate);
  const commonDepth = commonDirectoryDepth(path, candidate);
  const sameTop = topDirectory(path) === topDirectory(candidate);
  const sameExtension = extension(path) === extension(candidate);
  if (!sameParent && commonDepth === 0 && !sameExtension) return Number.NEGATIVE_INFINITY;
  const prior = lastSeen.get(candidate);
  const sameSession = prior?.session_id === event.session_id;
  const recency = prior ? 1 / Math.max(1, (event.ts_ms - prior.ts_ms) / 60_000) : 0;
  return Number(sameParent) * 10_000 + commonDepth * 1_000 + Number(sameTop) * 100
    + Number(sameExtension) * 20 + Number(sameSession) * 8 + Math.min(7, recency);
}

function buildBirthIndex(events, scopedPaths) {
  const first = new Map();
  const parent = new Map();
  const lastSeen = new Map();
  const ordered = [...events].sort((left, right) => left.ts_ms - right.ts_ms || left.id.localeCompare(right.id));
  for (const event of ordered) {
    if (!scopedPaths.has(event.path)) continue;
    if (!first.has(event.path)) {
      let bestPath = null;
      let bestScore = Number.NEGATIVE_INFINITY;
      for (const candidate of first.keys()) {
        const score = birthScore(event.path, candidate, event, lastSeen);
        if (score > bestScore || (score === bestScore && candidate.localeCompare(bestPath ?? "") < 0)) {
          bestPath = candidate;
          bestScore = score;
        }
      }
      first.set(event.path, event);
      if (Number.isFinite(bestScore) && bestPath) parent.set(event.path, bestPath);
    }
    lastSeen.set(event.path, event);
  }
  return { first, parent };
}

function buildModel(data) {
  const events = allAgentEvents(data);
  const touches = pathTouches(events);
  const files = gitScopedNebulaFiles(data);
  const fileByPath = new Map(files.map((file) => [file.path, file]));
  const scopedPaths = new Set(files.map((file) => file.path));
  const context = files.filter(isCurrentTracked);
  const observedPaths = new Set(touches.map((event) => event.path));
  const layoutFiles = files.filter((file) => isCurrentTracked(file) || observedPaths.has(file.path));
  const layout = buildGroupLayout(layoutFiles);
  const births = buildBirthIndex(touches, scopedPaths);
  const created = new Map();
  const deleted = new Map();
  const renamedFrom = new Map();
  for (const event of events) {
    for (const change of event.durable_changes ?? []) {
      const status = change.status?.[0];
      const evidence = { ...change, event };
      if (status === "A") created.set(change.path, evidence);
      if (status === "D") deleted.set(change.path, evidence);
      if ((status === "R" || status === "C") && change.old_path) {
        renamedFrom.set(change.path, { ...evidence, oldPath: change.old_path });
        if (status === "R") deleted.set(change.old_path, evidence);
      }
    }
  }
  const firstEventMs = events[0]?.ts_ms ?? Number.POSITIVE_INFINITY;
  const firstFileMs = touches.find((event) => scopedPaths.has(event.path))?.ts_ms
    ?? Number.POSITIVE_INFINITY;
  return {
    files, fileByPath, scopedPaths, context, events, touches, created, deleted, renamedFrom,
    ...layout, ...births, firstEventMs, firstFileMs,
  };
}

function modelFor(data) {
  if (!modelCache.has(data)) modelCache.set(data, buildModel(data));
  return modelCache.get(data);
}

function stateAt(model, cursorMs) {
  const visits = new Map();
  const last = new Map();
  for (const event of model.touches) {
    if (event.ts_ms > cursorMs) break;
    if (!model.scopedPaths.has(event.path)) continue;
    const weight = event.effect === "write" ? 2 : 1;
    visits.set(event.path, (visits.get(event.path) ?? 0) + weight);
    last.set(event.path, event);
  }
  return { visits, last };
}

function attentionAt(model, cursorMs) {
  const attention = new Map();
  for (const event of model.touches) {
    const age = cursorMs - event.ts_ms;
    if (age < 0 || age > ATTENTION_MS || !model.scopedPaths.has(event.path)) continue;
    const previous = attention.get(event.path);
    if (previous && previous.ts_ms > event.ts_ms) continue;
    attention.set(event.path, {
      ...event,
      age,
      strength: 2 ** (-age / ATTENTION_HALF_LIFE_MS),
      commandAssociated: event.category === "shell",
    });
  }
  return attention;
}

function smoothstep(value) {
  const unit = clamp(value, 0, 1);
  return unit * unit * (3 - 2 * unit);
}

function positionAt(path, cursorMs, model, memo = new Map()) {
  const key = `${path}:${cursorMs}`;
  if (memo.has(key)) return memo.get(key);
  const target = model.targets.get(path) ?? [0.5, 0.5];
  const first = model.first.get(path);
  if (!first || cursorMs < first.ts_ms) return target;
  const parentPath = model.parent.get(path);
  const rename = model.renamedFrom.get(path);
  const originBase = rename && rename.event.ts_ms <= first.ts_ms
    ? positionAt(rename.oldPath, rename.event.ts_ms, model, memo)
    : parentPath
      ? positionAt(parentPath, first.ts_ms, model, memo)
      : [0.5, 0.5];
  const offsetAngle = 2 * Math.PI * hashUnit(`${path}:birth`);
  const origin = parentPath || rename ? [
    originBase[0] + 0.008 * Math.cos(offsetAngle),
    originBase[1] + 0.008 * Math.sin(offsetAngle),
  ] : originBase;
  const progress = smoothstep((cursorMs - first.ts_ms) / BIRTH_TRAVEL_MS);
  const position = [
    origin[0] + (target[0] - origin[0]) * progress,
    origin[1] + (target[1] - origin[1]) * progress,
  ];
  memo.set(key, position);
  return position;
}

function percentile95(values) {
  if (!values.length) return 1;
  const ordered = [...values].sort((left, right) => left - right);
  return Math.max(1, ordered[Math.floor((ordered.length - 1) * 0.95)]);
}

function cloudLobes(points, alphaScale = 1, contextField = false) {
  const byGroup = new Map();
  for (const point of points) {
    if (!byGroup.has(point.group)) byGroup.set(point.group, []);
    byGroup.get(point.group).push(point);
  }
  return [...byGroup].flatMap(([group, rows]) => {
    const centroid = rows.reduce((sum, row) => ({
      x: sum.x + row.value[0] / rows.length,
      y: sum.y + row.value[1] / rows.length,
    }), { x: 0, y: 0 });
    const spread = Math.max(0.02, ...rows.map((row) => Math.hypot(
      row.value[0] - centroid.x, row.value[1] - centroid.y,
    )));
    const count = contextField
      ? clamp(Math.ceil(Math.sqrt(rows.length) * 0.7) + 6, 6, 42)
      : clamp(Math.ceil(Math.sqrt(rows.length) * 0.55) + 4, 4, 18);
    const ordered = [...rows].sort((left, right) => (
      Math.atan2(left.value[1] - centroid.y, left.value[0] - centroid.x)
      - Math.atan2(right.value[1] - centroid.y, right.value[0] - centroid.x)
      || left.path.localeCompare(right.path)
    ));
    const representatives = Array.from({ length: count }, (_, index) => (
      ordered[Math.floor(index * ordered.length / count)] ?? ordered[0]
    ));
    return representatives.map((row, index) => {
      const mix = contextField ? 0.92 : 0.82;
      const size = contextField
        ? clamp(48 + spread * 150 + 2.2 * Math.sqrt(rows.length), 58, 126)
        : clamp(72 + spread * 230 + 5 * Math.sqrt(rows.length), 82, 185);
      return {
        id: `${group}:cloud:${index}`,
        value: [
          centroid.x + (row.value[0] - centroid.x) * mix,
          centroid.y + (row.value[1] - centroid.y) * mix,
        ],
        group,
        symbolSize: size * (0.76 + 0.22 * hashUnit(`${group}:${contextField ? "context" : "active"}:${index}`)),
        itemStyle: {
          color: radialCloud(group, (contextField ? 0.14 : 0.12) * alphaScale),
          opacity: 1,
        },
      };
    });
  });
}

function ring(point, size, color, opacity, symbol = "circle") {
  return {
    ...point,
    symbol,
    symbolSize: size,
    itemStyle: {
      color: "transparent", borderColor: color, borderWidth: 1.25,
      opacity, shadowBlur: 10 * opacity, shadowColor: color,
    },
  };
}

function ambientAt(model, cursorMs) {
  const recent = model.events.filter((event) => {
    const age = cursorMs - event.ts_ms;
    return age >= 0 && age <= ATTENTION_MS;
  });
  const strength = (event) => 2 ** (-(cursorMs - event.ts_ms) / ATTENTION_HALF_LIFE_MS);
  const noPathCommands = recent
    .filter((event) => event.category === "shell" && eventPaths(event).length === 0)
    .slice(-6)
    .map((event, index, rows) => {
      const pulse = strength(event);
      return {
        id: event.id,
        value: [0.5, 0.5],
        event,
        symbol: "diamond",
        symbolSize: 24 + 16 * (rows.length - index) + 32 * (1 - pulse),
        itemStyle: {
          color: "transparent", borderColor: "#bd86ff", borderWidth: 1.2,
          opacity: 0.08 + 0.58 * pulse, shadowBlur: 12 * pulse, shadowColor: "#bd86ff",
        },
      };
    });
  const networkByKey = new Map();
  for (const event of recent.filter((row) => row.effect === "network" || row.domains?.length)) {
    const keys = event.domains?.length ? event.domains : [event.action];
    for (const key of keys) networkByKey.set(key, event);
  }
  const network = [...networkByKey].slice(-18).map(([domain, event]) => {
    const angle = 2 * Math.PI * hashUnit(domain);
    const pulse = strength(event);
    return {
      id: `${event.id}:${domain}`,
      value: [0.5 + 0.47 * Math.cos(angle), 0.5 + 0.43 * Math.sin(angle)],
      domain,
      event,
      symbol: "triangle",
      symbolRotate: angle * 180 / Math.PI + 90,
      symbolSize: 6 + 8 * pulse,
      itemStyle: {
        color: "#59e4ff", opacity: 0.18 + 0.78 * pulse,
        shadowBlur: 16 * pulse, shadowColor: "#59e4ff",
      },
    };
  });
  const processByName = new Map();
  for (const event of recent.filter((row) => (
    row.effect === "process" || row.effect === "test" || row.effect === "repo"
  ))) {
    const names = event.process_chain?.length ? event.process_chain : [event.action];
    for (const name of names) processByName.set(name, event);
  }
  const processes = [...processByName].slice(-14).map(([name, event]) => {
    const angle = 2 * Math.PI * hashUnit(`process:${name}`);
    const pulse = strength(event);
    const radius = 0.35 + 0.025 * hashUnit(name);
    return {
      id: `${event.id}:${name}`,
      value: [0.5 + radius * Math.cos(angle), 0.5 + 0.82 * radius * Math.sin(angle)],
      process: name,
      event,
      symbol: "rect",
      symbolRotate: 45,
      symbolSize: 4 + 6 * pulse,
      itemStyle: {
        color: "#ffc46b", opacity: 0.12 + 0.68 * pulse,
        shadowBlur: 10 * pulse, shadowColor: "#ffc46b",
      },
    };
  });
  const latestModel = recent.filter((event) => event.kind === "llm_response").at(-1);
  const modelHeartbeat = latestModel ? [{
    id: latestModel.id,
    value: [0.5, 0.5],
    event: latestModel,
    symbolSize: 5 + 10 * strength(latestModel),
    itemStyle: {
      color: "#61d7bf", opacity: 0.18 + 0.7 * strength(latestModel),
      shadowBlur: 22 * strength(latestModel), shadowColor: "#61d7bf",
    },
  }] : [];
  return { noPathCommands, network, processes, modelHeartbeat };
}

function lifecycleAt(model, cursorMs, pointsByPath) {
  const rows = [];
  const add = (path, evidence, kind) => {
    const age = cursorMs - evidence.event.ts_ms;
    if (age < 0 || age > WRITE_RIPPLE_MS) return;
    const point = pointsByPath.get(path);
    if (!point && kind !== "delete") return;
    const base = point ?? {
      path,
      value: model.targets.get(path) ?? [0.5, 0.5],
      symbolSize: 5,
    };
    const progress = clamp(age / WRITE_RIPPLE_MS, 0, 1);
    const color = kind === "create" ? "#72f1a8" : kind === "rename" ? "#6ddcff" : "#ff667d";
    rows.push({
      ...base,
      lifecycle: kind,
      evidence: evidence.evidence_bin,
      symbol: kind === "rename" ? "diamond" : "circle",
      symbolSize: base.symbolSize + 12 + 32 * progress,
      itemStyle: {
        color: "transparent", borderColor: color, borderWidth: 1.5,
        opacity: (1 - progress) * 0.9, shadowBlur: 14 * (1 - progress), shadowColor: color,
      },
    });
  };
  for (const [path, evidence] of model.created) add(path, evidence, "create");
  for (const [path, evidence] of model.renamedFrom) add(path, evidence, "rename");
  for (const [path, evidence] of model.deleted) add(path, evidence, "delete");
  return rows;
}

export function repositoryNebula(data, cursorMs, h) {
  const model = modelFor(data);
  if (!Number.isFinite(model.firstEventMs) || cursorMs < model.firstEventMs) {
    return {
      ...h.base(),
      grid: { left: 8, right: 8, top: 8, bottom: 8 },
      xAxis: { type: "value", min: 0, max: 1, show: false },
      yAxis: { type: "value", min: 0, max: 1, show: false },
      series: [
        { name: "repository context", type: "scatter", data: [] },
        { name: "repository context cloud", type: "scatter", data: [] },
        { name: "directory color field", type: "scatter", data: [] },
        { name: "files", type: "scatter", data: [] },
        { name: "active file cores", type: "scatter", data: [] },
        { name: "recent reads", type: "scatter", data: [] },
        { name: "recent writes", type: "scatter", data: [] },
        { name: "command-associated effects", type: "scatter", data: [] },
        { name: "durable lifecycle evidence", type: "scatter", data: [] },
        { name: "ambient commands", type: "scatter", data: [] },
        { name: "process activity", type: "scatter", data: [] },
        { name: "domain references", type: "scatter", data: [] },
        { name: "model heartbeat", type: "scatter", data: [] },
      ],
    };
  }

  const state = stateAt(model, cursorMs);
  const attention = attentionAt(model, cursorMs);
  const ambient = ambientAt(model, cursorMs);
  const visitP95 = percentile95([...state.visits.values()]);
  const positionMemo = new Map();
  const contextReveal = smoothstep((cursorMs - model.firstFileMs) / CONTEXT_REVEAL_MS);
  const observedPaths = new Set(state.visits.keys());
  const context = model.context
    .filter((file) => !observedPaths.has(file.path))
    .map((file) => ({
      id: file.path,
      value: model.targets.get(file.path) ?? [0.5, 0.5],
      path: file.path,
      group: directoryGroup(file.path),
      context: true,
      symbolSize: 2.1 + 1.1 / (1 + 0.2 * Math.max(0, pathParts(file.path).length - 1)),
      itemStyle: {
        color: groupColor(directoryGroup(file.path), 54, 52),
        opacity: 0.18 * contextReveal,
      },
    }));

  const points = [...observedPaths].filter((path) => {
    const deletion = model.deleted.get(path);
    return !deletion || cursorMs <= deletion.event.ts_ms + WRITE_RIPPLE_MS;
  }).map((path) => {
    const first = model.first.get(path);
    const focus = attention.get(path);
    const visits = state.visits.get(path) ?? 0;
    const depth = Math.max(0, pathParts(path).length - 1);
    const depthFactor = 1 / (1 + 0.2 * depth);
    const visitFactor = Math.log1p(visits) / Math.log1p(visitP95);
    const progress = smoothstep((cursorMs - first.ts_ms) / BIRTH_TRAVEL_MS);
    const baseline = clamp(0.28 + 0.15 * depthFactor + 0.20 * visitFactor, 0.3, 0.66);
    const position = positionAt(path, cursorMs, model, positionMemo);
    const group = directoryGroup(path);
    const deletion = model.deleted.get(path);
    const deletionFade = deletion && cursorMs >= deletion.event.ts_ms
      ? 1 - clamp((cursorMs - deletion.event.ts_ms) / WRITE_RIPPLE_MS, 0, 1)
      : 1;
    const file = model.fileByPath.get(path) ?? {};
    return {
      id: path,
      value: [...position, visits],
      path,
      group,
      visits,
      depth,
      focus,
      first,
      parent: model.parent.get(path),
      progress,
      tracked: isCurrentTracked(file) || hasTrackedLifetime(file),
      lifecycle: model.created.has(path) ? "durable add candidate"
        : model.renamedFrom.has(path) ? "durable rename candidate" : undefined,
      symbolSize: (4.2 + 1.4 * depthFactor + 0.35 * visitFactor)
        * (0.55 + 0.45 * progress) * (0.45 + 0.55 * deletionFade),
      itemStyle: {
        color: groupColor(group),
        opacity: baseline * (0.45 + 0.55 * progress) * deletionFade,
        borderColor: file.observed_untracked ? "#dce8f7" : "transparent",
        borderWidth: file.observed_untracked ? 0.8 : 0,
        shadowBlur: focus ? 4 + 18 * focus.strength : 2,
        shadowColor: focus
          ? focus.commandAssociated ? "#c9a7ff" : focus.effect === "write" ? "#ff8f83" : "#ffffff"
          : groupColor(group),
      },
    };
  });
  const pointsByPath = new Map(points.map((point) => [point.path, point]));
  const lifecycle = lifecycleAt(model, cursorMs, pointsByPath);

  const activeCores = points.filter((point) => point.focus).map((point) => {
    const command = point.focus.commandAssociated;
    const write = point.focus.effect === "write";
    return {
      ...point,
      symbol: command ? "diamond" : "circle",
      symbolSize: point.symbolSize + 2.5 + 5 * point.focus.strength,
      itemStyle: {
        color: command ? "#d1b3ff" : write ? "#ff9a82" : "#f8ffff",
        opacity: 0.28 + 0.72 * point.focus.strength,
        shadowBlur: 18 * point.focus.strength,
        shadowColor: command ? "#bd86ff" : write ? "#ff786c" : "#ffffff",
      },
    };
  });
  const reads = points
    .filter((point) => point.focus && !point.focus.commandAssociated && point.focus.effect !== "write")
    .map((point) => ring(
      point,
      point.symbolSize + 8 + 3 * (1 - point.focus.strength),
      "#f7ffff",
      0.18 + 0.72 * point.focus.strength,
    ));
  const writes = points
    .filter((point) => point.focus && !point.focus.commandAssociated && point.focus.effect === "write" && point.focus.age <= WRITE_RIPPLE_MS)
    .flatMap((point) => [0, 0.28, 0.56].map((offset) => {
      const progress = clamp(point.focus.age / WRITE_RIPPLE_MS + offset, 0, 1);
      return ring(
        point,
        point.symbolSize + 9 + 38 * progress,
        "#ff8a82",
        (1 - progress) * (0.32 + 0.55 * point.focus.strength),
      );
    }));
  const commandEffects = points
    .filter((point) => point.focus?.commandAssociated)
    .flatMap((point) => {
      const rows = [{
        ...point,
        symbol: "diamond",
        symbolSize: point.symbolSize + 7,
        itemStyle: {
          color: "transparent", borderColor: "#d1b3ff", borderWidth: 1.4,
          opacity: 0.25 + 0.7 * point.focus.strength,
          shadowBlur: 13 * point.focus.strength, shadowColor: "#bd86ff",
        },
      }];
      if (point.focus.effect !== "write" || point.focus.age > WRITE_RIPPLE_MS) return rows;
      return rows.concat([0.15, 0.5].map((offset) => {
        const progress = clamp(point.focus.age / WRITE_RIPPLE_MS + offset, 0, 1);
        return ring(point, point.symbolSize + 12 + 32 * progress, "#bd86ff", (1 - progress) * 0.7, "diamond");
      }));
    });

  const tooltip = ({ data: row = {} }) => {
    if (row.domain) return `${row.domain}\nrecorded domain-bearing tool event\n${row.event.vendor} · ${row.event.action}`;
    if (row.process) return `${row.process}\nrecorded process/repository activity\n${row.event.vendor} · ${row.event.action}`;
    if (!row.path && row.event) return `${row.event.vendor} · ${row.event.action}\n${row.event.effect} · no repository path`;
    if (!row.path) return "";
    if (row.lifecycle && !row.first) return `${row.path}\nAgent-associated durable ${row.lifecycle}\n${row.evidence ?? "candidate association"}`;
    if (row.context) return `${row.path}\nGit-tracked repository context\nnot yet observed by an Agent in this window`;
    const firstLabel = row.first.effect === "write" ? "first observed write" : "first discovered";
    const focus = row.focus
      ? `\nrecent: ${row.focus.vendor} ${row.focus.effect}${row.focus.commandAssociated ? " (command-associated)" : ""} · ${Math.round(row.focus.age / 60_000)} min ago`
      : "";
    const scope = row.tracked ? "Git-scoped" : "Agent-observed untracked";
    const durable = row.lifecycle ? `\n${row.lifecycle}` : "";
    return `${row.path}\n${row.group} cloud · depth ${row.depth}\n${row.visits} weighted Agent visits · ${scope}\n${firstLabel} via ${row.first.action}${row.parent ? ` near ${row.parent}` : ""}${durable}${focus}`;
  };

  return {
    ...h.base(),
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    tooltip: { renderMode: "richText", formatter: tooltip },
    series: [
      {
        id: "repository-context", name: "repository context", type: "scatter", silent: false, z: 1,
        animationDurationUpdate: 420, data: context,
      },
      {
        id: "repository-context-cloud", name: "repository context cloud", type: "scatter", silent: true, z: 0,
        animationDurationUpdate: 520, animationEasingUpdate: "cubicOut",
        data: cloudLobes(context, 0.08 * contextReveal, true),
      },
      {
        id: "directory-clouds", name: "directory color field", type: "scatter", silent: true, z: 2,
        animationDurationUpdate: 520, animationEasingUpdate: "cubicOut", data: cloudLobes(points),
      },
      {
        id: "observed-files", name: "files", type: "scatter", z: 4,
        animationDurationUpdate: 420, animationEasingUpdate: "cubicOut", data: points,
        emphasis: { scale: 1.8 },
      },
      {
        id: "active-cores", name: "active file cores", type: "scatter", silent: true, z: 5,
        animationDurationUpdate: 180, data: activeCores,
      },
      {
        id: "read-rings", name: "recent reads", type: "scatter", silent: true, z: 6,
        animationDurationUpdate: 180, data: reads,
      },
      {
        id: "write-ripples", name: "recent writes", type: "scatter", silent: true, z: 6,
        animationDurationUpdate: 180, data: writes,
      },
      {
        id: "command-effects", name: "command-associated effects", type: "scatter", silent: true, z: 6,
        animationDurationUpdate: 180, data: commandEffects,
      },
      {
        id: "lifecycle-effects", name: "durable lifecycle evidence", type: "scatter", z: 7,
        animationDurationUpdate: 180, data: lifecycle,
      },
      {
        id: "ambient-commands", name: "ambient commands", type: "scatter", z: 3,
        animationDurationUpdate: 180, data: ambient.noPathCommands,
      },
      {
        id: "process-activity", name: "process activity", type: "scatter", z: 3,
        animationDurationUpdate: 180, data: ambient.processes,
      },
      {
        id: "network-references", name: "domain references", type: "scatter", z: 8,
        animationDurationUpdate: 180, data: ambient.network,
      },
      {
        id: "model-heartbeat", name: "model heartbeat", type: "scatter", silent: true, z: 8,
        animationDurationUpdate: 180, data: ambient.modelHeartbeat,
      },
    ],
  };
}

export const nebulaDurations = {
  attentionMs: ATTENTION_MS,
  birthTravelMs: BIRTH_TRAVEL_MS,
  writeRippleMs: WRITE_RIPPLE_MS,
};
