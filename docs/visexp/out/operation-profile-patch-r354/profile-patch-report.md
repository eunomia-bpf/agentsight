# R354 Profile-Guided Patch Audit

- Overall: pass.
- Accepted patches: 5/6.
- AP improved tasks: 5/6.
- Top-5 lift improved tasks: 5/6.
- First-positive work improved tasks: 5/6.
- Median delta AP: 0.0376.
- Median group reduction: 0.0000.

| Task | Patch | AP delta | Top-5 lift delta | First-positive work delta | Verdict |
|---|---|---:|---:|---:|---|
| agentreward_looping | semantic->semantic | 0.1155 | 0.2820 | 0.0000 | accept_patch |
| agentreward_side_effect | semantic->coarse | 0.0591 | 0.1822 | -0.1125 | accept_patch |
| satraj_unsafe | semantic->coarse | 0.5081 | 2.2936 | -0.5986 | accept_patch |
| agentnet_incorrect_step | semantic->semantic | 0.0160 | 2.5010 | -0.0820 | accept_patch |
| agentnet_redundant_step | semantic->semantic | 0.0011 | 0.8679 | -0.0897 | accept_patch |
| osworld_group_start | semantic->semantic | -0.0004 | -0.1277 | -0.0020 | reject_patch_or_needs_new_mapping |

Hidden labels are used only after both profile specs have been executed by Rust.
The OSWorld-Human row is intentionally allowed to reject the visible rank-feature patch; it points to boundary-derived fields rather than a universal ranker.
