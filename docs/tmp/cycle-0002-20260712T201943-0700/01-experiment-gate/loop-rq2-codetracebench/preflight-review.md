# Independent REAL PREFLIGHT Review

**Reviewed:** 2026-07-12T21:47:00-07:00  
**Reviewer:** independent subagent  
**Skill applied:** `research-experiment-design`, including its real-preflight
rule and experiment-plan template  
**Round 1 verdict:** **REVISE**

## Materials

The reviewer read the then-current runner, source-only report, approved plan and
five-round plan review, selected official raw archives, CodeTracer classifier,
AgentProf JSON outputs, and both OpenHands source variants. The reviewer made no
file, Git, submodule, RQ, thesis, hypothesis, or paper-story change.

## Confirmed Passes

### Hidden-label boundary for executed code

The executed runner projected only ordinary trajectory identity, framework,
model/task metadata, outcome, step count, and raw paths. It did not load
annotation paths, stages, incorrect/unuseful step IDs, label reasoning, or
`llm_analysis`. Current operations and stacks are target-label blind.

This does not yet prove the eventual scoring path because label join and metrics
were absent.

### AgentProf engagement and count checking

Release AgentProf was genuinely invoked for semantic, raw-action, and phase
views. Its JSON stack weights were compared with a separate Python counter over
the operation rows. This proves operation-file ingestion and folding, but not
differential scoring, target ranking, prediction, or metrics.

## Must-Fix 1: Missing End-To-End REAL PREFLIGHT

The approved preflight requires real target archives, matching task-held-out
failed/successful references, AgentProf proposed and baseline profiles,
differential scores, predictions, terminal label join, and metric
recomputation. The current runner accepts no full manifest and implements none
of those downstream stages.

Minimal repair:

1. preserve the current result as a source-adapter/AgentProf dependency check;
2. implement one scoring path shared by `preflight` and `full`;
3. in preflight mode, run selected targets with their real references, semantic
   and both main baselines, prediction output, terminal label join, and actual
   AP/R@30%/work@50%; and
4. omit full permutation/bootstrap repetitions only during preflight.

## Must-Fix 2: MiniSWE Source Unit

The selected raw log has 48 visible assistant response markers, 47 fenced
commands, one non-fenced substantive final summary, and manifest step count 47.
The runner had called every non-fenced marker a protocol retry and used a
generic `len == expected - 1` synthetic terminal heuristic. Neither is a valid
source contract.

Minimal repair:

- explicitly define the benchmark operation as an executed fenced command if
  supported by the official parser/source protocol;
- record non-fenced assistant turns as excluded non-operation events without
  falsely labeling all of them retries;
- remove the generic synthetic-terminal count-fitting rule; and
- choose one deterministic official MiniSWE source path rather than switching
  because a count matches.

## Must-Fix 3: OpenHands Recall And Observation Pairing

The selected event stream has 94 agent-source non-bookkeeping actions, one
user-source workspace recall, one user task message, and manifest count 95.
Keeping recall while excluding the initial message is plausible but was not
stated as a source-schema principle. Worse, rendering recall arguments exposed
the duplicated task prompt to phase/action-kind regexes, allowing task words to
determine the semantic stack. Observations were not paired through integer
`cause` as planned.

Minimal repair:

- freeze recall as a framework retrieval operation and the initial message as
  the human prompt;
- render recall identity without its duplicated task text;
- pair observations through integer `cause`; and
- validate the rule across the real event-stream population.

## Must-Fix 4: OpenHands SWE-Raw Context Lineage

The source-only check changed to longest request `messages` after discovering
that concatenating responses crosses restarts and context compaction. Although
this avoids obvious double counting, revision 4 and the official seed parser do
not publish that rule. One sample contains 112 call records, a longest request
context with 48 prior tool calls, and 48 declared steps, while chronological
responses contain 111 tool actions and later continued work. Count agreement
does not itself prove the selected branch carries benchmark labels.

Before admitting this cell, require an official preprocessing rule, an
independent source-only completion lineage, or a complete source-variant audit
that fixes branch/compaction/retry/final-response behavior without selecting by
`step_count`. Maximize the actual assistant tool-call history, not generic
message count. If no independent canonical branch exists, mark the variant
unresolved rather than count-fit it.

