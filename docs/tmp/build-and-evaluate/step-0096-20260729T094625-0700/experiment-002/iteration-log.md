# Iteration Log

## Prompt-policy pilot

The 45-word profile-derived retry policy passed one real preflight but did not
generalize over the eight-scenario pilot:

- official similarity: 0.652 after vs 0.685 before;
- exact success: 0/8 after vs 1/8 before;
- agent tokens: 35,038 after vs 29,124 before (1.203×).

This development result is retained and is not paper evidence.

## Profiling the real BEFORE runs

AgentPProf converted the eight BEFORE traces into the single standard profile
`before-profile.pb.gz`. Stock pprof readback shows:

- 5/21 tool operations (23.8%) have `call_id:invalid` and
  `result:invalid-call-id`;
- 4/21 (19.0%) are exact repeats;
- all four exact repeats follow invalid-call-ID failures and then recover.

An independent agent given only this pprof concluded that prohibiting those
retries would be the wrong repair. It proposed fixing the compatibility layer's
tool-call ID before official ToolSandbox role parsing. The minimal v2 repair
retains valid IDs and replaces only invalid ones with a deterministic, unique,
Python-identifier-compatible opaque ID. Tool name, arguments, order, scenario
state, and official evaluator remain unchanged.

This implementation was tested on the same eight development scenarios before
any confirmation scenario was executed.

## Response-ID normalization pilot

The first implementation replaced invalid IDs in the returned model response.
Its eight-pair pilot was complete but did not balance exposure to the target
fault:

- BEFORE drew 19/19 valid raw IDs;
- ID-FIX drew 5/19 invalid raw IDs and normalized all five;
- official similarity was 0.7412 ID-FIX versus 0.7418 BEFORE;
- agent tokens were 42,103 versus 27,798 (1.515×).

The token increase does not support a utility claim. A trace audit found that
11,282 of the 14,305 extra tokens came from one scenario where no ID was
normalized and the simulated user continued into a different request. Across
the profiling run, this BEFORE run, and this ID-FIX run, 10/59 raw IDs were
invalid (16.95%), consistent with an unseeded alphanumeric allocator whose
leading digit is not a Python identifier. Thus the eight-run comparison is
also underpowered and imbalanced for the target stochastic fault. Two
independent reviewers returned REVISE and prohibited using this result as
paper evidence.

## Converter-level repair

The final implementation fixes the actual interface boundary. It retains the
opaque protocol ID in the assistant call and matching tool response while
deriving a separate safe internal Python variable for ToolSandbox execution.
It records raw-invalid IDs in both arms without using them for selection.

Because the server's ID allocator is not controlled by the request seed, the
final development pilot is fixed at three new seed blocks over all eight
development scenarios (24 pairs). It does not reuse the normalization pilot,
stop when ID counts balance, or select affected cells. If it passes the
existing outcome-or-efficient-noninferiority gate, confirmation applies the
unchanged implementation and three-repetition analysis to all 23 untouched
scenarios.

The converter preflight completed on one excluded scenario:

- BEFORE: one raw-invalid ID, one syntax failure, 4,606 agent tokens;
- CONVERTER-FIX: zero raw-invalid IDs in that draw, zero syntax failure, 3,708
  agent tokens;
- official similarity: 0.9165 in both arms.

This checks real execution and telemetry only; it is not outcome evidence.

The fixed five-pair mechanism preflight then exercised both sides of the
stochastic fault:

- all 10 cells completed with official evaluations;
- BEFORE generated three raw-invalid IDs and incurred three Python syntax
  failures;
- CONVERTER-FIX generated two raw-invalid IDs and incurred zero such failures;
- all model requests reported zero assistant/tool protocol-ID mismatches;
- official similarity changed by −0.0149, within the −0.05 non-inferiority
  margin, while the aggregate agent-token ratio was 0.7569.

All five pairs and all tokens are retained. These runs validate mechanism
engagement and the measurement path but remain excluded from outcome evidence.

## Final converter pilot

The fixed three-block pilot completed all 24 pairs over all eight development
scenarios:

- BEFORE generated 15 raw-invalid IDs and incurred 15 Python syntax
  failures;
- CONVERTER-FIX generated 9 raw-invalid IDs and incurred zero such failures;
- both arms recorded zero assistant/tool protocol-history ID mismatches;
- agent tokens fell from 105,952 to 88,047, a ratio of 0.8310 (16.90%
  lower); the scenario-cluster bootstrap 95% interval was
  `[0.7589, 0.9327]`;
- official similarity was 0.74718 BEFORE and 0.74748 CONVERTER-FIX; the
  after-minus-before interval was `[-0.00133, 0.00241]`;
- model calls fell from 110 to 96, tool calls from 73 to 57, and turns from
  202 to 174.

All 24 pairs are included regardless of fault exposure. The pilot passes the
predeclared efficiency-with-noninferior-similarity branch. It is development
evidence only; a fresh independent reviewer decides whether the unchanged
method may enter the 23-scenario, three-repetition confirmation.

The separate exact-state replay includes all 21 profiled operations. It
reproduces 21/21 original BEFORE responses and post-states, eliminates all five
Python syntax failures, preserves all 21 original protocol IDs, and leaves
all 16 valid-ID control responses and post-states unchanged. This is mechanism
evidence only and does not itself support token or task-outcome claims.

## Converter confirmation

After an independent reviewer passed the pilot, the unchanged converter and
analysis ran all 69 fixed pairs: 23 previously unexecuted scenarios, three
repetitions per scenario, and 138 successful official evaluations.

- BEFORE generated 28 raw-invalid IDs and incurred 28 Python syntax failures;
- CONVERTER-FIX generated 19 raw-invalid IDs and incurred zero syntax failures;
- both arms recorded zero protocol-history ID mismatches;
- agent tokens fell from 211,222 to 171,139, a ratio of 0.8102 (18.98%
  lower); the scenario-cluster bootstrap 95% interval was
  `[0.7336, 0.9212]`;
- official similarity increased in point estimate from 0.83105 to 0.85721;
  the after-minus-before interval was `[-0.02221, 0.07629]`;
- exact successes were 8 versus 9;
- model calls fell from 255 to 227, tool calls from 159 to 137, and turns from
  457 to 401.

The confirmation passes the predeclared efficiency-with-noninferior-similarity
branch. The similarity and exact-success intervals cross zero, so this is not
an outcome-improvement claim. It supports lower agent-side model token
volume and fewer calls/turns without an official-similarity loss larger than
the fixed 0.05 margin. Final paper eligibility remains subject to an
independent confirmation result review.

The independent final review returned PASS after reconstructing all 138
episode metrics and rerunning a 100,000-draw scenario-cluster bootstrap with a
different random seed. It admits the bounded agent-token/call efficiency claim
with official-similarity non-inferiority and rejects claims about significant
success improvement, human developer speed, dollar cost, wall time, unique
necessity, or cross-system generality.
