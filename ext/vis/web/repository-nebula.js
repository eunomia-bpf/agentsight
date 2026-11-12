import {
  forceCollide, forceLink, forceManyBody, forceSimulation,
} from "d3-force";

const WIDTH = 1200;
const HEIGHT = 675;
const ATTENTION_HALF_LIVES = 4;
const TRANSITION_STEPS = 6;
const GOLDEN_ANGLE_DEGREES = 137.508;
const RESTING_REFERENCE_FILES = 480;
const RESTING_MAX_SIZE = 6;
const RESTING_MIN_SIZE = 0.85;
const FOCUSED_MAX_SIZE = 10.5;
const DIRECTORY_COUNT_EXPONENT = 0.4;
const DIRECTORY_PSEUDOCOUNT = 8;
const DIRECTORY_MAX_SHARE = 0.42;
const DIRECTORY_RANK_HYSTERESIS = 0.15;
const IMPORTANCE_MIN_HALF_LIFE = 240;
const IMPORTANCE_MAX_HALF_LIFE = 2_400;
const OPERATION_WEIGHTS = { read: 1, write: 2, create: 2.5, rename: 2.5, delete: 2 };
const SHELL_EVIDENCE = 0.42;
const SEARCH_EVIDENCE = 0.68;
const DIRECTORY_SCOPE_EVIDENCE = 0.10;

const modelCache = new WeakMap();

function clamp(value, minimum, maximum) { return Math.max(minimum, Math.min(maximum, value)); }

function compareText(left, right) { return String(left).localeCompare(String(right)); }

function hash32(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function hashUnit(value) { return hash32(value) / 0xffffffff; }

function randomLcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function pathParts(path) { return String(path ?? "").split("/").filter(Boolean); }

function directoryParts(path) { return pathParts(path).slice(0, -1); }

function parentDirectory(path) {
  const parts = pathParts(path);
  return parts.length > 1 ? parts.slice(0, -1).join("/") : (parts[0] ?? "(root)");
}

function rootArea(path) {
  const parts = pathParts(path);
  return parts[0] ?? "(root)";
}

function layoutDirectory(path) {
  const directories = directoryParts(path);
  return directories.slice(0, Math.min(2, directories.length)).join("/")
    || pathParts(path)[0] || "(root)";
}

function scopeDisplayPath(path) {
  const value = String(path ?? "").replace(/^\/+|\/+$/g, "");
  return !value || value === "." ? "_scope" : `${value}/_scope`;
}

function actionEvidence(event, item) {
  if (item.scope) return { scale: DIRECTORY_SCOPE_EVIDENCE, kind: "directory scope" };
  if (event.category === "shell" || /^(bash|shell)$/i.test(event.tool_name ?? "")) {
    return { scale: SHELL_EVIDENCE, kind: "shell-inferred" };
  }
  if (/^(grep|rg|glob|search)$/i.test(event.command_name || event.tool_name || "")) {
    return { scale: SEARCH_EVIDENCE, kind: "search tool" };
  }
  return { scale: 1, kind: "direct tool" };
}

function normalizeEvents(data) {
  const events = [...(data.events ?? [])].sort((left, right) => (
    Number(left.ts_ms) - Number(right.ts_ms) || compareText(String(left.id), String(right.id))
  ));
  const priority = { rename: 0, delete: 1, create: 2, write: 3, read: 4 };
  return events.filter((event) => Number.isFinite(Number(event.ts_ms))).map((event, eventStep) => {
    const actions = [];
    for (const [index, item] of (event.actions ?? []).entries()) {
      if (!item.path || item.access === "rename_from") continue;
      const oldPath = item.previous_path;
      const type = item.access === "rename" && oldPath ? "rename" : item.access;
      const evidence = actionEvidence(event, item);
      actions.push({
        id: `${event.id}:${type}:${index}:${item.path}`,
        eventId: event.id,
        ts_ms: Number(event.ts_ms),
        session_id: event.session_id,
        vendor: event.vendor,
        eventStep,
        type,
        path: item.path,
        oldPath,
        scope: Boolean(item.scope),
        evidenceScale: evidence.scale,
        evidenceKind: evidence.kind,
      });
    }
    actions.sort((left, right) => (
      priority[left.type] - priority[right.type] || compareText(left.path, right.path)
    ));
    return {
      id: String(event.id),
      ts_ms: Number(event.ts_ms),
      session_id: String(event.session_id ?? "session"),
      vendor: String(event.vendor ?? "agent"),
      tool_name: String(event.tool_name ?? "Tool"),
      category: String(event.category ?? "tool"),
      command_name: String(event.command_name ?? ""),
      status: String(event.status ?? "observed"),
      eventStep,
      actions,
    };
  });
}

function directoryDistribution(event, directoryFor = layoutDirectory) {
  const weights = new Map();
  for (const action of event.actions) {
    const path = action.scope ? scopeDisplayPath(action.path) : action.path;
    const directory = directoryFor(path);
    const weight = (OPERATION_WEIGHTS[action.type] ?? 1) * action.evidenceScale;
    weights.set(directory, (weights.get(directory) ?? 0) + weight);
  }
  const total = [...weights.values()].reduce((sum, value) => sum + value, 0);
  return total > 0
    ? new Map([...weights].map(([directory, weight]) => [directory, weight / total]))
    : new Map();
}

function attentionHalfLifeFor(events) {
  const active = new Map();
  const runs = [];
  const close = (session) => {
    const row = active.get(session);
    if (row) runs.push(row.length);
    active.delete(session);
  };
  for (const event of events) {
    if (!event.actions.length) {
      close(event.session_id);
      continue;
    }
    const selected = [...directoryDistribution(event)]
      .sort((left, right) => right[1] - left[1] || compareText(left[0], right[0]))[0][0];
    const previous = active.get(event.session_id);
    if (previous?.directory === selected) previous.length += 1;
    else {
      close(event.session_id);
      active.set(event.session_id, { directory: selected, length: 1 });
    }
  }
  for (const session of [...active.keys()]) close(session);
  if (!runs.length) return 1;
  runs.sort((left, right) => left - right);
  const middle = Math.floor(runs.length / 2);
  return Math.max(1, Math.round(runs.length % 2
    ? runs[middle]
    : (runs[middle - 1] + runs[middle]) / 2));
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
    [rootArea(action.path), ...(action.oldPath ? [rootArea(action.oldPath)] : [])]
  )))].sort();
  const seedHue = hashUnit(repository) * 360;
  const baseHue = new Map(tops.map((top, rank) => [
    top, (seedHue + GOLDEN_ANGLE_DEGREES * rank) % 360,
  ]));
  return (path) => {
    const directories = directoryParts(path);
    const top = rootArea(path);
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
  addIndex(state.topIndex, rootArea(node.path), node.path);
  const directories = directoryParts(node.path);
  for (let depth = 1; depth <= directories.length; depth += 1) {
    addIndex(state.prefixIndex, directories.slice(0, depth).join("/"), node.path);
  }
}

