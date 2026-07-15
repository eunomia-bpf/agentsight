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
  const before = await slider.inputValue();
  await slider.focus();
  await slider.press("ArrowLeft");
  expect(await slider.inputValue()).not.toBe(before);
  await page.getByRole("button", { name: "codex", exact: true }).click();
  await expect(page.getByRole("button", { name: "codex", exact: true })).toHaveClass(/is-active/);
  await page.getByTestId("nav-matrix").click();
  await expect(page.getByText("File × observation-day matrix")).toBeVisible();
});

test("capture representative atlas plates", async ({ page }) => {
  await page.screenshot({ path: "artifacts/paper-atlas.png", fullPage: false });
  await page.screenshot({ path: "artifacts/overview.png", fullPage: true });
  for (const family of ["pixel", "map", "forensic", "longitudinal"]) {
    await page.getByTestId(`nav-${family}`).click();
    await page.waitForTimeout(family === "forensic" ? 2_000 : 700);
    if (family === "map") await page.screenshot({ path: "artifacts/paper-map.png", fullPage: false });
    await page.screenshot({ path: `artifacts/${family}.png`, fullPage: true });
  }
});
