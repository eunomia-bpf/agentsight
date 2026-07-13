# ToolSafe RQ2 Full Run Report

**Time:** 2026-07-13 02:15 PDT  
**Gate:** EXPERIMENT / RQ2 / ToolSafe  
**Execution status:** PASS  
**Predeclared tested-hypothesis classification:** CONTRADICTED  
**Paper and story changes:** none

## Boundary

This is the complete execution of Revision 3 over the released ToolSafe data.
It tests one supporting hypothesis within fixed paper-level RQ2: whether the
published TS-Guard semantic triple transfers across benchmark families as a
more useful problem-localization profile than equally informed risk-conditioned
raw-tool and risk-only profiles.

It does not test or replace the whole RQ, does not authorize changing the
positive paper hypothesis, and does not modify the canonical thesis, four RQs,
story, or paper. A contradicted construction is retained as internal experiment
history and routes the EXPERIMENT gate to a materially different real experiment.

## Command

```bash
python3 script/toolsafe_agentprof_eval.py full \
  --projection docs/visexp/out/toolsafe-rq2/source/projection.jsonl \
  --labels-dir docs/visexp/out/toolsafe-rq2/source/labels \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/toolsafe-rq2/full \
  --bootstraps 10000 --max-bootstrap-attempts 50000 --seed 4203
```

## Complete Execution Checks

All terminal requirements passed:

- 7,182 released rows were scored, including exactly 6,786 real operations and
  the 396-row compatibility extension.
- Three leave-one-family-out folds completed: AgentHarm 731 target / 6,451
  reference, ASB 5,231 / 1,951, and AgentDojo 1,220 / 5,962.
- Each predictor received only the two reference-family label files. Held-out
  labels entered only after ordinary predictions, reference densities,
  fallback choices, and bootstrap draws were saved.
- The real runner-recorded profiler was `agentpprof 0.2.37`.
- Every semantic, risk+tool, risk-only, exact-tool, causes, interaction, and
  flat profile matched an independent stack counter for target/reference sides
  of both populations and all folds.
- Case-sensitive raw tool identities were preserved; the AgentProf-only UTF-8
  hex encoding was one-to-one and reversible in every profile.
- Strict and unsafe-only mappings for both primary and compatibility populations
  each reached 10,000/10,000 valid paired bootstrap replicates in exactly 10,000
  supplied attempts. No retry or invalid-attempt supplementation was needed.
- Official strict TS-Guard metrics reproduced exactly for all 7,182 rows.

## Primary Strict Result

| Method | AP | Recall at 30% work | Work to 50% recall | Groups | Work@5 groups | Max group share |
|---|---:|---:|---:|---:|---:|---:|
| Semantic triple | 0.930871 | 0.233705 | 0.321839 | 30 | 0.097554 | 0.314618 |
| Risk + raw tool | 0.892672 | 0.534645 | 0.282051 | 826 | 0.018126 | 0.039051 |
| Risk only | 0.891822 | 0.241926 | 0.304892 | 9 | 0.304892 | 0.350722 |

The semantic view compresses the operation set to 30 groups versus 826 matched
raw-tool groups and 3,376 per-interaction groups. That satisfies the declared
10x compression requirement, but compression cannot compensate for worse
operation-level localization.

### Paired strict uncertainty

| Difference | Mean AP difference | 95% CI | Mean R@30 difference | Mean work-to-50 difference |
|---|---:|---:|---:|---:|
| Semantic - risk + raw tool | 0.029228 | [-0.005450, 0.058494] | -0.252180 | +0.056169 |
| Semantic - risk only | 0.030343 | [-0.004953, 0.060037] | -0.141398 | +0.047454 |

Both AP point differences are positive, but neither paired interval is strictly
above zero. Against raw-tool, the R@30 interval is entirely negative and the
work-to-50 interval entirely positive, so the semantic view exposes less signal
early and requires more operation work under the conservative tie policy.

## Mandatory Family Result

| Held-out family | Semantic AP | Risk + raw tool AP | Risk-only AP | Direction |
|---|---:|---:|---:|---|
| AgentHarm | 0.865998 | 0.864149 | 0.867093 | beats raw, loses to risk |
| ASB | 0.949481 | 0.950302 | 0.950302 | loses to both |
| AgentDojo | 0.904165 | 0.812525 | 0.844164 | beats both |

The predeclared no-family-reversal condition fails. The pooled AP increase is
driven primarily by AgentDojo and cannot hide the ASB reversal or the small
AgentHarm risk-only reversal.

## Unsafe-only Robustness

| Method | AP | Recall at 30% work | Work to 50% recall |
|---|---:|---:|---:|
| Semantic triple | 0.529137 | 0.482801 | 0.366048 |
| Risk + raw tool | 0.646298 | 0.760442 | 0.247126 |
| Risk only | 0.600268 | 0.730958 | 0.243442 |

Unsafe-only reverses the pooled direction and loses to the raw baseline in all
three families. This independently forbids an unconditional unsafe-operation
interpretation.

## Fallback and Artifact Checks

- Semantic: 6,786 exact semantic keys, no fallback.
- Risk + raw tool: 235 exact cross-family keys and 6,551 risk-only backoffs.
- Risk only: 6,786 exact risk keys.
- Exact-tool control: 250 exact keys and 6,536 global backoffs.
- The 396 declared non-operations do not create the conclusion: primary and
  compatibility results have the same direction, and
  `compatibility_only_improvement` is false.

The high raw-tool backoff rate is a measured property of the public benchmarks:
exact tool identities transfer poorly across families. It does not rescue the
semantic construction because the equally informed risk-only baseline remains
strong and the mandatory operation-work and family checks fail.

## Predeclared Decision

The runner records:

- source coverage, label isolation, AgentProf counts, official metric
  reproduction, and 10x compression: PASS;
- both paired strict AP confidence intervals strictly positive: FAIL;
- semantic R@30 and work-to-50 better than both baselines: FAIL;
- positive AP difference in every family against both baselines: FAIL;
- unsafe-only direction preserved: FAIL.

Revision 3 declares the construction contradicted when the main strict direction
reverses across families. Therefore the automatic `CONTRADICTED` classification
is the predeclared outcome; it is not a post-hoc conservative reinterpretation.

## Routing

Do not tune ToolSafe labels, semantic cells, thresholds, family weights, or
fallback rules. Do not change the fixed hypothesis, RQ2, four RQs, thesis, or
canonical paper. After independent result review, return to the outer EXPERIMENT
decision and select a materially different real tool-effect/localization
experiment that can test the positive hypothesis directly.

## Artifacts

- Full generated report: `docs/visexp/out/toolsafe-rq2/full/report.md`
- Complete metrics: `docs/visexp/out/toolsafe-rq2/full/metrics.json`
- Terminal execution status: `docs/visexp/out/toolsafe-rq2/full/execution-status.json`
- Fold predictions, profiles, counts, and bootstrap predictions:
  `docs/visexp/out/toolsafe-rq2/full/folds/`
- Approved plan and review history: this directory's `experiment-plan.md`,
  `plan-review.md`, `preflight-review.md`, and
  `preflight-review-round-2.md`
