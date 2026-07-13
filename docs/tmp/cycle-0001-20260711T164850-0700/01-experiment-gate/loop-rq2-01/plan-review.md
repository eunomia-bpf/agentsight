# Plan Review — RQ2 Revision 1

This file contains the required serial scientific review rounds for the single
current `experiment-plan.md`. No preflight is authorized before a PASS in round
3–5.

## Round 1 — Claim Alignment And Construct Validity

- **Timestamp:** 2026-07-11T19:55:11-07:00
- **Reviewer context:** Fresh independent subagent; read the current plan and
  direct sources without `plan-review.md` or prior verdicts.
- **Verdict:** `REVISE`.
- **Decision-critical findings:** The plan did not define whether internal-node
  traversal exposed membership, metadata, or content, so variable-size scope
  `Hit@K` was not comparable with SDBL's exactly-K-step construct. Breadcrumbs
  could convey information derived from unselected operations without charging
  it as inspection work. The downstream criterion allowed 10% more tokens despite
  claiming equal cost. Finally, the positive gate could pass even if query-free
  induction or non-risk navigation matched the advertised method.
- **Required edits applied:** Defined root/internal/terminal traversal and exact
  atomic-operation output; separated step-level `Hit@K` from descriptive
  variable-scope metrics; removed summaries/breadcrumbs from the primary
  localizer input; required both exact-operation and serialized-token budget
  comparisons with no extra-token allowance; and added decision criteria for
  query conditioning and risk navigation.
- **Next action:** Round 2 independently reviews external precedent, baselines,
  released data, and leakage on the revised plan.

## Round 2 — External Baselines, Data, Fairness, And Leakage

- **Timestamp:** 2026-07-11T20:02:26-07:00
- **Reviewer context:** Fresh independent subagent; read the revised plan and
  official source repositories without this review history or source-audit
  report.
- **Verdict:** `REVISE`.
- **Decision-critical findings:** All 117 released TRAIL GAIA raw traces expose
  offline `true_answer` and human `Annotator Metadata`; 30 of 31 SWE-Bench traces
  expose reference `patch` and `test_patch`. Hiding only processed annotations
  therefore did not create a deployment-style primary regime. SDBL SSD/EASD were
  not bound into the fair primary comparison, and their delineation cost and
  full-log-plus-flagged-scope localizer input were conflated with selected-context
  comparisons. Finally, the shared risk scorer lacked an exact model, labels,
  features, training procedure, stored artifact, and cost rule.
- **Required edits applied:** Added a scrubbed TRAIL primary regime and retained
  unmodified official raw input only as compatibility; split paper-faithful SDBL
  replication from an adapted common-localizer EASD comparison and charged both
  stages; made adapted EASD a mandatory Who comparator; and fully specified the
  development-only TF-IDF/logistic scorer, labels, visible features, selection,
  stored artifact, no-refit rule, identical-score use, and cost accounting.
- **Next action:** Round 3 independently reviews metrics, uncertainty,
  executability, full-matrix completion, and remaining scientific defects. A
  Round-3 PASS is required before real preflight.

## Round 3 — Metrics, Uncertainty, And Executability

- **Timestamp:** 2026-07-11T20:08:19-07:00
- **Reviewer context:** Fresh independent subagent; read the revised plan,
  current Rust/runner code, and official data without this review history.
- **Verdict:** `REVISE`.
- **Decision-critical findings:** The release has four zero-gold TRAIL traces, so
  multiple denominators and intent-to-treat behavior were undefined. Development
  selection and downstream equal-cost pass rules lacked a deterministic
  objective, curve statistic, comparator-selection treatment, margins, and full
  uncertainty procedure. Finally, the planned driver, Rust structural node
  output, navigation interface, and minimum-child option do not yet exist, so the
  command could not execute as written; the plan also lacked a significant-run
  resource estimate.
- **Required edits applied:** Defined zero-gold inclusion and every affected
  metric; fixed a maximin development objective and deterministic tie-break;
  specified operation/token AUC, non-inferiority and efficiency branches;
  selected the strongest comparator inside each nested bootstrap replicate while
  resampling localizer and matched-tree repetitions; and added an explicit
  implementation/test node plus Rust schema/CLI/driver requirements and a
  24–96-GPU-hour initial full-run estimate.
- **Next action:** Round 4 reviews the fully revised plan. A PASS authorizes the
  implementation node followed immediately by real preflight; a decision-critical
  defect is repaired in the same plan before Round 5.

## Round 4 — Final Mechanism And Decision-Rule Attack

- **Timestamp:** 2026-07-11T20:13:35-07:00
- **Reviewer context:** Fresh independent subagent; reviewed the whole current
  plan and Rust candidate-field behavior without this review history.
- **Verdict:** `REVISE`.
- **Decision-critical findings:** Removing `induce_query_terms` did not make the
  planned ablation query-free because `query_overlap` remained an eligible
  question-derived induction field. The 25%-saving branch also left budget
  rounding, oversized operations, interpolation, target crossing, unattained
  targets, and paired work-ratio aggregation open to implementation choices that
  could change PASS/FAIL.
- **Required edits applied:** Defined induction-query-free as removing task query
  terms and every explicit question-derived induction field while keeping the
  identical frozen risk/navigation stream, with input and selected-field
  assertions. Defined ceiling/floor rounding and stop-before-oversized prefix
  semantics. Added a directly measured 15% point and replaced target crossing
  with proposed-15%-versus-comparator-20% quality/cost tests; fixed AUC points,
  interpolation boundary, comparator tie-break, sum-of-paired-cost ratios, zero
  denominator behavior, and confidence rules.
- **Next action:** Round 5 is the final permitted plan review. PASS begins the
  implementation node and real preflight; REVISE returns the full plan history
  to WRITE_GATE and full-paper REVIEW without executing an unapproved plan.

## Round 5 — Whole-Scope Construct Check

- **Timestamp:** 2026-07-11T20:17:18-07:00
- **Reviewer context:** Fresh independent subagent; reviewed the complete final
  plan and current implementation boundary without this review history.
- **Verdict:** `REVISE`.
- **Decision-critical finding:** All mandatory pass criteria still operate on
  flattened atomic-operation budgets. They allow a budget to end inside a large
  terminal scope and rank individual operations within it, while internal-node
  expansion has no inspection charge. The method could therefore pass as
  hierarchy-shaped operation ranking without proving the claim that failures are
  concentrated in small, useful, whole semantic scopes.
- **Required future repair:** Add a mandatory whole-terminal-scope criterion with
  a predeclared operation and token work bound. Partial-scope filling cannot
  satisfy it. Require superiority over semantic leaf-only, fixed windows/fields,
  matched random scopes, native scopes, and adapted EASD on Who&When where
  applicable.
- **Routing:** This is the fifth and final permitted review round. The plan is not
  approved; no implementation or preflight may begin in this experiment loop.
  Return the complete RQ2 revision-1 history to WRITE_GATE and then full-paper
  REVIEW, preserving the immutable RQ and ambitious multi-resolution claim.
