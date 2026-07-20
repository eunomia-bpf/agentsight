# Round 10 — Citation Gate Check

**Started:** 2026-07-20T01:35:10-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `check-paper-citations`  
**Completed:** 2026-07-20T02:04:30-07:00  
**Status:** complete with documented checker exceptions

## Gate mode

All active bibliography entries have structured `VERIFIED`, `REAL`, `PDF`,
`ABSTRACT`, and `USED_FOR` annotations. Round 10 therefore performs the
mandatory mechanical check and the gate-mode missing-citation scan. It does not
repeat full PDF annotation work already represented in the bibliography.

## Mechanical pre-check

Command:

```text
python3 /home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/check-paper-citations/scripts/verify_bib.py docs/paper/references.bib
```

The script checked 65 active entries. It confirmed reachable URLs or matching
title/year/author metadata for the active set, then exited nonzero on nine
reported mismatches across seven entries. These are being independently audited
before any bibliography edit because the existing annotations already identify
official published records that some APIs expose only as older CoRR entries:

- official COLM `agentrewardbench` versus stale CoRR venue;
- official ICLR `taubench` and `scalecua` versus stale CoRR year/venue;
- official KDD `agentprocessbench` versus stale CoRR venue;
- full proceedings name versus `EMNLP-CoNLL` abbreviation for V-measure;
- official NeurIPS workshop `webgrapheval2025` versus CoRR;
- full JMLR journal name versus `J. Mach. Learn. Res.` abbreviation.

Correct official metadata will not be degraded merely to satisfy stale or
abbreviated API strings.

## Independent primary-source disposition

The independent reviewer confirmed the current official records:

- AgentRewardBench is a COLM 2025 paper on COLM's accepted-paper list.
- $\tau$-bench is an ICLR 2025 paper; the checker selected its older CoRR
  record.
- ScaleCUA is an ICLR 2026 paper on the official ICLR/OpenReview record.
- AgentProcessBench is a KDD 2026 paper whose released manuscript identifies
  the ACM DOI and conference; the project BibTeX still exposes an older arXiv
  form.
- The V-measure entry's full ACL proceedings title is the official form of the
  abbreviated `EMNLP-CoNLL` venue.
- WebGraphEval is explicitly a NeurIPS 2025 MTI-LLM workshop paper.
- `Journal of Machine Learning Research` is the official full form of the
  checker's abbreviation.

The mechanical nonzero exit is therefore retained as a tool limitation, not
hidden by inaccurate bibliography edits. No entry was downgraded or rewritten
to CoRR.

## Pass 3 and ghost-citation findings

The paper contains 65 citation commands and 58 unique cited keys after the
repairs below. Every key resolves. The reviewer found:

- zero hallucinated citations;
- zero missing benchmark or dataset provenance citations;
- zero missing original-technique citations requiring a new source;
- zero identity-leaking self-citation phrases; and
- one ghost-placement issue plus two local placement ambiguities.

## Applied repairs

1. The action-tag protocol now attributes the eight operational definitions to
   TraceView and the 2,737-annotation population to Bouzenia and Pradel, so both
   citations have an explicit role.
2. The existing pprof citation is repeated directly on the
   `tagroot`/`tagleaf` pseudo-frame capability.
3. The existing pprof/flame-graph citations are repeated directly on the CPU
   stack-attribution example.
4. Seven verified but uncited bibliography entries now carry `% STATUS:
   unused`; none was deleted.

No new source, scientific claim, benchmark, result, or related-work paragraph
was added.

## Exit validation

- All 82 BibTeX entries retain complete annotation blocks.
- All 58 cited keys resolve.
- `make -C docs/paper`: pass.
- PDF: 9 pages; Conclusion remains on page 7 and References begin on page 8.
- `main.log`: no undefined references/citations and no overfull boxes.
