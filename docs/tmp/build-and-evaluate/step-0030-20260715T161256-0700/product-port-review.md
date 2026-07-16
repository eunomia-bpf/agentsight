# Independent Product-Port Review: Reference-Calibrated Recurrence

**Reviewed:** 2026-07-15
**Skills used:** `oss-change-workflow`, `research-experiment-design`
**Review mode:** fresh read-only diff, contract, test, and raw-artifact audit
**Initial product verdict:** **REQUEST_CHANGES**
**Focused follow-up product verdict:** **APPROVE**
**Scientific experiment verdict:** **APPROVE / unchanged**
**Files edited by reviewer:** this report only

## Scope And Independence

I completely read both named skills, the Step 0030 experiment plan, plan
review, implementation review and follow-ups, preflight report, experiment
result, independent result review, and product-port plan. I then inspected the
current product diff in:

- `agentpprof/src/main.rs`;
- `agentpprof/src/profile.rs`;
- `agentpprof/tests/profile_spec_cli.rs`;
- `docs/design.md`;
- `docs/implementation.md`;
- `script/rq3_reference_calibrated_existing_traces_eval.py`; and
- `script/rq3_reference_calibrated_rust_equivalence.py`.

I inspected the complete scientific raw root and the complete release-binary
equivalence root. Concurrent changes outside this product-port scope, including
`CLAUDE.md`, `docs/evaluation.md`, and `docs/paper/main.tex`, were not treated as
part of this implementation review. I did not edit the product, tests,
scientific scripts, canonical documents, skills, Git state, or the read-only
`docs/agentpprof-paper` submodule. The submodule remains at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c` with no reviewed diff.

## Verdict Summary

The scientific Step 0030 result is valid and remains useful supporting RQ3
evidence. The Rust port correctly reproduces that result on the two complete
unit-weight populations. Its public shape is also appropriately small: one
optional calibration input, no numeric cutoff knob, no benchmark-specific
branch, no new algorithm name, and no change to the label-free default.

The initial review found that the fitted B-cubed objective was broader than the
tested algorithm and that the deterministic tie/error contract lacked focused
tests. The follow-up review confirms both findings are closed: calibration now
gives every operation one vote regardless of profile resource `value`, the
report and focused docs state that information budget, exact ties and missing
input combinations are exercised, and the complete release-binary equivalence
replay remains exact. No product must-fix remains.

## Initial Must-Fix Findings — Closed

### 1. Closed: the Rust fitter resource-weighted B-cubed, but Step 0030 tested per-operation B-cubed

**Classification:** product implementation correctness; the completed
scientific experiment is unaffected.

The approved and independently reviewed Python experiment implements B-cubed
as a per-operation mean: every operation row contributes once and the final
precision and recall divide by the number of operations. This is also the
reader-facing definition: “per-operation predicted--human group overlap.” The
older fixed experiment contracts make the same meaning explicit as unit
operation weights.

At initial review, the Rust port did something different in
`recurrence_calibration_partition_metrics`:

- `calibration[*index].value` becomes the item weight;
- predicted, oracle, and overlap totals accumulate that resource value; and
- each item's precision and recall contribution is multiplied by that value.

Thus a calibration operation with `value: 100` received one hundred votes even
though Step 0030's tested objective gives it one. This was not merely a report
wording difference: it could change the selected scalar and every target
boundary. For a three-operation oracle partition `[A,A,B]` whose increasing
cutoffs yield no boundary, a boundary after operation 1, and all boundaries,
unit B-cubed selects the all-boundary partition (`0.8000` versus `0.7143` and
`0.6667`), while resource weights `[2,2,1]` select the no-boundary partition
(`0.8095` versus `0.7500` and `0.6600`).

At initial review, the complete equivalence checker did not cover this behavior:
`product_rows()` always emits `{"value": 1, ...}` for OSWorld and CodeTrace.
The initial unit test used non-unit values but had a one-group oracle for which
those values did not expose the semantic difference; it did not compare the
result with a unit-valued copy.

**Minimum repair:**

1. Give each calibration operation exactly one vote in B-cubed, independent of
   the operation's profile/resource `value`. Keep `value` additive in the
   resulting profile, but do not let it select the motif boundary cutoff.
2. Make the intended meaning explicit in the focused docs: “operation-weighted”
   means a per-operation mean, not resource-value weighting.
3. Add a regression test showing that changing only calibration `value` leaves
   the selected cutoff, boundary decisions, and segments unchanged.
4. Rerun the complete Python/Rust replay and require the same six cutoffs and
   all 24,152 target decisions to remain exact.

This repair should reduce rather than expand the fitter: count one item in the
predicted/oracle/overlap maps and average over `calibration.len()` (or the
validated item count); the `u64` item-weight tuple and positive/total resource-
weight checks are unnecessary for calibration.

**Follow-up closure:** `recurrence_calibration_partition_metrics` now uses
`usize` operation counts, increments every predicted/oracle/overlap cell by
one, averages over the number of operations, and never reads
`calibration[*index].value`. The serialized objective says “per-operation
B-cubed,” and both focused docs state that every operation receives one vote
regardless of resource value. The existing fitter test now creates a
non-unit-valued calibration and a unit-valued copy and requires their complete
serialized induction reports to be identical. The rerun full-population
equivalence remains exact. **Status: CLOSED.**

### 2. Closed: the focused tests did not prove the advertised tie and invalid-combination contract

**Classification:** product validation completeness; algorithm inspection did
not reveal an incorrect tie implementation.

The code statically implements the intended candidate set and exact tie rule:
scores are sorted and deduplicated, candidates cover below-minimum, all
adjacent-score midpoints, and above-maximum, and an exact F1 tie retains the
numerically smallest cutoff. The complete real replay also matches all six
selected cutoffs and candidate counts. However, all six real fitted optima have
`best_ties = 1`, so neither the replay nor the initial tests exercised an actual
tie.

At initial review, the only new unit test asserted `candidate_cutoffs >= 2`
rather than the exact candidate set or exact selected cutoff. The CLI error
test covered calibration without a score reference and calibration/target
overlap, but it did not cover the separately advertised error for calibration
without `--induce-operation-stack`. Missing or multivalued `group` was checked
by the implementation but not by a focused regression.

**Minimum repair:**

1. Add one compact fitter-level case with an exact objective tie and assert that
   the smallest candidate cutoff wins, together with the exact candidate and
   tie counts.
2. Add the missing CLI case for a calibration input supplied without
   `--induce-operation-stack`.
3. Fold one missing/multivalued-`group` assertion into the existing invalid-
   input test rather than creating another large fixture.

Do not add a new validation framework or another experiment. These are small
regressions for public behavior already promised by the plan and help replace
the initial loose `>= 2` assertion.

**Follow-up closure:** a fitter-level regression constructs two distinct
scores, asserts exactly three candidates, produces exactly two best ties, and
requires the selected cutoff to be `next_f64_down(0.0)`, the numerically
smallest tied candidate. The existing invalid-input CLI test now also covers a
calibration file without induction and a calibration population missing
`group`, while retaining the no-reference and overlap cases. **Status: CLOSED.**

## Product Correctness Checks That Pass

### Fixed algorithm semantics

- The score reference still builds the unchanged adjacent-action NPMI table.
- Each reference transition contributes one occurrence; operation resource
  weights do not enter NPMI.
- Calibration candidates are the correct threshold-equivalence
  representatives, including both extremes.
- The comparison is strictly `score < cutoff`, matching the Python candidate.
- A transition absent from the score reference remains a boundary for every
  candidate and for target prediction.
- Candidate fitting is session-qualified and predicted groups are contiguous.
- Calibration group identities are session-qualified in B-cubed.
- Calibration and target session IDs are rejected on exact overlap.
- The calibration scalar is global for one invocation; there is no framework,
  benchmark, target-result, boundary-F1, or target-oracle branch.
- Segment construction, run-length motif naming, normalized-name
  disambiguation, and profile mass handling remain on the existing path.

### Default compatibility

When calibration is absent, the implementation takes the same Step 0024
branches and applies the same global/cross-action cutoffs. The three newly
optional report values are `None` and skipped by Serde, so the existing
operation-stack induction report remains unchanged. The CLI status object gains
an empty `induce_calibration_operation_files` list, but the product-port plan
promises exact compatibility for the induction report rather than byte identity
of the separate effective-argument status object.

The supervised report keeps the old global and cross-action calibration fields
for compatibility and places the fitted scalar in a separate nested object.
Per-decision `label_free_applied_cutoff` and `label_free_boundary` make the
Step 0024 comparison auditable without altering the default report.

### CLI, profile spec, and errors

- The one new CLI input follows the existing repeatable operation-file style.
- A profile-spec plural field is normalized relative to the spec path and
  merged using the existing list convention.
- CLI and profile-spec success paths are both exercised.
- Calibration with induction but without a score-reference file is rejected.
- Calibration/target overlap is rejected.
- Empty calibration, missing/multiple session or action, missing/multiple
  group, and no observed calibration transition all reach explicit error paths
  under static inspection.

The core induction function does not itself reject a calibration config that
lacks `reference_operations`; today the CLI prevents that state and this crate
has no library target. As optional hardening, add the same one-line invariant
at the core boundary so a future internal caller cannot silently use the target
as the score reference. This is not a reason to add a new public interface.

## Scientific Experiment Validity

The product findings above do not invalidate Step 0030 because both scientific
populations use one row per operation and the Rust replay also emits unit
values.

The reviewed raw scientific root contains exactly:

| Population | Sessions | Operations | Adjacent decisions |
|---|---:|---:|---:|
| OSWorld-Human | 287 | 3,978 | 3,691 |
| CodeTraceBench target | 405 | 20,866 | 20,461 |

The fresh result reviewer independently reconstructed NPMI, candidate
enumeration, folds/stages, boundaries, segments, and B-cubed. The supported
relation is exact on the predeclared primary metric:

- OSWorld B-cubed F1: `0.786169543748 -> 0.801087216271`;
- CodeTrace B-cubed F1: `0.649173103932 -> 0.666563572806`.

The CodeTrace boundary-F1 decline (`0.287106 -> 0.236176`) remains a real
merging/fragmentation qualification and prevents a universal boundary-
improvement claim, but it does not veto the predeclared partition-F1
hypothesis. The correct scientific judgment remains:

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional RQ evidence
```

