# Independent Implementation Review

**Skill used:** `research-experiment-design`
**Review type:** fresh read-only implementation audit before REAL PREFLIGHT
**Verdict:** **APPROVE**
**Candidate metrics, preflight, or full evaluator run:** none

## Scope And Standard

I read the complete `research-experiment-design` skill and its directly
required `references/plan-template.md`, then read the approved Step 0028
experiment plan and both rounds preserved in `plan-review.md`. I inspected the
complete uncommitted diff in:

- `agentpprof/src/profile.rs`;
- `agentpprof/src/main.rs`;
- `agentpprof/tests/profile_spec_cli.rs`;
- `script/rq3_reference_calibrated_common.py`;
- `script/rq3_reference_calibrated_recurrence_eval.py`; and
- `script/rq3_reference_calibrated_codetracebench_eval.py`.

I also compared the changed Rust decision path directly with the Step 0024
version at `HEAD`, inspected the existing OSWorld and CodeTrace scorer helpers
that the new evaluators import, and checked the worktree scope. I did not run
either new evaluator, inspect a candidate result, edit product/evaluator code,
edit the paper or canonical research documents, change a skill, change the
branch, or touch the read-only paper submodule.

Approval here means only that the implementation faithfully realizes the
approved experiment and may proceed to REAL PREFLIGHT. It does not predict or
authorize a favorable scientific result.

## Verdict Summary

The implementation realizes one optional supervised calibration mode of the
existing recurrence constructor. Its data path is:

```text
unchanged Step 0024 action-transition NPMI
-> one reference-group-B-cubed scalar cutoff
-> unchanged strict score < cutoff decision with unseen pairs as boundaries
-> unchanged segments, run-length motifs, operation field projection, and fold
```

The CLI accepts grouped reference operations rather than an experiment-supplied
numeric cutoff. Rust fits the scalar internally. Omitting the calibration input
takes the original Step 0024 branches. The Python code independently rebuilds
the score table, cutoff candidates, B-cubed objective, tie result, every target
decision, and every segment/motif before accepting Rust output. The OSWorld and
CodeTrace adapters implement their required session and label isolation in
control flow, and the CodeTrace adapter hard-checks the exact registered
reference and calibration populations.

**Remaining must-fix findings: none.**

## 1. Default Step 0024 Behavior Is Preserved

The no-calibration path is structurally identical to the Step 0024 decision
path:

- the recurrence model is still built by the same `recurrence_model` function;
- same-action pairs still use `model.global.cutoff`;
- action-changing pairs still use
  `min(model.global.cutoff, model.cross_action.cutoff)`;
- unseen pairs still become boundaries;
- the comparison remains strict `score < applied_cutoff`; and
- the boundary list, segment construction, motif disambiguation, operation
  field insertion, and profile folding code are unchanged.

The new `supervised` value is absent unless grouped calibration operations were
supplied. Its `else if` and `else` branches reproduce the old
`calibration_population` and `applied_cutoff` values exactly. The additional
`label_free_applied_cutoff` and `label_free_boundary` fields are diagnostic
copies of those original decisions; they do not feed the default or supervised
construction. Existing report fields remain present with their prior meaning.

The pre-existing label-free CLI integration test still passes, and the full
Rust test suite exercises the unchanged omitted-calibration route. Thus this is
not a second default constructor disguised as calibration.

## 2. The Supplied Mode Changes Exactly One Scalar

`--induce-calibration-operation-file PATH` is accepted only with both
`--induce-operation-stack` and `--induce-reference-operation-file`. The file is
parsed through the ordinary operation-record path and must supply exactly one
nonempty `session`, `action`, and `group` per calibration operation. There is
no CLI/profile-spec field for a numeric cutoff, target metric, benchmark name,
framework rule, boundary objective, or fallback policy.

