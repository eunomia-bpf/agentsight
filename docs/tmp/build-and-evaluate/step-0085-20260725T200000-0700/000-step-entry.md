# Step 0085 entry: Case Study 2 provenance repair (delegated to codex)

Timestamp: 2026-07-25T20:00:00-07:00
Outer gate: EXPERIMENT (verification/repair)
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Executor: external `codex` CLI agent

## Why this step exists

The independent evaluation audit
(`docs/tmp/review/codex-eval-review-20260725T193000-0700/eval-review.md`)
found that Case Study 2's displayed recovery counts (3,286 bad-side vs 455
good-side under `recover interaction`) are not traceable to any primary
result record (the closest record, step-0067 write-consistency-review,
holds older values 2,993/392), and that the current recovery percentages
(44.6%/12.0%) and both bootstrap intervals ([.181,.293] and [-.107,.061])
exist only in review narratives rather than durable primary artifacts.

This step recomputes every displayed Case Study 2 quantity from the frozen
workspace and produces one durable primary record. If recomputed values
differ from the paper, the paper is corrected to the recomputed values.

## Fixed constraints

- Source of truth: the frozen recursive annotation workspace under
  `docs/visexp/out/agentreward-diff-pprof-v1/` (`recursive-annotation-v1/`
  and the signed pair profiles), plus the frozen pairs/labels the existing
  harness `script/agentreward_diff_pprof_eval.py` reads (READ-ONLY).
- No re-annotation, no new LLM calls: this is deterministic recomputation.
- Every displayed number gets a manifest line: value, formula/definition,
  input files with checksums.

Full task specification: `experiment-001/task-spec.md`.
