// Copies the pre-built sample data from docs/ into the frontend public
// directory so the recorded demo exercises the same snapshot + overview
// model as a live Node. Also copies screenshot assets for the demo banner.

import { copyFileSync, mkdirSync, existsSync, readFileSync, writeFileSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const samples = [
  ['sample-snapshot.json', 'sample-snapshot.json'],
  ['sample-overview.json', 'sample-overview.json'],
];
const PUBLIC_DIR = resolve(here, '../public');
const IMG_DIR = resolve(PUBLIC_DIR, 'images');

function stableRecordedQuota(value) {
  if (Array.isArray(value)) return value.map(stableRecordedQuota);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value).map(([key, nested]) => [
    key,
    key === 'resets_at' ? null : stableRecordedQuota(nested),
  ]));
}

mkdirSync(PUBLIC_DIR, { recursive: true });
for (const [sourceName, outputName] of samples) {
  const src = resolve(here, `../../docs/${sourceName}`);
  const out = resolve(PUBLIC_DIR, outputName);
  const sample = stableRecordedQuota(JSON.parse(readFileSync(src, 'utf8')));
  writeFileSync(out, `${JSON.stringify(sample, null, 2)}\n`);
  console.log(`Prepared ${sourceName} -> ${out}`);
}

// Copy screenshots for the demo banner
mkdirSync(IMG_DIR, { recursive: true });
const images = ['demo-timeline.png', 'demo-tree.png', 'demo-metrics.png', 'top-mode-demo.png'];
for (const img of images) {
  const src = resolve(here, `../../docs/${img}`);
  if (existsSync(src)) {
    copyFileSync(src, resolve(IMG_DIR, img));
    console.log(`Copied ${img}`);
  }
}
