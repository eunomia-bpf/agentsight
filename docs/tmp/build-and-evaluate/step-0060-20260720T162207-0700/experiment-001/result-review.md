# Result-Grounded Task Stack — Independent Result Reviews

## Review Contract

Two independent read-only reviewers explicitly applied
`research-experiment-design`. One audited the complete public ToolSandbox
completion result; the other audited the complete CodeTrace compatibility
result. Neither edited code, artifacts, project memory, or the paper.

## ToolSandbox r6 Invalidity Review

The first completed ToolSandbox candidate run reproduced exactly but failed
source isolation. The reviewer found that 1,137 child-active CLOSE calls across
869 trajectories serialized an internal `instance` containing the complete
model/persona/trial/scenario sequence ID. The r6 candidate was therefore marked
**INVALID**, its hypothesis unadjudicated, and its metrics excluded from paper
or authoritative experiment evidence.

The same review found a hidden reporting problem: the then-current summary
combined actual model `keep` decisions with synthetic root-latch skips. The r7
summary separates those populations.

## Authoritative ToolSandbox r7 Review

The reviewer independently validated all 3,551 r7 candidate caches and all
3,551 reused r6 Step 0059 caches against current inputs, request hashes, and
state linkage. Baseline predictions are exactly equal between r6 and r7, and
no duplicate baseline cache exists under the repaired output. All 14,392
candidate requests succeeded in one attempt.

Full prompt scans found zero internal `instance`, complete sequence ID,
model/persona condition, progress/key/subgoal field, or future-turn exposure.
The reviewer independently recomputed:

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| candidate | 0.594318 | 0.752004 | 0.663927 |
| Step 0059 | 0.554208 | 0.189035 | 0.281913 |
| recurrence | 0.459012 | 0.990432 | 0.627303 |
| first-turn | 0.667699 | 0.613137 | 0.639256 |

All saved 10,000-draw paired scenario bootstraps match independent draws within
`3.33e-16`. Candidate-minus-baseline intervals are:

- Step 0059: `[+0.319003,+0.445484]`;
- recurrence: `[-0.017832,+0.093897]`; and
- first-turn: `[-0.003955,+0.057665]`.

The reviewer also reconstructed the collapse: 4,893/4,907 model CLOSE calls
return `complete`; 3,546/3,551 trajectories complete at turn zero; every one of
1,153 children closes; 1,149 close in one turn; only two turns reach root plus
two children and both are false positives; 68 labels copy tool names; and seven
completion conditions are literal `done_when`.

Verdict: **VALID / INCONCLUSIVE / NOT ADOPTED / zero must-fix**. The evidence
is a mechanism boundary only and cannot authorize topology or label semantics.

## Authoritative CodeTrace r7 Review

The second reviewer independently reconstructed all 405 source archives and
confirmed 17,148 turns, 20,866 operations, 20,461 adjacent pairs, 2,948 human
stage occurrences, and 251 task clusters. It replay-validated every cache,
input, request, state link, and operation assignment.

All 17,148 OPEN prompts and 13,604 real CLOSE prompts were scanned. No complete
sequence ID, internal instance key/value, or human-stage field was exposed.
Two generic regex hits were benign source text mentioning
`frame_transform_graph`, not controller identity.

The reviewer independently recomputed ordinary B-cubed, adjacent-boundary,
and exact-span metrics for candidate, Step 0059, and recurrence and matched
every persisted number. Both 10,000-draw task-cluster bootstrap streams match
exactly:

- candidate minus recurrence B-cubed F1:
  `[-0.063739,-0.025923]`;
- candidate minus Step 0059 B-cubed F1:
  `[-0.056416,-0.023798]`.

The one malformed-I/O repair used the same prompt, system, grammar, seed, and
temperature. The first 128-token output is retained by hash and parse error;
one 256-token retry parsed successfully. It opened no oracle, excluded no row,
and did not alter any completed cache. The raw first response itself is not
retained, a minor provenance limitation that does not invalidate the run;
excluding the entire affected task preserves the same negative ordering.

Policy collapse is independently confirmed: all 11,800 child frames close;
11,791 (99.92%) close in the same turn; 13,590/13,604 model CLOSE calls return
`complete`; only four operations reach depth three; 1,678 labels are
phase-like, 1,494 commandish, and 1,410 hit the 64-character limit.

Verdict: **VALID compatibility diagnostic / CONTRADICTORY relative to both
partition baselines / zero scientific must-fix**. The fixed Qwen2.5-3B policy
is not adopted. Flat CodeTrace stages cannot reject the task-stack abstraction,
RQ3, thesis, or paper story.

## Combined Disposition

The authoritative r7 experiment is valid and the registered constructor is not
adopted. OPEN/CLOSE makes completion mechanically available but the fixed 3B
policy degenerates to near-always-complete, produces mostly one-turn children,
and oversegments CodeTrace. Recurrence remains current. No result enters the
positive paper and no paper contract changes.