function unindexNode(state, node) {
  removeIndex(state.parentIndex, parentDirectory(node.path), node.path);
  removeIndex(state.topIndex, rootArea(node.path), node.path);
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
  const top = lastLivePath(state.topIndex.get(rootArea(path)), state, path);
  return top ? state.nodes.get(top) : null;
}

function initialPosition(path, parent, state) {
  const angle = hashUnit(`${path}:birth`) * 2 * Math.PI;
  if (!state.nodes.size) return [WIDTH / 2, HEIGHT / 2];
  if (parent) {
    return [parent.x + 13 * Math.cos(angle), parent.y + 13 * Math.sin(angle)];
  }
  const rows = state.topIndex.get(rootArea(path)) ?? [];
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
    sessions: new Set(),
    importanceRaw: 0,
    importanceStep: step,
    importance: 0,
    directoryShare: 1,
    directoryCellScale: 1,
    baseSize: RESTING_MAX_SIZE,
    birthStep: step,
    deleteStep: null,
    lastStep: step,
    focusType: action.type,
    focusScale: action.evidenceScale,
    scopeStep: null,
    scopeScale: 0,
    firstAction: action.type,
    firstTs: action.ts_ms,
    lastSession: action.session_id,
    lastVendor: action.vendor,
    bornNear: parent?.path,
    colorFrom: parent ? currentColor(parent, step) : targetColor,
    colorTo: targetColor,
    colorStep: step,
    lifecycleType: lifecycle,
    lifecycleStep: lifecycle ? step : null,
    lifecycleScale: action.evidenceScale,
  };
  state.nodes.set(path, node);
  indexNode(state, node);
  return node;
}

function currentColor(node, step) {
  return mixRgb(node.colorFrom, node.colorTo, (step - node.colorStep + 1) / TRANSITION_STEPS);
}

function decayedImportance(node, step, halfLife) {
  const age = Math.max(0, step - node.importanceStep);
  return node.importanceRaw * 2 ** (-age / halfLife);
}

function recordImportance(node, action, step, state) {
  const gains = { read: 1, write: 2.5, create: 4, rename: 4, delete: 4 };
  let gain = gains[action.type] ?? 1;
  const session = action.session_id;
  if (session && !node.sessions.has(session)) {
    node.sessions.add(session);
    gain += 1.5;
  }
  node.importanceRaw = decayedImportance(node, step, state.importanceHalfLife)
    + gain * action.evidenceScale;
  node.importanceStep = step;
}

function scopeMembers(path, state) {
  const prefix = String(path ?? "").replace(/^\/+|\/+$/g, "");
  if (!prefix || prefix === ".") return [...state.nodes.values()];
  return [...(state.prefixIndex.get(prefix) ?? [])]
    .map((candidate) => state.nodes.get(candidate))
    .filter(Boolean);
}

function applyScopeAction(action, step, state) {
  const source = action.type === "rename" && action.oldPath ? action.oldPath : action.path;
  const members = scopeMembers(source, state);
  if (action.type === "rename" && action.oldPath) {
    const moving = new Set(members);
    for (const node of members) unindexNode(state, node);
    for (const node of members) state.nodes.delete(node.path);
    for (const node of members) {
      const suffix = action.oldPath === "."
        ? node.path
        : node.path.slice(action.oldPath.length).replace(/^\//, "");
      const nextPath = [action.path.replace(/\/$/, ""), suffix].filter(Boolean).join("/");
      const replaced = state.nodes.get(nextPath);
      if (replaced && !moving.has(replaced)) {
        unindexNode(state, replaced);
        state.nodes.delete(replaced.path);
      }
      const oldColor = currentColor(node, step);
      node.path = nextPath;
      node.colorFrom = oldColor;
      node.colorTo = state.colorForPath(nextPath);
      node.colorStep = step;
      node.deleteStep = null;
      Object.assign(node, {
        lastStep: step, focusType: "rename", focusScale: action.evidenceScale,
        lifecycleType: "rename", lifecycleStep: step, lifecycleScale: action.evidenceScale,
        lastSession: action.session_id, lastVendor: action.vendor,
      });
      node.visits += 1;
      recordImportance(node, action, step, state);
      state.nodes.set(nextPath, node);
      indexNode(state, node);
    }
    return members.length;
  }
  if (action.type === "delete") {
    for (const node of members) {
      Object.assign(node, {
        lastStep: step, focusType: "delete", focusScale: action.evidenceScale,
        lifecycleType: "delete", lifecycleStep: step, lifecycleScale: action.evidenceScale,
        deleteStep: step, lastSession: action.session_id, lastVendor: action.vendor,
      });
      node.visits += 1;
      recordImportance(node, action, step, state);
    }
    return members.length;
  }
  const total = members.reduce((sum, node) => sum + Math.sqrt(0.05 + node.importance), 0);
  for (const node of members) {
    node.scopeStep = step;
    node.scopeScale = total > 0
      ? action.evidenceScale * Math.sqrt(0.05 + node.importance) / total
      : 0;
  }
  return members.length;
}

function applyAction(action, step, state) {
  if (action.scope) return applyScopeAction(action, step, state);
  if (action.type === "rename") {
    let node = action.oldPath ? state.nodes.get(action.oldPath) : null;
    if (node) {
      const replaced = state.nodes.get(action.path);
      if (replaced && replaced !== node) {
        unindexNode(state, replaced);
        state.nodes.delete(replaced.path);
      }
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
      focusScale: action.evidenceScale,
      lifecycleType: "rename",
      lifecycleStep: step,
      lifecycleScale: action.evidenceScale,
      lastSession: action.session_id,
      lastVendor: action.vendor,
    });
    recordImportance(node, action, step, state);
    return 0;
  }

  const node = createNode(action.path, action, step, state, action.type === "create" ? "create" : null);
  if (action.type !== "delete" && node.deleteStep !== null) {
    node.deleteStep = null;
    node.birthStep = step;
    node.lifecycleType = "create";
    node.lifecycleStep = step;
  }
  node.lastStep = step;
  node.focusType = action.type;
  node.focusScale = action.evidenceScale;
  node.lastSession = action.session_id;
  node.lastVendor = action.vendor;
  node.visits += action.type === "read" ? 1 : 2;
  recordImportance(node, action, step, state);
  if (action.type === "create") {
    node.lifecycleType = "create";
    node.lifecycleStep = step;
    node.lifecycleScale = action.evidenceScale;
  }
  if (action.type === "delete") {
    node.lifecycleType = "delete";
    node.lifecycleStep = step;
    node.lifecycleScale = action.evidenceScale;
    node.deleteStep = step;
  }
  return 0;
}

