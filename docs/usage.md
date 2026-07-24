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
uses live eBPF capture whenever sudo is already available. Without eBPF
privileges, it falls back to process snapshots and agent-native sessions.

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
no default event filters, and saves a local SQLite session for `report`,
`report prompts`, and other report queries.

Use `debug trace` only when you need low-level control over capture sources or
explicit filters. It is the advanced replacement for a raw trace command, not
the normal record/report workflow.

## Share Agent Nebula

`vis` reads local Claude, Codex, and Gemini sessions without sudo and produces
one self-contained Agent Nebula artifact per output file:

```sh
cd your-repository
agentsight vis
```

The default artifact is `output/agent-nebula.gif`. Specify `-o` only when you
want another path or format:

```sh
agentsight vis . --global \
  --compact-rate 30s \
  -o output/agent-nebula.html \
  -o output/agent-nebula.png \
  -o output/agent-nebula.gif \
  -o output/agent-nebula.mp4
```

HTML works without external assets. PNG, SVG, and MP4 require Chromium; GIF
additionally requires FFmpeg. Repeated `-o` values reuse one session scan and layout.
GIF/MP4 default to a 30-second compact replay whose frames are spaced uniformly
by action index; use `--compact-rate full` for one media frame per action. HTML
always keeps the full action timeline.
See [the Chinese algorithm specification](repository-nebula.zh-CN.md) for the
event boundary, force model, frame count, and export invariants.

## Diagnose a long-running workspace

`diagnose` computes a compact Markdown brief for another Agent to inspect. It
uses the same Claude, Codex, and Gemini session discovery as `vis`, but reports
source-linked process signals rather than rendering media:

```sh
cd your-repository
agentsight diagnose
```

The default output is `output/trajectory-brief.md`. It covers the
inspect–mutate–validate action sequence, pre-mutation inspection, module
migration, artifact revival, repeated changes, validation lag and carryover,
one-touch artifacts, documentation reuse, open and mutation-closed exploration
spans, and explicit Skill-associated session footprints. A signal is a place
to inspect, not an automatic claim that the Agent failed or wasted work; each
section states its interpretation boundary and cites the native transcript and
Tool call. When available, evidence also carries the associated native user
prompt preview so the next Agent can distinguish a user correction from an
unprompted change without scanning the entire transcript.

Continued and archived transcript files can contain the same native Tool call.
`diagnose` deduplicates those copies by source-native call/event identity before
computing patterns. Coverage prints both raw parsed Tool/LLM records and unique
retained Tool calls so the boundary is visible.

Use `-o output/trajectory-brief.json` for complete machine-readable session and
transition rows, or add `--global` to admit externally rooted sessions whose
file operations target the repository. Read-only external roots stay out of
the mutation-driven pre-mutation-inspection and module-transition sequence;
roots that mutate the repository remain evolution evidence. A root-external
session may be a delegated subagent intentionally working on the repository, so
access is not labelled an independent consumer or causal reuse.
The source-snapshot fingerprint in each output distinguishes changing live
histories.

Validation relations are deliberately conservative: a successful recognized
check closes pending mutations in the same worktree only as a temporal
association. It does not prove per-file coverage or correctness.
