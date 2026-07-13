# Experiment Plan: RQ2 CodeTraceBench Differential Profiling

**Started:** 2026-07-12T20:31:00-07:00  
**Revised:** 2026-07-12T20:44:00-07:00  
**Cycle/gate:** cycle 0002 / EXPERIMENT  
**Parent:** `../literature-20260712T203001-0700/source-protocol-baseline-report.md`  
**Plan revision:** 1; pending serial review round 2

## Research Question And Tested Hypothesis

- **RQ exactly as written in the paper:** **RQ2: Does Profiler Output
  Correspond to Real Problems?**
- **Specific uncertainty tested here:** whether a semantic differential resource
  profile learned from one real population of coding-agent runs concentrates
  independently annotated incorrect steps in a disjoint population of failed
  runs more strongly, and with less exposed-step work, than equally informed
  raw-action and target-blind trace-tree organizations.
- **Tested hypothesis:** on failed trajectories in the complete CodeTraceBench
  verified split, one fixed semantic operation stack scored only from
  failed-versus-successful operation excess in the disjoint full split will
  achieve higher tie-aware hidden-incorrect-step AP and recall at 30% exposed
  work, and lower work to 50% recall, than both main baselines.
- **Why the answer matters:** RQ2 is the paper's direct test that cross-run
  profiling brings recurring real problems to an analyst's attention. Prior
  runs reject two constructions but supply no clean positive answer.

This one experiment tests failed-run incorrect-step localization on coding
agents. It is decisive evidence toward RQ2, not the complete cross-domain RQ
answer. `unuseful` and the label union remain secondary analyses because the
official annotation protocol constructs them differently; they cannot alter the
primary verdict. Any contradiction bounds this construction and family, not the
fixed RQ, four-RQ program, or thesis.

## Paper-Value Admission

- **Planned role:** decisive RQ2 experiment and candidate headline evaluation.
- **Largest credible paper story unlocked:** AgentProf can use a reference
  population of real runs to build semantic differential hotspots that expose
  recurring incorrect work in unseen failed executions across heterogeneous
  coding-agent frameworks; per-run tracing remains complementary for causal
  reconstruction.
- **Strongest reject argument addressed:** semantic grouping merely renames
  actions, while any apparent localization comes from target labels, current-run
  outcome, group size, or a weaker baseline.
- **Independent evidence:** 4,316 official trajectories and 194,167 declared
  steps across a 3,316-trajectory reference split and disjoint 1,000-trajectory
  confirmatory split; four frameworks, multiple frontier models, real
  SWE-bench/TerminalBench tasks, and human step labels. None appeared in the
  prior AgentRx, TELBench, or Hodoscope confirmation sets.
- **Why it is not tautological:** full-split outcomes estimate profiles;
  verified-run outcomes select the failed-run evaluation population only and do
  not estimate a verified step's score. No annotation step, stage, reason, or
  directory reaches extraction, grouping, scoring, or cutoff selection.
- **Positive paper decision:** admit this condition as direct positive RQ2
  evidence and carry the identical frozen semantic construction to one
  independent safety or redundancy family before the complete RQ answer.
- **Contradictory/mixed decision:** retain RQ2 and the positive hypothesis;
  identify whether the failure belongs to raw alignment, differential signal,
  semantic mapping, transfer, or grouping. Route to a materially different real
  signal/family rather than tuning on verified labels.
- **Best alternative:** ToolSafe is the next safety replication, but its
  candidate-call classification unit is less direct for the current cross-run
  profiling objection. CodeTraceBench has higher immediate decision value.

## Expected And Alternative Outcomes

- **Expected:** cross-framework semantic folding reunites recurring inspection,
  modification, execution, and verification behavior that raw commands and a
  single-run trace tree fragment. Full-split failed-excess mass should therefore
  prioritize verified steps independently labeled incorrect.
- **Strongest competing explanation:** outcome-conditioned raw actions or the
  CodeTracer state-change/exploration tree contain all usable signal; semantic
  normalization adds no problem concentration.
- **Contradiction:** semantic profiling fails to beat the stronger main baseline
  on either primary AP or recall-at-30%-work, or its paired 95% interval includes
  zero for both metrics with no predeclared framework-wide positive regime.

## Published Precedent And Real Assets

