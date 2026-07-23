# Independent result review: HINTBench method matrix

Timestamp: 2026-07-22T16:57:08-07:00
Reviewer role: fresh result reviewer
Scope: HINTBench RQ2 full run only

## Verdict

**Run status: valid.** The full HINTBench population is present, every method
preserves exactly the same operation mass, the stored per-query AP values and
MAP values reproduce exactly, and the A1 construction is source-only.

**Tested hypothesis: inconclusive on HINTBench.** The product-aligned A1 method
is substantially better than recurrence N1, but it does not establish an
improvement over native-tree N0: the A1--N0 MAP difference is -0.005341 and its
paired 95% interval crosses zero. A1 is also significantly below the retained
historical AgentProf organization. The valid HINT result therefore supports
source preservation as a necessary constructor property and rejects A0's
semantic-only projection as the product-facing comparison, but it does not
support a claim that the automatic semantic hierarchy outperforms all native
or historical organizations on this workload.

**Research value: supporting.** This is useful additional RQ2 evidence and a
mechanism boundary, not a complete answer to RQ2 and not a direct thesis
challenge.

## Evidence reviewed

I read and checked:

- `method-matrix-plan.md`;
- `script/rq2_agent_segmentation_eval.py` in full;
- all eight full HINT source packets and all eight automatic-Agent annotation
  files;
