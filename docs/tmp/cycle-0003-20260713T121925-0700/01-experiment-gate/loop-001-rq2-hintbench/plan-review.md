# HINTBench RQ2 Experiment Plan Review

## Round 1 — Independent Scientific And Executability Review

**Reviewer role:** fresh independent experiment-plan reviewer  
**Review date:** 2026-07-13  
**Skill used:** `research-experiment-design`  
**Scope:** one fixed RQ2 experiment on the current official HINTBench artifact  
**Files changed by this reviewer:** this review only

### Material Read And Inspected

I read the complete `research-experiment-design/SKILL.md` and its
`references/plan-template.md` before reviewing. I then read the complete
`docs/user-instruction.md`, complete `docs/idea-story.md`, cycle-0003
EXPERIMENT gate entry, and proposed `experiment-plan.md`.

I independently inspected:

- the HINTBench paper and its fine-localization protocol at
  <https://arxiv.org/abs/2604.13954>;
- the current official artifact, `README.md`, `data/hintbench.json`,
  `data/hintbench_val.json`, and `eval/evaluate.py` at
  <https://anonymous.4open.science/r/HINTBench-B841>;
- the actual `agentpprof/target/release/agentpprof` binary and CLI
  (`agentpprof 0.2.37`);
- `agentpprof/src/profile.rs`, especially operation-file value loading, folded
  stacks, prefix-merged flamegraph construction, and JSON ranking;
- the existing `script/agentprocessbench_profile_eval.py` and
  `script/agentprocessbench_wilson_eval.py` implementations; and
- the currently running llama.cpp server and its `/v1/models` response.

### Overall Judgment

The experiment remains paper-valuable and stays inside one fixed RQ2. The
fresh target population, shared target-blind localizer, high matched-recall
criterion, safe controls, and complete 536-record run are materially stronger
than the paper's present low-recall result. I would keep the experiment and
repair the plan rather than replace it with another RQ, model, or benchmark.

The current plan is not ready for REAL PREFLIGHT, however. Two issues can
directly change the result: the current official data and official formatter do
not define one unambiguous prediction-step namespace, and AgentProf does not
preserve a binary zero-valued hit profile as the plan assumes. The principal
same-information baseline is also weaker than the proposed method because it
gets only one grouping resolution while AgentProf gets four prefix resolutions
and chooses the best one separately for every leaf. Those are scientific
defects, not optional robustness requests.

### What Is Already Sound

#### Fixed question and hypothesis

The plan copies RQ2 verbatim and tests a meaningful consequence: whether a
fixed target-blind semantic profile reduces atomic inspection at the same high
recall. It does not rename the RQ, treat one result as the entire RQ, or rewrite
the locked thesis. Positive, contradictory, mixed, and inconclusive outcomes
lead to different research decisions.

#### Population and target accounting

The current official test file really contains 536 records, 400 risky records,
136 safe controls, and 12,877 trajectory items. It contains 978 annotation
records and 938 distinct `(record, target step_id)` pairs. Keeping the three
unmappable targets as common terminal misses in the primary denominator is
scientifically conservative and avoids a method-dependent exclusion. The
935-target sensitivity is correctly secondary.

Counting every released item as one inspection unit is also consistent with
the paper's message-level definition of a step. Including safe-trajectory work
in the global work denominator prevents free false-positive inspection.

#### Shared-signal design

Using one terminal model response per record for all methods is a strong way to
isolate organization from detection. The model signal is not an AgentProf
contribution, and test gold is excluded from the model request, operation
fields, stack, and rank signal. A parse failure becoming a fixed zero-hit
response rather than a differently worded reprompt is fair.

#### AgentProf prefix property

An ordered operation stack and its cumulative prefixes are genuine AgentProf
properties. `--stack` creates ordered folded stacks; the flamegraph tree
accumulates every leaf's value into each prefix, and the documentation explicitly
describes drill-down through a shared stack prefix. Recovering prefix counts
from real emitted leaf stacks is therefore legitimate.

The exact `max Wilson lower score over a leaf's prefix path` is **not** an
AgentProf 0.2.37 built-in ranking. AgentProf's JSON ranking is leaf-local and
uses `--rank-rule` or `--rank-op-rule`; the Wilson path maximum is a custom
evaluation policy implemented by the thin scorer. That distinction is
acceptable if the plan and eventual claim say so explicitly and verify the
prefix accumulations from the real emitted stacks.

#### Complete execution intent

The declared FULL population, one shared model pass, fixed validation/test
split, terminal-response recovery, all method cells, conservation checks, and
10,000 bootstrap replicates are appropriately complete. No additional model,
benchmark, prompt sweep, oracle bundle, or reproducibility machinery is needed
for this experiment.

### Blocking Scientific And Executability Defects

#### 1. Published-protocol fidelity and the prediction-step namespace are not executable as written

The current release is not schema-compatible with the released evaluator. The
test file uses `risk_labels`; the evaluator reads ground truth only from
`injected_risks`. More importantly, the proposed `localizer_hit(i)` does not say
whether a predicted integer is a trajectory ordinal or a released `step_id`.
That ambiguity is material:

- validation has no `step_id` fields, so its only possible namespace is the
  zero-based trajectory ordinal;
- test has explicit `step_id`, but 216 of 536 trajectories are not the exact
  sequence `0..len-1`;
- the official formatter prints `step_id` incidentally for agent records but
  omits it for system, user, and environment records; and
- current test gold includes 24 user-step targets and 161 environment-step
  targets, plus the three absent targets.

Thus running the "official formatter exactly" cannot unambiguously map many
model outputs back to current released targets. The repair should define one
deterministic, target-blind display ID for **every** rendered item before any
request. The cleanest current-snapshot rule is validation ordinal for
validation and released `step_id` for test, with that ID explicitly rendered
for every role; predictions outside the displayed ID set recover no operation.
This preserves the official fine-localization task and prompt body but is a
necessary formatter deviation and must be recorded as such. If another mapping
is chosen, it must be equally explicit and must prove a one-to-one mapping for
all 12,877 released test items while leaving the three absent targets as
misses.

The source description must also stop calling HINTBench "real agent
trajectories." The paper says its normal and risk trajectories are generated
through a structured synthesis pipeline and then manually verified. It is a
real, official, human-verified public benchmark, but the trajectories are
synthetic. This does not disqualify the experiment, but it bounds the result to
human-verified synthetic long-horizon scenarios. The plan must also list the
actual sampling deviations: the released evaluator uses temperature `0.1`,
top-p `0.9`, unconstrained text parsing, and vLLM, whereas the proposal uses
temperature zero, constrained JSON, llama.cpp, and a different model.

#### 2. The proposed AgentProf hit profile destroys the binary signal, and the custom ranking is not separated from profiler output

