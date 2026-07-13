# Independent AgentNet FULL result review

**Review method:** `research-experiment-design`

**Review mode:** independent and read-only

**Execution disposition:** `VALID`

**Tested-construction verdict:** `CONTRADICTED`

**Execution must-fix:** zero

**Paper/story/RQ/thesis change authorized:** no

**Next transition:** remain in EXPERIMENT and propose a fresh RQ2 experiment

The reviewer reread the complete current experiment-design skill, Revision 4
plan, all plan/implementation/source/preflight/repair reviews, the full script
and 11-test suite, the complete FULL report, and current machine outputs. It
modified no file or branch.

`CONTRADICTED` has one narrow meaning: the current AgentNet construction—groups
defined by `domain, application, phase, action, repeat_state` and ranked by
mean transferred risk—does not satisfy the predeclared AP hypothesis. It does
not imply that semantic profiling is ineffective, that RQ2 failed, or that the
AgentProf thesis or four-RQ structure should shrink.

## Independent execution reconstruction

### Complete population

| Quantity | Windows | Darwin | Total |
|---|---:|---:|---:|
| Released trajectories | 12,427 | 5,198 | **17,625** |
| Unique task IDs | 12,364 | 5,168 | **17,532** |
| Operations | 239,710 | 99,295 | **339,005** |
| Positive labels | 38,565 | 16,653 | **55,218** |
| Negative labels | 201,145 | 82,642 | **283,787** |
| Unresolved | 0 | 0 | **0** |
| Label coverage | 100% | 100% | **100%** |

Independent line counts, operation IDs, and projection/label joins agree.
Repeated task rows remain separate released trajectories, while bootstrap
clustering uses original task IDs exactly as Revision 4 requires.

### Predictor and target-label boundary

Both folds have `target_label_input=null`. Predictor inputs are only the visible
projection and reference-platform labels; the predictor CLI has no target-label
argument. Both use seed 4204, the four fixed pure helpers, and
`legacy_normalize_agentnet_used=false`. Windows→Darwin converges in 18 of 1,000
maximum iterations and Darwin→Windows in 12 of 1,000.

### Real AgentProf

The binary and reports identify exactly `agentpprof 0.2.37`. Independent full-
population comparison among profile stack dictionaries, assignments, and group
summaries finds:

- all five views exact;
- every operation assigned to exactly one group in each view;
- identical group keys, operation counts, risk sums, and densities;
- zero maximum independent discrepancy;
- 99,295 Darwin and 239,710 Windows operations reconstructed.

### Bootstrap

Each fold contains one header and 50,000 attempt specifications. The task IDs
are unique, sorted, and equal to assignment clusters; attempts 0 through 49,999
are continuous; every draw seed matches the predeclared SHA-256 derivation.
Each scorer examines 10,240 attempts because it works in fixed 512-attempt
batches, then retains the first 10,000 valid paired draws. The effect rows are
exactly attempts 0 through 9,999. No seed or draw was refreshed after labels.

### Artifact and numerical reconstruction

All six pre-score artifacts in both folds—12 SHA-256 values total—remain
unchanged after target scoring. The reviewer independently reimplemented the
complete tie-block metric from labels, assignments, risks, and group keys rather
than calling the evaluation script's metric functions:

- maximum base-metric discrepancy: 0;
- maximum base-effect discrepancy: 0;
- maximum 10,000-draw percentile-interval discrepancy: 0;
- regenerated attempts 0 and 9,999 in each fold: all effects discrepancy 0;
- current regression suite: 11/11 pass.

No implementation or execution defect was found.

## Independently recomputed verdict

| Target | Effect | Point effect | 95% interval |
|---|---|---:|---:|
| Windows | semantic − raw AP | -0.010947 | **[-0.013612, -0.008404]** |
| Windows | semantic − raw recall@30 | -0.007831 | [-0.010696, 0.000949] |
| Windows | raw − semantic work-to-50 | +0.032931 | **[0.026254, 0.038707]** |
| Windows | semantic − ungrouped AP | -0.006773 | **[-0.008753, -0.004886]** |
| Darwin | semantic − raw AP | -0.005386 | **[-0.007675, -0.002635]** |
| Darwin | semantic − raw recall@30 | +0.002342 | [-0.008014, 0.011383] |
| Darwin | raw − semantic work-to-50 | +0.018611 | **[0.008931, 0.028578]** |
| Darwin | semantic − ungrouped AP | -0.008962 | **[-0.010687, -0.006901]** |

Both platforms have adverse zero-excluding semantic AP intervals against raw
action and ungrouped risk, so predeclared `CONTRADICTED` condition (b) holds.
Condition (a) does not hold because semantic work-to-50 is significantly better
than raw action in both folds. The machine verdict is exact.

## Why AP falls while work-to-50 improves

The metrics summarize different portions of the ranking:

- work-to-50 asks only when cumulative positives first reach 50%, and is
  sensitive to group boundaries;
- AP evaluates precision across the complete positive-recall trajectory, so
  poor ordering after the 50% crossing continues to reduce the score.

