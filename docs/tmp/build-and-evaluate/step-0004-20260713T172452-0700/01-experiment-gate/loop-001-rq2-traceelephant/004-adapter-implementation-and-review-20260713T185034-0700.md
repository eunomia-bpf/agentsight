# TraceElephant Adapter Implementation And Independent Review

**Completed:** 2026-07-13T18:50:34-07:00
**Phase / step / gate:** BUILD_AND_EVALUATE / 0004 / EXPERIMENT
**Loop:** loop-001-rq2-traceelephant
**Parent:** approved Plan version 2 and three-round plan review
**Status:** implementation review converged at PASS; real preflight is next

## Question And Entry

This node asks whether the approved fixed-RQ2 TraceElephant plan has one thin,
executable adapter that preserves the plan's source/reference/scorer boundary,
uses the real AgentProf binary for both primary conditions, implements every
predeclared metric and control exactly, and is safe to contact the actual model
on the one-trace real preflight. It does not ask for an RQ answer and performs
no model inference or scorer-label read.

Before implementation the root reread `docs/user-instruction.md`, the complete
approved plan, all plan-review findings, the official TraceElephant visible
schema and response-only prompt implementation, the AgentProf CLI/source, and
the reviewed HINTBench adapter patterns. The paper, idea story, skills, and
`docs/agentpprof-paper` remained outside this node.

## Implemented Path

The new thin adapter is
[`script/traceelephant_profile_localization_eval.py`](../../../../../../script/traceelephant_profile_localization_eval.py).
It implements:

1. an isolator process that enumerates the five official source cells and
   writes a visible metadata/path manifest without any `mistake_*` field;
2. the official released All-at-Once prompt builder called directly in uniform
   `response_only` mode, with reference answer/test status confined to this
   shared localizer;
3. trace-local batches of at most 20 steps for the fixed role/intent/status
   tagger, with no reference outcome or failure annotation in its requests;
4. actual llama.cpp `/apply-template` plus `/tokenize` checks for every exact
   request before inference, with no adaptive truncation;
5. byte-identical three-attempt terminal model records and reusable resume
   cache, with preflight requiring real successful engagement and FULL retaining
   the approved explicit no-hit/fallback outcomes;
6. exact source-native raw-action extraction and injective UTF-8 hex field
   encoding;
7. count and shifted operation JSONL fed to AgentProf 0.2.37 for both the
   six-field proposed stack and three-field headline raw stack, plus exact
   emitted-leaf/prefix reconstruction;
8. independent-step, session, source-native, flat, exact-reconstruction,
   width-only, scorer-only oracle, and 200 deterministic matched semantic
   permutations;
9. complete tied-tier atomic-step work at macro recall, exact localizer
   accuracy, cell-stratified paired trace bootstrap with duplicate
   multiplicities, nearest-rank intervals, and the exhaustive verdict; and
10. a separate scorer subprocess that alone reads `mistake_agent`,
    `mistake_step`, and `mistake_reason`, after every target-independent builder
    artifact is terminal.

The adapter archives the completed preflight's non-model artifacts before FULL
while keeping identical terminal model records available for exact resume. It
does not modify AgentProf core code or the official source clone.

## Source Reality Found During Implementation

The source projection independently reproduced the approved population exactly:

| Cell | Traces | Steps |
|---|---:|---:|
| Captain-Agent / AssistantBench | 12 | 187 |
| Captain-Agent / GAIA | 73 | 1,559 |
| Magentic-One / AssistantBench | 17 | 603 |
| Magentic-One / GAIA | 74 | 2,060 |
| SWE-Agent / SWE-Bench | 44 | 1,551 |
| **Total** | **220** | **5,960** |

Released `system_name` values are lower-case while the approved paper-facing
system identities are Captain-Agent, Magentic-One, and SWE-Agent; the adapter
checks normalized equality and records both. There are 174 distinct task IDs
and 46 task IDs repeated across systems/cells, so task ID alone is not a safe
operation key. The adapter uses the source-cell plus official trace-directory
identity, then exact step ID. This is a source-key repair only; it changes no
RQ, population, comparison, metric, or hypothesis.

## Non-Inference Tests

All checks below completed without model inference or scorer access:

- Python compilation and `git diff --check` passed.
- Visible source projection returned exactly 220 traces and 5,960 ordered
  steps; no scorer key was written.
- The selected preflight trace is the lexical first
  Captain-Agent/AssistantBench trace, has nine ordered steps, and produces one
  trace-local tag batch.
- Request inspection confirmed the localizer contains no failure annotation
  and the tag request contains neither reference outcome nor failure
  annotation.
- Synthetic raw-action cases passed editor subtype, repeated multi-tool, and
  no-tool response behavior.
- Synthetic real AgentProf count/shifted paths matched independent leaves,
  prefixes, hits, scores, and sample conservation; explicit zero-hit Wilson
  returned `+0.0` for different group sizes.
- The official nine-step visible preflight trace, supplied only fixed fallback
  tags and a no-hit signal for engineering purposes, completed both real
  primary binary paths, every non-oracle control, and all 200 matched
  permutation invocations. This was a path test, not a real preflight or RQ
  result.
- Supported, contradicted, inconclusive, and inconsistent point/interval
  branches passed direct contract tests; inconsistent branches produce
  execution `INVALID` with no scientific verdict.
- Array/object enum values now produce retryable tag schema errors rather than
  uncaught exceptions; the valid string-enum case still passes.

## Serial Independent Implementation Reviews

Every reviewer explicitly used `research-experiment-design`, reread current
user instructions and the complete approved plan, inspected the entire adapter,
and was prohibited from model inference, scorer execution, target values, file
edits, paper edits, or experiment expansion.

### Review 1 — MUST-FIX

The first reviewer found two blockers:

1. a failed localizer or all-unknown tag fallback could still let a one-trace
   preflight be reported `VALID`; and
2. point estimate and wholly one-sided bootstrap interval sign disagreement did
   not activate the plan's `INVALID` rule.

The root required every preflight localizer/tag record to have status
`success`, required the localizer step to be in range, retained fallbacks only
for FULL, and made numerical sign inconsistency produce `INVALID` with a null
scientific verdict. Direct tests passed.

### Review 2 — MUST-FIX

The fresh reviewer confirmed both earlier repairs, then reproduced an uncaught
`TypeError` when otherwise valid JSON gave an array/object for a tag enum. The
root added an explicit string-type check that raises the existing retryable
schema error before enum membership. Malformed-type and valid-enum tests passed.

### Review 3 — PASS

The third fresh reviewer reread the repaired complete implementation and
returned `PASS` with no material defect or optional expansion. The serial
implementation loop therefore converged.

## Scientific Impact And Decision

This node creates no scientific evidence and answers no RQ. It establishes that
the approved experiment can now contact a real source, model, profiler, and
label-isolated scorer without the known implementation paths fabricating
engagement or silently changing the verdict. Thesis, story, positive RQ2
hypothesis, four fixed RQs, population, headline baseline, controls, and result
criterion are unchanged.

## Completion And Next Action

Implementation review is complete. Run exactly the approved one-trace real
preflight with the actual Qwen server, official response-only builder, fixed
tagger, real AgentProf paths, all controls, and scorer subprocess. Review its
raw prompts, tokenization, terminal outputs, operation fields, profiles,
control invariants, and metric mapping. A path failure repairs only the runner
or parser and repeats preflight; after scorer observation no scientific field,
prompt, score, metric, or threshold may change.