For operation-file input, AgentProf 0.2.37 constructs every operation with
`record.value.unwrap_or(1).max(1)`. Therefore writing `value = 0` for a
non-localizer-hit operation turns it into weight one. A direct 0/1
`localizer_hit` weight profile makes hit and non-hit rows indistinguishable and
cannot produce the proposed prefix `h` counts.

The plan must predeclare the already established exact encoding: write a count
profile with value one, write a shifted-signal profile with
`value = 1 + localizer_hit`, and subtract the count profile from the shifted
profile for every full leaf and every accumulated prefix. It must require
per-leaf and global equality with independently counted hits, not merely total
"signal conservation."

At the same time, describe the result as **real AgentProf stack construction
plus a predeclared downstream prefix-ranking policy**. The scorer may aggregate
real leaf stacks into their genuine prefixes and apply Wilson ranking, but the
paper/result must not imply that AgentProf 0.2.37 natively emits Wilson prefix
scores. This repair keeps hierarchical prefix ranking a real test of the
ordered operation-stack representation without attributing custom evaluator
logic to the binary.

#### 3. The flat same-information baseline is not currently the strongest fair alternative

The proposed method receives four nested grouping contexts from the selected
field order and assigns each leaf the maximum score over those four contexts.
The flat comparator receives only one globally selected subset. This grants
AgentProf per-leaf multiresolution smoothing while denying ordinary flat
analysis the same operation fields and grouping opportunities. A SQL/pivot
analyst can issue several `GROUP BY` projections; one fixed subset is therefore
not the strongest competing answer to the stated reject argument.

Repair the existing flat-baseline row rather than adding another baseline. Use
the same full four-field leaf tuples as final inspection units and give the
flat method an explicit same-information multiview policy. The strongest
simple policy is to compute Wilson evidence for all 15 nonempty field subsets
and assign each full leaf the maximum subset score, with the identical tier and
work rules. AgentProf remains restricted to the four prefixes of one
validation-selected order. This is deliberately a hard baseline: if it matches
or wins, ordered hierarchy has not added localization value beyond ordinary
same-information multidimensional smoothing. A different flat policy is
acceptable only if it matches the proposed method's number of resolutions,
final inspection units, score formula, and tuning opportunity and explains why
ordinary multidimensional analysis could not use the omitted subsets.

This repair may make the expected win harder. That is required by the
experiment's load-bearing purpose and does not narrow RQ2.

#### 4. The metric, tie, strongest-baseline, and bootstrap algorithms contain result-changing ambiguity

The ranking section orders equal path scores by hit mass, smaller width, and
lexical key, while the metric section says an entire equal-score tier is
consumed. Both cannot determine the work threshold simultaneously. Define a
tier by the primary numerical rank score and consume every group/leaf with that
score before testing 80% recall; secondary deterministic order may be emitted
for display but cannot permit stopping inside that tier. State the analogous
tier unit for native, independent-step, session, action, and flat methods.

Do not select one "strongest baseline" after observing test point estimates and
then report only that paired interval. Compute and report the paired bootstrap
difference against every predeclared main baseline and require AgentProf's
upper 95% endpoint to be below zero for **each** main baseline. This matches the
plan's own positive interpretation and avoids an ambiguous post-test selection
rule.

Finally, specify the clustered bootstrap algorithm: resample complete risky
trajectories and complete safe trajectories within their two strata, preserve
the multiplicity of every sampled trajectory and all its targets/steps,
recompute group `n/h`, rank tiers, macro recall, and global work on each
resample, and keep validation-selected structures fixed. Do not rerun model
inference or reselect field order/subsets inside the test bootstrap. Without
these definitions, equally plausible implementations can yield different work
points and intervals.

#### 5. Visible-field derivation and the real command are under-specified before gold-guided validation

`phase` and action-response linkage are nearly deterministic as described, but
`status = error/success/unknown` from "explicit timeout/error/success markers"
is not a reproducible rule. Status is both a stack field and a likely risk
correlate, so marker choice after viewing validation scores would be an
unrecorded target-guided method change. Before any validation scoring, the plan
must give the exact finite JSON-key/value and literal-marker rules, precedence,
case handling, malformed-action behavior, environment extraction rule, and
previous-action linkage. The same fixed rules must run on validation and test.
This is necessary adapter specification, not a request for a new ontology or
tagger.

The execution section also needs one concrete preflight command and one full
command with the actual server address, binary, source paths, output path, and
resume behavior. The live server is reachable at `127.0.0.1:8012`; nothing is
listening on the default `127.0.0.1:8080`. Its model response confirms a
27,320,697,856-parameter Q4_K_M model and 32,768 runtime context. The existing
AgentProf binary is executable and reports 0.2.37. Plan review need not demand
that the adapter already exist, but it must leave no endpoint/default ambiguity
for REAL PREFLIGHT and must require preflight to prove that the longest planned
request fits without truncating any trajectory.

### Nonblocking Observations

- The Wilson lower value is acceptable as a fixed ranking heuristic, but it is
  not a calibrated confidence interval for ground-truth risk because its
  Bernoulli observations are the shared localizer's hits. Label it a
  Wilson-shaped conservative hit-density score; reserve the bootstrap interval
  for uncertainty in the work comparison.
- Native sequential inspection should state whether a trajectory-density tie
  consumes all tied trajectories before threshold evaluation. This is already
  covered by the required common tier definition and does not need a new
  baseline.
- One deterministic localizer response per record is sufficient for this
  conditional same-signal comparison. Repeating the model, adding a second
  model, or sweeping prompts would expand scope without repairing the stated
  hypothesis.
- Raw-action, per-session, and width-only rows are interpretable with their
  current roles. No oracle row or additional control is necessary.
- The current official test snapshot differs materially from the paper's
  advertised 629-record population. Running all 536 enumerable records and
  reporting the difference is the correct executable choice.

## Round 1 Verdict

**REPAIR**

Blocking must-fix items:

1. Define and visibly render one deterministic prediction-step namespace for
   every role; disclose the formatter/sampling/schema deviations and describe
   HINTBench accurately as human-verified synthetic trajectories.
2. Replace the invalid 0/1 AgentProf value encoding with shifted-signal minus
   count profiles, verify every leaf/prefix exactly, and separate genuine
   AgentProf prefix output from the custom Wilson path-ranking policy.
3. Strengthen the existing flat same-information baseline so it receives a
   fair multiresolution grouping/ranking opportunity and the same final
   inspection units as AgentProf.
4. Remove metric ambiguity by fixing equal-score tier consumption, paired
   comparisons against every main baseline, and the complete trajectory-cluster
   bootstrap recomputation rule.
5. Predeclare exact visible-field derivation and concrete preflight/full
   commands, including the actual llama.cpp endpoint and a no-truncation check.

## Root Response To Round 1

**Disposition:** accept all five blocking items; retain the experiment and fixed
RQ2 hypothesis; revise only the plan.

### Repair 1 — source fidelity and prediction namespace