The current semantic construction places enough positives into early groups to
cross 50% after 3.293 fewer Windows inspection-work percentage points and 1.861
fewer Darwin points. The remaining full ranking is worse, lowering AP. Neither
recall@30 interval excludes zero, which is consistent with early concentration
without a general full-ranking improvement.

### Exact-density ties are not the cause

| Target | View | Operations in exact-density ties |
|---|---|---:|
| Windows | semantic | 285 / 239,710 |
| Windows | raw action | 44 / 239,710 |
| Darwin | semantic | 185 / 99,295 |
| Darwin | raw action | 2 / 99,295 |

These populations are too small to explain the AP gaps; the complete-tie-block
policy is not the mechanism.

## Main construction defect: dropping `target`

The compared keys are:

```text
raw action: action → target → repeat_state
semantic:   domain → application → phase → action → repeat_state
```

The semantic construction adds domain, application, and phase but removes
target, even though the transferred-risk model uses target as a categorical
predictor of operation correctness and redundancy.

| Diagnostic | Windows | Darwin |
|---|---:|---:|
| Semantic groups spanning multiple targets | 3,761 / 8,332 | 2,708 / 6,176 |
| Operations in multi-target semantic groups | **86.43%** | **86.27%** |
| Maximum targets merged by one semantic group | 147 | 102 |

Thus more than 86% of operations receive a density averaged across different
targets. This smooths target-specific risk that the predictor retains.

Semantic has more groups than raw action—8,332 versus 3,174 on Windows and
6,176 versus 2,220 on Darwin, with median size two in every case—but greater
cardinality does not preserve the relevant information. The semantic partition
is finer on domain/application and coarser on target. Neither partition nests
the other, so the current experiment validly evaluates the whole construction
but cannot causally separate context value, target omission, averaging, and
hierarchy value. Target omission plus density averaging is the strongest
evidence-backed mechanism.

## What the source-native control shows

Source-native uses:

```text
system → domain → application → session → action
```

| Target | Source-native AP | Semantic AP | Raw AP | Source-native work-to-50 |
|---|---:|---:|---:|---:|
| Windows | 0.271543 | 0.269660 | 0.280606 | 0.311710 |
| Darwin | 0.265536 | 0.264431 | 0.269817 | 0.316934 |

Its AP is slightly above semantic but below raw and ungrouped, while its work-
to-50 is slightly better than semantic. Yet inclusion of session produces
49,982 Windows and 21,536 Darwin groups and does not represent recurring cross-
run semantic aggregation. This implies that finer, session-specific partition
can restore some AP and that work-to-50 improvement is not uniquely evidence
for semantic hierarchy; granularity and threshold crossing also contribute.

## Problem classification

### Implementation defect

None found. Source, boundary, AgentProf, artifact invariance, bootstrap,
metrics, intervals, and tests are all exact.

### Experiment-design limitation

The experiment validly tests its predeclared complete construction. However,
raw and semantic change several fields simultaneously: adding
domain/application/phase, dropping target, and changing cardinality and
averaging. It cannot identify the causal value of semantic context itself.
This is a mechanism-identification limitation, not an invalid execution.

### Method/construction defect

This has the strongest evidence. Removing target makes most semantic groups
average over label-relevant local distinctions. The next construction should
preserve all raw local fields, for example:

```text
domain → application → phase → action → target → repeat_state
```

This makes semantic context a true refinement of the raw grouping instead of a
simultaneous substitution.

### Dataset/estimand mismatch

AgentNet measures step-level incorrectness and redundancy. Operation-weighted
AP naturally rewards target-specific local ordering. A semantic hierarchy is
also intended to expose recurring responsibility, failure scope, and coarse-
to-fine navigation, which this estimand does not completely measure. AgentNet
remains a real, public, valid RQ2 dataset; the defensible conclusion is that the
current construction and estimand do not align, not that the dataset or RQ is
invalid.

## Constraints on the next experiment

Windows and Darwin annotations have now been observed. A stack, ranking rule,
or navigation policy selected in response cannot be retested on those same
targets and presented as confirmatory. AgentNet may be used only as development
or reference-side data for the next construction.

The next confirmatory design should:

1. retain raw action, target, and repeat state in the semantic leaf;
2. add semantic context as a nested refinement rather than removing local
   fields;
3. fix at most one coarse-to-fine navigation policy without target-label grid
   search if hierarchical navigation is tested;
4. evaluate the fixed construction on an untouched public, real-agent failure-
   localization family with its complete population;
5. preserve raw-action and ungrouped-risk baselines; and
6. keep the bold positive RQ2 goal of more accurate localization with less
   inspection work.

Who&When or TRAIL are possible external families only if their target
annotations have never entered prior analysis. If either has been read, a new
public family is required.

## Transition decision

The current AgentNet loop has completed:

```text
FULL RUN → RESULT REVIEW
```

It remains as auditable construction-level history. The next action is not
WRITE and not a paper change. Return to the EXPERIMENT gate in a new directory:

```text
fresh RQ2 PROPOSE
→ serial REVIEW
→ REAL PREFLIGHT
→ complete FULL RUN
→ independent RESULT REVIEW
```

The new plan must not overwrite the AgentNet plan or use the observed AgentNet
targets as confirmatory evidence.
