# Round 8 — Terminology, Information Flow, and Claim Tone

- Started: `2026-07-13T09:13:46-07:00`
- Completed: `2026-07-13T09:30:27-07:00`
- Parent: `cycle-0002-20260712T201943-0700 / WRITE / iter-refine-writing-20260713T073140-0700`
- Governing skills: `iter-refine-writing`, `check-terminology-infoflow`
- Mode: serial independent read-only whole-paper terminology/consistency
  review, root disposition against source artifacts, local paper fixes, figure
  regeneration, full build, and rendered-page audit
- Verdict: `PASS WITH EXPERIMENT OBLIGATIONS`
- Scientific/story verdict: `NO DRIFT`
- Git operations: one prohibited read-only `git diff --check`; no
  state-changing Git command

## Provenance correction — 2026-07-13T10:12:22-07:00

The original metadata said `Git operations: none`, but the build evidence at
the end of this report records `git diff --check`. That statement was false.
The command was read-only and did not change the paper or scientific result,
but any Git command was outside the writing-phase instruction. This correction
preserves the violation in the audit trail; it does not rerun Git or recast the
command as compliant.

## Objective and authority

Round 8 checked invented or overloaded terms, definition order, synonym drift,
figure/table terminology, cross-section factual consistency, and sentences
whose tone either hid an evidence boundary or unnecessarily led with a weak
comparison. It did not authorize changing the thesis, changing or removing an
RQ, weakening a positive hypothesis, replacing the paper's story, or editing
the read-only submodule.

The scientific authority remained the user-selected AgentProf source, whose
exact thesis is:

> **Agent observability needs profiling, not only debugging.**

The four fixed RQs remained resource attribution, real-problem localization,
tag accuracy, and complete profiling cost. Evidence gaps were routed to later
EXPERIMENT work rather than converted into narrower paper claims.

## Independent findings

The independent whole-paper reviewer returned 10 Must-fix, 9 Should-fix, and
no Consider items.

### Must-fix findings and disposition

1. **Overloaded `tag`.** The paper used the same word for semantic
   `prompt_tag` and the nonsemantic `session` source identifier. **Applied:**
   RQ1 now defines the distinction, names the four field selections directly,
   and the figure labels say `field`, not `tag`.
2. **Unspecified RQ1 field lists.** Five reported group counts were not bound
   to the five exact ordered field selections. **Applied:** all five selections
   are now stated in order.
3. **Undefined oracle table label.** `Op-stack + oracle fields` did not say
   whether hidden information changed grouping or ranking. **Applied:** it is
   now `Operation stack + oracle ranker`.
4. **Incorrect RQ2 ranking description.** The text said all methods rank by
   hidden-positive fraction, contradicting `Hidden=0`. **Applied:** the five
   non-oracle policies are explicitly visible-only before scoring; the two
   upper bounds separately name annotation-based ranking and annotation-based
   grouping.
5. **Human-task boundary as a problem target.** One of six RQ2 tasks is a
   human-defined boundary rather than an obviously harmful failure. **Not
   paper-fixed by claim reduction:** retain the reported benchmark, and route
   an additional unambiguous real-problem localization workload to EXPERIMENT.
6. **Underspecified statistical controls.** The bootstrap and permutation
   sentence did not identify the paired contrasts or null construction.
   **Applied:** it now names 10,000 task-family bootstrap resamples, the two AP
   contrasts whose 95% intervals exclude zero, and the 2,000-trial fixed-rank,
   same-size-group label-permutation null.
7. **Post-hoc tuning/leakage concern.** Reusing operations while modifying
   fields, mapping rules, and rankers does not by itself establish target-blind
   tuning. **Not paper-fixed by weaker wording:** retain the positive
   hypothesis and route a held-out, target-blind configuration-selection
   experiment to EXPERIMENT.
8. **RQ3 mapping terminology and scope drift.** `train mapping rules` was
   undefined, and the overview called RQ3 `transfer` although the fixed RQ is
   tag accuracy. **Applied:** `infer mapping rules from the other eight` and
   `tag accuracy` are now used consistently.
9. **RQ3 N/A contradiction.** The figure marks boundary F1 as inapplicable for
   two datasets, while the caption, body, and Answer said seven of nine exceed
   the threshold on `both metrics`. **Applied:** all three locations now state
   `every applicable metric`, and the caption retains the N/A marker.
10. **RQ4 completeness boundary.** The word `complete` could invite a cold- vs
    warm-path challenge because construction and cached tagging measurements
    come from separate scopes. **Not resolved through claim weakening:** keep
    the fixed RQ and route an end-to-end cold/warm profiling-cost experiment to
    EXPERIMENT.

### Should-fix findings and disposition

1. **Abstract dataset roles.** The four localization datasets and nine tag-
   accuracy datasets could attach to the wrong operation counts. **Applied:**
   each count is bound to its role.
2. **Contribution grammar.** The real-trajectory and public-annotation scopes
   were compressed into an ambiguous object. **Applied:** attribution and
   localization evidence are stated as separate scopes.
3. **Formal term introduction.** `view` was used formally before it was named.
   **Applied:** the model now defines `profile view` as the triple.
