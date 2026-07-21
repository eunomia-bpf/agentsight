# Cycle Audit And Final Verdict

## Entry-to-Exit Change Audit

- paper: unchanged
- thesis: unchanged and exact — **“Agent observability needs profiling, not
  only debugging.”**
- RQs: unchanged — attribution, real-problem localization, tag accuracy, cost
- idea story: unchanged
- shared skills: unchanged
- production AgentProf and AgentSight code: unchanged
- branch: unchanged
- new artifacts: review reports and source verification only

## Scientific Disposition

The review rejects the current field-centric visualization and flat recurrence
constructor as sufficient evidence of a task-semantic flamegraph. It does not
reject operation stacks, the profiling thesis, or the positive four-RQ program.

The current paper's hierarchy:

```text
project -> agent -> session/prompt -> tool -> command/path/status
```

answers where runtime records came from. The required hierarchy:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

answers how work was decomposed, where it consumed resources, where it
repeated, and what it produced. The two should not be conflated.

## Selected Next Mechanism Family

The next experiment will test **intent-anchored task-stack construction**:

1. user task messages establish task roots;
2. explicit plans, todo items, delegations, and nested agent tasks establish or
   update subtask paths;
3. progress and completion events close or resume those paths;
4. ordinary LLM, tool, command, file, process, and network operations inherit
   the active task path and supply action/object/result evidence;
5. agent, model, session, tool type, command, path, and status remain profile
   tags, filters, colors, measures, or detail fields.

This is not another version of the failed per-operation open-vocabulary stack
controller. It changes the information boundary: the constructor may mutate
task state only on sparse intent-bearing control events, and data-plane
operations cannot invent persistent task frames.

## First Evaluation Target And RQ

The next experiment answers **RQ3 only**: whether intent-anchored construction
recovers accurate task/subtask structure and stable task identities. The
primary scored population must provide structure independently of the tested
constructor. WorkArena++ is the leading public compositional reference because
its workflows are assembled from atomic subtasks. ToolSandbox can add an
independent dependency/completion check, but its milestone DAG is not by itself
nested task ground truth.

The complete eligible local Codex population is a secondary real-world
coverage and scale target. It can test that task frames arise from source-native
requests, plans, delegations, progress, and completion while data-plane events
inherit the active path, but it cannot score its own structural correctness.
The next experiment plan and real preflight must report the exact source paths,
enumeration method, eligibility rules, exclusions, parser validation, and
materialized output before a full Codex run.

The primary evaluation must separately score occurrence-level task/subtask
assignment and stable comparable identity across runs, use standard metrics and
fair fixed baselines, and keep the scoring reference hidden from construction.
RQ1 decision quality and RQ2 real-problem localization are later experiments;
repeated, failed, or abandoned paths observed in Codex are qualitative examples
until independently evaluated.

## Gate Routing

- EXPERIMENT: **required next**
- WRITE: skipped until a valid complete result is adopted
- REVIEW: complete for this step

No story rewrite is authorized. A positive result will enter a later WRITE
gate; a failed constructor changes the mechanism before it changes the thesis,
RQs, or intended task hierarchy.

## Final Verdict

**REVIEW complete; route to EXPERIMENT.** The paper-level gap is now precise,
the next RQ3 mechanism is non-equivalent to the failed field/recurrence and
per-operation controller families, and the larger original research ambition
is preserved.
