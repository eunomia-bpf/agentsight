# Round 5 — Terminology, Information Flow, and Paper Consistency

- **Timestamp:** 2026-07-14 04:32:26 -0700
- **Skill:** `check-terminology-infoflow`, including paper-consistency mode
- **Reviewer:** fresh independent subagent, read-only
- **Target:** complete `docs/paper/main.tex` and included architecture source
- **Disposition after fixes:** PASS

## Independent review result

The reviewer confirmed that the exact thesis, four fixed RQs, and Step 0006
headline numbers had not drifted. Its principal finding was a mechanism-identity
error: the new RQ3 text could be read as validating the release's TF-IDF
automatic stack-construction backend, but the experiment actually evaluates a
supervised Bernoulli Naive Bayes adjacent-boundary predictor and then feeds its
predicted group field into the released AgentProf projection/folding path.

### Must-fix findings

1. Distinguish the supervised RQ3 predictor from the TF-IDF automatic backend.
2. Explain that the pre-specified elements are the model family, fields,
   feature construction, and training procedure; each fold still fits its own
   parameters and threshold on training sessions.
3. Correct “nine features” to nine visible operation fields used to construct
   adjacent-pair features.
4. Stop conflating intent tags, group boundaries, group fields, and identities.
5. Do not imply the adjacent-boundary predictor is also the future task/phase/
   action tagger.
6. Define B-cubed partition F1 before interpreting it, and define the reported
   complement instead of inventing “partition distortion.”
7. Align the architecture figure with its caption and the four-stage Design
   pipeline.
8. Limit the RQ4 no-overhead statement to post-execution profile construction;
   trajectory-capture cost was not measured.
9. Define the RQ2 ranking signals and the exact meaning of target-blind.

### Should-fix findings

- Rename Design `R1–R3` to avoid collision with Evaluation `RQ1–RQ4`.
- State where RQ1 prompt tags came from.
- Remove internal experiment vocabulary such as `oracle-eligible`, `field
  interface`, and `release-profiler folding path`.
- Restore the formal name `semantic operation stack model` where it drifted.
- Expand AP and RSS at first use.
- Keep the complete-RQ3 evidence frontier in Scope rather than repeating it at
  the end of the positive RQ3 result.
- Use the already-defined term `semantic fields` instead of creating
  `semantic responsibility fields`.

## Applied fixes

### RQ3 mechanism and terminology

- Replaced every high-level `fixed boundary tagger` description with
  `pre-specified supervised boundary predictor evaluated out of fold`.
- Rewrote RQ3 around categorical operation fields: task/phase/action labels are
  distinct from the group boundary tested in this experiment.
- Named the tested mechanism as a supervised Bernoulli Naive Bayes
  adjacent-boundary predictor.
- Precisely listed what was pre-specified and what each session-blocked fold
  fits using its training sessions.
- Explained the integration boundary: predicted boundaries become an ordinary
  group field; the released AgentProf path only projects and folds that field.
- Explicitly stated that this experiment does not validate the Implementation
  section's TF-IDF automatic stack-construction backend.
- Replaced table label `Fixed tagger` with `Supervised predictor`.
- Replaced `learned-group stacks` with stacks projected on the predicted group
  field.
- Kept the larger fixed RQ3 hypothesis intact. Scope now says that task, phase,
  and action require matched annotations and their corresponding pre-specified
  taggers or mappings; it does not pretend the boundary predictor handles all
  four components.

### Metrics and external source

- Defined operation-weighted B-cubed partition F1 as per-operation predicted–
  human group overlap that captures merging and fragmentation.
- Rephrased the complement exactly as `1 - B-cubed F1`.
- Added and annotated the original Bagga–Baldwin source after verification
  against the ACL Anthology's primary metadata and PDF:
  `https://aclanthology.org/P98-1012/`.
- Preserved all RQ3 numbers: 287 sessions, 3,978 operations, 3,691 adjacent
  pairs, 2,042 human groups, 0.739/0.645 boundary F1, 0.816/0.678 B-cubed F1,
  and 2,249 output stacks.

### RQ2 information flow

- Defined target-blind as excluding test targets from tag, stack, and score
  construction.
- Identified the shared external step signals: released AgentProcessBench
  judge votes and predicted steps from the HINTBench/TraceElephant localization
  procedures.
- Defined group scoring: mean risk for AgentProcessBench and maximum 95% Wilson
  lower hit-density along a profile prefix for the other two.
- Stated that target labels enter only after ranking to compute
  operation-weighted average precision or inspection work.
- Renamed the table comparator from `Raw` to `Raw action`.

### Other consistency fixes

- Renamed Design requirements `D1–D3`, leaving the four paper RQs unchanged.
- Stated that RQ1 prompt tags came from the local 3B-model backend and are
  treated as declared categories, not an independent correctness oracle.
- Restored `semantic operation stack model` in Implementation.
- Expanded `average precision (AP)` and `resident set size (RSS)` at first use.
- Restricted RQ4's no-online-overhead claim to profile construction and stated
  that capture is excluded.
- Standardized Related Work on `semantic fields`.
- Updated the architecture diagram to show two real input forms converging on
  uniform operations, followed by field derivation, stack construction plus
  folding, and output profiles. Parsing/reading are labeled on the input edges.
- Updated the caption and description to match the rendered figure.

## Scope-control decisions

- No thesis, RQ, hypothesis, contribution, or experiment was removed.
- No new experiment, model variant, benchmark, threshold, or control was added.
- No change was made to the canonical `docs/agentpprof-paper` submodule.
- The RQ3 result remains positive and prominent; its remaining evidence need is
  stated once in Scope instead of weakening the result paragraph.
- The paper briefly grew to nine pages because of the definitions. Only the
  newly added explanatory prose and repeated Related Work wording were
  compressed; no evidence or claim was deleted. The final build is eight pages.

## Verification

- `make -C docs/paper`: PASS
- PDF: 8 pages
- Undefined citations/references: none
- Overfull boxes: none
- `git diff --check`: PASS after removing one trailing space
- Architecture figure: visually inspected; nodes and labels are readable and
  match the caption
- Canonical submodule: unchanged at `7f80c433c9555317a2aa45a78d0ff93518f4c12c`
- RQ3 number search: no old `fixed tagger`, `boundary identity`, `oracle-eligible`,
  or `learned-group` wording remains

## Residual items

The complete RQ3 still needs matched task/phase/action evidence, and RQ1 still
needs an independent attribution oracle. Those are scientific experiment
frontiers, not terminology defects, so this writing round does not try to hide
or solve them in prose.
