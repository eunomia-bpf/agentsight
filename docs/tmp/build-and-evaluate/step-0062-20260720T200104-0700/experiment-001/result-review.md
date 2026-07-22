# Final Result Review — Source-Native Task-Control pprof

Timestamp: 2026-07-21T09:30:00Z
Decision: valid supporting result after parser repair and complete rerun

## Reviewed Question

This review checks one RQ3 mechanism hypothesis: whether explicit Codex user
tasks, active plan items, and exactly linked delegations can be projected into
a variable-depth task stack while every attributable operation inherits one
active path and additive weights remain conserved. It does not judge whether
the source-declared plan is an ideal human decomposition or whether an LLM can
infer missing task structure.

## Review History

The first completed run was invalid. Review found that copied parent history in
fork files and an unparsed `sub_agent_activity` child-link encoding silently
removed real source work. The rejected output was not adopted. The evaluator
was repaired without changing the hypothesis, task-state rule, workload, or
metric, and the same full corpus was rerun.

## Recomputed Full-Run Facts

The repaired run processed the recorded byte prefix of all 6,357 Codex JSONL
files, containing 46,469,655,787 bytes. Before task-path construction it found
4,886 eligible source sessions and 1,267,006 source-owned operations.

- ownership-resolved sessions: 4,885 / 4,886;
- scored operations: 1,265,888 / 1,267,006, or 99.9118% coverage;
- exact complete-path agreement on the covered subset: 1,265,888 / 1,265,888;
- task-transition precision/recall/F1: 1.0 / 1.0 / 1.0 over 27,824 transitions;
- event weight conserved exactly at 1,265,888;
- token weight conserved exactly at 73,999,344,068;
- depth distribution: 390,781 / 743,595 / 99,330 / 32,182 operations at depths 1 / 2 / 3 / 4;
- delegation paths: 176,145 operations across 3,071 unique delegate frames.

The remaining exceptions are explicit rather than hidden: one missing ownership
boundary, 1,118 unscored raw operations, 44 unresolved parent links, five
unresolved operations, 246 multi-active-plan states, and 43 parse-error records
across 32 sessions. They prevent a universal-coverage claim but do not invalidate
the measured covered population.

## Product Artifact Review

The selected representative AgentCap family contains 38,330 operations and
1,100 explicit task-control transitions. AgentPProf generated one deterministic
standard pprof with 27,479 unique stacks and 1,118,275 compressed bytes:

`docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz`

Its SHA-256 is
`ca2e704a215d3dfe07c3dd613baa3cb707324dc43d1a9dbadc44261b420bc859`.
Stock `go tool pprof` decodes the file. Focusing on
`run_subagent_review` returns 379 operations, including a three-frame delegated
path that ends in reviewing AgentCap top-conference claim evidence. No custom
renderer or frontend is required.

## Implementation And Correctness Checks

The focused Python suite passes all six tests, including legacy fork ownership,
exact subagent linkage, concurrent parent/child isolation, variable task depth,
complete-prefix reading, and explicit machine-result parsing. AgentPProf passes
all 63 unit and integration tests across its library and CLI suites. The pprof
readback and focused query both succeed.

Candidate/reference exact agreement is source-replay fidelity, not independent
semantic accuracy: both interpretations are checked against raw source
coordinates, but the result cannot prove that the declared task names are the
best possible semantic decomposition. The experiment correctly keeps this
claim separate from later Codex annotation or public-label accuracy work.

## Verdict

```text
run status: valid
tested hypothesis: supported for observable source-native task control
research value: supporting
paper impact: additional RQ3 mechanism and product evidence
next paper decision: retain as source-fidelity evidence; do not promote it to complete semantic tag accuracy
```

The result may be returned to the outer orchestrator. It does not authorize a
paper-story change, a new RQ, a universal source-coverage claim, or a custom
visualization product.
