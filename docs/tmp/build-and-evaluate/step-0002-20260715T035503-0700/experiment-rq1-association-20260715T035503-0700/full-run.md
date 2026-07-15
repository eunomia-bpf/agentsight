# RQ1 Full Run

Regenerated after final path-evidence repair: 2026-07-15T08:18:48-07:00
Experiment base: `1d6497a4` plus the implementation under review
Frozen mature endpoint: `25fce75ab1827adf0cc0bfd7d8205c306595841e`

## Terminal run matrix

| Cell | Status | Evidence |
|---|---|---|
| real preflight | valid dependency | second and final allowed preflight; three native parsers; privacy scan clean |
| controlled proposed/baseline | complete | identical 50-positive/50-null held-out pairs |
| controlled ablations | complete | no-hunk and literal-only mechanisms |
| controlled edge coverage | complete | rename, recreation, ambiguity, squash, split, moved/rewritten line, clock skew, merge, and pathless for each native schema |
| mature naturalistic transfer | complete, inconclusive | 2026-06-02 and 2026-06-23; two independent annotators |
| 2026-07-14 naturalistic cell | right-censored, excluded | endpoint only 4.8 hours after day end; cannot supply 24-hour retrieval or seven-day oracle |
| naturalistic Gemini write transfer | missing, not imputed | mature days contain Gemini sessions but no eligible Gemini write-path pair |
| Git-hunk to current-line lineage | complete, inconclusive | 110 mature targets; 37 endpoint line predictions after exact-hunk safety repair |

Two early fixture-generation attempts failed before producing predictions
because automatic Git maintenance raced rapid nested-repository commits. A
later diagnostic rerun also exposed a user-level commit-message hook that
removed vendor names. The final fixture disables automatic maintenance and
hooks only inside its disposable repository. No method rule, truth label,
threshold, scenario, or seed changed.

## Controlled result

The proposed candidate-set method passed every frozen gate. It made 50 non-null
predictions, all correct, recovered all 50 positive targets, classified all 50
nulls, and obtained Wilson lower bounds of 0.929 for precision, positive recall,
and null specificity. ECE was 0.030 and Brier score was 0.00135.

The nearest same-literal-path baseline did not pass: precision was 0.667
(Wilson lower bound 0.554) and null specificity was 0.50 (lower bound 0.366).
Its Brier score was 0.1667. The paired 10,000-resample interval for proposed-
minus-baseline Brier was [-0.1967, -0.1348]. Removing edit-hunk evidence
reproduced the baseline failure. Literal-only association matched the primary
controlled result, so the measured advantage is attributable to exact-hunk
evidence; lifetime/rename value remains diagnostic rather than established.

The repaired fixture contains 337 exported events, including exactly one
pathless tool event for each Claude, Codex, and Gemini schema. Forty diagnostic
event--path pairs cover the frozen edge families; split operations contribute
two path units per schema. They do not enlarge primary gate support.

Reproducibility note: the final exports are
`raw/private/naturalistic/2026-06-*.json`; `truth-current.json` is the only
truth file accepted by the final metrics script. It hard-fails unless that
truth maps exactly and injectively onto every association in both exports.
Earlier `naturalistic-mature/` files predate the call-ID, exact-hunk, and shell
grammar repairs and must not be used to regenerate public metrics.

## Mature naturalistic transfer

The two mature source days contained 933 eligible event--path pairs. Independent
annotators agreed on 95.606% of labels (Cohen's kappa 0.827), with identical
target sets. Applying the frozen path-level null definition and retaining
candidate-bearing cases without content evidence as unadjudicable yielded 110
target, 45 null, and 778 unadjudicable pairs. All 41 disagreements were
reconciled as exhaustive no-candidate path-level nulls.

After reconciling Codex completions by call ID and suppressing event-level
fingerprints for multi-file/multi-hunk patches, the proposed method correctly
classified 103/110 targets and 45/45 nulls. Top-1 precision was 0.972 and
positive recall was 0.936; null specificity was 1.0 with a 0.921 Wilson lower
bound, and classification accuracy was 0.955. ECE was 0.192 and Brier score was
0.0912. Disagreement-as-error accuracy was 0.690. The nearest-path baseline
reached 0.736 precision/positive recall and 0.813 classification accuracy.
Paired intervals favored the proposed method for Brier and candidate-set recall.

A final conservative shell grammar separated compound commands, pipelines,
nested shell payloads, and unspaced redirections; it also rejected revisions,
API routes, variables, image names, and expression tokens as file paths.
The final repair additionally resolves tool-level `workdir`/`cwd`, explicit
`cd`, segment-local writes, heredoc bodies, input redirection, and `cp -t`
operands. Re-exporting the frozen 07:00Z observation windows yielded 560 and
373 mature write-path observations. Relative to the preceding 937-pair freeze,
semantic rebase carried 926 labels, removed 11 obsolete parser-derived pairs,
and exposed seven new pairs. Both independent annotators labeled the blinded
seven-pair delta before the full 933-pair reconciliation. The controlled and
lineage results were regenerated.

Naturalistic transfer did **not** pass the frozen gate: null support was 45,
five short of the required 50, and confidence remained miscalibrated (ECE 0.192
> 0.10). The precision, recall, and specificity lower-bound gates passed. The
preregistered selection remains `descriptive_only`. Proposed and literal-only
accuracy were identical, so the naturalistic run also does not demonstrate a
lifetime/rename advantage.

The original July 14 numbers are withdrawn. Its endpoint was 2026-07-15
04:48 PDT, only 4.8 hours after the sample day ended. The private artifact is
retained, but all labels, 24 apparent nulls, metrics, lineage rows, and transfer
claims from that cell are excluded. A valid rerun requires an endpoint after
2026-07-21; this is recorded as right-censored rather than silently replaced.

## Line-stage result

For 110 independently agreed mature target events, the endpoint linker required
a unique current content block and checked Git blame origin independently. It
emitted 37 line predictions: 36 were correct and one was a blame mismatch
(precision 0.973, Wilson lower bound 0.862). Fifty-seven targets were not unique at
the endpoint, five contained no added hunk, and eleven lacked a supported
single-file/single-hunk edit fingerprint. Corrected subgroup denominators
sum to all 110 targets by day and vendor. The line gate failed support (37 <
100) and lower-bound precision (0.862 < 0.95); line overlays are inconclusive.

## Privacy and reproducibility

Private exports contain no serialized prompt, command, preview, old/new string,
content field, or absolute home path under the frozen scans. Deterministic edit
hashes are pseudonymous evidence, not strong de-identification. Raw packets,
predictions, annotations, reconciliation, and line rows remain under ignored
`raw/private/`; public artifacts are aggregate-only.

## Scientific decision

The completed controlled result supports exact-hunk evidence as a useful
mechanism over nearest-path matching. Mature naturalistic transfer and line
lineage are inconclusive, July is right-censored, and naturalistic Gemini writes
are missing. Downstream views may show candidate sets, ambiguity, unmatched
states, exact-hunk evidence, and separate process/Git/endpoint layers. They may
not claim calibrated real-history association, authorship, certain provenance,
line survival accuracy, cross-vendor transfer, or lifetime-aware superiority.
