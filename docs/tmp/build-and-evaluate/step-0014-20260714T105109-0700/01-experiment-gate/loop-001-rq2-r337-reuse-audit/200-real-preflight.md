# REAL PREFLIGHT — R337 Reuse Audit

## Node metadata

- **Completed:** `2026-07-14T11:03:04-07:00`
- **Parent:** approved R337 reuse-audit plan
- **Purpose:** execute the real lightweight target-extraction path and verify
  that the fixed inputs, policies, target, and output schema are runnable
- **Verdict:** PASS for executability only

## Command

```bash
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337
```

The command exited successfully and wrote the real R337 report and CSV output.
It reported six tasks, six policies, and the three existing recall targets
0.10, 0.25, and 0.50. The required 25% rows are present for
`operation_stack:query_aware`, `fixed_session:query_aware`,
`raw_action_stack:query_aware`, and `flat:width`.

## Fixed-input schema check

One operation row from each fixed source was read successfully. The public
source identifiers are:

| Operation source | Public source identifier | Target label present separately from visible fields |
|---|---|---|
| AgentRewardBench | `McGill-NLP/agent-reward-bench` | `looping`, `side_effect` |
| SATraj-OS | `AI45Research/SATraj-OS` | `safety` |
| AgentNet | `xlangai/AgentNet` | `step_correct`, `step_redundant` |
| OSWorld-Human | `WukLab/osworld-human` | `group_position` |

All four rows also contain the existing visible action-derived fields required
by the ranker, including `action`, `phase`, `repeat_signal`, and `status`; the
applicable rows contain `environment`. The source schemas are therefore
compatible with the approved unchanged code path.

## Observed preflight output

The preflight reproduced the expected R337 shape and, as an executability
observation only, emitted the old operation-stack 25%-recall summary: 6/6 tasks,
median work 0.2000, and median 16 groups. The corresponding fixed-session,
raw-action, and flat rows are present. These values are not authorized as the
experiment result until the full R333 source replay and equivalence checks
finish.

## Boundary

This preflight did not establish source reconstruction, label separation, CSV
equivalence, the tested hypothesis, or a paper claim. It did not change a
source, task, policy, target, metric, model, or script. Proceed to the complete
R333 and R337 replay exactly as approved.
