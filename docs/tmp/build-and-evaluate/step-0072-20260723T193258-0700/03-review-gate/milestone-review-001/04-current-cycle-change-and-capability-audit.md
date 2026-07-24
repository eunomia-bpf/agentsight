# Current-cycle change and capability audit

## Audit scope

This report was written only after the blind review, external primary-source
check, and source-grounded full-paper assessment were complete. It audits Step
0072 itself:

- the step entry and baseline audit;
- the approved experiment plan and two independent plan reviews;
- the real preflight;
- the full-run report and independent result review;
- the implemented scorer and retained output artifacts;
- the targeted write outline/report;
- the resulting RQ2 paper text and synchronized evidence/story records.

No Git history or diff was used. The paper, project idea, user instructions,
and canonical memory were treated as read-only during this review.

## Executive finding

**The Step 0072 experiment is technically and statistically credible, and the
information-matched raw-action baseline is the correct control.** The cycle
should be retained as a successful corrective experiment.

**The result does not close the paper-level RQ2 objection.** Local+AgentProf
clearly improves over Local-only, but Local+Raw+Evidence produces statistically
indistinguishable MAP on every workload. The experiment therefore shows that a
group/evidence refinement complements a tied local score; it does not show
that the AgentProf semantic-operation prefix is responsible for that value.

The cycle is thus:

- **PASS** as an experiment execution and evidence correction;
- **PARTIAL SUPPORT** for the registered hypothesis;
- **FAIL** as proof of semantic-hierarchy-specific downstream benefit;
- **not sufficient** for whole-paper acceptance.

## What Step 0072 actually changed

### Experiment capability

The new scorer evaluates four ranking configurations:

1. `Local+AgentProf`;
2. `Local+Raw+Evidence`;
3. `Local only`;
4. `AgentProf only`.

Both local-first configurations preserve all strict local-score orderings and
may only refine exact ties. The raw control replaces the candidate's semantic
prefix with a normalized raw-action identity while retaining:

- the same task-family/root scope;
- the same three source-evidence suffix frames;
- the same local diagnostic score;
- the same workload-specific aggregation;
- the same prefix scoring rule;
- the same candidate population and AP/MAP scorer.

This is the key scientific capability added by the cycle: it separates the
semantic prefix from the source evidence that previous comparisons bundled
with it.

### Paper changes

The RQ2 body subsection now:

- describes the local-first lexicographic design;
- reports all four MAP columns;
- exposes paired intervals against Local-only;
- exposes paired intervals against Local+Raw+Evidence;
- states that semantic-prefix superiority is not established;
- declares the evidence adaptive rather than untouched.

The cycle also corrects CodeTrace A2 provenance from an incomplete
Qwen3.6-27B branch to independent Codex Agent batches plus root validation.
The evidence ledger, related-work/background ledger, and idea-story note were
synchronized.

### Changes deliberately not made

The write gate intentionally did not update:

- title;
- abstract;
- introduction;
- motivation;
- contribution list;
- thesis;
- four RQs;
- conclusion;
- section structure.

That narrowness protected the scientific story during the experiment, but it
also leaves headline statements inconsistent with the new strongest control.

## Reproduction and implementation audit

### Population and joins

The retained full output reports:

| Workload | Trajectories | Operations | Target-bearing queries |
|---|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 614 |
| HINTBench | 536 | 12,877 | 400 |
| TraceElephant | 220 | 5,960 | 220 |
| **Total** | **1,756** | **27,346** | **1,234** |

All 522 zero-positive trajectories are retained for coverage accounting and
excluded from AP/MAP. Exact one-to-one `operation_id` joins are enforced.
Duplicate IDs, missing IDs, population drift, and incumbent reproduction
fail hard.

**Audit judgment:** sound.

### Target-blind boundary

The implementation constructs all score vectors before calling the label
loader. Its ranking constructor receives source rows, fixed operation paths,
local scores, and raw identities but not correctness labels. The preflight and
independent review both verify this boundary.

This does not make the full protocol untouched: the paths, local-first rule,
field choices, and three populations were observed in prior development. The
paper now accurately calls the result adaptive mechanism evidence.

**Audit judgment:** no direct label leakage found; adaptivity correctly
disclosed.

### Information parity

For each operation, `source_suffix` verifies that the source-preserving
candidate is a strict extension of the automatic semantic path and extracts
exactly three suffix frames. The raw control uses:

`task family -> raw action -> identical suffix`.

The candidate uses:

`task family -> semantic operation(s) -> identical suffix`.

Both are passed to the same group-scoring function. This is a strong and fair
control for the question “does the semantic prefix help after local score and
source evidence are held fixed?”