function restingNodeSize(count) {
  const density = Math.sqrt(RESTING_REFERENCE_FILES / Math.max(RESTING_REFERENCE_FILES, count));
  return clamp(RESTING_MAX_SIZE * density, RESTING_MIN_SIZE, RESTING_MAX_SIZE);
}

function baseNodeSize(node, count) {
  const local = clamp(
    restingNodeSize(count) * node.directoryCellScale,
    RESTING_MIN_SIZE,
    RESTING_MAX_SIZE,
  );
  return clamp(
    local * (0.62 + 0.38 * Math.sqrt(node.importance)),
    RESTING_MIN_SIZE,
    RESTING_MAX_SIZE,
  );
}

function focusedNodeSize(node, strength) {
  const resting = node.baseSize;
  return resting + (FOCUSED_MAX_SIZE - resting) * clamp(strength, 0, 1);
}

function nodeRadius(node) {
  return node.baseSize / 2;
}

function cappedDirectoryShares(rows) {
  if (rows.length === 1) return new Map([[rows[0].top, 1]]);
  const cap = Math.max(DIRECTORY_MAX_SHARE, 1 / rows.length + 0.08);
  const active = new Set(rows.map((row) => row.top));
  const byTop = new Map(rows.map((row) => [row.top, row]));
  const shares = new Map();
  let remaining = 1;
  while (active.size) {
    const weight = [...active].reduce((sum, top) => sum + byTop.get(top).weight, 0);
    const oversized = [...active].filter((top) => (
      remaining * byTop.get(top).weight / weight > cap
    ));
    if (!oversized.length) {
      for (const top of active) shares.set(top, remaining * byTop.get(top).weight / weight);
      break;
    }
    for (const top of oversized) {
      shares.set(top, cap);
      active.delete(top);
      remaining -= cap;
    }
  }
  return shares;
}

function directoryRadius(share, memberCount, maximum) {
  const shareRadius = 0.34 * Math.sqrt(share * WIDTH * HEIGHT / Math.PI);
  const contentRadius = 7 + 4 * Math.sqrt(memberCount);
  return clamp(Math.min(shareRadius, contentRadius), 8, Math.max(8, maximum));
}

function refreshImportanceAndDirectories(state, nodes, step) {
  for (const node of nodes) {
    node.importanceRaw = decayedImportance(node, step, state.importanceHalfLife);
    node.importanceStep = step;
  }
  const ranked = nodes.map((node) => node.importanceRaw).sort((left, right) => left - right);
  const p95 = Math.max(1, ranked[Math.floor((ranked.length - 1) * 0.95)] ?? 1);
  for (const node of nodes) {
    node.importance = clamp(Math.log1p(node.importanceRaw) / Math.log1p(p95), 0, 1);
  }

  const groups = new Map();
  for (const node of nodes) {
    const top = rootArea(node.path);
    if (!groups.has(top)) groups.set(top, []);
    groups.get(top).push(node);
  }
  const rows = [...groups].map(([top, members]) => {
    const meanImportance = members.reduce((sum, node) => sum + node.importance, 0) / members.length;
    return {
      top,
      members,
      meanImportance,
      weight: (members.length + DIRECTORY_PSEUDOCOUNT) ** DIRECTORY_COUNT_EXPONENT
        * (0.8 + 0.2 * meanImportance),
    };
  });
  const shares = cappedDirectoryShares(rows);
  const profiles = new Map();
  for (const row of rows) {
    const share = shares.get(row.top) ?? 1 / rows.length;
    const cellScale = clamp(Math.sqrt(share * nodes.length / row.members.length), 0.52, 1.8);
    const peakImportance = Math.max(...row.members.map((node) => node.importance));
    profiles.set(row.top, {
      share,
      cellScale,
      members: row.members,
      importance: 0.7 * row.meanImportance + 0.3 * peakImportance,
      radius: directoryRadius(share, row.members.length, 140),
    });
    for (const node of row.members) {
      node.directoryShare = share;
      node.directoryCellScale = cellScale;
      node.baseSize = baseNodeSize(node, nodes.length);
    }
  }
  return profiles;
}