The plan now distinguishes the official prompt body from the released
formatter. Every rendered role receives an explicit `[STEP_ID=...]` prefix.
Validation uses zero-based ordinals because no IDs are released; test uses each
released `step_id`. Uniqueness and presence are preflight requirements, and
out-of-range model predictions map to no operation. The plan now discloses the
formatter, schema, model, serving, sampling, and constrained-decoding deviations
and describes HINTBench as an official human-verified synthetic benchmark.

### Repair 2 — AgentProf value semantics and attribution

The plan no longer assumes a 0/1 AgentProf weight. It predeclares a value-one
count profile and a `1 + localizer_hit` shifted profile, subtracting the former
from the latter at every leaf and accumulated prefix. Every recovered leaf and
prefix hit count must equal an independent assignment calculation. The plan now
calls the method real AgentProf stack construction plus a fixed downstream
prefix-ranking policy and explicitly says Wilson path-max is not built into
AgentProf 0.2.37.

### Repair 3 — hard same-information flat baseline

The flat row now uses the same full four-field leaf tuples as final inspection
units and computes all 15 nonempty field-subset projections. Each leaf receives
the maximum Wilson score over all 15 contexts. AgentProf receives only the four
prefixes of one validation-selected field order. The flat policy is fixed and
receives no validation-selected subset, making it a harder ordinary-analysis
alternative rather than a favorable strawman.

### Repair 4 — metric and bootstrap exactness

The plan now consumes complete primary-score tiers for every method and forbids
stopping within a tie. Native sequential inspection uses the exact pair of
trajectory Wilson score and released ordinal as its tier, keeping it distinct
from whole-session grouping. Positive evidence requires the paired interval to
exclude zero against every one of the five main baselines. Bootstrap resamples
complete trajectories within risky/safe strata, preserves multiplicity and all
steps/targets, recomputes groups and curves, and never reruns inference or
reselects validation structure.

### Repair 5 — deterministic mapping and commands

The plan now fixes phase, action linkage, malformed-action behavior, status
inheritance, exact error/success marker lists, precedence, case handling, and
fallbacks before validation scoring. It includes concrete preflight and FULL
commands with AgentProf 0.2.37, the actual `127.0.0.1:8012/v1` server, current
official URLs, output paths, seed, bootstrap count, and resume behavior.
Preflight must tokenize all 616 rendered prompts and prove no trajectory is
truncated under the 32,768-token context plus 4,096-token output allowance.

### Scope check

No second model, benchmark, RQ, prompt sweep, oracle bundle, integrity protocol,
paper edit, story change, or skill change was added. The revised plan remains
one complete HINTBench RQ2 experiment.

## Round 2 — Fresh Repair Verification And Remaining-Defect Review

**Reviewer role:** fresh independent Round-2 experiment-plan reviewer  
**Review date:** 2026-07-13  
**Skill used:** `research-experiment-design`  
**Scope:** verify every Round-1 repair and find only result-changing defects in
the same fixed HINTBench RQ2 experiment  
**Files changed by this reviewer:** this review only

### Material Read And Independently Inspected

Before judging the revision, I read the complete
`research-experiment-design/SKILL.md` and its complete
`references/plan-template.md`. I then read the complete
`docs/user-instruction.md`, complete `docs/idea-story.md`, the complete
cycle-0003 EXPERIMENT gate entry, the complete revised `experiment-plan.md`,
and all of Round 1 plus the root response above.

I independently inspected the current official HINTBench test and validation
JSON, the released `eval/evaluate.py` formatter/parser, the real AgentProf
binary and operation-file/profile implementation, the established shifted-
profile implementation in `script/agentprocessbench_profile_eval.py`, and the
live llama.cpp service. The current facts relevant to this review are:

- the test snapshot has 536 records and 12,877 items; every test item has one
  integer `step_id`, no record has a duplicate `step_id`, and the only roles are
  system, user, agent, and environment;
- validation has 80 records, 3,050 items, and no released item IDs; it has 60
  risky records, 169 injected-risk origin annotations, and 163 distinct
  `(validation record, origin ordinal)` pairs;
- one validation origin is not present in its trajectory: validation array
  index 39, task
  `digitalEvidenceBreachCounselHub_task_0009_risk_v3`, declares origin 35 for a
  33-item trajectory;
- all current nonempty agent `action` fields in both splits are JSON strings
  that parse to objects with nonempty string `name` values;
- `agentpprof/target/release/agentpprof` is executable and reports version
  0.2.37; and
- `http://127.0.0.1:8012/v1/models` exposes the exact model path named by the
  command, with `n_ctx = 32768`, and the llama.cpp `/tokenize` endpoint is live.

### Round-1 Repair Verification

#### 1. Test source namespace and protocol disclosure — closed; validation target handling remains open

The test-side ambiguity is repaired. Prefixing every role with its released
test `step_id`, requiring presence and uniqueness, mapping only exact displayed
IDs, and retaining out-of-range predictions makes the 12,877-item prediction
namespace one-to-one and target blind. The three absent test targets remain
common misses. The revision also correctly calls the benchmark human-verified
synthetic evidence and discloses the schema, formatter, server, model,
temperature, top-p, and constrained-decoding deviations.

Validation display IDs are also unambiguous: zero-based ordinals are the only
released per-item namespace. The remaining problem is gold accounting, not
prediction mapping. The revised plan says to use all validation
`risk_origin_step` values but does not say what happens to validation origin 35
in the 33-item record. Keeping it as a miss, dropping it, remapping it, or
stopping as a source error changes validation macro recall and can change the
selected field order. Because that order is the only test-time AgentProf
configuration selected with gold, its treatment must be fixed before scoring.

#### 2. Shifted encoding and prefix attribution — closed

The revision correctly uses a count profile with value one and a shifted
profile with `1 + localizer_hit`. Subtracting independently accumulated count
weights from shifted weights at every full leaf and every reconstructed
non-root prefix exactly recovers `h`, while the count profile supplies `n`.
The plan requires equality against independent operation assignments and both
leaf/prefix and global conservation. This directly closes AgentProf 0.2.37's
zero-to-one coercion problem.

The attribution boundary is also honest: ordered full stacks are emitted by
real AgentProf, their prefixes follow the actual folded-stack semantics, and
the Wilson path maximum is explicitly a downstream scorer rather than an
AgentProf built-in ranker. No further profile encoding or extra integrity
artifact is required.

#### 3. Flat same-information multiview — information coverage improved, tuning fairness not closed

The revised flat row now receives the same full four-field leaves, the same
binary localizer signal, the same Wilson formula, and all 15 nonempty field
subsets. It is no longer the one-subset strawman identified in Round 1.

However, “all 15 contexts” is not automatically a harder method than “the best
four nested contexts.” Taking a maximum over more contexts can raise a
spurious leaf above a true leaf and make the resulting ranking worse; score
dominance per leaf does not imply ranking or work dominance. AgentProf uses
gold validation to choose one of 24 context chains, while the flat policy gets
no validation-selected policy at all. Calling the latter's larger fixed context
set “harder” therefore does not repair the unequal tuning opportunity.

