import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:4173", viewport: { width: 1600, height: 1050 }, colorScheme: "dark" },
  webServer: { command: "npm run dev -- --port 4173", url: "http://127.0.0.1:4173", reuseExistingServer: true, timeout: 30_000 },
});
