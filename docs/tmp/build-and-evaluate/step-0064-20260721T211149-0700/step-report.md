# Step 0064 — aggregate real AgentCap reviews by user-facing task

Timestamp: 2026-07-21T21:21:00-07:00
Gate: EXPERIMENT
Status: complete

## Purpose

Build the smallest real demonstration of the user's proposed workflow: inspect
enough same-family sessions, decide a bounded shared vocabulary, mark task
transitions, permit unequal stack depth, and produce one actually aggregated
flame graph through standard pprof tooling.

## Node records

### PROPOSE

Selected four complete AgentCap research-review sessions spanning evaluator,
artifact, documentation, claim, first-review, and repair-review work. Required
full operation coverage within selected sessions, but deliberately did not scan
or label every AgentCap session.

Artifact: `experiment-001/experiment-plan.md`.

### REVIEW

Approved the bounded plan because it tests the user-facing representation
without claiming semantic-tag accuracy. Rejected run ID as a stack frame, fixed
depth, per-operation labeling, a custom renderer, and a broad all-project scan.

Artifact: `experiment-001/plan-review.md`.

### REAL PREFLIGHT

Verified the four source-native traces contain 80, 75, 76, and 95 operations.
Implemented explicit inclusive boundary lookup and unit checks for the shared
root and variable depth.

### FULL RUN

Annotated all 326 operations, generated a deterministic operation-count pprof,
decoded it with Go pprof, checked source-session labels, and captured the
standard pprof flame-graph view. Task depth is two or three frames before the
action leaf.

Artifacts: `experiment-001/full-run.md`, the retained `.pb.gz`, and the pprof
UI screenshot under `docs/visexp/out/agentcap-query-aggregation-v1/`.

### RESULT REVIEW

Accepted the tested hypothesis. The graph exposes cross-session recurring work
and yields a concrete sparse-boundary annotation interface. It is a product
prototype and qualitative case, not a broad scientific accuracy result.

Artifact: `experiment-001/result-review.md`.

## Outcome and next decision

The current evidence is strong enough to show the user the graph and discuss
the interaction. A later product change can accept sparse boundary annotations
as an external input. No paper text, frontend, shared skill, or AgentPProf
output contract was changed in this step.
