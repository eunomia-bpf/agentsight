# Step 0037 Report: Local-Evidence-Preserving Semantic Ranking

- started: 2026-07-17T05:22:37-0700
- completed: 2026-07-17T06:50:17-0700
- outer gates traversed: `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`
- selected RQ: RQ2 — Does profiler output correspond to real problems?
- final run status: valid
- registered tested hypothesis: inconclusive
- research value: supporting mechanism/workload boundary
- paper impact: compact, explicitly adaptive mechanism analysis
- thesis and RQs changed: no
- canonical submodule changed: no (`7f80c433c9555317a2aa45a78d0ff93518f4c12c`)

## Gate Entries, Skips, And Transitions

### EXPERIMENT_GATE

At entry the root read the repository instructions, complete
`docs/user-instruction.md`, complete `docs/idea-story.md`,
`docs/questions-for-author.md`, the RQ frontier in `docs/evaluation.md`, the
orchestrator skill and state-machine reference, and the complete experiment
skill. There were no open author questions. The selected RQ and single
candidate came directly from Step 0036's reviewed atomic/propagation boundary
and the user's instruction to improve the current algorithm on already-run
trajectories. Literature reopening was skipped because neither the frozen
thesis/RQs nor the mechanism's external conceptual basis changed; the node
reused the same public benchmarks, published diagnostic signals, and standard
ranking metric already source-checked in the parent experiment. The reviewed
valid result closed this experiment and transitioned to `WRITE_GATE` even
though its registered hypothesis was inconclusive, as required by the
experiment skill.

### WRITE_GATE

At entry the root reread the active user instructions, idea-story thesis and
fixed RQs, Step 0037 result review, current RQ2 section, and phase policy. The
targeted pass touched only the RQ2 result table/interpretation and the RQ2
frontier in `docs/evaluation.md`. Full `iter-refine-writing` was skipped because
the project is in `BUILD_AND_EVALUATE`, where full-paper rewriting and frozen
narrative edits are forbidden. `iter-refine-ideas` was skipped because the user
did not request an idea discussion in this node and the result changed no
problem, thesis, RQ, contribution, system direction, or story. No abstract,
introduction, motivation, design-goal, contribution, related-work, or
conclusion meaning changed. Full compilation and paper verification passed,
so the gate transitioned to `REVIEW_GATE`.

### REVIEW_GATE

At entry the root reread the complete user-instruction and idea-story files,
confirmed the scientific contract was unchanged, checked that the paper still
states the exact thesis and all four fixed RQs, and found no open author
question. A BOOTSTRAP root idea disposition was skipped because this is a
post-freeze `BUILD_AND_EVALUATE` step. A fresh subagent with no execution role
completed the required outer audit and meta-review using the orchestrator and
full-paper critique skills. The audit returned `PASS for Step 0037; not a
submission-acceptance PASS` and is persisted in
[`outer-audit-20260717T065017-0700.md`](outer-audit-20260717T065017-0700.md).
It found no defect requiring EXPERIMENT or WRITE re-entry. The step transitions
to the next `BUILD_AND_EVALUATE / EXPERIMENT_GATE` for the remaining RQ3
literal-phase evidence gap.

## Decision Entering The Step

Step 0036 established that the incumbent semantic grouping consistently beats
matched raw-action grouping under standard per-query AP/MAP and a fixed
operation budget, but direct operation-local scoring wins both measurements on
AgentProcessBench and exposes much less clean support on HINTBench. The user's
explicit direction was to improve the existing algorithm on already executed
trajectories, without replacing the paper story, changing the four RQs, adding
a benchmark, or creating a more complicated score.

Step 0037 therefore tested one parameter-free composition rather than another
feature or weight: preserve every strict operation-local score ordering and
use the existing semantic recurrence score only to refine exact local-score
ties. A matched local-plus-raw candidate uses the same composition with raw
action as its secondary key. The step did not change the thesis, RQ wording,
benchmark populations, localizers, source scores, profile hierarchy, cutoff,
or metric.

