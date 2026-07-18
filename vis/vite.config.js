import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    minify: "oxc",
    sourcemap: false,
    lib: {
      entry: resolve(import.meta.dirname, "runtime.js"),
      name: "AgentSightVis",
      formats: ["iife"],
      fileName: () => "repository-nebula.iife.js",
    },
  },
});