When calibration is present, `fit_supervised_recurrence_cutoff` receives the
already-built Step 0024 recurrence model and returns only one fitted `f64`
cutoff plus diagnostics. Target construction substitutes that scalar for the
label-free applied cutoff. It does not change the association map, pair score,
strict comparison, unseen-pair rule, segmentation, motif naming, operation
stack, or additive folding.

The additional CLI supports multiple ordinary input files in the same way as
the existing operation/reference inputs, but all records are concatenated into
one calibration population and still produce exactly one scalar. It is not a
second calibration rule.

## 3. Candidate Enumeration, Objective, And Tie Rule Match The Plan

Both Rust and the independent Python checker:

1. collect distinct finite NPMI values for calibration transitions seen in the
   unchanged score-reference association table;
2. place one cutoff immediately below the minimum;
3. place a midpoint between each consecutive distinct score, advancing one
   representable value when the midpoint rounds to the left endpoint;
4. place one cutoff immediately above the maximum;
5. treat every transition absent from the association table as a boundary for
   every candidate;
6. compute operation-weighted B-cubed precision, recall, and F1 over partitions
   whose group identities are session-qualified; and
7. maximize F1, breaking an exact tie with the numerically smallest cutoff.

Rust uses `f64::total_cmp` for deterministic score ordering and explicit
next-representable-number helpers at the two extremes. Python independently
uses `math.nextafter`. Both use exact equality only for the plan's explicitly
exact tie rule. No boundary F1, target result, external comparator, population
identity, paper preference, or second statistic enters selection.

## 4. Session And Label Isolation

### Product-level isolation

Rust rejects any calibration session ID that is present in the target input.
The target product file contains only `session` and `action`; the calibration
file alone contains `group`. The CLI also refuses calibration without a
separate score-reference file. These checks prevent the normal product command
from treating target annotations as calibration rows.

### OSWorld-Human

The evaluator first projects the source into an in-memory visible object that
retains only `session`, ordered `turn`, and `action`; no group value is retained
in this candidate object. For fold `f`, it then:

- derives train and target session sets with the unchanged five-fold function;
- loads `human_group` only for the four training folds;
- writes score-reference and target product rows containing exactly
  `{session, action}`;
- writes calibration rows containing exactly `{session, action, group}`;
- runs the product and writes `target-predictions.jsonl`; and only then
- calls `load_groups` for fold `f` to score the persisted predictions.

The target label is therefore absent from fitting, from the Rust target input,
and from the independent Python decision recomputation. The fact that the
source JSONL physically co-locates visible fields and annotations does not
create a code path from a withheld target group to the candidate: the visible
loader discards it, and the scorer accesses it only after prediction.

### CodeTraceBench

The evaluator loads visible target operations and establishes all 405 target
IDs before reading any manifest stage column. It removes those IDs from the
broad reference set before constructing either NPMI or the calibration subset.
Only then does it read manifest identity columns (`traj_id`, `solved`, and
`step_count`) and select solved non-target references. The only pre-prediction
stage read is a Parquet projection filtered to those already-selected
calibration IDs. Target stages are first read by
`load_stages_after_prediction`, after both `profile.json` and
`target-predictions.jsonl` exist.

The following counts are hard assertions, not merely report booleans:

| Population | Sessions | Operations | Stages |
|---|---:|---:|---:|
| target-disjoint score reference | 2,229 | 87,703 | n/a |
| solved labeled calibration subset | 483 | 18,152 | 2,886 |
| full target | 405 | 20,866 | 2,948 |

The adapter also hard-checks 112 unavailable non-target manifest IDs, 20,461
full target pairs, per-session operation/stage coverage, and the expected nine
visible action kinds. Preflight selects one target only after the full
reference/calibration population and isolation checks, so it cannot silently
fit a different preflight model.

## 5. Rust/Python Equivalence Is Independent And Complete

The common checker does not consume Rust's selected cutoff as its candidate.
It independently recomputes:

- the action-transition NPMI association table from score-reference actions;
- all scalar candidates;
- calibration B-cubed precision, recall, and F1;
- the selected cutoff and exact tie count;
- every target boundary decision; and
- every target segment and run-length motif.

