# Round 9 — Paragraph and Section Flow

**Started:** 2026-07-17T02:45:50-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skills:** `paper-writing-style` for paragraph mechanics and readable systems
prose; the current `iter-refine-writing` node controls scope and serial order.

**Objective:** Read the complete rendered paper as one argument and identify
paragraph-level discontinuities, overloaded paragraphs, weak topic sentences,
buried antecedents, abrupt section transitions, and sentences whose local
structure obscures the paper's scientific meaning. Preserve the exact thesis,
four RQ meanings, algorithm, evidence scope, protected hedges, all numbers,
all citations, and the completed terminology/metric repairs from Round 8.

## Entry State and Method

The entry is the completed Round 8 paper. It uses the official `aaai2027`
format, builds without warnings as nine US-letter pages, and keeps all
non-reference content within physical pages 1--7. The exact thesis appears
three times; 58 citation commands cover 53 unique keys. Standard metrics are
primary, while token-weighted B$^3$ and the matched reader analysis are
secondary.

A fresh read-only reviewer must invoke `paper-writing-style`, read
`docs/user-instruction.md`, this report, and the complete current
`docs/paper/main.tex` before judging anything. It must review the paper in
order, report findings as Must-fix, Should-fix, or Consider with exact anchors
and minimal repairs, and distinguish genuine flow defects from scientific
disagreement. It may not edit files, run experiments, use Git, change the
story, narrow a claim or RQ, change an algorithm, delete negative evidence,
alter a number or citation, or propose layout tricks.

No edit will be applied until the independent full-paper findings arrive.

## Independent Review

The reviewer explicitly used `paper-writing-style`, read the complete paper
and user instructions, and performed no edit, experiment, or Git operation. It
reported four Must-fix flow defects, thirteen Should-fix defects, and three
Consider improvements:

- RQ1 changed from the 20-task capture experiment to the 405-trajectory
  attribution experiment inside one paragraph.
- The RQ2 protocol packed corpus accounting, validation selection, controlled
  comparison, benchmark-specific scoring, target blindness, query definition,
  and AP/MAP into one paragraph.
- The RQ2 result paragraph conflated the standard MAP result with the secondary
  reader protocol/result, making the final RQ answer appear to follow from the
  smaller reader study.
- The RQ3 OSWorld protocol packed the population, supervised procedure,
  label-free procedure and development hedge, optional calibration, controls,
  and metrics into one paragraph.
- Lower-severity findings covered the abstract's result density, the evaluation
  contribution's grammatical subject, the Background--Design handoff, the
  formal view's missing backward link, adapter rationale order, boundary
  algorithm paragraph load, data-class paragraph load, semicolon-heavy
  baseline and definition sentences, an interrupted V-measure result, two
  captions, an unattached weight-conservation invariant, and repeated RQ4
  union results.

The reviewer explicitly excluded scientific disagreements from this writing
round. It required preservation of the phase-only comparison, supervised and
reference-calibrated comparators, CodeTraceBench post-hoc qualifier,
OSWorld development-evidence qualifier, standard-primary/secondary metric
hierarchy, and remaining evidence gaps.

## Applied Repairs

All four Must-fix, all thirteen Should-fix, and all three Consider findings
were resolved with paragraph boundaries and local sentence repairs:

1. RQ1 now closes the capture result before introducing CodeTraceBench. Its
   baseline definitions use two direct sentences instead of semicolon-linked
   clauses. The five-depth use case and final RQ1 answer each separate the
   validated evidence from the broader selectable-profile consequence.
2. RQ2 now has separate paragraphs for workload/snapshot selection,
   benchmark-specific scoring, and target-blind AP/MAP evaluation. The methods
   are explicitly identical except for grouping.
3. RQ2's primary MAP and pooled AP results are separated from a paragraph that
   begins `In a secondary matched comparison`. The reader protocol, reader
   result, and final RQ answer are distinct. The answer now states that the
   primary MAP comparison supports the conclusion across all three complete
   localization benchmarks.
4. RQ3 now separates the held-out supervised procedure, label-free and
   optional calibrated procedures, simple controls, and standard Boundary
   P/R/F1 plus ordinary B$^3$ metrics. The development-evidence qualification
   remains intact.
5. The abstract separates capture/folding, recurrence, localization, and
   OSWorld evidence into readable sentences without changing any result. The
   Introduction result block is split after the CodeTraceBench sensitivity
   result and after the OSWorld result.
6. The contribution now assigns semantic evidence to the profiles and the
   27,765-operation execution result to \sys. The Background ending directs
   the reader into Design, and the formal definition now says that it
   formalizes each selectable profile.
7. The AgentSight adapter rationale now precedes the adapter behavior. The
   boundary algorithm separates NPMI scoring, deterministic two-cutoff
   segmentation, and optional reference calibration without changing a step.
8. The three evaluation data classes are separate paragraphs. The RQ1 and RQ3
   table captions use canonical metric/task wording; all compared RQ3 methods
   are explicitly connected to the weight-conservation invariant.
9. The TF-IDF/K-Means result states full coverage in a separate sentence. The
   RQ4 answer no longer repeats its union result and preserves both absolute
   and relative time/RSS deltas.

During disposition, one remaining Round 8 terminology inconsistency was also
removed: system outputs and evidence gaps now consistently use `task/action
tags` and `phase tags`, while reader-hidden metadata uses `scoring fields`.
This is vocabulary normalization only.

No repair changes the thesis, RQ wording or order, story, algorithm,
population, comparator, result, citation, evidence scope, or claim strength.
Ordinary B$^3$, Boundary P/R/F1, AP/MAP, V-measure, macro-F1/accuracy, runtime,
and peak RSS remain standard primary metrics in their respective experiments.
Token-weighted B$^3$ and the reader analysis remain secondary.

## Verification

- A fresh `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
  build completes.
- The final log contains no overfull box, LaTeX/package warning, undefined
  reference, or undefined citation.
- `main.pdf` remains nine US-letter pages. All non-reference content ends on
  physical page 7; physical pages 8--9 contain references only.
- The exact thesis occurs three times, and the four RQ subsections retain their
  fixed order and meanings.
- The paper retains 58 citation commands and 53 unique citation keys. No
  quantitative result was edited.
- The canonical `docs/agentpprof-paper` submodule was not edited.
- No experiment or Git publication operation was performed in this round.

**Completed:** 2026-07-17T02:55:15-07:00

**Round 9 result:** PASS. The standard-metric evidence and its secondary
analyses now read in the intended hierarchy, so the serial writing workflow can
proceed to citation verification.
