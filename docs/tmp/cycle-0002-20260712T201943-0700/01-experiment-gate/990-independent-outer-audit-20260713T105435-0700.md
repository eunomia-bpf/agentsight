# Independent Outer Audit: Cycle 0002 EXPERIMENT Gate

**Node:** `990-independent-outer-audit-20260713T105435-0700`  
**Timestamp:** 2026-07-13T10:54:35-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Cycle:** `cycle-0002-20260712T201943-0700`  
**Gate:** EXPERIMENT  
**Parent:** `01-experiment-gate`  
**Role:** independent read-only outer auditor  
**Status:** COMPLETE  
**Verdict:** **REPAIR CURRENT GATE**

The experimental evidence is sufficient to choose the next scientific action,
and no experiment should be rerun. The only gate-blocking defect is a bounded
canonical-memory repair: `docs/background-related-work.md` still presents
CodeTraceBench as the next RQ2 experiment and omits the completed CodeTraceBench,
ToolSafe, AgentNet, and two AgentProcessBench branches. That stale search
frontier conflicts with the current decision in `docs/evaluation.md` and could
cause a resumed agent to repeat completed work. Repair that canonical frontier,
then perform a fresh outer verification before writing `999-gate-report` and
transitioning to WRITE. The result artifacts themselves remain valid under the
classifications below; this verdict does **not** request another experiment.

## Audit Question And Entry Condition

The audit asks whether the current EXPERIMENT gate is ready to transition to
WRITE after independently checking:

1. the exact user thesis and four fixed RQs;
2. every Markdown node under this gate;
3. the literature/source, plan, plan-review, REAL PREFLIGHT, FULL, and result-
   review chain for each tested construction;
4. direct raw artifacts and key implementation paths;
5. separation of run validity from scientific support, contradiction,
   inconclusiveness, and invalidity;
6. leakage, label-order, smoke-only, incomplete-matrix, and provenance risks;
7. canonical memory, research-tree, and next-search updates; and
8. whether any open paper-wide objection actually invalidates this gate's
   evidence or next decision.

The audit was requested because the gate had completed its specialist loops but
had neither an independent `990` audit nor a `999` transition report. I did not
execute an experiment, modify code, invoke a submodule skill, use KVM, or run a
Git command. This report is the audit's only file change.

## Inputs And Provenance

### Governing instructions and current scientific contract

I read the following governing inputs directly:

- `docs/user-instruction.md` in full;
- `docs/idea-story.md`, including the retained initial thesis and the current
  fixed-RQ entries relevant to this gate;
- the current paper's explicit four RQ statements under `docs/paper/`;
- `docs/evaluation.md` in full;
- `docs/background-related-work.md` in full;
- `docs/questions-for-author.md` in full;
- the complete `auto-research-orchestrator` skill and its hierarchical research
  state-machine reference; and
- the complete `research-experiment-design` skill plus its plan-template and
  technique-catalog references.

The controlling thesis remains **“Agent observability needs profiling, not only
debugging.”** The four fixed questions remain:

1. **RQ1:** Does Semantic Profiling Improve Resource Attribution?
2. **RQ2:** Does Profiler Output Correspond to Real Problems?
3. **RQ3:** How Accurate Are the Tags?
4. **RQ4:** What Is the Profiling Cost?

This gate worked on RQ2. Neither a failed construction nor an inconclusive
conjunctive test is allowed to narrow that question, replace the thesis, remove
inspection work, or turn a mechanism boundary into the paper's main story.

### Gate reports

I read all 46 Markdown files, totaling 8,888 lines, under
`docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/`. This includes the
gate entry; every literature/source report; all plans and plan-review rounds;
all implementation and implementation-review reports; every preflight and
preflight review; the invalid first AgentNet FULL attempt; each final FULL
report; and each result review.

The reviewed branches were:

- `loop-rq2-codetracebench/`;
- `loop-rq2-toolsafe/`;
- `loop-rq2-agentnet/`;
- `loop-rq2-agentprocessbench/`; and
- `loop-rq2-agentprocessbench-wilson/`.

