# Step 0053 Report — Source-Native Task-Progress Boundary Test

## Step Identity

- started: 2026-07-20 07:48:53 -0700
- outer gate: EXPERIMENT
- selected paper RQ: **RQ3 — How accurate are the tags?**
- tested uncertainty: whether a fixed local adjacent-pair policy can use a
  completed trajectory's native intent/progress/action/result evidence to
  recover the author-verified flat workflow-stage partition better than the
  current action-field recurrence constructor
- final status: **VALID / COMPLETE / CONTRADICTED / NOT ADOPTED**

## User Intent Carried Into The Step

The main profile path must be task responsibility rather than system-field
classification:

```text
concrete task
-> nested subtask
-> phase/strategy
-> semantic action
-> operation object
-> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, visual encodings, additive measures, or source-linked evidence. A
system-field tree is not called a task-semantic flamegraph.

The thesis remains exactly **“Agent observability needs profiling, not only
debugging.”** The four author-fixed RQs and positive hypotheses remain
unchanged. A local mechanism result cannot rewrite or narrow them.

## Why This Experiment Was Selected

Steps 0050--0052 had already tested task-rooted responsibility inventories,
index-free label transitions, and a factorized continuation/label interface.
Those runs used root task, action fields, and preceding observations but did
not expose the agent's source-native per-step intent/progress and the current
action result. Step 0053 changes that missing observable while holding the real
population, standard metric, local model, and principal comparator fixed.

It tests one hypothesis and one flat stage component. It does not attempt to
validate nested depth, generated label wording, diagnosis quality, or the
complete task-semantic hierarchy.

## EXPERIMENT Node Record

### PROPOSE

The approved plan defines five exact source adapters and one fixed binary
`continue`/`boundary` policy. Inference sees only concrete task, native intent,
native progress, source action, and uniquely attributable result. The official
manifest and stages are opened only by the separate scorer.

Artifact: `experiment-001/experiment-plan.md`.

### REVIEW

An independent reviewer explicitly used `research-experiment-design`. Round 1
found one scientific must-fix: all five archive layouts needed exact,
deterministic source-evidence joins rather than count-based positional zipping.
The plan then fixed message/trajectory indices, OpenHands event cause and exact
tool-call ids, and ordered Terminus2 command-to-response alignment. Round 2
approved the plan.

Implementation review then found and closed three defects: wrong helper-module
imports, incomplete model/request cache identity, and omitted OpenHands native
model-response intent. A second implementation pass approved the evaluator with
zero must-fix issues.

Artifact: `experiment-001/plan-review.md`.

### REAL PREFLIGHT

One smallest complete trajectory from each source layout completed the real
source adapter, Qwen server call, fixed grammar, atomic cache, prediction
materialization, manifest-isolated scorer, standard metrics, and bootstrap
path. The 5 sessions contained 100 operations and 95 adjacent decisions. All
95 decisions were `continue`; this observation did not trigger prompt, model,
grammar, evidence, metric, or decision-rule tuning.

Artifact: `experiment-001/real-preflight.md`.

### FULL RUN

All registered cells reached terminal status:

- 405 sessions, 251 tasks, 20,866 operations, 20,461 adjacent pairs;
- 20,461 deterministic Qwen calls, zero retries;
- intent/progress/result coverage 15,304 / 10,418 / 13,143 operations;
- 19,856 `continue`, 605 `boundary`, 1,010 candidate groups;
- 33,560,944 prompt tokens, 122,766 completion tokens, 1,777.42 seconds.

The candidate ordinary B-cubed precision/recall/F1 is
0.253830/0.948235/0.400462, versus 0.782026/0.575029/0.662740 for the current
multi-resolution recurrence. Candidate boundary F1 is 0.066074: 104 true
positives, 501 false positives, and 2,439 false negatives. Exact-span F1 is
0.012633. The candidate loses in all four frameworks.

The 10,000-resample paired task-cluster candidate-minus-incumbent effect has
mean -0.262088 and 95% interval [-0.286562,-0.236752], with zero positive
resamples. The registered adoption condition fails.

Artifact: `experiment-001/full-run.md`; machine output remains under
`.agentsight/experiments/rq3-source-native-task-progress-boundary-v1/`.

### RESULT REVIEW

A fresh independent reviewer followed `research-experiment-design`, remained
read-only, and independently reconstructed the population, joins, isolation,
all primary/secondary metrics, four framework rows, and the 10,000-resample
bootstrap. It additionally rematerialized 15 trajectories across all five
source layouts and reproduced 832 operations' prompts and availability flags.

Verdict: **APPROVE, zero must-fix**. The narrow authorized conclusion is that
this fixed Qwen2.5-3B memoryless adjacent-pair policy substantially
under-segments the CodeTraceBench human stages and reliably loses to
multi-resolution recurrence. The review forbids generalizing this result to
all source-native task evidence, stateful constructors, nested task stacks,
RQ3, or the thesis.

Artifact: `experiment-001/independent-result-review.md`.

## Scientific Decision

The candidate is not adopted, not ported into the release runtime, not placed
in the positive paper result story, and not used to generate a positive
task-semantic flamegraph. The current released multi-resolution recurrence
remains the strongest complete flat-stage comparator on this population.

The experiment identifies the concrete mechanism failure: the fixed policy is
memoryless and compares only adjacent completed operations. It does not retain
an active subtask state and therefore merges long trajectories containing many
human workflow-stage transitions. This does not show that source-native task
evidence is generally insufficient or that a stateful constructor cannot work.

The next decision returns to the outer research loop. It must not be another
cosmetic adjacent prompt, grammar branch, cutoff, system-field rearrangement,
or post-hoc contraction. Any future task-semantic constructor must explicitly
maintain or expose task/subtask state and must be evaluated before its output is
called a task-semantic flamegraph.

## Repository Change Ledger

Added:

- `script/rq3_source_native_task_progress_boundary_eval.py`;
- the approved plan, review history, REAL PREFLIGHT, full-run report, independent
  result review, this step report, and outer audit under the timestamped Step
  0053 directory.

Updated:

- `docs/operation-stack-induction-algorithms.md` with the tested algorithm and
  failure mechanism;
- `docs/evaluation.md` with a development-only task-semantic construction
  boundary; and
- `docs/idea-story.md` with the task-main-stack versus system-metadata
  distinction, without changing thesis, RQs, or story.

Intentionally unchanged:

- all files under `docs/paper/`;
- the canonical `docs/agentpprof-paper` submodule;
- all shared skills;
- the released AgentProf runtime and recurrence implementation; and
- the current branch.
