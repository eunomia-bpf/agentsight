# Usage

**English** | [中文](https://github.com/eunomia-bpf/agentsight/blob/master/docs/usage.zh-CN.md)

## Building from Source

### 1. Clone the repository and initialize submodules

```sh
git clone https://github.com/eunomia-bpf/agentsight.git
cd agentsight
git submodule update --init --recursive
```

If you have already cloned the repository but the submodule directories (`libbpf/` and `bpftool/`) are empty, run:

```sh
git submodule update --init --recursive
```

### 2. Install system dependencies

```sh
make install
```

This installs the required build dependencies: libelf, zlib, clang, llvm, Node.js, and the Rust toolchain.

### 3. Build

```sh
make build
```

After a successful build, the agentsight binary is located at `collector/target/release/agentsight`.

You can also build individual components:

```sh
make build-bpf       # eBPF C programs only
make build-rust      # Rust collector only
make build-frontend  # Frontend only
```

## Running from Source

Navigate to the repository root after `make build`. Commands that load eBPF
probes should be run with `sudo`, except `top`, which can run without sudo and
uses live eBPF capture only when sudo is already available.

```sh
# Live view of local agent sessions
./collector/target/release/agentsight top

# Launch and record a command
sudo ./collector/target/release/agentsight record -- claude

# Inspect the latest saved run
./collector/target/release/agentsight report

# Attach to an already-running process family
sudo ./collector/target/release/agentsight record -c claude

# Debug-level configurable tracing
sudo ./collector/target/release/agentsight debug trace --server -c claude

# Raw SSL debug capture with HTTP parsing
sudo ./collector/target/release/agentsight debug ssl --http-parser
```

Use `top` for the normal live view. Use `record` when you want a durable
agent-run artifact; it starts SSL, process, system, and web-view collection with
AgentSight's default filters, and saves a local SQLite session for `report`,
`top --db`, `report prompts`, and other report queries.

Use `debug trace` only when you need low-level control over capture sources or
filters. It is the advanced replacement for a raw trace command, not the normal
record/report workflow.
