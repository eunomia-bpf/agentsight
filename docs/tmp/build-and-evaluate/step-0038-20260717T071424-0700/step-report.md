# Step 0038 — RQ3 Construct and Metric Audit

## Purpose

This step decides whether the next outer action should be a new literal-phase
experiment or a targeted WRITE correction. It does not change the exact thesis,
the four fixed RQs, the two core abstractions, the accepted recurrence
constructor, or the read-only submodule. It audits whether the current request
for another taxonomy experiment follows from the authoritative RQ3 or from a
later over-strong interpretation of that RQ.

Timestamp: `2026-07-17T07:14:24-07:00`.

## Authoritative Inputs

- Read-only story source: `docs/agentpprof-paper/main.tex`, commit
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.
- Original RQ3 figure source:
  `docs/agentpprof-paper/figures/make_rq_figures.py`.
- Original RQ3 raw summary:
  `docs/visexp/out/operation-map-leaveout-api-r285/leaveout-summary.json`.
- Current paper: `docs/paper/main.tex`.
- Current evidence frontier: `docs/evaluation.md`.
- Current story invariants: `docs/idea-story.md` and
  `docs/user-instruction.md`.

The worktree began clean on
`research/semantic-flamegraph-artifacts-v2` at
`4abe73ec58391d72a2754952f21aeb1ef477347b`. The submodule was inspected only;
it was not edited.

## Fixed RQ and Construct

The authoritative question remains exactly **RQ3 — How Accurate Are the
Tags?** The original paper operationalized it by comparing a mapping-derived
`phase` partition with benchmark-native `action` values using V-measure and by
comparing their transition locations using boundary F1. It did not evaluate
literal phase names against independently annotated phase names.

The original construct therefore contains two distinct objects:

1. **named semantic tags**, for which exact class identity can be tested; and
2. **semantic structure**, for which partitions and transition boundaries can
   be tested even when cluster names are permutation-invariant.

The current paper preserves the fixed RQ and evaluates both objects more
directly: literal task-family and action labels use multiclass metrics, while
task/group partitions and operation boundaries use structural metrics. Requiring
a universal literal phase-name ontology is an additional construct, not a
requirement stated by the original RQ3 protocol.

## Metric Classification

| Measurement target | Current metric | Status | Paper role |
|---|---|---|---|
| Ranking independently annotated problem operations | Per-query AP and MAP | Standard information-retrieval/ranking metrics | RQ2 primary |
| Closed-set task/action identity | Macro-F1 and accuracy | Standard multiclass metrics | RQ3 primary for literal labels |
| Predicted versus reference partitions | V-measure | Standard permutation-invariant clustering metric | RQ3 primary for task partitions |
| Predicted versus reference operation groups | Ordinary, unweighted B-cubed precision/recall/F1 | Standard partition/coreference metric | RQ3 primary for group structure |
| Exact adjacent transition decisions | Precision, recall, and F1 | Standard binary metrics on a project-declared exact-boundary unit | RQ3 primary for boundaries; the unit must be stated |
| Ranking under a 20% inspection budget | Recall at 20% inspection budget | Valid but protocol-specific | RQ2 secondary only; never call it fixed-rank `Recall@20` |
| Resource-weighted B-cubed | Published weighted extension; provider-token weighting is a non-default application | Valid extension, not the ordinary default | Sensitivity analysis only, never the sole headline result |

The formulas are not the main problem. Metric validity also requires the
reference label to represent the claimed construct. A standard V-measure cannot
turn native action identity into independent literal phase-name truth.

## Independent Recalculation of the Original RQ3 Result

The raw leave-dataset-out summary contains 9 datasets and 13,265 operations.
Direct JSON recomputation gives:

- 7/9 datasets have mapped phase/action V-measure greater than 0.7;
- 6/9 datasets have numeric mapped boundary F1 greater than 0.7;
- only 6/9 have both numeric metrics greater than 0.7;
- `agenttrek` has V-measure 0.8617 but no applicable boundary value in the
  figure; its raw `0.0` sentinel cannot count as greater than 0.7;
- `api-bank` likewise has an inapplicable boundary in the figure;
- `toolbench` has V-measure 0.1342 and boundary F1 0.3533.

Consequently, the original caption and prose claim that seven of nine datasets
exceed 0.7 on **both** metrics is not supported by its own raw artifact. The
supported summaries are either “7/9 exceed 0.7 V-measure” or “6/7 datasets with
an applicable boundary measurement exceed 0.7 on both.” Neither authorizes the
stronger literal sentence that the method assigns the “correct semantic phase.”

There is a second construct issue. For several datasets, the no-mapping
`phase`/`action` comparison is already V-measure 1.0 and boundary F1 1.0. The
learned mapping commonly lowers those values while reducing stack cardinality.
That behavior measures a coarsening/compression relation to native actions; it
does not by itself demonstrate more accurate literal phase identity. The
original raw result is therefore useful development history, but it should not
replace the current paper's direct task/action and independently grouped
structure evidence.

