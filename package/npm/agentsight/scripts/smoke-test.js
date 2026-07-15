"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { serveWeb } = require("../lib/cli");

const bin = path.resolve(__dirname, "..", "bin", "agentsight.js");

for (const args of [["--version"], ["--help"]]) {
  const result = childProcess.spawnSync(process.execPath, [bin, ...args], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    console.error(result.stdout);
    console.error(result.stderr);
    process.exit(result.status || 1);
  }
}

const temp = fs.mkdtempSync(path.join(os.tmpdir(), "agentsight-npm-"));
const fakeCollector = path.join(temp, "agentsight");
fs.writeFileSync(
  fakeCollector,
  "#!/usr/bin/env node\nrequire('fs').writeFileSync(process.env.AGENTSIGHT_FAKE_OUT, JSON.stringify(process.argv.slice(2)))\n",
  { mode: 0o755 },
);
const fakeOut = path.join(temp, "collector-args.json");
const delegated = childProcess.spawnSync(process.execPath, [bin, "monitor", "--help"], {
  env: { ...process.env, AGENTSIGHT_FAKE_OUT: fakeOut, PATH: `${temp}${path.delimiter}${process.env.PATH || ""}` },
  encoding: "utf8",
});
if (delegated.status !== 0 || fs.readFileSync(fakeOut, "utf8") !== '["monitor","--help"]') {
  console.error(delegated.stdout);
  console.error(delegated.stderr);
  process.exit(delegated.status || 1);
}

const scopedInstall = path.join(temp, "node_modules", "@eunomia-bpf", "agentsight");
fs.mkdirSync(path.join(scopedInstall, "bin"), { recursive: true });
fs.copyFileSync(bin, path.join(scopedInstall, "bin", "agentsight.js"));
const otherBinDir = path.join(temp, "other-bin");
fs.mkdirSync(otherBinDir);
fs.symlinkSync(path.join(scopedInstall, "bin", "agentsight.js"), path.join(otherBinDir, "agentsight"));
const noCollector = childProcess.spawnSync(process.execPath, [bin, "top", "--plain", "--once"], {
  env: { ...process.env, AGENTSIGHT_COLLECTOR: "", PATH: otherBinDir },
  encoding: "utf8",
  timeout: 2000,
});
if (noCollector.status !== 127 || !noCollector.stderr.includes("AgentSight collector not found")) {
  console.error(noCollector.stdout);
  console.error(noCollector.stderr);
  process.exit(noCollector.status || 1);
}

const server = serveWeb({ host: "127.0.0.1", port: 0, open: false, snapshot: null });
setTimeout(() => {
  server.close();
  console.error("Timed out waiting for npm web malformed-host smoke.");
  process.exit(1);
}, 5000).unref();
server.on("listening", () => {
  const { port } = server.address();
  const request = http.request({ host: "127.0.0.1", port, path: "/", headers: { Host: "[" } }, (response) => {
    if (response.statusCode !== 400) {
      console.error(`expected 400 for malformed Host, got ${response.statusCode}`);
      process.exit(1);
    }
    response.resume();
    response.on("end", () => server.close(() => console.log("AgentSight npm smoke test passed.")));
  });
  request.end();
});
