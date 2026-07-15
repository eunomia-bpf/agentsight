import { chromium } from "playwright";
import { stat, writeFile } from "node:fs/promises";

const baseURL = process.argv[2] ?? "http://127.0.0.1:4173";
const destination = process.argv[3] ?? "artifacts/browser-metrics.json";
const families = ["pixel", "matrix", "map", "animation", "river", "forensic", "storylines", "longitudinal"];
const browser = await chromium.launch({ headless: true });
const firstRenderMs = [];
const familyNavigationMs = Object.fromEntries(families.map((family) => [family, []]));
const scrubResponseMs = [];
let heapBytes = null;

for (let repetition = 0; repetition < 7; repetition += 1) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1050 } });
  const start = performance.now();
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  await page.getByTestId("family-overview").waitFor({ state: "visible" });
  firstRenderMs.push(performance.now() - start);
  for (const family of families) {
    const navStart = performance.now();
    await page.getByTestId(`nav-${family}`).click();
    await page.getByTestId(`family-${family}`).locator(".panel").first().waitFor({ state: "visible" });
    await page.waitForTimeout(family === "forensic" ? 120 : 20);
    familyNavigationMs[family].push(performance.now() - navStart);
  }
  const slider = page.getByTestId("playback-slider");
  const scrubStart = performance.now();
  await slider.focus();
  await slider.press("ArrowLeft");
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  scrubResponseMs.push(performance.now() - scrubStart);
  heapBytes = await page.evaluate(() => {
    const memory = performance.memory;
    return memory ? memory.usedJSHeapSize : null;
  });
  await page.close();
}
await browser.close();

function summary(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const p95 = sorted[Math.min(sorted.length - 1, Math.ceil(sorted.length * 0.95) - 1)];
  return { median_ms: Number(median.toFixed(2)), p95_ms: Number(p95.toFixed(2)), samples: values.map((value) => Number(value.toFixed(2))) };
}

const dataset = await stat("public/gallery-data.json");
const result = {
  schema: "agentsight.gallery.browser-metrics.v1",
  measured_at: new Date().toISOString(),
  environment: { browser: "Playwright Chromium 1.61.1", viewport: "1600x1050", repetitions: 7, cold_page_per_repetition: true },
  workload: { dataset_bytes: dataset.size, sessions: 56, path_event_rows: 6535, file_lifetimes: 1027, commits: 177, git_changes: 1852, line_pixels: 12000 },
  first_family_visible: summary(firstRenderMs),
  family_navigation: Object.fromEntries(Object.entries(familyNavigationMs).map(([family, values]) => [family, summary(values)])),
  cursor_scrub_two_frames: summary(scrubResponseMs),
  used_js_heap_bytes_last_run: heapBytes,
  caveat: "Headless local measurements are systems diagnostics, not evidence of human review utility or perceptual scalability.",
};
await writeFile(destination, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify(result, null, 2));
