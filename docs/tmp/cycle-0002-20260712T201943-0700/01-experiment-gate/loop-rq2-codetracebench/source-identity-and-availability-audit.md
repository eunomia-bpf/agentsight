# CodeTraceBench Source Identity And Availability Audit

**Started:** 2026-07-12T20:52:00-07:00  
**Completed:** 2026-07-12T21:03:00-07:00  
**Cycle/gate:** cycle 0002 / EXPERIMENT  
**Parent:** `experiment-plan.md` revision 1  
**Status:** complete; invalidates revision 1 and supplies revision-2 population

## Question

Are CodeTraceBench's `full` and `verified` manifests independent reference and
test populations, and does every manifest row have an official raw artifact
that can be processed without reading annotations?

This audit examines source identity and availability only. It does not read a
hidden step label to select a row, define an operation, or score a method.

## Official Inputs

- full Parquet:
  `https://huggingface.co/datasets/NJU-LINK/CodeTraceBench/resolve/refs%2Fconvert%2Fparquet/default/full/0000.parquet`
- verified Parquet:
  `https://huggingface.co/datasets/NJU-LINK/CodeTraceBench/resolve/refs%2Fconvert%2Fparquet/default/verified/0000.parquet`
- official dataset repository tree:
  `NJU-LINK/CodeTraceBench`, enumerated through Hugging Face Hub
- local ignored copies:
  `.agentsight/experiments/codetracebench-rq2/manifests/`

The two manifests have the same 19-column schema. Identity comparison projects
all ordinary row fields and separately checks nested-row equality; availability
comparison uses manifest artifact paths and exact `traj_id` occurrence in the
official repository file list.

## Manifest Identity Result

| Property | Full | Verified | Intersection |
|---|---:|---:|---:|
| rows / unique `traj_id` | 3,316 | 1,000 | 1,000 |
| declared steps | 147,628 | 46,539 | 46,539 |
| unique `artifact_path` values | 3,292 including null | 993 including null | 993 |
| unique `source_relpath` values | 3,071 including null | 989 including null | 989 |
| unique `task_slug` values | 3,316 | 1,000 | 1,000 |

All 1,000 verified rows occur in full under the same `traj_id`. The rows are
column-for-column identical, including outcome, step count, paths when present,
and nested annotation fields. Therefore:

```text
verified ⊂ full
unique union = full = 3,316 trajectories / 147,628 steps
```

The earlier 4,316-trajectory / 194,167-step count double-counted the verified
subset. More importantly, revision 1's full-manifest reference included every
target's own operations and outcome, so revision 1 is scientifically invalid.

## Raw Artifact Availability

The full manifest has 25 rows where both `artifact_path` and `source_relpath`
are null. Exact search of all 20,447 paths in the official dataset repository
finds no file containing any of those 25 `traj_id` values. These are true source
omissions, not paths that can be reconstructed from the normal naming rule.
Conversely, every one of the 3,291 non-null manifest artifact paths occurs
exactly in the official repository tree; there is no additional dangling path.

| Population | Manifest rows | Raw-available rows | Missing rows | Missing steps |
|---|---:|---:|---:|---:|
| full | 3,316 | 3,291 | 25 | 1,451 |
| verified | 1,000 | 992 | 8 | 583 |
| failed verified | 468 | 461 | 7 | 540 |

All 25 omissions are OpenHands trajectories from DeepSeek-V3.2 or Kimi-K2.
They must not be reconstructed from annotation-embedded action references:
those references occur only inside label-bearing data and are not a complete
raw trajectory. Availability exclusion is performed before any annotation
column is projected, and the missing IDs remain in the coverage report.

The full real execution population is consequently all 3,291 officially
published raw archives and 146,177 declared steps. This is a complete run over
the released raw source, not a convenience sample.

## Task-Held-Out Reference Audit

For each of the 461 raw-available failed verified targets, revision 2 excludes
every full row sharing its `task_name`, then requires at least ten successful
and ten failed raw-available reference trajectories in the selected stratum.
Before extraction, manifest fields alone give:

| Selected reference stratum | Primary targets |
|---|---:|
| `(agent, model, difficulty, category)` | 134 |
| `(agent, model, category)` | 83 |
| `(agent, model)` | 244 |
| no supported stratum | 0 |

Thus every primary target receives one supported target-specific score table;
no target, duplicate row, or same-task run contributes to its estimator, and no
coarser-than-agent/model fallback is required.

## Decision And Downstream Changes

1. Revision 1 is **REJECTED**; no runner or preflight may implement it.
2. Revision 2 uses per-target leave-task-out scoring over raw-available rows.
3. Every unique-population count is corrected; full and verified are never
   added.
4. Source availability is a terminal status for all 3,316 manifest rows;
   extraction completeness applies to all 3,291 published raw archives.
5. The 992 raw-available verified rows are the complete target source; the 461
   failed rows are the primary incorrect-step population.
6. Hidden labels enter only after every operation, group, score, cutoff, and
   prediction is written.

This correction changes experiment execution, not RQ2, the four-RQ program, the
positive hypothesis, or the AgentProf thesis.
