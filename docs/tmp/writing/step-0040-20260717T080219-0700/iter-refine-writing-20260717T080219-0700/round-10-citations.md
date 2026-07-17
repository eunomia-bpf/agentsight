# Round 10 — Citation Verification

## Node identity

- **Started:** 2026-07-17T14:36:00-07:00
- **Completed:** 2026-07-17T14:49:00-07:00
- **Parent:** Step 0040 WRITE gate
- **Procedure:** the root read the complete `check-paper-citations` skill and
  ran its mandatory mechanical verifier. Because every bibliography entry had
  a complete verified annotation, an independent read-only subagent then ran
  the gate-mode Pass 3 missing-citation audit over the complete paper and
  bibliography. No agent performed a Git operation.

## Mechanical pre-check

`verify_bib.py references.bib` exited zero. The bibliography contains 76
entries, and all 76 have complete `VERIFIED`, `REAL: yes`, `PDF`, `ABSTRACT`,
and `USED_FOR` fields. No entry is `REAL: no` or `REAL: unverified`. The paper
uses 45 distinct citation keys; all 45 resolve to bibliography entries. The 31
unused entries retain their existing status because the skill explicitly
forbids deleting unused, real references.

Under the skill's `iter-refine-writing` rule, this evidence authorizes the
Pass 3-only gate rather than downloading and re-verifying all 76 sources.

## Independent Pass 3 verdict

The reviewer returned **REVISE** with two high-confidence citation-placement
findings and no ghost citation:

1. V-measure's defining Rosenberg--Hirschberg citation appeared at the concrete
   dataset result but not at the earlier RQ3 construct-to-metric definition.
   The root added the same existing citation at first metric definition.
2. The evaluation data overview put the three RQ2 benchmark citations after a
   sentence that also stated the RQ4 union, leaving the union's four public
   workloads without a local source. The root split the statements: RQ2 cites
   AgentProcessBench, HINTBench, and TraceElephant; RQ4 cites AgentRewardBench,
   SATraj-OS/Safactory, OSWorld-Human, and AgentNet.

No bibliography entry, source claim, paper result, or story changed.

## Standard-metric source verdict

- Ordinary B$^3$ uses the Bagga--Baldwin defining source.
- Non-interpolated AP and its across-query mean use Robertson's average-
  precision source, with MAP defined explicitly in the protocol sentence.
- Macro-F1 and accuracy use the RCV1 standard text-classification benchmark
  precedent.
- V-measure uses Rosenberg--Hirschberg's definition at first RQ3 use.
- Exact boundary precision, recall, and F1 use the Ruokolainen et al. exact-
  boundary evaluation precedent.

The independent reviewer found no high-confidence ghost citation, unsupported
metric role, retraction issue, or missing named-system/benchmark citation.

## Required output summary

- bibliography entries mechanically verified: **76**;
- distinct paper citation keys resolved: **45**;
- hallucinated citations: **0**;
- inaccurate source claims fixed: **0**;
- missing citation placements fixed: **2**;
- new bibliography entries added: **0**;
- entries that could not be verified: **0**.

## Build and status

The final build remains nine US-Letter pages, with all body content on pages
1--7 and references beginning on page 8. It has no undefined citation/reference,
multiply-defined label, or overfull warning. Round 10 is complete. Round 11 is
a fresh meaning-preservation diff against the read-only entry baseline.
