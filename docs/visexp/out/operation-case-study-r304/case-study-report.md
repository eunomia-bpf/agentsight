# R304 Operation-Stack Case Packet

R304 converts the automated utility proxy into a label-hidden case packet. Across six existing labeled tasks, the top-5 query-aware operation-stack cases inspect a median 9.4% of operations, recover 18.8% of positives, and achieve median lift 1.651. The packet exposes only ordinary operation fields and keeps oracle labels in a separate answer key.

## Task Scores

| Task | Dataset | Groups | Work fraction | Recall | Precision | Lift |
|---|---|---:|---:|---:|---:|---:|
| agentreward_looping | agent-reward-bench | 5 | 0.4938 | 0.6508 | 0.9111 | 1.3179 |
| agentreward_side_effect | agent-reward-bench | 5 | 0.1454 | 0.1139 | 0.217 | 0.7831 |
| satraj_unsafe | satraj-os-safety | 5 | 0.042 | 0.2621 | 0.9056 | 6.2384 |
| agentnet_incorrect_step | agentnet | 5 | 0.0014 | 0.0034 | 0.1429 | 2.4057 |
| agentnet_redundant_step | agentnet | 5 | 0.0089 | 0.0177 | 0.1444 | 1.9838 |
| osworld_group_start | osworld-human | 5 | 0.4074 | 0.3874 | 0.1812 | 0.951 |

## Claim Scope

- Supports: operation-stack groups can become reviewer-auditable case packets for real labeled failure, safety, quality, and boundary questions.
- Narrows: these packets are automated evidence over existing labels, not a detector or human productivity study.
- Integrity: visible packet fields exclude hidden oracle labels; the answer key is separate.
