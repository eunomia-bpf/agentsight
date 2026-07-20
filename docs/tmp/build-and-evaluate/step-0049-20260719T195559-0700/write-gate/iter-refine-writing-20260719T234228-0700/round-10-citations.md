# Round 10 — Citation Gate Check

**Started:** 2026-07-20T01:35:10-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `check-paper-citations`  
**Status:** in progress

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
