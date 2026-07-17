# Round 8 — Terminology and Jargon

**Started:** 2026-07-17T02:20:30-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skills:** `check-terminology-infoflow` in terminology-infoflow scope and
`paper-writing-style` in terminology/readability scope.

**Objective:** Audit the complete paper for invented terminology, one-use
compounds, undefined or overloaded terms, synonym drift, term-definition order,
caption/body mismatch, and terminology-driven information-flow breaks. Preserve
the exact thesis, all four RQ meanings, algorithms, evidence scope, protected
hedges, numbers, citations, and the completed Round 7 word-choice repairs.

## Entry State and Method

The entry is the compiled Round 7 paper. It uses the official `aaai2027` class,
builds as nine US-letter pages, contains four fixed RQ subsections, and places
all non-reference content on physical pages 1--7. Ordinary operation-level
B$^3$, MAP, V-measure, macro-F1, accuracy, precision/recall, runtime, and RSS
remain the standard core metrics; token-weighted B$^3$ and reader/work analyses
remain explicitly secondary.

The root agent read the complete `check-terminology-infoflow` instructions and
selected terminology-infoflow rather than combined paper-consistency scope:
Round 5 already completed the factual consistency pass, whereas this node is
specifically Round 8's terminology/jargon audit. A fresh read-only reviewer will
invoke both named skills, read `docs/user-instruction.md`, the complete current
paper, and this report, construct a concept inventory, run Jargon, Consistency,
Information Flow, and Cross-section checks in order, and report only
Must-fix/Should-fix/Consider findings. It may not edit files, run experiments,
perform Git operations, change scientific meaning, or revisit the story.

No paper edit will be applied until the independent findings arrive.

## Independent Review

A fresh read-only reviewer completed a full-paper pass using both named
skills. It found eight Must-fix clusters, eight Should-fix clusters, and three
Consider items. The findings were terminology and information-flow defects,
not requests to change the thesis, RQs, algorithm, or evidence:

- The capture experiment alternated among `source-linked`, `lineage`,
  `fidelity`, `scoped join`, and `source linkage` without one operational
  scope definition.
- The formal view used overloaded notation and a figure caption depended on a
  definition that appeared later.
- NPMI and the occurrence-weighted one-dimensional clustering procedure were
  either abbreviated or described with the nonstandard name `two-means`.
- RQ1 baseline rows did not state exactly how their groups were formed.
- RQ2 did not expand AP/MAP or fully define how benchmark evidence becomes an
  operation score.
- The matched reader comparison did not state the fields exposed, hidden
  information, fixed selection budget, or precision/recall denominators.
- RQ3 overloaded `tag`, `label`, `annotation`, `group`, and `boundary`.
- RQ4 did not state the two exact field hierarchies, time unit, or expansion of
  RSS.
- Lower-severity debt included late definitions of folding and label-free
  recurrence, one-use compounds, abbreviated benchmark/table labels,
  ambiguous `coverage`, `majority`, and `fixed model`, and remaining uses of
  `motif` where `stack-frame value` was sufficient.

The reviewer explicitly found the core concept inventory controlled: the
paper needs only AgentProf, operation, semantic operation stack, intent
attribution, stack construction, and the defined label-free recurrence
constructor. It did not recommend another mechanism name or metric.

## Applied Repairs

All eight Must-fix clusters, all eight Should-fix clusters, and all three
Consider edits were resolved. The repairs are:

1. `capture-and-join path` and `declared process/tool scope` are now the sole
   RQ1 terms. The Implementation section operationally defines the scope as the
   captured target agent process plus its launched tool command, excluding the
   concurrent control. The result is described directly as capture-and-join
   precision/recall and lossless folding, not as a new `source fidelity`
   concept.
2. Folding is defined at first use. The formal view is now
   $(\varphi,\sigma,w)$ with the predicate, ordered field projection, and
   additive weight defined for operation $o$. Figure captions remain
   self-contained.
3. The paper expands normalized pointwise mutual information (NPMI) and names
   the deterministic procedure as occurrence-weighted one-dimensional
   $k$-means with $k=2$. `Motif` was removed from the reader-facing model in
   favor of the actual run-length-compressed stack-frame value.
4. RQ1 now defines raw-action, phase-only, action-kind, per-session, and
   per-operation grouping. Table 1 names `Label-free recurrence`,
   `Raw-action grouping`, and marks token-weighted B$^3$ as secondary.
5. RQ2 now expands average precision (AP) and mean average precision (MAP).
   It states that AgentProcessBench averages benchmark judge votes, while
   HINTBench and TraceElephant compute a 95% Wilson lower bound for each
   root-to-frame prefix and assign each operation the maximum containing-prefix
   score. The paired bootstrap unit and benchmark-defined strata are named.
6. The matched reader comparison now states the two field projections, five
   position-balanced summaries, exactly-three selection budget, visible
   summary contents, hidden identifiers/ranks/scoring labels, and the standard
   operation-level precision and recall denominators. This remains supporting
   evidence; MAP remains the primary RQ2 metric.
7. RQ3 now defines a tag as an AgentProf-produced operation field, a reference
   annotation as benchmark-provided truth, and a predicted group/boundary as
   structural output derived from tags. It also names session-held-out
   cross-validation, the profile path, one fitted NPMI cutoff, full coverage,
   the predeclared Qwen configuration, and majority-class baselines.
8. RQ4 now states the semantic hierarchy
   `project, agent, task, phase, op, tool, status` and the raw hierarchy
   `project, agent, action, status`. The table labels seconds and expands
   resident set size (RSS) and MiB.
9. One-use phrases such as `operation-producing responses`, `mapped
   families`, `task-budget`, `action-duplication`, `session-detail`, and
   `recurrence-over-raw` were replaced by direct descriptions. The
   architecture caption is now explicitly the AgentProf pipeline.

No repair changes the fixed thesis, the meanings or order of the four RQs, the
constructor, a population, a baseline value, a result, or an evidence
qualifier. Ordinary operation-level B$^3$ remains the primary RQ1 partition
metric; exact boundary P/R/F1 and ordinary B$^3$ remain the primary RQ3
structure metrics; AP/MAP, V-measure, macro-F1/accuracy, runtime, and peak RSS
remain standard metrics. Token-weighted B$^3$ and the matched reader analysis
remain explicitly secondary. No ARI/AMI/NMI metric bundle was added.

## Verification

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` completes.
- The final log contains no overfull box, LaTeX/package warning, undefined
  reference, or undefined citation.
- `main.pdf` is nine US-letter pages. All paper content ends on physical page
  7; pages 8--9 contain references only.
- The exact thesis still occurs three times, and the four fixed RQ subsections
  remain attribution, problem correspondence/localization, tag accuracy, and
  profiling cost.
- The paper still contains 58 citation commands covering 53 unique keys. The
  Round 8 edits add or remove no citation command and change no quantitative
  result.
- The canonical `docs/agentpprof-paper` submodule was not accessed for editing
  and was not changed.
- No experiment or Git publication operation was performed in this writing
  round.

**Completed:** 2026-07-17T02:44:53-07:00

**Round 8 result:** PASS. Terminology and metric roles are explicit and
consistent enough to proceed to the paragraph-level Round 9 review.
