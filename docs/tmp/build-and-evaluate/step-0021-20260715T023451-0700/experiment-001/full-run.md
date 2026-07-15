# Full Run — Reused CodeTraceBench Stage Fidelity

**Run time:** 2026-07-15T02:51:00-07:00
**Plan:** [`experiment-plan.md`](experiment-plan.md)
**Status:** terminal; independent result review PASS / scientific result MIXED

## Command

```bash
python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-recurrence-codetracebench-v1/full
```

The command exited zero. The only stderr text was a local pandas warning that
installed `bottleneck` 1.3.5 is older than pandas' optional 1.3.6 preference;
the parquet input, scorer, and run all completed.

## Complete Population

- Disjoint reference: 2,229 sessions / 87,703 operations.
- Target: 405 sessions / 20,866 operations / 20,461 adjacent pairs.
- Official annotation: 2,948 complete stage intervals.
- Frameworks: 213 OpenHands, 28 SWE-agent, 93 Terminus2, and 71
  mini-SWE-agent trajectories.
- Rust input: unit weight plus only `session` and nine-way `action`.
- Rust version: `agentpprof 0.2.37`.

## Primary Results

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed F1 |
|---|---:|---:|---:|---:|
| recurrence | 0.161640 | 0.792371 | 0.268506 | 0.475008 |
| phase-change | 0.164126 | 0.359811 | 0.225425 | 0.654445 |
| action-change | 0.160897 | 0.793158 | 0.267524 | 0.473242 |
| always-boundary | 0.124285 | 1.000000 | 0.221092 | 0.247585 |
| session-one-block | 0.000000 | 0.000000 | 0.000000 | 0.295788 |

Recurrence improves boundary F1 over the strongest alternative by 0.000981
but trails the strongest partition alternative by 0.179438. The plan therefore
classifies the complete result as `mixed`, subject to independent result review.

## Mechanism Diagnostic

The recurrence cutoff is 0.122991, between low/high occurrence-weighted NPMI
centers -0.061435 and 0.307416. It creates 12,871 segments and only ten unique
motifs. Compared with direct action-change over all 20,461 pairs:

- 20,391 decisions are identical;
- 70 action changes are merged, all `install -> other`;
- zero same-action pairs are split.

Thus the release recurrence is not expressing a meaningful cross-action stage
structure on this population. High-NPMI self-transitions dominate cutoff
calibration, leaving only one cross-action transition above the continuity
threshold. This is a mechanism diagnosis, not permission to change RQ3 or the
paper story.

## Validity

The emitted summary reports all required checks true: full population scored,
reference and target sessions disjoint, minimal Rust inputs, phase/raw-action/
official-stage fields absent from Rust, stages loaded only after prediction,
exact stage coverage, every pair scored once, every operation assigned once,
all operation weight conserved, and no algorithm or threshold search.

## Raw Artifacts

- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/summary.json`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/report.md`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/profile.json`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/pair-decisions.jsonl`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/operation-assignments.jsonl`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/reference-input.jsonl`
- `.agentsight/experiments/rq3-recurrence-codetracebench-v1/full/target-input.jsonl`

No paper, idea-story, thesis, RQ, or hypothesis change follows until the fresh
result reviewer verifies the raw rows and interpretation.