It then compares the fitted cutoff and all calibration diagnostics with Rust,
checks every emitted target NPMI and applied cutoff, rejects duplicate decision
keys, requires the complete decision dictionary to equal the Python dictionary,
and requires the complete ordered Rust segment list—including motif text—to
equal the independently constructed list. This would not pass on agreement of
only an aggregate metric.

The evaluators separately preserve and score the Step 0024 label-free decision
field. In full mode, OSWorld requires its pooled historical B-cubed value to
match to `1e-15`; CodeTrace requires every historical boundary and partition
precision/recall/F1 value to match to `1e-15`. Static inspection supplies the
stronger decision-level fact: that field is computed by the exact old cutoff
branches before supervised substitution.

## 6. Coverage, Motifs, And Mass Cannot Silently Pass

`run_product` hard-checks the product status, target sample count, and total
profile weight for every fold/population. `check_product_equivalence` requires
the complete expected decision key set and complete ordered segment list.
OSWorld then requires one operation assignment per selected operation and one
pair row per selected adjacent pair; full mode necessarily covers every one of
the five deterministic folds. CodeTrace additionally hard-checks its full
20,461-pair and 2,948-stage totals. Missing motif coverage fails when scorer
rows index the segment-derived assignment, while duplicate motif assignments
are rejected explicitly.

The `validity` booleans written to summaries restate preceding hard checks; they
are not used as promotion gates and do not substitute for assertions. The raw
profile, persisted prediction JSONL, pair decisions, operation assignments,
and summary remain ordinary experiment artifacts.

## 7. Complexity And Scope

The product change is localized to one optional input, one scalar fitter, its
B-cubed calculation, and reporting needed for independent recomputation. The
three Python files separate shared independent mathematics/product checking
from the two source-specific adapters. No schema, seal, manifest, finalizer,
hash binding, target-result retry, per-framework branch, extra benchmark,
second model, or experiment-control interface was introduced.

The worktree diff contains no `docs/paper/` change, no `skills/` change, and no
paper-submodule pointer or content change. `docs/agentpprof-paper` remains at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. The separate Step 0027 audit
correction is outside the algorithm and accurately changes the old calibration
arithmetic to 483 / 18,152 / 2,886; it does not alter paper text or experiment
behavior.

## Static Checks Run

These checks do not execute a candidate metric or either evaluator:

```text
cargo test --all-targets --all-features
  44 Rust unit tests passed
   9 profile CLI tests passed
   3 standard-trace CLI tests passed

cargo clippy --all-targets --all-features -- -D warnings
  passed

cargo fmt --all -- --check
  passed

Python AST parse of all three new scripts
  passed
```

The new tests specifically exercise grouped-reference calibration through the
normal CLI, verify its reported B-cubed fit and changed target boundary, reject
calibration without a score-reference file, and reject calibration/target
session overlap. Existing label-free induction tests remain green.

## Non-Blocking Observations

- A small synthetic exact-tie unit test could make the tie policy more obvious
  to future maintainers, but the current Rust branch is direct and the full
  evaluator independently recomputes the tie count and selected cutoff. This is
  not required for validity.
- The version string remains `agentpprof 0.2.37`, as assumed by the approved
  commands. A later release may choose to bump it, but version publication is
  outside this experiment and is not a scientific blocker.
- Preflight and the full run must still use the approved release-binary commands
  and raw roots. Passing this implementation review does not let a preflight
  prefix count as evidence or relax any complete-population assertion.

## Return

**APPROVE.** There are zero must-fix implementation findings. Step 0028 may
proceed to its two approved REAL PREFLIGHT commands without changing the plan,
algorithm, target population, cutoff rule, paper, skills, branch, or submodule.
Any preflight failure must be treated only as an execution-path defect under
the skill's two-attempt limit; it cannot authorize a target-informed algorithm
repair.