function buildLinks(nodes, profiles) {
  const byParent = new Map();
  const byTop = new Map();
  for (const node of nodes) {
    addIndex(byParent, parentDirectory(node.path), node.path);
    addIndex(byTop, rootArea(node.path), node.path);
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
    links.push({ source, target, distance, strength });
    linked.add(key);
  };
  const addTree = (paths, distance, strength) => {
    const ordered = [...paths].sort();
    for (let index = 1; index < ordered.length; index += 1) {
      add(ordered[Math.floor((index - 1) / 4)], ordered[index], distance, strength);
    }
  };
  for (const paths of byParent.values()) {
    const scale = paths.reduce((sum, path) => sum + byPath.get(path).directoryCellScale, 0) / paths.length;
    addTree(paths, clamp((14 + 0.7 * Math.sqrt(paths.length)) * scale, 10, 38), 0.14);
  }
  for (const [top, paths] of byTop) {
    const representatives = [...new Map(paths.sort().map((path) => [parentDirectory(path), path])).values()];
    const treeDepth = Math.max(1, Math.ceil(Math.log(Math.max(1, representatives.length)) / Math.log(4)));
    const share = profiles.get(top)?.share ?? 1 / byTop.size;
    const targetRadius = 0.42 * Math.sqrt(share * WIDTH * HEIGHT);
    addTree(representatives, clamp(targetRadius / treeDepth, 24, 68), 0.04);
  }
  return links;
}

function recordDirectoryTransition(event, state) {
  if (!event.actions.length) {
    state.lastDirectories.delete(event.session_id);
    return;
  }
  const current = directoryDistribution(event, rootArea);
  const previous = state.lastDirectories.get(event.session_id);
  if (previous) {
    for (const [source, sourceWeight] of previous) {
      for (const [target, targetWeight] of current) {
        if (source === target) continue;
        const key = `${source}\0${target}`;
        state.directoryTransitions.set(
          key,
          (state.directoryTransitions.get(key) ?? 0) + sourceWeight * targetWeight,
        );
      }
    }
  }
  state.lastDirectories.set(event.session_id, current);
}

function updateDirectoryRanking(event, state, step) {
  const scoreAt = (top) => {
    const row = state.directoryActivity.get(top);
    if (!row) return 0;
    return row.score * 2 ** (-(step - row.step) / state.directoryRankHalfLife);
  };
  const gains = new Map();
  for (const action of event.actions) {
    const top = rootArea(action.scope ? scopeDisplayPath(action.path) : action.path);
    gains.set(top, (gains.get(top) ?? 0)
      + (OPERATION_WEIGHTS[action.type] ?? 1) * action.evidenceScale);
  }
  for (const [top, gain] of gains) {
    state.directoryActivity.set(top, { score: scoreAt(top) + gain, step });
    if (!state.directoryOrder.includes(top)) state.directoryOrder.push(top);
  }

  // One adjacent promotion per action keeps rank changes visually traceable.
  let swapAt = -1;
  let largestLead = 0;
  for (let index = 1; index < state.directoryOrder.length; index += 1) {
    const previous = scoreAt(state.directoryOrder[index - 1]);
    const challenger = scoreAt(state.directoryOrder[index]);
    const lead = challenger - previous * (1 + DIRECTORY_RANK_HYSTERESIS);
    if (lead > largestLead) {
      largestLead = lead;
      swapAt = index;
    }
  }
  if (swapAt > 0) {
    [state.directoryOrder[swapAt - 1], state.directoryOrder[swapAt]] =
      [state.directoryOrder[swapAt], state.directoryOrder[swapAt - 1]];
  }
}

function transitionAffinities(transitions) {
  const degree = new Map();
  for (const [key, weight] of transitions) {
    const [source, target] = key.split("\0");
    degree.set(source, (degree.get(source) ?? 0) + weight);
    degree.set(target, (degree.get(target) ?? 0) + weight);
  }
  const pairs = new Map();
  for (const [key, weight] of transitions) {
    const [source, target] = key.split("\0");
    const pair = [source, target].sort();
    const pairKey = pair.join("\0");
    if (!pairs.has(pairKey)) pairs.set(pairKey, { source: pair[0], target: pair[1], weight: 0 });
    pairs.get(pairKey).weight += weight;
  }
  return [...pairs.values()].map((row) => {
    const scale = Math.sqrt((degree.get(row.source) ?? 0) * (degree.get(row.target) ?? 0));
    return { ...row, strength: scale > 0 ? 1 - Math.exp(-row.weight / scale) : 0 };
  }).filter((row) => row.strength > 0);
}

function directoryForce(profiles, transitions) {
  const groups = [...profiles.entries()].map(([top, profile]) => ({ top, ...profile }));
  const byTop = new Map(groups.map((group) => [group.top, group]));
  const affinities = transitionAffinities(transitions);
  const membersByCluster = new Map();
  for (const group of groups) {
    for (const node of group.members) {
      const key = layoutDirectory(node.path);
      if (!membersByCluster.has(key)) membersByCluster.set(key, []);
      membersByCluster.get(key).push(node);
    }
  }
  const clusters = [...membersByCluster.entries()].map(([key, members]) => {
    const top = rootArea(members[0].path);
    const parent = byTop.get(top);
    const share = parent.share * members.length / parent.members.length;
    return {
      key,
      top,
      members,
      share,
      radius: directoryRadius(share, members.length, parent.radius * 0.85),
    };
  });
  const updateCenter = (group) => {
    group.x = group.members.reduce((sum, node) => sum + node.x, 0) / group.members.length;
    group.y = group.members.reduce((sum, node) => sum + node.y, 0) / group.members.length;
  };
  const translate = (group, x, y) => {
    for (const node of group.members) {
      node.vx += x;
      node.vy += y;
    }
  };
  const repel = (items, alpha, scaleFor, strengthFor) => {
    for (let left = 0; left < items.length; left += 1) {
      for (let right = left + 1; right < items.length; right += 1) {
        const a = items[left];
        const b = items[right];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distance = Math.hypot(dx, dy);
        if (distance < 0.001) {
          const angle = hashUnit(`${a.key ?? a.top}:${b.key ?? b.top}:separate`) * 2 * Math.PI;
          dx = Math.cos(angle);
          dy = Math.sin(angle);
          distance = 1;
        }
        const minimum = scaleFor(a, b) * (a.radius + b.radius) + 3;
        if (distance >= minimum) continue;
        const impulse = (minimum - distance) * alpha * strengthFor(a, b);
        const totalShare = a.share + b.share;
        translate(a, -dx / distance * impulse * b.share / totalShare, -dy / distance * impulse * b.share / totalShare);
        translate(b, dx / distance * impulse * a.share / totalShare, dy / distance * impulse * a.share / totalShare);
      }
    }
  };
  const force = (alpha) => {
    for (const group of groups) updateCenter(group);
    for (const cluster of clusters) updateCenter(cluster);
    repel(groups, alpha, () => 0.68, () => 0.04);
    repel(clusters, alpha,
      (a, b) => a.top === b.top ? 0.68 : 0.82,
      (a, b) => a.top === b.top ? 0.018 : 0.03);
    for (const group of groups) {
      const centerPull = alpha * (0.018 + 0.016 * group.importance);
      translate(group, (WIDTH / 2 - group.x) * centerPull, (HEIGHT / 2 - group.y) * centerPull);
    }
    for (const affinity of affinities) {
      const source = byTop.get(affinity.source);
      const target = byTop.get(affinity.target);
      if (!source || !target) continue;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const impulse = alpha * 0.006 * affinity.strength;
      translate(source, dx * impulse * target.share / (source.share + target.share),
        dy * impulse * target.share / (source.share + target.share));
      translate(target, -dx * impulse * source.share / (source.share + target.share),
        -dy * impulse * source.share / (source.share + target.share));
    }
    for (const cluster of clusters) {
      const parent = byTop.get(cluster.top);
      translate(cluster, (parent.x - cluster.x) * alpha * 0.014, (parent.y - cluster.y) * alpha * 0.014);
      for (const node of cluster.members) {
        const dx = cluster.x - node.x;
        const dy = cluster.y - node.y;
        const distance = Math.hypot(dx, dy);
        const normalizedDistance = distance / Math.max(1, cluster.radius);
        const localPull = alpha * (
          0.004 + 0.024 * node.importance + 0.012 * normalizedDistance * normalizedDistance
        );
        node.vx += dx * localPull;
        node.vy += dy * localPull;
      }
    }
  };
  force.initialize = () => {};
  return force;
}

