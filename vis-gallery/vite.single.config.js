import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    target: "es2022",
    outDir: "single/dist",
    emptyOutDir: true,
    sourcemap: false,
    minify: true,
    lib: {
      entry: resolve(import.meta.dirname, "single/browser-entry.js"),
      formats: ["iife"],
      name: "AgentSightSingleBundle",
      fileName: () => "runtime.iife.js",
    },
  },
});
