# Repair-corpus-v2 gate

Date: 2026-07-26

Status: **pass**

The fixed parent set contains exactly 116 question IDs, with 29 questions in
each family. Answers and artifact identities were recomputed under
`native-root-conformance-v5-repair-20260726`; the parent P0--P4 paths and
question IDs were not reranked or reselected.

| Family | Correct | Wrong | Abstain | Total |
|---|---:|---:|---:|---:|
| A | 13 | 16 | 0 | 29 |
| B | 29 | 0 | 0 | 29 |
| C | 29 | 0 | 0 | 29 |
| D | 29 | 0 | 0 | 29 |
| Overall | **100** | **16** | **0** | **116** |

The registered strict gates are B+C 58/58 and D 29/29; both pass.

## Conformance ledgers

| Ledger | Expected | Actual | Matched | Missing | Extra |
|---|---:|---:|---:|---:|---:|
| Attempted edges | 2000 | 2000 | 2000 | 0 | 0 |
| Confirmed-effect edges | 1848 | 1848 | 1848 | 0 | 0 |
| Edge/call statuses | 1843 | 1843 | 1843 | 0 | 0 |
| Session order | 70 | 70 | 70 | 0 | 0 |

Release binary SHA-256:
`8b1351911d72dd33f776613cb5f9b48d50ecfb85be95db17b0205e85c1f7c4b3`.
Question-spec SHA-256:
`52236d197523299b94969efec1647d24bdc08714090596de60dd20ffaf51ab5f`.

## Validity boundary

This corpus was inspected to design and validate the repair. It is therefore
no longer held out and is strictly renamed **repair-corpus-v2**. The 100/116
score measures closure on known defects. Any new claim of generality requires
a third, independently selected corpus.

Compact machine-readable evidence is in `summary.json` and
`question-results.csv`. The ignored runtime, projection, and raw directories
were reproduced with:

```text
python3 scripts/run_heldout.py \
  --binary build/cargo-target/release/agentvis
```
