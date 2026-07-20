# REAL PREFLIGHT — Variable-Depth Semantic Task Stack

**Completed:** 2026-07-19T21:07:32-07:00  
**State:** Complete; full run is authorized subject to independent review of the
bounded output-constraint repair  
**RQ:** RQ3 — tag accuracy

## Scope

The preflight executed one complete public CodeTraceBench trajectory from each
of mini-SWE-agent, OpenHands, SWE-agent, and Terminus2. It covered 196 source
operations (47, 95, 32, and 22 respectively). Inference opened neither the
official stage manifest nor any stage ranges. The model saw only the visible
root task, complete current stack, preceding observation, and current source
action specified by the approved plan.

## First Attempt And Preserved Failure

The first attempt used llama.cpp's top-level JSON Schema conversion. It
materialized 143 valid transitions before Qwen attempted a label longer than
the 128-token response budget. The partial output showed that llama.cpp had
silently skipped the schema's `maxLength`/pattern restriction, so generation
could not close the JSON object. The run stopped immediately and produced no
score. Its four partial per-session caches are preserved under
`.agentsight/experiments/rq3-qwen3b-semantic-task-stack-v1/preflight-invalid-json-schema-20260719T210652-0700/`.
They contain 5/47, 84/95, 32/32, and 22/22 transitions for the four sessions.
No partial response was reused.

This was an output-constraint implementation defect, not a semantic-result
failure. The repair changed only how the already approved transition contract
is enforced: the evaluator now generates a depth-specific llama.cpp GBNF
directly from the legal `keep_depth` range, non-empty-first-stack rule, JSON
keys, lowercase label alphabet, and 48-character label limit. The model,
quantization, system prompt, evidence representation, transition equation,
seed, temperature, metrics, comparisons, and interpretation are unchanged.
There is still no retry, repair, clamp, fallback, or inferred transition.

Two label-free implementation probes verified that the grammar admits the
intended state changes: an empty stack produced a legal push, and a two-frame
stack retained its root while replacing its leaf. The failed preflight was then
archived, and the four-framework preflight was restarted from empty caches.

## Completed Preflight

The repaired run completed all 196/196 operations and wrote one validated
transition for every source operation. Stack depth was genuinely variable:
minimum 1, maximum 6, mean 2.5102, with counts 1:5, 2:129, 3:29, 4:27, 5:2,
and 6:4. The longest generated label used the full allowed 48 characters. The
largest request used 2,527 prompt tokens, below the fixed 8,192-token slot.
Total local inference usage was 102,145 prompt tokens and 4,023 completion
tokens; wall time was 17.64 seconds with four concurrent sessions on the RTX
5090.

All transitions satisfied the transition contract. Their structural actions
were 30 pushes, 164 suffix replacements, two ancestor-only pops, and zero
same-leaf stays. The last distribution is recorded as a visible diagnostic,
not silently corrected or used to tune the prompt: the approved complete run
and ordinary B-cubed score must determine whether Qwen 3B's semantic decisions
are useful.

The completed predictions have SHA-256
`13f9f03a49b4c2f03b278e1068d36d284f46442ab176498200f0d0851e624987`.
A second invocation reused the fixed caches, completed in 1.56 seconds, and
reproduced the same prediction file. No benchmark stage label or score was
opened during either invocation.

## Checks And Decision

- Archive extraction, source-reference equality, and exact operation ordering:
  passed for all four adapters.
- Sequential state and fresh within-trajectory frame identities: passed.
- Non-empty variable-depth stack after every operation: passed.
- Direct GBNF output contract and independent parser validation: passed.
- Complete prompt representation and context capacity: passed.
- Cache identity and deterministic resume: passed.
- Stage/manifest isolation: passed.
- Semantic accuracy: intentionally not inspected in preflight.

The implementation is executable on real trajectories and the correction did
not tune semantics from labels or scores. Proceed to the fixed 405-trajectory
run if the independent reviewer agrees that direct GBNF is an equivalent
enforcement of the approved JSON transition contract.
