# Round 0 — Macro Structure

**Started:** 2026-07-16T20:53:02-07:00

**Completed:** 2026-07-16T21:04:00-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Objective:** Check the complete AAAI-27 paper at Level 1 and repair macro
writing structure without changing the fixed thesis, four RQs, scientific
meaning, or quantitative evidence.

## Entry Snapshot

- Repository HEAD: `26ed64d3c48a606516977ab696894fba8c0744bf`.
- Dirty-tree paper baseline: `5fcba1d5a474e7036e2c8777c1f05ff243e79760`,
  produced by read-only `git stash create`; no ref or working-tree file changed.
- Entry paper: `docs/paper/main.tex` and its 9-page letter-size
  `docs/paper/main.pdf`.
- Entry evidence: Step 0035 full run and independent result review.
- Fixed RQs: exactly four, at `docs/paper/main.tex` Evaluation opening.
- Entry citation set: 52 unique keys.

The reviewer read the complete paper and PDF, invoked
`check-paper-structure-flow`, and applied its full-paper Level-1 reference with
the AAAI-27 constraint of seven main-content pages plus two reference-only
pages. It performed no Git operation and edited no file.

## Raw Reviewer Findings

### Must-fix

1. **RQ3 is not yet scientifically complete.** Its fixed wording and positive
   hypothesis cover task, phase, action, and group identity, while the paper
   explicitly says literal phase labels remain untested. A compact standard
   macro-F1/accuracy phase-label experiment is still needed. This cannot be
   repaired by writing, invented evidence, or a narrower RQ.
2. **Conclusion was only the thesis sentence.** It did not restate the model,
   system, or paper-level empirical answer.
3. **Related Work was only two compressed sentences.** It could not support
   novelty positioning against observability aggregation, classical profiling,
   and agent diagnosis.

### Should-fix

1. Evaluation floats did not always remain after the RQ protocol that produced
   them.
2. RQ3 combines boundary, task, action, and missing phase evidence in one dense
   block and repeats CodeTraceBench default-selection evidence already used by
   RQ1.
3. Evaluation dominated the page budget, leaving almost no Related Work or
   Conclusion.
4. The Evaluation data setup did not visibly enumerate its promised three data
   classes.

### Consider

- Do not add a mechanical Discussion section under the seven-page limit;
  preserve `Scope and Limitations` and put the main implication in Conclusion.
- All other Level-1 structure passes: correct section order, coherent merged
  Background/Motivation, explicit D1--D3 requirements, Design-to-requirement
  mapping, architecture overview, Design/Implementation separation, exactly
  four RQs, and direct RQ1/RQ2/RQ4 closing answers.

## Applied Fixes

### Related Work

Expanded the section into three compact topic paragraphs:

1. agent observability and cross-trace aggregation;
2. systems profiling and trace querying; and
3. agent diagnosis and localization.

Each paragraph states what prior systems do and the specific complementary role
of AgentProf. The final version is deliberately compact for AAAI rather than a
systems-paper-length survey. All entry citation keys remain present.

### Conclusion

Expanded the one-sentence section into a compact thesis--model--results
paragraph. It restates the fixed thesis, semantic operation stack and AgentProf,
and the existing attribution, problem prioritization, semantic-structure, and
cost evidence. It introduces no new number or claim.

### Page Balance

- Reduced the vertical size of the existing three-view flame-graph figure to
  90% width without changing its content.
- Condensed the public-dataset family enumeration while retaining all dataset
  categories and all 52 unique citation keys.
- Replaced the repeated RQ3 CodeTraceBench numeric paragraph with a cross-RQ
  statement that keeps its post-hoc implementation-selection role explicit.
- Repaired the stale RQ1 transition `Beyond tag separation` to `Beyond
  independent stage agreement` after removal of the circular prompt-tag figure.

### Float Placement

Changed the five tables to bottom-permitted single-column floats and converted
the wide reader table to a column-width table. Tables 1 and 2 now render after
their RQ headings and protocols. The reader table still lands at the bottom of
page 6 after some RQ3 text because forcing a barrier creates a tenth page and
violates the official format. This remaining presentation issue is retained for
later micro/layout rounds; it does not move a result into another RQ or change
reading-order references.

## Deferred Scientific Fix

The missing literal phase-label result is accepted as a real paper-level gap
and is not modified in this writing round. It is recorded for the outer
REVIEW/EXPERIMENT decision after the writing cycle. The root explicitly rejects
three invalid writing-only alternatives: deleting `phase` from RQ3, weakening
the hypothesis, or treating stage-boundary agreement as literal phase-name
accuracy.

## Verification

- `make` completes.
- Final PDF: 9 letter-size pages.
- Pages 1--7 contain main content; page 7 contains Related Work and Conclusion.
- Pages 8--9 contain references only.
- Final log has no undefined citation/reference, LaTeX warning, or overfull box.
- `git diff --check` passes.
- The 52-key citation set is identical to the entry snapshot; adjacent citation
  commands were consolidated without dropping a source.
- All four RQ strings and every quantitative value remain unchanged except for
  the already-authorized Step 0035 evidence integrated before this round.
- The canonical `docs/agentpprof-paper` submodule remains untouched.

## Next Node

Proceed serially to Round 1 micro structure. The phase-label experiment remains
an outer scientific concern, not authority for a writing-round story change.
