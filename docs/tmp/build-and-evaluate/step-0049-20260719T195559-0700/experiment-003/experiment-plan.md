# Experiment Plan — Single-Frame Incremental Semantic Task Stack

**Proposed:** 2026-07-19T21:38:00-07:00  
**State:** Approved after three serial read-only plan reviews; implementation
and REAL PREFLIGHT authorized  
**Paper RQ:** **RQ3 — How accurate are the tags?**

## Fixed Scientific Contract

The thesis remains exactly **“Agent observability needs profiling, not only
debugging.”** The four RQs remain attribution, localization, tag accuracy, and
cost. The original abstract, introduction, motivation, system story, and
positive RQ3 hypothesis remain fixed. This experiment may select only the
automatic operation-stack construction mechanism and its directly owned
evidence. It cannot narrow, replace, or reinterpret the paper story.

Experiment 001's multi-resolution recurrence is a complete strong baseline.
Experiment 002's arbitrary-list semantic stack is invalid/incomplete and has no
score. Experiment 003 is a new mechanism test motivated only by V1's
source-visible execution failure; no CodeTrace stage or score was viewed.

## One Tested Hypothesis

> On all 405 existing source-valid failed CodeTraceBench trajectories, a fixed
> local Qwen 2.5 3B model that incrementally maintains a variable-depth active
> semantic task stack, introducing at most one new semantic frame per observed
> operation, produces leaf-operation instances whose ordinary per-operation
> B-cubed F1 against human stages exceeds the current recurrence, the completed
> multi-resolution recurrence candidate, source-derived phase, and matched raw
> action.

This is one RQ3 mechanism hypothesis. It does not answer all of RQ3 and no
outcome authorizes changing the paper-level hypothesis or RQs.

## Single Online Transition

Let `S_0 = []`. Before operation `t`, `S_(t-1)` is an ordered list of active
semantic frame instances. The fixed local model reads public task-identity
text, complete current stack labels, preceding source observation, and current
source action. It returns exactly:

```json
{"keep_depth": 1, "new_frame": "write introduction"}
```

or:

```json
{"keep_depth": 2, "new_frame": null}
```

The transition is:

```text
S_t = prefix(S_(t-1), keep_depth)
if new_frame is a string: append one fresh frame instance(new_frame)
```

`keep_depth` may be any integer in `0..|S_(t-1)|`. `new_frame` is either null
or one non-empty lowercase English verb phrase of at most 48 characters. The
resulting stack must be non-empty. A new frame always receives a fresh
within-trajectory instance identity. Operation `t` is assigned to the active
leaf and its full ancestor path is retained for weighted profile folding.

This one rule supports all required online state changes:

- keep the full prefix and use null: stay on the current goal;
- keep the full prefix and add one frame: enter one child goal;
- keep a shorter prefix and use null: return to any ancestor in one step;
- keep a shorter prefix and add one frame: replace a completed suffix with one
  sibling or branch goal.

Total depth has no fixed maximum. It may differ widely across trajectories and
may grow by one on every successive operation. A single observed operation may
introduce at most one new semantic goal because it cannot causally justify an
arbitrary hidden chain of newly invented goals. Multi-level pop remains legal
because the preceding observation and current action can show that several
active goals have ended.

A semantic frame is a temporally extended goal capable of owning multiple
lower-level operations. It is not one command, file, function, argument,
expression, benchmark stage, explanation, or word from an action. Continued
work under the same goal retains the existing leaf; the model does not rename
retained frames. Invalid JSON, illegal depth, illegal label, empty resulting
stack, output truncation, or context overflow makes execution incomplete.
There is no retry, repair, clamping, default, or fallback.

## Fixed Representation And Backend

The system instruction states the transition semantics and the temporally
extended-goal definition above. It does not include benchmark labels, stage
examples, target counts, thresholds, or score feedback. The user prompt uses
this fixed order:

1. public task-identity text deterministically de-slugged from `source_ref`,
   limited to 1,200 characters;
2. the complete root-to-leaf stack without truncation;
3. preceding observation or literal `none`, limited to 2,400 characters;
4. current source action, limited to 2,400 characters.

Long fields use the already approved deterministic head/ellipsis/tail
representation. The current action's result, future operations, stages, stage
counts, incorrect-step labels, weights, and targets are invisible.

