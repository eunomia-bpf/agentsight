#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { requireView, views } from "./registry.js";

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(here, "..");
const repositoryRoot = resolve(packageRoot, "..");
const runtimePath = join(here, "dist", "runtime.iife.js");

function usage() {
  return `Generate one self-contained AgentSight evolution visualization per file.

Usage:
  agentsight-vis --repo PATH --since TIME [--until TIME] --view ID --output FILE
  agentsight-vis --list-views

Options:
  --repo PATH       Repository whose native sessions and Git history are inspected
  --since TIME      RFC3339, YYYY-MM-DD, relative duration, or repo (root commit)
  --until TIME      RFC3339, YYYY-MM-DD, or now (default: now)
  --head REV        Frozen Git revision (default: HEAD)
  --global          Include Tool operations from every local Agent session
                    when they target PATH, even if the session belongs elsewhere
  --view ID         One of the registered single-artifact views
  --output FILE     .html, .svg, .png, .gif, or .mp4
  --at TIME         Snapshot cursor (default: end of window)
  --frames N        Animation frames (default: 60)
  --fps N           Animation frame rate (default: 10)
  --width N         Chart width (default: 1400)
  --height N        Chart height (default: 760)
  --list-views      Print all supported view IDs
`;
}

export function parseArgs(values) {
  const options = { until: "now", head: "HEAD", frames: 60, fps: 10, width: 1400, height: 760 };
  for (let index = 0; index < values.length; index += 1) {
    const flag = values[index];
    if (flag === "--help" || flag === "-h") return { help: true };
    if (flag === "--list-views") { options.listViews = true; continue; }
    if (flag === "--global") { options.global = true; continue; }
    const value = values[++index];
    if (value === undefined) throw new Error(`missing value for ${flag}`);
    const key = {
      "--repo": "repo", "--since": "since", "--until": "until", "--head": "head",
      "--view": "view", "--output": "output", "--at": "at",
      "--frames": "frames", "--fps": "fps", "--width": "width", "--height": "height",
    }[flag];
    if (!key) throw new Error(`unknown option ${flag}`);
    options[key] = ["frames", "fps", "width", "height"].includes(key) ? Number(value) : value;
  }
  return options;
}

export function parseTime(value, fallback, anchor = Date.now()) {
  if (!value) return fallback;
  if (value === "now") return Date.now();
  if (value === "HEAD" || value === "end") return fallback;
  const relative = /^(\d+(?:\.\d+)?)([hdw])$/.exec(value);
  if (relative) {
    const scale = { h: 3_600_000, d: 86_400_000, w: 604_800_000 }[relative[2]];
    return anchor - Number(relative[1]) * scale;
  }
  const parsed = Date.parse(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00Z` : value);
  if (!Number.isFinite(parsed)) throw new Error(`invalid time ${value}`);
  return parsed;
}

export function repositoryStartMs(repo, head = "HEAD") {
  const roots = run("git", ["rev-list", "--first-parent", "--max-parents=0", head], repo)
    .trim().split(/\s+/).filter(Boolean);
  if (!roots.length) throw new Error(`cannot find a root commit for ${repo}`);
  let earliest = Number.POSITIVE_INFINITY;
  for (const root of roots) {
    const seconds = Number(run("git", ["show", "-s", "--format=%ct", root], repo).trim());
    if (!Number.isFinite(seconds)) throw new Error(`invalid root commit timestamp for ${root}`);
    earliest = Math.min(earliest, seconds * 1_000);
  }
  return earliest;
}

function iso(value) {
  return new Date(value).toISOString();
}

function run(command, args, cwd = repositoryRoot, input) {
  const result = spawnSync(command, args, {
    cwd, input, encoding: "utf8", maxBuffer: 256 * 1024 * 1024,
    stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"],
  });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed\n${result.stderr || result.stdout}`);
  }
  return result.stdout;
}

