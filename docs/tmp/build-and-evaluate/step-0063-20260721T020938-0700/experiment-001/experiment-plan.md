# Experiment plan — real good-versus-bad differential pprof

Timestamp: 2026-07-21T02:09:38-07:00
Status: approved and executed

## Research question and tested hypothesis

This experiment belongs to RQ1: can AgentPProf attribute agent resource use to
task structure and localize behavior that distinguishes good and bad runs?

Tested hypothesis: when two real traces execute the same task, a signed
bad-minus-good task-semantic pprof makes excess failure-related work and the
good run's missing successful path inspectable with standard pprof tooling.

The experiment judges this hypothesis, not the entire RQ and not the full
paper.

## Real workload

Use the complete cleaned AgentRewardBench release at revision
`b6d17e646009d6cb63d5dd7be78807b680693f61`. The release contains trajectories
from AssistantBench, WebArena, VisualWebArena, and WorkArena with independent
human annotations. Normalize only the published VisualWebArena `resized` task
suffix so variants of the same benchmark task can be paired. Exclude a
trajectory when its annotators disagree on success; do not break annotation
ties in AgentPProf's favor.

The plan has two required scopes:

1. A detailed, source-verified case study for canonical task
   `visualwebarena.512`, which has successful and unsuccessful real traces.
2. The complete set of consensus-labeled canonical tasks containing at least
   one successful and one unsuccessful trace. Generate every bad-good pair in
   that set rather than stopping after a small smoke sample.

## Stack construction

Each benchmark step becomes one weighted operation. The stack is selected from
the following visible fields:

`task → subtask → strategy → action → object → result`

- `task` is the benchmark goal, not agent/model/session metadata.
- `subtask` is a short current-purpose phrase extracted from the trace's own
  reasoning and contracted across adjacent semantically similar steps.
- `strategy` is a small trace-visible action class such as search, inspect,
  navigate, input, verify, recover, or finish.
- `action` is the native action verb.
- `object` is the accessible-name target, URL domain, or explicit action
  object when available.
- `result` records only visible progress, repetition, error, finish, or stopped
  state.

Missing fields are omitted, so depth may vary. Agent identity, model, benchmark
label, session identifier, and success/looping annotations never become stack
frames. The human labels select and pair trajectories and later score results;
stack construction itself receives no outcome field.

The transition policy is deliberately sparse: native task/control context can
change the task stack; ordinary browser actions inherit it. No LLM call is made
for every operation. The deterministic fallback only contracts adjacent
purpose phrases and classifies visible action verbs.

## Product artifact and comparison

For each pair, AgentPProf receives the unsuccessful trace as
`--operation-file`, the successful trace as `--diff-base-operation-file`, the
same explicit stack, and one standard view. It emits exactly one signed pprof:

- positive sample: more measured work in the unsuccessful trace;
- negative sample: more measured work in the successful trace.

The case study uses token weight to answer where model cost accumulated. The
broad run also records operation-count profiles so conclusions do not depend
only on provider-specific token accounting. `go tool pprof` must decode the
artifact; no custom renderer is admitted.

## Evaluation

Primary evaluation statistics are standard:

- pairwise accuracy: whether a trace-visible non-progress rate ranks the
  unsuccessful trace above the successful trace for every real pair;
- ROC AUC across trajectories for the same blinded non-progress rate;
- ROC AUC for exact repeated-action rate against the independent human looping
  label;
- counts and results stratified by all four benchmarks.

The non-progress rate is not presented as a new metric. It is a deliberately
simple model score: the fraction of steps with either a reported action error
or a repeated action in the same visible state. Step count, total tokens, and
repeat rate are reported as baselines. Accuracy and ROC AUC—not a bespoke
top-k/cutoff measure—evaluate these scores.

For the case study, inspect the top positive and negative task paths and trace
them back to raw actions/reasoning. This is qualitative localization evidence;
the dataset has no human annotation of the correct stack path, so the run must
not call it localization accuracy.

## Acceptance and interpretation

The run is complete only if every consensus-labeled same-task bad-good pair is
attempted, every generated pprof decodes, additive candidate/base weights are
accounted for, the detailed case is traceable to raw evidence, and failures are
reported rather than silently dropped.

The result may support usefulness and RQ1 attribution/localization evidence. It
cannot by itself prove diagnostic repair, universal task decomposition, or
semantic tag accuracy.
