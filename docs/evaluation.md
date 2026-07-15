# Evaluation

## Open research questions

| RQ | Evidence promised | Status |
|---|---|---|
| RQ1 Evidence recoverability and association accuracy | Controlled known-link histories; double-annotated naturalistic sample; event-to-Git and Git-lineage accuracy/calibration; source ablation | Open; first implementation gate |
| RQ2 Recurring process patterns and outcomes | Discovery/held-out split; vendor/model/session strata; event-only predictors versus durable Git and endpoint outcomes | Gated by RQ1 |
| RQ3 Review utility | Frozen tasks against strong Git-only, native event table, noncoordinated full joined table, and coordinated core views | Gated by RQ1 and participant protocol |
| RQ4 Long-horizon scalability | Export/render throughput and latency plus scale-matched navigation/crowding tasks | Open after minimum gallery |

## Available real history

The initial feasibility audit found AgentSight-specific Claude sessions across
20 calendar dates from 2026-06-01 through 2026-07-15. Local Codex history spans
the same period at substantially larger volume. These counts are environment
inventory, not paper results; a privacy-safe, repository-filtered export and
join-quality audit are still required.

## Baseline obligations

- Strong Git-only visualization over identical repository/time ranges.
- Native normalized event table without Git join or coordinated views.
- Noncoordinated table over the complete joined evidence, separating
  information gain from visual coordination.
- Perfetto trace over equivalent fields where its format permits, plus Gource
  animation export and Hercules aggregate cross-check where reproducible.
- Githru as a strong Git visual-analytics baseline when runnable; otherwise
  document artifact limits and construct the strongest reproducible analogue.
- Ablations for event/Git/survival sources, stable versus recomputed layout,
  raw versus overview aggregation, and overview versus linked detail.

## RQ1 ground truth and gates

The join is never evaluated by coverage alone. A controlled fixture will create
known event-to-change links, pathless events, unmatched events and Git changes,
ambiguous candidate windows, renames, deletion/recreation, and refactoring-
sensitive lines. A separate naturalistic sample is independently annotated by
two reviewers before reconciliation.

The controlled truth label is observed edit-to-commit correspondence created by
the fixture. Naturalistic adjudication labels only whether evidence supports a
candidate correspondence; it does not label causality or authorship. The
primary association unit is an event--normalized-path pair, and the primary Git
target is a rename-aware file-change entry in a non-merge commit. For an event
at time `t`, the frozen primary candidate window is `[t - 15 minutes, t + 24
hours]` on the same continuous file lifetime; 1-hour and 6-hour upper bounds are
reported only as prespecified sensitivity analyses. Zero candidates, one
candidate, multiple candidates, and unadjudicable evidence are separate labels.

Primary association accuracy uses all adjudicated association-eligible event--
path pairs as its denominator. Top-k recall uses adjudicated pairs with a non-
null target; unmatched specificity uses adjudicated null-target pairs; Git-side
coverage uses all non-merge file-change entries in the selected corpus. Merge
changes are a separate stratum. Squash commits permit many events to correspond
to one Git change; split work permits one event to retain several candidates.
No maximum-weight matching forces a bijection.

A continuous file lifetime begins at a Git addition, follows detected renames,
and ends at deletion. Same-path recreation receives a new lifetime identifier.
Path endpoint survival means that this lifetime reaches the selected HEAD. Line
endpoint survival additionally requires the separately evaluated hunk-to-
current-line link.

Report accuracy, precision/recall where defined, top-k candidate recall,
calibration/Brier score, ambiguity, and unmatched yield separately for
event-to-Git associations and Git hunk-to-current-line lineage. Stratify by
vendor/schema, rename class, payload availability, confidence, and path versus
line granularity. Only validated strata may support RQ2/RQ3 event-to-outcome
claims; all excluded and ambiguous records remain visible in descriptive views.

Thresholds are fit only on controlled/calibration data and evaluated once on a
held-out scenario split and the unreconciled naturalistic annotations. A path-
level candidate stratum is supported only with at least 30 positive and 30
null adjudicated pairs, a 95% Wilson lower bound of 0.90 for candidate precision
and 0.85 for unmatched balanced accuracy, and expected calibration error at
most 0.10. A line overlay additionally requires at least 30 adjudicated linked
hunks and a 95% Wilson lower bound of 0.95 for the joint event-to-hunk and hunk-
to-current-line precision. If no stratum passes, RQ2/RQ3 cannot make joined
event-to-outcome claims and the gallery is bounded to descriptive process,
Git, mismatch, and endpoint views.

## Frozen RQ3 task map

| Task | Answer evidence | Conditions and primary metrics |
|---|---|---|
| Find an edit with no recorded later verification action | Deterministic event order/status | Four conditions; accuracy, time, confidence calibration |
| Classify eligible-unmatched versus candidate-associated events | RQ1 adjudicated sample | Four conditions; accuracy, time, confidence calibration |
| Explain a cross-file exploration sequence | Recorded event order and blinded rubric | Four conditions; rubric score, time, strategy trace |
| Find high-change-frequency surviving code | Git/current tree negative control | Git-only versus joined conditions; accuracy and time |

## Experimental sequence

1. Build controlled histories and implement only enough join/export machinery
   to run the RQ1 preflight.
2. Run a privacy-safe real preflight on several days of AgentSight history;
   audit mismatch categories before tuning on more data.
3. Freeze join rules, confidence strata, pattern definitions/discovery split,
   RQ3 task wording, and core view set.
4. Run the full multi-day export and independent naturalistic join audit.
5. Run held-out pattern/outcome analysis and sensitivity across join strata.
6. Run the approved diagnostic-task study or, if recruitment remains blocked,
   report RQ3 as unexecuted rather than substituting an informal demo.
7. Measure export, artifact size, first render, brush/scrub latency, memory,
   navigation accuracy, and crowding over explicit event/path/duration ranges.

Raw outputs will live under the step-specific experiment directory and be
linked here after review. No result placeholder is treated as evidence.
