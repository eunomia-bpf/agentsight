# RQ2 HINTBench REAL PREFLIGHT Attempts

## Scope

This report records execution and repair history for the approved REAL
PREFLIGHT.  It does not alter the fixed RQ2, tested hypothesis, official
HINTBench populations, localizer prompt, model, AgentProf construction,
baselines, metrics, or positive-evidence threshold.  Failed attempts are
development evidence only and are not paper results.

## Attempt 1 — 2026-07-13

### Intended execution

The preflight was launched against the two official HINTBench sources, the
local Qwen3.6-27B Q4_K_M model served at `http://127.0.0.1:8012/v1`, and the
real `agentpprof 0.2.37` binary.  It was required to tokenize all 616 exact
requests and then run inference, profile construction, and every downstream
path for the fixed first risky and first safe validation trajectories.

### Completed work

- Both official sources were downloaded and population-checked.
- The official evaluator was downloaded and recorded.
- The model endpoint and server properties both reported a 32,768-token
  context window.
- All 616 exact chat-template prompts were applied and tokenized.
- Every prompt fit the declared context budget.  The longest was `test:5` at
  8,497 prompt tokens, or 9,521 tokens including the 1,024-token output
  allowance.
- All 15,927 target-blind operations passed the UTF-8 hex round-trip check.

### Failure boundary

No terminal localizer output, profile, metric, or scientific result was
produced.  The first fixed validation request (`validation:20`) received HTTP
400 on each of three identical attempts.  The server response was:

```text
Failed to initialize samplers: std::exception
```

The failure occurred before model inference.  Direct compatibility probes
showed that unconstrained chat, plain `json_object`, and explicit GBNF grammar
all initialize successfully, while both the OpenAI `json_schema` envelope and
llama.cpp's `json_object` plus schema object fail during sampler
initialization.  Therefore the defect is the running server's schema compiler,
not the prompt, population, context length, model execution, or scientific
design.

### Minimal repair

The canonical `RESPONSE_SCHEMA` remains unchanged.  Its exact required keys,
two verdict values, eleven risk-name values, integer-array boundary, empty
array allowance, and no-additional-property boundary are now expressed as an
explicit llama.cpp GBNF grammar in the request.  The grammar permits either
JSON object field order, so it does not introduce an ordering restriction that
the schema did not have.  The scientific prompt and terminal parser are
unchanged.

HTTP errors now retain the server response body in the transport-failure log,
so a repeated compatibility failure is auditable without an out-of-band
diagnostic request.

### Local verification after repair

- Python compilation: PASS.
- Ten adapter unit tests: PASS.
- A live constrained-decoding probe using the same grammar mechanism: HTTP
  200 with structurally valid JSON.
- No inference result from the failed attempt was cached or scored.

### Status

The implementation repair passed independent review and Attempt 2 may rerun
the same approved REAL PREFLIGHT.

## Independent Repair Review — 2026-07-13

**Skill:** `research-experiment-design`

**Verdict:** PASS

The independent reviewer verified that the approved plan now names the
canonical schema as the normative semantics and GBNF only as the current
llama.cpp constraint transport.  Required keys, both field orders at both
object levels, both verdict values, all eleven risk names, empty arrays,
integer arrays, and the no-extra-field boundary were checked explicitly.
Twenty-two valid enum/order cases were accepted and seven invalid cases were
rejected.  An exact live payload reproduced HTTP 400 through the native schema
compiler and HTTP 200 through GBNF; the resulting output was `ok_safe` under
the official parser.  HTTP-body retention and top-level experiment-error
handling were also verified.  All ten adapter tests passed.

No paper, story, RQ, tested hypothesis, model, prompt, population, AgentProf
construction, baseline, metric, or evidence threshold changed.  Attempt 2 is
authorized.

## Attempt 2 — 2026-07-13

### Execution result

**Status:** VALID

The same approved command completed in 26.93 seconds.  All 616 exact prompts
were templated and tokenized again; all fit the 32,768-token context, with
`test:5` remaining the longest at 8,497 prompt tokens and 9,521 tokens with the
output allowance.  The model returned terminal outputs for the fixed first
risky and first safe validation records: one parsed `ok_unsafe` and one parsed
`ok_safe`, with no out-of-range predicted step.

The two trajectories contained 60 operations.  All 24 field-order profile
paths completed through the real `agentpprof 0.2.37` binary.  Count/shifted
recovery, leaf/prefix/global conservation, the independent flat reconstruction,
the four main baselines, the width-only control, mappable-target sensitivity,
and report generation all completed.  The flat reconstruction was exactly
identical to the AgentProf path.

### Interpretation boundary

Preflight used the lexically first field order only to exercise downstream
paths.  `scientific_selection=false`, no positive threshold was evaluated, and
the emitted verdict is `PREFLIGHT_ONLY`.  The two-record point estimates are
not evidence for or against the tested hypothesis and must not enter the paper.
They neither select a scientific configuration nor alter RQ2, the hypothesis,
or the planned FULL population.

### Status

The complete artifacts are under `results/preflight/`.  Independent result
review passed and FULL execution is authorized.

## Independent Attempt 2 Result Review — 2026-07-13

**Skill:** `research-experiment-design`

**Verdict:** PASS → FULL

The reviewer independently matched all 616 current request bodies and hashes
to the adapter and tokenization artifacts, confirmed all prompts fit, and
matched the two terminal usage counts exactly at 4,219 and 2,601 tokens.  The
selected records were the fixed first risky `validation:20` and first safe
`validation:0`; gold top-level fields were absent from their prompts.

All 24 real AgentProf candidates contained the expected 60 count units, 61
shifted units, and one recovered localizer hit.  Leaf, prefix, and global
conservation and flat identity were exact for every candidate.  The reviewer
independently recomputed all seven method/control point paths from the emitted
artifacts with no mismatch.  Attempt 1 failures were neither cached nor scored.

The result remains `PREFLIGHT_ONLY`, uses no scientific selection, and evaluates
no positive threshold.  FULL is authorized for all 80 validation records, all
536 test records, and 10,000 paired trajectory-cluster bootstrap replicates.
