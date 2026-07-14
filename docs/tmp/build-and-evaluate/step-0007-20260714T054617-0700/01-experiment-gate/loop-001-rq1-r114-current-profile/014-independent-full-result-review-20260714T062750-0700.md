# Independent Full-Result Review: RQ1 R114 Current Profile

## Review identity

- Timestamp: 2026-07-14T06:27:50-07:00
- Role: independent read-only result reviewer
- Reviewed node: Step 0007 EXPERIMENT, R114 current-profile full run
- Verdict: **PASS**
- Must-fix findings: none

## Independent recomputation

The reviewer read the approved experiment plan, the full R114 aggregate JSON,
all 20 per-task effect-lineage CSVs, the emitted operation JSONL, the AgentProf
profile, and the structured replay result. It did not trust only the runner's
reported booleans.

| Check | Independently recomputed | Approved threshold |
|---|---:|---:|
| Completed tasks | 20/20 | 20/20 |
| Tasks with observed control | 20/20 | 20/20 |
| TP / FP / FN | 1,520 / 0 / 54 | measured |
| Precision | 100.000% | at least 98% |
| Recall | 96.569% | at least 95% |
| Negative effects / joined | 1,629 / 0 | joined = 0 |
| Selected rows | 1,520 | equals TP |
| Emitted operations | 1,520 | equals selected rows |
| AgentProf total mass | 1,520 | equals input mass |

| Category | Independently derived input | AgentProf output | Delta |
|---|---:|---:|---:|
| `dependency` | 121 | 121 | 0 |
| `edit` | 380 | 380 | 0 |
| `failure` | 39 | 39 | 0 |
| `read` | 723 | 723 | 0 |
| `test` | 257 | 257 | 0 |

## Artifact and identity checks

- All 20 DBs, snapshots, and lineage CSVs exist.
- Every task's TP, FP, FN, negative-effect count, and negative-join count agrees
  with the saved aggregate result.
- The 1,520 selected `(task,event_id)` pairs contain no duplicate.
- Independently applying the persisted `agent_process_ids` and
  `agent_tool_ids` to the per-task CSVs produces an operation multiset exactly
  equal to the emitted JSONL.
- Every emitted operation has unit weight.
- The weights of all 152 AgentProf stacks, the profile summary total, and all
  five category masses agree exactly with the independent input calculation.

## Deviation assessment

The valid preflight and full run used a temporary build of the existing
R114-compatible `agentsight 0.2.37` implementation because the PATH-installed
0.2.43 binary does not contain the research-only `--agent-comm` option.
`agentpprof 0.2.37` is the current AgentProf binary used by the paper. This
dependency deviation is disclosed in the preflight and full-run reports and
does not invalidate the scoped tested hypothesis. It forbids describing the
result as validation of AgentSight 0.2.43 specifically.

## Scientific decision

```text
run status: valid, with disclosed AgentSight binary deviation
tested hypothesis: supported
research value: supporting
paper impact: additional RQ1 evidence
```

The result authorizes a cumulative RQ1 integration statement: under the fixed
R114 real-Codex suite and its scoped process/tool lineage definition, AgentSight
rejects concurrent controls, and current AgentProf folds the correctly
attributed rows across runs while exactly preserving row count, total mass,
and known task-category mass.

The result does not assert that AgentProf inferred task categories, establish
arbitrary causal attribution, or cover every agent. These are boundaries on
this experiment, not changes to the larger thesis or the four fixed RQs. The
fixed thesis remains “Agent observability needs profiling, not only debugging.”
