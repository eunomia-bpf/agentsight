# R407 Paper Induction Display

This artifact converts existing R402/R403/R404 induction evidence into one claim-facing paper table.
It is not a new empirical experiment.

- Status: pass
- Git commit: `6650a93c534b4b351dff3aed7e01cd68de1b35f0`

| Paper block | Question | Evidence | Main numbers | Supported conclusion | Non-claim |
| --- | --- | --- | --- | --- | --- |
| E1 recursive formation | Can the profiler form recursive operation stacks without a user-supplied field chain? | Rust induction replay over one tracked AgentRewardBench slice. | 729 operations; 15 induced stacks; depth histogram 2:1/3:1/4:13; session-as-evidence view has 16 stacks. | Visible boundary evidence can induce ragged operation-only stacks, and session remains optional evidence. | Not automatic discovery of all intent boundaries. |
| E2 localization ablation | Do induced stacks work as a visible profiler view on real hidden-label tasks? | The induced view is scored on the same six R300/R320 labeled tasks as the main benchmark. | 4/6 variable-depth tasks, 2/6 material-stop tasks; AP 0.2762 vs hand-configured 0.3116; work@5 0.653 vs flat 1; groups 12 vs fixed-session 285. | Induction reduces flat work and fixed-session fragmentation, but hand-configured specs remain stronger by AP. | Not a replacement for task-specific profile specs. |
| E3 depth actionability | Is induced-stack depth a real tuning surface? | The depth cap is swept from 1 to 5 while hidden labels are used only after profiling. | best query-aware median AP at depth 3 (0.2865); lowest median work@5 at depth 5 (0.4727); material-split AP-best depths span 2, 3, 4, 5. | Different objectives prefer different recursive depths, so depth is a profile-configuration knob. | Not an automatic depth selector or analyst-productivity result. |

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