## Complete Equivalence Evidence

The generated release-binary replay summary reports `status: pass`. I checked
its raw coverage and timing: the release binary is newer than the reviewed Rust
sources and predates the full equivalence summary. It covers all five OSWorld
folds and the complete CodeTrace target:

- all 3,691 OSWorld and 20,461 CodeTrace target decisions are equal;
- all six selected cutoffs are exactly equal;
- all NPMI values agree within `1e-15`;
- all segments and motifs are equal; and
- calibration precision, recall, and F1 agree within `1e-12`.

Because target decisions and segment assignments are exact on the same target
populations, the independently reviewed target partition metrics are preserved.
The checker does not separately rescore target B-cubed against target oracles;
the documentation could more precisely say that exact decisions/segments
*imply* the same pooled metrics rather than implying an additional independent
metric implementation.

## Validation Run By This Reviewer

I executed the already-built current test binaries directly, avoiding a source
or lockfile rewrite:

```text
agentpprof unit/CLI tests:       44 passed, 0 failed
profile_spec_cli integration:   10 passed, 0 failed
standard_trace_cli integration:  3 passed, 0 failed
total:                          57 passed, 0 failed
```

The new success, profile-spec, missing-reference, and overlap cases passed.
`agentpprof --help` exposes both reference and calibration inputs. In addition:

