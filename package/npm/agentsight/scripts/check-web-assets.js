"use strict";

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const index = path.join(root, "web", "index.html");

if (!fs.existsSync(index)) {
  console.error("Missing npm Web assets.");
  console.error("Run from the repository root:");
  console.error("  npm ci --prefix frontend");
  console.error("  node frontend/scripts/prepare-sample.mjs");
  console.error("  npm run build --prefix frontend");
  console.error("  node script/npm/prepare-agentsight.mjs");
  process.exit(1);
}
