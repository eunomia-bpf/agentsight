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
  return Boolean(file.lifetime_id || file.lifetime_ids?.length);
}

export function gitScopedNebulaFiles(data) {
  const observed = new Set((data.events ?? []).map((event) => event.path));
  return (data.files ?? [])
    .filter((file) => isCurrentTracked(file) || (observed.has(file.path) && hasTrackedLifetime(file)))
    .sort((left, right) => left.path.localeCompare(right.path));
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

function relaxCircles(nodes, iterations, bounds) {
  for (let iteration = 0; iteration < iterations; iteration += 1) {
    const movement = nodes.map(() => ({ x: 0, y: 0 }));
    for (let left = 0; left < nodes.length; left += 1) {
      for (let right = left + 1; right < nodes.length; right += 1) {
        const a = nodes[left];
        const b = nodes[right];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distance = Math.hypot(dx, dy);
        const desired = a.radius + b.radius + 0.018;
        if (distance >= desired) continue;
        if (distance < 1e-6) {
          const angle = 2 * Math.PI * hashUnit(`${a.id}:${b.id}`);
          dx = Math.cos(angle) * 1e-3;
          dy = Math.sin(angle) * 1e-3;
          distance = 1e-3;
        }
        const push = (desired - distance) * 0.5;
        const x = dx / distance * push;
        const y = dy / distance * push;
        movement[left].x -= x;
        movement[left].y -= y;
        movement[right].x += x;
        movement[right].y += y;
      }
    }
    nodes.forEach((node, index) => {
      const stability = iteration < iterations * 0.7 ? 0.16 : 0.28;
      node.x += movement[index].x + (node.homeX - node.x) * stability;
      node.y += movement[index].y + (node.homeY - node.y) * stability;
      node.x = clamp(node.x, bounds.left + node.radius, bounds.right - node.radius);
      node.y = clamp(node.y, bounds.top + node.radius, bounds.bottom - node.radius);
    });
  }
  return nodes;
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
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([id, count], index, all) => {
      const fraction = all.length <= 1 ? 0 : Math.sqrt((index + 0.35) / all.length);
      const angle = -Math.PI / 2 + index * GOLDEN_ANGLE + (hashUnit(id) - 0.5) * 0.38;
      const distance = all.length <= 1 ? 0 : 0.36 * fraction;
      const radius = clamp(0.07 + 0.0072 * Math.sqrt(count), 0.08, 0.19);
      const homeX = 0.5 + distance * Math.cos(angle);
      const homeY = 0.5 + 0.78 * distance * Math.sin(angle);
      return { id, count, radius, homeX, homeY, x: homeX, y: homeY };
    });
  relaxCircles(tops, 72, { left: 0.04, right: 0.96, top: 0.06, bottom: 0.94 });
  const topById = new Map(tops.map((row) => [row.id, row]));

  const groupNodes = [];
  for (const top of tops) {
    const children = [...groups]
      .filter(([group]) => group.split("/")[0] === top.id)
      .sort((left, right) => right[1].length - left[1].length || left[0].localeCompare(right[0]));
    children.forEach(([group, rows], index) => {
      const fraction = children.length <= 1 ? 0 : Math.sqrt((index + 0.25) / children.length);
      const angle = index * GOLDEN_ANGLE + 2 * Math.PI * hashUnit(`${top.id}:${group}`);
      const distance = children.length <= 1 ? 0 : top.radius * 0.62 * fraction;
      const radius = clamp(0.018 + 0.0048 * Math.sqrt(rows.length), 0.024, top.radius * 0.62);
      const homeX = top.x + distance * Math.cos(angle);
      const homeY = top.y + 0.78 * distance * Math.sin(angle);
      groupNodes.push({ id: group, top: top.id, count: rows.length, radius, homeX, homeY, x: homeX, y: homeY });
    });
  }
  for (const top of tops) {
    const children = groupNodes.filter((row) => row.top === top.id);
    relaxCircles(children, 42, {
      left: clamp(top.x - top.radius, 0.03, 0.9),
      right: clamp(top.x + top.radius, 0.1, 0.97),
      top: clamp(top.y - top.radius, 0.04, 0.9),
      bottom: clamp(top.y + top.radius, 0.1, 0.96),
    });
  }
  const groupById = new Map(groupNodes.map((row) => [row.id, row]));
  const targets = new Map();
  for (const [group, rows] of groups) {
    const center = groupById.get(group) ?? topById.get(group.split("/")[0]) ?? { x: 0.5, y: 0.5, radius: 0.08 };
    rows.forEach((file, index) => {
      const fraction = rows.length <= 1 ? 0 : Math.sqrt((index + 0.4) / rows.length);
      const angle = index * GOLDEN_ANGLE + 2 * Math.PI * hashUnit(`${file.path}:position`);
      const irregularity = 0.82 + 0.18 * hashUnit(`${file.path}:radius`);
      const radius = center.radius * 0.88 * fraction * irregularity;
      targets.set(file.path, [
        clamp(center.x + radius * Math.cos(angle), 0.025, 0.975),
        clamp(center.y + 0.78 * radius * Math.sin(angle), 0.035, 0.965),
      ]);
    });
  }
  return { groups, groupById, targets };
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
  const files = gitScopedNebulaFiles(data);
  const scopedPaths = new Set(files.map((file) => file.path));
  const context = files.filter(isCurrentTracked);
  const layout = buildGroupLayout(files);
  const births = buildBirthIndex(data.events ?? [], scopedPaths);
  const firstEventMs = Math.min(...[...births.first.values()].map((event) => event.ts_ms));
  return { files, scopedPaths, context, ...layout, ...births, firstEventMs };
}

