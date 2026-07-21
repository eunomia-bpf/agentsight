# Step 0063 — Task-semantic differential pprof

Timestamp: 2026-07-21T02:09:38-07:00
Outer state: EXPERIMENT
Research question: RQ1, attribution and localization

## Why this step exists

The previous source-native run established that explicit task, plan, and
delegation control events can carry a task hierarchy without asking an LLM to
classify every operation. That run did not yet give an end user a compact way
to compare two executions of the same task. This step tests the product-facing
question directly: can one standard pprof make the excess work and missing work
of a bad execution visible relative to a good execution?

## Fixed hypothesis under test

For two real executions of the same task, a signed bad-minus-good pprof over a
task-semantic stack exposes repeated, error, abandoned, and successful paths in
a form that standard pprof tools can inspect, while ordinary actions inherit
the current task context rather than creating a new stack frame per action.

This experiment tests that hypothesis only. It does not redefine the paper's
RQ, thesis, four-RQ structure, or claims.

## Product boundary

AgentPProf emits one standard pprof artifact. This step may use Markdown and raw
JSON/JSONL as experiment records, but it must not add a frontend, dashboard,
custom visualization runtime, or new paper artifact. The existing `frontend/`,
`docs/agentpprof-paper/`, and all skills are out of scope.

## Nodes

- `experiment-001/experiment-plan.md`: fixed scientific and product plan.
- `experiment-001/plan-review.md`: three rounds of plan review.
- `experiment-001/real-preflight.md`: one real same-task pair through the exact
  parser, pprof writer, and `go tool pprof` reader.
- `experiment-001/full-run.md`: complete consensus-labeled mixed-task run.
- `experiment-001/result-review.md`: independent interpretation and limits.
- `outer-audit.md`: checks scope, state transition, and repository changes.

## Final state

The case study and complete 125-task/338-pair run finished. A first independent
result review invalidated the adapter, the two defects were minimally repaired,
and the unchanged full experiment was rerun. The fixed run generated and read
back all 676 planned pprof files with zero failures; the second independent
review returned PASS. The bounded RQ1 result and product backend may return to
the outer orchestrator. Grok 4.5 then reviewed the exact pushed commit and also
returned PASS with no must-fix. No paper, frontend, or skill change was made.