There is also an identifiability issue the final plan must confront explicitly:
each AgentProf prefix count used by this scorer is exactly reproducible by an
ordinary `GROUP BY` over that prefix's field subset. A credible ordinary
multiview competitor can use validation to choose the same finite context
policy and then reproduce the same downstream scores without an ordered-stack
file. If that exact reconstruction is denied to the baseline, a win can be
caused by policy selection rather than hierarchy. If it is allowed, an exact
tie demonstrates that this particular scoring policy does not isolate a
representation-specific localization advantage. This is not a request for a
new baseline row or benchmark; it is a required repair to the existing flat
row and to what this one comparison can identify.

#### 4. Native/session distinction, tier-complete work, and strongest-baseline decision — closed

Native and session are now different executable positions. Native first orders
trajectories by their shared-signal density and then exposes released atomic
positions; its tier is the exact score/ordinal pair. Session treats the whole
trajectory as an indivisible group. The revision states the order of inspection
and forbids gold from resolving equal pairs. Session grouping can therefore no
longer collapse conceptually into native sequential inspection.

For every method, the primary numerical score defines an indivisible tier and
the complete tier is charged before recall is tested. Safe steps remain in the
global work denominator, duplicate target annotations are deduplicated, and
the three absent test targets remain in risky-trajectory recall denominators.
The plan also predeclares all five paired comparisons and requires a negative
upper confidence endpoint against every one, rather than selecting a favorable
baseline after test results. Those definitions remove the Round-1 stopping and
post-selection ambiguity.

#### 5. Clustered bootstrap — closed

The bootstrap now resamples complete trajectories separately within the 400-
risky and 136-safe strata, preserves sampled multiplicity, steps, and targets,
and recomputes group `n/h`, rankings, tiers, macro recall, and the global work
denominator on each replicate. It fixes the validation-selected structure and
does not rerun inference. This is the correct sampling unit for a population of
trajectories and is sufficient for the declared paired work differences.

An implementation must give repeated sampled trajectories replicate-local
lineage when constructing session/native units, or equivalently preserve their
weights exactly. The plan's explicit multiplicity requirement already entails
that behavior, so this is an implementation check for RESULT REVIEW rather
than another plan blocker.

#### 6. Visible-field derivation — most rules fixed; two result-changing transformations remain unspecified

Phase, action-response linkage, report inheritance, JSON error/success
precedence, exact marker lists, lowercase handling, malformed-action fallback,
and unknown fallback are now predeclared. The current source also contains no
malformed nonempty action, so the specified fallback is not an observed
selection variable.

Two operations are still not exact:

1. validation `environment` is described only as “the prefix of `task_id`.”
   The plan does not name the delimiter or extraction expression. This field
   participates in all 24 gold-scored AgentProf orders and all 15 flat
   projections, so different interpretations can change both selection and
   the test comparison;
2. stack strings “may sanitize” values, but the encoding is not fixed and is
   not required to be injective. Replacing several characters with one token,
   truncating, or collapsing empty/special values can merge leaves and prefixes
   and thereby change `n/h`, ties, and work.

The plan should give one literal validation-environment extraction rule and one
deterministic stack encoding that preserves equality and inequality (or aborts
on a collision), both before validation scoring. This is necessary thin-adapter
specification, not a new semantic ontology.

#### 7. Concrete 8012 execution and complete no-truncation preflight — closed

Both commands name the real official URLs, real AgentProf binary, live
`127.0.0.1:8012/v1` server, exact exposed model path, output directories,
bootstrap count, seed, and resume behavior. The current endpoint and model file
exist, and AgentProf reports the required version. The command surface is
concrete enough for REAL PREFLIGHT; adapter implementation is correctly left
to the execution stage.

Preflight must render all 616 target-blind requests and prove that the largest
exact chat-formatted request plus the 4,096-token output allowance fits the
32,768-token runtime context. That is a complete-population truncation check,
not a smoke-only estimate. During implementation the tokenizer input must
include the same llama.cpp chat template and explicit step-ID rendering sent to
`/v1/chat/completions`, rather than tokenize only the untemplated trajectory
string. This follows directly from “planned prompts” and is a nonblocking
execution clarification; RESULT REVIEW can verify the recorded maximum.

### Scientific Scope Judgment

The experiment still passes paper-value admission. It uses a fresh official
target population, attacks a load-bearing low-recall/ordinary-grouping
explanation, and makes positive and contradictory outcomes decision-relevant
without changing RQ2 or the thesis. No additional model, benchmark, RQ, prompt
sweep, optional robustness bundle, or provenance machinery is warranted.

### Nonblocking Observations

- The primary result remains conditional on one shared deterministic localizer;
  that is appropriate because the experiment isolates organization rather than
  claiming detector generality.
- Calling the Wilson quantity a conservative hit-density score, rather than a
  confidence interval for official risk, remains the clearest terminology.
- The mappable-target sensitivity and width-only row are properly labeled as
  secondary/control results and do not need expansion.
- The live server and current source facts should be rechecked in REAL
  PREFLIGHT, but neither Git identity nor a frozen source object is needed.

## Round 2 Verdict

**REPAIR**

Blocking must-fix items:

1. Fix validation target accounting by explicitly retaining validation record
   39's absent origin 35 as a common unrecovered miss (or predeclaring another
   scientifically justified treatment) in the validation macro-recall
   objective; never let the adapter silently drop, infer, or remap it.
2. Repair the existing flat multiview comparison so it receives a predeclared
   validation-selection opportunity comparable to AgentProf's 24-way
   selection, and state how the experiment handles the exact ordinary
   `GROUP BY` reconstruction of AgentProf's chosen prefix policy. Otherwise a
   result cannot distinguish hierarchy from unequal downstream policy tuning.
3. Make visible-field construction fully deterministic before validation by
   specifying the exact validation `task_id`-to-`environment` extraction and an
   injective, collision-checked AgentProf stack-string encoding.

## Root Response To Round 2

**Disposition:** accept all three blocking items. Preserve the fixed RQ2, the
paper thesis, and the one-experiment scope; revise only the experiment plan.

### Repair 1 — validation absent-target accounting

The plan now fixes the validation denominator at all 163 distinct official
origin pairs. Validation array index 39's absent origin 35 remains an
unrecovered miss for every one of the 24 candidates and for both independent
implementations. It cannot be silently dropped, remapped, inferred, or promoted
to a source error. This matches the already fixed test treatment of the three
absent released targets.

### Repair 2 — equal tuning and exact flat reconstruction

The reviewer identified a mathematical boundary rather than a missing
engineering control: every cumulative stack prefix used by this scorer is
exactly reproducible by an ordinary `GROUP BY` over the same fields. Therefore
a representation-specific accuracy win over an algebraically identical query
is impossible and must not be manufactured by unequal tuning.

