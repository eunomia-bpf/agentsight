# Independent Result Review — Step 0029 Experiment 001

**Reviewed:** 2026-07-15T15:49:38-07:00
**Skill used:** `research-experiment-design`
**Review verdict:** **APPROVE**
**Run status:** **VALID / COMPLETE**
**Tested hypothesis:** **CONTRADICTED**
**Research value:** **supporting**
**Paper impact:** **mechanism boundary; additional internal RQ3 evidence**

## Scope And Independence

I completely reread `research-experiment-design`, the approved experiment
plan and both plan-review rounds, the implementation review and its focused
follow-up, the REAL PREFLIGHT report, `docs/user-instruction.md`, the result
report, all three Step 0029 evaluators, the Rust product implementation, and
the retained Step 0024 comparison artifacts. I then reconstructed the result
from raw files rather than accepting either Step 0029 `summary.json` or the
reported verdict as authority.

The review covered:

- every OSWorld-Human pair decision and operation assignment across all five
  folds;
- every CodeTraceBench target operation and adjacent decision, globally and
  separately for all four frameworks;
- the retained Step 0024 main-baseline raw assignments and decisions;
- every registered simple control and the OSWorld supervised OOF comparator;
- every learned grammar rule, its support/occurrence facts, total tie order,
  replacement count, termination condition, and target application;
- Rust/Python segment and assignment equivalence, population coverage, and
  additive-mass conservation; and
- the prediction-persistence and scorer-load order in both code and raw-file
  timestamps.

I did not rerun or change the experiment, edit the product/evaluators/plan,
inspect or edit the read-only paper submodule, change the paper/story/RQs, or
perform Git operations. This review file is my only edit.

## Population, Completion, And Oracle Isolation

The complete registered populations are present exactly once.

| Population | Reference | Target | Adjacent decisions | Oracle groups |
|---|---:|---:|---:|---:|
| OSWorld-Human | four folds per held-out fold | 287 sessions / 3,978 operations | 3,691 | 2,042 |
| CodeTraceBench | 2,229 sessions / 87,703 operations | 405 sessions / 20,866 operations | 20,461 | 2,948 |

The CodeTrace targets comprise exactly 213 OpenHands, 28 SWE-agent, 93
Terminus2, and 71 mini-SWE-agent sessions. Reference and target session IDs are
disjoint. Every product input row contains only `value` plus the visible
`session` and `action` fields.

The OSWorld evaluator writes independent Python segments and assignments for
each fold, then persists the Rust profile, and only afterward opens the
label-bearing scorer population. The CodeTrace evaluator constructs and
persists both Rust and Python predictions before its sole call to the official
stage loader. The observed raw-file order agrees with that control flow:
OSWorld fold predictions and profiles precede `pair-decisions.jsonl`, while
the CodeTrace profile and Python prediction files precede both scored raw
files and the summary. The algorithm-family choice remains adaptive post-hoc
development on previously observed populations, exactly as the approved plan
states; this review does not upgrade it to untouched confirmation.

## Independent Grammar And Equivalence Audit

I independently replayed grammar construction from every persisted reference
operation file. At every iteration I recomputed non-overlapping pair counts per
session, distinct-session support, and the full registered ordering key:
descending support, descending occurrences, structured expanded left/right
actions, then stable terminal/rule identity. Every selected pair, support,
occurrence count, before/after symbol total, expansion, depth, and rule ID
matched the Rust report.

- OSWorld learned 136, 121, 124, 120, and 120 rules in folds 0--4: 621 rules
  total, maximum depth 6 in each fold.
- CodeTrace learned 2,453 rules, reduced the reference from 87,703 to 17,008
  symbols, and reached maximum depth 8.
- After the final rule, no adjacent pair retained support in two reference
  sessions, confirming termination under the uncapped rule.

I separately applied every rule exactly once in creation order to each target
session. The reconstructed contiguous target segments matched the product
report exactly: 1,492 OSWorld groups and 5,187 CodeTrace groups. Expanding the
segments produced one unique assignment for all 3,978 and 20,866 target
operations respectively, with no gap, overlap, duplicate, loss, or mass
change.

The independent Python segments equal the Rust report segments exactly in all
six product runs. The separate OSWorld equivalence execution verifies the same
621 rules, 1,492 segments, and 3,978 assignments; its per-fold profiles,
segments, assignments, references, and targets are byte-identical to the
corresponding scored execution artifacts.

## Independently Recomputed Metrics

