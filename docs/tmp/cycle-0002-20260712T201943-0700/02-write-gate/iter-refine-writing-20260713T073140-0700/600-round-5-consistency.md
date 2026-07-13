# Round 5 — Terminology, Information Flow, and Paper Consistency

- Completed: `2026-07-13T09:27:00-07:00`
- Governing skills: `iter-refine-writing`, `check-terminology-infoflow`
- Mode: independent combined paper-consistency/terminology review followed by
  root-agent minimal fixes
- Edited source: `docs/paper/main.tex`
- Verdict: `PASS` for writing consistency; scientific evidence obligations
  remain open for REVIEW/EXPERIMENT
- Story verdict: `NO DRIFT`

## Independent review

An independent reviewer read the complete paper, bibliography, project memory,
idea history, user instructions, current WRITE reports, relevant source records,
and current implementation. It explicitly used the combined
paper-consistency and terminology/infoflow contracts and made no edits or Git
operations.

The reviewer confirmed these authoritative anchors:

- the exact thesis remains “Agent observability needs profiling, not only
  debugging”;
- exactly four fixed RQs remain, in the order attribution, real-problem
  localization, tag accuracy, and profiling cost;
- operations and operation stacks remain the only two core abstractions;
- intent attribution and stack construction remain mechanisms rather than new
  contributions; and
- the large quality, safety, failure, wasted-work, resource, and cost motivation
  remains present.

## Factual and paper--artifact fixes applied

### 1. Correct 13,265-operation provenance

The field-selection comparison incorrectly attributed the corpus to four
families. R279/R286 and the previous cycle's own consistency audit establish
that these 13,265 operations come from nine public datasets. The sentence and
its Chinese source comment now say nine public datasets. The operation count
and 9/57/226/455/3,757 group counts are unchanged.

### 2. Match automatic stack induction to the implementation

The paper described an obsolete TF-IDF cosine mechanism. Direct inspection of
`agentpprof/src/profile.rs` confirmed the implemented recursive procedure:

- it detects adjacent changes in non-oracle visible fields;
- it computes token-set distance between neighboring operations;
- it scores structural gain, segment-label quality, balance, coverage, query
  bonus, semantic shift, and field changes; and
- it recursively splits subject to minimum-child, majority, score, and depth
  constraints.

The Design text now describes visible-field changes, token-set distance,
within-segment consistency, recursion, balance, and depth. It does not expose
internal coefficients or promote the algorithm into another abstraction. The
Introduction's one-off “work-phase boundaries” wording was also replaced with
“boundaries inferred from visible operation fields.”

### 3. Separate the three intent-attribution measurements

The old RQ4 sentence merged three different experiments. It now keeps their
scopes separate:

- the full-history run contains 118,021 requests, 70% cache hits, and 35,136
  llama.cpp calls;
- a separate 300-fragment run measures 31 ms p95 per tag with a local 3B model;
  and
- three local model configurations produce 2,700/2,700 syntactically valid
  tags under grammar-constrained decoding.

No number changed. The fix removes the false implication that 35,136 is simply
the arithmetic remainder of the request count and that all measurements came
from one run.

### 4. Align figure, implementation, and terminology details

- The flamegraph reference now names all three visible views: tokens, time, and
  files.
- The 9.8K-LOC statement now scopes the count to the Rust CLI and parser
  codebase rather than the CLI alone.
- Chinese comments now use DR1--DR3 consistently with the English Design
  requirements.
- The RQ3 caption retains every metric, threshold, dataset count, and legend
  distinction in a more compact formulation.

### 5. Correct the Related Work boundary

The old text categorically reduced current observability systems to
single-execution debugging and denied resource aggregation. The corrected text
acknowledges per-execution tracing, evaluation, metadata/cost aggregation,
input clustering, and structured-signal extraction. It states AgentProf's
specific distinction as cross-layer operations plus query-time responsibility
paths for profiling across trajectories. All citations remain in place for the
dedicated citation round.

## Page-limit repair

After the Round 4 opening expansion, visual inspection revealed that the
Conclusion had spilled onto page 8 even though an earlier report incorrectly
called pages 8--9 reference-only. This round repaired the actual rendered
paper, not just the source order.

The repair:

