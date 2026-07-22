# Independent implementation review

## Round 1 — REVISE

The reviewer used `oss-change-workflow`, ran the focused tests, and accepted
strict recursive shrinkage, same-turn preservation, stable semantic IDs,
complete visible-path score keys, official-label isolation, and the server
model-path check. Three execution blockers remained:

1. session cache identity omitted the exact prompt/grammar contract;
2. 118 OpenHands public-task fallbacks were incorrectly called raw first-user
   messages; and
3. pprof validation checked readability but not exact operation/sample mass.

## Round 2 — PASS

The cache now includes a deterministic hash over both system prompts, grammar
shape, seed, completion budget, prompt construction, and fixed projection. The
input contract now accurately reports 287 raw first-user messages and 118
target-blind public OpenHands recall queries without revealing source identity
to the model. Both collection-profile invocations validate input operation,
session, and mark counts; parse AgentPProf status, format, view, operation,
sample, stack, and warning fields; and perform stock pprof readback.

Focused recursive tests pass 5/5. All 68 AgentPProf tests pass. As an additional
readback control, the strict helper reproduced the retained AgentCap profile at
326 operations, 326 samples, 62 stacks, 7,410 bytes, and SHA-256
`6c086ac1f33cb5b6d85ad20a0bdb0939ae66d0c19b55a040c11f9a1e686835c9`.
The reviewer returned PASS with no remaining must-fix before preflight.

## Round 3 — PASS for v2 continuation

After real source-only preflight reopened the binary-child contract, the
reviewer independently checked the v2 implementation. A child equal to the
current operation recurses on a strictly smaller interval without pushing a
frame; a new child pushes the current frame exactly once; normalized siblings
must differ; earlier ancestors remain invalid; and continuation is recursively
reconsidered rather than converted to STOP. Leaf coverage, strict shrinkage,
stable IDs, cache identity, and mark materialization all remain intact.

Focused tests pass 7/7, including both continuation directions, no duplicate
frame, earlier-ancestor rejection, and a real stock-AgentPProf replay with
exact sample mass. The reviewer returned PASS with no remaining must-fix.
