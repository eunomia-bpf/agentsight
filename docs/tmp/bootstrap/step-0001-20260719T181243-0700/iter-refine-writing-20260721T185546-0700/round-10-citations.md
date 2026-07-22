# Round 10 — Citation Verification

## Independent review

Reviewer: `writing_round10_citations` (read-only), using the citation-verification
gate and the original PDFs.

The mechanical verifier passed the original bibliography.  The manual audit
found no hallucinated source or material claim--citation mismatch, but identified
four named benchmarks without citations and one AgentRx terminology mismatch.

## Applied changes

- downloaded and read the abstract/introduction of the original Harness-Bench,
  SWE-ContextBench, SWE-INTERACT, and CORE-Bench papers;
- added fully annotated BibTeX entries and cited each benchmark at its first
  formal body use;
- used the current twelve-author SWE-ContextBench v3 metadata rather than stale
  early-result metadata;
- cited the published TMLR CORE-Bench record and retained the downloaded revised
  paper for claim checking;
- changed AgentRx's “synthesized invariants” to the paper's “synthesized
  constraints and stepwise validation logs” and synchronized its annotation;
- retained the unused behavioral-drivers entry and marked it `STATUS: unused`;
  and
- standardized the formal benchmark spellings Harness-Bench,
  SWE-ContextBench, and SWE-INTERACT.

## Gate result

- bibliography entries verified: 16 total (15 active, 1 explicitly unused);
- hallucinated citations: 0;
- inaccurate claim wording fixed: 1;
- missing citations added: 4;
- entries left unverified: 0;
- mechanical metadata errors/warnings after fixes: 0/0;
- LaTeX compile: PASS;
- document length: 6 content pages plus one reference-only page;
- undefined citations/references: none reported.
