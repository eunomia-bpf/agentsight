# FULL Result Report: RQ3 Task/Action Partition Fidelity

- Status: **VALID / supporting mixed evidence**; independent review **PASS**
- Fixed RQ: **RQ3 — How Accurate Are the Tags?**
- Scientific unit: four predeclared per-source partition-fidelity cells
- Repetitions/tuning: one deterministic complete run; none

## Validity inventory

| Source | Requested rows | Returned rows | Operations | Access |
|---|---:|---:|---:|---|
| Mind2Web `train_10.json` | up to 100 | 9, complete file | 49 | existing repo-file converter |
| lclan ScienceWorld mirror `default/test` | 100 | 100 | 2,504 | official HF converted Parquet |
| AndroidControl `default/train` | 2 | 2 | 9 | official HF converted Parquet |
| GUI-Odyssey `default/all` | 500 | 500 | 7,868 | official HF converted Parquet |

The Dataset Viewer remained HTTP 503. The three affected sources therefore use
their official Hugging Face converted Parquet from the same repository,
configuration, split, offset, and prefix, then pass through the unchanged
existing normalizers. Counts exactly match the historical R285 prefixes for
ScienceWorld, AndroidControl, and GUI-Odyssey. Mind2Web's current source file
contains nine rows rather than the older assumed hundred; all nine were run.

Both action source audits completed before inference and found zero structured
gold copies. Task texts were submitted once per session to the unchanged
TF-IDF/K-Means backend and predictions were broadcast to operations. Every
missing action prediction is the literal label `unmatched` inside scoring.

## Primary per-cell result vector

| Cell | Sessions | Operations | Gold labels | Emitted labels | Coverage | V-measure | Constant V |
|---|---:|---:|---:|---:|---:|---:|---:|
| task/Mind2Web | 9 | 49 | 3 | 5 | 1.000000 | 0.5565 | 0.0000 |
| task/ScienceWorld | 100 | 2,504 | 17 | 16 | 1.000000 | 0.8151 | 0.0000 |
| action/AndroidControl | 2 | 9 | 5 | 4 | 1.000000 | 0.8601 | 0.0000 |
| action/GUI-Odyssey | 500 | 7,868 | 6 | 324 | 0.172344 | 0.3000 | 0.0000 |

The task backend automatically selected 7 clusters on Mind2Web and 22 on
ScienceWorld; keyword-name collisions yield 5 and 16 emitted labels. No gold
label selected cluster count or names. AndroidControl supplies a positive but
small action cell. GUI-Odyssey is a complete mixed/negative backend boundary:
6,512 of 7,868 operations are unmatched, and the numerous coordinate/text/key
strings produce 324 emitted labels for six native action classes. This result
is retained rather than filtered or replaced.

## Current AgentProf correctness

| Profile | Input rows/weight | Reported operations/samples | Folded weight | Unique stacks | Exact |
|---|---:|---:|---:|---:|---|
| task/Mind2Web | 49 | 49 | 49 | 5 | yes |
| task/ScienceWorld | 2,504 | 2,504 | 2,504 | 16 | yes |
| action/AndroidControl | 9 | 9 | 9 | 4 | yes |
| action/GUI-Odyssey | 7,868 | 7,868 | 7,868 | 324 | yes |
| union | 10,430 | 10,430 | 10,430 | 349 | yes |

Every per-cell and union row count and total weight is conserved. This is a
profiler correctness check, not tag-quality evidence.

## Scientific interpretation before independent review

- The complete task vector is positive for target-blind task partition
  fidelity on two heterogeneous public trace sources, with strongest evidence
  from 100 ScienceWorld sessions and 2,504 operations.
- Action evidence is mixed: the existing normalization path aligns well on the
  tiny AndroidControl prefix but does not robustly recover GUI-Odyssey classes
  from coordinate/key/text `info` fields.
- The run does not answer phase fidelity, literal human-readable tag naming,
  stability under repeated sampling, or all unseen agent/task families.
- The result does not change the fixed RQ3, its positive hypothesis, the paper
  thesis, or the four-RQ structure. REVIEW decides whether the positive task
  evidence is paper-ready and whether a materially better existing action
  signal is worth a later experiment.

Negative/mixed backend development evidence stays in this audit trail. It is
not automatically inserted into the paper's positive result story.

## Raw artifacts

- Inputs: `.agentsight/experiments/rq3-task-action-v1/inputs/`
- Official same-source caches:
  `.agentsight/experiments/rq3-task-action-v1/source-cache/`
- Complete output: `.agentsight/experiments/rq3-task-action-v1/full/`
- Primary summary:
  `.agentsight/experiments/rq3-task-action-v1/full/summary.json`