The revised flat row is now an **algebraic identity control**, not a fifth main
baseline. For each of all 24 orders it independently reconstructs exactly the
four cumulative prefix projections, applies the same Wilson path maximum, tier
rule, validation objective, and tie-breakers, and must match AgentProf's prefix
counts, scores, curves, selection, selected order, and test result exactly. Any
mismatch invalidates execution. The positive decision remains aggressive and
paper-relevant: AgentProf must reach 80% macro recall and significantly reduce
work against all four genuine competing workflows—native sequential debugging,
independent-step ranking, per-session grouping, and raw-action grouping—while
passing the identity check. This preserves RQ2 and the profiling-not-only-
debugging thesis without asserting an impossible serialization advantage.

### Repair 3 — exact environment derivation and injective frames

Test `environment` is the exact nonempty released `env`. Validation
`environment` is the substring before the first literal `_task_`; a missing
delimiter or empty prefix stops preflight. Every raw semantic field value is
encoded for AgentProf as `hex:` plus lowercase hexadecimal UTF-8 bytes. The
encoding survives AgentProf's lowercase/safe-character normalization and is
injective. Preflight must round-trip every observed value across both splits,
verify a one-to-one map, and abort on any collision or mismatch. No lossy
sanitization or truncation remains available to change grouping.

### Scope check

No new benchmark, model, prompt sweep, RQ, paper edit, story change, skill
change, provenance protocol, or non-Markdown contract was added. The plan still
contains one complete HINTBench RQ2 experiment and awaits a fresh serial Round-3
review before any implementation or preflight.

## Round 3 — Fresh Source-Level Verification Of Round-2 Repairs

**Reviewer role:** fresh independent Round-3 experiment-plan reviewer  
**Review date:** 2026-07-13  
**Skill used:** `research-experiment-design`  
**Scope:** verify the three Round-2 repairs and identify only scientific or
executability defects that can change this same one-RQ experiment's result  
**Files changed by this reviewer:** this review only

### Material Read And Review Method

Before judging the plan, I read the complete
`research-experiment-design/SKILL.md`, its complete
`references/plan-template.md`, and its complete
`references/technique-catalog.md`. I then read the complete
`docs/user-instruction.md`, complete `docs/idea-story.md`, complete cycle-0003
EXPERIMENT gate entry, complete revised `experiment-plan.md`, and complete
Round-1/Round-2 discussion above.

I independently queried the current official HINTBench validation and test
JSON and inspected the real AgentProf operation-file, stack construction, and
`safe_frame` implementations. I did not run a preflight or experiment, inspect
test labels to tune a method, add a benchmark/model, or use Git. The technique
catalog does not justify adding a systems-test bundle here: the admitted
question is a matched localization benchmark, and the current integrated
comparison is the smallest technique that can test it.

### Independent Source And Implementation Evidence

- The official validation file still contains 80 trajectories, 60 with
  injected risks and 20 without, and 3,050 atomic items. Its 169 origin
  annotations deduplicate to 163 `(record, origin ordinal)` pairs. Validation
  array index 39 still declares origin 35 for a 33-item trajectory.
- The official test file still contains 536 trajectories and 12,877 items. All
  test items have unique integer `step_id` values within their trajectory.
- Contrary to the revised mapping's stated precondition, only 382 test records
  contain a string `env`; 154 records omit the `env` key. Those 154 records
  include 143 risky and 11 safe records, so they cannot be excluded without
  changing both recall and work. Every one of the 154 records does have a
  nonempty string `task_id` with a literal `_task_` and a nonempty prefix.
- AgentProf 0.2.37 still coerces an operation-file value with
  `record.value.unwrap_or(1).max(1)`, confirming that the repaired count plus
  shifted-signal construction is necessary.
- `safe_frame` ASCII-lowercases a value and preserves ASCII alphanumerics plus
  `._:/+-`. Therefore `hex:` followed by lowercase hexadecimal UTF-8 bytes is
  preserved, round-trippable, and injective when the proposed collision and
  decode checks pass.

### Verification Of The Three Round-2 Repairs

#### 1. Validation absent-target accounting — closed

The revised plan explicitly fixes the validation denominator at all 163
distinct origins and makes index 39/origin 35 an unrecovered miss for every
candidate and both implementations. It forbids dropping, remapping, inferring,
or treating that origin as a source error. This closes the Round-2 target-
accounting defect and matches the test-side treatment of the three absent
targets.

#### 2. Equal tuning and ordinary flat reconstruction — closed

The revised flat row independently implements the same 24 ordered chains, the
same four cumulative projections per order, the same path-maximum Wilson score,
the same complete-tier work rule, and the same validation selection. Requiring
candidate-level and selected-test equality makes it an algebraic identity
control rather than a baseline that can be made weaker by unequal policy
tuning.

This is the scientifically correct boundary. The experiment may test whether
the declared multiresolution profile improves inspection over the four genuine
debugging/simple-view alternatives; it cannot claim that stack serialization
is more accurate than an exactly equivalent `GROUP BY` program. Requiring an
exact tie does not invalidate RQ2 and does not warrant another comparator,
model, or benchmark.

#### 3. Exact environment derivation and injective frame encoding — encoding closed; test source handling remains open

The validation rule (substring before the first literal `_task_`) is exact and
executable for all 80 validation records. The lowercase hexadecimal encoding
is also exact under the actual AgentProf sanitizer and has the required
round-trip/collision checks.

The test-side rule is not executable for the current official population,
however. It requires an exact **nonempty** released `env`, while 154 of the 536
official records have no `env` value at all. Elsewhere the plan says an empty
value can be encoded as `hex:`, but that does not define how an absent JSON
field becomes an environment value; if the field is omitted from an operation,
AgentProf also produces a shorter stack. Stopping, omitting the frame, using an
empty string, using `unknown`, or deriving a task-family prefix creates
different groups and can change the selected test work curve.

The minimal target-blind repair is available from the same official record:
use exact released `env` when it is a nonempty string, and otherwise use the
substring of `task_id` before its first literal `_task_`, with the already
specified missing-delimiter/empty-prefix error. All 154 affected records satisfy
that fallback's source preconditions. Whatever rule is chosen must be one exact
predeclared rule applied before any scoring; no record may be excluded.

### Additional Result-Changing Defect

#### Validation order selection is still not fully defined

The plan says to choose the order with minimum work at 80% validation macro
recall, but it does not state the population over which validation macro recall
is averaged or the validation work denominator. Two plausible implementations
can therefore average over the 60 target-bearing trajectories or attempt to
include all 80 trajectories, and can charge only risky steps or all 3,050
validation steps. Those choices can select different field orders.

The plan should state the exact validation analogue of the primary test rule:
macro recall is the mean over the 60 validation trajectories with official
origins; index 39/origin 35 remains in its trajectory's denominator; and work is
the atomic-step count/fraction over all 3,050 validation items, including the 20
safe trajectories.

