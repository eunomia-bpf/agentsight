#!/usr/bin/env node
"use strict";

const { main } = require("../lib/cli");
const path = require("path");

main(process.argv.slice(2)).catch((error) => {
  const message = error && error.message ? error.message : String(error);
  const commandName = path.basename(process.argv[1] || "agentsight");
  console.error(`${commandName}: ${message}`);
  process.exitCode = 1;
});