## Required State

The report must state:

```text
SOURCE-ONLY CHECK: PARTIAL PASS
AgentProf folding matches for selected archives.
REAL PREFLIGHT: INCOMPLETE
```

The full 3,291-archive scientific run must not begin until the four items above
are repaired and an independent re-review passes. No change to the fixed RQ,
hypothesis, thesis, contribution, or paper story is authorized or needed.

## Round 2: End-To-End Implementation Re-Review

**Reviewed:** 2026-07-12T23:21:56-07:00
**Reviewer:** same independent subagent
**Skill applied:** `research-experiment-design`
**Verdict:** **REVISE**

The reviewer confirmed that all four Round-1 must-fixes are closed:

1. REAL PREFLIGHT now executes public source extraction, release AgentProf,
   source-valid matching, scoring, pre-label prediction, terminal label join,
   and tie-block metrics through one shared path.
2. MiniSWE no longer synthesizes or count-fits a terminal operation.
3. Native OpenHands uses real agent actions, excludes user prompt/recall from
   semantic features, and pairs observations only through integer `cause`.
4. SWE-raw OpenHands has a complete 313-archive lineage audit and never selects
   a branch from `step_count` or annotations.

The reviewer also passed safe manifest projection, predictions-before-label,
same-task exclusion, source-valid support fallback, exact AgentProf counts, and
complete tie-block semantics. The six-target negative sign remains a preflight
diagnostic and does not authorize any hypothesis, RQ, thesis, story, or paper
change.

### Sole Remaining Must-Fix

The then-current `full` command invoked only the deterministic primary path and
could label that incomplete execution `PASS`. It lacked the declared
frequency-matched controls, 2,000 outcome-null trials, 10,000 task-clustered
bootstrap replicates, compatibility/secondary metrics, and terminal status for
all 3,316 manifest rows.

### Minimal Implementation Response

The runner now:

- gives every full-manifest row a terminal source-valid or excluded status;
- runs main semantic/raw-action/phase paths through release AgentProf;
- writes primary predictions and frequency-partition selection before labels;
- computes CodeTracer-compatible macro P/R/F1 and separate zero-positive
  false-positive burden;
- reports incorrect, unuseful, and union labels plus framework breakdowns;
- evaluates flat/session, absolute-hotspot, and 200 of 10,000 frequency-matched
  non-semantic controls;
- runs 2,000 exact-cell outcome permutations;
- runs 10,000 task-clustered full score-recomputing bootstrap replicates with
  same-task exclusion reapplied; and
- emits `PASS` only when all approved counts and components complete.

The altered shared path passed `py_compile`, a synthetic end-to-end control,
null, bootstrap, and report-boundary test, and a fresh real six-target
CodeTraceBench preflight with unchanged metrics. Round-3 independent re-review
is required before the full run.

## Round 3: Full-Runner Convergence Review

**Reviewed:** 2026-07-12T23:26:19-07:00
**Reviewer:** same independent subagent
**Skill applied:** `research-experiment-design`
**Verdict:** **PASS**

The reviewer independently verified the sole Round-2 repair:

- all 3,316 manifest rows receive exactly one terminal source status;
- the auxiliary deterministic full report is always `INCOMPLETE`, and the
  final report can pass only after 405 targets, 200 retained controls, 2,000
  null trials, and 10,000 bootstrap replicates complete;
- the 10,000-to-200 frequency partition selection is label-blind and the
  retained controls reuse matching, same-task exclusion, the differential
  estimator, and tie-block metrics;
- outcome permutations rebuild exact-cell reference profiles and fallback;
- task bootstrap multiplicities rebuild references, same-task subtraction,
  fallback, target work, and positives jointly for all three paired methods;
- compatibility metrics, zero-positive burden, unuseful/union analyses, and
  framework breakdowns use frozen pre-label scores; and
- CLI defaults equal revision 6, while the fresh real preflight remains PASS
  with unchanged metrics.

No scientific-validity or executability must-fix remains. This PASS authorizes
the approved complete run, not a scientific conclusion, RQ answer, hypothesis
change, story change, or paper edit. The reviewer changed no file and performed
no Git or submodule action.
