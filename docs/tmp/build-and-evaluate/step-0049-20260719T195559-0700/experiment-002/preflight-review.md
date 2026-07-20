# Independent Preflight Review — Experiment 002

**Reviewer:** Grok 4.5, read-only  
**Verdict:** **APPROVE FULL RUN**

## Scope Checked

The reviewer read the plan, plan review, plan re-review, real preflight, and
`script/rq3_qwen_semantic_task_stack_eval.py`. It inspected retained outputs
under `.agentsight/experiments/rq3-qwen3b-semantic-task-stack-v1/`, including
the failed partial caches, completed preflight caches, predictions, and
inference summary. It found no stage score in the inference outputs and edited
no file.

## Bounded Execution Correction

The first preflight failure was an output-constraint implementation defect.
The archived caches are partial (5/47, 84/95, 32/32, and 22/22), lack the new
constraint version, and were never scored. The repair changes only enforcement
of the already approved transition contract: depth-specific direct GBNF for
legal `keep_depth`, the non-empty first stack, fixed JSON keys, lowercase label
alphabet, and the 48-character limit. Independent transition validation still
rejects illegal output, and there is no retry, clamp, default, or fallback.

The model path and SHA, seed, temperature, budgets, visible prompt fields,
transition equation, and stage isolation remain unchanged. Resume rejects any
cache whose algorithm or output-constraint version differs. Different raw
responses under the stricter grammar are an expected consequence of fixing the
constraint and are not semantic tuning from labels or scores.

## Preflight Findings

| Check | Result |
|---|---|
| One complete trajectory from each framework | 47 + 95 + 32 + 22 = 196/196 operations |
| Prediction SHA-256 | `13f9f03a49b4c2f03b278e1068d36d284f46442ab176498200f0d0851e624987` |
| Variable depth | minimum 1, maximum 6, mean approximately 2.51 |
| Transition validity, non-empty stacks, retained IDs | zero invalid |
| Grammar expressiveness | stay is admitted and an empty initial stack is rejected |
| Context capacity | maximum prompt 2,527 tokens, below 8,192 |
| Stage isolation | no manifest or score artifact; scorer not run |
| Resume | cache-only second invocation reproduced predictions |

Direct GBNF is an equivalent strict enforcement of the approved JSON
transition contract and the plan's constrained-JSON requirement.

## Zero Same-Leaf Stays

The observed 30 pushes, 164 suffix replacements, two ancestor-only pops, and
zero same-leaf stays are adverse semantic behavior, not invalid execution.
Stay is legal and expressible, but the validity contract does not require every
transition type to occur. Qwen 3B almost always creates a fresh leaf, which may
over-segment and hurt ordinary B-cubed. The preflight correctly recorded this
without retuning. The fixed full-population score must decide usefulness.

## Must-Fix Issues And Authorization

There are no must-fix issues for contract validity. The fixed 405-trajectory
run may proceed from empty `direct-gbnf-v1` caches, without semantic changes,
and scoring may begin only after all predictions are fixed.
