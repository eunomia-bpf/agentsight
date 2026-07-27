# Execution Log

Date: 2026-07-27 (America/Vancouver)

Status: **VALID / COMPLETE / Phase 2B**

## Constraints followed

- No Git command was run.
- Computation was deterministic and local.
- No model, network, random sampling, or nondeterministic inference was used.
- No file outside this `experiment-001` directory was created or modified.
- `docs/paper/`, `docs/agentpprof-paper/`, `docs/evaluation.md`,
  `docs/idea-story.md`, and `docs/user-instruction.md` were read-only.

## Required context read

Before data work, the complete experiment skill instructions and required
AgentProf context were read:

```text
/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/research-experiment-design/SKILL.md
docs/user-instruction.md
docs/idea-story.md
docs/evaluation.md
docs/tmp/build-and-evaluate/step-0091-20260727T060000-0700/experiment-001/task-spec.md
```

The fixed research question remained RQ3, “How Accurate Are the Tags?” The
paper thesis and RQs were not changed.

## Phase 1: gold investigation

Phase 1 completed before any proxy analysis.

Inspected:

- the Arrow and Parquet schemas and all selected rows of
  `.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet`;
- the exact scorer-only stage loader in
  `script/rq3_codetracebench_stage_fidelity_eval.py`;
- all 12 Step 0087 source-packet batches;
- Step 0087 canonical predictions, scorer records, and canonicalization report;
- Step 0071 and Step 0075 input/archive records;
- exhaustive `tar --zstd -tf` member listings for all 405 selected released
  archives;
- the local CodeTraceBench dataset-field documentation and output schemas.

The decisive checks established:

```text
selected trajectories: 405
operations: 20,866
human stage ranges: 2,948
stage object keys: end_step_id, stage_id, start_step_id
stage-name/type fields: none
stage_id values: one-based local ordinals 1..27
literal incorrect-step labels: incorrect, unuseful
packet gold/label keys: none
archives missing: 0
archive annotation_relpath hits: 0
archive basenames containing annotation/label/stage/gold: 0
```

The branch decision was recorded in `phase1-gold-report.md`: Phase 2A is
inapplicable, so Phase 2B must run.

## Phase 2B: deterministic proxy

The reproducible analyzer was written only after the Phase 1 decision. It was
then run from the repository root:

```text
/usr/bin/python3 docs/tmp/build-and-evaluate/step-0091-20260727T060000-0700/experiment-001/analyze_identity_proxy.py
```

Terminal summary:

```json
{"branch":"2B","canonical_ids":783,"complete_paths":2086,"leaf_ids":740,"operations":20866,"sessions":405,"status":"complete"}
```

The analyzer:

1. rechecks the full gold schema, local ordinal property, packet key inventory,
   and all 405 archive listings;
2. aligns all 20,866 pre- and post-canonical predictions by
   `(session, step_id)`;
3. checks path-depth preservation and one label per canonical ID;
4. enumerates all 783 canonical IDs, all 740 leaf IDs, and all 2,086 complete
   paths;
5. computes session, task, framework, original-name, action, and local
   stage-position contingencies without treating any as identity gold;
6. retains deterministic source-linked examples for qualitative audit;
7. writes `raw-results.json`.

No pairwise identity score or baseline was computed because the required gold
relation does not exist.

## Validation

The analyzer was run a second time. The regenerated `raw-results.json` had the
same bytes as the first run. JSON and branch-specific invariants were checked
with `jq`, including:

```text
branch = 2B
sessions = 405
operations = 20,866
human stage occurrences = 2,948
cross-run gold available = false
canonical IDs = 783
cross-session IDs = 243
cross-session leaf IDs = 227
complete paths = 2,086
```

The required `phase1-gold-report.md` and
`impossibility-and-proxy.md` exist. The Phase 2A-only
`identity-results.md` does not exist.

One initial validation wrapper containing temporary-directory cleanup was
rejected by the command runner before execution. It made no filesystem change;
the successful validation used an in-memory before/after digest comparison and
no cleanup command.

## Deliverables

```text
task-spec.md
phase1-gold-report.md
impossibility-and-proxy.md
raw-results.json
analyze_identity_proxy.py
execution-log.md
```
