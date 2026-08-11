"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const WEB_ROOT = process.env.AGENTSIGHT_WEB_ROOT || path.join(PACKAGE_ROOT, "web");
const PROJECT_URL = "https://github.com/eunomia-bpf/agentsight";
const COLLECTOR_COMMANDS = new Set(["record", "top", "monitor", "stat", "report", "debug"]);

function packageJson() {
  return JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, "package.json"), "utf8"));
}

function commandName() {
  return path.basename(process.argv[1] || "agentsight");
}

function printHelp() {
  console.log(`AgentSight ${packageJson().version}

Usage:
  ${commandName()} web [--host 127.0.0.1] [--port 7395]
  ${commandName()} serve --snapshot snapshot.json [--host 127.0.0.1] [--port 7395]
  ${commandName()} open snapshot.json [--host 127.0.0.1] [--port 7395]
  ${commandName()} record|top|monitor|stat|report|debug ...

Web commands are implemented by this npm package. Collector commands delegate to
a real AgentSight collector binary when one is available.

Project: ${PROJECT_URL}`);
}

function printVersion() {
  console.log(`AgentSight npm ${packageJson().version}`);
  const collector = findCollector();
  console.log(`Collector: ${collector || "not found; install with `cargo install agentsight`"}`);
}

function parseOptions(args) {
  const options = {
    host: "127.0.0.1",
    port: 7395,
    open: false,
    snapshot: null,
    positionals: [],
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--host" || arg === "--listen") {
      options.host = requiredValue(args, ++i, arg);
    } else if (arg.startsWith("--host=")) {
      options.host = arg.slice("--host=".length);
    } else if (arg.startsWith("--listen=")) {
      options.host = arg.slice("--listen=".length);
    } else if (arg === "--port") {
      options.port = parsePort(requiredValue(args, ++i, arg));
    } else if (arg.startsWith("--port=")) {
      options.port = parsePort(arg.slice("--port=".length));
    } else if (arg === "--snapshot" || arg === "--db-export") {
      options.snapshot = requiredValue(args, ++i, arg);
    } else if (arg.startsWith("--snapshot=")) {
      options.snapshot = arg.slice("--snapshot=".length);
    } else if (arg === "--open") {
      options.open = true;
    } else if (arg === "-h" || arg === "--help") {
      options.help = true;
    } else {
      options.positionals.push(arg);
    }
  }

  return options;
}

function requiredValue(args, index, flag) {
  const value = args[index];
  if (!value || value.startsWith("--")) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function parsePort(value) {
  const port = Number.parseInt(value, 10);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`invalid port: ${value}`);
  }
  return port;
}

function contentType(filePath) {
  const types = {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
  };
  return types[path.extname(filePath).toLowerCase()] || "application/octet-stream";
}

function staticPath(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath.split("?")[0]).replace(/^\/+/, "") || "index.html";
  } catch {
    return null;
  }

  const root = path.resolve(WEB_ROOT);
  const candidate = path.resolve(root, decoded);
  if (candidate !== root && !candidate.startsWith(root + path.sep)) {
    return null;
  }
  if (isFile(candidate)) {
    return candidate;
  }
  if (isFile(path.join(candidate, "index.html"))) {
    return path.join(candidate, "index.html");
  }
  return path.extname(decoded) ? null : path.join(root, "index.html");
}

function isFile(filePath) {
  try {
    return fs.statSync(filePath).isFile();
  } catch {
    return false;
  }
}

function sendFile(response, filePath) {
  fs.readFile(filePath, (error, data) => {
    if (error) {
      response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end(`Failed to read file: ${error.message}\n`);
      return;
    }
    response.writeHead(200, {
      "Content-Type": contentType(filePath),
      "Cache-Control": filePath.replace(/\\/g, "/").includes("/_next/static/")
        ? "public, max-age=31536000, immutable"
        : "no-cache",
    });
    response.end(data);
  });
}