- **Protocol:** CodeTracer defines gold failure-relevant step set `G`, predicted
  set `P`, per-instance Precision/Recall/F1, and macro averaging. Ranked outputs
  may be capped by a shared fixed implementation budget; CodeTracer does not
  prescribe a 30% budget. This experiment reuses its set equations and calls
  30% an AgentProf inspection protocol.
- **Official assets:**
  [CodeTracer](https://github.com/NJU-LINK/CodeTracer),
  [CodeTraceBench](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench),
  and the release-build AgentProf binary from this worktree. Execution records
  the actual CodeTracer commit and Hub revision.
- **Reused components:** official raw archives and manifests; official
  MinisweParser, OpenHandsParser, and Terminus2Parser; a thin SWE-agent `.traj`
  adapter following the released SWE-agent JSON schema; official
  `ClassificationStore` regex behavior and `TreeBuilder.build`; official step
  IDs/labels and macro P/R/F1 equations; AgentProf operation-file ingestion and
  JSON/folded output.
- **Necessary glue:** download/extract orchestration, strict raw-to-step
  alignment, operation JSONL conversion, invocation of AgentProf for each view,
  reference/test differential scoring, and metric computation. It introduces no
  learned detector, synthetic trace, private oracle, or annotation.

## Data, Information Boundary, And Matching

### Reference and test populations

- **Reference:** all 3,316 full-split trajectories (147,628 declared steps).
  The 3,210 rows with non-missing `solved` values estimate differential scores;
  106 missing-outcome rows remain extraction-coverage cases and absolute-profile
  controls.
- **Confirmatory:** all 1,000 verified trajectories (46,539 declared steps).
  All are extraction-audited. The primary target population is the 468
  `solved=false` rows; failed rows with no incorrect gold steps remain in pooled
  work accounting and receive a separate false-positive burden report.
- **Disjointness:** no verified trajectory contributes operations or outcome to
  its score estimator. All 1,000 verified task names occur in the full split,
  but the exact trajectory rows and artifacts are separate.

### Matching strata

Reference excess is estimated within `(agent, model, difficulty, category)`
when both outcomes occur. If a verified row's exact stratum lacks both cohorts,
the fixed fallback is `(agent, model, category)`, then `(agent, model)`.
Source audit found 834/1,000 verified rows have both cohorts in the first stratum
and 958/1,000 in the second; all 1,000 have both outcomes under `(agent, model)`.
The fallback is therefore complete and fixed before label scoring. Task/category
metadata are matching variables only and are not semantic stack frames.

Reference profiles are normalized inside stratum before macro-averaging stratum
scores. Bootstrap resamples trajectories as task-clustered units and recomputes
the matching, cohort profiles, scores, and metrics in every replicate.

### Forbidden inputs

The extraction/ranking process may read raw official archives and manifest
fields `traj_id`, agent/model/task/category/difficulty metadata, artifact path,
step count, and full-split `solved`. Verified `solved` is read only to define the
predeclared failed-run evaluation population, never as a feature or score.

It may not read manifest `stages`, `incorrect_error_stage_count`,
`annotation_relpath`, `incorrect_stages`, label reasoning, released annotation
directories, or any generated `step_N.jsonl` containing `llm_analysis`. The
only allowed official code paths are the three named seed parser `parse`
methods, the explicit SWE-agent raw adapter, `ClassificationStore.classify`
with an isolated empty `XDG_CONFIG_HOME`, and `TreeBuilder.build`. The runner
must reject calls to `build_from_annotation`, `normalize_step_jsonl`, or any
path containing the released annotation directory names.

## Common Operations And Fixed Views

Every raw command/action becomes one value-one AgentProf operation with source
step ID and target-blind fields. The exact semantic stack is:

```text
phase -> action_kind
```

- `phase` is exactly CodeTracer's target-blind `ClassificationStore.classify`
  output: `change` or `explore`, using its published default regex and an empty
  experiment-local store; no LLM fallback or persisted user classification.
- `action_kind` is the first executable/tool family mapped before verified
  scoring to the fixed vocabulary `inspect`, `search`, `edit`, `execute`,
  `test`, `install`, `version-control`, `communicate`, `other`. Rules are plain
  AgentProf op-map regexes over the raw action string and are identical across
  splits. They may be clarified for uncovered syntax using full-split raw data
  only; vocabulary, priority, and final rules are printed before preflight.

No outcome, task/category, observation status, annotation stage, or target word
appears in this stack.

For each matching stratum and view, AgentProf folds operation count separately
for failed and successful reference cohorts. For group `g`:

```text
score(g) = failed_count(g) / failed_total
           - successful_count(g) / successful_total
```

Scores are not clipped. An unseen verified group receives neutral score zero.
Stratum scores are macro-averaged where a group appears. Verified operations do
not update counts.

### Main baselines

1. **Raw-action grouping:** normalized raw executable/tool identity with
   arguments and paths removed, but without semantic category folding. It
   represents ordinary log aggregation. If it matches or wins, semantic
   normalization has not earned its abstraction cost.
2. **Target-blind CodeTracer tree:** the path produced by official
   `TreeBuilder.build` over raw normalized steps, using only the isolated
   change/explore classifier. It represents the strongest released alternative
   hierarchy available without annotation stages. If it matches or wins, the
   simpler operation stack is not better for this decision.

Both baselines receive the same raw operations, matching strata, outcome
cohorts, differential equation, and metric implementation. The tree output is
mapped back to exact source steps; no annotation-derived stage is accepted.

### Controls and external references

- **Flat/global:** one group and full inspection; lower bound.
- **Per-session:** trajectory identity; conventional per-run drilldown. It is a
  control, not a strongest localization baseline.
- **Framework-native action/episode:** raw OpenHands event/cause, SWE `.traj`
  turn, Terminus episode, or MiniSWE command-response identity. Where this key
  is identical to raw-action or session grouping, the duplicate cell is merged
  and reported once.
- **Absolute hotspot:** operation-count ranking without any `solved` outcome for
  the semantic and strongest main-baseline views.
- **Outcome null:** within the full reference split's matching strata, permute
  `solved` at trajectory level, preserve each trajectory's operations and the
  group-size multiset, and recompute profiles/scores 2,000 times. This breaks
  group-outcome association without breaking trajectories.
- **Annotation stage:** one oracle upper bound after terminal label join. Direct
  label grouping is omitted as trivial.
- **Published CodeTracer:** cite its Bare LLM/Mini-CodeTracer/CodeTracer
  P/R/F1/token results as direct-diagnosis references, not equally informed
  matched rows.

## Metrics And Tie Semantics

### Primary estimand

The primary estimand is pooled hidden-incorrect-step concentration across the
468 failed verified trajectories. A profile exposes complete groups, not an
invented order inside a group.

Distinct score values form tie blocks. Groups within a tie block are exposed
together. Inspection work is the number of unique source steps exposed divided
by all source steps in the primary population. When a requested budget or
recall threshold intersects a block, linearly interpolate between the state
before and after that complete block; do not hash-order groups or steps.

- **Primary metric 1:** tie-aware pooled average precision, computed as the sum
  of precision after each score block times that block's recall increment.
- **Primary metric 2:** pooled recall at 30% exposed-step work, using the
  predeclared interpolation. This is an AgentProf inspection budget, not a
  CodeTracer cutoff.
- **Primary metric 3:** pooled exposed-step work required for 50% recall.
- **Primary comparator:** the stronger of the two main baselines by AP; semantic
  profiling must beat each main baseline on AP and R@30%, with positive paired
  95% intervals, and have no worse work@50% to support the tested hypothesis.

### Compatibility and secondary metrics

- Apply CodeTracer's per-instance P/R/F1 equations at the AgentProf 30% group-
  block budget and macro-average only across failed verified trajectories with
  at least one hidden incorrect step. Separately report false-positive exposed
  work on failed trajectories with `|G|=0`; never encode their undefined AP,
  recall, or work@50% as zero or silently delete them.
- Report incorrect-step results by framework. Bootstrap uses task-clustered,
  framework-stratified resampling of both reference and test populations and
  recomputes scores/ranking/metrics for 10,000 replicates.
- Report `unuseful` and union results with the same frozen outputs only as
  secondary descriptive analyses, partitioned by the annotation-eligible
  population. They do not select fields, score, cutoff, or primary verdict.
- Secondary usability measures are groups exposed, unique groups, first-
  positive work, extraction/profile wall time, and total download/storage.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| extraction | dependency inside experiment | all 4,316 raw archives | official parsers + SWE adapter | one complete pass | any unresolved alignment invalidates affected framework cell |
| reference | proposed/baseline input | 3,210 outcome-bearing full rows | per-stratum failed/success profiles | deterministic | estimates target-blind group scores |
| main | proposed | all failed verified rows | semantic stack | deterministic | tests the construction |
| matched baselines | main baseline | identical reference/test operations | raw-action and target-blind CodeTracer tree | deterministic | tests semantic value against real alternatives |
| controls | control | identical operations | flat, session/native, absolute hotspot | deterministic | interprets grouping and outcome contributions |
| null | control | full reference split | stratum-wise trajectory outcome permutation | 2,000 | rejects generic grouping/cohort explanation |
| uncertainty | analysis | reference + failed verified populations | task-clustered paired bootstrap | 10,000 | estimates comparison uncertainty |
| oracle | upper bound | scored failed verified rows | annotation stage | deterministic | calibrates headroom only |

## Execution And Completion

- **Implementation command:**

  ```bash
  python3 script/codetracebench_agentprof_eval.py full \
    --full-manifest .agentsight/experiments/codetracebench-rq2/manifests/full.parquet \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --raw-root .agentsight/experiments/codetracebench-rq2/raw \
    --codetracer-root .agentsight/experiments/codetracebench-rq2/CodeTracer \
    --agentpprof-bin agentpprof/target/release/agentpprof \
    --out docs/visexp/out/codetracebench-rq2 \
    --permutations 2000 --bootstraps 10000 --seed 4202
  ```

  The runner does not yet exist at revision 1; implementation is required and
  independently reviewed before real preflight. Its grouping scorer must derive
  each step's stack from the exact operation fields and refuse completion unless
  every recomputed stack weight matches AgentProf JSON output exactly.
- **Real preflight:** four verified rows selected only by framework, outcome, and
  deterministic manifest order—never by hidden labels—plus matching full-split
  references. Download real archives, extract/align all raw steps, invoke release
  AgentProf for every non-oracle view, write predictions, then join labels and
  recompute all metrics. Finding no positive in the four rows is a valid
  preflight result; engagement, not a favorable label, is the criterion.
- **Full completion:** terminal extraction status for all 4,316 rows and all
  194,167 declared steps; exact one-to-one source step-ID alignment within every
  valid framework cell; every proposed/baseline/control profile complete; all
  primary and secondary targets scored under the frozen outputs; 2,000 null
  trials and 10,000 full score-recomputing bootstraps complete; raw commands,
  coverage, metric tables, and figure data preserved. A prefix, one framework,
  or “discrepancies listed” without invalidation is incomplete.
- **Validity rule:** any missing, duplicate, reordered, or action-unit-mismatched
  step makes that trajectory invalid. A systematic mismatch makes the affected
  framework cell invalid/incomplete and blocks a cross-framework result until
  repaired and rerun.
- **Artifact layout:** downloads/extracted data under ignored
  `.agentsight/experiments/codetracebench-rq2/`; summaries, coverage, AgentProf
  outputs, metric tables, and figure data under
  `docs/visexp/out/codetracebench-rq2/`; Markdown reports in this loop directory.
- **Cost:** the official dataset card reports approximately 3.52 GB total files;
  local storage has more than 100 GB free. Preflight measures download,
  extraction, profile, bootstrap time, and peak disk before the full run.
- **Recovery:** resumable archive downloads and one terminal status row per
  trajectory. Checkpoints are execution conveniences, not scientific state.

## Interpretation

- **Positive:** semantic differential profiling beats both main baselines on AP
  and R@30% with positive paired 95% intervals, is no worse on work@50%, exceeds
  the outcome null, and is not driven by one framework. Admit this coding-agent
  condition as direct RQ2 evidence and replicate the frozen construction.
- **Contradictory:** a valid run rejects this semantic stack/differential signal
  on CodeTraceBench. Preserve RQ2 and route to a materially better real signal or
  independent family, never verified-label retuning.
- **Mixed/inconclusive:** framework-specific or secondary-target gains are
  supporting mechanism evidence only and do not enter the paper as the RQ2
  answer.
- **Paper artifact:** one RQ2 table with primary AP/R@30%/work@50%, compatibility
  macro P/R/F1, group count, and actual work; one recall-versus-work curve with
  paired bootstrap bands.

## Reproducibility Notes

Record CodeTracer commit, Hub revision, AgentProf worktree revision/dirty
boundary, parser/stack/op-map text, package versions, extraction coverage, the
single command, seed 4202, and all deviations. These are ordinary evidence, not
hash-bound gate artifacts. No Git action affects the verdict.