## Candidate Literal-Phase Sources

Two sources were screened without modifying the project:

- GUIDE/GuideBench is scientifically promising because it contains externally
  annotated GUI behavior states organized under phases and uses accuracy for
  its published classification protocol. Its Hugging Face data files are gated
  behind contact-sharing acceptance, and this environment has no authenticated
  access. The autonomous pipeline records that uncertainty and continues; it
  neither bypasses access terms nor waits for a person.
- OpenDiscoveryTrace is openly available, but its phase value is elicited from
  the acting model by a system prompt and parsed from the model's own response.
  It is not an independent phase annotation and is therefore unsuitable as the
  decisive RQ3 reference.

These findings do not prove that no useful literal-phase corpus exists. They do
show that immediately adding another taxonomy experiment is not currently the
highest-paper-value action.

## Gate Decision

**Do not admit a new experiment in this step. Route to targeted WRITE and then
full-paper REVIEW.**

Reasoning:

1. The fixed RQ3 is already evaluated with standard metrics appropriate to
   named labels, partitions, and boundaries.
2. The original authoritative protocol did not require independent literal
   phase-name classification.
3. The current “literal phase is the remaining blocker” arose from later
   wording that collapsed phase/group structure into literal identity.
4. The best immediately available candidate is access-gated; the open
   alternative is self-reported rather than independent.
5. Another taxonomy cell would not improve the current operation-stack
   constructor, change a paper-level RQ answer, or repair the main AAAI
   readiness concern as directly as precise construct/metric alignment.

The WRITE correction must be minimal and non-narrowing:

- keep the exact RQ title and positive tag-accuracy program;
- keep task, phase, action, and boundary as supported semantic dimensions;
- state that named task/action tags use literal multiclass evaluation;
- state that mapping-derived phase/group structure uses standard
  permutation-invariant partition and exact-boundary evaluation;
- remove only the unsupported implication that a universal literal phase-name
  benchmark is mandatory;
- preserve every empirical number and the complete original story spine.

## Proposed Files

- `docs/idea-story.md`: clarify the fixed RQ3 hypothesis and record why this is
  restoration of the original construct rather than a smaller RQ.
- `docs/evaluation.md`: replace the automatic literal-phase blocker with the
  metric/construct distinction and route to an unprimed paper review.
- `docs/implementation.md`: describe the current product/evaluation boundary
  without treating a universal phase ontology as a missing implementation.
- `docs/paper/main.tex`: change only the opening RQ3 protocol paragraph so the
  claimed annotations exactly match the measurements.

No abstract, introduction, background, motivation, system design, thesis,
contribution, RQ heading, algorithm, result number, bibliography, or submodule
file is in scope for this correction.

## Required Independent Audit

An independent reviewer must recompute the 9-dataset counts, inspect the current
and original RQ3 protocols, classify the metrics, and decide whether the proposed
WRITE route preserves rather than narrows the paper. Any substantive objection
is incorporated before the outer gate advances.

The completed [independent construct audit](independent-construct-audit.md)
reproduces the 9-dataset counts and agrees that a literal phase-name experiment
is not a blocker. It identified two bounded corrections: explicitly reuse the
existing complete CodeTraceBench phase-structure result in RQ3, and classify
weighted B-cubed as a published extension with non-default provider-token
weights. Both were incorporated. The final independent verdict is **PASS; route
to unprimed whole-paper REVIEW without admitting a new taxonomy experiment**.

## Build and AAAI-27 Format Verification

After the targeted source edit, `make` in `docs/paper` completed through
pdflatex, BibTeX, and two final pdflatex passes. The resulting PDF is nine
US-letter pages. Main content ends on page seven; References begins on page
eight, and pages eight and nine contain references only. The log contains no undefined citation,
undefined reference, or overfull-box warning.

The official AAAI-27 Main Technical Track call currently limits submissions to
seven pages of main content and nine pages total, reserving pages after seven
exclusively for references. A fresh download of the official author kit from
`https://aaai.org/authorkit27/` gives byte-identical workspace copies:

- `aaai2027.sty` SHA-256:
  `391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`;
- `aaai2027.bst` SHA-256:
  `5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`;
- `AnonymousSubmission2027.tex` SHA-256:
  `035ebdb17e57885a1fd43a188fd17777bdbf90f1fda1a1e000c49c7f52ce1f9d`.

This verifies the current venue wrapper and page budget; it does not by itself
establish scientific acceptance readiness.

A second read-only audit caught one rendered Conclusion fragment above
`References` on page eight after the phase cross-reference was added. The
Conclusion's second sentence was shortened without changing the exact thesis or
its operation-stack meaning, and the paper was rebuilt. The final page-seven
tail contains the complete Conclusion, while page eight now begins with
`References`.

The final second-round convergence verdict is **PASS with 0 must-fix items**.
Step 0038 may be committed and the outer loop may enter a genuinely unprimed
whole-paper review.
