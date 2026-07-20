# Build From Source

Use this guide when developing AgentSight or building a local binary from the repository. If you only want to run a release binary, see the Quick Start in [README.md](https://github.com/eunomia-bpf/agentsight#quick-start).

## Requirements

- Linux with eBPF support
- Rust toolchain 1.88.0+
- Node.js 18+
- clang and LLVM
- libelf development headers
- zlib development headers
- make and standard C build tools

On Ubuntu/Debian, the repository Makefile can install the expected system dependencies:

```bash
make install
```

## Build

Clone with submodules:

```bash
git clone https://github.com/eunomia-bpf/agentsight.git --recursive
cd agentsight
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

Build all components:

```bash
make build
```

`make build` rebuilds the frontend and eBPF loaders, then refreshes the
vendored assets embedded by the Rust binary. The frontend build id is stable for
the same source inputs, so repeated builds do not create new hashed asset paths
unless the frontend source or configuration changed.

The built binary is at:

```text
collector/target/release/agentsight
```

Build individual components when iterating:

```bash
make build-frontend  # frontend assets
make build-vis       # self-contained Agent Nebula runtime
make build-bpf       # eBPF programs
make build-rust      # Rust collector
```

`make build-rust` and direct `cargo build` use the existing vendored assets and
do not refresh them. For packaging outside the Makefile, set
`AGENTSIGHT_SYNC_VENDOR=1` when building the collector after rebuilding the
frontend and eBPF loaders.

## Verify

Run the test suite:

```bash
make test
```

For frontend development:

```bash
cd frontend
npm run dev
```