## Approved Experiment

The reviewed plan is
[`experiment-plan.md`](01-experiment-gate/experiment-001/experiment-plan.md).
Both serial review rounds are retained in
[`plan-review.md`](01-experiment-gate/experiment-001/plan-review.md).

Round 1 required four corrections before execution:

1. make the later user authorization explicitly supersede the earlier score
   freeze only for this candidate;
2. disclose that the candidate was selected after inspecting Step 0036;
3. state the exact all-workload MAP support rule; and
4. name the real inputs, rank canonicalization, seeds, outputs, leakage checks,
   and clean-support predicates.

After those corrections, the same independent reviewer returned
`APPROVED FOR REAL PREFLIGHT` with no blocking defect. The planned full
population was unchanged:

| Benchmark | Trajectories | Operations | Target-bearing | Clean |
|---|---:|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 614 | 386 |
| HINTBench | 536 | 12,877 | 400 | 136 |
| TraceElephant | 220 | 5,960 | 220 | 0 |
| **Total** | **1,756** | **27,346** | **1,234** | **522** |

The primary measurement remained standard non-interpolated AP per
target-bearing trajectory and arithmetic workload MAP. Exact-K analytic
tie-averaged Recall@20% remained a secondary fixed-budget analysis: Recall@K
is a standard ranking family, but the 20% budget and tie protocol are declared
experiment choices rather than an official benchmark metric. Clean-support
propagation remained an algorithm-property check, not a performance metric.

## Implementation And Real Preflight

The implementation is
[`script/rq2_local_first_semantic_ranking.py`](../../../../script/rq2_local_first_semantic_ranking.py).
It reuses the already reviewed Step 0036 loaders, score canonicalization,
standard AP implementation, exact-budget tie calculation, and clustered
bootstrap. The pure rank-key constructor accepts only three target-free
inputs: local score, semantic score, and raw-action score. It cannot accept a
target, correctness field, gold label, or target identifier. Equal tuples
remain tied, and tuple ordinals are independent of source row order.

One real preflight used three target-bearing trajectories plus one
AgentProcessBench clean trajectory and one HINTBench clean trajectory. It
exercised all four ranking paths, both measurements, strict-order preservation,
tie preservation, Step 0036 reproduction, clean-support identity, and persisted
rank-key inspection. All checks passed, so the full run proceeded without a
plan change.

## Full Execution History

The first full invocation returned exit status zero but produced no result
files. It is recorded as an empty attempt, not as a run. A separate ten-draw
execution under `/tmp/rq2-local-first-debug` then checked only that the full
path completed; its coarse verdict is not a paper result and is not cited.

The authoritative full invocation subsequently completed with 10,000 draws
for every workload/measurement/baseline comparison. Its raw root is:

```text
.agentsight/experiments/rq2-local-first-semantic-ranking-v1/full/
```

Final hashes are:

| Artifact | SHA-256 |
|---|---|
| `summary.json` | `b1b85841dc90ee0d89e43899f94d15e6a140ef169d04f6d876344ea5c58c7ae6` |
| `per-query.jsonl` | `a8d42c1a86cc703e658a90232a6b0d5bc2301380b61af2acf3b45cd5326a58b6` |
| `rank-keys.jsonl` | `7f852a01f5d4697d5121f06ca7bfc8fcaffe0208a324eff5208ec7e8f3d90b63` |
| `rank-key-mappings.json` | `c86cf02e4dd089934bb10edaa8f0edbaa94596c8ae423b66e0068e1d654e4405` |
| `bootstrap-deltas.json` | `e0e5671b8f1eef0e60c2850e8d8b59492d6081e1994bb37728c9b7389be84447` |
| `report.md` | `4b81f364b9f4c3f4fe83d35466291b29e09779b1f88e1dcf8dbc98586954c57c` |

## Independently Reviewed Results

The fresh read-only result reviewer reconstructed every rank component and
tuple, all 27,346 rank rows, all 1,234 AP and exact-budget Recall values, the
Step 0036 baselines, and all 180,000 bootstrap draws from the source roots. The
formal review is
[`result-review.md`](01-experiment-gate/experiment-001/result-review.md).

