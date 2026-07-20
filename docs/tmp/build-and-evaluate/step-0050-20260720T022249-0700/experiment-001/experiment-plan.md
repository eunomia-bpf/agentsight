# Experiment 001 Plan — Task-Rooted Semantic Stage Alignment

- proposed: 2026-07-20T02:22:49-07:00
- revised: 2026-07-20T03:44:41-07:00
- outer gate: EXPERIMENT
- paper RQ: **RQ3 — How accurate are the tags?**
- plan revision: 8, **approved after nine serial independent reviews**
- target paper story: unchanged

## Research Question And One Tested Hypothesis

This experiment asks one bounded question within the fixed RQ3:

> On complete real coding-agent trajectories with independent human stage
> intervals, can a task-rooted semantic plan followed by causal sequential
> alignment recover human workflow-stage spans more accurately than a matched
> plan-free semantic segmenter and the strongest current field-based grouping?

The tested hypothesis is:

> Given the concrete task and the same complete source-visible operation
> sequence, Qwen2.5-3B first constructing stable task/subtask hypotheses and
> then causally aligning every operation to those hypotheses achieves higher
> micro unlabeled span F1 than both a same-model plan-free segmenter and current
> multi-resolution recurrence on the complete 405-trajectory CodeTraceBench
> target population.

This tests one annotated workflow-stage level. It does not claim that
CodeTraceBench supplies gold names or nested trees; it does not independently
validate lower phase, semantic-action, object, or result frames; and it cannot
change the exact thesis, four RQs, contribution scope, or positive paper story.

## Task-Centric Semantic Contract

The paper-level main stack remains:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status are not main semantic
frames. They remain colors, filters, side details, or bottom-level evidence.
Event count, elapsed time, token use, and measured effects remain additive
width choices. The experiment scores only whether the proposed task-rooted
mechanism locates one independently annotated workflow-stage level; it does not
replace this larger semantic contract with CodeTraceBench's flat stages.

## Why This Experiment Has Paper Value

The current recurrence constructor groups repeated visible fields and therefore
can agree with stage partitions without explaining the concrete task being
performed. The completed per-operation Qwen policy had the opposite failure:
it maintained legal variable depth but created a fresh leaf for almost every
operation because each local decision could invent a new label. The smallest
principled change is to make task responsibilities stable before alignment:
derive them once from the real task, then reuse them while interpreting the
complete trajectory.

This experiment reuses existing trajectories rather than selecting another
benchmark or changing another cutoff. It directly asks whether that semantic
prior improves the hierarchy level that the human intervals can score.

## Public Real Workload And Complete Population

Use the already reconstructed public CodeTraceBench target population:

- benchmark: CodeTraceBench / CodeTracer;
- source manifest:
  `.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet`;
- raw public archives:
  `.agentsight/experiments/codetracebench-rq2/hub/bench_artifacts/full/`;
- target operation sequence:
  `docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl`;
- population: all 405 source-valid failed trajectories already used by the
  paper, containing 20,866 operations and 2,948 human-verified contiguous
  stage intervals across OpenHands, mini-SWE-agent, SWE-agent, and Terminus2;
- trajectory lengths: 20--275 operations; the full operation sequence of every
  trajectory is retained.

The run is post-hoc mechanism development on this existing population, not
untouched confirmation. No project-authored task, trajectory, stage, or gold
label is added.

## Independent Gold And Evidence Isolation

CodeTraceBench supplies contiguous stage ranges covering the scored operations.
Those ranges are used only as unlabeled workflow-stage intervals. Stage IDs are
arbitrary within a trajectory and are not treated as semantic names.

Inference reconstructs source evidence without opening the stage manifest.
Each model-input record is produced from an explicit whitelist containing only:

- the complete concrete task text from the initial public user request;
- operation ordinal;
- source-derived action kind and raw-action key;
- the source action;
- the preceding source observation, which is the result visible before the
  current action.

Human stage ranges, stage count, incorrect or unuseful labels, solved state,
resource weights, and every scorer output are absent. An observation is attached
only to the following operation as its preceding result. Each causal decision
sees no future operation and does not see the current action's result. A
preflight assertion checks the serialized model record keys against this whitelist.
Prediction outputs are completed before a separate scoring phase opens
`verified.parquet`.

## Shared Causal Operation Projection

Candidate and matched baseline process every operation in order and receive
byte-identical task, current-action, and preceding-observation evidence at each
step. Each call sees the projected concrete task, operation ordinal, action
kind, raw-action key, source action, and preceding observation. It does not see
future operations or the current action's result. Long text uses deterministic
head/ellipsis/tail projection measured by the retained Qwen tokenizer rather
than by characters. A request exceeding 8,192 input tokens after projection is
incomplete; no operation is removed or skipped.

This is a complete causal pass over every operation, not a claim that every byte
of every command output is model-visible. Raw archives and exact per-operation
requests are retained for audit.