function actionAlpha(actions) {
  if (actions.some((action) => ["create", "rename", "delete"].includes(action.type))) return 0.35;
  if (actions.some((action) => action.type === "write")) return 0.18;
  return 0.10;
}

function runForces(state, actions, step) {
  const nodes = [...state.nodes.values()];
  if (!nodes.length) return;
  const profiles = refreshImportanceAndDirectories(state, nodes, step);
  state.refreshedStep = step;
  if (nodes.length === 1) {
    Object.assign(nodes[0], { x: WIDTH / 2, y: HEIGHT / 2, vx: 0, vy: 0 });
    return;
  }
  const links = buildLinks(nodes, profiles);
  const densityScale = clamp(Math.sqrt(RESTING_REFERENCE_FILES / nodes.length), 0.24, 1);
  const simulation = forceSimulation(nodes)
    .stop()
    .randomSource(randomLcg(hash32(`${state.repository}:${step}`)))
    .velocityDecay(0.38)
    .alpha(actionAlpha(actions))
    .alphaDecay(0)
    .force("charge", forceManyBody().strength((node) => (
      (-1.3 - 0.65 * nodeRadius(node))
        * (0.55 + 0.75 * node.importance)
        * clamp(node.directoryCellScale, 0.65, 1.3)
        * densityScale
    )))
    .force("collision", forceCollide((node) => nodeRadius(node) + 0.8)
      .iterations(nodes.length > 1_000 ? 1 : 2))
    .force("directories", directoryForce(profiles, state.directoryTransitions));
  if (links.length) {
    simulation.force("links", forceLink(links)
      .id((node) => node.path)
      .distance((link) => link.distance)
      .strength((link) => link.strength));
  }
  const ticks = nodes.length > 1_000 ? 1 : nodes.length > 500 ? 2 : nodes.length > 200 ? 4 : 8;
  simulation.tick(ticks);
  for (const node of nodes) {
    const margin = Math.max(4, nodeRadius(node) + 1);
    if (node.x < margin) {
      node.x = margin;
      node.vx = Math.abs(node.vx) * 0.25;
    } else if (node.x > WIDTH - margin) {
      node.x = WIDTH - margin;
      node.vx = -Math.abs(node.vx) * 0.25;
    }
    if (node.y < margin) {
      node.y = margin;
      node.vy = Math.abs(node.vy) * 0.25;
    } else if (node.y > HEIGHT - margin) {
      node.y = HEIGHT - margin;
      node.vy = -Math.abs(node.vy) * 0.25;
    }
  }
}

function nodeOpacity(node, step) {
  const born = clamp((step - node.birthStep + 1) / TRANSITION_STEPS, 0, 1);
  if (node.deleteStep === null) return born;
  return born * (1 - clamp((step - node.deleteStep + 1) / TRANSITION_STEPS, 0, 1));
}

function summarizeEvent(event) {
  const { actions } = event;
  const tool = event.command_name || event.tool_name || event.category;
  if (!actions.length) return `${event.vendor} · ${tool} · ${event.status} · no repository file action`;
  const counts = new Map();
  for (const action of actions) counts.set(action.type, (counts.get(action.type) ?? 0) + 1);
  const vendors = [...new Set(actions.map((action) => action.vendor))];
  if (actions.length === 1) {
    const action = actions[0];
    return `${action.vendor} · ${tool} · ${action.type}${action.scope ? " scope" : ""} · ${action.oldPath ? `${action.oldPath} → ` : ""}${action.path}`;
  }
  const summary = ["read", "write", "create", "rename", "delete"]
    .filter((type) => counts.has(type))
    .map((type) => `${counts.get(type)} ${type}`)
    .join(" / ");
  return `${vendors.join("+")} · ${actions.length} actions · ${summary}`;
}

function summarizeEvidence(event, scopeCount) {
  const tool = event.command_name || event.tool_name || event.category;
  const kinds = [...new Map(event.actions.map((action) => [
    action.evidenceKind, action.evidenceScale,
  ])).entries()];
  if (!kinds.length) return `${tool} · no repository file effect`;
  const evidence = kinds.map(([kind, scale]) => `${kind} ${scale.toFixed(2)}×`).join(" + ");
  const scope = scopeCount ? ` · ${scopeCount} files in scope` : "";
  return `${tool} · ${evidence}${scope}`;
}

