# Analyst Study Protocol R315

R315 packages the existing R305 visible case packets and hidden answer key into a controlled analyst-study protocol. It does not sync datasets, rerun profilers, or report human/agent analyst results.

## Status

- Protocol status: ready_to_run.
- Participants in assignment table: 24.
- Trials: 144.
- Tasks: 6.
- Views: flat, fixed_session, operation_stack.
- Balanced task-view cells: True (8 to 8 trials per task-view cell).
- Leakage check: pass.

## Analyst Task

For each visible packet, the analyst ranks up to three `group_id` values that appear most likely to contain the target phenomenon, assigns confidence, cites visible fields, and records time. The hidden answer key scores selected groups after the response is locked.

## Endpoints

- Primary endpoint: whether the analyst selects at least one hidden-positive or high-lift group before exhausting the visible packet.
- Secondary endpoints: selected positive recall; selected positive precision; selected operation work fraction; time to first accepted evidence; confidence calibration against hidden positive rate.

## Claim Scope

- Supports now: R315 supports readiness for a controlled human/agent analyst study over existing label-hidden packets.
- Does not support: developer productivity improvement; time-to-answer improvement; human accuracy improvement; automatic anomaly detection; single-view dominance.
- Promotion gate: Only after analysts complete the visible packets and hidden answer-key scoring shows better accuracy/work/time tradeoffs can the paper promote C4 beyond automated inspectability.

## Tasks

| Task | Dataset | Query family | Problem |
|---|---|---|---|
| agentnet_incorrect_step | agentnet | step-quality | Find incorrect human desktop steps. |
| agentnet_redundant_step | agentnet | step-quality | Find redundant human desktop steps. |
| agentreward_looping | agent-reward-bench | failure-looping | Find repetitive web-agent behavior in expert-reviewed trajectories. |
| agentreward_side_effect | agent-reward-bench | failure-side-effect | Find side-effectful web-agent trajectories. |
| osworld_group_start | osworld-human | human-boundary | Find human grouped-action segment starts in desktop traces. |
| satraj_unsafe | satraj-os-safety | safety | Find unsafe desktop computer-use operations. |