- `cargo fmt --all -- --check`: pass;
- focused `git diff --check`: pass; and
- the current release binary successfully produced the complete equivalence
  artifacts.

I did not independently rerun Clippy because this review was constrained to one
report write and the current compiled artifacts already cover the reviewed
source. The implementer reports that Clippy and the release build were rerun
after the repair; the release binary is newer than the repaired sources and
predates the rerun complete equivalence summary.

## Code-Growth And Reduction Audit

The current tracked product diff, excluding the pre-existing scientific run
and concurrent canonical-paper edits, is:

| Area | Added | Removed | Assessment |
|---|---:|---:|---|
| Product Rust (`main.rs` plus non-test `profile.rs`) | 331 | 6 | net +325 after the objective reduction |
| Rust tests (unit plus CLI/profile-spec) | 397 | 0 | core numeric, CLI, profile-spec, and error coverage |
| Focused product docs | 43 | 1 | paragraph-level, no Quick Start churn |
| Product equivalence checker | 437 | 0 | research validation, not release runtime |

The 970-line scientific evaluator and 1,078 lines of Step 0030 experiment
reports predate the product port's decision and are scientific artifacts, not
production-code growth. They should not be represented as product
functionality.

Net +325 production lines is substantial for one scalar, but most of it is the
actual B-cubed fitter, diagnostics, and existing CLI/profile-spec plumbing; no
dependency, unrelated refactor, numeric tuning knob, benchmark branch, or new
algorithm abstraction was added. The public interface is close to minimal and
the report diagnostics are useful for auditing the information advantage.