### Direct implementation and raw evidence

I inspected the label-order, grouping, scoring, bootstrap, shuffle, and FULL
entry paths in:

- `script/codetracebench_agentprof_eval.py`;
- `script/toolsafe_agentprof_eval.py`;
- `script/agentnet_cross_platform_eval.py`;
- `script/agentprocessbench_profile_eval.py`; and
- `script/agentprocessbench_wilson_eval.py`.

I then recalculated the load-bearing point estimates and intervals from the raw
JSONL/GZip artifacts rather than treating the generated Markdown reports or
their embedded verdicts as authoritative. Principal raw locations were:

- `docs/visexp/out/codetracebench-rq2/full/`;
- `docs/visexp/out/toolsafe-rq2/full/`;
- `docs/visexp/out/agentnet-rq2/full/`;
- `docs/visexp/out/agentprocessbench-rq2/full/`; and
- `docs/visexp/out/agentprocessbench-rq2-wilson/full/`.

### Contamination disclosure

I necessarily saw the specialist reports' prior verdicts, expected hypothesis
directions, proposed repairs, and current `docs/evaluation.md` disposition.
Those inputs were not excluded because this task explicitly required auditing
all gate Markdown. I was not given an intended outer-audit verdict or a hidden
answer. To limit priming, I checked source/prediction/label separation in code,
joined raw artifacts independently, recalculated point estimates and raw
percentile intervals, and classified run status separately from hypothesis and
paper impact. Prior reviewer labels are therefore disclosed context, not the
evidentiary basis of this verdict.

## Method

For each branch I applied the following checks:

1. **Admission and scope:** real paper-level RQ, declared target, competing
   explanation, published/official external asset, strongest fair baseline,
   completion rule, and paper-value decision.
2. **Plan convergence:** whether must-fix objections were resolved before
   execution and whether plan changes altered the intended question.
3. **REAL PREFLIGHT:** whether the actual source, actual profiler, actual
   prediction path, actual label boundary, and actual scorer ran; a schema or
   synthetic smoke did not count.
4. **FULL completion:** expected population, folds/cells, repetitions,
   exclusions, and terminal statuses.
5. **Leakage and ordering:** fields visible to profile construction, when human
   target values entered, whether target-label files reached prediction, and
   whether scoring mutated pre-label artifacts.
6. **Raw reconstruction:** exact ID coverage, method metrics, family/fold
   diagnostics, bootstrap percentiles, shuffle/null p-values, and conservation
   checks where raw replicates were retained.
7. **Scientific classification:** execution validity, tested-hypothesis verdict,
   research value, paper impact, and next decision were judged separately.
8. **Outer state:** user-intent fidelity, frozen-contract fidelity, research
   tree, search policy, canonical-memory consistency, and transition predicate.

No internal `PASS` marker, generated report, or reviewer conclusion was treated
as sufficient without direct support.

## Result Matrix

| Branch | Run status | Tested construction | Scientific result | Current value | Paper authorization |
|---|---|---|---|---|---|
| CodeTraceBench | VALID and complete | Task-held-out differential semantic profile versus raw-action and phase views on real coding-agent failures | MIXED / INCONCLUSIVE | Workload/mechanism boundary | None |
| ToolSafe | VALID and complete | Cross-family semantic grouping of released structured safety judgments versus risk+tool and risk-only | CONTRADICTED | Strong negative construction boundary | None |
| AgentNet | Final execution complete; intended comparison INVALID | Cross-platform learned risk aggregated by a semantic key that dropped visible `target`, versus raw action retaining `target` | Comparison invalid; fixed observed construction adverse | Design warning: preserve the raw local leaf | None |
| AgentProcessBench mean-risk | VALID and complete | Target-preserving AgentProf semantic groups scored by mean released blind-judge risk | INCONCLUSIVE | Supporting RQ2 evidence: semantic-specific AP, unresolved work interval | No paper result yet |
| AgentProcessBench Wilson | VALID and complete | Target-preserving groups scored by a fixed family-local Wilson-shaped finite-ensemble score | INCONCLUSIVE | Supporting adaptive evidence; same unresolved work condition | No paper result yet |

