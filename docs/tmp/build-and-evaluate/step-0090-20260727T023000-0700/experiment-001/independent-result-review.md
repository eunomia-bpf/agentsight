# Independent result review

Verdict: **VALID**

Scientific disposition: supported as a **supporting, provenance-separated
multi-measure demonstration**; inconclusive for exact inner-LLM-to-kernel
lineage and network-failure correlation.

## Independent recomputation

- Git has 489 rows and 489 unique evidence IDs. All factual fields and order
  exactly match the fixed count input.
- The hierarchy oracle compares 489 expanded paths with 489 frozen workspace
  tool paths and finds zero missing, extra, or mismatched paths. Ordered
  mapping SHA-256:
  `ff290b2aed20ce2057241c151ed7c47a10d078c754dcd7026c8d509990d007f3`.
- Defined time is 3,982 seconds: session totals 715 + 2,049 + 1,218.
  Raw observed gaps are 3,983.640 seconds; floored mass is 3,805; 174
  minimum-one-second additions plus three terminal seconds yield 3,982.
- All 274 nonblank Terminus commands exactly match all 274 retained cast
  inputs after excluding `clear`; one blank command is explicitly imputed.
- `diagnose authentication` retains the fixed 105 rows and carries 1,492
  seconds, or 37.4686%.
- FILE-READ, FILE-WRITE, and NETWORK inputs/profile checks preserve 737, 31,
  and 61 target references. Both claimed created targets are successful
  retained `apply_patch` `Add File` headers with exact filenames.
- All 55 Step-0086 network-classified tools are `ok`; Git has no eBPF
  recording; R114 has zero network rows. Network-failure correlation is
  unavailable.
- R114 preserves all 1,520 original rows and values: 745 `process.exec`, 740
  `process.exit`, and 35 `file.write`. Its failure task retains 39 rows,
  reports one false negative, and has no retained `python3` effect.
- All five profile pairs have matching SHA-256 values, zero conservation
  delta, and successful stock-pprof reads.

## Required corrections and disposition

The reviewer required two corrections:

1. The amendment table must call the single semantic-operation-to-kernel chain
   **partially materialized/inconclusive**, because Step-0086 supplies source
   targets while R114 supplies a separate, coarser eBPF chain.
2. The adapter's general network-failure availability predicate must require a
   failed network row, not merely any R114 network row.

Both are fixed. They do not change any profile, count, digest, or scientific
verdict.

No additional experiment is requested. The result is admitted as supporting
RQ1 evidence under the claim boundaries in `results.md`.