The subsequent tie-breaker is also result-changing as written. “Lower total
group count” can mean final four-field leaves, whose count is invariant under
field reordering, or the sum of distinct groups across the four cumulative
prefix depths, which can differ by order. The smallest repair is to remove this
redundant phrase and break equal-work candidates by the already declared
lexical field-order key. Alternatively, define total group count explicitly as
the sum of distinct prefix groups at depths one through four. AgentProf and the
flat identity control must use the same fixed definition.

### Other Scientific And Executability Checks

- The plan retains the paper's exact RQ2 and thesis, tests one hypothesis, and
  treats one result as evidence toward rather than a complete answer to RQ2.
- Shared deterministic localizer output, official labels loaded only at
  scoring, disjoint validation/test selection, complete equal-score tiers,
  absent targets, safe-case work, and all four paired comparisons remain
  scientifically coherent.
- Native sequential, independent-step, per-session, and raw-action rows retain
  distinct competing positions. The exact flat row and width-only row are
  correctly separated as controls.
- The paired stratified trajectory bootstrap is adequately specified. The
  already stated multiplicity requirement is sufficient for implementation;
  it does not need another plan artifact.
- The concrete `8012` commands, complete 616-prompt tokenization check,
  terminal-response resume rule, all-536 completion rule, and raw paths are
  sufficient once the two blockers above are repaired.
- No extra model repetition, second benchmark, prompt sweep, oracle, source
  freeze, Git binding, or provenance machinery would repair either blocker.

### Nonblocking Observations

- The exact flat tie should remain visible in the eventual result as an
  implementation and claim-boundary check, not a superiority comparison.
- Validation/test environments need not share literal category values for a
  field-order transfer experiment; only the derivation rule and selection
  boundary must be fixed before scoring.
- Wilson remains a downstream hit-density ranking score, not an AgentProf
  built-in ranker or a confidence interval for official risk. The plan already
  states that boundary.

## Round 3 Verdict

**REPAIR**

Blocking must-fix items:

1. Define one executable target-blind test `environment` rule for the 154
   official records that omit `env` (the source-supported minimal rule is
   nonempty released `env`, otherwise the pre-`_task_` `task_id` prefix), and
   retain all 536 records.
2. Fully define validation selection as macro recall over the 60 target-bearing
   trajectories with work charged over all 3,050 validation items, and remove
   or precisely define the ambiguous “total group count” tie-breaker.

No other must-fix item remains in this Round-3 review. After these two local
plan repairs, a fresh serial reviewer should verify them before REAL PREFLIGHT;
the experiment should not expand beyond its current one-RQ matrix.

## Root Response To Round 3

**Disposition:** accept both blockers as local source/metric-definition repairs;
preserve the experiment, fixed RQ2, thesis, methods, and positive threshold.

### Repair 1 — retain all records with one deterministic environment fallback

The plan now uses the exact released test `env` when it is a nonempty string.
When `env` is absent or empty, it uses the substring of the same record's
nonempty `task_id` before the first literal `_task_`. A present non-string
`env`, invalid `task_id`, missing delimiter, or empty prefix is a source error.
The plan records the current 382/154 split and explicitly retains all 536 test
records. Thus neither source missingness nor risk labels may decide exclusion,
stack depth, or a special semantic category.

### Repair 2 — exact validation objective and deterministic tie

The plan now defines validation macro recall over exactly the 60 trajectories
with official origins, retaining index 39's absent origin in its trajectory's
denominator. It charges work over all 3,050 released validation items, including
all items from the 20 no-origin trajectories. The selected order is the one
with minimum atomic-step work at at least 80% macro recall; an exact work tie is
broken only by the lexical field-order key. The ambiguous and redundant “total
group count” tie-breaker has been removed. AgentProf and the independent flat
reconstruction use this identical objective.

### Scope check

No method, benchmark, model, prompt, result criterion, RQ, paper text, skill,
or implementation was changed. A fresh serial Round-4 review must verify these
two repairs before REAL PREFLIGHT.

## Round 4 — Fresh Verification Of Round-3 Repairs

**Reviewer role:** fresh independent Round-4 experiment-plan reviewer  
**Review date:** 2026-07-13  
**Skill used:** `research-experiment-design`  
**Scope:** verify the two Round-3 repairs at source/executable level and identify
only remaining result-changing blockers inside the same fixed HINTBench RQ2
experiment  
**Files changed by this reviewer:** this Round-4 review only

### Material Read And Review Boundary

Before reviewing, I read the complete `research-experiment-design/SKILL.md`
and its complete `references/plan-template.md`. I then read the complete
`docs/user-instruction.md`, complete `docs/idea-story.md`, complete cycle-0003
EXPERIMENT gate entry, complete revised `experiment-plan.md`, and complete
Round-1 through Round-3 discussion and root responses above.

I independently re-read the current official HINTBench test and validation
files and executed target-blind source-accounting checks against them. The
current official downloads match the locally inspected copies byte-for-byte:

- test SHA-256:
  `87b33d3941be49cc40e6b38e1faec3cb420fd3483369eff68821e43a4db62e44`;
- validation SHA-256:
  `3e3cb4d692faccbf1ca7bc4826fddba9af5feeb6373b00b7f9c14802059e7449`.

I did not run model inference, construct an experimental result, inspect labels
to tune a method, add a method or workload, modify the plan, or use Git.

### Round-3 Repair 1 — Test Environment Fallback

**Verified closed.**

The current official test source has exactly:

- 536 records and 12,877 released trajectory items;
- 382 records with a present nonempty string `env`;
- 154 records with no `env` key, comprising 143 risky and 11 safe records;
- zero present empty-string `env` values and zero present non-string `env`
  values; and
- zero records with a missing or duplicate released item `step_id`.

For every one of the 154 records without `env`, `task_id` is a nonempty string,
contains the first literal `_task_`, and has a nonempty prefix before that
delimiter. I executed the plan's exact decision rule over all 536 records:
use a present nonempty string `env`; otherwise take the pre-`_task_` `task_id`
prefix; otherwise fail. It produced 536 environment assignments, zero empty
assignments, zero failures, and 45 distinct environment values. Repeating the
deterministic transformation produces the same ordered-output digest.

The plan states this exact rule, distinguishes absent/empty fallback from the
present-non-string source error, records the observed 382/154 split, and
explicitly retains all 536 records. No risk label, target, model output, or
post-scoring fact participates in the fallback. The repair therefore closes
both the executability defect and the possible population-selection bias.

### Round-3 Repair 2 — Validation Population, Work, And Tie

**Verified closed.**

Independent source recomputation gives:

- 80 validation trajectories and 3,050 released items;
- 60 trajectories with official injected-risk origins and 20 without origins;
- 169 raw origin annotations, deduplicating to 163 distinct
  `(record, origin ordinal)` pairs over exactly those 60 target-bearing
  trajectories; and