The last two branches are the load-bearing current evidence. They establish a
reproducible semantic-specific concentration effect but do not establish the
full conjunctive RQ2 claim because both task-cluster work-to-50 intervals cross
zero. The earlier branches remain auditable boundaries and must not be promoted
or silently forgotten.

## Branch-Level Evidence

### 1. CodeTraceBench

#### Scope and execution

The branch used a real released CodeTraceBench population, real raw trajectory
archives from four official agent formats, real AgentProf, and terminal
incorrect-step annotations. The full source ledger gives a terminal status to
all 3,316 manifest trajectories: 2,717 were source-valid and 599 were explicitly
excluded. The target population contains 405 source-valid failed trajectories
and 20,866 public operations. The FULL matrix includes 200 retained frequency-
matched controls, 2,000 outcome-null trials, and 10,000 task-cluster bootstrap
replicates.

The implementation writes `predictions-pre-label.md` before the only terminal
loader projects `incorrect_stages`. The raw `reference-operations.jsonl`
(108,569 rows) and `target-operations.jsonl` (20,866 rows) contain operation,
phase, raw-action, source, step, trajectory, and task identifiers, but no
incorrect/unuseful label values. The code path confirms that prediction
materialization precedes label loading.

#### Independent checks

The 200 frequency-control effects reconstructed from
`frequency-partition-results.md` have:

- median `0.042294`;
- 2.5th percentile `0.03617655`;
- 97.5th percentile `0.048459125`; and
- maximum `0.050981`.

These values match the generated report. The semantic AP point estimate is
higher than raw-action and phase, but paired intervals cross zero and the
outcome-null p-value is `0.531`. This is a valid real experiment with a mixed
answer, not evidence for the RQ2 claim and not evidence against the broader
paper thesis.

#### Limitation classification

The branch retains the point/control table and summarized null/bootstrap
results but not the individual 2,000 outcome-null and 10,000 bootstrap replicate
arrays. That weakens direct raw reproducibility relative to later branches.
Because the reported result is conservative, the branch is not load-bearing,
and its boundary is independently consistent with retained artifacts, this is
a provenance limitation rather than a result-invalidating defect. It should be
recorded in the gate report; it does not justify rerunning the experiment.

### 2. ToolSafe

#### Scope and execution

The branch uses all 7,182 released records: 6,786 operation records plus 396
non-operation compatibility records. It executes all three leave-one-family-out
folds over AgentHarm, ASB, and AgentDojo and retains the required bootstrap
cells. Prediction code checks that target-family IDs are absent from the
reference-label map, persists predictions before `score-all` loads held-out
target labels, and reports explicit fallback behavior.

The source projection joins the separate labels exactly at 7,182/7,182 and
contains no score, target label, attack-success, aggressive, attacker-tool, or
meta-sample label keys.

#### Independent checks

From raw predictions and separate labels, primary strict results reproduce as:

| Method | AP | Recall at 30% work | Work to 50% recall |
|---|---:|---:|---:|
| semantic | 0.930871202828 | 0.233705226072 | 0.321839080460 |
| risk+tool | 0.892672462716 | 0.534644744568 | 0.282051282051 |
| risk-only | 0.891821745032 | 0.241926012918 | 0.304892425582 |

Unsafe-only results reproduce as:

| Method | AP | Recall at 30% work | Work to 50% recall |
|---|---:|---:|---:|
| semantic | 0.529137229155 | 0.482800982801 | 0.366047745358 |
| risk+tool | 0.646298360735 | 0.760442260442 | 0.247126436782 |
| risk-only | 0.600267758306 | 0.730958230958 | 0.243442381373 |

The family pattern also reproduces: semantic only slightly exceeds both
baselines on AgentDojo, does not clearly do so on AgentHarm, and is lower on ASB.
Fallback counts are exact: semantic has 6,786 exact assignments; risk+tool has
235 exact tool-level assignments and 6,551 risk backoffs; risk-only has 6,786
exact assignments.