## Candidate: Goal Plan Then Causal Sequential Alignment

Use the retained official Qwen2.5-3B-Instruct Q4_K_M GGUF with temperature zero
and seed 20260720.

### Goal planner

The planner sees only the concrete task. It returns an ordered JSON list of
concise, concrete task responsibilities. It may choose as many responsibilities
as the task requires, up to the number of operations; there is no fixed sibling
count and no hierarchy-depth limit implied by this one-level experiment.
Examples are `locate the failing parser`, `change its boundary handling`, and
`verify the regression test`, not `shell`, `read`, a file path, or `success`.
The raw returned plan is retained unchanged. Before alignment, exact duplicate
strings are removed deterministically after their first occurrence so the fixed
inventory contains unique responsibilities. This normalization reads neither
operations nor gold and does not rewrite any label.

The planner emits a nonempty JSON array under GBNF. Each unique label must
match `[a-z][a-z0-9 /+._-]{0,63}`. The normalized plan must remain nonempty and
cannot contain more items than operations. The prompt requires a concrete task
responsibility rather than an agent, model, session, tool, command, path, file
extension, or status. Every raw label is retained without semantic retry or
rewriting. Violations of that minimum task-semantic rule are counted
deterministically and bound interpretation of generated names; they do not make
an otherwise syntactically valid unlabeled-span prediction disappear. The
planner request is limited to 8,192 input and 2,048 output tokens; these limits
are separate from the smaller causal-decision output limit.

### Causal sequential aligner

The aligner keeps the preceding plan index as state. For each operation in
order, it sees the task, retained plan, preceding index (or `none` initially),
preceding observation, and current action, then returns exactly one zero-based
plan index. Indices may stay, advance, revisit an earlier responsibility, or
return after a failed attempt.
Consecutive equal indices form predicted spans. The immutable task root contains
every operation exactly once.

The exact candidate response is `{"plan_index": k}`, where GBNF restricts `k`
to an index present in the retained plan. No other key or text is permitted.

The aligner does not invent another frame. A plan with one entry is legal; an
empty plan, an out-of-range index, a missing operation, or context overflow is
an incomplete run rather than a post-hoc repair.

## Main Baseline And Controls

### Main matched plan-free semantic segmenter

The main baseline processes the same operations causally with the same task,
byte-identical current evidence, Qwen GGUF, temperature, seed, context, and
decoder. It keeps one current free-text workflow-stage label. At each operation
it returns either `stay`, retaining that label, or `switch` with one new concise
stage label. It has no goal-only planner or fixed responsibility inventory.
Consecutive operations retaining the same stage instance form spans.

The exact plan-free response is either
`{"decision":"stay","new_label":null}` or
`{"decision":"switch","new_label":"label"}`. The first operation must
switch. A new label obeys the planner's syntax and length. The prompt requests
a task-semantic name, but this baseline's generated names are neither scored
nor used as main task-stack frames. A copied system detail is therefore retained
and counted as a qualitative label violation rather than changing or
invalidating its otherwise legal boundary decision. `stay` preserves the same
stage instance and label; `switch` creates one new stage instance even if its
text matches an earlier label.

Each candidate call emits one constrained plan index; each plan-free call emits
one constrained stay/switch decision. Neither can create more than one boundary
at an operation. Candidate plan-label violations directly audit whether the
generated hierarchy meets the task-centric semantic contract. Plan-free labels
are unscored diagnostics and cannot enter that stack. Neither arm receives
semantic retries, rewriting, or score-driven edits. A
transport failure may be retried at most twice with the identical request; all
attempts are retained. The candidate's extra planner call, tokens, and latency
are reported rather than called compute-matched.

### Existing comparators and descriptive controls

- strongest current comparator: completed multi-resolution recurrence;
- current released coarse recurrence;
- phase-change grouping;
- raw-action-change grouping;
- action-kind-change grouping;
- one complete-trajectory span.

Only the plan-free Qwen segmenter and multi-resolution recurrence are main
comparators. The others diagnose whether a result exceeds trivial or
field-centered partitions.

## Standard Outcomes

Use ordinary, unweighted operation spans:

- **Primary:** micro PARSEVAL-style unlabeled exact-span precision, recall, and
  F1, excluding the immutable whole-task root;
- **Secondary:** ordinary unweighted B-cubed precision, recall, and F1 for the
  flat operation partition; exact adjacent-boundary precision, recall, and F1;
- **Diagnostics:** per-framework and trajectory-length slices, predicted span
  count, plan size, plan-index revisit rate, candidate and plan-free
  system-label violation counts, malformed/incomplete count, model calls,
  prompt/completion tokens, latency, and peak memory.

No labeled span score is reported because CodeTraceBench stage IDs are not
semantic names. No token-weighted metric, inspection-budget cutoff, reader
score, or project-authored accuracy measure is allowed.