The paths are not equal in granularity or depth, but that is not a fairness
defect: granularity and depth are part of the proposed semantic mechanism. A
matched-depth synthetic control could be a useful mechanism probe, but it
cannot replace the information-matched raw control.

**Audit judgment:** scientifically appropriate and should remain in the
paper.

### Rank semantics

Distinct lexicographic keys are converted to monotonically increasing ordinal
scores. `validate_local_order` confirms that every tier associated with a lower
local score ranks below every tier associated with the next higher local
score. Identical keys receive identical ordinals, so the AP implementation
handles tied keys consistently.

This operationalizes the plan correctly: group scores refine exact local-score
ties and cannot override strict local evidence.

**Audit judgment:** sound.

### Metric and inference

The scorer uses `sklearn.metrics.average_precision_score` per target-bearing
trajectory and arithmetic mean MAP per workload. It performs 10,000 paired
resamples using pre-existing workload-specific strata/clusters.

The retained artifacts reproduce:

| Workload | Local+AgentProf | Local+Raw+Evidence | Local only | AgentProf only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .8943 | .8931 | .8632 | .7906 |
| HINTBench | .5175 | .5180 | .4106 | .4324 |
| TraceElephant | .3255 | .3239 | .2087 | .2593 |

Candidate-minus-Local intervals are wholly positive:

- AgentProcessBench: +.0311, 95% interval [.0237, .0393];
- HINTBench: +.1069, [.0934, .1204];
- TraceElephant: +.1168, [.0876, .1479].

Candidate-minus-matched-raw intervals all contain zero:

- AgentProcessBench: +.0012, [-.0003, .0029];
- HINTBench: -.0005, [-.0116, .0103];
- TraceElephant: +.0016, [-.0247, .0280].

The independent reviewer reconstructed every AP, MAP, point difference,
bootstrap draw, interval, population count, and incumbent result from separate
inputs. The only report correction concerned comparison-specific seed
derivation and did not alter any decision.

**Audit judgment:** execution and recomputation are strong. However, AP/MAP is
an AgentProf reformulation rather than the official primary outcome of these
three benchmarks. This limits paper-level construct validity even though the
calculation is correct.

### Tests and validation

The write report records:

- Python compilation: pass;
- seven canonical-tag comparison tests: pass;
- full scorer replay: pass;
- complete independent numerical reconstruction: pass;
- LaTeX build: pass;
- visual inspection: pass.

The seven named unit tests exercise the predecessor canonical-tag comparison
module, not the new `rq2_current_agent_local_first.py` scorer. The new scorer
has extensive runtime assertions and unusually strong independent
recomputation, so this does not invalidate the result, but the test report
overstates direct unit coverage. Future maintenance should add focused tests
for:

- suffix extraction and parity failure;
- raw-path construction;
- local-order preservation;
- tied-key handling;
- zero-positive exclusion;
- stratified/clustered resampling;
- label-load ordering.

**Audit judgment:** adequate for the current numerical result, with a
maintenance/test-reporting correction.

## Scientific interpretation audit

### Claim supported by this cycle

The exact claim supported is:

> On three previously observed complete public workloads, adding either an
> AgentProf or information-matched raw-action/source-evidence group score to
> refine exact ties in a fixed local diagnostic score raises MAP over the local
> score alone; the experiment does not detect a semantic-prefix advantage.

The candidate-minus-local improvements are real. But because the raw/evidence
control achieves the same result, the most conservative causal inference is
that retained evidence and group-level tie refinement add value. The current
data do not attribute that value to semantic names, recursive hierarchy, or
cross-run shared responsibility.

### Over-interpretation remaining in the RQ2 body

The new body says:

> “Thus the profile adds clear ranking information to a fixed local diagnostic
> signal...”

and later:

> “It instead establishes the practical composition used by AgentProf:
> operation profiles complement local diagnosis, retain source evidence, and
> provide the cross-run hierarchy and drilldown...”

The first statement is acceptable if “profile” means the complete
Agent+Evidence configuration. The second sentence joins an experimentally
supported ranking-composition result to hierarchy/drilldown capabilities that
were not shown to cause the MAP gain. It should explicitly say:

> The matched result attributes the ranking gain to group/evidence refinement
> in the complete profile, not specifically to its semantic prefix; hierarchy
> and drilldown are separate representation capabilities.

### Headline inconsistency left by the narrow write gate

The abstract still says:

- declared semantic hierarchy improves MAP over raw action in all three;
- automatic Agent+Evidence improves over raw action on every workload;
- canonical renaming alone improves HINT while intervals include zero on the
  other two.