The high pooled semantic AP does not rescue the construction: inspection-work
metrics are worse, the unsafe-only comparison reverses, and gains are not
family-stable. The correct construction-level verdict is **CONTRADICTED**. That
verdict limits this cross-family transfer/scoring design; it does not narrow RQ2
or negate the paper thesis.

### 3. AgentNet

#### Scope and execution

The final repaired FULL run covers the complete released cross-platform source:
17,625 trajectories, 17,532 task IDs, and 339,005 operations, with Windows-to-
Darwin and Darwin-to-Windows folds and 10,000 valid task bootstraps per fold.
The first FULL attempt was honestly marked invalid after a group-key mismatch;
the key path was repaired, REAL PREFLIGHT reran, and only the final attempt was
used.

The predictor receives one reference-platform label file and no target-platform
label file. It persists predictions, groups, profiles, bootstrap draws, and
digests before the scorer receives held-out target labels. Post-score digests
confirm the label-blind artifacts are unchanged.

#### Independent checks

For Darwin, the exact 99,295-operation join gives:

- raw AP `0.269816781315`, recall@30 `0.474268900498`, work@50
  `0.338566896621`;
- semantic AP `0.264431115461`, recall@30 `0.476610820873`, work@50
  `0.319955687598`; and
- ungrouped-risk AP `0.273393387589`.

Raw 10,000-replicate percentile intervals are:

- semantic-minus-raw AP `[-0.00767463, -0.00263532]`;
- semantic-minus-raw recall@30 `[-0.00801383, 0.01138256]`;
- raw-minus-semantic work@50 `[0.00893128, 0.02857847]`; and
- semantic-minus-ungrouped AP `[-0.01068742, -0.00690083]`.

For Windows, the exact 239,710-operation join gives:

- raw AP `0.280606366949`, recall@30 `0.492026448853`, work@50
  `0.346798214509`;
- semantic AP `0.269659850791`, recall@30 `0.484195514067`, work@50
  `0.313866755663`; and
- ungrouped-risk AP `0.276432473086`.

Raw percentile intervals are:

- semantic-minus-raw AP `[-0.01361157, -0.00840421]`;
- semantic-minus-raw recall@30 `[-0.01069590, 0.00094917]`;
- raw-minus-semantic work@50 `[0.02625389, 0.03870663]`; and
- semantic-minus-ungrouped AP `[-0.00875348, -0.00488560]`.

#### Validity classification

These adverse AP results cannot be attributed fairly to “semantic refinement.”
The raw-action key is `(action, target, repeat_state)`, while the semantic key
is `(domain, application, phase, action, repeat_state)`: it drops the visible
`target` field. The raw assignments quantify the resulting destructive merge:

- Darwin: 2,708 of 6,176 semantic groups merge multiple raw targets, covering
  86.268% of operations, with a maximum of 102 targets in one group;
- Windows: 3,761 of 8,332 semantic groups merge multiple raw targets, covering
  86.428% of operations, with a maximum of 147 targets in one group.

Therefore the **run** is valid and complete, but the intended semantic-versus-
raw comparison is **scientifically invalid** for its stated refinement claim.
It contributes a useful design rule—preserve `target` and the raw local leaf—
but neither supports nor contradicts the intended RQ2 hypothesis.

### 4. AgentProcessBench Mean-Risk Construction

#### Scope and execution

This is the first load-bearing current branch. It uses the complete official KDD
2026 AgentProcessBench source: 1,000 trajectories, 8,509 assistant steps, four
families, 200 tasks, and 20 released blind-judge prediction slots per step.
Profiles are built from visible operation fields and released judge votes; human
step labels enter only after group assignments and risk/profile artifacts are
materialized. AgentProf operation counts and integer risk mass are conserved per
group and globally.

The source screen disclosed that project agents had seen some HotpotQA and tau2
human-label values while auditing the official schema. That prevents calling
the work a pristine never-observed holdout. It does not create demonstrated
value leakage into this construction: the fixed fields and mean released-risk
score were derived independently, the construction is written before the human
label loader, and all target labels are used only by the scorer. The result is
properly classified as supporting benchmark evidence rather than fresh hidden-
target confirmation.

