import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const baseURL = process.argv[2] ?? "http://127.0.0.1:4173";
const destination = process.argv[3] ?? "artifacts";
await mkdir(destination, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1050 } });
await page.goto(baseURL, { waitUntil: "domcontentloaded" });
await page.getByTestId("family-overview").waitFor({ state: "visible" });
await page.screenshot({ path: `${destination}/paper-atlas.png`, fullPage: false });
await page.screenshot({ path: `${destination}/overview.png`, fullPage: true });

for (const family of ["pixel", "map", "forensic", "longitudinal"]) {
  await page.getByTestId(`nav-${family}`).click();
  await page.getByTestId(`family-${family}`).locator(".panel").first().waitFor({ state: "visible" });
  await page.waitForTimeout(family === "forensic" ? 2_000 : 700);
  if (family === "map") {
    await page.screenshot({ path: `${destination}/paper-map.png`, fullPage: false });
  }
  await page.screenshot({ path: `${destination}/${family}.png`, fullPage: true });
}

await browser.close();