| Workload | Ranking | MAP | Expected Recall@20% |
|---|---|---:|---:|
| AgentProcessBench | local + semantic | 0.895972 | 0.661047 |
|  | local + raw | 0.893071 | 0.660402 |
|  | local only | 0.863171 | 0.651185 |
|  | semantic only | 0.788919 | 0.562766 |
| HINTBench | local + semantic | 0.544906 | 0.628065 |
|  | local + raw | 0.505961 | 0.615060 |
|  | local only | 0.410559 | 0.548394 |
|  | semantic only | 0.452373 | 0.574109 |
| TraceElephant | local + semantic | 0.321905 | 0.495422 |
|  | local + raw | 0.249353 | 0.415774 |
|  | local only | 0.208713 | 0.332129 |
|  | semantic only | 0.230168 | 0.457529 |

Primary MAP effects for local-plus-semantic are:

| Workload | Versus local + raw | Versus local only | Versus semantic only |
|---|---:|---:|---:|
| AgentProcessBench | +.002900 [-.000497,+.006852] | +.032801 [.024421,.042081] | +.107052 [.088462,.126437] |
| HINTBench | +.038945 [.029118,.048908] | +.134348 [.121196,.147153] | +.092534 [.077050,.109587] |
| TraceElephant | +.072552 [.049844,.097053] | +.113192 [.086972,.141692] | +.091736 [.058967,.126763] |

The registered hypothesis required the candidate-minus-local-plus-raw MAP
interval to be wholly positive on all three workloads. HINTBench and
TraceElephant pass; AgentProcessBench crosses zero. The exact verdict is
therefore `INCONCLUSIVE`, not supported. No interval is wholly negative.

Candidate clean support equals local-only support operation-by-operation by
construction: 8/2,459 AgentProcessBench clean operations and 25/3,368 HINTBench
clean operations. That identity verifies the local-first construction; it does
not independently establish specificity.

## Scientific Interpretation

The admitted conclusion is:

> On these previously observed complete populations, preserving local order
> and using semantic recurrence only for exact local-score ties improves over
> local-only and incumbent semantic-only ranking on all three workloads. It
> beats a composition-matched raw-action tie refinement on HINTBench and
> TraceElephant, while AgentProcessBench does not distinguish the two
> refinements.

This is a simple mechanism result: semantic recurrence is useful as a
refinement of otherwise-equal local evidence, not as permission to override
stronger local evidence. Because the candidate was chosen after inspecting
Step 0036 outcomes on the same populations, the result is explicitly adaptive
and cannot be presented as untouched generalization. It does not authorize a
universal algorithm replacement, an all-workload superiority claim, lower
human work, higher specificity, or another round of score tuning.

## Write-Gate Integration

The project evaluation memory now records the final reviewed result and closes
the candidate as a universal replacement. It also marks Step 0033's pre-zero-
canonicalization HINT values as superseded by the authoritative Step 0036
result. `docs/design.md` records the resulting principle---semantic grouping
may refine otherwise-equal local evidence but should not override stronger
local evidence---without introducing a third abstraction or adopting the
candidate universally. `docs/implementation.md` records the three completed
evaluation adapters and that the Step 0037 candidate is evaluation-only rather
than the Rust release ranking path. The paper keeps the Step 0036
semantic-versus-raw table as the confirmatory RQ2 result and adds only one
compact post-hoc mechanism paragraph. That paragraph reports the local-first
MAP values, the local-only and semantic-only comparators, the two positive
matched local-plus-raw effects, and the AgentProcessBench indistinguishable
effect. The earlier nonstandard LLM-reader description was removed from the
seven-page paper, leaving standard AP/MAP as the RQ2 primary metric. The
abstract, introduction, thesis, four RQs, system story, contribution list, and
submodule were not changed by Step 0037.

