# Round 5 — Paper Consistency

**Started:** 2026-07-16T22:05:09-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skill:** `check-terminology-infoflow`, paper-consistency scope with a
terminology/infoflow screen used only to expose factual ambiguity.

**Objective:** Establish one paper-wide factual model and repair local
contradictions across architecture, workflow, terminology, figures, tables,
claims, numbers, RQs, and evidence. Preserve the fixed thesis, four RQs,
algorithm, citations, populations, and all audited quantitative values.

## Review Method

A fresh independent subagent was instructed to read the skill and its complete
`paper-consistency.md` reference, then read the complete current LaTeX source,
all nine rendered pages in column order, and Round 0–4 reports. Its review is
read-only: it may not edit files, run experiments, or perform Git operations.
The main agent independently rendered pages 1, 3, 6, and 7 and spot-checked
quantitative anchors against `docs/evaluation.md` and the Step 0035 audited
result records while the reviewer worked.

## Factual Anchor Inventory Before Edits

| Anchor | Authoritative paper meaning |
|---|---|
| Thesis | `Agent observability needs profiling, not only debugging.` Exactly three occurrences. |
| RQs | Exactly four: attribution, problem correspondence/localization, tag accuracy, and construction cost. |
| Model | One semantic operation stack model with uniform weighted operations and query-time operation stacks. |
| Mechanisms | Intent attribution supplies stable semantic fields; stack construction supplies hierarchical attribution. |
| Source path | AgentSight captures/scopes/joins system effects; a source adapter emits linked operations; AgentProf projects and folds fields and weights. |
| Automatic constructor | Reference-session adjacent-action recurrence, NPMI, label-free two-means cutoff, optional one-scalar grouped-reference calibration; emitted group/motif values are ordinary fields. |
| RQ1 metrics | Ordinary operation-level B-cubed P/R/F1 is standard and primary; token-weighted B-cubed is secondary sensitivity evidence. CodeTraceBench supplies human stage partitions, not an official B-cubed diagnostic protocol. |
| RQ2 metrics | Non-interpolated AP per trajectory containing a target and MAP across such trajectories; reader precision/recall is separate supporting evidence. |
| RQ3 metrics | Exact adjacent-boundary P/R/F1; ordinary B-cubed partition F1; standard V-measure; macro-F1 and accuracy for literal declared-label classification. |
| RQ4 metrics | Three-run wall-clock medians, throughput, and maximum observed RSS from fixed-field operation JSONL through stack construction/folding/serialization. |
| Evidence boundary | Capture/adaptation/tag generation are outside RQ4. Literal phase-name accuracy remains a scientific outer-gate gap and cannot be replaced by boundary/partition metrics. |
| Format | Official `aaai2027` submission style, 9 US-letter pages; main content ends on page 7. |

## Initial Main-Agent Consistency Screen

The preliminary screen found three wording candidates to verify against the
independent report before editing:

1. several result sentences abbreviate `boundary F1` to `boundary`, which can
   make a standard metric look like an undefined custom value;
2. `per-operation V-measure` can be misread as a modified metric even though
   standard V-measure is computed over operations as the items;
3. `target-bearing trajectory` is used repeatedly but should be defined once
   as a trajectory containing at least one independent target annotation.

No change will be applied until the independent findings arrive. Round 5 does
not authorize a story, RQ, algorithm, or evidence change.

## Independent Review Verdict

**REVISE: 6 Must-fix, 6 Should-fix, and 3 Consider findings.** The
reviewer confirmed that the fixed thesis, RQs, semantic operation stack model,
algorithm, audited numbers, and standard-primary/secondary metric hierarchy
remain stable. It found no reason to change the story or invent an algorithm.

### Must-fix

1. **AAAI page limit:** Related Work continues and the complete Conclusion
   appears on physical page 8, although the repository requires pages after 7
   to contain references only. Earlier reports and the README incorrectly
   claimed compliance.
2. **RQ3 gap accounting:** the close names only literal phase-label accuracy,
   although the fixed cross-family hypothesis also lacks genuinely independent
   family-held-out confirmation. This is an outer EXPERIMENT item, not a
   license to narrow RQ3.
3. **Source ownership:** Design says operations perform D1 linkage, while
   Implementation correctly assigns capture/scoped joining to AgentSight,
   conversion to the adapter, and projection/folding to AgentProf.
4. **Formal view mismatch:** Figure 1 prose says only stack fields and weights
   change, but the formal view changes selection predicate \(\varphi\), stack
   function \(\sigma\), and weight \(w\).
5. **Internal vocabulary:** `R114-compatible`, `source-valid target`,
   `manifest-category weights`, `rank-hidden ... packets`, and
   `agent-session parsing` leak repository/workflow terms into reader prose.
6. **Metric names:** numerical `boundary` must be `boundary F1`;
   `per-operation V-measure` should be standard V-measure over operation
   assignments and needs its original metric citation.

### Should-fix

1. Define the label-free recurrence constructor at first body use.
2. Use `reference-calibrated recurrence` consistently for the optional scalar
   mode, reserving `supervised predictor` for Bernoulli Naive Bayes.
3. Define the RQ2 evaluation unit once, stabilize query/trajectory wording,
   and replace opaque interval wording with the actual paired bootstrap.
4. Use official Table 4 workload names.
5. Crop Figure 1's renderer titles/diagnostics and the time panel's unused
   vertical area; this also recovers page space without deleting evidence.
6. Split the roughly 100-word final abstract sentence while retaining all
   values and no more than nine total sentences.

### Consider

1. Replace the one `semantic stack` occurrence with the defined `operation
   stack` term.