- the authoritative HINT full-test projection, source targets, selected
  historical profile, and historical point-estimate metadata under
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/`;
- every current HINT result needed to reconstruct the four method paths,
  profile mass, localizer scores, per-query AP, and summary under
  `.agentsight/experiments/rq2-a0-v1/full/hint/results/`.

The recomputation did not call the experiment scorer. It independently parsed
the packet and annotation files, expanded sparse marks, reconstructed N0 and
A1 from native fields, parsed N1 assignments from the actual recurrence pprof
raw text, opened the benchmark target and localizer artifacts afterward, and
reimplemented Wilson prefix scoring and per-query AP.

## Population, coverage, and profile mass

The source and annotation populations are complete and one-to-one:

| Quantity | Independently observed |
|---|---:|
| Packet files | 8 |
| Annotation files | 8 |
| Sessions / queries | 536 |
| Source operations | 12,877 |
| Sparse Agent marks | 5,887 |
| Mapped target operations | 935 |
| Target-bearing queries used for per-query AP | 400 |
| No-target queries excluded from MAP | 136 |

For each of N0, N1, A0, and A1, direct `go tool pprof -raw` inspection found
12,877 sample rows, 12,877 distinct `evidence_id` values, and total operation
mass 12,877. The four profiles therefore compare exactly the same operation
population. Their stored unique-stack counts are 2,294 for N0, 633 for N1,
1,242 for A0, and 2,872 for A1; these are representation outcomes, not changes
in sample mass.

Sparse annotation legality also holds: every one of the 536 sessions has a
first mark at its first operation, all later marks reference existing
operations in strict order, complete paths are nonempty, adjacent marks change
the complete path, and expansion covers every operation exactly once.

## Independent metric reconstruction

For every method I counted the benchmark's frozen `localizer_hit` signal at
every semantic prefix, computed the 95% Wilson lower bound for that prefix,
assigned each operation the maximum score along its path, and computed
`sklearn.metrics.average_precision_score` within each target-bearing query.
The arithmetic mean over the 400 query APs gives:

| Organization | Independently recomputed MAP | Difference from stored |
|---|---:|---:|
| N0: native tree | 0.419329360321 | 0 |
| N1: recurrence tree | 0.193269892875 | 0 |
| A0: automatic Agent semantics | 0.283678412090 | 0 |
| A1: source-preserving automatic Agent | 0.413988731273 | 0 |
| Historical AgentProf | 0.452851577264 | 0 |

All 400 stored per-query rows matched independently recomputed AP exactly;
the maximum absolute difference was 0. The historical AgentProf reproduction
also exactly equals the registered value `0.45285157726449404`, with absolute
difference 0 rather than merely falling within the scorer's `1e-12` tolerance.

## Paired per-query uncertainty

I used a nonparametric paired bootstrap over the 400 target-bearing queries,
with 100,000 resamples and seed `20260722`. Each draw resamples complete query
AP pairs, so it preserves within-query operation dependence. The intervals
below are percentile 95% intervals; wins/ties/losses are exact query-level
counts before resampling.

| Contrast | Mean AP delta | 95% paired interval | Wins / ties / losses |
|---|---:|---:|---:|
| A1 - N0 | -0.005341 | [-0.021567, 0.010945] | 139 / 61 / 200 |
| A1 - N1 | +0.220719 | [0.196942, 0.244881] | 315 / 39 / 46 |
| A1 - A0 | +0.130310 | [0.114660, 0.146306] | 259 / 106 / 35 |
| A1 - historical | -0.038863 | [-0.054096, -0.023430] | 106 / 62 / 232 |
| A0 - N0 | -0.135651 | [-0.155783, -0.115819] | 82 / 22 / 296 |
| A0 - N1 | +0.090409 | [0.072497, 0.108830] | 254 / 56 / 90 |
| A0 - historical | -0.169173 | [-0.188149, -0.150296] | 60 / 18 / 322 |
| N0 - historical | -0.033522 | [-0.046180, -0.021136] | 128 / 63 / 209 |

These results make the interpretation unambiguous. Source preservation repairs
most of A0's HINT localization loss, but A1 is statistically indistinguishable
from N0 and remains below the historical AgentProf organization. A1's large
gain over A0 is evidence about retained source-call structure, not evidence
that the Agent's semantic names alone improve localization.

## A1 construction and target-dependence audit

A1 passes the requested exact construction audit:

1. For all 12,877 operations, the A1 group in `fixed-groups.jsonl` is exactly
   the complete A0 path followed by the two source-derived frames returned as
   `source_kind` and `source_call`/`tool`. There are zero exceptions.
2. The A0 and A1 mark files are byte-identical. Both have SHA-256
   `0126042b17269e211c914af29cf3664991b71acb09867948cbb6b142c5240a09`.
3. The two replay commands differ in stack selection as intended: A0 uses
   `project,operation`; A1 uses
   `project,operation,source_kind,tool`.
4. The shared source-operation rows contain only `agent`, `call`,
   `evidence_id`, `operation_id`, `project`, `prompt`, `session`,
   `source_kind`, `source_session`, and `tool`. They contain no target,
   `localizer_hit`, risk label, or judge output.
5. The implementation derives these leaves from `native_path` in
   `source_leaf_frames` and constructs all four complete method maps before it
   writes `fixed-groups.jsonl`. Only afterward does line 857 call
   `load_signals_after_groups`. The fixed file independently matches a fresh
   reconstruction from packets and annotations.

Thus A1 has no direct target dependence and does not change an A0 boundary,
name, or annotation. It is nevertheless a **post-A0 method correction**: the
plan explicitly says it was added after the A0 full result exposed the product
projection mismatch. That history does not invalidate the target-blind result,
but it limits confirmatory interpretation. A1 should be reported as the
corrected product projection and not as if it had been a predeclared method
chosen before observing A0.

## HINT zero-hit Wilson compatibility behavior

The scorer intentionally evaluates the Wilson formula directly for HINT,
including zero-hit prefixes, instead of canonicalizing them to exact `+0.0`.
I reproduced that behavior. Floating-point cancellation is actually signed,
not exclusively positive: observed zero-hit prefix values range from about
`-1.17e-17` to `+4.87e-17`. The numbers of positive-valued zero-hit prefixes
were 884 for N0, 149 for N1, 239 for A0, 1,334 for A1, and 1,000 for the
historical organization.

This compatibility behavior is correctly used by the stored run and is what
makes the historical MAP reproduce exactly. As a sensitivity check, forcing
all zero-hit Wilson bounds to exact zero leaves N0, N1, A0, and A1 MAP
unchanged, while historical MAP becomes `0.452372661964`, a decrease of
`0.000478915301`. Consequently:

- the current four-method conclusions are not artifacts of the zero-hit
  floating-point cancellation;
- exact historical reproduction does depend slightly on preserving the
  published behavior;
- the code comment saying cancellation leaves only "tiny positive values" is
  incomplete. Future reporting should call this the direct floating-point
  Wilson evaluation, with signed near-zero roundoff, rather than imply that all
  zero-hit bounds are positive. This is a reporting clarification, not a reason
  to rerun or invalidate the experiment.

## Correctness, fairness, and interpretation boundaries

- The metric is standard per-query AP/MAP, and targets do not define the
  semantic groups or prefix scores. The localizer signal scores already-fixed
  groups; gold risky steps are opened only to evaluate the ranking.
- Queries with no positive target are excluded because AP for an all-negative
  query is not the registered HINT per-query metric. Their operations still
  participate in the frozen group-level localizer statistics.
- N0, N1, A0, and A1 consume the same source population and are scored with
  identical prefix and tie behavior. N1 assignments parsed from its actual
  pprof match all 12,877 stored N1 fixed groups.
- Historical AgentProf is a retained, runnable same-workload comparator and is
  stronger than every new row on this metric. It must not be omitted when
  interpreting HINT merely because it is outside the four-row constructor
  matrix.
- A0 is a useful ablation showing what is lost when semantic operations replace
  rather than preserve source-call structure. It is not the correct final
  product configuration.
- HINT alone supplies one workload's evidence toward RQ2. It cannot establish
  end-to-end diagnostic usefulness, answer the complete RQ, or authorize a
  thesis/RQ/story rewrite.

## Required result wording

No code or rerun is required for validity. Before using this result in a paper
or aggregate RQ report, the wording should satisfy all of the following:

1. State that A1 significantly improves on A0 and N1, **matches rather than
   beats N0**, and remains below historical AgentProf on HINT.
2. Attribute the A1--A0 gain to retaining source-call structure beneath the
   same Agent semantic paths; do not attribute the full gain to better semantic
   segmentation.
3. Identify A1 as a target-blind post-A0 product-contract correction.
4. Describe HINT's zero-hit behavior as direct floating-point Wilson
   evaluation, not universally positive zero-hit bounds.
5. Keep the conclusion scoped to this complete HINTBench localization
   workload and its registered localizer signal.

## Formal result-review judgments

```text
run status: valid
tested hypothesis: inconclusive (supported versus N1; not established versus N0; below historical AgentProf)
research value: supporting
paper impact: additional RQ2 evidence and a source-preservation mechanism boundary
next paper decision: retain A1 as the product-aligned constructor; report HINT as parity with N0 and improvement over N1, not semantic-hierarchy superiority
```

There are no must-fix execution defects and no authorization for additional
HINT retuning. The remaining issue is scientific scope: this valid workload
does not provide the claimed superiority over the strongest native/historical
organizations, so broader RQ2 conclusions must rely on the other complete
registered workloads and product cases rather than reinterpreting this one.
