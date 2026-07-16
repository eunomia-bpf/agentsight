import { expect, test } from "@playwright/test";
import { mkdir, readFile, rm } from "node:fs/promises";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { views } from "../../single/registry.js";
import { renderOne } from "../../single/render.mjs";

const outputDirectory = resolve("test-results/single-html");
const screenshotDirectory = resolve("test-results/screenshots/all-views");
const fixturePath = resolve("public/gallery-data.json");
const data = JSON.parse(await readFile(fixturePath, "utf8"));

test.beforeAll(async () => {
  await rm(outputDirectory, { recursive: true, force: true });
  await rm(screenshotDirectory, { recursive: true, force: true });
  await mkdir(outputDirectory, { recursive: true });
  await mkdir(screenshotDirectory, { recursive: true });
  for (const view of views) {
    await renderOne(data, view, {
      input: fixturePath,
      output: join(outputDirectory, `${view.id}.html`),
      width: 1200,
      height: 640,
      frames: 3,
      fps: 2,
    });
  }
});

test("opens and checks every one-graph HTML artifact individually", async ({ page }) => {
  for (const view of views) {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    const onConsole = (message: { type(): string; text(): string }) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    };
    const onPageError = (error: Error) => pageErrors.push(error.message);
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