function serveWeb(options) {
  if (!isFile(path.join(WEB_ROOT, "index.html"))) {
    throw new Error(
      `missing Web assets at ${WEB_ROOT}; run ` +
        "`npm ci --prefix frontend && node frontend/scripts/prepare-sample.mjs && npm run build --prefix frontend && node script/npm/prepare-agentsight.mjs`.",
    );
  }

  const snapshot = options.snapshot ? path.resolve(options.snapshot) : null;
  if (snapshot && !isFile(snapshot)) {
    throw new Error(`snapshot not found: ${snapshot}`);
  }

  const server = http.createServer((request, response) => {
    let url;
    try {
      url = new URL(request.url || "/", `http://${request.headers.host || "localhost"}`);
    } catch {
      response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Bad request\n");
      return;
    }
    if (snapshot && request.method === "GET" && url.pathname === "/api/v1/info") {
      response.writeHead(200, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      });
      response.end(JSON.stringify({
        protocol_version: 1,
        product: "agentsight",
        authorization_required: false,
      }));
      return;
    }
    if (url.pathname === "/api/v1/snapshot" || (snapshot && url.pathname === "/sample-snapshot.json")) {
      if (!snapshot) {
        response.writeHead(404, { "Content-Type": "application/json; charset=utf-8" });
        response.end(JSON.stringify({ error: "No snapshot was provided to the npm viewer." }));
        return;
      }
      sendFile(response, snapshot);
      return;
    }

    const filePath = staticPath(url.pathname);
    if (!filePath) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Not found\n");
      return;
    }
    sendFile(response, filePath);
  });

  server.listen(options.port, options.host, () => {
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : options.port;
    const url = `http://${options.host}:${port}`;
    console.log(`AgentSight Web UI: ${url}`);
    if (snapshot) {
      console.log(`Snapshot: ${snapshot}`);
    }
    if (options.open) {
      openBrowser(url);
    }
  });
  return server;
}

function openBrowser(url) {
  const platform = os.platform();
  const command = platform === "darwin" ? "open" : platform === "win32" ? "cmd" : "xdg-open";
  const args = platform === "win32" ? ["/c", "start", "", url] : [url];
  const child = childProcess.spawn(command, args, { detached: true, stdio: "ignore" });
  child.on("error", (error) => {
    console.warn(`Could not open browser automatically: ${error.message}`);
  });
  child.unref();
}

function findCollector() {
  if (process.env.AGENTSIGHT_COLLECTOR && isExecutable(process.env.AGENTSIGHT_COLLECTOR)) {
    return path.resolve(process.env.AGENTSIGHT_COLLECTOR);
  }

  const current = realPath(process.argv[1] || "");
  for (const dir of (process.env.PATH || "").split(path.delimiter).filter(Boolean)) {
    for (const name of executableNames("agentsight")) {
      const candidate = path.join(dir, name);
      if (isExecutable(candidate) && realPath(candidate) !== current && !isNpmDispatcher(candidate)) {
        return candidate;
      }
    }
  }
  return null;
}

function executableNames(name) {
  return process.platform === "win32" ? [`${name}.exe`, `${name}.cmd`, `${name}.bat`, name] : [name];
}

function isExecutable(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.X_OK);
    return true;
  } catch {
    return process.platform === "win32" && fs.existsSync(filePath);
  }
}

function realPath(filePath) {
  try {
    return fs.realpathSync(filePath);
  } catch {
    return filePath;
  }
}

function isNpmDispatcher(filePath) {
  return realPath(filePath).replace(/\\/g, "/").endsWith("/agentsight/bin/agentsight.js");
}

function delegateToCollector(args) {
  const collector = findCollector();
  if (!collector) {
    console.error(`AgentSight collector not found.

Install it with:
  cargo install agentsight

or download:
  ${PROJECT_URL}/releases/latest`);
    process.exitCode = 127;
    return;
  }

  const child = childProcess.spawn(collector, args, { stdio: "inherit" });
  child.on("error", (error) => {
    console.error(`failed to start collector: ${error.message}`);
    process.exitCode = 127;
  });
  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exitCode = code === null ? 1 : code;
    }
  });
}

async function main(args) {
  const command = args[0];
  if (!command || command === "-h" || command === "--help") {
    printHelp();
  } else if (command === "-V" || command === "--version" || command === "version") {
    printVersion();
  } else if (command === "web" || command === "serve" || command === "open") {
    const options = parseOptions(args.slice(1));
    if (options.help) {
      printHelp();
      return;
    }
    if (!options.snapshot && (command === "serve" || command === "open")) {
      options.snapshot = options.positionals[0] || null;
    }
    options.open ||= command === "open";
    serveWeb(options);
  } else if (COLLECTOR_COMMANDS.has(command)) {
    delegateToCollector(args);
  } else {
    throw new Error(`unknown command: ${command}. Run ${commandName()} --help.`);
  }
}

module.exports = { main, findCollector, serveWeb };
