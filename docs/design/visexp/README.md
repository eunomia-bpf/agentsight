# Semantic Profiling Research Notes

This directory keeps the design and paper notes for semantic agent profiling,
semantic flamegraphs, and `agentpprof`. It intentionally does not include the
large generated experiment-output tree from the research branch or the many
interim planning notes used while developing the idea.

## Read First

1. [semantic-operation-profiling.md](semantic-operation-profiling.md)

   Core model: the weighted typed operation tree used by `agentpprof`, and why
   semantic flamegraphs are folded operation paths rather than a separate
   dashboard abstraction.

2. [agentpprof-backend-architecture.md](agentpprof-backend-architecture.md)

   Backend design: future backends as operation-tree rewrites, with the current
   implementation keeping the core fold algorithm small.

3. [paper/evaluation-claims-setup.zh-CN.md](paper/evaluation-claims-setup.zh-CN.md)

   Chinese write-up of the claims, terminology, experiment setup, oracles,
   results, and evidence boundaries.

4. [agent-observability-landscape.md](agent-observability-landscape.md)

   Landscape note: how current observability, tracing, debugging, and profiling
   tools differ from semantic profiling.

## Directory Boundaries

Keep new semantic profiling design notes here instead of creating another
`agentpprof/` or `semantic-profiling/` directory under `docs/design/`.

Use this split:

- model and paper framing: `semantic-operation-profiling.md`;
- backend and algorithm architecture: `agentpprof-backend-architecture.md`;
- experiments, claims, evidence gates: `paper/evaluation-claims-setup.zh-CN.md`;
- related work and tool landscape: `agent-observability-landscape.md`;
- user-facing CLI docs: `../../agentpprof.md` and `../../agentpprof-zh.md`.

Generated files under `docs/visexp/out/` are not committed to `main` here. They
remain on the research branch as experiment artifacts.