function updateFocus(state, event) {
  if (!event.actions.length) {
    return state.focus ? { ...state.focus, active: false } : null;
  }
  const points = event.actions.flatMap((action) => {
    const nodes = action.scope
      ? scopeMembers(action.path, state)
      : [state.nodes.get(action.path)].filter(Boolean);
    const mass = (OPERATION_WEIGHTS[action.type] ?? 1) * action.evidenceScale;
    const total = nodes.reduce((sum, node) => sum + Math.sqrt(0.05 + node.importance), 0);
    return nodes.map((node) => ({
      node,
      weight: total > 0 ? mass * Math.sqrt(0.05 + node.importance) / total : 0,
      scale: action.evidenceScale,
    }));
  }).filter((row) => row.node && row.weight > 0);
  if (!points.length) return state.focus ? { ...state.focus, active: false } : null;
  const total = points.reduce((sum, row) => sum + row.weight, 0);
  const x = points.reduce((sum, row) => sum + row.weight * row.node.x, 0) / total;
  const y = points.reduce((sum, row) => sum + row.weight * row.node.y, 0) / total;
  const scale = Math.max(...points.map((row) => row.scale));
  const previous = state.focus?.session === event.session_id ? state.focus : null;
  const blend = 0.7 * scale;
  state.focus = {
    x: previous ? (1 - blend) * previous.x + blend * x : x,
    y: previous ? (1 - blend) * previous.y + blend * y : y,
    lastStep: event.eventStep,
    session: event.session_id,
    vendor: event.vendor,
    scale,
  };
  return { ...state.focus, active: true };
}