export async function buildEvolutionData(options, spec = null) {
  const repo = resolve(options.repo);
  const untilMs = parseTime(options.until, Date.now());
  const sinceMs = options.since === "repo"
    ? repositoryStartMs(repo, options.head)
    : parseTime(options.since, untilMs - 7 * 86_400_000, untilMs);
  if (sinceMs >= untilMs) throw new Error("--since must be before --until");
  const exporterArgs = [
    "--repo", repo, "--head", options.head, "--since", iso(sinceMs),
    "--until", iso(untilMs), "--output", "-",
  ];
  const leanNebula = spec?.id === "workspace-constellation";
  if (leanNebula) exporterArgs.push("--git-lifetimes-only");
  if (options.global) exporterArgs.push("--global");
  const sessionData = run("cargo", [
    "run", "--quiet", "--manifest-path", join(repositoryRoot, "agent-session", "Cargo.toml"),
    "--bin", "agent-session-export", "--", ...exporterArgs,
  ]);
  const projectArgs = [join(here, "project.py"), "--repo", repo];
  if (leanNebula) projectArgs.push("--lean-nebula");
  return JSON.parse(run("python3", projectArgs, repositoryRoot, sessionData));
}

export function projectForView(data, spec) {
  const keys = new Set(["meta", ...(spec.requirements ?? [])]);
  const projected = Object.fromEntries(Object.entries(data).filter(([key]) => keys.has(key)));
  projected.meta = Object.fromEntries([
    "repository", "endpoint_revision", "window_start_ms", "window_end_ms", "session_scope",
  ].map((key) => [key, data.meta[key]]));
  if (spec.id === "repository-treemap") {
    const observedPaths = new Set((projected.events ?? []).map((event) => event.path));
    projected.files = (projected.files ?? []).filter((file) => observedPaths.has(file.path));
  }
  if (spec.id === "workspace-constellation") {
    const observedPaths = new Set((projected.agent_events ?? []).flatMap((event) => event.paths ?? []));
    const durableLifetimeIds = new Set((projected.agent_events ?? []).flatMap((event) => (
      event.durable_changes ?? []
    )).map((change) => change.lifetime_id));
    projected.files = (projected.files ?? []).filter((file) => (
      (file.survives_to_head && file.current_path === file.path)
      || observedPaths.has(file.path)
      || file.lifetime_ids?.some((id) => durableLifetimeIds.has(id))
    )).map((file) => ({
      path: file.path,
      tracked: Boolean(file.lifetime_id || file.lifetime_ids?.length),
      survives_to_head: file.survives_to_head,
      current_path: file.current_path,
    }));
    projected.agent_events = (projected.agent_events ?? []).map((event) => ({
      id: event.id,
      session_id: event.session_id,
      vendor: event.vendor,
      ts_ms: event.ts_ms,
      kind: event.kind,
      action: event.action,
      category: event.category,
      effect: event.effect,
      paths: event.paths,
      write_paths: event.write_paths,
      process_chain: event.process_chain,
      domains: event.domains,
      durable_changes: (event.durable_changes ?? []).map((change) => ({
        status: change.status,
        path: change.path,
        old_path: change.old_path,
      })),
    }));
    projected.file_lifetimes = (projected.file_lifetimes ?? []).filter((lifetime) => (
      lifetime.paths?.length > 1 || durableLifetimeIds.has(lifetime.id)
    )).map((lifetime) => ({
      id: lifetime.id,
      paths: lifetime.paths,
      birth_ms: lifetime.birth_ms,
      death_ms: lifetime.death_ms,
      current_path: lifetime.current_path,
      survives_to_head: lifetime.survives_to_head,
    }));
    projected.commits = (projected.commits ?? []).map((commit) => ({
      committed_at_ms: commit.committed_at_ms,
    }));
  }
  return projected;
}

