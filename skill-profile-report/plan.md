# Experiment Plan: RQ1 skill-scoped resource attribution

## Research Question

- RQ exactly as written in the paper: **RQ1 — Does Semantic Profiling Improve Resource Attribution?**
- Specific uncertainty: whether exact Claude Code `Skill` invocations recur often enough for a skill scope in AgentPProf to identify which named skill accounts for aggregate token and operation budget.
- Why it matters: a recurrent named skill is an actionable optimization target that a developer can read from one aggregate pprof profile without inspecting every trajectory.

## Paper-Value Admission

- Planned role: supporting.
- Largest credible result: an exact, source-native skill frame exposes a recurrent budget concentration that no single session represents, directly illustrating “Agent observability needs profiling, not only debugging.”
- Strongest reject argument: the signal may be too sparse, or one session may dominate the apparent top skill.
- Independent evidence added: a complete census of the current full local Claude history, rather than the skill-thin frozen 42-session corpus.
- Positive decision: retain the skill hierarchy level and report the recurrent top skill as an actionable aggregate finding.
- Contradictory, mixed, or inconclusive decision: retain the implementation only if the exact field remains useful as a general source-native dimension, but state plainly that this corpus does not justify an aggregate paper finding.
- Best alternative: reanalyze the frozen paper corpus. It has only 3/42 exact Skill-call sessions, so the full local history has higher decision value for this question.

## Expected And Alternative Outcomes

- Expected: several named skills recur across sessions, and the token-leading skill is not dominated by one session.
- Competing explanation: the aggregate is sparse or is effectively one unusually large trajectory.
- Contradiction: exact Skill calls are too rare, or the top skill's maximum single-session share makes the aggregate finding indistinguishable from inspecting that one trajectory.

## Real Assets And Comparison

- System/data/tool: all readable Claude Code session JSONL files under `/home/yunwei37/.claude/projects`, the repository's `agent-session` parser and `agentpprof` binary, stock `go tool pprof`, and the existing paper-only pprof renderer path.
- Invocation signal: only a literal tool-use object with `name == "Skill"` and nonempty `input.skill`. `skill_listing`, `invoked_skills`, and `command-name` do not create scopes.
- Scope: the Skill tool event and subsequent LLM/tool events in the same Claude `promptId`, until the next exact Skill invocation (latest-wins replacement) or the first non-metadata `user` record with a different `promptId` (reset). For legacy rows without `promptId`, a non-meta, non-tool-result user message is a reset. Tool results, `isMeta:true` skill payloads, `sourceToolUseID`/`sourceToolAssistantUUID` records, same-`promptId` command metadata, attachments, and `last-prompt` snapshots do not reset scope. All other samples receive `skill=unscoped`.
- Start semantics: the LLM completion that emits a Skill tool call remains in the prior scope because the choice precedes the invocation. The Skill tool operation itself starts and is charged to the named scope.
- Crossing semantics: a later Skill invocation replaces the earlier skill. This produces disjoint, noncrossing, covering attribution intervals but deliberately does not attempt to infer a return to a possibly nested outer skill.
- Frame order: `project -> agent -> semantic task/operation path -> skill -> phase/action/object/result/outcome -> LLM/tool evidence`. Skill is below the semantic responsibility path because the same operation can use different skills, and above concrete evidence because its width must include governed LLM and tool work rather than the near-zero Skill call alone. Every sample also carries a `skill` pprof label so stock `go tool pprof -tagfocus` can select a scope.
- Main comparison: aggregate named-skill attribution versus per-session concentration of the same named skill.
- Controls: exact additive conservation and explicit exclusion of non-invocation availability metadata.
- Fairness: no inferred tags, hidden labels, model calls, thresholds, or target-guided corpus selection.

## Workloads And Metrics

- Workload: the complete parseable full-history Claude corpus discovered from the directory above at run time.
- Primary measurements: named-skill token mass and named-skill operation count.
- Recurrence: sessions per skill and invocations per skill.
- Aggregate-only visibility: maximum single-session share of the token-leading skill, plus the number of contributing sessions and the rank of that skill within each contributing session.
- Correctness: raw unique source-completion total equals parsed sample total equals folded-stack total equals decoded pprof sample total for each run. Claude assistant fragments sharing `(session file, message.id)`, with `requestId` as fallback, are one completion and repeated usage is counted once.
- Uncertainty: this is a complete local-history census, so no sampling interval is reported; limitations concern representativeness and signal coverage.

## Execution

- Preflight: run one real session containing an exact Skill invocation through the release build and inspect its pprof frames and `skill` tag.
- Full-history input: create a sorted NUL-safe manifest from `find /home/yunwei37/.claude/projects -type f -name '*.jsonl' -print0`, expand every entry as an explicit `--session-file PATH`, and record discovered, readable, parseable, excluded, emitted, skill-bearing, and distinct-project counts. Explicit session files are required because default root discovery filters by the current project.
- Full run command shape: `agentpprof --project-root "$PWD" --project-name claude-full-history --agent claude --view {tokens|operations} --stack project,agent,task,skill,phase,action,object,result,outcome,op,call,tool,token --no-cache --deterministic-output --output skill-profile-report/full-history-{tokens|operations}.pb.gz $(for each manifest path: --session-file PATH)`. Run once per view; each invocation emits exactly one `.pb.gz`.
- Completion: both crate test suites pass; every input file has been considered; both profiles load in stock pprof; conservation holds; both renderings are inspected.
- Raw/result path: `skill-profile-report/`.
- Target figures: renderer-produced token and operation flame graphs from the two standard pprof profiles.

## Interpretation Boundaries

- The profile attributes observed work to an invocation-defined scope; it does not prove the skill caused that work or that improving the skill will reduce all attributed cost.
- Sequential replacement prevents crossing scopes but cannot recover nested skill returns because the source records invocations, not return events.
- The rule over-counts work later in a prompt after the agent has stopped following the skill. It under-counts work that continues into a later genuine prompt. Latest-wins loses an earlier still-active or nested skill because no return event exists.
- The Skill invocation adds one named operation; its invocation-producing LLM completion remains outside the named scope.
- The finding is local-history evidence, not a population estimate for all Claude Code users or projects.
