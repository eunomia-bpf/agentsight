#!/usr/bin/env node
import { mkdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { views } from "./registry.js";
import { buildEvolutionData, parseArgs, renderOne } from "./render.mjs";

const supportedFormats = new Set(["html", "svg", "png", "gif", "mp4"]);

function usage() {
  return `Generate every AgentSight single-view artifact from one data scan.

Usage:
  agentsight-vis-all --repo PATH --since TIME --output-dir DIR [--formats html,svg,png]

The repository/session scan runs once. Static views become one-frame GIF/MP4
files; time-aware animations sample each view's observed evidence range.
`;
}

function parseAll(values) {
  const forwarded = [];
  let outputDir;
  let formats = ["html"];
  for (let index = 0; index < values.length; index += 1) {
    const flag = values[index];
    if (flag === "--help" || flag === "-h") return { help: true };
    if (flag === "--output-dir") {
      outputDir = values[++index];
    } else if (flag === "--formats") {
      formats = values[++index].split(",").map((value) => value.trim().toLowerCase()).filter(Boolean);
    } else {
      forwarded.push(flag, values[++index]);
    }
  }
  if (!outputDir) throw new Error("--output-dir is required");
  const invalid = formats.filter((format) => !supportedFormats.has(format));
  if (invalid.length) throw new Error(`unsupported formats: ${invalid.join(", ")}`);
  return { common: parseArgs(forwarded), outputDir: resolve(outputDir), formats };
}

export async function main(values = process.argv.slice(2)) {
  const options = parseAll(values);
  if (options.help) { process.stdout.write(usage()); return; }
  if (!options.common.repo || !options.common.since) throw new Error("--repo and --since are required");
  await mkdir(options.outputDir, { recursive: true });
  const data = await buildEvolutionData(options.common);
  let rendered = 0;
  for (const spec of views) {
    for (const format of options.formats) {
      await renderOne(data, spec, {
        ...options.common,
        output: join(options.outputDir, `${spec.id}.${format}`),
      });
      rendered += 1;
    }
  }
  process.stderr.write(`rendered ${rendered} files from one scan -> ${options.outputDir}\n`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(`agentsight-vis-all: ${error.message}`); process.exitCode = 2; });
}
