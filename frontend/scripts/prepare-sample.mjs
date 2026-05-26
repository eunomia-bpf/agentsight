// Produces frontend/public/sample-trace.log for the live demo from the raw
// recorded session in docs/. The raw log carries the kernel monotonic clock in
// NANOSECONDS (bpf_ktime_get_ns), but the frontend expects epoch MILLISECONDS
// (normally produced by the backend's TimestampNormalizer). We replicate that
// here: shift every event onto a real wall-clock anchor and convert ns -> ms,
// so the demo shows sensible absolute times and a correct ~5 min duration.
//
// The raw log is left untouched; this only writes the bundled demo copy.

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(here, '../../docs/example_record_ claude_init.log');
const OUT = resolve(here, '../public/sample-trace.log');

const NS_PER_MS = 1_000_000;
// Wall-clock the session is anchored to (the recording date). Only the relative
// spacing matters for the demo; this just makes absolute timestamps look real.
const ANCHOR_MS = Date.parse('2026-04-29T10:00:00Z');
// Real epoch-ms today is ~1.8e12; anything above 1e13 (year ~2286) can't be a
// real epoch-ms value, so it's a raw monotonic-ns timestamp that needs converting.
const NS_THRESHOLD = 1e13;

const lines = readFileSync(SRC, 'utf8').split('\n').filter((l) => l.trim());

// First pass: find the minimum monotonic timestamp to use as t=0.
let minTs = Infinity;
for (const line of lines) {
  const ts = JSON.parse(line).timestamp;
  if (typeof ts === 'number' && ts < minTs) minTs = ts;
}

const toEpochMs = (ts) =>
  typeof ts === 'number' && ts > NS_THRESHOLD
    ? ANCHOR_MS + Math.round((ts - minTs) / NS_PER_MS)
    : ts;

const out = lines.map((line) => {
  const e = JSON.parse(line);
  e.timestamp = toEpochMs(e.timestamp);
  if (e.data && typeof e.data.timestamp === 'number') {
    e.data.timestamp = toEpochMs(e.data.timestamp);
  }
  return JSON.stringify(e);
});

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, out.join('\n') + '\n');
console.log(`Wrote ${out.length} normalized events -> ${OUT}`);