export function animationBounds(data, spec) {
  const windowStart = data.meta.window_start_ms;
  const windowEnd = data.meta.window_end_ms;
  if (spec.playbackMoments) {
    const moments = spec.playbackMoments(projectForView(data, spec))
      .map(Number).filter(Number.isFinite);
    return moments.length ? [Math.min(...moments), Math.max(...moments)] : [windowStart, windowEnd];
  }
  const timestampFields = ["ts_ms", "committed_at_ms", "started_at_ms", "ended_at_ms"];
  const requirements = new Set(spec.requirements ?? []);
  const timestampGroups = [
    ["events", "verification_events"],
    ["time_buckets"],
    ["commits", "changes"],
    ["sessions"],
  ];
  let timestamps = [];
  for (const group of timestampGroups) {
    timestamps = group.filter((key) => requirements.has(key)).flatMap((key) => {
      const rows = Array.isArray(data[key]) ? data[key] : [];
      return rows.flatMap((row) => timestampFields
        .map((field) => Number(row?.[field]))
        .filter((value) => Number.isFinite(value) && value >= windowStart && value <= windowEnd));
    });
    if (timestamps.length) break;
  }
  if (!timestamps.length) return [windowStart, windowEnd];
  let start = timestamps[0];
  let end = timestamps[0];
  for (const timestamp of timestamps.slice(1)) {
    start = Math.min(start, timestamp);
    end = Math.max(end, timestamp);
  }
  if (start < end) return [start, end];
  const context = 3_600_000;
  return [Math.max(windowStart, start - context), Math.min(windowEnd, end + context)];
}

function sampleValues(values, count, exponent = 1) {
  if (count === 1) return [values.at(-1)];
  return Array.from({ length: count }, (_, index) => (
    values[Math.round((values.length - 1) * (index / (count - 1)) ** exponent)]
  ));
}

function preserveMoments(sampled, required) {
  const output = [...sampled];
  const occupied = new Set();
  for (const value of required.map(Number).filter(Number.isFinite)) {
    if (output.includes(value)) continue;
    let bestIndex = -1;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (let index = 1; index < output.length - 1; index += 1) {
      if (occupied.has(index)) continue;
      const distance = Math.abs(output[index] - value);
      if (distance < bestDistance) {
        bestIndex = index;
        bestDistance = distance;
      }
    }
    if (bestIndex >= 0) {
      output[bestIndex] = value;
      occupied.add(bestIndex);
    }
  }
  return output.sort((left, right) => left - right);
}

export function animationCursors(data, spec, frames) {
  const landmarks = spec.playbackMoments?.(projectForView(data, spec)) ?? [];
  const finiteLandmarks = landmarks.map(Number).filter(Number.isFinite);
  const [start, end] = finiteLandmarks.length
    ? [Math.min(...finiteLandmarks), Math.max(...finiteLandmarks)]
    : animationBounds(data, spec);
  if (frames === 1) return [end];
  const values = [...new Set([start, ...finiteLandmarks, end])]
    .sort((left, right) => left - right);
  if (values.length > 1) {
    const sampled = sampleValues(values, frames, spec.id === "workspace-constellation" ? 1.65 : 1);
    if (spec.id !== "workspace-constellation") return sampled;
    const events = data.agent_events?.length ? data.agent_events : (data.events ?? []);
    const firstWrite = events.find((event) => (
      event.effect === "write" || event.write_paths?.length
    ))?.ts_ms;
    const commits = (data.commits ?? [])
      .map((commit) => Number(commit.committed_at_ms))
      .filter((value) => value >= start && value <= end);
    return preserveMoments(sampled, [events[0]?.ts_ms, firstWrite, commits[Math.floor(commits.length / 2)]]);
  }
  return Array.from({ length: frames }, (_, index) => start + (end - start) * index / (frames - 1));
}

function safeJson(value) {
  return JSON.stringify(value).replaceAll("<", "\\u003c").replaceAll("\u2028", "\\u2028").replaceAll("\u2029", "\\u2029");
}

