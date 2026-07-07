# R406 English Operation-Stack Induction Sync Packet

This is a read-only sync packet over the English submodule and existing outer-repo R402/R403/R404 artifacts.
It does not edit the English paper submodule and it is not a new empirical experiment.

- Status: pass
- Git commit: `121fbcd40d6bfc7c282f2c835ba9d4236d5b7a0c`
- Rows: 4

## Evidence To Port

| Paper block | English status | Ready evidence | Numbers | Claim boundary | Sync action |
| --- | --- | --- | --- | --- | --- |
| RQ1 mechanism: recursive operation-stack construction | missing_from_submodule | R402 replays the maintained Rust profiler on a tracked AgentRewardBench slice and emits induced operation frames without a user stack-field order. | 729 operations; overview 15 stacks with depth histogram {'2': 1, '3': 1, '4': 13}; session-allowed view 16 stacks. | This supports configurable recursive folding, not automatic discovery of all intent boundaries. | Port the induction paragraph and keep session as optional evidence, not a default stack level. |
| RQ2 mechanism ablation: hidden-label localization | missing_from_submodule | R403 scores induced operation-stack groups on the same six R300/R320 hidden-label tasks. | 4/6 tasks produce variable-depth stacks and 2/6 stop when visible evidence has no material split; median AP 0.2762 vs hand-configured operation-stack 0.3116; median work@5 0.653 vs flat 1; median groups 12 vs fixed-session 285. | The hand-configured operation stack remains the stronger main policy by AP, so induction is an ablation and configuration probe. | Add a short RQ2 paragraph or table row under baseline/actionability discussion, not a new top-level experiment. |
| RQ3 actionability: depth sensitivity | missing_from_submodule | R404 sweeps --induce-max-depth over depths 1 through 5 using hidden labels only after profiling. | query-aware median AP is highest at depth 3 (0.2865); median work@5 is lowest at depth 5 (0.4727); material-split task AP-best depths span 2, 3, 4, 5. | This is a profile-configuration surface, not an automatic depth selector. | Use this as actionability evidence: different tasks prefer different recursive depths and metrics. |
| Scope guardrail | must_preserve_non_claim | R402/R403/R404 exclude oracle source fields and score hidden labels only after profiling. | R403 and R404 both pass hidden-label and no-oracle-source checks. | Do not claim human productivity, automatic patch selection, universal boundary discovery, or full OTel/LangSmith/Phoenix compatibility. | When porting into English, keep these limitations adjacent to the induced-stack result. |

## English Snippet Draft

```tex
% R406 read-only sync packet. Do not paste until English submodule edits are allowed.
\paragraph{Automatic operation-stack induction.}
The profiler can construct a recursive operation stack without asking the user for a fixed field order such as phase/action/status.
We run \texttt{--induce-operation-stack} on a tracked AgentRewardBench slice and let visible boundary evidence, semantic shift, changed-field density, and query hints choose adjacent cuts inside each current segment.
The overview replay covers 729 operations and produces 15 induced operation stacks; allowing session as evidence changes the result to 16 stacks, which confirms that session is an optional evidence field rather than a required stack level.
This result is an implementation and mechanism check for recursive folding, not an automatic boundary detector.

\paragraph{Induced stacks as a localization ablation.}
We then score the same induced operation-stack path on the six hidden-label localization tasks.
The induced view creates variable-depth stacks on 4/6 tasks and stops on 2/6 tasks when visible fields do not support a material split.
Its median top-5 inspection work is 0.653, compared with 1 for flat summaries, and its median group count is 12, compared with 285 for fixed-session drilldown.
The hand-configured operation stack remains stronger by median AP (0.3116 versus 0.2762), so this ablation supports configurable recursive folding rather than replacing task-specific profile specifications.

\paragraph{Depth sensitivity.}
Changing only the induced-stack depth cap changes the localization surface.
The query-aware induced view reaches its highest median AP at depth 3 (0.2865), while the lowest median top-5 work occurs at depth 5 (0.4727).
Across tasks with material splits, AP-best depths span 2, 3, 4, 5.
This is profile-configuration actionability, not an analyst-productivity result or an automatic depth selector.
```

## Checks

| Check | Passed | Detail |
| --- | --- | --- |
| english_submodule_read_only_scope | True | The script writes only under docs/visexp/out and reads docs/agentpprof-paper/main.tex without editing it. |
| r402_passed | True | R402 run-result.json reports pass. |
| r403_passed | True | R403 run-result and report both pass. |
| r404_passed | True | R404 run-result and report both pass. |
| english_gap_detected | True | The current English submodule does not yet mention --induce-operation-stack or induced operation-stack evidence. |
| outer_paper_and_ledger_have_evidence | True | The outer Chinese paper and evaluation ledger mention R402/R403/R404 induced operation-stack evidence. |
| public_profile_uses_operation_stack_key | True | R402 public JSON exposes operation_stack_induction and no stale task_stack_induction key. |
| snippets_include_claim_boundaries | True | The generated English snippets include non-claim boundaries. |
