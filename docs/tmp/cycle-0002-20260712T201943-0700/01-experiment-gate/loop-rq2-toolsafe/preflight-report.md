# ToolSafe RQ2 Real Preflight Report

**Time:** 2026-07-13 01:57 PDT  
**Gate:** EXPERIMENT / RQ2 / ToolSafe  
**Status:** PASS FOR INDEPENDENT REVIEW  
**Paper and story changes:** none

## Purpose

This preflight checks whether the approved Revision 3 experiment can execute on
real released ToolSafe artifacts with the real AgentProf binary. It is not a
scientific result and cannot support, contradict, narrow, or rewrite the paper's
RQ2, hypothesis, thesis, or story.

The fixed paper-level RQ remains whether AgentProf's semantic profiles correspond
to real problem outcomes better than conventional execution-oriented profiles.
This experiment tests only the approved supporting hypothesis: on ToolSafe's
published cross-family safety signal, the semantic triple profile should improve
operation-level prioritization over risk-conditioned raw-tool and risk-only
profiles.

## Approved Markdown Plan Inputs

- Public repository: ToolSafe at commit
  `46358fa424a927a895c6c8322f99032c4eb5155e`.
- Public source and released TS-Guard logs: AgentHarm, ASB, and AgentDojo.
- Real profiler: `agentpprof 0.2.37` from
  `agentpprof/target/release/agentpprof`.
- Target-blind preflight sample: the first 128 clusters in neutral source order
  from each family. The approved first-32 prefix was enlarged because AgentHarm's
  first 32 and 64 clusters contain no strict negative; 128 is the first planned
  checkpoint that exercises both classes without changing order.
- Bootstrap: seed 4203, 200 required valid paired replicates for both populations
  and both label mappings.
- Primary population: real proposed tool operations only.
- Compatibility population: all released rows, including declared non-operations.
- Primary mapping: strict, where controversial and unsafe are benchmark-positive
  triage targets. Mandatory robustness: unsafe-only.

## Commands

```bash
python3 script/toolsafe_agentprof_eval.py prepare \
  --toolsafe-root .agentsight/experiments/toolsafe-rq2/ToolSafe \
  --out docs/visexp/out/toolsafe-rq2/source

python3 script/toolsafe_agentprof_eval.py preflight \
  --projection docs/visexp/out/toolsafe-rq2/source/projection.jsonl \
  --labels-dir docs/visexp/out/toolsafe-rq2/source/labels \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/toolsafe-rq2/preflight \
  --clusters-per-family 128 --bootstraps 200 --seed 4203
```

## Source Preparation Checks

Source preparation passed all declared checks:

| Family | Released records | Real operations | Non-operations |
|---|---:|---:|---:|
| AgentHarm | 731 | 731 | 0 |
| ASB | 5,231 | 4,835 | 396 |
| AgentDojo | 1,220 | 1,220 | 0 |
| **Total** | **7,182** | **6,786** | **396** |

Every ToolSafe `meta_sample` equals its joined TS-Bench row, every released
`labels.json` entry equals the row score, and every released prediction equals
the stored TS-Guard risk result. Prediction input contains only allowlisted
visible fields and published detector outputs. Outcome labels remain in separate
per-family files.

## Repairs Found by Real Preflight

The initial run and independent preflight review found five local implementation
defects. They were repaired without changing the approved scientific plan:

1. Subset scoring initially compared a 32-cluster sample with complete-population
   official metrics. Exact official reproduction is now required only when all
   7,182 rows are scored; a subset still computes its own diagnostic metric.
2. AgentProf normalizes folded-stack frames to ASCII lowercase and trims frame
   separators. The scientific projection now preserves all 522 exact,
   case-sensitive raw tool strings. Operation files use a reversible one-to-one
   UTF-8 hex representation only at the AgentProf boundary; every target and
   reference report records equal raw and encoded unique counts.
3. Taking the first 32 clusters produced a one-class AgentHarm strict subset and
   made valid bootstrap sampling impossible. The runner again uses the approved
   neutral prefix, enlarged to the first 128 clusters per family as authorized by
   the plan review. This is an execution repair, not a scientific sample choice.
4. The runner now queries the supplied binary and records `agentpprof 0.2.37` in
   every fold status, the combined metrics, and terminal execution status.
5. Full-run classification now records every predeclared decision boolean,
   applies family reversal and compatibility-only contradiction rules, checks
   unsafe-only reversal before `SUPPORTED`, and reports preflight as
   `NOT_EVALUATED_PREFLIGHT`. A new run clears stale terminal artifacts and a
   successful run removes `need-more.json`.

## Execution Checks

- Each leave-one-family-out predictor process received exactly two reference
  label files and no target-family label file.
- Held-out labels were loaded only by the later scoring process after prediction
  artifacts existed.
- AgentProf successfully profiled semantic, risk+tool, risk-only, exact-tool,
  causes-only, interaction, and flat/direct groupings for target and reference
  populations in every fold.
- Every real AgentProf stack counter exactly matched an independently reconstructed
  counter for every profile, population, target, and reference input.
- All raw-tool encodings were one-to-one and reversible in every target/reference
  profile; raw scientific keys were not normalized.
- The output directory contains only the successful `report.md`, `metrics.json`,
  and `execution-status.json` terminal artifacts; no stale failure status remains.
- All four bootstrap cells reached 200/200 valid paired replicates:

| Population | Strict | Unsafe-only |
|---|---:|---:|
| Real operations | 200 | 200 |
| Compatibility | 200 | 200 |

## Diagnostic Preflight Numbers

The 1,081-operation preflight sample produced the following strict pooled metrics:

| Method | AP | Recall at 30% work | Work to 50% recall | Groups |
|---|---:|---:|---:|---:|
| Semantic | 0.855946 | 0.004065 | 0.380204 | 24 |
| Risk + raw tool | 0.917037 | 0.000000 | 0.455134 | 196 |
| Risk only | 0.917688 | 0.000000 | 0.461610 | 9 |

The paired semantic-minus-risk+tool AP mean was -0.054947 with a 200-replicate
95% interval of [-0.077534, -0.033240]. Against risk-only it was -0.055807 with
an interval of [-0.080206, -0.035614]. The runner correctly records
`NOT_EVALUATED_PREFLIGHT`: these deliberately partial diagnostics cannot decide
the tested hypothesis. They verify that every predeclared result branch runs
without silently skipping a method and do not update the paper.

## Preflight Decision

The implementation completed the approved real preflight and produced all
required artifacts. No paper claim is updated. Proceed to the full run only if
an independent `research-experiment-design` review confirms that label isolation,
AgentProf use, grouping fairness, bootstrap construction, and result boundaries
match Revision 3.

## Artifacts

- Source preparation: `docs/visexp/out/toolsafe-rq2/source/report.md`
- Preflight summary: `docs/visexp/out/toolsafe-rq2/preflight/report.md`
- Complete metrics: `docs/visexp/out/toolsafe-rq2/preflight/metrics.json`
- Fold predictions and profiles:
  `docs/visexp/out/toolsafe-rq2/preflight/folds/`
- Implementation: `script/toolsafe_agentprof_eval.py`
