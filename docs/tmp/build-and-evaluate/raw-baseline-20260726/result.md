# P2 Result — Bounded Raw Reader Full Matrix

## Outcome

The registered matrix reached terminal status for all **18/18 model calls** and
materialized all **360/360 denominator rows**. Thirteen calls returned a
schema-valid 20-ID response; five calls crossed the frozen 1 MiB returned-tool
byte cap and were stopped. Consequently:

- scoreable rows: **260/360 (72.2%)**;
- overall exact correct coverage: **191/360 (53.1%)**;
- exact correctness among scoreable rows, counting explicit abstentions:
  **191/260 (73.5%)**;
- conditional exact accuracy among answered rows: **191/247 (77.3%)**;
- claim-matched B+C correct coverage: **94/180 (52.2%)**;
- B+C exact correctness among scoreable rows: **94/130 (72.3%)**; and
- B+C conditional exact accuracy: **94/122 (77.0%)**.

The preflight was separate from the matrix. It passed on its first attempt for
`agentskill-observability-paper`: 20/20 scoreable, 19/20 correct, 12 retrieval
calls, 326,412 returned bytes, and 229.18 seconds.

## Per-cell results

Each cell is one model call over one project's 20 questions. B+C has 10
questions per cell. A cap-stopped cell contributes denominator abstentions but
zero scoreable rows.

| Project | Rep. | Terminal status | Scoreable | All correct | B+C correct | B+C wrong | B+C abstain |
|---|---:|---|---:|---:|---:|---:|---:|
| agentsight | 1 | complete | 20/20 | 16/20 | 8/10 | 2 | 0 |
| agentsight | 2 | complete | 20/20 | 15/20 | 8/10 | 2 | 0 |
| agentsight | 3 | tool-result byte cap | 0/20 | 0/20 | 0/10 | 0 | 10 |
| ActPlane | 1 | complete | 20/20 | 12/20 | 7/10 | 3 | 0 |
| ActPlane | 2 | complete | 20/20 | 12/20 | 7/10 | 0 | 3 |
| ActPlane | 3 | complete | 20/20 | 12/20 | 7/10 | 3 | 0 |
| bpf-developer-tutorial | 1 | tool-result byte cap | 0/20 | 0/20 | 0/10 | 0 | 10 |
| bpf-developer-tutorial | 2 | tool-result byte cap | 0/20 | 0/20 | 0/10 | 0 | 10 |
| bpf-developer-tutorial | 3 | tool-result byte cap | 0/20 | 0/20 | 0/10 | 0 | 10 |
| eunomia.dev | 1 | complete | 20/20 | 11/20 | 5/10 | 5 | 0 |
| eunomia.dev | 2 | complete | 20/20 | 13/20 | 5/10 | 3 | 2 |
| eunomia.dev | 3 | complete | 20/20 | 15/20 | 7/10 | 0 | 3 |
| agentskill-observability-paper | 1 | tool-result byte cap | 0/20 | 0/20 | 0/10 | 0 | 10 |
| agentskill-observability-paper | 2 | complete | 20/20 | 19/20 | 10/10 | 0 | 0 |
| agentskill-observability-paper | 3 | complete | 20/20 | 19/20 | 10/10 | 0 | 0 |
| academic-writing-skills | 1 | complete | 20/20 | 15/20 | 6/10 | 4 | 0 |
| academic-writing-skills | 2 | complete | 20/20 | 16/20 | 7/10 | 3 | 0 |
| academic-writing-skills | 3 | complete | 20/20 | 16/20 | 7/10 | 3 | 0 |

Full machine-readable cell values are in `raw/cell-summary.csv`; raw responses,
events, prompts, commands, costs, and both unscored and atomic v4 checkpoints
are under `private/full/raw-model/`.

## Family results

| Family | Registered | Scoreable | Correct | Wrong | Abstain | Correct coverage | Scoreable-row exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — action | 90 | 65 | 32 | 28 | 30 | 35.6% | 49.2% |
| B — artifact-linked | 90 | 65 | 55 | 10 | 25 | 61.1% | 84.6% |
| C — cross-session | 90 | 65 | 39 | 18 | 33 | 43.3% | 60.0% |
| D — cutoff state | 90 | 65 | 65 | 0 | 25 | 72.2% | 100.0% |
| **All** | **360** | **260** | **191** | **56** | **113** | **53.1%** | **73.5%** |
| **B+C** | **180** | **130** | **94** | **28** | **58** | **52.2%** | **72.3%** |

The reader was exact on all 65 scoreable D rows. Its main weakness among
scoreable outputs was C (39/65 correct), followed by A (32/65).

## Project-level B+C results

| Project | Scoreable | Correct | Wrong | Abstain | Registered coverage | Scoreable-row exact |
|---|---:|---:|---:|---:|---:|---:|
| agentsight | 20/30 | 16 | 4 | 10 | 53.3% | 80.0% |
| ActPlane | 30/30 | 21 | 6 | 3 | 70.0% | 70.0% |
| bpf-developer-tutorial | 0/30 | 0 | 0 | 30 | 0.0% | N/A |
| eunomia.dev | 30/30 | 17 | 8 | 5 | 56.7% | 56.7% |
| agentskill-observability-paper | 20/30 | 20 | 0 | 10 | 66.7% | 100.0% |
| academic-writing-skills | 30/30 | 20 | 10 | 0 | 66.7% | 66.7% |