- exactly one absent distinct origin: array index 39,
  `digitalEvidenceBreachCounselHub_task_0009_risk_v3`, origin 35 in a 33-item
  trajectory.

Index 39 has two distinct origins, one mappable and one absent. Thus its recall
at complete released-step inspection is `1/2`, and complete inspection yields
validation macro recall `0.991666...` over the 60 target-bearing trajectories.
The declared 80% target is consequently defined and reachable while still
charging the absent origin as a common miss.

The revised plan now fixes all result-changing parts of selection:

1. deduplicate and retain all 163 official origins;
2. average macro recall over exactly the 60 target-bearing trajectories;
3. retain index 39/origin 35 in that trajectory's recall denominator;
4. charge work over all 3,050 items, including every item from the 20
   no-origin trajectories;
5. choose minimum atomic-step work at at least 80% macro recall; and
6. resolve an exact work tie only by the lexical field-order key.

The candidate set is the 24 permutations of four fixed, uniquely named fields.
Lexicographic comparison therefore defines one total deterministic order over
otherwise tied candidates. The previous ambiguous group-count tie-breaker is
absent from the current plan. AgentProf and the independently implemented flat
identity control receive the same population, objective, and tie rule and must
select the same order.

### Remaining Result-Changing-Blocker Audit

No result-changing scientific or executability blocker remains inside this
fixed experiment:

- the plan retains the exact RQ2, one hypothesis, and one official benchmark
  population;
- localizer output is shared and target blind, and official labels enter only
  terminal scoring or the predeclared validation selection;
- the test and validation step namespaces, absent-target treatment, operation
  mapping, injective stack encoding, and shifted AgentProf signal recovery are
  executable and fixed;
- the flat exact reconstruction is correctly an identity/claim-boundary
  control, receives identical 24-way selection, and cannot be misreported as a
  representation-specific win;
- native sequential, independent-step, per-session, and raw-action methods are
  distinct main competing workflows with the same visible signal;
- complete score-tier consumption, primary populations, four paired
  comparisons, positive threshold, and trajectory-cluster bootstrap are fixed;
  and
- the concrete endpoint, source URLs, AgentProf binary, preflight/full
  commands, full 616-request and 12,877-operation completion rules, prompt
  tokenization check, raw-output path, and recovery behavior are sufficient to
  execute the next stage.

The thin adapter is intentionally an execution-stage artifact and need not
exist before plan approval. Its implementation must follow this plan and will
be tested by the real end-to-end preflight; that is not a reason to add another
plan round, benchmark, model, prompt sweep, oracle, integrity protocol, or
provenance mechanism.

## Round 4 Verdict

**PASS**

No must-fix remains. The repaired plan is scientifically meaningful, fair,
source-complete, deterministic where result-changing choices occur, and
executable for the declared one-RQ matrix. **REAL PREFLIGHT is authorized.**

## Post-Round-4 Implementation-Audit Correction

**Status:** Round-4 authorization is temporarily superseded; no inference was
run. One final Round-5 review is required after the corrections below.

### New official-source evidence

A read-only implementation audit re-read the current official
`eval/evaluate.py` and computed SHA-256
`ab7bcfc70d6cb45fe91c8020a61754312c9fb7e6a8cb909fb260aab76236ab80`.
The actual `SamplingParams` are temperature `0.1`, top-p `0.9`, and
`max_tokens=1024`. Earlier plan/review text incorrectly described the official
maximum as 4,096. The adapter had not yet made any inference request, so no
result or cache is contaminated.

### Factual repair

The plan now uses the official 1,024-token maximum and reserves 1,024 tokens in
the complete-population context check. It accurately distinguishes the
remaining deviations: llama.cpp/Qwen rather than vLLM/example Llama; one Qwen
chat-template envelope rather than direct raw-prompt generation; deterministic
temperature zero/top-p one; and constrained rather than unconstrained JSON.

### Exact implementation choices closed before inference

The same audit found five places where multiple plausible implementations could
change model output or a reported endpoint. The plan now fixes them without
adding a method, workload, or analysis:

1. one `/v1/chat/completions` user message contains the complete filled official
   prompt; reasoning is disabled with the exact declared request fields;
2. every role-specific item begins with the exact prefix bytes
   `[STEP_ID=<id>]\n`, while the remaining official rendering is preserved;
3. the JSON schema fixes required fields, official risk-name enum, integer step
   arrays, and no extra properties, but deliberately adds no `minItems` or
   safe/unsafe conditional beyond the published prompt/parser semantics;
4. bootstrap percentile endpoints use NumPy `method="linear"`; and
5. the signal-free width control ranks atomic width descending and consumes a
   complete equal-width tier.

The exact request is applied through llama.cpp `/apply-template` and then
`/tokenize` with special-token handling before any inference for all 616
records. The first real response must confirm the precomputed prompt-token
count through its usage field. Resume reuse requires the canonical complete
request body to match.

### Scope and next action

These are source-fidelity and deterministic-execution repairs only. RQ2,
thesis, hypothesis, populations, operation mapping, AgentProf construction,
four main baselines, exact flat identity, work/recall metric, positive
threshold, and paper remain unchanged. A fresh Round-5 reviewer must verify the
repaired plan and official evaluator before REAL PREFLIGHT resumes.

## Round 5 — Final Fresh Official-Protocol And Regression Review

**Reviewer role:** fresh independent Round-5 experiment-plan reviewer
**Review date:** 2026-07-13
**Skill used:** `research-experiment-design`
**Scope:** verify the post-Round-4 official-protocol corrections and reconfirm
that no earlier scientific repair regressed inside the same fixed HINTBench RQ2
experiment
**Files changed by this reviewer:** this Round-5 review only

### Material Read And Independent Evidence

Before judging the correction, I read the complete
`research-experiment-design/SKILL.md`, its complete
`references/plan-template.md`, and its complete
`references/technique-catalog.md`. I then read the complete
`docs/user-instruction.md`, complete `docs/idea-story.md`, complete cycle-0003
EXPERIMENT gate entry, complete current `experiment-plan.md`, and the complete
Round-1 through Round-4 discussion, root responses, and post-Round-4 correction
above.

I independently downloaded the current official HINTBench
`eval/evaluate.py` from the plan's 4open URL. Its SHA-256 is exactly:

`ab7bcfc70d6cb45fe91c8020a61754312c9fb7e6a8cb909fb260aab76236ab80`.

The downloaded source constructs `SamplingParams` with temperature `0.1`,
top-p `0.9`, and `max_tokens=1024`, builds each prompt by applying the official
`format_trajectory` and `PROMPT_TEMPLATE`, and passes the resulting raw prompt
strings directly to `llm.generate(prompts, sampling_params)`. It does not wrap
them in chat messages or constrain generation with a JSON schema. The repaired
plan therefore states both the official maximum and every material inference
deviation accurately.

