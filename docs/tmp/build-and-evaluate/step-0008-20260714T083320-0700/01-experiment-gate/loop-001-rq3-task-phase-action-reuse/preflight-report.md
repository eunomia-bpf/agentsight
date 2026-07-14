# REAL PREFLIGHT Report: RQ3 Tag Fidelity

- Completed: `2026-07-14T09:13:59-07:00`
- Verdict pending independent review
- Scientific role: connectivity only; none of these values is a paper result

## Real source recovery

The approved Mind2Web command returned the complete current
`data/train/train_10.json` prefix: 9 sessions and 49 operations. The
GUI-Odyssey Dataset Viewer endpoint returned HTTP 503 on both row and first-row
requests. The preflight therefore downloaded the official Hugging Face
converted Parquet for the same `OpenGVLab/GUI-Odyssey`, `default/all` source,
read its first row, and passed that row through the unchanged existing
`normalize_gui_odyssey()` converter. This produced 1 real trajectory and 11
operations. The manifest records the same-source access fallback; no dataset,
split, row, tagger, or metric was substituted.

## Source-field audit

The GUI raw row exposes native `step.action` separately from `step.info`.
Across the 11 preflight operations, visible `info` contains coordinates, one
text argument, one key name, or an empty value. The approved automated audit
found zero explicit `action`/`action_type` serializations, arrow-suffixed gold
labels, or exact uppercase gold enums. The candidate is therefore available.

## End-to-end paths

| Cell | Real rows | Operations | Reference labels | Predicted labels | Coverage | V-measure | Constant V | Conservation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| task/Mind2Web | 9 | 49 | 3 | 5 | 1.000000 | 0.5565 | 0.0000 | 49/49 rows and weight |
| action/GUI-Odyssey | 1 | 11 | 3 | 3 | 0.181818 | 0.5245 | 0.0000 | 11/11 rows and weight |

The unchanged task backend automatically selected seven internal K-Means
clusters; keyword-name collisions yielded five emitted tags. Task input was
submitted once per session and broadcast to operation rows. The action backend
received only `step.info`; nine operations became literal `unmatched` and
remain inside the scorer's 11-operation support. The low action coverage is a
useful connectivity check, not a preflight success threshold.

Current AgentProf folded both cell files and their union. The union contains 60
input rows and weight 60, reports 60 operations and samples, and its folded
weights sum to 60. Every row and weight conservation boolean is true.

## Raw artifacts

- Inputs: `.agentsight/experiments/rq3-task-action-v1/preflight-inputs/`
- Same-source cache:
  `.agentsight/experiments/rq3-task-action-v1/source-cache/`
- Complete preflight output:
  `.agentsight/experiments/rq3-task-action-v1/preflight/`
- Primary machine summary:
  `.agentsight/experiments/rq3-task-action-v1/preflight/summary.json`

## Full-run decision

The real preflight exercised both backend types, scorer-only references,
explicit unmatched handling, the constant control, source leakage audit,
per-cell folding, and union folding. It authorizes the fixed full matrix if an
independent reviewer reproduces these checks without a blocker.
