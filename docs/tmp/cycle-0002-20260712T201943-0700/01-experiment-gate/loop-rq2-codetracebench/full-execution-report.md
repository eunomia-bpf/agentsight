# Full Execution Report: CodeTraceBench RQ2 Differential Profiling

**Started:** 2026-07-12T23:28:22-07:00
**Completed:** 2026-07-13T00:28:03-07:00
**Cycle/gate:** cycle 0002 / EXPERIMENT
**Parent plan:** `experiment-plan.md` revision 6
**Implementation review:** `preflight-review.md`, Round 3 PASS
**Execution status:** **PASS**
**Scientific verdict:** pending independent result review

## Scope

This run executes the one approved CodeTraceBench experiment for the tested
hypothesis under fixed RQ2. Execution PASS means every declared source,
proposed-method, baseline, control, null, uncertainty, compatibility, and
secondary-analysis component completed. It is not a positive scientific
verdict and does not answer the entire RQ.

No source adapter, operation mapping, matching fallback, metric, repetition
count, RQ, hypothesis, thesis, story, or paper text changed during execution.

## Command

```bash
python3 script/codetracebench_agentprof_eval.py full \
  --full-manifest .agentsight/experiments/codetracebench-rq2/manifests/full.parquet \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --codetracer-root .agentsight/experiments/codetracebench-rq2/CodeTracer \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/codetracebench-rq2 \
  --partition-candidates 10000 --partition-retained 200 \
  --permutations 2000 --bootstraps 10000 --seed 4202
```

The command exited zero after 3,580.755 seconds.

## Source Completion

Every one of the 3,316 full-manifest rows received a terminal status before
scientific scoring:

| Status | Trajectories |
|---|---:|
| source-valid | 2,717 |
| explicit source exclusion | 599 |
| terminal total | 3,316 |

The runner retained 2,634 source-valid outcome-bearing reference trajectories.
The primary target population is exactly the 405 source-valid failed verified
trajectories established by the complete verified audit, containing 20,866
steps. It never truncated, padded, synthesized, reordered, or count-fitted a
source-invalid trajectory.

The complete 3,316-row ledger is
`../../../../visexp/out/codetracebench-rq2/full/full-source-coverage.md`.

## Information Boundary And AgentProf

The runner built operations and target-held-out profiles from the safe manifest
projection and public raw archives. It invoked release AgentProf for semantic,
raw-action, and phase organizations over the complete reference and target
operation files, and all stacks matched independent counts exactly.

Before loading `incorrect_stages`, it wrote:

- all 405 target score tables:
  `../../../../visexp/out/codetracebench-rq2/full/predictions-pre-label.md`;
- the operation-mass-only selection of 200 controls from 10,000 candidates:
  `../../../../visexp/out/codetracebench-rq2/full/frequency-partitions-pre-label.md`.

Only then did the terminal metric phase load incorrect and unuseful step IDs.

## Completion Audit

| Component | Required | Completed |
|---|---:|---:|
| source terminal statuses | 3,316 | 3,316 |
| source-valid failed targets | 405 | 405 |
| frequency-partition candidates | 10,000 | 10,000 |
| retained frequency-matched controls | 200 | 200 |
| outcome-null trials | 2,000 | 2,000 |
| valid task-cluster bootstrap replicates | 10,000 | 10,000 |
| task-bootstrap sampling attempts | informational | 10,007 |

Seven task draws lost required source-valid dual-cohort support after
resampling. They were excluded by the fixed rule and replaced until 10,000
valid replicates completed. The three compared methods shared every valid draw.

## Primary Result Snapshot

The 405 targets contain 833 hidden incorrect steps; 206 targets have no
incorrect step and remain in pooled work accounting.

| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall |
|---|---:|---:|---:|
| semantic | 0.052290 | 0.307323 | 0.434343 |
| raw-action | 0.042936 | 0.310924 | 0.500144 |
| phase | 0.048382 | 0.310924 | 0.517588 |

Semantic profiling has the highest deterministic AP and lowest work to 50%
recall, but the predeclared paired AP bootstrap intervals do not establish a
win:

| Paired AP difference | Mean | 95% interval |
|---|---:|---:|
| semantic - raw-action | 0.009443 | [-0.008322, 0.036855] |
| semantic - phase | -0.001548 | [-0.031736, 0.021013] |

The 200 frequency-matched non-semantic controls have median AP 0.042294 and a
2.5--97.5% range of [0.036177, 0.048459]. Semantic AP exceeds the best retained
partition by 0.001309. However, its outcome-null mean AP is 0.052879 with
one-sided empirical p=0.531234, so the observed failed-versus-successful signal
is not distinguished from exact-cell outcome permutation.

These facts require scientific interpretation; execution itself must not label
the tested hypothesis positive merely because the report status is PASS.

## Heterogeneity And Secondary Checks

- Semantic AP is strongest in Terminus2 (0.075917) and mini-SWE-agent
  (0.101729), loses to raw-action in OpenHands, and loses to phase in SWE-agent.
- CodeTracer-compatible semantic macro P/R/F1 is
  0.111408/0.214760/0.123887 over the 199 positive targets.
- Semantic pooled false-positive burden on the 206 zero-positive targets is
  0.144058.
- Unuseful and union analyses, absolute-hotspot controls, framework breakdowns,
  and all bootstrap intervals are present in the canonical output report.

The complete result is
`../../../../visexp/out/codetracebench-rq2/full/report.md`; all 200 control
metrics are in
`../../../../visexp/out/codetracebench-rq2/full/frequency-partition-results.md`.

## Git Note

The converged runner and review state were committed as `a932f739`. The required
push was attempted but the remote returned HTTP 500 while receiving about 3.46
GiB of pre-existing branch history. This external Git failure is orthogonal to
the experiment and did not affect or delay execution.

## Handoff

Independent result review must now classify only this tested hypothesis,
diagnose whether the limitation is the differential signal, semantic grouping,
transfer, or benchmark protocol, and select the single next highest-value real
experiment. It may not change the fixed RQ, thesis, story, or paper. No paper
edit is authorized from this execution report alone.
