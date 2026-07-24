# Preflight report: one complete Git session

Timestamp: 2026-07-24T00:07:00-07:00
Status: PASS for executability; no paper result

## Purpose

This preflight exercised the final path on one complete real
`git-multibranch` session:

1. source-only trace plus empty annotation;
2. fixed automatic Codex backend complete first pass;
3. deterministic AgentPProf diagnosis and pprof generation;
4. bounded issue-packet construction;
5. fresh same-model local revision backend;
6. deterministic regeneration and stock-pprof readback; and
7. actual and logical token/time accounting.

The preflight did not open the retained case answer, paper figure, old
annotation, human stage, or outcome data. Its measurements are diagnostic and
do not enter the paper.

## Input

The preflight used the first complete OpenHands/Claude Git deployment session:

- 240 ordered source nodes;
- one session and one prompt;
- 119 LLM calls and 119 tool calls;
- 119 operation-count samples;
- 2,264,980 token samples.

Every derived `path` was cleared and `annotation.json` began as `{}`.

## First-pass automatic backend

The fresh `gpt-5.6-sol` high-reasoning backend created all mandatory and
optional annotations. The first request exposed a genuine contract omission:
the fixed instruction described the tag rules but not the exact JSON shape.
The backend stopped without guessing. The schema was added to the fixed
instruction, after which the same preflight backend completed.

The resulting 22 annotations created:

- 19 optional semantic tags;
- semantic depths 3--4 over weighted leaves;
- operation depth mass `{3: 42, 4: 77}`;
- six bounded coarse-span issues.

The operation profile contained exactly 119 samples and the token profile
exactly 2,264,980. Both opened in stock `go tool pprof`; reported depth mass
equaled pprof mass.

The preflight rollout was
`019f92eb-228a-7113-abe1-a9e3a50aeeb0`. Including the stopped schema request
and follow-up, it consumed:

- 460,197 input tokens, of which 428,800 were cached;
- 7,449 output tokens;
- 3,158 reasoning-output tokens;
- 209.424 seconds wall time.

The finalized serialized source-visible payload contains 46,710
`o200k_base` input tokens and the annotation contains 2,612 logical output
tokens. Because the first request used the pre-schema instruction and then
re-read its amended form, those logical counts describe the finalized payload,
not the sum of both diagnostic requests.

## Local revision

The deterministic packet sorted all six issues by
`kind,tag,session_id,start_node_id` and contained:

- six issue records;
- 154 of 240 source nodes;
- ten relevant annotations;
- 119,690 bytes / 38,602 `o200k_base` packet tokens.

A fresh same-model backend read only that packet, the fixed instruction, and
the current annotation. It kept five broad spans after finding that each was a
single cohesive setup, repair, or diagnostic responsibility. It changed one
span:

```text
test SSH connectivity
```

became three source-grounded siblings:

```text
test SSH connectivity
inspect SSH service
test password auth
```

This added two boundaries and removed the corresponding coarse-span issue.
The remaining five warnings were explicitly considered and kept rather than
split mechanically.

Revision rollout `019f92ef-897e-7f20-ae77-a05b3a25f86a` consumed:

- 537,179 input tokens, of which 499,456 were cached;
- 4,549 output tokens;
- 1,925 reasoning-output tokens;
- 158.816 seconds wall time.

Its logical payload was 42,067 input tokens and 3,239 output tokens, including
the final annotation and decision report.

The regenerated profiles retained exactly 119 operations and 2,264,980
tokens. Annotation count rose from 22 to 24 and issue count fell from six to
five. Depth mass remained `{3: 42, 4: 77}` because the refined spans replaced
one sibling with three siblings at the same semantic depth.

## Cost finding

The preflight does **not** show that local revision is cheaper than a complete
first pass:

- logical revision input was 90.06% of the finalized first-pass logical input
  because six coarse intervals covered much of this one session;
- actual revision input tokens were 16.73% higher than the first-pass rollout,
  although its wall time was 24.17% lower;
- cached input dominated both Codex rollouts.

This is a useful negative preflight observation, not a reason to alter the
hypothesis or omit cost. The complete experiment must report cumulative actual
and logical cost over both full populations. It may support answerability while
contradicting the incremental-token prediction.

## Implementation finding

Independent code review found three issues before the full run:

1. inherited interval ends depended on annotation-key ordering;
2. near-name output silently stopped after 25 pairs; and
3. noncontiguous source sessions could reach diagnostics with an invalid
   interval.

The implementation was repaired to resolve ends recursively through declared
semantic parents, reject nested siblings and noncontiguous roots, emit all
near-name candidates using character-consistent distance, and assert
depth-mass equality at runtime. Regression tests cover all findings, all five
views, Unicode near names, and non-null issue endpoints.

## Verdict

**PASS for executability.** The exact first-pass and bounded-revision paths
work on real data, preserve pprof mass, retain source evidence, and expose
auditable actual/logical cost. The complete run may proceed after final code
review convergence. No preflight number is authorized for the paper.