#### Independent raw reconstruction

The raw `group-assignments.jsonl`, `risks.jsonl`, and `labels.jsonl` join exactly
on 8,509 operation IDs. Human-label counts are 2,710 harmful (`-1`), 452 neutral
(`0`), and 5,347 positive (`+1`). Released judge evidence contains 168,382
available predictions and 24,634 negative predictions; only three operations
have all prediction slots null.

Equal-family macro results reproduce as:

| Metric | Raw action | Semantic | Favorable effect |
|---|---:|---:|---:|
| AP | 0.556133374449 | 0.587655275866 | +0.031521901417 semantic-minus-raw |
| Recall at 30% work | 0.358486746657 | 0.435248166682 | +0.076761420024 semantic-minus-raw |
| Work to 50% recall | 0.329920409058 | 0.313600351330 | +0.016320057728 raw-minus-semantic |

The effect directions by family reproduce exactly:

| Family | Raw AP | Semantic AP | Raw work@50 | Semantic work@50 |
|---|---:|---:|---:|---:|
| BFCL | 0.392090 | 0.424146 | 0.313127 | 0.297297 |
| GAIA | 0.761772 | 0.793278 | 0.417690 | 0.380221 |
| HotpotQA | 0.377033 | 0.399956 | 0.348774 | 0.354223 |
| tau2 | 0.693640 | 0.733240 | 0.240090 | 0.222660 |

From all 10,000 retained bootstrap effect rows, independently recomputed 95%
percentile intervals are:

- semantic-minus-raw AP: `[0.015137772679136, 0.053514347686639]`;
- raw-minus-semantic work@50: `[-0.022550253752915, 0.074213662641834]`.

The 200 retained matched-shuffle rows contain one AP effect at least as large as
observed, giving the finite-sample value `(1+1)/(200+1) = 0.009950248756219`;
all group-size preservation checks are exact.

#### Classification

The run is **VALID**. The semantic AP condition is supported and is not explained
by pure refinement granularity, but the predeclared work condition is unresolved
and HotpotQA has an adverse work point estimate. The conjunctive tested
hypothesis is therefore **INCONCLUSIVE**, not contradicted and not fully
supported. This is real supporting RQ2 evidence but does not answer RQ2 or
authorize a reader-facing result by itself.

### 5. AgentProcessBench Wilson-Shaped Construction

#### Scope and execution

This is the predeclared second and final score construction on the same target.
It reuses the same official benchmark and target-preserving profile keys but
replaces mean risk with a fixed family-local Wilson-shaped finite-ensemble score
using a published statistical principle and a fixed `z=1.959963984540054`.
Group vote totals, scores, and operation scores are written before the human
label loader is called. The score is correctly described as a conservative
finite-ensemble ranking statistic, not a calibrated confidence interval on
human harm.

The raw `wilson-group-scores.jsonl` contains 10,252 group rows. Recalculation of
the formula gives zero numerical discrepancy at retained precision. Four groups
have zero available votes and receive the predeclared score zero. Neither the
group-score nor operation-score artifacts contain human-label fields.

Because the project had already observed this benchmark's target results, this
branch is adaptive supporting evidence on a reused target, not an independent
replication. The reports disclose that limitation and preclude a third
AgentProcessBench score variant.

#### Independent raw reconstruction

Equal-family macro results reproduce as:

| Metric | Raw action | Semantic | Favorable effect |
|---|---:|---:|---:|
| AP | 0.556443324450 | 0.580958623243 | +0.024515298792 semantic-minus-raw |
| Recall at 30% work | 0.357884770 | 0.425245090 | +0.067360320 semantic-minus-raw |
| Work to 50% recall | 0.330628249076 | 0.302976937966 | +0.027651311110 raw-minus-semantic |

All four families have favorable point estimates for both AP and work:

| Family | Raw AP | Semantic AP | Raw work@50 | Semantic work@50 |
|---|---:|---:|---:|---:|
| BFCL | 0.393528 | 0.409251 | 0.327027 | 0.302703 |
| GAIA | 0.761928 | 0.785689 | 0.416462 | 0.360565 |
| HotpotQA | 0.377831 | 0.397434 | 0.348774 | 0.340599 |
| tau2 | 0.692486 | 0.731460 | 0.230250 | 0.208040 |

From all 10,000 retained bootstrap effect rows, independently recomputed 95%
percentile intervals are:

- semantic-minus-raw AP: `[0.016471713510015, 0.051485986082663]`;
- raw-minus-semantic work@50: `[-0.026808793797087, 0.080506256673838]`.

No one of the 200 matched-shuffle AP effects reaches the observed effect, giving
`(1+0)/(200+1) = 0.004975124378109`; group-size preservation is exact.

#### Classification

The run is **VALID**. Semantic-specific AP concentration again survives the
matched-refinement control and the work point estimate improves in every family,
but task-cluster work uncertainty still crosses zero. The conjunctive result is
again **INCONCLUSIVE**. It strengthens the mechanism signal and motivates a
fresh source or different evidence mechanism; it does not justify a third score
variant, a completed RQ2 claim, or a thesis change.

## Cross-Branch Validity Checks

### Real external evidence

All five final branches contacted released external sources and used the real
AgentProf path. The load-bearing AgentProcessBench branches used the complete
official population, not a convenience prefix. CodeTraceBench explicitly
accounted for source-invalid exclusions. ToolSafe completed all source families.
AgentNet completed both full cross-platform folds. No synthetic-only or
same-context reflection result is being admitted.

### Preflight versus FULL

Each branch has an execution-only REAL PREFLIGHT followed by a separate FULL
run. Preflight metrics are not used as paper evidence. Failed attempts remain
recorded; the AgentNet first FULL attempt is not silently overwritten and its
replacement passed a repaired preflight. The final result classifications refer
only to complete intended matrices.

### Label and target-order boundary

- **CodeTraceBench:** pre-label prediction and control-partition artifacts are
  written before terminal incorrect/unuseful label projection.
- **ToolSafe:** target-family labels are excluded from fold prediction and enter
  only in pooled scoring.
- **AgentNet:** each predictor receives only the opposite platform's labels;
  target scoring occurs after digested label-blind artifacts are written.
- **AgentProcessBench mean risk:** visible operations, released blind-judge
  risks, profiles, and assignments are materialized before human labels.
- **AgentProcessBench Wilson:** all family-local group and operation scores are
  additionally materialized before human labels.

No raw artifact or code path demonstrates target-value leakage into the
load-bearing profile construction. Disclosed prior human-target observation
limits independence of the second AgentProcessBench construction; it does not
make either materialized construction post-label.

### Fairness and competing explanations

Matched refinement shuffles in both AgentProcessBench branches preserve raw
group sizes exactly and test whether smaller semantic groups alone explain the
AP effect. They reject that explanation for the observed AP gain. They do not
resolve the work-to-50 uncertainty. AgentNet demonstrates why preserving
visible local identity is a fairness requirement rather than an optional
robustness check.

### No overinterpretation

`docs/evaluation.md` correctly distinguishes:

- CodeTraceBench as valid but mixed;
- ToolSafe as a contradicted construction;
- AgentNet as an invalid intended comparison;
- the first AgentProcessBench branch as valid but conjunctively inconclusive;
- the Wilson branch as supporting adaptive evidence on a reused target and
  still inconclusive;
- the predeclared two-construction same-target limit; and
- WRITE as the next outer state without inserting unsupported or negative prose.

It does not claim that RQ2, the thesis, or the four-RQ evidence chain is
complete. This restraint is scientifically correct.

## User-Intent And Frozen-Contract Audit

The current paper and `docs/evaluation.md` retain the exact thesis and all four
fixed RQs. Negative and invalid branches remain internal evidence rather than
reader-facing replacement stories. The RQ2 positive hypothesis still requires
both correspondence to independently annotated real problems and reduced
inspection work. The gate improves mechanisms and records boundaries instead
of weakening that hypothesis after failed tests.

