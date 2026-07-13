# Round 9 — Paragraph Flow and Final Prose

- Started: `2026-07-13T09:30:27-07:00`
- Completed: `2026-07-13T09:47:00-07:00`
- Parent: `cycle-0002-20260712T201943-0700 / WRITE / iter-refine-writing-20260713T073140-0700`
- Governing skills: `iter-refine-writing`, `paper-writing-style`
- Mode: serial independent read-only whole-paper review, root disposition,
  source-fidelity checks, local prose fixes, full build, and rendered-page audit
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

Round 9 checked paragraph roles, sentence-to-sentence information flow, stale
referents, parallel structure, note-like definition runs, cross-section result
scope, self-attacking presentation, and final whole-paper prose. The reviewer
explicitly used `paper-writing-style`, read the complete user instructions,
idea story, and current paper, and edited no file.

The user-selected AgentProf source remained authoritative. The exact thesis
remained:

> **Agent observability needs profiling, not only debugging.**

The four fixed RQs remained resource attribution, real-problem localization,
tag accuracy, and profiling cost. Neither the reviewer nor the root was
authorized to narrow them.

## Independent findings and root disposition

The independent reviewer returned 15 Must-fix, 16 Should-fix, 3 Consider, and
8 experiment-obligation items. All prose Must-fix items were accepted. The
Should-fix items were either already satisfied or accepted with local wording
that preserves the paper's established terms. All three Consider items were
accepted because they improve compression or bilingual consistency without
changing science.

### Must-fix items

1. **Ambiguous `them` in the thesis argument.** Applied: the hierarchy now
   attributes the resulting resource measures, not an unclear antecedent.
2. **Two algorithm frameworks lacked parallel roles.** Applied: numbered
   clauses separately assign tag derivation and operation-stack construction.
3. **Four-dataset and nine-dataset results shared one grammatical scope.**
   Applied: localization/group reduction and held-out tag accuracy are now two
   sentences.
4. **The Evaluation contribution omitted RQ3 and RQ4.** Applied: the
   contribution now covers attribution, localization, tag accuracy, and end-
   to-end cost.
5. **Background named two challenges while Introduction/Design named three
   capabilities.** Applied: Background now says that, beyond cross-layer
   projection, two additional core challenges remain.
6. **`exclude it` had an ambiguous antecedent.** Applied: both debugging and
   aggregate views now name `session` explicitly.
7. **`operations through mapping rules` was grammatically and causally
   unclear.** Applied: mapping rules convert 15 public families into 47,590
   operations.
8. **The automatic-induction AP definition contradicted visible-only ranking.**
   Applied: AP is defined for the visible-field group ranking.
9. **The baseline paragraph read as seven disconnected notes.** Applied: it is
   now a connected comparison that separates visible ranking, post-ranking
   hidden scoring, and the two oracle mechanisms.
10. **157.5 looked like one run's group count.** Applied: it is explicitly the
    median group count.
11. **`three methods that do not use hidden annotations` was under-specified
    because the table has five such rows.** Applied: the three focal methods
    are named as flat, per-session, and operation-stack profiling.
12. **Native hierarchy was inaccurately summarized as a dataset-boundary
    hierarchy.** Applied: the two fixed alternatives use session-specific or
    dataset-native boundaries.
13. **The RQ3 setup compressed rule inference and two metrics into one long
    sentence.** Applied: protocol, V-measure, and boundary F1 are separated.
14. **`responsibility paths` was an undefined Related Work synonym.** Applied:
    Related Work now uses the established `query-time operation stacks`.
15. **Conclusion said `Across the four RQs` but summarized only three.**
    Applied: it now also reports median 1.6-second construction across 76
    configurations.

### Should-fix items

The 16 Should-fix items produced the following disposition:

- The costly-manual-analysis sentence already had a clear subject and was
  retained.
- The existing-tool sentence now uses `span trees that support debugging`.
- The prompt-boundary sentence is split at the runtime-mechanism contrast.
- The Design bridge removes a redundant parenthetical list.
- The operation definition removes double apposition.
- The duplicate call-stack analogy is removed.
- The four example views are grammatically parallel.
- The local-LLM sentence removes nested explanatory parentheses.
- The flat `GROUP BY` limitation names the three questions directly.
- The weight-function setup removes `e.g.` parenthetical prose.
- Automatic induction now refers directly to the six RQ2 tasks.
- Table-caption metric definitions are complete sentences; `Hidden=1` is
  explicit.
- The benchmark scope is split into counts and task identities.
- Three repetitive RQ3 setup sentences are compressed into one fixed-RQ
  question.
