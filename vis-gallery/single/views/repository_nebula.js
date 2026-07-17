import {
  forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY,
} from "d3-force";

const WIDTH = 1200;
const HEIGHT = 675;
const MAX_VISUAL_STEPS = 360;
const ATTENTION_STEPS = 24;
const ATTENTION_HALF_LIFE_STEPS = 6;
const TRANSITION_STEPS = 6;
const GOLDEN_ANGLE_DEGREES = 137.508;

const modelCache = new WeakMap();

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

function hash32(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function hashUnit(value) {
  return hash32(value) / 0xffffffff;
}

function randomLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function pathParts(path) {
  return String(path ?? "").split("/").filter(Boolean);
}

function directoryParts(path) {
  return pathParts(path).slice(0, -1);
}

function parentDirectory(path) {
  return directoryParts(path).join("/") || "(root)";
}

function topDirectory(path) {
  const parts = pathParts(path);
  return parts.length > 1 ? parts[0] : "(root)";
}

function commonDirectoryDepth(left, right) {
  const leftParts = directoryParts(left);
  const rightParts = directoryParts(right);
  let depth = 0;
  while (depth < leftParts.length && depth < rightParts.length && leftParts[depth] === rightParts[depth]) {
    depth += 1;
  }
  return depth;
}

function eventPaths(event) {
  return [...new Set(event.paths ?? (event.path ? [event.path] : []))].filter(Boolean);
}

function allAgentEvents(data) {
  const source = data.agent_events?.length ? data.agent_events : (data.events ?? []).map((event) => ({
    ...event,
    kind: event.kind ?? "tool",
    paths: eventPaths(event),
    read_paths: event.effect === "read" ? eventPaths(event) : [],
    write_paths: event.effect === "write" ? eventPaths(event) : [],
    durable_changes: [],
  }));
  return [...source].sort((left, right) => (
    Number(left.ts_ms) - Number(right.ts_ms) || String(left.id).localeCompare(String(right.id))
  ));
}

function inferredReadPaths(event) {
  if (Array.isArray(event.read_paths)) return event.read_paths;
  if (event.effect === "read" || /read|search|glob|grep/i.test(event.action ?? "")) {
    const writes = new Set(event.write_paths ?? []);
    return eventPaths(event).filter((path) => !writes.has(path));
  }
  return [];
}

function normalizeFileActions(data) {
  const actions = [];
  for (const event of allAgentEvents(data)) {
    if (event.kind && event.kind !== "tool") continue;
    const handled = new Set();
    const lifecycle = [...(event.durable_changes ?? [])].sort((left, right) => (
      String(left.path).localeCompare(String(right.path))
    ));
    for (const [index, change] of lifecycle.entries()) {
      const status = String(change.status ?? "")[0];
      if (!status || !change.path) continue;
      let type;
      if (status === "A" || status === "C") type = "create";
      if (status === "D") type = "delete";
      if (status === "R" && change.old_path) type = "rename";
      if (!type) continue;
      handled.add(change.path);
      if (change.old_path) handled.add(change.old_path);
      actions.push({
        id: `${event.id}:durable:${index}:${change.path}`,
        eventId: event.id,
        ts_ms: Number(event.ts_ms),
        session_id: event.session_id,
        vendor: event.vendor,
        type,
        path: change.path,
        oldPath: change.old_path,
        source: event.category === "shell" ? "bash+git" : "tool+git",
      });
    }

    const writePaths = new Set(event.write_paths ?? []);
    if (!writePaths.size && event.effect === "write") {
      for (const path of eventPaths(event)) writePaths.add(path);
    }
    let ordinal = 0;
    for (const path of [...writePaths].sort()) {
      if (handled.has(path)) continue;
      actions.push({
        id: `${event.id}:write:${ordinal++}:${path}`,
        eventId: event.id,
        ts_ms: Number(event.ts_ms),
        session_id: event.session_id,
        vendor: event.vendor,
        type: "write",
        path,
        source: event.category === "shell" ? "bash" : "tool",
      });
    }
    ordinal = 0;
    for (const path of [...new Set(inferredReadPaths(event))].sort()) {
      if (handled.has(path) || writePaths.has(path)) continue;
      actions.push({
        id: `${event.id}:read:${ordinal++}:${path}`,
        eventId: event.id,
        ts_ms: Number(event.ts_ms),
        session_id: event.session_id,
        vendor: event.vendor,
        type: "read",
        path,
        source: event.category === "shell" ? "bash" : "tool",
      });
    }
  }
  const priority = { rename: 0, delete: 1, create: 2, write: 3, read: 4 };
  return actions.filter((action) => action.path && Number.isFinite(action.ts_ms)).sort((left, right) => (
    left.ts_ms - right.ts_ms
    || left.eventId.localeCompare(right.eventId)
    || priority[left.type] - priority[right.type]
    || left.path.localeCompare(right.path)
  ));
}

export function gitScopedNebulaFiles(data) {
  const paths = new Set(normalizeFileActions(data).flatMap((action) => (
    action.oldPath ? [action.oldPath, action.path] : [action.path]
  )));
  return [...paths].sort().map((path) => ({ path, observed: true }));
}

function actionDurationMs(count) {
  return clamp(8_000 + 40 * count, 8_000, 30_000);
}

function buildBuckets(actions) {
  if (!actions.length) return [];
  const eventGroups = [];
  for (const action of actions) {
    const current = eventGroups.at(-1);
    if (current?.[0]?.eventId === action.eventId) current.push(action);
    else eventGroups.push([action]);
  }
  const count = Math.min(eventGroups.length, MAX_VISUAL_STEPS);
  const buckets = Array.from({ length: count }, () => []);
  eventGroups.forEach((group, index) => {
    const bucket = Math.min(count - 1, Math.floor(index * count / eventGroups.length));
    buckets[bucket].push(...group);
  });
  return buckets.filter((bucket) => bucket.length);
}

function srgbChannel(value) {
  const linear = clamp(value, 0, 1);
  const gamma = linear <= 0.0031308 ? 12.92 * linear : 1.055 * linear ** (1 / 2.4) - 0.055;
  return Math.round(255 * clamp(gamma, 0, 1));
}

function oklchRgb(lightness, chroma, hueDegrees) {
  const hue = hueDegrees * Math.PI / 180;
  const a = chroma * Math.cos(hue);
  const b = chroma * Math.sin(hue);
  const lRoot = lightness + 0.3963377774 * a + 0.2158037573 * b;
  const mRoot = lightness - 0.1055613458 * a - 0.0638541728 * b;
  const sRoot = lightness - 0.0894841775 * a - 1.291485548 * b;
  const l = lRoot ** 3;
  const m = mRoot ** 3;
  const s = sRoot ** 3;
  return [
    srgbChannel(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    srgbChannel(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    srgbChannel(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  ];
}

function rgbString(rgb, alpha = 1) {
  return alpha >= 1
    ? `rgb(${rgb.map(Math.round).join(" ")})`
    : `rgba(${rgb.map(Math.round).join(",")},${alpha})`;
}

function mixRgb(left, right, progress) {
  const unit = clamp(progress, 0, 1);
  return left.map((value, index) => value + (right[index] - value) * unit);
}

function buildPalette(actions, repository) {
  const tops = [...new Set(actions.flatMap((action) => (
    [topDirectory(action.path), ...(action.oldPath ? [topDirectory(action.oldPath)] : [])]
  )))].sort();
  const seedHue = hashUnit(repository) * 360;
  const baseHue = new Map(tops.map((top, rank) => [
    top, (seedHue + GOLDEN_ANGLE_DEGREES * rank) % 360,
  ]));
  return (path) => {
    const directories = directoryParts(path);
    const top = topDirectory(path);
    const depth = Math.max(0, directories.length - 1);
    const parent = directories.join("/") || "(root)";
    const hue = (baseHue.get(top) ?? seedHue) + (hashUnit(parent) * 2 - 1) * 8;
    const lightness = Math.min(0.84, 0.58 + 0.055 * depth);
    const chroma = Math.max(0.08, 0.17 - 0.015 * depth);
    return oklchRgb(lightness, chroma, hue);
  };
}

function addIndex(index, key, path) {
  if (!index.has(key)) index.set(key, []);
  const rows = index.get(key);
  if (!rows.includes(path)) rows.push(path);
}

function removeIndex(index, key, path) {
  const rows = index.get(key);
  if (!rows) return;
  const position = rows.indexOf(path);
  if (position >= 0) rows.splice(position, 1);
  if (!rows.length) index.delete(key);
}

function indexNode(state, node) {
  addIndex(state.parentIndex, parentDirectory(node.path), node.path);
  addIndex(state.topIndex, topDirectory(node.path), node.path);
  const directories = directoryParts(node.path);
  for (let depth = 1; depth <= directories.length; depth += 1) {
    addIndex(state.prefixIndex, directories.slice(0, depth).join("/"), node.path);
  }
}

function unindexNode(state, node) {
  removeIndex(state.parentIndex, parentDirectory(node.path), node.path);
  removeIndex(state.topIndex, topDirectory(node.path), node.path);
  const directories = directoryParts(node.path);
  for (let depth = 1; depth <= directories.length; depth += 1) {
    removeIndex(state.prefixIndex, directories.slice(0, depth).join("/"), node.path);
  }
}

function lastLivePath(paths, state, excluded) {
  return [...(paths ?? [])].reverse().find((path) => path !== excluded && state.nodes.has(path));
}

function birthParent(path, state) {
  const parent = lastLivePath(state.parentIndex.get(parentDirectory(path)), state, path);
  if (parent) return state.nodes.get(parent);
  const directories = directoryParts(path);
  for (let depth = directories.length - 1; depth >= 1; depth -= 1) {
    const candidate = lastLivePath(state.prefixIndex.get(directories.slice(0, depth).join("/")), state, path);
    if (candidate) return state.nodes.get(candidate);
  }
  const top = lastLivePath(state.topIndex.get(topDirectory(path)), state, path);
  return top ? state.nodes.get(top) : null;
}

function initialPosition(path, parent, state) {
  const angle = hashUnit(`${path}:birth`) * 2 * Math.PI;
  if (!state.nodes.size) return [WIDTH / 2, HEIGHT / 2];
  if (parent) {
    return [parent.x + 13 * Math.cos(angle), parent.y + 13 * Math.sin(angle)];
  }
  const rows = state.topIndex.get(topDirectory(path)) ?? [];
  const peers = rows.map((candidate) => state.nodes.get(candidate)).filter(Boolean);
  if (peers.length) {
    const x = peers.reduce((sum, node) => sum + node.x, 0) / peers.length;
    const y = peers.reduce((sum, node) => sum + node.y, 0) / peers.length;
    return [x + 18 * Math.cos(angle), y + 18 * Math.sin(angle)];
  }
  return [WIDTH / 2 + 36 * Math.cos(angle), HEIGHT / 2 + 36 * Math.sin(angle)];
}

function createNode(path, action, step, state, lifecycle = null) {
  const existing = state.nodes.get(path);
  if (existing) return existing;
  const parent = birthParent(path, state);
  const [x, y] = initialPosition(path, parent, state);
  const targetColor = state.colorForPath(path);
  const node = {
    path, x, y, vx: 0, vy: 0,
    visits: 0,
    birthStep: step,
    deleteStep: null,
    lastStep: step,
    focusType: action.type,
    firstAction: action.type,
    firstTs: action.ts_ms,
    source: action.source,
    lastSession: action.session_id,
    lastVendor: action.vendor,
    bornNear: parent?.path,
    colorFrom: parent ? currentColor(parent, step) : targetColor,
    colorTo: targetColor,
    colorStep: step,
    lifecycleType: lifecycle,
    lifecycleStep: lifecycle ? step : null,
  };
  state.nodes.set(path, node);
  indexNode(state, node);
  return node;
}

function currentColor(node, step) {
  return mixRgb(node.colorFrom, node.colorTo, (step - node.colorStep + 1) / TRANSITION_STEPS);
}

function applyAction(action, step, state) {
  if (action.type === "rename") {
    let node = action.oldPath ? state.nodes.get(action.oldPath) : null;
    if (node) {
      const oldColor = currentColor(node, step);
      unindexNode(state, node);
      state.nodes.delete(node.path);
      node.path = action.path;
      node.colorFrom = oldColor;
      node.colorTo = state.colorForPath(action.path);
      node.colorStep = step;
      node.deleteStep = null;
      state.nodes.set(node.path, node);
      indexNode(state, node);
    } else {
      node = createNode(action.path, action, step, state, "rename");
    }
    Object.assign(node, {
      visits: node.visits + 2,
      lastStep: step,
      focusType: "rename",
      lifecycleType: "rename",
      lifecycleStep: step,
      source: action.source,
      lastSession: action.session_id,
      lastVendor: action.vendor,
    });
    return;
  }

  const node = createNode(action.path, action, step, state, action.type === "create" ? "create" : null);
  node.lastStep = step;
  node.focusType = action.type;
  node.source = action.source;
  node.lastSession = action.session_id;
  node.lastVendor = action.vendor;
  node.visits += action.type === "read" ? 1 : 2;
  if (action.type === "create") {
    node.lifecycleType = "create";
    node.lifecycleStep = step;
  }
  if (action.type === "delete") {
    node.lifecycleType = "delete";
    node.lifecycleStep = step;
    node.deleteStep = step;
  }
}

function attention(node, step) {
  const age = step - node.lastStep;
  if (age < 0 || age > ATTENTION_STEPS || node.focusType === "delete") return 0;
  const gain = { read: 0.35, write: 0.75, create: 1, rename: 0.8 }[node.focusType] ?? 0;
  return gain * 2 ** (-age / ATTENTION_HALF_LIFE_STEPS);
}

function nodeRadius(node) {
  return clamp(3 + 0.9 * Math.log1p(node.visits), 3, 8);
}

function buildLinks(nodes, step) {
  const byParent = new Map();
  const byTop = new Map();
  for (const node of nodes) {
    addIndex(byParent, parentDirectory(node.path), node.path);
    addIndex(byTop, topDirectory(node.path), node.path);
  }
  const byPath = new Map(nodes.map((node) => [node.path, node]));
  const links = [];
  const linked = new Set();
  const add = (sourcePath, targetPath, distance, strength) => {
    if (!sourcePath || !targetPath || sourcePath === targetPath) return;
    const key = [sourcePath, targetPath].sort().join("\0");
    if (linked.has(key)) return;
    const source = byPath.get(sourcePath);
    const target = byPath.get(targetPath);
    if (!source || !target) return;
    const activity = 1 + 0.35 * attention(source, step) + 0.35 * attention(target, step);
    links.push({ source, target, distance, strength: strength * activity });
    linked.add(key);
  };
  for (const paths of byParent.values()) {
    const ordered = [...paths].sort();
    for (let index = 1; index < ordered.length; index += 1) {
      add(ordered[index - 1], ordered[index], 30, 0.34);
      if (index > 1) add(ordered[index - 2], ordered[index], 38, 0.18);
    }
  }
  for (const paths of byTop.values()) {
    const representatives = [...new Map(paths.sort().map((path) => [parentDirectory(path), path])).values()];
    for (let index = 1; index < representatives.length; index += 1) {
      const left = representatives[index - 1];
      const right = representatives[index];
      const depth = commonDirectoryDepth(left, right);
      add(left, right, depth > 0 ? 52 : 90, depth > 0 ? 0.14 : 0.07);
    }
  }
  return links;
}

function actionAlpha(actions) {
  if (actions.some((action) => ["create", "rename", "delete"].includes(action.type))) return 0.35;
  if (actions.some((action) => action.type === "write")) return 0.18;
  return 0.10;
}

function runForces(state, actions, step) {
  const nodes = [...state.nodes.values()];
  if (!nodes.length) return;
  const links = buildLinks(nodes, step);
  const simulation = forceSimulation(nodes)
    .stop()
    .randomSource(randomLcg(hash32(`${state.repository}:${step}`)))
    .velocityDecay(0.32)
    .alpha(actionAlpha(actions))
    .alphaDecay(0)
    .force("charge", forceManyBody().strength((node) => -7 - 0.8 * nodeRadius(node)))
    .force("collision", forceCollide((node) => nodeRadius(node) + 2).iterations(2))
    .force("x", forceX(WIDTH / 2).strength(0.026))
    .force("y", forceY(HEIGHT / 2).strength(0.036));
  if (links.length) {
    simulation.force("links", forceLink(links)
      .id((node) => node.path)
      .distance((link) => link.distance)
      .strength((link) => link.strength));
  }
  const ticks = nodes.length > 1_000 ? 1 : nodes.length > 500 ? 2 : nodes.length > 200 ? 4 : 8;
  simulation.tick(ticks);
  for (const node of nodes) {
    node.x = clamp(node.x, 18, WIDTH - 18);
    node.y = clamp(node.y, 18, HEIGHT - 18);
  }
}

function nodeOpacity(node, step) {
  const born = clamp((step - node.birthStep + 1) / TRANSITION_STEPS, 0, 1);
  if (node.deleteStep === null) return born;
  return born * (1 - clamp((step - node.deleteStep + 1) / TRANSITION_STEPS, 0, 1));
}

function summarizeActions(actions) {
  const counts = new Map();
  for (const action of actions) counts.set(action.type, (counts.get(action.type) ?? 0) + 1);
  const vendors = [...new Set(actions.map((action) => action.vendor))];
  if (actions.length === 1) {
    const action = actions[0];
    return `${action.vendor} · ${action.type} · ${action.oldPath ? `${action.oldPath} → ` : ""}${action.path}`;
  }
  const summary = ["read", "write", "create", "rename", "delete"]
    .filter((type) => counts.has(type))
    .map((type) => `${counts.get(type)} ${type}`)
    .join(" / ");
  return `${vendors.join("+")} · ${actions.length} actions · ${summary}`;
}

function snapshot(state, actions, step) {
  const nodes = [...state.nodes.values()].filter((node) => nodeOpacity(node, step) > 0.001).map((node) => ({
    path: node.path,
    x: node.x / WIDTH,
    y: node.y / HEIGHT,
    visits: node.visits,
    birthStep: node.birthStep,
    deleteStep: node.deleteStep,
    lastStep: node.lastStep,
    focusType: node.focusType,
    firstAction: node.firstAction,
    firstTs: node.firstTs,
    source: node.source,
    lastSession: node.lastSession,
    lastVendor: node.lastVendor,
    bornNear: node.bornNear,
    lifecycleType: node.lifecycleType,
    lifecycleStep: node.lifecycleStep,
    color: currentColor(node, step),
    opacity: nodeOpacity(node, step),
  }));
  return {
    step,
    ts_ms: actions.at(-1).ts_ms,
    actions,
    summary: summarizeActions(actions),
    nodes,
  };
}

function pruneDeleted(state, step) {
  for (const node of [...state.nodes.values()]) {
    if (node.deleteStep === null || step - node.deleteStep < TRANSITION_STEPS) continue;
    unindexNode(state, node);
    state.nodes.delete(node.path);
  }
}

function buildModel(data) {
  const actions = normalizeFileActions(data);
  const buckets = buildBuckets(actions);
  const repository = data.meta?.repository ?? "repository";
  const state = {
    repository,
    nodes: new Map(),
    parentIndex: new Map(),
    prefixIndex: new Map(),
    topIndex: new Map(),
    colorForPath: buildPalette(actions, `${repository}:${data.meta?.endpoint_revision ?? "HEAD"}`),
  };
  const snapshots = [];
  buckets.forEach((bucket, step) => {
    pruneDeleted(state, step);
    for (const action of bucket) applyAction(action, step, state);
    runForces(state, bucket, step);
    snapshots.push(snapshot(state, bucket, step));
  });
  return {
    actions,
    snapshots,
    firstMs: actions[0]?.ts_ms ?? Number.POSITIVE_INFINITY,
    lastMs: actions.at(-1)?.ts_ms ?? Number.NEGATIVE_INFINITY,
    durationMs: actionDurationMs(actions.length),
  };
}

function modelFor(data) {
  if (!modelCache.has(data)) modelCache.set(data, buildModel(data));
  return modelCache.get(data);
}

function snapshotAt(model, cursorMs) {
  let left = 0;
  let right = model.snapshots.length - 1;
  let found = null;
  while (left <= right) {
    const middle = Math.floor((left + right) / 2);
    const row = model.snapshots[middle];
    if (row.ts_ms <= cursorMs) {
      found = row;
      left = middle + 1;
    } else {
      right = middle - 1;
    }
  }
  return found;
}

export function nebulaVisualMoments(data) {
  const model = modelFor(data);
  const windowStart = Number(data.meta?.window_start_ms);
  const windowEnd = Number(data.meta?.window_end_ms);
  if (!model.snapshots.length) {
    return [windowStart, windowEnd].filter(Number.isFinite);
  }
  return [windowStart, ...model.snapshots.map((row) => row.ts_ms), windowEnd]
    .filter(Number.isFinite);
}

export function nebulaPlaybackDuration(data) {
  return modelFor(data).durationMs;
}

function emptyOption(h) {
  return {
    ...h.base(),
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    series: [
      { id: "files", name: "files", type: "scatter", data: [] },
      { id: "read-rings", name: "reads", type: "scatter", data: [] },
      { id: "write-ripples", name: "writes", type: "scatter", data: [] },
      { id: "lifecycle", name: "lifecycle", type: "scatter", data: [] },
    ],
  };
}

function ring(point, size, color, opacity, symbol = "circle") {
  return {
    ...point,
    symbol,
    symbolSize: size,
    itemStyle: {
      color: "transparent", borderColor: color, borderWidth: 1.25,
      opacity, shadowBlur: 9 * opacity, shadowColor: color,
    },
  };
}

export function repositoryNebula(data, cursorMs, h) {
  const model = modelFor(data);
  if (!Number.isFinite(model.firstMs) || cursorMs < model.firstMs) return emptyOption(h);
  const current = snapshotAt(model, cursorMs);
  if (!current) return emptyOption(h);
  const visitP95 = Math.max(1, ...current.nodes.map((node) => node.visits).sort((a, b) => a - b)
    .slice(Math.floor(current.nodes.length * 0.95), Math.floor(current.nodes.length * 0.95) + 1));
  const cameraScale = clamp(1.05 + 4 / Math.sqrt(Math.max(1, current.nodes.length)), 1.05, 2.3);

  const points = current.nodes.map((node) => {
    const age = current.step - node.lastStep;
    const strength = age <= ATTENTION_STEPS
      ? ({ read: 0.35, write: 0.75, create: 1, rename: 0.8 }[node.focusType] ?? 0)
        * 2 ** (-age / ATTENTION_HALF_LIFE_STEPS)
      : 0;
    const depth = directoryParts(node.path).length;
    const visitFactor = Math.log1p(node.visits) / Math.log1p(visitP95);
    const baseline = clamp(0.58 + 0.14 / (1 + 0.18 * depth) + 0.18 * visitFactor, 0.6, 0.9);
    const size = clamp(5.2 + 1.2 * Math.log1p(node.visits), 5.2, 12);
    return {
      id: node.path,
      value: [
        clamp(0.5 + (node.x - 0.5) * cameraScale, 0.02, 0.98),
        clamp(0.5 + (node.y - 0.5) * cameraScale, 0.02, 0.98),
        node.visits,
      ],
      path: node.path,
      directory: parentDirectory(node.path),
      visits: node.visits,
      depth,
      focusType: node.focusType,
      age,
      strength,
      firstAction: node.firstAction,
      firstTs: node.firstTs,
      source: node.source,
      lastSession: node.lastSession,
      lastVendor: node.lastVendor,
      bornNear: node.bornNear,
      lifecycleType: node.lifecycleType,
      lifecycleStep: node.lifecycleStep,
      symbolSize: size,
      itemStyle: {
        color: rgbString(node.color),
        opacity: baseline * node.opacity,
        shadowBlur: 6 + 20 * strength,
        shadowColor: strength > 0
          ? node.focusType === "read" ? "#ffffff" : "#ff9b78"
          : rgbString(node.color, 0.65),
      },
    };
  });

  const reads = points.filter((point) => point.focusType === "read" && point.age <= ATTENTION_STEPS)
    .map((point) => ring(
      point,
      point.symbolSize + 7 + 0.35 * point.age,
      "#f7ffff",
      0.12 + 0.72 * point.strength,
    ));

  const writes = points.filter((point) => point.focusType === "write" && point.age <= ATTENTION_STEPS)
    .flatMap((point) => [0, 0.34].map((offset) => {
      const progress = clamp(point.age / 14 + offset, 0, 1);
      return ring(point, point.symbolSize + 8 + 34 * progress, "#ff9678", (1 - progress) * 0.78);
    }));

  const lifecycle = points.filter((point) => (
    point.lifecycleStep !== null && current.step - point.lifecycleStep <= TRANSITION_STEPS
  )).map((point) => {
    const age = current.step - point.lifecycleStep;
    const progress = clamp(age / TRANSITION_STEPS, 0, 1);
    const color = point.lifecycleType === "create" ? "#75f0a9"
      : point.lifecycleType === "rename" ? "#63dfff" : "#ff647c";
    return ring(
      point,
      point.symbolSize + 12 + 28 * progress,
      color,
      (1 - progress) * 0.9,
      point.lifecycleType === "rename" ? "diamond" : "circle",
    );
  });

  const tooltip = ({ data: row = {} }) => row.path ? [
    row.path,
    `directory color: ${row.directory}`,
    `${row.visits} recorded file actions · depth ${row.depth}`,
    `first observed: ${row.firstAction} · ${new Date(row.firstTs).toISOString()}`,
    row.bornNear ? `entered near: ${row.bornNear}` : "entered at repository center",
    `latest: ${row.lastVendor} · ${row.source} · session ${row.lastSession}`,
  ].join("\n") : "";

  return {
    ...h.base(),
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    tooltip: { renderMode: "richText", formatter: tooltip },
    graphic: [{
      type: "group", left: 12, top: 12, silent: true, z: 100,
      children: [
        {
          type: "rect", shape: { x: 0, y: 0, width: 560, height: 48, r: 8 },
          style: { fill: "rgba(5,10,18,.78)", stroke: "rgba(120,155,190,.18)", lineWidth: 1 },
        },
        {
          type: "text", style: {
            x: 14, y: 12, text: current.summary,
            fill: "#dce8f7", font: "12px ui-monospace,monospace", width: 530, overflow: "truncate",
          },
        },
        {
          type: "text", style: {
            x: 14, y: 30,
            text: `${new Date(current.ts_ms).toISOString()} · step ${current.step + 1}/${model.snapshots.length} · ${points.length} files`,
            fill: "#74869c", font: "9px ui-monospace,monospace",
          },
        },
      ],
    }],
    series: [
      {
        id: "files", name: "files", type: "scatter", z: 3,
        animationDurationUpdate: 260, animationEasingUpdate: "cubicOut", data: points,
        emphasis: { scale: 1.7 },
      },
      {
        id: "read-rings", name: "reads", type: "scatter", silent: true, z: 5,
        animationDurationUpdate: 180, data: reads,
      },
      {
        id: "write-ripples", name: "writes", type: "scatter", silent: true, z: 6,
        animationDurationUpdate: 180, data: writes,
      },
      {
        id: "lifecycle", name: "create / rename / delete", type: "scatter", silent: true, z: 7,
        animationDurationUpdate: 180, data: lifecycle,
      },
    ],
  };
}

export const nebulaDurations = {
  attentionSteps: ATTENTION_STEPS,
  attentionHalfLifeSteps: ATTENTION_HALF_LIFE_STEPS,
  transitionSteps: TRANSITION_STEPS,
  maxVisualSteps: MAX_VISUAL_STEPS,
};