## Registered Decision Rule

The tested hypothesis is **supported and the task-rooted mechanism is adopted**
only if all of the following hold on all 405 trajectories:

1. candidate micro unlabeled span F1 is strictly higher than both the matched
   plan-free Qwen segmenter and multi-resolution recurrence;
2. a paired task-cluster bootstrap 95% interval for candidate minus each of those
   two comparators is wholly above zero;
3. candidate coverage is 405/405, every one of 20,866 operations is assigned
   exactly once, and all evidence-isolation/context/output checks pass.

It is **promising but not adopted** if the candidate has the highest point
estimate but either interval includes zero. It is **contradicted** if a complete
valid run does not beat both main comparators. It is **incomplete** if coverage,
isolation, context, parsing, or assignment conservation fails. Secondary metrics
explain the result but cannot rescue a failed primary rule.

This decision rule addresses only unlabeled human workflow-stage fidelity.
Candidate system-label violations are reported separately and prohibit using
this experiment to claim that generated responsibility names are accurate or
that every rendered hierarchy already satisfies the full semantic contract;
CodeTraceBench provides no gold responsibility names for such a claim.

A local contradiction changes only this mechanism. It cannot narrow or replace
the fixed RQ3, exact thesis, four RQs, contributions, or paper story, and it is
not inserted as a negative result in the paper.

## Statistics

- bootstrap unit: underlying CodeTraceBench task, retaining every trajectory
  for each sampled task cluster;
- resamples: 10,000 paired samples;
- seed: 20260720;
- comparison: candidate minus each named main comparator, recomputing pooled
  micro unlabeled span F1 within every resample;
- interval: 2.5th and 97.5th percentiles;
- no prompt, model, evidence, plan, threshold, or metric change after scoring.

## Execution And Real Preflight

After serial plan-review approval:

1. implement one evaluator by reusing the existing CodeTraceBench source
   adapters and scorers;
2. reconstruct all public sources without opening stages, then run a real
   preflight on the complete trajectory with the largest source-evidence
   character estimate from each framework; report the actual tokenizer-measured
   request maximum across those four trajectories without calling it the
   population-wide token maximum;
3. exercise raw extraction, task recovery, the shared projection, goal planning,
   both sequential aligners, and single-decision grammars without opening the
   stage manifest or rendering a scored result;
4. if implementation defects are found, repair only the implementation or
   output grammar and repeat real preflight; do not change the RQ, hypothesis,
   population, evidence, baselines, metrics, or decision rule;
5. start the full inference outputs empty, complete all candidate and baseline
   calls for all 405 trajectories, then open the stage manifest once for
   scoring and run an independent result review.

The local inference server uses llama.cpp build 9870 (revision `2d973636e`) and
the official Qwen2.5-3B-Instruct Q4_K_M GGUF with SHA-256
`626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.
It has 65,536 total context across four parallel slots, temperature zero, and
seed 20260720. Each causal request uses at most 8,192 input tokens and 96 output
tokens; planner calls retain the separate 2,048-token output limit. Complete
execution makes one planner call per trajectory and one
candidate plus one plan-free decision per operation. The registered commands are:

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf \
  -ngl 99 -c 65536 -np 4 --host 127.0.0.1 --port 18182 \
  --seed 20260720 --temp 0 --metrics \
  --log-file .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/llama-server.log

python3 script/rq3_task_rooted_stage_alignment_eval.py infer preflight \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/preflight

python3 script/rq3_task_rooted_stage_alignment_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18182 --workers 4 \
  --out .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full

python3 script/rq3_task_rooted_stage_alignment_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/rq3-task-rooted-stage-alignment-v1/score
```

## Outputs

Raw output stays outside Git under
`.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/`:

- source metadata and selected public archive hashes;
- whitelisted model-visible records;
- exact requests, planner outputs, both assignment outputs, and attempt logs;
- predicted spans, scorer sufficient statistics, aggregate standard metrics,
  and all 10,000 bootstrap deltas;
- one representative folded profile and rendered task-semantic flame graph.

The Markdown experiment directory retains this plan, at least three serial plan
reviews, real-preflight report, complete-run report, and an independent result
review.

## Interpretation Boundaries

- A positive result supports automatic recovery of human workflow-stage spans
  on this complete CodeTraceBench target population; it does not by itself
  establish that the generated names are correct task responsibilities, nor
  validate universal nested hierarchy or literal free-text labels.
- The generated responsibility names may be shown qualitatively only. Their
  semantic accuracy needs independent label annotations before a quantitative
  label claim.
- Lower phase/action/object/result frames are visualization evidence until
  separately validated.
- Agent/model/session/tool/status remain metadata, never main-stack frames.
- Paper text remains unchanged until complete execution and independent result
  review authorize the WRITE gate.