function snapshot(state, event) {
  const actionStep = event.eventStep;
  const nodes = [...state.nodes.values()].filter((node) => nodeOpacity(node, actionStep) > 0.001).map((node) => ({
    path: node.path,
    x: node.x / WIDTH,
    y: node.y / HEIGHT,
    visits: node.visits,
    sessionCount: node.sessions.size,
    importance: node.importance,
    directoryShare: node.directoryShare,
    baseSize: node.baseSize,
    birthStep: node.birthStep,
    deleteStep: node.deleteStep,
    lastStep: node.lastStep,
    focusType: node.focusType,
    focusScale: node.focusScale,
    scopeStep: node.scopeStep,
    scopeScale: node.scopeScale,
    firstAction: node.firstAction,
    firstTs: node.firstTs,
    lastSession: node.lastSession,
    lastVendor: node.lastVendor,
    bornNear: node.bornNear,
    lifecycleType: node.lifecycleType,
    lifecycleStep: node.lifecycleStep,
    lifecycleScale: node.lifecycleScale,
    color: currentColor(node, actionStep),
    opacity: nodeOpacity(node, actionStep),
  }));
  return {
    step: actionStep,
    actionStep,
    ts_ms: event.ts_ms,
    actions: event.actions,
    summary: summarizeEvent(event),
    evidence: summarizeEvidence(event, state.scopeCount),
    scopeCount: state.scopeCount,
    focus: state.visibleFocus,
    directoryOrder: [...state.directoryOrder],
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
  const events = normalizeEvents(data);
  const actions = events.flatMap((event) => event.actions);
  const eventStepCount = events.length;
  const attentionHalfLife = attentionHalfLifeFor(events);
  const repository = data.meta?.repository ?? "repository";
  const model = {
    repository,
    events,
    actions,
    importanceHalfLife: clamp(
      Math.round(eventStepCount * 0.08),
      IMPORTANCE_MIN_HALF_LIFE,
      IMPORTANCE_MAX_HALF_LIFE,
    ),
    colorForPath: buildPalette(actions, repository),
    topOrder: [...new Set(actions.flatMap((action) => (
      [rootArea(action.path), ...(action.oldPath ? [rootArea(action.oldPath)] : [])]
    )))].sort(compareText),
    attentionHalfLife,
    attentionSteps: attentionHalfLife * ATTENTION_HALF_LIVES,
    firstMs: events[0]?.ts_ms ?? Number.POSITIVE_INFINITY,
    lastMs: events.at(-1)?.ts_ms ?? Number.NEGATIVE_INFINITY,
  };
  resetModel(model);
  return model;
}

function resetModel(model) {
  model.state = {
    repository: model.repository,
    nodes: new Map(),
    parentIndex: new Map(),
    prefixIndex: new Map(),
    topIndex: new Map(),
    importanceHalfLife: model.importanceHalfLife,
    colorForPath: model.colorForPath,
    directoryTransitions: new Map(),
    lastDirectories: new Map(),
    directoryActivity: new Map(),
    directoryOrder: [],
    directoryRankHalfLife: model.importanceHalfLife,
    focus: null,
    visibleFocus: null,
    currentSession: null,
    pendingLayoutWeight: 0,
    scopeCount: 0,
    refreshedStep: -1,
  };
  model.currentStep = -1;
  model.current = null;
}

function advanceTo(model, requestedStep) {
  if (!model.events.length) return null;
  const target = clamp(Math.floor(requestedStep), 0, model.events.length - 1);
  if (target < model.currentStep) resetModel(model);
  for (let step = model.currentStep + 1; step <= target; step += 1) {
    const event = model.events[step];
    const { state } = model;
    if (state.currentSession !== event.session_id) {
      for (const node of state.nodes.values()) node.focusType = null;
      state.focus = null;
      state.currentSession = event.session_id;
    }
    pruneDeleted(state, step);
    recordDirectoryTransition(event, state);
    state.scopeCount = 0;
    for (const action of event.actions) state.scopeCount += applyAction(action, step, state);
    updateDirectoryRanking(event, state, step);
    state.pendingLayoutWeight += event.actions.reduce(
      (sum, action) => sum + (OPERATION_WEIGHTS[action.type] ?? 1) * action.evidenceScale, 0,
    );
    const structural = event.actions.some((action) => (
      action.type === "create" || action.type === "rename" || action.type === "delete"
    ));
    const threshold = Math.max(1, Math.sqrt(state.nodes.size));
    if (event.actions.length && (
      structural || state.pendingLayoutWeight >= threshold || step === model.events.length - 1
    )) {
      runForces(state, event.actions, step);
      state.pendingLayoutWeight = 0;
    }
    state.visibleFocus = updateFocus(state, event);
    model.currentStep = step;
  }
  if (model.state.nodes.size && model.state.refreshedStep !== target) {
    refreshImportanceAndDirectories(model.state, [...model.state.nodes.values()], target);
    model.state.refreshedStep = target;
  }
  model.current = snapshot(model.state, model.events[target]);
  return model.current;
}

function modelFor(data) {
  if (!modelCache.has(data)) modelCache.set(data, buildModel(data));
  return modelCache.get(data);
}

function snapshotAt(model, cursorMs) {
  let left = 0;
  let right = model.events.length - 1;
  let found = -1;
  while (left <= right) {
    const middle = Math.floor((left + right) / 2);
    const row = model.events[middle];
    if (row.ts_ms <= cursorMs) {
      found = middle;
      left = middle + 1;
    } else {
      right = middle - 1;
    }
  }
  return found >= 0 ? advanceTo(model, found) : null;
}

export function nebulaVisualMoments(data) {
  const model = modelFor(data);
  const windowStart = Number(data.meta?.window_start_ms);
  const windowEnd = Number(data.meta?.window_end_ms);
  if (!model.events.length) {
    return [windowStart, windowEnd].filter(Number.isFinite);
  }
  return [windowStart, ...model.events.map((row) => row.ts_ms), windowEnd]
    .filter(Number.isFinite);
}

function emptyOption(h) {
  return {
    ...h.base(),
    grid: { left: 8, right: 8, top: 8, bottom: 8 },
    xAxis: { type: "value", min: 0, max: 1, show: false },
    yAxis: { type: "value", min: 0, max: 1, show: false },
    series: [
      { id: "files", name: "files", type: "scatter", data: [] },
      { id: "scope-rings", name: "directory scope", type: "scatter", data: [] },
      { id: "read-rings", name: "reads", type: "scatter", data: [] },
      { id: "write-ripples", name: "writes", type: "scatter", data: [] },
      { id: "lifecycle", name: "lifecycle", type: "scatter", data: [] },
      { id: "trajectory-focus", name: "agent focus", type: "scatter", data: [] },
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

function readAttention(points) {
  const active = points.filter((point) => (
    point.focusType === "read" && point.strength > 0
  ));
  return active.sort((a, b) => b.strength - a.strength).slice(0, 4)
    .map((point) => ring(
      point,
      point.symbolSize + 6,
      "#f7ffff",
      0.12 + 0.58 * point.strength,
    ));
}

function scopeAttention(points) {
  return points.filter((point) => point.scopeStrength > 0).map((point) => ring(
    point,
    point.symbolSize + 3,
    "#b7cce2",
    0.025 + 0.65 * point.scopeStrength,
  ));
}

function directoryLegend(points, current, model) {
  const counts = new Map();
  for (const point of points) {
    const top = rootArea(point.path);
    counts.set(top, (counts.get(top) ?? 0) + 1);
  }
  const active = new Set(current.actions.map((action) => (
    rootArea(action.scope ? scopeDisplayPath(action.path) : action.path)
  )));
  const visible = [...new Set([...current.directoryOrder, ...model.topOrder])]
    .filter((top) => top !== "(root)" && counts.has(top));
  const shown = visible.slice(0, 8);
  const rows = shown.map((top) => ({
    top,
    label: top,
    count: counts.get(top),
    active: active.has(top),
    color: rgbString(model.colorForPath(`${top}/_legend`)),
  }));
  const more = Math.max(0, visible.length - rows.length);
  const height = 54 + 20 * rows.length + (more ? 16 : 0);
  const children = [
    {
      type: "rect", shape: { x: 0, y: 0, width: 236, height, r: 8 },
      style: { fill: "rgba(5,10,18,.78)", stroke: "rgba(120,155,190,.18)", lineWidth: 1 },
    },
    {
      type: "text", style: {
        x: 12, y: 11, text: "REPOSITORY AREAS", fill: "#91a6bd",
        font: "11px ui-monospace,monospace",
      },
    },
  ];
  rows.forEach((row, index) => {
    const y = 31 + 20 * index;
    children.push({
      type: "circle", shape: { cx: 15, cy: y + 4, r: row.active ? 5 : 4 },
      style: {
        fill: row.color, stroke: row.active ? "#ffffff" : "transparent",
        lineWidth: row.active ? 1.3 : 0, shadowBlur: row.active ? 8 : 0, shadowColor: row.color,
      },
    }, {
      type: "text", style: {
        x: 28, y, text: row.label, width: 154, overflow: "truncate",
        fill: row.active ? "#f4f8ff" : "#b4c2d2", font: "11px ui-monospace,monospace",
      },
    }, {
      type: "text", style: {
        x: 222, y, text: String(row.count), textAlign: "right",
        fill: "#71849a", font: "10px ui-monospace,monospace",
      },
    });
  });
  if (more) children.push({
    type: "text", style: {
      x: 12, y: 31 + 20 * rows.length, text: `+ ${more} more`,
      fill: "#607287", font: "10px ui-monospace,monospace",
    },
  });
  children.push({
    type: "text", style: {
      x: 12, y: height - 16, text: "color = path area · glow = attention",
      fill: "#607287", font: "9px ui-monospace,monospace",
    },
  });
  return { type: "group", right: 12, top: 12, silent: true, z: 100, children };
}

export function repositoryNebula(data, cursorMs, h) {
  const model = modelFor(data);
  const layoutStep = Number(data.meta?.render_layout_step);
  const hasLayoutStep = Number.isInteger(layoutStep);
  if (!Number.isFinite(model.firstMs) || (!hasLayoutStep && cursorMs < model.firstMs)) {
    return emptyOption(h);
  }
  const current = hasLayoutStep
    ? advanceTo(model, clamp(layoutStep, 0, model.events.length - 1))
    : snapshotAt(model, cursorMs);
  if (!current) return emptyOption(h);
  const cameraScale = clamp(0.92 + 3 / Math.sqrt(Math.max(1, current.nodes.length)), 0.92, 1.8);

  const points = current.nodes.map((node) => {
    const age = current.actionStep - node.lastStep;
    const strength = age <= model.attentionSteps
      ? ({ read: 0.35, write: 0.75, create: 1, rename: 0.8 }[node.focusType] ?? 0)
        * (node.focusScale ?? 1)
        * 2 ** (-age / model.attentionHalfLife)
      : 0;
    const scopeAge = node.scopeStep === null ? Number.POSITIVE_INFINITY
      : current.actionStep - node.scopeStep;
    const scopeStrength = scopeAge <= model.attentionSteps
      ? (node.scopeScale ?? 0) * 2 ** (-scopeAge / model.attentionHalfLife)
      : 0;
    const depth = directoryParts(node.path).length;
    const baseline = clamp(
      0.22 + 0.58 * Math.sqrt(node.importance) + 0.08 / (1 + 0.18 * depth),
      0.24,
      0.9,
    );
    const size = focusedNodeSize(node, strength);
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
      sessionCount: node.sessionCount,
      importance: node.importance,
      directoryShare: node.directoryShare,
      baseSize: node.baseSize,
      depth,
      focusType: node.focusType,
      age,
      strength,
      scopeAge,
      scopeStrength,
      firstAction: node.firstAction,
      firstTs: node.firstTs,
      lastSession: node.lastSession,
      lastVendor: node.lastVendor,
      bornNear: node.bornNear,
      lifecycleType: node.lifecycleType,
      lifecycleStep: node.lifecycleStep,
      lifecycleScale: node.lifecycleScale,
      symbolSize: size,
      itemStyle: {
        color: rgbString(node.color),
        opacity: baseline * node.opacity,
        shadowBlur: 1 + 4 * node.importance + 20 * strength,
        shadowColor: strength > 0
          ? node.focusType === "read" ? "#ffffff" : "#ff9b78"
          : rgbString(node.color, 0.65),
      },
    };
  });

  const scopes = scopeAttention(points);
  const reads = readAttention(points);

  const writes = points.filter((point) => point.focusType === "write" && point.age <= model.attentionSteps)
    .flatMap((point) => [0, 0.34].map((offset) => {
      const progress = clamp(point.age / Math.max(1, model.attentionSteps) + offset, 0, 1);
      return ring(
        point,
        point.symbolSize + 8 + 34 * progress,
        "#ff9678",
        (1 - progress) * 0.78 * clamp(point.strength / 0.75, 0, 1),
      );
    }));

  const focus = current.focus ? (() => {
    const age = current.actionStep - current.focus.lastStep;
    const strength = age <= model.attentionSteps
      ? (current.focus.scale ?? 1) * 2 ** (-age / model.attentionHalfLife)
      : 0;
    if (strength <= 0) return [];
    const x = current.focus.x / WIDTH;
    const y = current.focus.y / HEIGHT;
    return [ring({
      value: [
        clamp(0.5 + (x - 0.5) * cameraScale, 0.02, 0.98),
        clamp(0.5 + (y - 0.5) * cameraScale, 0.02, 0.98),
      ],
    }, 14 + 10 * strength, "#dcecff", 0.08 + 0.24 * strength)];
  })() : [];

  const lifecycle = points.filter((point) => (
    point.lifecycleStep !== null && current.actionStep - point.lifecycleStep <= TRANSITION_STEPS
  )).map((point) => {
    const age = current.actionStep - point.lifecycleStep;
    const progress = clamp(age / TRANSITION_STEPS, 0, 1);
    const color = point.lifecycleType === "create" ? "#75f0a9"
      : point.lifecycleType === "rename" ? "#63dfff" : "#ff647c";
    return ring(
      point,
      point.symbolSize + 12 + 28 * progress,
      color,
      (1 - progress) * 0.9 * (point.lifecycleScale ?? 1),
      point.lifecycleType === "rename" ? "diamond" : "circle",
    );
  });

  const tooltip = ({ data: row = {} }) => row.path ? [
    row.path,
    `path area: ${row.directory}`,
    `${row.visits} recorded file actions · ${row.sessionCount} sessions · depth ${row.depth}`,
    `decayed importance: ${Math.round(100 * row.importance)}% · directory share: ${Math.round(100 * row.directoryShare)}%`,
    `first observed: ${row.firstAction} · ${new Date(row.firstTs).toISOString()}`,
    row.bornNear ? `entered near: ${row.bornNear}` : "entered at repository center",
    `latest: ${row.lastVendor} · agent-session · session ${row.lastSession}`,
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
          type: "rect", shape: { x: 0, y: 0, width: 560, height: 64, r: 8 },
          style: { fill: "rgba(5,10,18,.78)", stroke: "rgba(120,155,190,.18)", lineWidth: 1 },
        },
        {
          type: "text", style: {
            x: 14, y: 12, text: current.summary,
            fill: "#dce8f7", font: "14px ui-monospace,monospace", width: 530, overflow: "truncate",
          },
        },
        {
          type: "text", style: {
            x: 14, y: 30, text: current.evidence,
            fill: "#91a6bd", font: "11px ui-monospace,monospace", width: 530, overflow: "truncate",
          },
        },
        {
          type: "text", style: {
            x: 14, y: 47,
            text: `${new Date(current.ts_ms).toISOString()} · step ${current.step + 1}/${model.events.length} · ${points.length} files`,
            fill: "#74869c", font: "10px ui-monospace,monospace",
          },
        },
      ],
    }, directoryLegend(points, current, model)],
    series: [
      {
        id: "files", name: "files", type: "scatter", z: 3,
        animationDurationUpdate: 260, animationEasingUpdate: "cubicOut", data: points,
        emphasis: { scale: 1.7 },
      },
      {
        id: "scope-rings", name: "directory scope", type: "scatter", silent: true, z: 4,
        animationDurationUpdate: 180, data: scopes,
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
      {
        id: "trajectory-focus", name: "agent focus", type: "scatter", silent: true, z: 4,
        animationDurationUpdate: 180, data: focus,
      },
    ],
  };
}