All three `bpf-developer-tutorial` calls crossed the byte cap. One of three
calls did so for both `agentsight` and `agentskill-observability-paper`.
This is a bounded-reader coverage result, not a transport or path-monitor
failure.

## Comparison with existing exact-fact conditions

All values below use the same 120 question IDs and corrected v4 answers. Raw is
the mean over three repetitions and therefore has three times as many registered
rows. The percentage is the directly comparable quantity.

| Condition | All-family correct coverage | B+C correct coverage | Scoreable rate | Interpretation |
|---|---:|---:|---:|---|
| Final State | 30/120 (25.0%) | 0/60 (0.0%) | 100% | answers cutoff-state facts only |
| Counts | 3/120 (2.5%) | 0/60 (0.0%) | 100% | aggregate lower-information control |
| ProcGrep | 12/120 (10.0%) | 0/60 (0.0%) | 100% | official action-only baseline |
| bounded Raw | 191/360 (53.1%) | 94/180 (52.2%) | 72.2% | measured, but five calls exceeded the retrieval-byte budget |
| repaired Trajectory | 102/120 (85.0%) | 60/60 (100.0%) | 100% | repair-corpus result under test |

The registered B+C effect is repaired Trajectory minus Raw =
**+0.478**, with a seeded hierarchical fixed-corpus interval
**[+0.272, +0.728]**. However, the predeclared invalid-cell veto applies:
five Raw cells did not return a scoreable response. The comparison verdict is
therefore **mixed/inconclusive**, not Trajectory superiority or accuracy
parity. The interval remains useful only as a denominator-inclusive sensitivity
summary.

## Historical baseline compatibility

The historical State Diff, Session Local, and OCPM Features conditions were
specified for a superseded pathology-diagnosis experiment. They produced no
scores on this 120-question exact-fact matrix.

| Historical condition | Compatible numerical score here | Requirement for a future matched row |
|---|---|---|
| State Diff | N/A | same 72 files/cutoffs, same 120 IDs/v4 oracle, and an explicit mapping from exact diff evidence to every question |
| Session Local | N/A | same evidence split by true top-level session, fixed aggregation, same reader/repetitions/budgets and failure denominator |
| OCPM Features | N/A | frozen official OCEL/OCPM output over the same sources, then the same reader/repetitions/budgets and question scorer |

Final State is retained as the available state-only control; it is not relabeled
as the richer historical State Diff condition. No incompatible old diagnostic
score is pooled with this result.

## Cost and resource use

Across the 18 matrix calls, the monitor recorded:

- **4,222.41 seconds** of summed per-call wall time (70.37 minutes; calls were
  scheduled with at most two-way concurrency);
- **282** retrieval tool calls;
- **11,876,245** returned tool-result bytes;
- for the 13 complete calls that emitted final usage records,
  **13,434,834** input tokens, of which **12,344,832** were reported cached,
  **193,206** output tokens, and **81,959** reasoning tokens.

Among the 13 schema-valid calls, median wall time was 284.41 seconds. The five
cap-stopped calls emitted no final model-usage record and together crossed the
cap on 6,676,489 returned bytes; a completed tool result can carry the
cumulative counter past 1 MiB before the monitor terminates the process.
The runtime manifest contains 221,487,880 logical source bytes across the 72
files; use that reproducible value instead of a rounded on-disk-size label in
any paper-facing resource description.

The old deterministic timing assigned one shared project-loop time to several
methods and was independently ruled non-comparable. Raw/Trajectory speedup or
cost ratio is therefore not reported.

## Decision and paper-facing recommendation

This run closes the literal `Raw=N/A` gap: Raw now has a real bounded 18-call
matrix, 360 denominator rows, raw artifacts, and measured accuracy/cost.
It does **not** establish the registered representation-superiority hypothesis,
because 5/18 Raw calls failed to engage through a scoreable final answer under
the fixed byte budget.

Recommended baseline-table treatment:

1. replace `Raw=N/A` with **53.1% overall correct coverage, 52.2% B+C coverage,
   72.2% scoreable rows**, explicitly labeled `gpt-5.6-terra`, medium,
   64-call/1 MiB/15-minute bounded reader;
2. retain the five cap-stopped cells and the mixed/inconclusive verdict;
3. do not claim Trajectory superiority, necessity, or cost advantage from this
   run; and
4. keep State Diff, Session Local, and OCPM Features as N/A for this exact-fact
   protocol unless they are separately executed on the matched matrix.

No paper or evaluation-document edit is made by this experiment.

## Reproducibility artifacts

- frozen protocol: `protocol.md`
- runner and scoring path: `runner.py`
- runtime/source hashes: `runtime-freeze.json`
- boundary controls: `controls/boundary-controls.json`
- real preflight: `preflight-result.json`
- all scored rows: `raw/method-results.csv`
- all model costs: `raw/costs.csv`
- per-cell and per-project summaries:
  `raw/cell-summary.csv`, `raw/project-family.csv`
- comparison and effect:
  `raw/baseline-comparison.csv`, `raw/effects.json`
- machine-readable run summary: `raw/run-summary.json`
