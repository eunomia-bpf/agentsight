# Step 0087 direct-hierarchy control audit

## Decision

Step 0087 already is the reviewer-requested direct complete-hierarchy control.
Reuse its complete population and score rows; do not rerun it under a second
name.

## Frozen mechanism

The frozen instruction in
`step-0087-20260726T023000-0700/experiment-001/direct_annotation/annotate.py`
requires the backend to:

- read the complete already-finished trajectory;
- directly write sparse multi-level complete-path marks in one pass;
- avoid a STOP/SPLIT protocol and recursive binary questions;
- emit the complete active path at each responsibility transition;
- use variable depth without a fixed cap.

There is one isolated Codex request per trajectory. The response contains the
complete mark list for that trajectory. The harness performs schema/contract
validation and, on a format error, makes at most one ordinary complete-response
retry. It does not issue semantic refinement requests, maintain an external
STOP/SPLIT controller, recursively subdivide intervals, or revise accepted
marks after inspecting an aggregate. The one exceptional third request for
ordinal 53 repaired an exact session-ID format error; it did not use a score,
stage, aggregate diagnosis, or iterative semantic refinement.

The post-request pipeline only packages accepted marks, applies deterministic
root-prefix repair and the frozen action-object canonicalizer, materializes
pprof profiles, and invokes the frozen RQ3 scorer. The canonicalization report
states that the temporal partition is unchanged.

## Model and request configuration

- CLI: `codex-cli 0.145.0`.
- Model: `gpt-5.6-sol`.
- Command isolation: fresh temporary working directory, `--sandbox read-only`,
  `--ephemeral`, `--skip-git-repo-check`, and `--ignore-user-config`.
- Decoding/reasoning: no decoding or reasoning override; model defaults under
  ignored user configuration.
- Request budget: one complete source packet per request and one complete
  response object.
- Worker pattern: up to four isolated trajectory requests concurrently.
- Timeout: 1,200 seconds per request.
- Ordinary retry policy: one format-only complete-response retry.

All retained run records identify `gpt-5.6-sol` and isolated
one-trajectory calls. The terminal population contains 396 one-call
trajectories, eight two-call trajectories, and one trajectory with the
explicitly documented third format-repair call.

## Input and leakage audit

The exact input population is
`.agentsight/experiments/rq4-end-to-end-cost-v1/full/source-packets-rep-1/`:
405 unique sessions, 17,148 turns, and 20,866 operations. Each session exposes
only archive/source provenance, framework, task text/source, session identity,
counts, and ordered turns. Each turn exposes its intent, planned action,
progress text, visible result, operation IDs, turn identity/order, and source
references.

A recursive key inventory contains no `stage`, `outcome`, `score`, `reward`,
`target`, or `label` field. Step 0087's independent review additionally checked
that none of the 2,948 exact official stage IDs occurs in packet text. The
backend's 415 raw event files contain no command execution, file change, MCP,
or web-search event. Official stages are loaded only after annotations and
canonicalization are fixed.

## Complete reusable result

Step 0087 covers all 405 trajectories, 20,866 operation rows, 20,461 adjacent
pairs, 2,948 official stages, and 251 task clusters. Its reusable direct
hierarchy result is:

| Metric | Precision | Recall | F1 |
|---|---:|---:|---:|
| Operation-level B-cubed | 0.793409 | 0.735836 | 0.763539 |
| Exact adjacent boundary | 0.389147 | 0.626032 | 0.479952 |

It emits 4,496 groups/marks. Raw complete-path depths are 1 for 3 marks, 2 for
2,873, 3 for 1,588, and 4 for 32; the deterministic root repair supplies the
mandatory root where needed. The frozen per-operation and per-pair rows are
`score/operation-score-rows.jsonl` and `score/pair-score-rows.jsonl`.

The complete run used 415 Codex calls, 12,050,384 input tokens, 6,008,320
cached input tokens, 231,886 output tokens, 116,909 reasoning-output tokens,
8,689.405 seconds of summed request time, 2,215.858 seconds of union active
request time, and 11.516 seconds for the deterministic downstream pipeline.

## Consequence for this experiment

Control 2 is genuine but not new: it is exactly the adopted Step 0087
condition. The only fresh model arm is the same-model flat partition. The
primary matched comparison is Step 0087 direct hierarchy minus the fresh flat
arm. No “recursive/refined minus direct” effect will be reported because the
audited adopted condition contains no distinct recursive or iterative
refinement arm.
