# AgentNet complete source-preparation report

**Completed:** 2026-07-13T03:49:52-07:00  
**Stage:** `prepare` before REAL PREFLIGHT  
**Execution status:** `VALID`  
**Scientific status:** `NOT_EVALUATED`

## Command

```bash
python3 script/agentnet_cross_platform_eval.py prepare \
  --revision d76ee50a63fad81cfdbe576416757d7c2091ed50 \
  --out docs/visexp/out/agentnet-rq2/source
```

The first invocation had already downloaded and checksum-verified the official
files but stopped on the real repeated-task schema documented in
`source-schema-audit.md`. After the reviewed Revision 4 repair, the command
reused the exact verified files, replaced the invalid partial projection and
labels, and completed in full.

## Official source identity

| File | Bytes | SHA-256 |
|---|---:|---|
| `agentnet_win_mac_18k.jsonl` | 1,400,605,632 | `5c0d782cbf55af02835c3d6d9120072b87c06d24c5a8354c2544bd8d3568e72c` |
| `meta_data_merged.jsonl` | 18,840,344 | `9bb101e8373cd8cd1316f29d53c938b378f96aae1f09776a32bcc27454a0184d` |

Dataset revision:
`d76ee50a63fad81cfdbe576416757d7c2091ed50`.

## Complete population

| Platform | Unique task IDs | Released trajectories | Repeated task IDs | Operations | Positives | Negatives | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Windows | 12,364 | 12,427 | 63 | 239,710 | 38,565 | 201,145 | 0 |
| Darwin | 5,168 | 5,198 | 30 | 99,295 | 16,653 | 82,642 | 0 |
| **Total** | **17,532** | **17,625** | **93** | **339,005** | **55,218** | **283,787** | **0** |

**Arithmetic correction (2026-07-13T04:14:00-07:00):** the original total
row transposed `339,005` as `333,005` and consequently reported `277,787`
instead of `283,787` negatives. The platform rows, prepared files, and machine
status were always correct. The corrected totals are
`239,710 + 99,295 = 339,005` operations and
`201,145 + 82,642 = 283,787` negatives.

Positive means the predeclared combined truth table
`incorrect OR redundant`; negative means `correct AND necessary`. These counts
are source diagnostics from the only raw-reading stage. They were computed
while writing separate label files and never enter `projection.jsonl` or a
held-out predictor.

## Prepared boundary

- Visible projection: 339,005 rows, approximately 275 MiB.
- Windows label file: 239,710 rows, approximately 67 MiB.
- Darwin label file: 99,295 rows, approximately 28 MiB.
- Every raw row has a deterministic trajectory ID and unique operation IDs.
- All 17,532 unique raw task IDs join official metadata; no extra or missing ID
  exists.
- Full-source validation independently re-read the prepared files and confirmed
  exact task, trajectory, operation, and projection/label ID coverage.
- Only the four approved pure AgentNet helpers were used;
  `normalize_agentnet()` was not used.

The large source and derived data remain under the ignored
`docs/visexp/out/agentnet-rq2/` path. Only this detailed Markdown report and the
reviewed converter are tracked; no 1.4 GB source or 370 MB derived artifact is
added to Git.

## Interpretation boundary

This node proves source identity, completeness, schema handling, and physical
projection/label separation only. It provides no localization metric, no
scientific verdict, and no permission to alter the paper, RQs, hypothesis, or
story.

## Next transition

Run the fixed REAL PREFLIGHT on the lexically fixed first 256 original task IDs
per platform with 200 required valid task bootstraps from 1,000 fully presaved
attempt specifications. Preflight may judge only pipeline execution.