I also independently downloaded the current test and validation JSON. Their
SHA-256 values remain:

- test: `87b33d3941be49cc40e6b38e1faec3cb420fd3483369eff68821e43a4db62e44`;
- validation:
  `3e3cb4d692faccbf1ca7bc4826fddba9af5feeb6373b00b7f9c14802059e7449`.

Source recomputation still gives 536 test trajectories, 12,877 test items, 400
risky and 136 safe records, 978 annotations, 938 distinct test targets, and the
three declared absent targets. Validation still gives 80 trajectories, 3,050
items, 60 target-bearing records, 163 distinct origins, and the declared absent
origin at array index 39. Test item IDs remain present, integer, and unique
within every trajectory; the test environment split remains 382 direct `env`
values and 154 valid `task_id` fallbacks.

Finally, I inspected the live llama.cpp service and its current server path
without running model inference. `/v1/models` exposes the exact plan model and
32,768-token context. `/apply-template` accepts the declared one-user-message
envelope, `reasoning_format="none"`, `chat_template_kwargs`, and JSON-schema
response format through the same chat-parameter parser used by
`/v1/chat/completions`; `/tokenize` accepts the returned prompt with
`add_special=true` and `parse_special=true`. The server reports the evaluated
prompt length as `usage.prompt_tokens`, so the plan's first-request equality
check is executable and catches any mismatch between the precomputed and
actual chat-template path.

### Post-Round-4 Correction Verification

#### 1. Official output budget and protocol boundary — closed

The plan now uses 1,024 everywhere that controls generation or context
admission: the official-source description, concrete request, full-population
token check, reproducibility notes, and known-deviation summary. No stale 4,096
value remains in the current plan. The older value survives only inside the
historical review record and is explicitly superseded above, so it cannot
govern implementation.

The official raw-vLLM path and the proposed serving path are not conflated.
The adapter sends the complete filled official prompt as the content of exactly
one user message to `/v1/chat/completions`; it discloses Qwen chat templating,
llama.cpp, the different model, temperature zero, top-p one, reasoning off, and
constrained JSON as deviations. This remains one shared target-blind response
per record and does not create a method-specific signal.

#### 2. Exact display-ID bytes and official rendering — closed

For validation, the displayed integer is the zero-based trajectory ordinal;
for test, it is the released integer `step_id`. Every system, user, agent, and
environment item starts with the exact UTF-8/ASCII bytes
`[STEP_ID=<display id>]\n`, immediately followed by that item's official
role-specific rendering. The plan explicitly preserves the rest of the
rendering byte-for-byte, including the official agent rendering's possible
second `[STEP_ID]: <id>` line. Uniqueness, exact-ID lookup, out-of-range
treatment, and absent-target behavior remain fixed. There is no remaining
ordinal-versus-released-ID ambiguity.

#### 3. Exact JSON schema without extra semantic constraints — closed

The schema fixes only the output surface already requested by the official
prompt: a root object with required `verdict` and `risks`; the official
`safe`/`unsafe` enum; risk objects with required `risk_name` and `risk_steps`;
the official eleven risk names; and integer step arrays. It disallows
undeclared object properties but deliberately has no `minItems`,
`uniqueItems`, verdict-dependent conditional, target range, or other semantic
constraint. Empty arrays, duplicate integers, and safe/unsafe consistency are
therefore left to the released parser semantics exactly as the plan states.
The grammar cannot introduce gold labels or silently force a nonempty unsafe
prediction.

#### 4. Exact template-to-token context check — closed

Before inference, all 616 complete requests are rendered. The declared
one-message chat envelope and `enable_thinking=false` template argument are
applied through the live server's `/apply-template`; the returned exact prompt
is passed to `/tokenize` with both special-token flags true. Admission requires
`input tokens + 1,024 <= 32,768` for every record, so neither a longest-sample
estimate nor an untemplated trajectory can authorize FULL. The first real
chat-completion response must report the same `usage.prompt_tokens`; a mismatch
is an implementation error and cannot be treated as permission to truncate or
change the prompt. This is sufficient to detect any overlooked prompt-affecting
server behavior before continuing the cache.

#### 5. Percentiles, width control, and cache identity — closed

All primary work intervals and four paired-difference intervals use NumPy's
explicit `method="linear"` percentile definition over the already fixed 10,000
paired stratified trajectory-cluster replicates. The signal-free control ranks
leaf groups by atomic width in descending order and consumes the entire
equal-width tier before testing recall; it cannot use an unspecified secondary
order to stop early. A cached response is reusable only when split, record key,
and the complete canonical request body match, which captures the prompt,
model, sampling, reasoning, schema, and template settings that can affect the
terminal localizer output. Parse errors and out-of-range predictions remain
terminal; only transport/non-2xx/missing-choice failures retry the identical
request.

### Regression Audit Of Earlier Scientific Repairs

No earlier must-fix has regressed:

- the exact thesis, RQ2 wording, fixed positive hypothesis, one-benchmark
  scope, and decisive-but-not-whole-RQ interpretation remain unchanged;
- all 80 validation and 536 test records remain in the complete matrix, with
  safe work, duplicate-target deduplication, and every absent origin retained;
- validation selection remains exactly one of 24 four-field orders using macro
  recall over 60 target-bearing trajectories, work over all 3,050 items, and
  lexical order as the sole exact-work tie-breaker;
- operation derivation, the 382/154 environment rule, lowercase hexadecimal
  injective frame encoding, count-plus-shifted AgentProf profiles, and exact
  leaf/prefix/global conservation remain fixed before scoring;
- the independently implemented flat `GROUP BY` reconstruction remains an
  exact identity and claim-boundary control, not a fifth baseline or a false
  representation-specific win;
- native sequential, independent-step, per-session, and raw-action grouping
  remain the four distinct main comparators with one shared visible signal;
- complete numerical-score tiers, the 80% macro-recall work point, all four
  paired comparisons, the strict positive threshold, and full clustered
  bootstrap recomputation remain unchanged; and
- REAL PREFLIGHT and FULL commands, terminal-response rules, all-operation
  completion, raw paths, and result-class decisions remain executable without
  adding another model, benchmark, prompt sweep, RQ, oracle, integrity
  protocol, paper edit, or story change.

The current plan continues to satisfy paper-value admission. A positive and a
contradictory result produce different paper decisions, every main baseline
represents a credible competing workflow, and the exact flat tie prevents the
experiment from claiming an impossible serialization advantage. The
post-Round-4 repairs improve source fidelity and determinism without narrowing
the RQ2 hypothesis or expanding the experiment.

## Round 5 Verdict

**PASS**

No scientific or executability must-fix remains. The five post-Round-4
corrections are exact, the official evaluator facts are independently verified,
and all prior scientific repairs remain intact. **REAL PREFLIGHT is explicitly
authorized.**
