# Independent Experiment-Plan Review

Experiment: H6 / RQ1 objective continuation utility
Reviewer: `/root/objective_plan_review` (fresh, read-only subagent)
Review round: 1 of at most 3
Verdict: **BLOCK**
Disposition: accepted; no model or benchmark call is admitted before repair and
follow-up review.

## Preflight blockers

1. The proposed command was not executable through the current Rust research
   path. The existing implementation supports only Raw/Trajectory, emits the
   superseded pathology schema, exposes `goal_diff` rather than `session_diff`,
   hard-locks different budgets, and accepts only the old two-scope capture.
2. Exact `session_diff` had no exact source because the official runner does
   not retain a workspace snapshot after every round. Raw/Trajectory
   information parity therefore was not yet demonstrated field by field.
3. Four host fork paths could leak condition identity through the rendered
   prompt, argv, environment, or filesystem metadata. Content hashes alone did
   not cover all Agent-visible state.
4. Hiding the local benchmark checkout with Bubblewrap did not stop a worker
   tool from downloading the public oracle or ground truth. The evidence store
   also needed an explicit allowlist that excludes credentials and benchmark
   internals.

## Full-run interpretation blockers

5. Positive, contradictory, and inconclusive verdicts were based too heavily
   on point estimates; uncertainty did not control the verdict.
6. The no-intervention ceiling gate was too weak to establish headroom across
   the fixed six-task workload.
7. Five prefixes for each of six hand-selected tasks do not create thirty
   independent task samples. The admissible estimand is the equal-weight mean
   operational effect on these six fixed tasks, not a benchmark population or
   cross-domain effect.
8. Codex exposes no decoding seed. The experiment is checkpoint-matched, not
   paired decoding, and an infrastructure failure must rerun the whole
   four-condition block within the same execution wave.
9. The official process LLM rubric must not merely be ignored after execution;
   the driver must never call it and must prove zero rubric/provider requests.

## Reviewer-accepted properties

- The RQ and primary Trajectory-minus-Raw estimand directly test realized
  continuation utility.
- No-intervention, generic current-state reflection, and Full Raw jointly
  control natural continuation, another inference pass, and same-source
  historical access. Human or Agent semantic gold is unnecessary.
- The selected hooks permit faithful pause-after-round and resume-before-final
  execution at the pinned benchmark revision.
- The local fixed worker, supervisor, Bubblewrap/user namespace, and model
  assets are sufficient once the isolation contract is repaired.

## Required repair before round 2

The plan must define an executable adapter contract, immutable post-round
snapshots, stable worker-visible paths and complete manifests, a no-egress tool
sandbox with still-functional trusted model transport, an explicit evidence
allowlist, direct executable-oracle-only grading, a six-task no-op headroom
gate, clustered fixed-task inference, uncertainty-controlled verdicts, and
whole-block failure recovery.

## Round 2

Reviewer: `/root/objective_plan_review` (same independent read-only reviewer)
Verdict: **PASS**

The reviewer reread the complete repaired plan and found no remaining
plan-level blocker. In particular, every Round 1 issue is now an explicit,
falsifiable implementation contract or P0 completion rule. Implementation may
begin. A real model/benchmark P0 remains prohibited until the complete
`--prepare-only` contract passes.
