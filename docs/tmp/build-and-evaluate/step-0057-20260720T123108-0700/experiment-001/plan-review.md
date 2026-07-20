# Plan Review — Global Task-Semantic Segmentation

## Round 1 — REVISE

The independent read-only reviewer explicitly applied the
`research-experiment-design` PLAN REVIEW standard after reading the user
instructions, RQ3, the proposed plan, and the necessary Step0050--Step0056
history.

The scientific design passed: the whole-completed-trajectory interval method is
non-equivalent to every prior causal/local transition method; the complete
CodeTraceBench workload, current recurrence baseline, causal control, ordinary
unweighted B-cubed primary metric, gold isolation, task-cluster uncertainty,
and bounded interpretation are sufficient. No additional benchmark, baseline,
metric, model, or infrastructure was requested.

One executability defect blocked approval. Port 18182 was launched with
`-c 65536 -np 4`, and llama.cpp `/props` reports only 16,384 tokens per slot.
Some complete projected trajectories exceed that limit. The reviewer required
the same model on a single-slot 65,536-token server, concrete commands, and a
real preflight that verifies server properties and exact prompt plus completion
budget.

## Repair

The plan now uses port 18183 with `-np 1 -c 65536`, retains the same model,
temperature, and seed, records complete server/infer/score commands, selects the
projected-token-longest complete trajectory in each framework for preflight,
and verifies `/props` plus token budget before inference. It also removes a
nonexistent CodeTraceBench token-width option; the figure uses observed
operation count only.

## Round 2 — APPROVE

The same reviewer checked only the repaired blocking defect. It confirmed that
the single-slot context, concrete commands, preflight selection and checks, full
single-worker run, and operation-only figure are executable. There are no
remaining scientific or executability blockers and no requested scope
expansion.

## Real-Startup Configuration Repair

Before inference, the actual single-slot startup exposed the model's native
limit: llama.cpp caps Qwen2.5-3B from a requested 65,536 tokens to its 32,768
training context. This is a runner/configuration fact, not a scientific-plan
change. The server command is therefore fixed at `-c 32768 -np 1`, and the
completion budget is reduced from 8,192 to 4,096 tokens. The longest measured
complete projected input is about 26.5K tokens, so input, completion budget,
and a 512-token margin fit without dropping any turn or adding rope scaling.

The first raw-archive preflight path was also replaced by direct reuse of the
already completed source-only operation projections and native-turn
assignments. Repeated archive decompression was the only bottleneck; the reused
caches cover all 20,866 operations and do not contain human stages. This is the
plan's stated evidence-reuse path and does not alter model-visible information.

## Round 3 — APPROVE

The same reviewer verified the actual native-context repair: `26,478 + 4,096 +
512 = 31,086 < 32,768`, with no truncation or rope scaling. It confirmed that
the code checks both projected and actual chat-token budgets and that the server
is single-slot. No blocker remained.

## Preflight Output-Schema Repair

The first real model response showed that redundant model-generated `start`
and `end` values could disagree. The interface now asks each non-final segment
only for its inclusive `through` boundary, derives the next start, and fixes the
final end to the trajectory end. This makes gap-free coverage structural; it
does not move a predicted boundary, alter semantic labels, or change the
hypothesis, input, model, workload, baseline, or metric.

The exact population-wide token check then found that the longest reused source
projection exceeded the native model context. Fixed field caps of 256 intent,
128 progress, 128 action, and 256 result characters retain every one of the
17,148 turns while making the longest exact input 27,552 tokens. With the
4,096-token completion budget and 512-token margin, the registered bound is
32,160, below 32,768. No trajectory, turn, or semantic field is removed.

During the complete run, one 70-turn trajectory reached the 4,096-token output
cap while its input used only 8,851 tokens. The runner now allocates the
available completion cap per request, with the reviewed 4,096-token minimum and
an 8,192-token maximum. All 331 cached completed responses used at most 78
tokens, so increasing their unused cap cannot alter them; the interrupted
response was never cached. This is a completion-truncation repair, not an
algorithm or evidence change.

Inspection of that deterministic truncated output showed the actual defect: the
model interpreted `subtasks[]` as an unbounded sequential plan and repeated
steps, while the first 331 completed responses all chose one whole-trajectory
segment. The single final interface revision uses one `parent > child`
`subtask_path` string and tells the model to avoid both whole-trajectory collapse
and per-turn fragmentation. This is the only prompt/schema revision admitted;
if the complete run still fails, the global Qwen2.5-3B mechanism closes rather
than spawning more prompt variants.
