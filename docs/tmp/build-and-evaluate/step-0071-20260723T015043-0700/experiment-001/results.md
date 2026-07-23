# Experiment 001 result: latest-operation RQ3 replay

Timestamp: 2026-07-23T02:31:00-07:00
Status: VALID / COMPLETE

## Complete input

- 405 CodeTraceBench sessions;
- 17,148 source-native turns;
- 20,866 operations;
- 5,752 sparse A2 marks;
- 2,948 independent human stage occurrences;
- four agent frameworks and 251 task clusters.

The name adapter opened the accepted A2 `operation_names`, sparse marks, and
unchanged operation-count JSONL. It opened accepted source-only predictions
only after independent mark expansion to check temporal-partition equality.
Official stages, outcomes, score rows, and recurrence assignments were
unavailable to the transformation.

## Preflight finding and fixed rule

The base action--object map reduced 5,537 open-vocabulary names but made 717
adjacent, structurally distinct complete paths display-identical. Applying only
the earlier head-noun refinement was insufficient. Before the transformed
candidate was accepted by AgentPProf, the fail-closed rule was fixed:

1. use the common action--object tag;
2. for a would-be adjacent collision, retain the canonical action verb and up
   to two source-only content words;
3. if a collision remains, retain the smallest source token that distinguishes
   the colliding peers;
4. abort if a meaningful one-to-three-word distinction is impossible.

No target or score enters this rule. The final mapping uses 1,151 first-stage
refinements and eight second-stage refinements.

The current product then exposed a second necessary compatibility rule: one
display name cannot be assigned to multiple semantic IDs. The adapter therefore
derives one stable ID from each canonical display name. This intentionally
merges recurring cross-session identity; it does not alter temporal mark
occurrences.

## Structural result

| Check | Result |
|---|---:|
| Old semantic names/IDs | 5,537 |
| Canonical names/IDs | 1,434 |
| Two-word source-name mappings | 4,177 |
| Three-word source-name mappings | 1,360 |
| Initial adjacent display-path collisions | 717 |
| Remaining adjacent display-path collisions | 0 |
| Marks | 5,752 |
| Regenerated predictions | 20,866 |
| Temporal occurrence partition equals accepted A2 | yes |
| Mark sequence/start/depth skeleton digest equal | yes |
| Product one-name-per-ID check | pass |
| Stock pprof readback | pass |

The unchanged mark-skeleton SHA-256 is
`14b3a2a4d02b11029c320a98ef2ff36788f476696474127e056739a7405580d4`.
The regenerated temporal occurrence partition SHA-256 is
`1deba2ee48f8a40bcb3111217515e88b24fb6b546c6730b5c9d3efdc0c4e0fbf`,
and the adjacent-boundary vector SHA-256 is
`d595d76ad7fe11486b29d5c221401638bb713658df8315141620b68eee331213`.

“Partition preserved” refers to the temporal mark-occurrence partition.
Nonadjacent and cross-session display identities intentionally merge under the
canonical ID so pprof can aggregate recurring work.

## Standard RQ3 result

| Method | B³ P | B³ R | B³ F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Raw action | -- | -- | 0.541 | -- |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 |
| Latest automatic Agent A2 + canonical identity | 0.839025 | 0.606577 | **0.704113** | **0.393916** |

The complete operation-assignment rows excluding display paths, all adjacent
boundary rows, and all 10,000 task-cluster bootstrap draws are byte-identical
to accepted A2. Candidate-minus-recurrence B-cubed has mean delta 0.04111 and
95% interval `[0.02137, 0.06060]`.

The number is not expected to rise from name-only canonicalization: standard
B-cubed and boundary metrics score the unchanged temporal partition. The
improvement over recurrence comes from the adopted automatic Agent
segmentation; this replay proves that the current short, aggregating identity
can be used without losing that gain.

## Decision

Adopt `.agentsight/experiments/a2-canonical-v1/` as the current complete A2
profile input. It is the latest operation identity for RQ3 and RQ4. Do not
describe the 1,434 canonical IDs as 1,434 gold semantic classes; they are the
source-only display identities used for cross-session pprof aggregation.
