# Step 0062 — Source-Native Variable-Depth Task Stack

Timestamp: 2026-07-20T20:01:04-07:00
Outer state: EXPERIMENT
Selected RQ: RQ3 — How Accurate Are the Tags?
Status: complete; valid supporting result

## Purpose

This step tests whether AgentPProf can use task control that Codex explicitly
emits—user task turns, active plan items, delegation, nested child sessions,
and completion—to construct a variable-depth responsibility stack. Ordinary
model, tool, file, process, and network operations inherit that state and never
create persistent task frames merely because execution metadata changes.

The step tests source fidelity only. It does not infer an unexpressed ideal
human plan, canonicalize paraphrases across unrelated runs, or answer all of
RQ3. The paper thesis, four fixed RQs, paper sources, skills, and frontend are
unchanged.

## Experiment Nodes

- `experiment-001/experiment-plan.md`: fixed source-native hypothesis, real
  workload, independent raw replay, metrics, commands, and interpretation.
- `experiment-001/plan-review.md`: three serial reviews; the first rejected a
  per-operation WorkArena/Qwen pseudo-gold design, and the final reviewed plan
  approved the source-native mechanism.
- `experiment-001/real-preflight.md`: real root-family execution through
  parsing, replay, pprof input construction, and readback.
- `experiment-001/full-run.md`: complete repaired 6,357-file run.
- `experiment-001/result-review.md`: final validity and claim-boundary review.
- `outer-audit.md`: completion, scope, and transition audit.

## Execution And Repair

The first full run was rejected because fork files copy parent history and
because one exact Codex `sub_agent_activity` child-link encoding was not
parsed. Those defects omitted real operations before scoring. The same
experiment was repaired to use the canonical ownership boundary and both exact
spawn-to-child encodings, then rerun on the same complete byte-prefix census.

The final run reports 4,886 eligible source sessions, 1,267,006 source-owned
operations, 1,265,888 scored operations, and 99.9118% operation coverage.
Complete-path agreement and transition F1 are 1.0 on that covered subset;
event and 73,999,344,068-token weights are exactly conserved. Natural task
depth reaches four, and 176,145 operations lie on delegation paths.

Remaining source exceptions are recorded rather than guessed away: one missing
ownership boundary, 1,118 unscored operations, 44 unresolved parent links,
five unresolved operations, 246 multi-active-plan states, and 43 parse-error
records across 32 sessions.

## Product Result

The representative AgentCap root family contains 38,330 operations. AgentPProf
emits one deterministic standard pprof:

`docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz`

The file contains 27,479 unique stacks, is 1,118,275 bytes, and decodes with
stock `go tool pprof`. A focus query for `run_subagent_review` finds 379
operations and includes an exact delegated path for reviewing AgentCap
top-conference claim evidence. No frontend or alternative product artifact was
added.

## Verification

- `PYTHONPATH=script python3 -m unittest -v script.test_source_native_task_stack_eval`: 6/6 pass.
- `cargo test --manifest-path agentpprof/Cargo.toml --all-targets`: 63/63 pass.
- `go tool pprof -top`: pass.
- `go tool pprof -top -focus=run_subagent_review`: pass.

## Final Interpretation

The tested source-native hypothesis is supported for 99.9118% of the observed
source-owned operation population. This is useful product and supporting RQ3
evidence because the resulting hierarchy follows declared user work, plan
responsibilities, and delegation rather than session/tool/path metadata.

The perfect covered-subset replay score is not semantic gold accuracy. It does
not establish that continuation prompts such as `继续` are correctly
canonicalized, that lower result labels are complete, or that no-control
backends can infer the same task tree. Those remain later mechanism questions,
not reasons to discard or narrow the source-native result.

WRITE is intentionally skipped because this step is limited to experiment and
product evidence. The result returns to the orchestrator for later routing.
