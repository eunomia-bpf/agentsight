# Phase 1: CodeTraceBench Gold Availability

## Decision

**CodeTraceBench's released gold does not define cross-trajectory stage
identity.** The 2,948 human stages used by Step 0087 are per-trajectory
contiguous ranges. There is no released `stage_name`, `stage_type`, or
equivalent semantic label with which to decide whether stages from two
different trajectories represent the same operation.

Therefore Phase 2A is inapplicable. This experiment proceeds to Phase 2B.

## Exact population and inputs inspected

The investigation follows the exact Step 0087 data path:

- 405 sessions selected by
  `step-0087-20260726T023000-0700/experiment-001/canonical/predictions.jsonl`;
- 20,866 operations in
  `docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl`;
- the scorer-only release manifest
  `.agentsight/experiments/codetracebench-rq2/manifests/verified.parquet`;
- all 12 source-packet batches under
  `.agentsight/experiments/rq4-end-to-end-cost-v1/full/source-packets-rep-1/`;
- all 405 released `.tar.zst` archives named by the selected manifest rows;
- the Step 0087 scorer implementation
  `script/rq3_codetracebench_stage_fidelity_eval.py`;
- the Step 0071 and Step 0075 records that identify the same manifest,
  normalized operations, packet exporter, and raw-archive root.

The selected rows contain exactly 405 trajectories, 20,866 steps, and 2,948
stage ranges.

## Released stage gold

The Arrow/Parquet type of `stages` is:

```text
list<struct<
  end_step_id: int64,
  stage_id: int64,
  start_step_id: int64
>>
```

These are the only three fields in every selected `stages[]` object.

| Field | Meaning in the release | Vocabulary on 405 trajectories | Cross-trajectory recurrence |
|---|---|---:|---|
| `stages[].stage_id` | One-based stage ordinal local to a trajectory | 27 integers (`1` through `27`) | All 27 integer values recur where trajectories are long enough, but only as positions |
| `stages[].start_step_id` | Inclusive local start step | Integer coordinate | Not an identity label |
| `stages[].end_step_id` | Inclusive local end step | Integer coordinate | Not an identity label |

For every selected trajectory, `stage_id` is exactly
`1, 2, ..., stage_count`. Every range begins immediately after the preceding
range and the ranges cover the full trajectory. The apparent recurrence of
numeric IDs is therefore ordinal, not semantic: `stage_id = 1` means “the
first annotated segment of this trajectory,” not a shared type such as
“reproduce” or “localize.”

The selected-stage ordinal counts are:

```text
1:405, 2:405, 3:405, 4:388, 5:342, 6:266, 7:198, 8:138, 9:98,
10:74, 11:47, 12:37, 13:31, 14:26, 15:22, 16:15, 17:11,
18:10, 19:5, 20:5, 21:5, 22:5, 23:4, 24:3, 25:1, 26:1, 27:1
```

The Step 0087 scorer makes the scope explicit by converting each ordinal to
`<session>:stage-<ordinal>`. Thus equal ordinals in different trajectories
are never treated as gold-equal identities.

## Other released annotation labels

The manifest contains one separate error annotation:

```text
incorrect_stages[].stage_id
incorrect_stages[].incorrect_step_ids
incorrect_stages[].unuseful_step_ids
incorrect_stages[].steps[].step_id
incorrect_stages[].steps[].labels
incorrect_stages[].steps[].action_ref
incorrect_stages[].steps[].observation_ref
```

`incorrect_stages[].stage_id` only references the same local ordinal.
`steps[].labels` has exactly two literal values:

| Label | Annotated step records | Trajectories containing it | Meaning |
|---|---:|---:|---|
| `incorrect` | 833 | 199 | Step-quality/error label |
| `unuseful` | 132 | 66 | Step-quality/error label |

These 965 sparse step records occur in 277 local stage instances. They label
step quality, not stage or operation type, and cannot define whether stages
from different trajectories are semantically identical.

The release also carries task- and dataset-level metadata. These fields recur,
but none labels a stage:

| Field | Vocabulary | Values recurring across trajectories | Maximum trajectories for one value | Scope |
|---|---:|---:|---:|---|
| `agent` | 4 | 4 | 213 | Framework |
| `model` | 3 | 3 | 147 | Model |
| `task_name` | 251 | 102 | 5 | Whole task |
| `task_slug` | 405 | 0 | 1 | Trajectory-specific task key |
| `difficulty` | 3 | 3 | 182 | Whole task/dataset |
| `category` | 22 | 17 | 209 | Whole task/dataset |
| flattened `tags[]` | 208 | 134 | 50 | Whole task/dataset |
| `solved` | 1 (`false`) | 1 | 405 | Outcome of this failed-only population |

The Step 0087 scorer reads only `traj_id`, `agent`, `task_name`, `solved`,
`step_count`, and `stages`. It does not use `incorrect_stages`, task
categories, or tags as stage identity.

The normalized operation input also has visible categorical fields. They are
source-derived inputs to the methods, not released human stage labels:

| Visible operation field | Vocabulary | Values recurring across trajectories | Maximum trajectories for one value | Values |
|---|---:|---:|---:|---|
| `action_kind` | 9 | 9 | 402 | `communicate`, `edit`, `execute`, `inspect`, `install`, `other`, `search`, `test`, `version-control` |
| `phase` | 2 | 2 | 405 | `change`, `explore` |
| `raw_action_key` | 400 | 155 | 169 | Complete vocabulary retained in `raw-results.json` |
| `source_kind` | 1 | 1 | 405 | `tool` |
| `agent` | 4 | 4 | 213 | Four benchmark frameworks |
| `project` | 1 | 1 | 405 | `codetracebench` |

In particular, the two-value `phase` field is not the 2,948-stage human gold,
and neither `action_kind` nor `raw_action_key` defines cross-run stage
identity.

## Packet and archive audit

The exact 12 source-packet batches contain 405 sessions, 17,148 source-native
turns, and 20,866 operations. Their complete structural key inventory is:

```text
packet:
  annotation_contract, question, schema, sessions
session:
  archive, archive_sha256, framework, operation_count, session, task,
  task_source, turn_count, turns
turn:
  first_operation_id, intent, operation_ids, planned_action, progress,
  source_refs, turn, turn_id, visible_result
```

There is no `stage`, `stages`, `stage_id`, `stage_name`, `stage_type`,
`label`, `labels`, `outcome`, `score`, or `reward` key in these packets.

All 405 manifest-named archives exist. Exhaustive member listing found:

- the manifest's `source_relpath` represented in every archive;
- zero members under any manifest `annotation_relpath`;
- zero member basenames containing `annotation`, `label`, `stage`, or `gold`.

The archives are raw trajectory evidence used to construct packets. They do
not contain a second, richer cross-run identity oracle omitted by the scorer.

## Consequence

Pairwise precision, recall, or F1 against a “gold same stage type” cannot be
computed because no such relation exists in the released data. Treating equal
local ordinals, task categories, action keys, or error labels as stage types
would manufacture an oracle and would not answer the requested identity
question.

Phase 2B will therefore report impossibility and deterministic descriptive
proxies only. Those proxies can expose how broadly the current canonical IDs
are reused and provide examples for qualitative audit, but they cannot validate
false merges or synonym splits.
