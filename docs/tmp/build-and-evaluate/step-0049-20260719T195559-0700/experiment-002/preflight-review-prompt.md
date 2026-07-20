# Independent Preflight Review Request

Act as a read-only senior AI/agent-systems experiment reviewer. Read the
complete files below and inspect the implementation and retained local outputs
they name:

- `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-002/experiment-plan.md`
- `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-002/plan-review.md`
- `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-002/plan-rereview.md`
- `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-002/real-preflight.md`
- `script/rq3_qwen_semantic_task_stack_eval.py`

The first preflight exposed that llama.cpp's JSON Schema conversion did not
enforce string length and yielded truncated JSON. The failed caches were
preserved and never scored. The evaluator was repaired to generate direct GBNF
from the same already approved JSON transition contract, then restarted from
empty caches and completed 196 operations.

Judge only whether this is a bounded execution correction rather than semantic
tuning, whether the repaired preflight validates the approved mechanism, and
whether the fixed full run may proceed. Explicitly consider the observed zero
same-leaf stays: decide whether it makes execution invalid under the approved
contract or is an adverse semantic behavior that must be left for the fixed
full score. Do not propose a new prompt, threshold, dataset, metric, RQ, or
paper story. Do not edit any file. Return one of `APPROVE FULL RUN`, `BLOCK`, or
`INCOMPLETE`, followed by concrete must-fix issues only if they are necessary
for contract validity.