The prior rounded HINT and Trace table values were also corrected to the final
Step 0036 reconstruction: HINT `0.452` with interval `[.154,.188]`, and Trace
interval `[.077,.142]`.

## AAAI 2027 Format Verification

`make -C docs/paper` completed successfully after the write integration.
The final PDF at this point has SHA-256
`08a9a3c9683723bafaceb07922009fe3b424ae2e6aac1fba3771eff7eefcc783`.

- template: local `aaai2027.sty` with `\usepackage[submission]{aaai2027}`;
- author: `Anonymous Submission`;
- paper size: letter, 612 x 792 points;
- total pages: 9;
- main content ends on page 7;
- page 8 and page 9 contain references only;
- undefined citations/references: none;
- overfull boxes: none; and
- page 7 was visually inspected; no clipping or overlap was found.

## Outer Audit, Meta-Review, And Routing

The fresh outer audit covers the experiment, targeted write, complete paper,
canonical intent and story, metric classification, and AAAI format. It confirms
that Step 0037 is complete and valid, that the paper's exact thesis and four RQs
did not drift, and that the reader-facing paragraph stays within the independent
result review's authorization. It also confirms that standard AP/MAP is the RQ2
primary metric, while Recall@20%, weighted B-cubed, and clean-support checks are
correctly classified as secondary protocol, adapted measurement, and algorithm
property respectively.

The audit's meta-review findings are:

- **Direction:** the original ambitious story remains intact; the candidate
  clarifies a simple mechanism without becoming a new contribution or thesis.
- **Efficiency:** reusing complete trajectories was high value, and another
  RQ2 score, metric, cutoff, or benchmark on these populations would be waste.
- **Maintenance:** no new skill or repository rule is justified. Canonical
  evaluation memory remains longer than the preferred current-frontier form;
  stale history should be archived later through minimal housekeeping rather
  than another research gate. This step already repairs the concrete stale
  Step 0033 HINT authority, advances `Next Evidence Selection` through Steps
  0036/0037 and RQ3 routing, and updates current design/implementation reality.

## Ranked Open Paper Objections

1. **RQ3 phase-tag evidence remains partial.** The fixed RQ3 hypothesis names
   task, phase, action, and boundary identity. Current evidence covers task,
   action, partitions, and boundaries but not a complete literal phase-tag
   evaluation on an official annotated population. This is the next
   paper-decision blocker and routes to one RQ3 experiment.
2. **Final novelty pressure remains.** Once RQ3 closes, a genuinely unprimed
   milestone review must compare the complete contribution against primary
   sources for cross-trace aggregation and agent observability. It must test
   whether additive system-effect linkage, query-time operation stacks, and
   standard profiler output form a substantive contribution rather than
   metadata grouping exported to pprof.
3. **Local evidence is a competing explanation, not a Step 0037 defect.** The
   complete adaptive result now exposes where semantic tie refinement matters.
   This objection does not authorize story shrinkage or more RQ2 tuning.

None of these objections invalidates Step 0037's experiment, write integration,
or transition.

## Next Step

Enter `BUILD_AND_EVALUATE / EXPERIMENT_GATE` for exactly one RQ3 experiment
addressing literal phase-tag accuracy. Prefer an existing official public
corpus with phase annotations, its complete released population, one
appropriate standard metric, and a small fair baseline set. The experiment may
improve the mechanism or adapter but may not change the RQ, thesis, story, or
contributions. Apply only targeted WRITE updates after independent result
review. Do not reopen RQ2 score tuning on the three observed populations.

## Git Persistence Recovery

At this step boundary, completed Step 0035 and Step 0036 reports, their three
evaluation scripts, and their interdependent paper/evaluation edits were still
uncommitted in the inherited worktree. Safely separating their already-mixed
tracked hunks after the fact would risk rewriting accepted paper state. The
root therefore publishes the accumulated Steps 0035--0037 as one coherent
recovery commit at this boundary, without touching the canonical submodule.
Subsequent steps return to one commit per completed outer step. This Git
recovery has no role in any scientific gate verdict.
