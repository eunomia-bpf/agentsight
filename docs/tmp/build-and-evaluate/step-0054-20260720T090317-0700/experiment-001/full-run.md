# Full Run

## Verdict

**VALID / COMPLETE / CONTRADICTED / NOT ADOPTED.** The fixed source-native
stateful task-stack policy completed all 405 trajectories and every registered
standard score. It is substantially better than the prior per-operation stack
and the native-turn singleton control, but it does not recover the verified
workflow-stage partition as accurately as multi-resolution recurrence.

This rejects one fixed Qwen2.5-3B transition policy. It does not reject the
task-semantic hierarchy, stateful stacks in general, the paper thesis, or RQ3.

## Commands

```bash
python3 script/rq3_stateful_native_turn_task_stack_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full

python3 script/rq3_stateful_native_turn_task_stack_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/inference-summary.json \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --prior-stateful-assignments .agentsight/experiments/rq3-qwen3b-semantic-task-stack-v2/full/score/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score
```

## Complete Population And Isolation

- 405/405 trajectories, 251 task clusters, 17,148 source-native turns, 20,866
  operations, 20,461 adjacent pairs, and 2,948 verified stages completed;
- every operation appears exactly once under one immutable-root-to-active-leaf
  task path;
- five source layouts contributed 2,175 MiniSWE, 6,454 OpenHands-native, 3,576
  OpenHands-maximal, 1,460 SWE-agent, and 7,201 Terminus2 operations;
- native intent, progress, and result were available on 15,304, 10,418, and
  13,143 operations respectively;
- inference saw concrete task, complete active task labels, native
  intent/progress, planned source action, and only the preceding turn's result;
- it did not see human stages, recurrence assignments, phase/action-kind,
  agent/model/session/status, or the current turn's result;
- the active stack was never truncated and no fixed depth cap or post-hoc
  contraction was applied; and
- 17,148 deterministic Qwen2.5-3B calls used 26,006,567 prompt tokens and
  260,158 completion tokens in 2,128.42 seconds; all succeeded on the first
  attempt.

## Stack Behavior

All outputs and state transforms were legal. The policy emitted 6,534 `push`,
6,249 `replace`, 4,363 `stay`, and only two pure `pop` transitions. The
new-frame rate is 0.74545. Operation path depth including the root ranges from
1 to 69, with mean 6.49; the median per-session maximum depth is 7, the 90th
percentile is 34, and the maximum is 69. In 101/405 sessions the depth never
decreases.

The central failure is more specific than generic Qwen instability:

- 6,246 transitions create a fresh frame whose label is identical to the
  previously active leaf: 3,216 `push` and 3,030 `replace` decisions, nearly
  half of all new-frame decisions;
- 2,732 replacements leave the complete visible label path byte-for-byte
  unchanged while changing only the hidden frame instance identity;
- unique frame-instance identity turns these semantic continuations into new
  predicted groups even when the model repeats the same task goal;
- OpenHands maximal-history has new-frame rate 0.99525 and maximum depth 69;
  SWE-agent has rate 0.90685;
- the model generated 1,182 exact `phaseN` or `phase-N` labels despite the
  prompt's explicit prohibition on treating phases as persistent task frames;
- MiniSWE, OpenHands native, and Terminus2 are less degenerate, with new-frame
  rates 0.5582, 0.6873, and 0.6460 respectively.

Thus the persistent state and native evidence improve behavior, but the model's
transition interface does not preserve semantic frame identity. A repeated
label usually becomes a fresh sibling rather than `stay`.

## Standard Results

| Method | B³ P | B³ R | B³ F1 | Exact-span F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| stateful native-turn task stack | 0.931958 | 0.333171 | 0.490861 | 0.032768 | 0.261643 |
| multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.056435 | 0.265571 |
| prior raw operation stack | 0.999569 | 0.141282 | 0.247572 | 0.008062 | 0.221092 |
| native-turn singleton | 0.983154 | 0.221199 | 0.361145 | 0.019705 | 0.246396 |

The new policy produces 13,041 groups versus 2,948 official stages and 6,018
recurrence groups. Its high B-cubed precision and low recall identify residual
over-segmentation. It recovers 1,986/2,543 true adjacent boundaries but creates
10,652 false boundaries. Boundary F1 (0.26164) is close to recurrence (0.26557),
but partition F1 and exact spans remain clearly worse.

Across 10,000 paired bootstrap resamples over 251 task clusters, candidate
minus recurrence B-cubed F1 has mean -0.17226 and 95% interval
[-0.20665, -0.13666]; zero resamples are positive. The registered adoption
condition fails decisively.

## Framework Heterogeneity

| Framework | Candidate B³ F1 | Recurrence B³ F1 | Delta |
|---|---:|---:|---:|
| OpenHands | 0.377918 | 0.676295 | -0.298377 |
| SWE-agent | 0.271718 | 0.708893 | -0.437175 |
| Terminus2 | 0.627902 | 0.605471 | +0.022431 |
| MiniSWE-agent | 0.556650 | 0.691523 | -0.134873 |

Terminus2 is the one positive framework: response-level turns group multiple
commands under shared native analysis/plan, and the candidate slightly exceeds
recurrence. This is diagnostic heterogeneity, not an adoption veto or a license
to report only the favorable workload.

## Interpretation And Next Mechanism Question

The run establishes that source-native turns, an immutable task root, and
persistent variable-depth state materially improve the previous stack policy:
B-cubed rises from 0.2476 to 0.4909 and boundary F1 from 0.2211 to 0.2616. The
policy clearly can emit legal variable depth. A prominent, directly testable
remaining failure is identity churn for an unchanged semantic task; the current
run does not establish that this is the primary cause of the full B-cubed gap.

The most direct next question is whether a replacement that leaves the complete
visible label path unchanged should preserve frame identity rather than create
a fresh instance. For 2,732 such transitions this deterministic state semantics
leaves all future model-visible prompts unchanged, so it can be evaluated on
the already completed model trajectory without another model run. Same-label
pushes or replacements that also remove ancestors do change the visible path
and cannot be normalized without a new causal run. No normalization is applied
to the current registered result; it must be treated as a new, explicitly
reviewed experiment rather than a rescue score.

Flat CodeTrace stages validate only the active-leaf partition. They do not
validate ancestor topology, variable depth, nested label meaning, or the lower
`phase/strategy -> semantic action -> operation object -> result` suffix.

## Raw Artifacts

- inference, predictions, and 405 resumable session caches:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/`
- standard score rows, bootstrap samples, summary, and report:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/`