function modelFor(data) {
  if (!modelCache.has(data)) modelCache.set(data, buildModel(data));
  return modelCache.get(data);
}

function stateAt(data, model, cursorMs) {
  const visits = new Map();
  const last = new Map();
  for (const event of data.events ?? []) {
    if (event.ts_ms > cursorMs) break;
    if (!model.scopedPaths.has(event.path)) continue;
    const weight = event.effect === "write" ? 2 : 1;
    visits.set(event.path, (visits.get(event.path) ?? 0) + weight);
    last.set(event.path, event);
  }
  return { visits, last };
}

function attentionAt(data, model, cursorMs) {
  const attention = new Map();
  for (const event of data.events ?? []) {
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
  const center = model.groupById.get(directoryGroup(path)) ?? { x: target[0], y: target[1] };
  const originBase = parentPath
    ? positionAt(parentPath, first.ts_ms, model, memo)
    : [center.x, center.y];
  const offsetAngle = 2 * Math.PI * hashUnit(`${path}:birth`);
  const origin = [
    originBase[0] + 0.008 * Math.cos(offsetAngle),
    originBase[1] + 0.008 * Math.sin(offsetAngle),
  ];
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
        { name: "recent reads", type: "scatter", data: [] },
        { name: "recent writes", type: "scatter", data: [] },
        { name: "command-associated effects", type: "scatter", data: [] },
      ],
    };
  }

  const state = stateAt(data, model, cursorMs);
  const attention = attentionAt(data, model, cursorMs);
  const visitP95 = percentile95([...state.visits.values()]);
  const positionMemo = new Map();
  const contextReveal = smoothstep((cursorMs - model.firstEventMs) / CONTEXT_REVEAL_MS);
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
        opacity: 0.035 + 0.085 * contextReveal,
      },
    }));

  const points = [...observedPaths].map((path) => {
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
      symbolSize: (4.2 + 1.4 * depthFactor + 0.35 * visitFactor) * (0.55 + 0.45 * progress),
      itemStyle: {
        color: groupColor(group),
        opacity: baseline * (0.45 + 0.55 * progress),
        shadowBlur: focus ? 4 + 18 * focus.strength : 2,
        shadowColor: focus
          ? focus.commandAssociated ? "#c9a7ff" : focus.effect === "write" ? "#ff8f83" : "#ffffff"
          : groupColor(group),
      },
    };
  });

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
    if (!row.path) return "";
    if (row.context) return `${row.path}\nGit-tracked repository context\nnot yet observed by an Agent in this window`;
    const firstLabel = row.first.effect === "write" ? "first observed write" : "first discovered";
    const focus = row.focus
      ? `\nrecent: ${row.focus.vendor} ${row.focus.effect}${row.focus.commandAssociated ? " (command-associated)" : ""} · ${Math.round(row.focus.age / 60_000)} min ago`
      : "";
    return `${row.path}\n${row.group} cloud · depth ${row.depth}\n${row.visits} weighted Agent visits\n${firstLabel} via ${row.first.action}${row.parent ? ` near ${row.parent}` : ""}${focus}`;
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
        data: cloudLobes(context, 0.05 + 0.08 * contextReveal, true),
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
    ],
  };
}

export const nebulaDurations = {
  attentionMs: ATTENTION_MS,
  birthTravelMs: BIRTH_TRAVEL_MS,
  writeRippleMs: WRITE_RIPPLE_MS,
};