- tightened repeated RQ4 scope and measurement prose without deleting a
  measurement;
- combined Related Work comparisons without removing a citation or comparison;
- compacted the RQ3 caption without removing content; and
- removed from the Conclusion a repeated per-session counterpoint and a generic
  future-work sentence. The per-session result remains fully reported in RQ2;
  it is simply no longer repeated as the paper's closing headline.

The final rendered page 7 contains all of RQ3, RQ4, Related Work, and the
complete Conclusion. Page 8 begins with `References`, and pages 8--9 contain
references only.

## Evidence obligations carried to REVIEW/EXPERIMENT

The following are not writing problems and were not hidden by weaker prose:

1. **RQ1 independent attribution reference.** The mixed-weight scorer may be
   circular with the tag axis, and the visible 90.4/84.4/36.7 values do not
   derive the “over 90%” headline.
2. **RQ2 target-blind ranking.** Group construction hides labels, but current
   ranking uses hidden-positive density. A visible ranker, fixed objective, and
   complete baseline rerun are required.
3. **RQ2 statistical protocol.** The pairwise contrasts, resampling unit,
   permutation null, and multiplicity handling must be made explicit in a
   complete experiment.
4. **RQ3 mechanism coverage.** The current experiment tests mapping-derived
   phase against native action; it does not yet validate prompt tags, the local
   LLM tagger, arbitrary intent tags, or an RQ2 ranker.
5. **RQ4 complete cost.** The 76-configuration timing uses prepared operation
   files. Cold raw-input construction, warm repeated queries, memory/output
   size, scale, tagger batching, and separately scoped capture cost remain to be
   measured.
6. **Regex-authoring workflow.** The “below 5% in 5--10 rounds” statement needs
   a complete authoring study.
7. **Dataset provenance.** One source-derived table should map the 15-family
   universe, 9-dataset/13,265-operation subset, and 4-dataset/6-task/34,539-
   operation subset to their RQs.
8. **Decision value of multiple weights.** Different rankings are established;
   independently correct bottlenecks or downstream decisions are not yet.

These obligations call for stronger experiments. They do not authorize
narrowing the thesis, changing an RQ, replacing a hypothesis, or retracting the
original contribution boundary.

## Terminology audit

- Core concept budget: pass; two paper-defined abstractions.
- Operation/operation stack terminology: stable.
- System name: all live prose uses `\sys`; the literal name appears only in the
  macro and title.
- Attribution: explicitly defined as conserved additive accounting, not causal
  diagnosis.
- Remaining overloaded vocabulary: prompt tag, mapping-derived phase, native
  action annotation, and hidden problem label need continued distinction in the
  language rounds.
- Remaining measure ambiguity: “system-effect weight” versus “cost” requires
  evidence clarification rather than a global writing substitution.

## Build and visual verification

The full `pdflatex -> bibtex -> pdflatex -> pdflatex` build succeeds.

- PDF: 9 US-letter pages.
- Main content: ends on page 7.
- Pages 8--9: references only.
- Unresolved citations/references: none.
- Overfull boxes: none.
- Fonts: embedded Type 1 only.
- Visual page-7 audit: RQ3 figure/caption, RQ4, Related Work, and Conclusion are
  legible, correctly ordered, and remain inside the page.
- `main.tex` SHA-256:
  `adf7959b09391d14c645ccc240a83a531355cd07259e64ad095502fbb5d084a3`.
- `main.pdf` SHA-256:
  `63fd3c639e135a813c523f4af716c7f10be874340fc54d8d44900eb33af19349`.
- `references.bib` SHA-256 remains
  `f044ea5eb5a5e3dba7aee2bbb8e634cad484b60428ae379e10cf48eca70c3`.

## Story-drift and content-loss audit

`PASS`.

- Exact thesis remains in Abstract, Introduction, and Conclusion.
- Four RQs remain explicit and unchanged in meaning.
- Operations and operation stacks remain the only core abstractions.
- No contribution, positive result, dataset count, metric, figure, table, or
  citation was removed.
- No failed AgentProcessBench result entered the paper.
- No scientific claim was narrowed to make an evidence objection disappear.
- The opening and body now describe the same implemented system and data
  subsets more accurately.
