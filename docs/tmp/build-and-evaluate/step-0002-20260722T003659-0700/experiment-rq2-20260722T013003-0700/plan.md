# RQ2 Experiment Plan — Validation Dynamics

**Created:** 2026-07-22T01:30:03-07:00  
**State:** preregistration draft; no RQ2 statistic has been computed

## 1. Question and claim boundary

RQ2 asks how recognized validation is interleaved with mutation during
long-running Agent work. The experiment may describe validation scarcity,
burstiness, inter-success mutation accumulation, failed attempts, and complete
validation cycles. It
does not claim that a successful command covers or proves any specific change,
that an unrecognized command is not validation, or that cadence causes final
quality.

The frozen source already establishes that only AgentSight, ActPlane, and
eunomia.dev expose a recognized success. The preregistered four-project gate is
therefore known to stop cross-case interpretation. This is a supporting
source-coverage result plus three within-case descriptions, not six independent
replications. The expected observable pattern is uneven validation cadence and
mutation accumulation; the competing possibilities are proportional tracking
of activity or adapter coverage too sparse to resolve a pattern.
Artifact-type stratification is deferred to the independently frozen RQ5
classifier. This experiment supplies only RQ2's cadence/accumulation facet and
cannot alone close canonical RQ2.

## 2. Frozen source and eligibility

Reuse only
`docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw/`
at cutoff `1784708569241`; do not rescan mutable native sessions. The mutation
CSV hash is
`3d911332f7827afdee74a1f6a0f85aa002be297379e14909dbba1fee36d88964`.
The six compressed event hashes are:

```text
f8536f1ab6d73393d993c2cde66e6fc9deff759329f17a12eaa1888a49986db4  academic-writing-skills.json.gz
4ee9fc1aebeee30bc3c2b45117e38a0d63053bda1d167a839466eed630034026  ActPlane.json.gz
ebbf3dd94459a6d43db945a41f8b112f3289b5833d09b864a070fbc66a8bbf46  agentsight.json.gz
33b6b1b172027b77ae66695a37025ec41c818df5d0f81c05390568f8fc5c6880  agentskill-observability-paper.json.gz
88dec6db8a1320c6991fefa236eb6afbfc65e175d62eddbadb80c68ed6a46098  bpf-developer-tutorial.json.gz
cf7dfea58a4453b221abe8eaf32ed83fe24842d3cac67010fd23a46f974b4fe9  eunomia-dev.json.gz
```

The analysis reads these verified gzip files directly through Python's `gzip`
module; it never substitutes the mutable uncompressed copies. An event is a
recognized validation attempt only when the existing `agent-session` adapter
emits `effect == test`. Split native `status` into `ok`, `fail`, and `observed`
without imputation. Use only actions whose worktree ID is resolved for the
primary action axis. A project is validation-qualified only if it contains at
least one recognized successful attempt; projects without one remain explicit
source-coverage rows.

## 3. Deterministic measurements

Preserve the frozen JSON event-array order, which was produced by
`(ts_ms, event.id)`, and first verify event IDs are unique. Partition every
sequence by `(project, worktree_id)`; a validation in one worktree can never
bound mutation accumulation in another. Assign a one-based
`worktree_attributed_action_rank` within each partition. Keep native session IDs
without serializing overlapping sessions into an invented order.

1. Report successful, failed, and status-unknown recognized validation attempts
   per 1,000 worktree-attributed Tool actions.
2. Define a **worktree-local validation cycle** as the interval after one
   recognized successful validation through the next. Action length includes
   the ending validation event and excludes the starting event. Report elapsed
   wall time, distinct native session IDs, confirmed mutation rows, distinct
   mutated artifacts, and failed/observed attempts. This is cadence evidence,
   not mutation coverage.
3. Define **inter-success mutation accumulation** literally as the count of
   confirmed mutation rows in that interval. Do not say that the ending success
   clears, covers, or validates those mutations. A single Tool event can supply
   multiple mutation rows and each row remains counted.
4. When an ending successful validation event also carries mutation rows, the
   source provides no within-event order. Mark those rows as co-observed
   validation-command effects, report them separately, and exclude them from
   the preceding interval's accumulation.
5. Treat the prefix from the worktree's first attributed action to its first
   success as left-censored and the suffix from its last success to its last
   attributed action at/before the cutoff as right-censored. Show both in the
   trajectory but exclude them from complete-cycle distributions.

No fixed 24-event window, commit alignment, scalar quality score, intent label,
or inferred test coverage is introduced.

## 4. Figure F5

Create vector PDF and PNG from one Python/matplotlib script:

- **Panel A — validation trajectories:** one lane per worktree; exact cumulative
  confirmed mutations over normalized worktree-attributed action position, with
  native successful, failed, and status-unknown attempts overlaid. Normalized x
  is display compaction only; labels expose exact action and elapsed-time range,
  mutation rows, co-observed effects, and attempt counts.
- **Panel B — complete-cycle accumulation:** empirical distributions of
  inter-success confirmed mutation rows by project/worktree, with exact cycle
  counts. Left/right-censored intervals and co-observed mutation rows are
  reported beside the panel and never entered as completed-cycle accumulation.
- **Panel C — validation source coverage:** per-project recognized attempt rate
  and native outcome composition for all six projects. It explicitly states
  `3/6 recognized-success coverage; cross-case interpretation stopped`.
  Projects without a success are unavailable for cycle analysis rather than
  assigned zero cadence.

The figure title and caption must say “recognized validation,” not “tests,”
unless the underlying adapter family is explicitly broken out.

## 5. Stop conditions and verification

- Write event-level worktree lanes to
  `experiment-rq2-20260722T013003-0700/raw/rq2-trajectory.csv`, interval rows to
  `raw/rq2-cycles.csv`, and project/worktree coverage to
  `raw/rq2-coverage.csv`. The exact command is:

  ```bash
  python3 agentvis/research/plot_rq2.py \
    --rq1-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw \
    --output docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq2-20260722T013003-0700
  ```

  It renders `figures/rq2-validation-dynamics.pdf` and `.png`. Record the exact
  command and all output hashes in `commands.log`.
- Recheck all frozen input hashes and recompute event/action/mutation totals
  against the frozen RQ1 summaries.
- Every attempt and mutation row must resolve to a frozen source event.
- Verify two interleaved worktrees, multiple/overlapping sessions, equal
  timestamps, multiple mutation rows per Tool event, success with co-observed
  mutation, zero/one/two successes, every attempt status, both censored ends,
  and missing worktree identity on hand-constructed fixtures.
- The fewer-than-four stop is already triggered: report source coverage plus
  within-case descriptions only, and never pool thousands of cycles in two
  projects as population-level replication.
- If fewer than two complete cycles exist in a qualified project, omit its
  cycle distribution while retaining its timeline.
- Plot generation must consume only a frozen RQ2 CSV derived from the frozen
  RQ1 files; no fixture values may enter final media.

A real preflight must run one qualified project from the pinned files and
verify selected cycle boundaries by `event_id`. A fresh reviewer must approve
this repaired plan before implementation. A different
fresh reviewer must recompute selected cycles and inspect F5 before any RQ2
result enters the paper.
