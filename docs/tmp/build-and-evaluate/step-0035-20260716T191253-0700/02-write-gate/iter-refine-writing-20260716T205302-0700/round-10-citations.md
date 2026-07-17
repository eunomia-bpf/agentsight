# Round 10 — Citation Verification

**Started:** 2026-07-17T02:56:15-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skill:** `check-paper-citations`, invoked in its `iter-refine-writing` gate
mode.

**Objective:** Verify that the bibliography's existing source annotations are
complete, run the mandatory external-metadata precheck, and then audit the
complete paper for unsupported factual claims, missing first-use citations,
ghost citations, and claim--citation mismatch. Preserve the exact thesis, four
RQ meanings, algorithm, evidence scope, protected hedges, all quantitative
results, and the standard-primary/secondary metric hierarchy.

## Entry State and Routing

The entry is the completed Round 9 paper. It builds as nine US-letter pages
without warnings and keeps all non-reference content on physical pages 1--7.
The paper contains 58 citation commands covering 53 unique keys.

`references.bib` contains 69 entries. All 69 have complete `VERIFIED`, `REAL:
yes`, `PDF`, `ABSTRACT`, and `USED_FOR` annotation fields; none is marked
unverified. Under the skill's gate routing, this avoids redoing the completed
69-entry PDF/abstract annotation pass. The mandatory mechanical verifier must
still run on the complete `.bib`; after it passes, a fresh reviewer will
perform Pass 3 over the complete paper and spot-check claim alignment where
the prose changed during Rounds 6--9.

This round does not create a separate citation ledger: the annotation blocks
inside `references.bib` remain the citation-verification source of truth. This
report records only the writing-loop procedure and disposition.

## Independent Full-Paper Review

A fresh read-only reviewer explicitly used `check-paper-citations`, read the
complete 1,061-line paper, all 69 bibliography annotation blocks, the project
user instructions, and this report. It performed no edit, experiment, or Git
operation. Its initial verdict was `REVISE`: five must-fix groups and four
should-fix groups.

The review confirmed that all 69 entries are real and completely annotated.
It also confirmed three authoritative metadata exceptions that must not be
"fixed" to stale secondary records: AgentRewardBench is a COLM 2025 paper,
tau-bench is an ICLR 2025 paper, and AgentSight is a PACMI@SOSP 2025 workshop
paper. CodeTracer remains an arXiv `@misc` entry rather than a journal article.

## Disposition

All five must-fix groups were resolved with local citation/prose changes:

1. AgentSight is cited at its first citable use in the Introduction result.
2. CodeTraceBench is cited at first use; the later weighted-B-cubed sentence
   now cites only the weighted-metric precedent, so no source appears to own
   AgentProf's measured result.
3. Qwen3.6-27B is cited at its first use in the RQ2 reader experiment.
4. V-measure is cited at its definition/use, and Mind2Web and ScienceWorld are
   cited immediately with their dataset populations.
5. The unsupported generic magnitudes “over weeks or months” and “hundreds of
   such cycles” were removed. The scale argument remains, but the paper no
   longer presents unmeasured population-wide magnitudes.

All four should-fix groups were also resolved:

- AgentAtlas was removed from the evaluator-cost sentence; AgentRewardBench
  and the LLM-as-judge source now support that motivation.
- the Wilson citation is attached only to the Wilson lower bound, not to
  AgentProf's inheritance and tie rules;
- six active `USED_FOR` annotations were updated to match actual RQ1/RQ2/RQ3
  use; and
- seven retained but uncited candidate sources, including AgentAtlas, are now
  explicitly marked `STATUS: unused` rather than being force-cited.

The bibliography metadata changes made during this round are limited to
correcting CodeTracer's entry type and recording authoritative official-venue
metadata for AgentRewardBench and tau-bench. No citation was added merely to
increase density.

## Verification

The mandatory `verify_bib.py` run completed after the fixes with no emitted
diagnostic. The final source has 50 active citation commands covering 43 unique
keys; the remaining literal citation commands occur in Chinese comment lines
and do not compile. BibTeX and `latexmk` complete successfully with no missing
or undefined citation/reference and no overfull box.

The resulting PDF is nine US-letter pages. All non-reference content still
ends on physical page 7; pages 8--9 contain references only. The remaining
underfull-box diagnostics are ordinary line-breaking notices and do not change
content or exceed the page limit.

**Round 11 correction:** the Round 10 page-boundary check concatenated pages
7--9 before searching for section names and therefore did not prove the claim
above. A subsequent per-page read showed that part of Related Work and the
Conclusion actually occupied page 8 at this point. Round 11 corrected the
layout through meaning-preserving prose tightening and independently verified
that pages 8--9 are now reference-only. This correction does not change Round
10's citation verdict, but it supersedes its original format assertion.

**Completed:** 2026-07-17T03:14:34-07:00

**Verdict:** `PASS`. Every reviewer finding is resolved, the citation source
of truth is internally consistent, and the paper's thesis, four RQ meanings,
algorithm, quantitative evidence, qualifiers, and primary/secondary metric
hierarchy are unchanged.
