# Experiment 001 plan: latest-operation RQ3 replay

Timestamp: 2026-07-23T01:50:43-07:00
Outer gate: EXPERIMENT
Research question: RQ3 — How Accurate Are the Tags?

## Why this experiment is necessary

The adopted complete CodeTraceBench result uses the A2 automatic-Agent
segmentation over all 405 sessions and 20,866 operations. It predates the
current operation-name contract: reusable action-first tags containing at most
three meaningful words. Step 0070 applied that contract to all three RQ2
workloads, but not to the adopted RQ3 input. The paper must not call A2 the
latest complete automatic-backend input until both segmentation and naming are
replayed together. This is one name/partition-compatibility component of the
fixed RQ3, not a replacement wording or a complete new RQ3 experiment.

## Fixed RQ and tested hypothesis

RQ3 and the paper thesis remain unchanged. This experiment tests only:

> Applying the current deterministic action--object name canonicalization to
> the complete adopted A2 marks preserves every source occurrence, mark
> boundary, and induced partition; therefore its ordinary operation-level
> B-cubed and exact adjacent-boundary scores remain equal to the accepted A2
> result while every emitted semantic operation name satisfies the current
> one-to-three-word contract.

This is a complete CodeTrace compatibility replay, not a new benchmark,
target-conditioned tuning pass, complete new RQ3 experiment, or attempt to
change the RQ.

## Inputs

- Complete adopted A2 source operations and marks:
  `.agentsight/experiments/a2-rootfix-v1/profile-inputs/`
- Existing CodeTraceBench target operations and accepted scorer inputs used by
  A2.
- Fixed, target-blind lexical mapping in
  `script/rq2_canonical_tag_compare.py`.

Forbidden inputs to the name transformation are official stages, score rows,
outcomes, and any target labels. Those are opened only by the existing scorer
after the transformed mark file is materialized.

## Method

1. Transform only `operation_names` using the fixed action--object
   canonicalizer.
2. If two different names on adjacent complete paths would collapse to the
   same canonical path, retain the canonical action verb and the smallest
   source-only content tokens that distinguish the operations. Every output
   must still begin with a verb in the fixed action vocabulary. Abort if this
   deterministic second refinement cannot preserve every adjacent path; do
   not inspect labels or scores.
3. Preserve mark order, sequences, start IDs, path depth, source operation
   JSONL, weights, and ordering. Replace old semantic IDs with a deterministic
   ID of the canonical display name so equal cross-session identities actually
   aggregate and the product's one-display-name-per-ID contract holds.
4. Independently expand predictions from the transformed marks and unchanged
   operation JSONL using the source-only mark expansion shared with
   `assemble_agent_operation_profile.py`. Do not derive them by relabeling the
   accepted prediction rows.
5. Score the complete 405-session population with the existing CodeTraceBench
   scorer.

## Primary and secondary metrics

- Primary: ordinary, unweighted operation-level B-cubed F1.
- Secondary: exact adjacent-boundary precision, recall, and F1.
- Contract checks: byte-identical source operation inputs; identical mark
  sequence, start, order, and path depth; identical temporal occurrence
  assignments and adjacent-boundary vector; no adjacent resolved display-path
  collision; one canonical ID per canonical display name; complete mass;
  tag word lengths; and number of unique displayed operation identities. Score
  equality is not accepted as a substitute because the scorer groups the
  candidate by temporal occurrence ID.

These are the same standard structure metrics and same population as the
accepted A2 result.

## Baselines and expected interpretation

- Raw action: B-cubed F1 0.541.
- Multi-resolution recurrence: B-cubed F1 0.662740 and boundary F1 0.265571.
- Accepted pre-canonical A2: B-cubed F1 0.704113 and boundary F1 0.393916.

The scientific success criterion is equality to accepted A2 on partition and
boundary metrics plus full compliance with the current name contract. A score
increase is neither expected nor claimed because the transformation changes
names, not source occurrence membership. Any metric drift rejects the replay
and requires diagnosing a structural transformation bug.

“Partition preserved” means the temporal mark-occurrence partition only.
Canonical names intentionally merge nonadjacent and cross-session display
identities under one stable canonical operation ID so recurring work folds in
pprof; that display-name identity partition is allowed to change.

## Outputs

- Latest canonical operation mark file and name map.
- Reconstructed complete prediction/profile inputs.
- Full standard score output.
- Structural equivalence report.
- Result review and paper-facing interpretation.

## Exact execution

```bash
python3 script/canonicalize_operation_marks.py \
  --operation-marks .agentsight/experiments/a2-rootfix-v1/profile-inputs/operation-marks.json \
  --operations .agentsight/experiments/a2-rootfix-v1/profile-inputs/operations-count.jsonl \
  --reference-predictions .agentsight/experiments/a2-rootfix-v1/profile-inputs/predictions.jsonl \
  --out-dir .agentsight/experiments/a2-canonical-v1/profile-inputs

python3 script/rq3_recursive_operation_segmentation_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/a2-canonical-v1/profile-inputs/predictions.jsonl \
  --inference-summary .agentsight/experiments/a2-rootfix-v1/profile-inputs/inference-summary.json \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --out .agentsight/experiments/a2-canonical-v1/score
```

The canonicalizer is the sole A2 adapter. It accepts no target, manifest, or
score argument. The scorer runs only after the transformed marks and
independently regenerated predictions are complete.
