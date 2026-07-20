# Full Run

## Verdict

**VALID / COMPLETE / CONSTRUCT EFFECT SUPPORTED / ONLINE CONSTRUCTOR NOT
ADOPTED.** The exact complete visible task-label path is materially more
faithful to session-local CodeTrace stages than Step 0054's hidden frame-
instance partition. It remains decisively below multi-resolution recurrence,
so the fixed Qwen2.5-3B online constructor is not adopted.

This is a retrospective construct-correction audit. The result direction was
inspected before the formal plan, disclosed in that plan, and is not presented
as preregistered discovery.

## Command

```bash
python3 script/rq3_stateful_visible_path_identity_eval.py full \
  --predictions .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/predictions.jsonl \
  --step0054-score-rows .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/operation-score-rows.jsonl \
  --step0054-summary .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/summary.json \
  --out .agentsight/experiments/rq3-stateful-visible-path-identity-v1/full
```

The scorer made no model call and did not replay or alter a transition.

## Complete Population And Validity

- 405 trajectories, 251 task clusters, 20,866 operations, 20,461 adjacent
  pairs, and 2,948 verified session-local stage occurrences;
- all MiniSWE, SWE-agent, OpenHands, and Terminus2 operations retained;
- prediction and Step 0054 score-row key sets match exactly;
- every complete visible path is nonempty, ordered, depth-consistent, and ends
  in the recorded active leaf label;
- hidden instance and recurrence metrics reproduce Step 0054 within `1e-12`;
- session prefixes only namespace the stage-occurrence score and never become a
  semantic frame; and
- no fuzzy matching, normalization, embedding, phase deletion, pruning, depth
  cap, system-field key, score threshold, or model call occurs.

## Standard Session-Local Results

| Identity/method | Groups | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|---:|
| hidden active-frame instance | 13,041 | 0.931958 | 0.333171 | 0.490861 | 0.261643 | 0.032768 |
| **exact complete visible label path** | **9,585** | **0.822397** | **0.432771** | **0.567111** | **0.262350** | **0.034995** |
| adjacent-identical-label contraction (secondary) | 6,290 | 0.741428 | 0.550438 | 0.631815 | 0.264670 | 0.047913 |
| multi-resolution recurrence | 6,018 | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

Exact visible-path identity recovers 0.076250 B-cubed F1 over hidden instance
at the full-population point estimate. Across 10,000 paired task-cluster
resamples, the mean effect is +0.076239 with 95% interval
[+0.060647,+0.092940]; every resample is positive. The construct-correction
hypothesis is supported.

Against recurrence, exact visible path has mean paired effect -0.096019 with
95% interval [-0.123890,-0.068765]; no resample is positive. The online
constructor adoption condition fails decisively.

Adjacent-identical-label contraction is not standard flamegraph folding and
does not replace the primary result. Its 0.631815 point estimate shows that
directly nested repeated task labels account for part of the remaining gap
under this scorer, but the fixed output remains below recurrence even under
this secondary normalization.

## Framework Heterogeneity

| Framework | Hidden instance | Exact visible path | Recurrence | Visible minus recurrence |
|---|---:|---:|---:|---:|
| OpenHands | 0.377918 | 0.469636 | 0.676295 | -0.206659 |
| SWE-agent | 0.271718 | 0.550365 | 0.708893 | -0.158528 |
| Terminus2 | 0.627902 | 0.654087 | 0.605471 | +0.048615 |
| MiniSWE-agent | 0.556650 | 0.615879 | 0.691523 | -0.075644 |

Terminus2 is again positive. Its native turns often contain multiple retained
operations, whereas the other layouts usually expose one retained operation
per turn. This is diagnostic evidence that task persistence is easier when a
source turn already groups atomic operations; it is not grounds for selective
adoption.

## Global Folding Behavior

Without the session scoring namespace, the fixed outputs contain 9,109 exact
visible paths. Of those, 183 occur in at least two sessions, and one path occurs
in as many as 31 sessions. Adjacent contraction gives 5,890 paths, 132 recurring
across sessions, again with a maximum of 31 sessions.

These are profile-fold behavior statistics only. CodeTrace stage occurrence IDs
cannot determine whether identical generated paths in different sessions are
semantically equivalent, so no cross-run accuracy claim is made.

## Interpretation And Next Decision

The experiment establishes a representation fact and an accuracy result:

1. the user-visible task-semantic flamegraph identity is the exact ordered label
   path, not a hidden controller occurrence ID; and
2. scoring that construct materially improves stage fidelity but does not make
   the current online Qwen transition policy competitive with recurrence.

The result does not validate label meaning, ancestors, variable depth, global
semantic equivalence, root canonicalization, or the lower
`phase/strategy -> action -> object -> result` suffix. It does not change the
thesis, RQ3, its positive hypothesis, or the target task-semantic hierarchy.

Per the Step 0054 outer audit, the only eligible next experiment in this online
branch is a causal exact-same-leaf identity invariant: apply any `push` or
`replace` whose proposed label exactly equals the active visible leaf as
identity-preserving `stay`, while leaving every other choice fixed. Because that
changes future visible stacks, it requires a complete causal replay rather than
post-hoc contraction. If it remains below recurrence or preserves the phase/no-
pop/depth pathology, this online Qwen2.5-3B branch closes.

## Raw Artifacts

- preflight:
  `.agentsight/experiments/rq3-stateful-visible-path-identity-v1/preflight/`
- full score rows, two paired bootstraps, summary, and report:
  `.agentsight/experiments/rq3-stateful-visible-path-identity-v1/full/`