No idea-level rewrite, RQ replacement, or contribution shrinkage is present in
this gate. The paper itself was not rewritten by these experimental nodes. The
next WRITE gate must preserve that boundary: it may express only established,
phase-permitted evidence and must not insert negative/inconclusive construction
prose as though it were a positive final result.

## Procedural Deviations

These deviations must be recorded in `999-gate-report`, but none changes the
raw numerical results or requires an experimental rerun.

1. **Multiple experiments in one EXPERIMENT gate.** The user requires one
   experiment per step, and the orchestrator requires exactly one explicit RQ
   and one experiment for its specialist invocation. This gate instead ran a
   long serial chain of distinct CodeTraceBench, ToolSafe, AgentNet, and two
   AgentProcessBench constructions. This is a material orchestration deviation.
   It is historical and cannot be made compliant by rerunning or erasing work.
   The correct response is to preserve every node, stop the branch now, and
   enforce one admitted experiment in the next step.
2. **Reviewer freshness is not consistently demonstrated.** Several successive
   review rounds identify the same independent reviewer rather than clearly
   recording a fresh reviewer per serial round. The concrete must-fix issues did
   converge, and this outer audit independently checked the raw evidence, so
   this is process debt rather than a validity failure.
3. **Gate-local Git activity was reported.** Some historical node reports record
   commits during a child/gate loop even though the orchestrator permits Git
   persistence once per completed step, after reports and audits. This audit ran
   no Git command. The deviation is orthogonal to the data and should not be
   repaired through history rewriting.
4. **Custom/flattened report naming.** The gate preserves detailed Markdown
   nodes but does not consistently use the canonical timestamped
   `loop-NNN/001...005` layout. Provenance remains readable, so this is a report-
   hygiene issue, not missing scientific evidence.

## Gate-Blocking Canonical-Memory Defect

`docs/evaluation.md` is a current, bounded experiment frontier and links the
active branch reports and raw paths. In contrast,
`docs/background-related-work.md` is stale in ways that affect routing:

- it calls CodeTraceBench the “selected primary RQ2 condition” even though that
  experiment has completed;
- it labels CodeTraceBench extraction and evaluation as the next literature
  tasks;
- it lists ToolSafe and AgentNet only as later candidates even though both have
  completed current-cycle branches;
- it omits both completed AgentProcessBench constructions and their evidence
  limits;
- it says the next experiment should begin with target-blind localization,
  conflicting with the current `docs/evaluation.md` decision to enter WRITE and
  end same-target score variants; and
- at 243 lines, it has also drifted past the orchestrator's rough one-to-two-
  hundred-line current-frontier budget without archiving stale detail.

The state machine makes canonical memory and research-tree updates an explicit
large-gate exit requirement. This defect does not invalidate a score, interval,
or branch verdict, but it invalidates the formal claim that memory/search state
is ready for transition. It also creates a real repetition hazard on resume.

### Required bounded repair

Before `999-gate-report`:

1. rewrite `docs/background-related-work.md` as a concise current frontier;
2. preserve the verified closest-work and novelty constraints;
3. mark CodeTraceBench, ToolSafe, AgentNet, AgentProcessBench mean-risk, and
   AgentProcessBench Wilson as completed typed branches with their correct
   `mixed`, `contradicts`, `invalid comparison`, and `supports-but-inconclusive`
   edges;
4. link the detailed current-cycle reports instead of duplicating their
   histories;
5. state that same-target AgentProcessBench score search is closed and a third
   variant is prohibited;
6. align next search with `docs/evaluation.md`: WRITE next, then whole-paper
   REVIEW chooses a fresh public source or different independently grounded
   evidence mechanism if RQ2 reopens; and
7. retain the fixed thesis and all four RQs without converting the boundary into
   a new story.

This repair is Markdown-only. It requires neither data generation nor an
experiment rerun. Because this independent audit has identified a must-fix,
the root should request a fresh outer verification of the repaired frontier
before it claims a passing `999` transition.

