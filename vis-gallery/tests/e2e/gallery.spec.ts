import { expect, test } from "@playwright/test";

const families = ["overview", "pixel", "matrix", "map", "animation", "river", "forensic", "storylines", "longitudinal"];

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("family-overview")).toBeVisible({ timeout: 30_000 });
});

test("every family renders real-data panels", async ({ page }) => {
  for (const family of families) {
    await page.getByTestId(`nav-${family}`).click();
    await expect(page.getByTestId(`family-${family}`)).toBeVisible();
    await expect(page.getByTestId(`family-${family}`).locator(".panel, .metric").first()).toBeVisible();
  }
});

test("shared playback cursor and filters remain interactive", async ({ page }) => {
  const slider = page.getByTestId("playback-slider");
  const maximum = Number(await slider.getAttribute("max"));
  const initial = Number(await slider.inputValue());
  expect(maximum - initial).toBeLessThan(60_000);
  await page.getByRole("button", { name: "Play history" }).click();
  await expect.poll(async () => Number(await slider.inputValue())).toBeLessThan(initial);
  await page.getByRole("button", { name: "Pause playback" }).click();
  const before = await slider.inputValue();
  await slider.focus();
  await slider.press("ArrowLeft");
  expect(await slider.inputValue()).not.toBe(before);
  await slider.press("End");
  const visibleEvidence = page.locator(".metric-strip .metric strong").first();
  const allVendorCount = await visibleEvidence.textContent();
  await page.getByRole("button", { name: "codex", exact: true }).click();
  await expect(page.getByRole("button", { name: "codex", exact: true })).toHaveClass(/is-active/);
  await expect.poll(() => visibleEvidence.textContent()).not.toBe(allVendorCount);
  await page.getByTestId("nav-river").click();
  await expect(page.getByText("Agent activity river")).toBeVisible();
  await page.getByTestId("nav-matrix").click();
  await expect(page.getByText("File × observation-day matrix")).toBeVisible();
});

test("capture representative atlas plates", async ({ page }) => {
  await page.screenshot({ path: "test-results/screenshots/paper-atlas.png", fullPage: false });
  await page.screenshot({ path: "test-results/screenshots/overview.png", fullPage: true });
  for (const family of ["pixel", "map", "forensic", "longitudinal"]) {
    await page.getByTestId(`nav-${family}`).click();
    await page.waitForTimeout(family === "forensic" ? 2_000 : 700);
    if (family === "map") await page.screenshot({ path: "test-results/screenshots/paper-map.png", fullPage: false });
    await page.screenshot({ path: `test-results/screenshots/${family}.png`, fullPage: true });
  }
});