- The RQ3 figure text now says `where applicable`.
- `7/9` prose is normalized to `seven of nine`.

### Consider items

- The two-sentence flamegraph preview is merged.
- Figure shorthand `12k` and `25k` is normalized to `12,000` and `25,000`.
- Chinese comments that still said tag `transfer` now say tag `accuracy`.

## Dataset-accounting source audit

The reviewer correctly noticed that 47,590, 34,539, and 13,265 must not be
naively added. Existing artifacts resolve the apparent discrepancy:

- R292's `combined-15datasets-quality.json` reports 47,590 operation records
  across the 15-family mapped universe.
- R285's leave-dataset-out artifact reports a nine-dataset, 13,265-operation
  subset of that public universe.
- R320 reports `task_operations=34539` over six scored tasks. Some source
  datasets contribute to more than one task, including two AgentRewardBench
  targets and two AgentNet targets, so this is a task-operation count rather
  than a disjoint addition to the R285 subset.

The paper now calls the RQ2 total `34,539 task-operation instances` in the
Abstract, Introduction, and RQ2 setup. No count was guessed or changed.

## Experiment obligations preserved for the next EXPERIMENT gate

1. **RQ1 headline evidence.** Establish the exact numerator and denominator
   behind `separates over 90%`, including the per-session comparison, with a
   full source-linked computation.
2. **RQ1 tag validation.** Validate the same `prompt_tag` backend and real-
   trajectory scope used by RQ1; mapping-derived RQ3 phases alone do not close
   this obligation.
3. **RQ2 target blindness and strongest baseline.** Use held-out configuration
   selection and compare directly with the stronger native-hierarchy rows.
4. **RQ2 matched-decision evidence.** Compare methods at matched recall,
   matched inspection budget, or a real analyst decision rather than treating
   Work@5 against flat as matched utility.
5. **RQ2 problem definition.** Add an unmistakable real failure, safety, or
   waste decision target so the fixed RQ does not depend partly on group-start
   boundary localization.
6. **RQ3 backend coverage.** Evaluate tag accuracy, stability, and unseen-
   family behavior for the tag mechanisms claimed by the system, including the
   RQ1 path.
7. **RQ4 complete cost.** Run complete cold- and warm-path measurements that
   include parse, tag derivation, stack construction, and folding.

The review's eighth concern, dataset accounting, was resolved from existing
artifacts and therefore is not an experiment obligation. All remaining items
ask for stronger evidence and do not authorize weaker claims.

## Preservation and drift audit

- Exact thesis: unchanged and present in Abstract, Introduction, and
  Conclusion.
- RQs: exactly four, unchanged in order and meaning.
- Positive hypotheses: none narrowed, withdrawn, or converted into defensive
  prose.
- Numerical values: unchanged; `operations` became `task-operation instances`
  only where R320 already defines that counting unit.
- Citations: unchanged at 44 commands and 71 cited-key occurrences.
- Core abstractions: operations and operation stacks remain unchanged.
- Internal negative or inconclusive experiments: not added to the paper.
- Read-only submodule, idea story, skills, and KVM files: unmodified.

## Build and rendered evidence

The complete `pdflatex -> bibtex -> pdflatex -> pdflatex` build succeeds.

- `docs/paper/main.tex` SHA-256:
  `92b8ebe9d0b13340dc5fcb0acabc71355bd39424b4e6f433c3ae89b5417a696e`.
- `docs/paper/main.pdf` SHA-256:
  `093114d5ea5c4dfa5c7f7662006df734470a5f224186ac5e7d1c55aa03979f0d`.
- `docs/paper/references.bib` remains
  `f044ea5eb5a5e3dba7aee92e2bbb8e634cad484b60428ae379e10cf48eca70c3`.
- PDF: nine US-letter pages.
- Main content and complete Conclusion: end on page 7.
- References: begin at the bottom of page 7; pages 8--9 contain bibliography
  material only.
- Undefined citations/references: none.
- Overfull boxes: none.
- Remaining warnings: three cosmetic underfull horizontal boxes and one
  cosmetic underfull page box.
- `git diff --check`: clean.

## Scientific impact and next action

Round 9 makes the four-RQ logic parallel from Introduction through Conclusion,
clarifies the public-data counting units, and removes stale terminology and
ambiguous antecedents without changing the AgentProf story.

Next, Round 10 performs citation verification under
`check-paper-citations`. It may repair citation metadata or citation-to-claim
alignment, but it may not change the thesis, RQs, results, or evidence scope.
After Round 10, an independent WRITE-loop completion audit must decide whether
all 11 serial rounds and their reports are complete.