The introduction repeats older AgentProf-only versus raw-action MAP numbers and
the contribution list says automatic operation structure improves ranking over
raw action on all three workloads. The conclusion again says AgentProf
improves localization MAP over raw action on all three.

Those older comparisons may remain as ablations, but they are no longer the
strongest causal test. A reasonable reader will interpret the headlines as
semantic-hierarchy superiority, while Step 0072 finds no advantage after
evidence is matched. This is a **whole-paper blocker**.

### “RQ2 closed” is too strong

The cycle closes the registered local-first experiment on these three reused
populations. It does not close the paper-level question “does profiler output
correspond to real problems?” because:

- the official benchmark outcomes are not jointly reported;
- no direct review-time or decision outcome is measured;
- semantic hierarchy is not separated from evidence/grouping;
- no untouched family confirms the effect;
- current adjacent work reports direct review or intervention outcomes.

The correct project-memory state is: **this exact scoring branch is closed; the
paper-level evidence frontier moves to a different outcome or untouched
population.**

## Baseline and closest-work audit

The cycle correctly rejected forced numerical adapters for Hodoscope,
TraceProbe, AgentRx, AgentLocate, and HarnessFix when their native outputs do
not match the Step 0072 operation-score contract. It is good scientific
practice not to fabricate incompatible baseline numbers.

However, this does not discharge the whole-paper comparison burden:

- Hodoscope is directly relevant to human review of cross-run behavior.
- Graphectory and TraceGraph establish intervention/recovery consequences.
- Datadog Patterns and LangSmith Insights establish hierarchical population
  grouping, rollups, and drilldown.
- ACT*ONOMY is a missing closest hierarchical action-profile baseline.
- Official metrics from AgentProcessBench, HINTBench, and TraceElephant are
  needed beside MAP.

These can be handled through native-outcome comparisons, capability matrices,
artifact imports, or a new decision-level experiment. They need not be
distorted into the current scorer.

## Compliance with the fixed thesis and user instructions

The cycle appropriately preserved:

- the paper thesis;
- all four RQs;
- the ambitious semantic-profiling scope;
- the non-zero-objection standard;
- the instruction not to shrink claims merely because one mechanism test is
  inconclusive.

The matched tie should not trigger default shrinkage to “pprof export.” It
should trigger stronger evidence where semantic cross-run aggregation ought to
matter. This is exactly an **evidence expansion** problem.

The cycle also obeyed the one-hypothesis scope: it did not mix RQ3 or RQ4
execution into RQ2. The A2 provenance edit was a factual correction, not an
extra experiment.

## Cycle findings by severity

| Finding | Severity | Disposition |
|---|---:|---|
| Exact score construction, joins, and independent recomputation | pass | Retain |
| Local+Raw+Evidence is information-matched and fair | pass | Retain as mandatory control |
| Registered hypothesis receives partial support | pass with limitation | Report exactly |
| No semantic-prefix advantage on any workload | blocker for paper-level claim | Route to new outcome/family, not retuning |
| Headline sections retain weaker raw-action-win framing | blocker | Repair after next experiment or immediately as factual consistency |
| Adaptive populations and rules | major | Keep scope disclosure; require untouched confirmation |
| MAP differs from official benchmark outcomes | major | Add official metrics and construct validation |
| RQ2 body causally joins ranking value with hierarchy/drilldown | major | Separate consequence from capability |
| Closest work not numerically forced into incompatible scorer | pass | Keep |
| ACT*ONOMY and product capability comparison absent | blocker/major | Add in next write after source-grounded audit |
| Unit-test list is mostly for predecessor module | minor | Add direct scorer tests; correct report wording |
| 12-page build | submission blocker | Resolve after science stabilizes |

## Cycle verdict

### Experiment execution

**PASS.**

### Registered hypothesis

**PARTIAL SUPPORT**, exactly as the independent result review states.

### Write gate

**PARTIAL PASS.** The RQ2 body and evidence ledgers accurately expose the
matched non-result, and the A2 provenance correction is valuable. The chosen
scope deliberately leaves abstract/introduction/contribution/conclusion
inconsistency, so the manuscript as a whole is not yet sound.

### Paper-level capability established

AgentProf can compose source evidence with a local diagnostic signal and use
group scores to refine ties. Step 0072 does not establish that semantic
operation identity is better than raw action for this ranking task.

### Next route

**EXPERIMENT_GATE**, not another RQ2 score/ranker retuning cycle. The next
experiment should use a different, consequential outcome or untouched
population where cross-run semantic aggregation is essential. In the fixed
outer sequence, RQ3 untouched automatic-operation validation is the cleanest
immediate next node, followed by RQ4 end-to-end annotation cost. A later RQ2
decision-level study remains necessary for the strongest paper.
