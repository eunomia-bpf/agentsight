import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 180_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  use: { viewport: { width: 1280, height: 900 }, colorScheme: "dark" },
});