The reduction audit records one completed reduction and one optional
opportunity:

1. The closed unit-operation objective removed resource-weight storage,
   arithmetic, zero/total-weight checks, and overflow exposure from the fitter.
2. With the crate's declared Rust 1.87 floor, the standard `f64::next_up` and
   `f64::next_down` methods can replace the two custom bit-manipulation helpers
   if the complete equivalence remains exact. This is optional but removes
   roughly two dozen lines of delicate numeric edge-case code.

The 397 test lines are fixture-heavy, especially the duplicated reference and
target JSONL setup, but the growth now covers the core numeric rule, full-report
resource-value invariance, an actual deterministic tie, CLI and profile-spec
success, and four invalid-input paths. A local fixture helper might shorten the
file, but a new test abstraction would cost more review surface than it saves
at this point. The production path became smaller, and no test-only schema or
framework was added, so this is justified test coverage rather than a blocking
complexity expansion. I find no unnecessary public flag or invented research
term to remove; “reference-calibrated recurrence” and B-cubed describe the
tested mechanism directly.

## Optional Clarifications

These are not blockers and should not expand the interface:

1. The top-level report still lists `group` under `excluded_oracle_fields`
   while the nested supervised report names `group` as its calibration field.
   A short doc sentence should clarify that the exclusion list describes
   score-reference/target boundary construction, whereas grouped calibration
   is the separately declared information budget.
2. `removed_current_boundaries` and `added_current_boundaries` retain their old
   comparison with the global two-means decision. In supervised output, the
   actual Step 0024 comparison is the per-decision `label_free_boundary` field.
   Document this distinction rather than adding more aggregate fields.
3. The release-note impact is a new optional CLI/profile-spec input and new
   supervised-only JSON report fields. No changelog should be invented inside
   this research step, but a future product release note should name the
   annotation requirement and retain the label-free default.

## Focused Follow-Up And Final Verdict

The follow-up reread the final fitter, report, docs, numeric and CLI tests, and
the newly generated complete equivalence artifacts. I independently executed
the current compiled test binaries: 44 core tests, 10 profile-spec/CLI tests,
and 3 standard-trace tests all pass. Formatting and focused diff checks pass.
The implementer also reran Clippy and the release build successfully; the
reviewed release binary is newer than the repaired source and predates the
rerun equivalence summary.

The rerun equivalence summary is `PASS` over the same complete populations:

- OSWorld-Human: 287 sessions, 3,978 operations, 3,691 decisions;
- CodeTraceBench: 405 sessions, 20,866 operations, 20,461 decisions;
- all six selected cutoffs exact;
- every target boundary, label-free boundary, segment, and motif exact; and
- all NPMI values within `1e-15` and calibration B-cubed within `1e-12`.

The focused repair neither changes the scientific result nor adds another
candidate, benchmark, metric, cutoff interface, algorithm name, story, or RQ.
Both initial blocker IDs are closed, and the optional clarification/reduction
items above remain nonblocking.

**Final product-port verdict: APPROVE. Remaining must-fix findings: none.**