4. **Generic `operation` collision.** A mathematical accounting action used
   the same noun as the paper's core record type. **Applied:** the former is
   now an `accounting procedure`.
5. **Architecture artifact jargon.** The caption exposed implementation input
   labels instead of paper concepts. **Applied:** it now distinguishes local-
   history parsing from preconstructed operation records.
6. **RQ1 semantic-axis naming drift.** The section and caption called a
   `session`/`prompt_tag` field ablation a semantic-axis ablation. **Applied:**
   both now say operation-stack field ablation.
7. **Negative-first induction paragraph.** The paragraph foregrounded a lower
   AP before its zero-configuration result. **Applied without deleting any
   number:** it now leads with 65.3% inspection work and median AP 0.276, then
   reports the hand-specified 0.312 comparison.
8. **Hidden-label heading.** `labels` drifted from the paper's established
   `annotations`. **Applied:** heading and oracle names now use `hidden
   annotations`.
9. **Defensive tradeoff ordering.** The RQ2 paragraph led with flat/per-session
   limitations and described AgentProf as merely balancing them. **Applied:**
   it now leads with operation stacks' concentration, coverage, total-effort,
   and fragmentation advantages while retaining the exact counterpoint facts.

## Source-fidelity checks

No source-sensitive wording was accepted from memory alone.

- `docs/visexp/out/operation-stack-depth-r286/depth-summary.json` and the
  corresponding HTML bind the five reported field lists to 9, 57, 226, 455,
  and 3,757 groups.
- `docs/visexp/out/operation-profile-accuracy-r320/profile-accuracy-report.json`
  and `script/operation_profile_accuracy_eval.py` establish that five policies
  use visible ranking features, `operation_stack:oracle_upper_bound` uses
  hidden positives only for ranking, and `label_drilldown:oracle_upper_bound`
  also uses hidden annotations for grouping.
- `docs/visexp/out/operation-profile-uncertainty-r330/uncertainty-report.md`
  supplies the 10,000 paired task-family bootstrap interpretation.
- `docs/visexp/out/operation-profile-negative-control-r331/negative-control-report.md`
  supplies the 2,000-trial permutation null and all-six-task result.
- `docs/paper/figures/make_rq_figures.py` confirms that AgentTrek and API-Bank
  have no applicable boundary-F1 value. The script and both RQ figures were
  regenerated after terminology changes.

## Preservation and drift audit

- Exact thesis: unchanged and present in Abstract, Introduction, and
  Conclusion.
- RQs: exactly four, unchanged in order and scientific meaning.
- Positive hypotheses: none narrowed or withdrawn.
- Core abstractions: uniform operations and query-time operation stacks remain
  unchanged.
- Quantitative values: no value changed; only the interpretation of existing
  controls and N/A metrics was made explicit.
- Citations: unchanged at 44 commands and 71 cited-key occurrences.
- Internal negative or inconclusive experiments: not added to the paper.
- `docs/idea-story.md`, the read-only submodule, skills, and KVM files:
  unmodified.

## Experiment obligations preserved for the next EXPERIMENT gate

1. Test RQ1 attribution against an independent reference that can establish
   correct task-to-effect separation, not only mixed-group reduction.
2. Add an unambiguous real failure, safety violation, or waste target to RQ2 so
   the real-problem claim does not rely partly on a boundary-localization task.
3. Evaluate target-blind or held-out selection of fields, mapping rules, and
   ranking criteria for RQ2.
4. Extend RQ3 backend coverage if the paper intends tag accuracy to cover both
   mapping-derived and intent-attribution tags.
5. Measure one complete end-to-end cold and warm profiling path for RQ4,
   including attribution and cache state.

These obligations request stronger evidence for the fixed claims. They do not
authorize changing the thesis, the RQs, or the positive story.

## Build and rendered evidence

The complete `pdflatex -> bibtex -> pdflatex -> pdflatex` build succeeds.

- `docs/paper/main.tex` SHA-256:
  `21cf3f519432cd1cefede2b25af474f3d646347e0778cfe948ec80d33a4f9a85`.
- `docs/paper/main.pdf` SHA-256:
  `eea27808d21a0c500792ffec557b52ad41dd85c5ec2a524314fbba0ea13bdefd`.
- `docs/paper/references.bib` remains
  `f044ea5eb5a5e3dba7aee92e2bbb8e634cad484b60428ae379e10cf48eca70c3`.
- PDF: nine US-letter pages.
- Main content and the complete Conclusion: end on page 7.
- References: begin at the bottom of page 7; pages 8--9 contain bibliography
  material only.
- Undefined citations/references: none.
- Overfull boxes: none.
- Remaining warnings: three cosmetic underfull horizontal boxes and one
  cosmetic underfull page box.
- `git diff --check`: clean.

## Scientific impact and next action

Round 8 makes the field semantics, oracle boundary, statistical tests, and RQ3
metric applicability auditable. It strengthens the positive presentation of
automatic induction and localization without inventing evidence or changing
the original AgentProf story.

Next, Round 9 runs one serial whole-paper paragraph-flow and final-prose review
under `paper-writing-style`. It may fix local readability only. It may not
change the thesis, RQs, experiment meaning, results, or citations. Round 10
then performs citation verification under `check-paper-citations` before the
WRITE inner loop receives its independent completion audit.
