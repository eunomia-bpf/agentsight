# Separate Tool Question — Measurement Capability

All deterministic rows use the same 120-question source-direct oracle. The bounded Raw reader is N/A: the final registered Terra preflight engaged local evidence retrieval but was stopped by the frozen boundary contract before a scoreable answer. Its rows are not scored as wrong or abstain.

| Method | Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |
|---|---:|---:|---:|---:|---:|---:|
| final_state | A | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | B | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | C | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | D | 30 | 0 | 0 | 1.000 | 1.000 |
| counts | A | 7 | 11 | 12 | 0.233 | 0.389 |
| counts | B | 0 | 0 | 30 | 0.000 | 0.000 |
| counts | C | 0 | 0 | 30 | 0.000 | 0.000 |
| counts | D | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | A | 18 | 12 | 0 | 0.600 | 0.600 |
| procgrep | B | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | C | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | D | 0 | 0 | 30 | 0.000 | 0.000 |
| trajectory | A | 18 | 12 | 0 | 0.600 | 0.600 |
| trajectory | B | 16 | 14 | 0 | 0.533 | 0.533 |
| trajectory | C | 16 | 14 | 0 | 0.533 | 0.533 |
| trajectory | D | 28 | 0 | 2 | 0.933 | 1.000 |

## Predeclared contrasts and vetoes

- Trajectory − ProcGrep B+C correct coverage: 0.533, frozen-corpus project-block interval [0.283, 0.767].
- Trajectory B+C: 32/60 correct, 28/60 wrong, 60/60 answered.
- Per-project Trajectory B+C conditional accuracy: agentsight=1.000, ActPlane=0.400, bpf-developer-tutorial=0.700, eunomia.dev=0.000, agentskill-observability-paper=0.600, academic-writing-skills=0.500.

## Decision

- **procgrep_incremental_coverage:** rejected_by_correctness_veto
- **action_spine_identity_pass:** True
- **action_source_correctness_veto_pass:** False
- **trajectory_correctness_veto_pass:** False
- **raw_model_comparison:** unavailable_after_preflight

The positive factual-coverage difference over ProcGrep does not support a
capability claim. The trajectory preserved ProcGrep's action answers exactly,
but the official adapter grammar and the experiment's broader source-direct
action grammar agreed on only 18/30 action questions. More decisively, the
trajectory answered all 60 B+C questions but returned 28 wrong answers. The
exact numeric B+C thresholds originated in the superseded Step 0003 plan, but
this error rate rejects the implementation claim without depending on those
thresholds. This is a negative result for the current projection, not evidence
against workspace-centered representation in principle.

The deterministic preflight covered all six projects and is reused as the
complete 480-row deterministic matrix. The planned integrated comparison is
incomplete because none of the 360 Raw rows ran. Raw is N/A after a
retrieval-engaged Terra preflight was stopped by the frozen boundary contract;
the stop is a harness/contract incompatibility and yields no LLM-reader
accuracy, cost, efficiency, or superiority result. Deterministic wall times
also cannot be compared because the four methods share one project-loop timing
measurement.
