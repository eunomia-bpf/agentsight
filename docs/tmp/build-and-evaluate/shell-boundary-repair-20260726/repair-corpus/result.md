# Original repair-corpus gate

Date: 2026-07-26

Status: **pass**

The final repaired release projection was run over the original 72-file,
120-question repair corpus. The required relation gate did not regress:

| Family | Correct | Wrong | Abstain | Total |
|---|---:|---:|---:|---:|
| A | 12 | 18 | 0 | 30 |
| B | 30 | 0 | 0 | 30 |
| C | 30 | 0 | 0 | 30 |
| D | 30 | 0 | 0 | 30 |
| B+C gate | **60** | **0** | **0** | **60** |

The overall diagnostic score is 102/120; this gate's registered stop
condition is B+C 60/60. All six project join-diagnostic maps were empty.

Release binary SHA-256:
`8b1351911d72dd33f776613cb5f9b48d50ecfb85be95db17b0205e85c1f7c4b3`.

Compact machine-readable evidence is in `summary.json` and
`question-results.csv`. The ignored `projection/` directory was reproduced
with:

```text
python3 scripts/run_repair_corpus.py \
  --binary build/cargo-target/release/agentvis
```
