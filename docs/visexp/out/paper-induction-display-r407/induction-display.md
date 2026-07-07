# R407 Paper Induction Display

This artifact converts existing R402/R403/R404 induction evidence into one claim-facing paper table.
It is not a new empirical experiment.

- Status: pass
- Git commit: `4e1d441e9fba5eeac40287a825428a45cc13d884`

| Paper block | Question | Evidence | Main numbers | Supported conclusion | Non-claim |
| --- | --- | --- | --- | --- | --- |
| E1 recursive formation | profiler 能否在没有用户指定 field chain 的情况下形成递归 operation stack? | Rust induction replay over one tracked AgentRewardBench slice. | 729 个 operations；15 个 induced stacks；深度直方图 2:1/3:1/4:13；session-as-evidence view 有 16 个 stacks。 | 可见边界证据足以诱导参差递归的 operation-only stacks，session 只是可选 evidence field。 | 不能声称自动发现所有 intent boundaries。 |
| E2 localization ablation | induced stacks 能否作为真实 hidden-label tasks 上的可见 profiler view? | The induced view is scored on the same six R300/R320 labeled tasks as the main benchmark. | 4/6 tasks 形成 variable depth，2/6 tasks 在 material stop 停止；AP 0.2762 vs hand-configured 0.3116；work@5 0.653 vs flat 1；groups 12 vs fixed-session 285。 | induction 降低 flat inspection work 和 fixed-session fragmentation，但 AP 仍弱于 hand-configured specs。 | 不能把它写成 task-specific profile specs 的替代品。 |
| E3 depth actionability | induced-stack depth 是否是实际可调的 profiling surface? | The depth cap is swept from 1 to 5 while hidden labels are used only after profiling. | query-aware median AP 在 depth 3 最高（0.2865）；median work@5 在 depth 5 最低（0.4727）；material-split AP-best depths 覆盖 2, 3, 4, 5。 | 不同目标偏好不同递归深度，因此 depth 是 profile-configuration knob。 | 不能声称自动 depth selector 或 analyst-productivity 改善。 |

## Checks

| Check | Passed | Detail |
| --- | --- | --- |
| r402_passed | True | R402 run-result reports pass. |
| r403_passed | True | R403 run-result and report both pass. |
| r404_passed | True | R404 run-result and report both pass. |
| r406_passed | True | The read-only English sync packet has no failing checks. |
| table_has_three_claim_rows | True | The display is organized as three claim-facing rows, not a run ledger. |
| non_claim_boundaries_present | True | Each table row carries an explicit non-claim. |
| chinese_paper_inputs_table | True | The Chinese paper inputs the generated R407 table fragment. |
