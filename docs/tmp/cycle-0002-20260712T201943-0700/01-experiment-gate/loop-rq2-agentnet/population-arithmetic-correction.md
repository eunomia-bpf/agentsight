# AgentNet complete-population arithmetic correction

**Recorded:** 2026-07-13T04:14:00-07:00  
**Scope:** report-only correction before FULL authorization  
**Implementation change:** none  
**Experiment-definition change:** none

## Discovery

The independent post-repair REAL PREFLIGHT reviewer recomputed the complete
population from the prepared machine artifacts rather than trusting the total
printed in Markdown. The two platform counts are:

| Platform | Trajectories | Operations | Positive | Negative |
|---|---:|---:|---:|---:|
| Windows | 12,427 | 239,710 | 38,565 | 201,145 |
| Darwin | 5,198 | 99,295 | 16,653 | 82,642 |
| **Correct total** | **17,625** | **339,005** | **55,218** | **283,787** |

The previous Markdown total of 333,005 operations was an addition/transcription
error. The previous 277,787 negative total propagated the same 6,000-operation
error. The correct arithmetic is:

```text
239,710 + 99,295 = 339,005 operations
201,145 + 82,642 = 283,787 negative operations
38,565 + 16,653 = 55,218 positive operations
283,787 + 55,218 = 339,005 labeled operations
```

## Authoritative evidence

The unchanged ignored `prepare-status.json` reports 239,710 Windows and 99,295
Darwin operations. Its label-state counts report the same positive and negative
platform totals. Independent line counts are 339,005 for `projection.jsonl`,
239,710 for `labels/windows.jsonl`, and 99,295 for `labels/darwin.jsonl`.

`validate_full_source()` already checks the two per-platform operation counts,
task counts, trajectory counts, and projection/label operation-ID identity.
Therefore the executable FULL path always targeted the correct complete
population; no source row was omitted and no machine artifact was rewritten.

## Corrections applied

The arithmetic was corrected in:

- `source-preparation-report.md` (population table and projection row count);
- `preflight-report.md` (requested FULL population);
- `preflight-review.md` (authorized FULL population); and
- `preflight-rerun-after-key-repair.md` (requested repaired FULL population).

Each affected historical report now includes an explicit read-back correction
note rather than silently presenting the typo as though it never occurred.
Git history retains the original text.

## Scientific boundary

This correction does not change the tested hypothesis, RQ2, model, features,
views, baseline, metric, confidence interval, bootstrap unit, seed, verdict
rule, paper, or story. It only makes the human-readable full-population total
consistent with the data and executable validation already in use.

The corrected authorization scope to be reviewed is exactly 17,625 released
trajectories / 339,005 operations, 10,000 valid task-cluster draws per fold,
50,000 maximum attempts per fold, and seed 4204.