- Model: official `Qwen/Qwen2.5-3B-Instruct`, 3.09B parameters.
- Quantization: local Q4_K_M GGUF, SHA-256
  `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.
- Runtime: local llama.cpp build 9870, revision `2d973636e`, 8,192 tokens per
  concurrent slot, NVIDIA GeForce RTX 5090.
- Decoding: temperature zero, fixed seed 20260719, direct depth-specific GBNF,
  and a fixed 96-token response budget.

The output grammar permits exactly one label or null, so generation cannot use
an unbounded same-step frame list. It does not limit total stack depth.

## Complete Inputs, Baselines, And Standard Metrics

Reuse all 405 source-valid failed CodeTraceBench trajectories: 20,866
operations, 2,948 human-verified contiguous stages, 251 tasks, and four agent
frameworks. Reuse the existing public source adapters and source references.
Inference constructs archive paths directly from trajectory IDs and fixes all
predictions before a separate process may open the verified stage manifest.

Compare exactly:

1. single-frame Qwen semantic stack;
2. completed multi-resolution recurrence from Experiment 001;
3. current released recurrence;
4. source-derived phase grouping;
5. matched raw-action grouping.

The primary metric is ordinary unweighted per-operation B-cubed precision,
recall, and F1 against the complete official stage partitions. Exact adjacent
boundary precision, recall, and F1 are secondary standard segmentation
metrics. Report candidate-minus-each-baseline differences; a paired 10,000-
resample task-cluster bootstrap interval against the completed multi-resolution
recurrence by name; each framework separately; group counts; transition
coverage; depth distribution; new-frame rate; validity; model calls and tokens;
wall time; and peak memory. New-frame rate diagnoses small-model degeneration;
it is not an adoption metric or a custom accuracy substitute.

CodeTraceBench has flat stages, not gold nested trees or open-vocabulary frame
names. Therefore the result tests leaf-instance partition fidelity, not literal
label accuracy or complete nested-hierarchy fidelity. This is a system-level
comparison using richer source-visible text, not a claim of matched action-only
algorithmic superiority or proof that stack discipline alone causes a gain.

## Fixed Interpretation

- **Supported and adopted:** candidate B-cubed F1 exceeds all four baselines,
  the paired task-cluster 95% interval versus the completed multi-resolution
  recurrence is wholly positive, all four framework effects are non-negative,
  and every isolation, coverage, grammar, and stack-validity check passes.
  Adoption additionally requires remeasuring stack-construction time and
  resource use in RQ4, because per-operation local-model inference replaces the
  current inexpensive constructor.
- **Promising but not adopted:** candidate point estimate is highest but the
  interval includes zero or one framework materially regresses.
- **Contradicted:** candidate B-cubed F1 does not exceed the strongest existing
  baseline.
- **Invalid/incomplete:** leakage, missing operations, future evidence, invalid
  transitions, truncation, context overflow, or scoring failure.

A supported result authorizes one bounded release implementation and updates
only to mechanism-owned paper text. Any other valid result retains the current
release mechanism and records the candidate without inventing a third prompt
variant. No result changes the story, thesis, contributions, or RQs.

B-cubed compares only the candidate leaf partition with flat human stages. It
cannot validate ancestor labels, nested depth, or hierarchy quality. Even a
supported result may be stated only as evidence for the complete semantic-stack
backend under its richer visible text; it must not be attributed to variable
depth or stack discipline. A contradicted result likewise cannot by itself
distinguish a bad hierarchy hypothesis from degeneration of this fixed 3B
model; the registered new-frame rate is reported to expose that limitation,
not to override the score.

## Execution

1. Three serial read-only plan reviews judge scientific fit, transition
   sufficiency, causal visibility, metric validity, baseline strength, and
   interpretation. Repairs may simplify or clarify the plan but cannot use
   target labels or scores.
2. Update the external evaluator to the single-frame contract. Use synthetic
   transition tests only before REAL PREFLIGHT.
3. REAL PREFLIGHT starts from empty caches and executes one complete trajectory
   per framework. It checks extraction, grammar, state, depth, context, and
   resume while all stages remain hidden.
4. If preflight is valid, run all 405 trajectories from empty V2 caches to
   completion. Preserve every request, response, transition, assignment, and
   runtime summary.
5. Only after complete predictions are fixed, run the scorer once over all
   official stages.
6. A fresh independent reviewer reconstructs metrics and judges the registered
   interpretation before any release or paper change.

If supported and adopted, the full WRITE loop may update mechanism-owned paper
text while preserving the original AgentProf story. Grok and Claude must then
independently review the complete paper and evidence. The read-only
`docs/agentpprof-paper/` submodule remains untouched.
