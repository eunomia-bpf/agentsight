# Round 10 — Citation Verification

**Started:** 2026-07-12T15:52:18-07:00  
**Completed:** 2026-07-12T16:23:44-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Reviewer:** fresh independent read-only subagent using the complete
`check-paper-citations` procedure  
**Paper:** `docs/paper/main.tex`  
**Bibliography:** `docs/paper/references.bib`

## Scope And Method

The reviewer read the project instructions, verbatim user prompts, complete
idea story, paper, bibliography, and local source corpus. It ran the mandatory
mechanical verifier, checked all citation uses in context, opened primary
papers, official proceedings, official documentation, dataset cards, and
source repositories, and audited published versions, venue accuracy,
retractions, self-citation leakage, ghost citations, and missing citations. It
made no edits, ran no Git operation, and returned source-specific findings to
the root.

At entry, the bibliography contained 59 entries, 46 cited keys, and 24 entries
without a complete five-field annotation block. The reviewer checked 69
citation-key uses and found no hallucinated or retracted reference and no
identity leak.

## Applied Source And Claim Repairs

The root fixed five claim groups without changing the thesis, RQs, experiments,
or quantitative results:

1. the corpus-review motivation now cites expert and LLM evaluation without
   claiming that AgentAtlas establishes review cost;
2. Datadog topic clustering and Laminar structured-signal extraction are no
   longer conflated;
3. tracing tools, span standards, evidence/provenance work, and telemetry fault
   detection receive source-specific descriptions;
4. AgentAtlas is correctly described as a diagnostic vocabulary and audit
   protocol rather than a per-trajectory localizer;
5. failure, anomaly, safety, redundancy, scope, and responsibility sources are
   distinguished by their actual outputs.

The 15-family evaluation provenance is now complete in the paper: the original
eleven named families plus AgentRewardBench, SATraj-OS, OSWorld-Human, and
AgentNet. The five-configuration boundary analysis cites its two
OSWorld-Human variants, AgentNet correctness/redundancy labels, and
AgentRewardBench looping labels directly.

Nine previously uncited provenance or method keys are now used:
`codexcli`, `llamacpp`, `salton1988term`, `macqueen1967methods`,
`sculley2010web`, `rosenberg2007vmeasure`, `safactory`, `osworldhuman`, and
`opencua`. Claude Code, Perfetto, and pprof citations were moved to their first
relevant uses. The optional standalone t-SNE citation was rejected because the
Hodoscope source already supports the reproduced protocol and the extra entry
did not earn its page cost.

## Bibliography Repairs

The root corrected materially wrong author or publication records for
OSWorld, GUIOdyssey, ToolBench, OSWorld-Human, and AgentFixer. In particular,
OSWorld-Human is now the Abhyankar--Qi--Zhang MLSys 2026 paper rather than an
organization-authored 2025 repository entry, and AgentFixer retains its arXiv
identity rather than claiming unavailable proceedings metadata.

Nine stale preprint records now identify formal publication where a primary
venue record exists: WebLINX, AgentTrek, tau-bench, AndroidControl,
AgentRewardBench, ScaleCUA, ARIA, OpenCUA, and OSWorld-Human. The SDBL record is
an AAAI proceedings article and no longer triggers the simultaneous
`volume`/`number` BibTeX warning.

Every one of the final 65 entries has an immediately preceding `VERIFIED`,
`REAL`, `PDF`, `ABSTRACT`, and `USED_FOR` block. Ten unused legacy entries are
retained and identified as unused rather than deleted. Twelve additional
primary PDFs were stored under `docs/reference/`; every local path named by a
`PDF` annotation exists and is a readable PDF.

## Mechanical And Manual Verification

The final mandatory verifier checks 65 entries, of which 55 are active, with
zero errors. Its only two warnings are heuristic false positives caused by the
real titles of API-Bank and GUIOdyssey containing `A Comprehensive`. The root
also manually resolved earlier API false matches: DBLP initially matched the
2008 t-SNE title to a different 2016 paper and lagged the COLM 2025 and MLSys
2026 publication records. The final bibliography uses the primary venue
records rather than stale indexing metadata.

Final counts:

- bibliography entries: 65;
- citation commands: 64;
- unique cited keys: 55;
- hallucinated citations: 0;
- retractions: 0;
- inaccurate claim groups repaired: 5;
- previously missing provenance/method keys cited: 9;
- formal-publication upgrades: 9;
- entries without complete annotations: 0.

## Build, Format, And Scientific Preservation

Source-specific wording and new citations initially pushed the Conclusion to
page 8 and the bibliography to a third reference page. The root compacted only
duplicated RQ3 and Related Work wording, used standard short venue names and
`and others` for large author consortia, and inserted a clean page break before
the bibliography. No experiment, result, limitation, closest-work distinction,
or contribution was removed.

- `make` completes with exit code 0 and no BibTeX warning, undefined citation,
  undefined reference, or fatal LaTeX error.
- The PDF is nine US-Letter pages.
- All technical content and the complete Conclusion end on page 7.
- Page 8 begins with `References`; references end on page 9.
- TeXCount reports 247 abstract text words, below the 250-word limit.
- The exact author-fixed thesis remains verbatim in Abstract, Introduction,
  and Conclusion.
- No semicolon appears in non-comment LaTeX prose.
- No paper-level RQ, experimental number, interval, negative result, open
  evidence requirement, or broad cost/regression/safety/failure/waste scope
  changed during citation repair.

No verified source requires thesis revision. The remaining gaps are empirical,
not bibliographic: positive real decision value, independent lineage,
unchanged transfer, and end-to-end cost still require experiments.

## Next Node

The complete eleven-round writing loop now enters an independent WRITE outer
audit. The audit must compare the current paper with the complete idea story,
verbatim user instructions, all round reports, build evidence, and actual diff;
it must reject any hidden thesis/RQ drift and route empirical gaps back to the
next EXPERIMENT gate rather than treating polished prose as scientific closure.