## Ranked Open Scientific Objections

These objections belong in the gate report's ranked open-objections list. None
invalidates the completed node evidence or the decision to stop same-target
variants; they limit scientific impact and select later research.

1. **RQ2 is still open.** Both load-bearing constructions have positive
   semantic AP intervals but work-to-50 intervals crossing zero. Session and
   ungrouped-risk views also remain competitive on some metrics. This prevents
   an RQ2 answer; it does not invalidate the runs.
2. **The Wilson branch is adaptive and non-independent.** It reuses a benchmark
   whose human targets had already been observed. It may support a mechanism
   but cannot serve as fresh confirmation. A third same-target variant would
   worsen this problem and is prohibited.
3. **The measured signal is a released 20-model judge ensemble.** AgentProf
   structures an external detector's signal; it does not independently discover
   harmful steps. This constrains claims about profiling correspondence and
   should motivate a different evidence mechanism or source.
4. **Only RQ2 advanced in this cycle.** RQ1 still has mechanism evidence rather
   than a final answer, and RQ3/RQ4 remain open. Whole-paper REVIEW should rank
   the next highest-paper-value evidence gap across all four RQs rather than
   mechanically continuing RQ2.
5. **CodeTraceBench raw replicate retention is weaker.** Its individual null and
   bootstrap arrays are not preserved. The conservative mixed boundary is
   still supported, but the branch should not become load-bearing later without
   acknowledging this limitation.
6. **Production breadth remains missing.** Current sources are public benchmark
   traces, not production telemetry with analyst studies, multimodal agents, or
   ecosystem-native trace imports. This limits external validity, not current
   artifact correctness.

## Research-Tree And Search-Policy Disposition

The evidence implies the following typed edges:

- CodeTraceBench **limits** the task-held-out differential construction;
- ToolSafe **contradicts** the tested cross-family safety construction;
- AgentNet **invalidates** target-dropping as a fair semantic-refinement
  comparison and **requires** target/local-leaf preservation;
- AgentProcessBench mean risk **supports** semantic-specific AP concentration
  but **leaves unresolved** inspection-work reduction;
- AgentProcessBench Wilson **supports** the same semantic-specific signal under
  an adaptive score but **leaves unresolved** inspection-work reduction;
- the two AgentProcessBench branches together **close** same-target score
  variants and **motivate** a fresh source or different evidence mechanism; and
- all branches **preserve** the fixed RQ2 hypothesis and the broader four-RQ
  thesis.

The project has exploited the RQ2 score-construction branch long enough. Search
should backtrack at the whole-paper level after WRITE, compare the remaining RQ
gaps, and select one sibling branch with highest paper-level decision value.
If RQ2 is selected again, the source or measured signal must be genuinely fresh;
if another RQ is more decisive, the next step should follow that evidence
instead. Repeating AgentProcessBench, dropping `target`, or reopening a completed
negative branch requires materially new external evidence and an explicit
reopen condition.

## Final Decision

### Scientific decision

The source, protocol, code-path, FULL-matrix, and raw-result checks support the
specialist reports' conservative classifications. No leak, prefix-only run,
proxy-only execution, missing planned cell, or arithmetic mismatch invalidates
the load-bearing evidence. The gate has resolved the current branch well enough
to choose WRITE as the next scientific action. It has **not** answered RQ2,
completed the paper's evidence chain, or authorized a third AgentProcessBench
construction.

### Formal transition decision

**REPAIR CURRENT GATE.** Do not rerun experiments. Bring
`docs/background-related-work.md` to the current literature/search frontier,
then obtain a fresh passing outer verification and write the timestamped
`999-gate-report` that links every child node, this audit and its repair,
canonical updates, raw artifacts, procedural deviations, ranked objections,
and the exact WRITE handoff.

Until that memory repair is verified, this report is **not sufficient for an
honest passing 999**. After the bounded repair, the experimental evidence is
sufficient; no additional empirical work is required for the EXPERIMENT-to-
WRITE transition.
