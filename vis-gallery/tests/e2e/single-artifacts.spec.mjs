import { expect, test } from "@playwright/test";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, readdir, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { views } from "../../single/registry.js";
import { buildEvolutionData, renderOne } from "../../single/render.mjs";
import { fixtureData as data } from "../fixture-data.mjs";

const outputDirectory = resolve("test-results/single-html");
const screenshotDirectory = resolve("test-results/screenshots/all-views");
const formatDirectory = resolve("test-results/single-formats");

test.beforeAll(async () => {
  await rm(outputDirectory, { recursive: true, force: true });
  await rm(screenshotDirectory, { recursive: true, force: true });
  await rm(formatDirectory, { recursive: true, force: true });
  await mkdir(outputDirectory, { recursive: true });
  await mkdir(screenshotDirectory, { recursive: true });
  await mkdir(formatDirectory, { recursive: true });
  for (const view of views) {
    await renderOne(data, view, {
      output: join(outputDirectory, `${view.id}.html`),
      width: 1200,
      height: 640,
      frames: 3,
      fps: 2,
    });
  }
});

test("exports portable formats, rejects static animation, and cleans temporary frames", async ({ page }) => {
  const dynamic = views.find((view) => view.id === "activity-pulse");
  const staticView = views.find((view) => view.id === "git-sediment");
  const options = (output) => ({ output, width: 480, height: 300, frames: 2, fps: 2 });
  const frameDirectories = async () => new Set(
    (await readdir(tmpdir())).filter((name) => name.startsWith("agentsight-vis-frames-")),
  );
  const before = await frameDirectories();

  const svgPath = join(formatDirectory, "activity-pulse.svg");
  const pngPath = join(formatDirectory, "activity-pulse.png");
  const gifPath = join(formatDirectory, "activity-pulse.gif");
  const mp4Path = join(formatDirectory, "activity-pulse.mp4");
  await renderOne(data, dynamic, options(svgPath));
  await renderOne(data, dynamic, options(pngPath));
  await renderOne(data, dynamic, options(gifPath));
  await renderOne(data, dynamic, options(mp4Path));

  expect(await readFile(svgPath, "utf8")).toContain("<metadata>");
  for (const path of [pngPath, gifPath, mp4Path]) {
    expect((await stat(path)).size, `${path} should not be empty`).toBeGreaterThan(100);
  }
  await page.goto(pathToFileURL(pngPath).href);
  const [pngWidth, pngHeight] = await page.locator("img").evaluate((image) => [image.naturalWidth, image.naturalHeight]);
  expect(pngWidth).toBe(544);
  expect(pngHeight).toBeGreaterThanOrEqual(490);
  for (const path of [gifPath, mp4Path]) {
    expect(spawnSync("ffprobe", ["-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path], { encoding: "utf8" }).stdout).toContain("video");
  }

  await expect(renderOne(data, staticView, options(join(formatDirectory, "git-sediment.gif"))))
    .rejects.toThrow(/static view/);
  expect([...await frameDirectories()].filter((name) => !before.has(name))).toEqual([]);
});

test("builds a shareable graph directly from repository and native histories", async ({ page }) => {
  const evolution = await buildEvolutionData({ repo: resolve(".."), since: "1d", until: "now", head: "HEAD" });
  expect(evolution.meta.repository).toBe(basename(resolve("..")));
  expect(evolution.tree.children.length).toBeGreaterThan(0);
  const output = join(outputDirectory, "direct-repository-treemap.html");
  await renderOne(evolution, views.find((view) => view.id === "repository-treemap"), {
    output, width: 720, height: 420, frames: 2, fps: 2,
  });
  await page.goto(pathToFileURL(output).href);
  await page.waitForFunction(() => window.__AGENTSIGHT_READY__ === true);
  await expect(page.locator("#chart svg")).toHaveCount(1);
  await expect(page.locator("#provenance")).toContainText("generator: agentsight-vis 0.1");
});

test("opens and checks every one-graph HTML artifact individually", async ({ page }) => {
  for (const view of views) {
    const consoleErrors = [];
    const pageErrors = [];
    const onConsole = (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    };
    const onPageError = (error) => pageErrors.push(error.message);
    page.on("console", onConsole);
    page.on("pageerror", onPageError);

    const artifactPath = join(outputDirectory, `${view.id}.html`);
    await page.goto(pathToFileURL(artifactPath).href, { waitUntil: "load" });
    await page.waitForFunction(() => window.__AGENTSIGHT_READY__ === true);
    await expect(page.locator('meta[name="agentsight:view"]')).toHaveAttribute("content", view.id);
    await expect(page.locator("#chart")).toHaveCount(1);
    await expect(page.locator("#chart svg")).toHaveCount(1);
    await expect(page.locator("#chart svg")).toBeVisible();
    await expect(page.locator("#view-title")).toHaveText(view.title);
    await expect(page.locator("#provenance")).toContainText("generator: agentsight-vis 0.1");

    const timeline = page.locator("#timeline");
    if (view.timeMode === "static") {
      await expect(timeline).toBeDisabled();
    } else {
      await expect(timeline).toBeEnabled();
      await page.evaluate((cursor) => window.AgentSightSingle.renderAt(cursor), data.meta.window_start_ms);
      await expect(timeline).toHaveValue(String(data.meta.window_start_ms));
      await page.evaluate((cursor) => window.AgentSightSingle.renderAt(cursor), data.meta.window_end_ms);
      await expect(timeline).toHaveValue(String(data.meta.window_end_ms));
    }

    const overflow = await page.locator("#artifact").evaluate((node) => ({
      x: node.scrollWidth - node.clientWidth,
      y: node.scrollHeight - node.clientHeight,
    }));
    expect(overflow.x, `${view.id} horizontal overflow`).toBeLessThanOrEqual(1);
    expect(overflow.y, `${view.id} vertical overflow`).toBeLessThanOrEqual(1);
    expect(consoleErrors, `${view.id} console errors`).toEqual([]);
    expect(pageErrors, `${view.id} page errors`).toEqual([]);
    await page.screenshot({ path: join(screenshotDirectory, `${view.id}.png`), fullPage: true });

    page.off("console", onConsole);
    page.off("pageerror", onPageError);
  }
});
