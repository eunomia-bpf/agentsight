# R299 Boundary-Family Calibration

This run tests whether the R297 adjacent-boundary backend pattern remains useful beyond OSWorld-Human. It uses existing tracked operation JSONL only; no new dataset is synced.

## Results

| Candidate | Oracle | Test pairs | F1 | Precision | Recall | ECE | Best baseline | Best baseline F1 |
|---|---|---:|---:|---:|---:|---:|---|---:|
| osworld_human_group | human_group | 1122 | 0.6916 | 0.6531 | 0.735 | 0.3121 | always_boundary | 0.6706 |
| agentnet_step_correct | step_correct | 4066 | 0.3197 | 0.2518 | 0.4379 | 0.1256 | always_boundary | 0.2155 |
| agentnet_step_redundant | step_redundant | 2881 | 0.3361 | 0.3119 | 0.3645 | 0.1425 | always_boundary | 0.2645 |
| agentreward_looping | looping | 387 | 0.7833 | 0.7833 | 0.7833 | 0.0584 | repeat_signal_change | 1.0 |

## Suitability

| Candidate | Adjacent pairs | Positive rate | Eligible | Reason |
|---|---:|---:|---|---|
| osworld_human_group | 3691 | 0.4755 | True | eligible |
| agentnet_step_correct | 13883 | 0.1217 | True | eligible |
| agentnet_step_redundant | 9518 | 0.1516 | True | eligible |
| agentreward_looping | 700 | 0.18 | True | eligible |
| satraj_safety | 4035 | 0.0 | False | safety label is per trajectory, not an adjacent boundary in the sample |
| scalecua_history_state | 4869 | 0.0819 | False | previous-context marker, not a semantic boundary oracle |
| taubench_tool_dialogue | 0 | 0.0 | False | operation JSONL is not tracked for this run |