2. Replace ambiguous `Agents can refine the rules` with `Users` or
   `Developers` if humans are intended.
3. Consider describing the time width as summed per-operation elapsed duration
   rather than wall-clock duration because timed operations may overlap.

All Must and Should findings are accepted. All three Consider findings are
also accepted because they remove ambiguity without changing technical
meaning. Edits follow subsection by subsection.

## Page-limit Repair Outline

The first post-review rebuild succeeds with nine physical pages and no
overfull, undefined-reference, citation, or compilation error, but page 8
still begins with the final two Related Work paragraphs and Conclusion before
References. The required repair is therefore prose economy, not a format
change. It will proceed in subsection-sized edits:

1. compact RQ3's repeated setup and fold descriptions while retaining every
   population, method, information boundary, standard metric, headline number,
   and unresolved literal-phase/family-held-out evidence item;
2. remove the RQ3 sentence that repeats RQ1's CodeTraceBench post-hoc status,
   which remains explicit in both RQ1 and Scope and Limitations;
3. compact RQ4's duplicated setup/result wording while retaining every cost
   boundary and value;
4. remove Scope's repeated RQ4 exclusion sentence and compact its RQ1/RQ3
   boundaries without changing scope; and
5. tighten Related Work comparisons without deleting a cited work or the
   paper's distinction from observability, systems profiling, or diagnosis.

No font, margin, spacing, title, abstract, introduction, contribution, RQ,
algorithm, baseline, evidence population, quantitative value, citation, or
scientific qualifier may change in this repair. Table font size remains
unchanged unless prose economy alone is insufficient.

## Applied Fixes

All six Must-fix, all six Should-fix, and all three Consider findings were
applied. No reviewer finding was rejected or deferred.

| Finding | Applied repair and preserved source |
|---|---|
| M1: page limit | Cropped only renderer chrome and unused plot whitespace in Figure 1, then compacted redundancy within RQ3, RQ4, Scope, and Related Work. The RQ3 CodeTraceBench post-hoc sentence was removed only because the same boundary remains explicit in RQ1 and Scope with the same citation. No table font, AAAI layout parameter, evidence, number, claim, or citation key was removed. |
| M2: RQ3 gap | The RQ3 answer and Scope now both name literal phase-label accuracy and independent family-held-out evaluation as remaining evidence. The fixed RQ and hypothesis were not narrowed. |
| M3: source ownership | Design, Implementation, Figure 2, and Evaluation now agree on `AgentSight scope/join -> source adapter -> linked operation -> AgentProf projection/folding`. |
| M4: formal view | Figure 1 and its body reference now both state that the selection predicate, stack fields, and weight function change over the same input operation corpus. |
| M5: internal vocabulary | Replaced workflow-internal names with reader-facing descriptions: declared process/tool scope, trajectories whose released sources yield the official operation sequence, predeclared task-category totals, group summaries blinded to view identity/rank labels, and native-history parsing. |
| M6: metrics | Every numerical boundary result is named `boundary F1`; ordinary B-cubed remains the primary partition metric; V-measure is described as standard V-measure over operation assignments and cites Rosenberg--Hirschberg. |
| S1--S3 | Defined label-free recurrence at first body use, stabilized `reference-calibrated recurrence`, defined one RQ2 query as one trajectory containing an annotated target, and named the 10,000 paired cluster-stratified bootstrap. |
| S4--S6 | Restored official RQ4 workload names; cropped Figure 1 without altering image data; split the abstract result conclusion while retaining nine sentences and every value. |
| C1--C3 | Replaced `semantic stack` with `operation stack`, assigned rule refinement to developers, and defined the time width as summed per-operation elapsed duration. |

The page-limit compaction preserves each deleted fact elsewhere in the same
paper: RQ3's setup is stated once rather than twice; RQ4's exclusions stay in
its protocol rather than repeating in Scope; the RQ1/CodeTraceBench
post-hoc boundary stays in RQ1 and Scope; and Related Work retains every cited
system and all three comparison classes. The alternative of shrinking table
text was rejected because prose economy already satisfies the limit and is
more readable.

## Preservation and Build Verification

- Official `aaai2027` submission build succeeds on US-letter paper with nine
  physical pages.
- Main content ends on physical page 7: Related Work, Conclusion, and the start
  of References all render there. Pages 8--9 contain references only.
- The final log has no LaTeX/package warning, undefined citation/reference,
  overfull box, or compilation error.
- The abstract contains 250 mechanically counted words and nine sentences.
- The exact thesis remains present three times; Evaluation still has exactly
  four RQ subsections with unchanged meanings: attribution, problem
  correspondence/localization, tag accuracy, and cost.
- The unique citation-key set is 53 versus 52 at the writing entry baseline:
  all entry keys remain, and the only addition is the original V-measure
  source required by M6.
- Every experimental population, baseline row, metric value, interval,
  resource total, cost value, and scope-bearing qualifier present before the
  page repair remains present afterward. The compaction changed no numerical
  value.
- `git diff --check` passes.
- The read-only `docs/agentpprof-paper` submodule remains clean at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.
- No Git publication action, experiment, scientific-contract edit, idea-story
  edit, or project-memory/tree change occurred in this writing round.

## Remaining Concerns and Next Node

Round 5 leaves no paper-consistency Must-fix. Literal phase-label accuracy and
independent family-held-out evidence remain outer EXPERIMENT-gate questions;
they are not writing defects and did not alter the fixed story. Proceed
serially to Round 6 sentence-structure review.

**Completed:** 2026-07-16T22:27:47-07:00