export async function htmlFor(data, spec, options, renderer = "svg") {
  if (!existsSync(runtimePath)) throw new Error(`missing ${runtimePath}; run npm run build`);
  const runtimeSource = await readFile(runtimePath, "utf8");
  const cursorMs = Math.max(data.meta.window_start_ms, Math.min(data.meta.window_end_ms, parseTime(options.at, data.meta.window_end_ms, data.meta.window_end_ms)));
  const payload = projectForView(data, spec);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="agentsight-vis 0.1">
<meta name="agentsight:view" content="${spec.id}"><meta name="agentsight:revision" content="${data.meta.endpoint_revision}"><meta name="agentsight:time-mode" content="${spec.timeMode}">
<title>${spec.title} · AgentSight</title><style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#070b12;color:#dce8f7}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 75% 0,rgba(35,106,114,.17),transparent 34%),#070b12}.artifact{width:${options.width + 64}px;min-height:${options.height + 190}px;padding:24px 32px;background:#070b12;transition:box-shadow .12s}.artifact.commit-flash{box-shadow:inset 0 0 0 2px #efd265,0 0 30px rgba(239,210,101,.42)}.header{display:flex;justify-content:space-between;gap:24px;border-bottom:1px solid rgba(135,160,190,.18);padding-bottom:14px}.eyebrow,.mode{font:10px ui-monospace,monospace;color:#61d7bf;letter-spacing:.12em;text-transform:uppercase}.header h1{font-size:24px;margin:6px 0}.header p{font-size:11px;color:#71839a;margin:0;max-width:900px}.mode{color:#8c9bb0;border:1px solid rgba(135,160,190,.18);padding:7px 9px;border-radius:99px;align-self:flex-start}.visual{width:${options.width}px;height:${options.height}px;margin-top:14px}.timeline{display:grid;grid-template-columns:42px 1fr 190px;gap:12px;align-items:center;border-top:1px solid rgba(135,160,190,.18);padding:14px 0 8px}.timeline button{width:36px;height:36px;border-radius:50%;border:1px solid rgba(97,215,191,.4);background:#10231f;color:#61d7bf;cursor:pointer}.timeline input{width:100%;accent-color:#61d7bf}.timeline output{font:9px ui-monospace,monospace;color:#9bacc0;text-align:right}.legend{display:flex;gap:18px;font:9px ui-monospace,monospace;color:#71839a}.legend i{display:inline-block;width:13px;height:3px;margin-right:5px;vertical-align:middle}.footer{margin-top:8px;color:#7c8ba0;font:9px ui-monospace,monospace;letter-spacing:0}
</style></head><body><main id="artifact" class="artifact"><header class="header"><div><span class="eyebrow">AgentSight · repository evolution</span><h1 id="view-title"></h1><p id="view-note"></p></div><span id="time-mode" class="mode"></span></header><section id="visual" class="visual"><div id="chart"></div></section><section class="timeline"><button id="play" aria-label="Play history">▶</button><input id="timeline" type="range"><output id="cursor-label"></output></section><section class="legend"><span><i style="background:#62cfe8"></i>recorded Agent event</span><span><i style="background:#efd265"></i>commit border flash</span><span><i style="border:1px solid #9aa8b9"></i>frozen Git reference</span></section><footer id="provenance" class="footer"></footer></main>
<script>${runtimeSource}</script><script>AgentSightSingle.initialize(${safeJson(payload)},${safeJson(spec.id)},{renderer:${safeJson(renderer)},cursorMs:${cursorMs},width:${options.width},height:${options.height},reducedMotion:${Boolean(options.reducedMotion)}})</script></body></html>`;
}

async function openPage(html, options) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: options.width + 64, height: options.height + 190 }, deviceScaleFactor: 1 });
    await page.setContent(html, { waitUntil: "load" });
    await page.waitForFunction(() => window.__AGENTSIGHT_READY__ === true);
    return { browser, page };
  } catch (error) {
    await browser.close();
    throw error;
  }
}

function svgWithMetadata(svg, data, spec, cursorMs) {
  const value = safeJson({
    view: spec.id, repository: data.meta.repository, revision: data.meta.endpoint_revision,
    session_scope: data.meta.session_scope,
    window: [data.meta.window_start_ms, data.meta.window_end_ms], cursor_ms: cursorMs,
    generator: "agentsight-vis 0.1",
  }).replaceAll("&", "&amp;");
  const metadata = `<metadata>${value}</metadata>`;
  return `<?xml version="1.0" encoding="UTF-8"?>\n${svg.replace(">", `>${metadata}`)}`;
}

export async function renderSnapshot(format, html, data, spec, options) {
  const { browser, page } = await openPage(html, options);
  try {
    if (format === "png") {
      await page.locator("#artifact").screenshot({ path: options.output });
    } else if (format === "svg") {
      const svg = await page.locator("#chart svg").evaluate((node) => node.outerHTML);
      const cursorMs = await page.evaluate(() => window.__AGENTSIGHT_CURSOR__);
      await writeFile(options.output, svgWithMetadata(svg, data, spec, cursorMs));
    }
  } finally {
    await browser.close();
  }
}

export async function renderAnimation(format, html, data, spec, options) {
  const temporary = await mkdtemp(join(tmpdir(), "agentsight-vis-frames-"));
  try {
    const { browser, page } = await openPage(html, options);
    try {
      const cursors = animationCursors(data, spec, options.frames);
      const start = cursors[0];
      const end = cursors.at(-1);
      await page.locator("#timeline").evaluate((node, bounds) => {
        [node.min, node.max] = bounds.map(String);
      }, [start, end]);
      for (let frame = 0; frame < options.frames; frame += 1) {
        const cursor = cursors[frame];
        await page.evaluate((value) => window.AgentSightSingle.renderAt(value), cursor);
        await page.evaluate(() => new Promise((resolve) => {
          requestAnimationFrame(() => requestAnimationFrame(resolve));
        }));
        await page.locator("#artifact").screenshot({ path: join(temporary, `frame-${String(frame).padStart(4, "0")}.png`) });
      }
    } finally {
      await browser.close();
    }
    const input = join(temporary, "frame-%04d.png");
    if (format === "gif") {
      run("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-framerate", String(options.fps), "-i", input, "-vf", `fps=${options.fps},scale=${options.width + 64}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a`, options.output]);
    } else {
      run("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-framerate", String(options.fps), "-i", input, "-c:v", "libx264", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", options.output]);
    }
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
}

export async function renderOne(data, spec, options) {
  for (const key of ["width", "height", "frames", "fps"]) {
    if (!Number.isInteger(options[key]) || options[key] <= 0) throw new Error(`--${key} must be a positive integer`);
  }
  const format = extname(options.output).slice(1).toLowerCase();
  if (!["html", "svg", "png", "gif", "mp4"].includes(format)) {
    throw new Error(`unsupported output format .${format}; use html, svg, png, gif, or mp4`);
  }
  options.output = resolve(options.output);
  await mkdir(dirname(options.output), { recursive: true });
  const html = await htmlFor(data, spec, {
    ...options,
    reducedMotion: ["gif", "mp4"].includes(format),
  }, "svg");
  if (format === "html") await writeFile(options.output, html);
  else if (["svg", "png"].includes(format)) await renderSnapshot(format, html, data, spec, options);
  else await renderAnimation(format, html, data, spec, {
    ...options,
    frames: spec.timeMode === "static" ? 1 : options.frames,
  });
  process.stderr.write(`rendered ${spec.id} -> ${basename(options.output)}\n`);
}

export async function main(values = process.argv.slice(2)) {
  const options = parseArgs(values);
  if (options.help) { process.stdout.write(usage()); return; }
  if (options.listViews) { process.stdout.write(`${views.map((view) => `${view.id}\t${view.title}`).join("\n")}\n`); return; }
  if (!options.view || !options.output) throw new Error("--view and --output are required\n\n" + usage());
  if (!options.repo || !options.since) throw new Error("--repo and --since are required");
  const spec = requireView(options.view);
  const data = await buildEvolutionData(options, spec);
  await renderOne(data, spec, options);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(`agentsight-vis: ${error.message}`); process.exitCode = 2; });
}