I recomputed boundary confusion matrices directly from raw pair decisions and
operation-weighted B-cubed precision/recall/F1 directly from reconstructed
partitions. All raw counts and full-precision values match the registered
summaries. Rounded values below are for readability.

### OSWorld-Human

| Method | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 | Predicted groups |
|---|---:|---:|---:|---:|---:|
| Grammar candidate | 0.452703 | 0.664142 | 0.780897 | 0.717803 | 1,492 |
| Step 0024 | 0.679922 | 0.855872 | 0.726966 | 0.786170 | 2,656 |
| Supervised OOF | 0.738768 | 0.835863 | 0.797096 | 0.816019 | 2,249 |
| Phase change | 0.333688 | 0.565077 | 0.809217 | 0.665461 | 1,355 |
| Action change | 0.477080 | 0.818318 | 0.551852 | 0.659174 | 3,135 |
| Always boundary | 0.644510 | 1.000000 | 0.513323 | 0.678405 | 3,978 |
| One session block | 0.000000 | 0.210250 | 1.000000 | 0.347449 | 287 |

The candidate's primary delta from Step 0024 is
`0.717802670181 - 0.786169543748 = -0.068366873567`. Its higher recall does
not offset the much lower precision. The 1,492-versus-2,656 group count is
consistent with over-merging, but that explanation is diagnostic rather than
a new success criterion.

### CodeTraceBench

| Method | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 | Predicted groups |
|---|---:|---:|---:|---:|---:|
| Grammar candidate | 0.255563 | 0.839528 | 0.509224 | 0.633931 | 5,187 |
| Step 0024 | 0.287106 | 0.828579 | 0.533630 | 0.649173 | 6,897 |
| Phase change | 0.225425 | 0.685564 | 0.626030 | 0.654445 | 5,980 |
| Action change | 0.267524 | 0.947623 | 0.315368 | 0.473242 | 12,941 |
| Always boundary | 0.221092 | 1.000000 | 0.141282 | 0.247585 | 20,866 |
| One session block | 0.000000 | 0.173563 | 1.000000 | 0.295788 | 405 |

The candidate's primary delta from Step 0024 is
`0.633930888617 - 0.649173103932 = -0.015242215315`. Per-framework candidate
versus Step 0024 F1 is 0.646800 versus 0.661593 for OpenHands, 0.647293 versus
0.707955 for SWE-agent, 0.597383 versus 0.593876 for Terminus2, and 0.674729
versus 0.683439 for mini-SWE-agent. The one Terminus2 improvement cannot
override the fixed complete-population rule.

The candidate run's four deterministic CodeTrace control assignments match
the retained Step 0024 population and values operation by operation. I also
recomputed Step 0024's recurrence and all four controls from its own raw pair
and operation files, globally and per framework; all values match those reused
by Step 0029. The OSWorld Step 0024 and supervised OOF values likewise
recompute from their retained raw session/pair predictions.

## Scientific Judgment

The run is **VALID**: the registered method engaged, target labels did not
enter construction or application, the main baseline is the intended retained
Step 0024 method on the same populations, metrics are non-circular, and Rust
and independent Python agree exactly.

The run is **COMPLETE**: every planned target, fold, framework, comparator,
control, assignment, and adjacent decision is present; no partial prefix is
being interpreted as the experiment.

The tested hypothesis is **CONTRADICTED**. The fixed rule required the candidate
to be no lower than Step 0024 on both complete populations and strictly higher
on at least one. It is lower on both. This judgment does not answer all of RQ3
and is not a challenge to the paper's thesis, four RQs, original AgentProf
story, or contribution surface. It bounds this one multi-session grammar
constructor on these two complete development populations.

## Required Paper Decision

**APPROVE the result and its predeclared disposition.** Restore the Step 0024
product exactly, retain Step 0029 as internal mechanism evidence, and return
the paper-level choice to REVIEW. Nothing in this result authorizes a paper
story/RQ change, a negative-result foreground in the paper, a second
target-tuned grammar variant, or a reinterpretation through boundary F1,
grammar compression, an aggregate mean, or the single Terminus2 win.

The strongest honest mechanism inference is narrow and useful: recurring
multi-action compression alone is not a better proxy for human/source-authored
operation partitions than Step 0024 on either complete population. The next
paper decision should therefore leave the current positive paper evidence and
story unchanged while selecting any future experiment by paper-level decision
value, not by an obligation to rescue this candidate.
