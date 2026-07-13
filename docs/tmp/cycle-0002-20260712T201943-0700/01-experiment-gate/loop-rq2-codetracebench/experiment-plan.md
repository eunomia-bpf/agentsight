# Experiment Plan: RQ2 CodeTraceBench Differential Profiling

**Started:** 2026-07-12T20:31:00-07:00
**Revised:** 2026-07-12T22:50:35-07:00
**Cycle/gate:** cycle 0002 / EXPERIMENT
**Parent:** `../literature-20260712T203001-0700/source-protocol-baseline-report.md`
**Plan revision:** 6; revision 4 was approved after serial plan-review round 5.
Revision 6 incorporates the complete verified-source audit and successful
end-to-end REAL PREFLIGHT; independent implementation re-review is required
before the full run.

## Research Question And Tested Hypothesis

- **RQ exactly as written in the paper:** **RQ2: Does Profiler Output
  Correspond to Real Problems?**
- **Specific uncertainty tested here:** whether a semantic differential resource
  profile learned from real coding-agent runs on other tasks concentrates
  independently annotated incorrect steps in task-held-out failed runs more
  strongly, and with less exposed-step work, than equally informed raw-action
  and target-blind CodeTracer phase organizations.
- **Tested hypothesis:** on the source-valid failed trajectories in
  CodeTraceBench's verified subset, one fixed semantic operation stack scored only from
  failed-versus-successful operation excess in runs with a different
  `task_name` will achieve higher tie-aware hidden-incorrect-step AP and recall
  at 30% exposed work, and lower work to 50% recall, than both main baselines.
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
- **Independent evidence:** the manifest describes 3,316 unique trajectories
  and 147,628 declared steps, of which the official Hub actually publishes raw
  archives for 3,291 trajectories and 146,177 steps. The 1,000-row verified set
  is an exact subset of the full manifest, not an additional split; 992 verified
  rows have raw archives. Every scored target excludes every full
  row with the same `task_name`, so its profile comes from other real tasks.
  The source covers four frameworks, multiple frontier models, real
  SWE-bench/TerminalBench tasks, and human step labels. None appeared in the
  prior AgentRx, TELBench, or Hodoscope confirmation sets.
- **Why it is not tautological:** for target trajectory `t`, profiles are
  estimated only from full-manifest trajectories whose `task_name` differs from
  `t`; therefore neither `t`, a duplicate manifest row for `t`, nor another run
  of the same task contributes operations or outcome to its score. Target
  outcome selects the failed-run evaluation population only. No annotation
  step, stage, reason, or directory reaches extraction, grouping, scoring, or
  cutoff selection.
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
- **Strongest competing explanation:** outcome-conditioned raw actions, the
  published CodeTracer change/explore classification, or arbitrary low-
  cardinality grouping contains all usable signal; semantic normalization adds
  no problem concentration.
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
  MinisweParser, OpenHandsParser, and Terminus2Parser source-schema logic plus
  thin target-blind alignment adapters where those seed parsers merge or omit
  benchmark step units; a thin SWE-agent `.traj` adapter following the released
  SWE-agent JSON schema; official
  `ClassificationStore` regex behavior and `TreeBuilder.build`; official step
  IDs/labels and macro P/R/F1 equations; AgentProf operation-file ingestion and
  JSON/folded output.
- **Necessary glue:** download/extract orchestration, strict raw-to-step
  alignment, operation JSONL conversion, invocation of AgentProf for each view,
  reference/test differential scoring, and metric computation. It introduces no
  learned detector, synthetic trace, private oracle, or annotation.

## Data, Information Boundary, And Matching

### Reference and test populations

- **Unique source population:** the full manifest has 3,316 trajectories and
  147,628 declared steps. The verified manifest's 1,000 rows and 46,539 steps
  are an exact subset: all 1,000 `traj_id` values and all shared row fields are
  identical. These rows are never added to the full count.
- **Raw availability boundary:** the official repository tree contains no file
  matching 25 full-manifest IDs (1,451 steps), including eight verified IDs
  (583 steps). All 25 have null `artifact_path` and `source_relpath`; they are
  unavailable source rows, not parse failures. They are excluded before any
  label field is projected and listed in coverage. The experiment must not
  reconstruct them from annotation-embedded action snippets.
- **Target population:** all 1,000 verified rows were availability-audited and
  all 992 raw-available rows were extraction-audited. Exactly 911 align
  one-to-one to the released benchmark step unit: 483 solved, 405 failed, and
  23 with missing outcome. The 89 missing, mismatched, or adapter-error rows are
  reported as source exclusions and are never truncated, padded, synthesized,
  or count-fitted. The primary target population is therefore all 405
  source-valid `solved=false` rows. Failed rows with no incorrect gold steps
  remain in pooled work accounting and receive a separate false-positive burden
  report.
- **Per-target reference:** for each target `t`, start from all full-manifest
  raw-available rows with non-missing `solved`, retain only rows that pass the
  same source-unit extraction rule, then exclude every row with
  `task_name == t.task_name`. This excludes `t` itself and all same-task
  near-neighbors before any profile or score is estimated. Missing-outcome and
  source-invalid rows remain coverage cases and absolute-profile controls only.
- **Identity audit:** before extraction, assert verified IDs are a subset of
  full IDs, never sum the two manifests, and emit counts for overlap in
  `traj_id`, artifact path, source path, and full projected row content. Any
  unexpected non-subset row or conflicting duplicate is a source error, not a
  second sample.

### Matching strata

After same-task exclusion, reference excess is estimated within
`(agent, model, difficulty, category)` only when at least 10 trajectories occur
in each outcome cohort. Otherwise the fixed fallback is
`(agent, model, category)`, then `(agent, model)`, always with the same 10-per-
outcome minimum. Support is recomputed after source-invalid references and the
target task are excluded; pre-audit assignments over raw-available rows are not
authoritative. The end-to-end six-target REAL PREFLIGHT used the three levels
for 1, 4, and 1 targets respectively. The full run must emit the final support
counts for all 405 targets. Task/category metadata are matching variables only
and are not semantic stack frames.

Reference profiles are normalized inside the selected target-specific stratum.
Bootstrap resamples unique tasks as clusters and, in every replicate, removes
all reference draws sharing the current target task before recomputing cohort
eligibility, fallback, profiles, scores, and metrics.

### Forbidden inputs

The extraction/ranking process may read raw official archives and a projected
manifest containing only fields `traj_id`, agent/model/task/category/difficulty
metadata, artifact path, step count, and full-manifest `solved`. Verified
`solved` is read only to define the
predeclared failed-run evaluation population, never as a feature or score.

It may not read manifest `stages`, `incorrect_error_stage_count`,
`annotation_relpath`, `incorrect_stages`, label reasoning, released annotation
directories, or any generated `step_N.jsonl` containing `llm_analysis`. Allowed
raw adapter fields are limited to MiniSWE message/log action-observation turns;
OpenHands session-event `id/source/action/args/tool_call_metadata/message/cause/
observation` or SWE-raw LLM-call `timestamp/messages[].role/tool_calls.function`
fields; Terminus2 released `commands.txt` Python-literal records; and
SWE-agent `.traj` `trajectory[].action/observation`. The official seed parsers
are the starting implementation, with thin target-blind adapters for the
released source structures listed below. They may use `step_count` only as a
post-extraction assertion, never to select, split, retain, truncate, or pad
operations, and they never read hidden step IDs or labels. The only other
allowed official paths are
`ClassificationStore.classify` with an isolated empty `XDG_CONFIG_HOME` and
`TreeBuilder.build`. The runner must reject calls to `build_from_annotation`,
`normalize_step_jsonl`, or any path containing released annotation directories.

The benchmark-step adapters are frozen as follows; they preserve source order
and assign consecutive one-based IDs:

1. **MiniSWE:** when the archive publishes a `.traj.json`, deterministically use
   the official seed-parser rule: every assistant message containing the
   required bash action contributes its fenced bash body in message order.
   Prose-only assistant turns remain source events but are not executed
   benchmark operations. Only when `.traj.json` is absent and
   `sessions/agent.log` is published,
   strip ANSI control sequences and segment at each visible
   `mini-swe-agent (step N, ...)` marker. Only a bash fence in the assistant
   portion before the next visible `User:` prompt is an executed action;
   prose-only assistant turns are recorded as excluded non-operation events,
   and bash examples in the following user prompt are not actions. Reindex
   executed actions consecutively and pair the following `<returncode>` block
   when present. No terminal or other operation is synthesized to satisfy
   `step_count`; any count mismatch is invalid.
2. **OpenHands:** for released session events, order by numeric event ID and
   include every non-null agent-source action except `system` and `message`.
   Preserve real agent `think`, `run`, `run_ipython`, `read`, `edit`, `finish`,
   and other non-bookkeeping actions; exclude user-source task messages and
   user-source `recall`. Pair an observation only through its integer `cause`.
   For released
   `swe_raw/openhands` LLM-call records, do not concatenate responses across
   restarts or context compaction. Select the request record with the largest
   complete visible assistant-`tool_calls[]` history (tie: later numeric
   `timestamp`, then path) and emit those calls in request order; the selected
   record's response is not yet part of that request transcript. The complete
   verified audit reproduced 313/313 SWE-raw OpenHands counts; 57 archives
   contain a context decrease and 137 have tied maximum contexts, so the fixed
   timestamp/path tie rule is exercised rather than inferred from one sample.
3. **Terminus2:** read released `commands.txt` in source order with
   `ast.literal_eval`; each string record, including an empty string, is one
   agent operation. Non-string list records are harness recording/test/control
   commands and are not agent steps. Episode response JSON is not the released
   benchmark step stream and is never used to count-fit the manifest.
4. **SWE-agent:** emit exactly one operation for each released `.traj`
   `trajectory[]` element in list order.

These are source-format inclusion rules, not “adjust until the count matches.”
Any trajectory that violates its rule or declared count is invalid until the
raw-schema adapter is corrected without annotations and the complete affected
framework is rerun. The complete verified audit currently retains 185/199
raw-available native OpenHands, 313/313 SWE-raw OpenHands, 174/222 Terminus2,
65/82 native MiniSWE, 68/68 SWE-raw MiniSWE, and 106/108 SWE-agent trajectories.

## Common Operations And Fixed Views

Every raw command/action becomes one value-one AgentProf operation with source
step ID and target-blind fields. The exact semantic stack is:

```text
phase -> action_kind
```

- `phase` is exactly CodeTracer's target-blind `ClassificationStore.classify`
  output: `change` or `explore`, using its published default regex and an empty
  experiment-local store; no LLM fallback or persisted user classification.
- `action_kind` is assigned by Python 3's `re` engine with `re.IGNORECASE`,
  using the first matching rule in the following frozen ordered table. Matching
  is over the complete raw action;
  structured bracketed tool names are kept in that string. The final fallback
  is `execute` for any non-empty action and `other` only for an empty action.

  ```text
  1 communicate:
    COMPLETE_TASK|SUBMIT_FINAL|\[(SendMessage|AskUser|TaskOutput|TaskStop)\]
  2 version-control:
    (?:^|[;&|\s])(?:git|gh)(?:\s|$)
  3 install:
    pip3?\s+install|uv\s+add|poetry\s+add|npm\s+(?:install|i)|yarn\s+add|pnpm\s+add|apt(?:-get)?|yum|dnf|brew\s+install|cargo\s+add
  4 test:
    pytest|python3?\s+-m\s+pytest|cargo\s+test|go\s+test|npm\s+test|yarn\s+test|pnpm\s+test|ctest|mvn\s+test|gradle\s+test|make\s+test
  5 edit:
    str_replace_editor\s+(?:str_replace|create|insert|undo_edit)|\[(?:Write|Edit|NotebookEdit|FileWrite|FileEdit)\]|apply_patch|sed\s+-i|(?:^|[;&|\s])(?:tee|touch|mkdir|rm|mv|cp|chmod|chown)(?:\s|$)|(?:^|[;&|\s])cat\s.*(?:>|<<)|(?:^|[;&|\s])echo\s.*>
  6 search:
    \[(?:Grep|Glob|WebSearch|WebFetch)\]|(?:^|[;&|\s])(?:rg|grep|find|fd|locate)(?:\s|$)
  7 inspect:
    str_replace_editor\s+view|\[(?:Read|FileRead|recall)\]|(?:^|[;&|\s])(?:cat|sed|head|tail|less|more|ls|pwd|stat|file|wc|du|df|ps|which)(?:\s|$)
  8 execute: any remaining non-empty action
  9 other: empty action only
  ```

  No rule may be added, reordered, or reworded after any verified label is
  joined. The six-source-variant dependency check and complete 992-archive
  verified-source audit exercised this fixed mapping before the end-to-end
  label join. REAL PREFLIGHT then verified the semantic, raw-action, and phase
  stacks through release AgentProf. Coverage is reported, never repaired from
  labels.

No outcome, task/category, observation status, annotation stage, or target word
appears in this stack.

For each matching stratum and view, AgentProf folds operation count separately
for failed and successful reference cohorts. For group `g`:

```text
score(g) = failed_count(g) / failed_total
           - successful_count(g) / successful_total
```

Scores are not clipped. An unseen target group receives neutral score zero.
Each target receives exactly one score table from its selected supported
target-specific stratum; scores are never macro-averaged across alternative
fallback strata. Target operations do not update counts.

### Main baselines

1. **Raw-action grouping:** the lowercase basename of the first non-wrapper
   executable in the action (`env`, `sudo`, `timeout`, `command`, `bash -c`, and
   `sh -c` are skipped); a structured bracketed tool name wins when present.
   Arguments, paths, flags, and later pipeline/compound commands are removed.
   Empty actions map to `other`. The resulting key is passed through the same
   lowercase `safe_frame` normalization used by release AgentProf, and the
   independent scorer must use that emitted key rather than a pre-normalized
   alias. This represents ordinary log aggregation. If it matches or wins,
   semantic normalization has not earned its abstraction.
2. **CodeTracer phase-only grouping:** exactly the official target-blind
   `ClassificationStore.classify` output, `change` or `explore`, using commit
   `2d302191dd07e7c0c2da6f7a5e9451c7cbb62d34`, its published default regexes,
   an empty store, and no LLM. It is a real released alternative abstraction
   and tests whether the second semantic frame adds value beyond two-way
   coarsening.

Both baselines receive the same raw operations, matching strata, outcome
cohorts, differential equation, and metric implementation.

### Controls and external references

- **Flat/global:** one group and full inspection; lower bound.
- **Per-session:** trajectory identity; conventional per-run drilldown. It is a
  control, not a strongest localization baseline.
- **Framework-native action/episode:** raw OpenHands event, SWE `.traj` turn,
  Terminus episode, or MiniSWE command-response step identity. Because the
  released parsers normalize these mostly to command-bearing `StepRecord`s,
  this is a descriptive control; any cell identical to raw-action or session is
  merged and reported once.
- **Target-blind CodeTracer tree:** official `TreeBuilder.build` is reported as
  a single-run navigation control only. Its action-text labels and step-specific
  paths are not converted into a purported recurrent cross-run baseline.
- **Frequency-matched non-semantic partition null:** before projecting outcome
  or annotation fields, compute the semantic view's occupied group count `K`
  and sorted operation-mass shares over all raw-available actions. Generate
  10,000 SHA-256 partitions of the **normalized raw-action baseline key** into
  `K` buckets using integer seeds `4202..14201`. Encode
  `decimal_seed + NUL + raw_action_key` as UTF-8, take the first eight digest
  bytes as an unsigned big-endian integer, and assign it modulo `K`; bucket
  labels are zero-padded `bucket-00` onward. Discard partitions with an empty
  bucket. Sort each partition's and the semantic view's mass shares descending,
  rank candidates by `(L1 distance, integer seed)` ascending, and retain the
  first 200. Each retained partition receives the identical
  task-held-out outcome scoring and metrics. Report the semantic paired-AP
  difference against the full 200-partition distribution. Seed selection uses
  actions and mass only—never outcome, task result, or annotations.
- **Absolute hotspot:** operation-count ranking without any `solved` outcome for
  the semantic and strongest main-baseline views.
- **Outcome null:** permute `solved` at trajectory level within the mutually
  exclusive `(agent, model, difficulty, category)` cells, preserving every
  covariate used by the observed estimator and each trajectory's
  operations and the group-size multiset, then reapply same-task exclusion,
  cohort minimums, fallback, and profile scoring 2,000 times. This breaks
  group-outcome association without breaking trajectories or admitting the
  target task.
- **Annotation stage:** one oracle upper bound after terminal label join. Direct
  label grouping is omitted as trivial.
- **Published CodeTracer:** cite its Bare LLM/Mini-CodeTracer/CodeTracer
  P/R/F1/token results as direct-diagnosis references, not equally informed
  matched rows.

## Metrics And Tie Semantics

### Primary estimand

The primary estimand is pooled hidden-incorrect-step concentration across all
405 source-valid failed verified trajectories. A profile exposes complete
groups, not an invented order inside a group.

Distinct score values form tie blocks. Groups within a tie block are exposed
together. Inspection work is the number of unique source steps exposed divided
by all source steps in the primary population. No group or tie block is exposed
fractionally and no hash order is invented. Recall at 30% uses the last complete
block whose cumulative work does not exceed 30%; work to 50% recall uses the
first complete block whose cumulative recall reaches at least 50%.

- **Primary inferential metric:** tie-aware pooled average precision, computed as the sum
  of precision after each score block times that block's recall increment.
- **Operating summary 1:** pooled recall at 30% exposed-step work under the
  complete-block rule. This is an AgentProf inspection budget, not a CodeTracer
  cutoff.
- **Operating summary 2:** pooled exposed-step work required for 50% recall.
- **Primary comparator:** the stronger of the two main baselines by AP; semantic
  profiling must beat each main baseline on AP with a positive paired 95%
  percentile-bootstrap interval. R@30%, work@50%, the full curve, and the
  frequency-matched partition null must support the same interpretation but is
  not a separate conjunctive significance gate.

### Compatibility and secondary metrics

- Apply CodeTracer's per-instance P/R/F1 equations at the AgentProf 30% group-
  block budget and macro-average only across failed verified trajectories with
  at least one hidden incorrect step. Separately report false-positive exposed
  work on failed trajectories with `|G|=0`; never encode their undefined AP,
  recall, or work@50% as zero or silently delete them.
- Report incorrect-step results by framework. Bootstrap draws unique task
  clusters jointly from the full population, preserving verified membership;
  for each sampled target it again removes every reference draw with the same
  task. It recomputes support fallback, profiles, scores, rankings, metrics, and
  paired method differences for 10,000 replicates. Report percentile 95% CIs.
- Report `unuseful` and union results with the same frozen outputs only as
  secondary descriptive analyses, partitioned by the annotation-eligible
  population. They do not select fields, score, cutoff, or primary verdict.
- Secondary usability measures are groups exposed, unique groups, first-
  positive work, extraction/profile wall time, and total download/storage.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| availability | source boundary | all 3,316 manifest rows | official Hub tree vs artifact path and ID | one complete pass | fixes the 3,291-row raw-available population before labels |
| extraction | dependency inside experiment | all 3,291 official raw archives | four frozen source-step adapters above, reusing official parser logic | one complete pass | any unresolved alignment invalidates affected framework cell |
| reference | proposed/baseline input | per-target task-held-out, source-valid subset of the raw-available full-manifest outcome-bearing rows | per-stratum failed/success profiles | deterministic | estimates target-blind group scores without target/same-task reuse |
| main | proposed | all 405 source-valid failed verified rows | semantic stack | deterministic | tests the construction |
| matched baselines | main baseline | identical reference/test operations | raw-action and target-blind CodeTracer phase | deterministic | tests semantic value against real alternatives |
| controls | control | identical operations | flat, session/native, CodeTracer tree, 200 frequency-matched non-semantic partitions, absolute hotspot | deterministic / 200 partitions | interprets grouping and outcome contributions |
| null | control | task-held-out reference population | exact `(agent,model,difficulty,category)`-cell trajectory-outcome permutation with complete recomputation | 2,000 | rejects generic grouping/cohort explanation |
| uncertainty | analysis | reference + failed verified populations | task-clustered paired bootstrap | 10,000 | estimates comparison uncertainty |
| oracle | upper bound | scored failed verified rows | annotation stage | deterministic | calibrates headroom only |

## Execution And Completion

- **Shared deterministic-path command:**

  ```bash
  python3 script/codetracebench_agentprof_eval.py full \
    --full-manifest .agentsight/experiments/codetracebench-rq2/manifests/full.parquet \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --raw-root .agentsight/experiments/codetracebench-rq2/hub \
    --codetracer-root .agentsight/experiments/codetracebench-rq2/CodeTracer \
    --agentpprof-bin agentpprof/target/release/agentpprof \
    --out docs/visexp/out/codetracebench-rq2
  ```

  This command now runs the same source extraction, release-AgentProf
  verification, matching, scoring, pre-label prediction, terminal label join,
  and deterministic primary metrics as REAL PREFLIGHT. It is not yet the
  complete declared experiment: frequency-matched controls, 2,000 outcome-null
  trials, and 10,000 task-clustered bootstraps must be implemented and included
  in the final full-run command before execution. The scorer derives every
  stack from the exact operation fields and refuses completion unless every
  recomputed stack weight matches AgentProf JSON exactly.
- **Real preflight:** completed with **PASS** on six source-valid verified
  targets covering the six released source variants across four frameworks.
  Selection used only framework, source layout, failed outcome, and
  deterministic trajectory-ID order—never hidden step labels. The shared path
  loaded 3,316 full and 1,000 verified safe-projection rows; retained 1,077 of
  1,328 candidate references and all 6 targets; processed 36,125 reference
  operations and 270 target operations; matched targets at support levels
  1/4/1; invoked release AgentProf for semantic, raw-action, and phase views;
  wrote predictions before loading `incorrect_stages`; and computed pooled
  tie-block metrics. The report is
  `docs/visexp/out/codetracebench-rq2/real-preflight/report.md`. Its six-target
  metric sign is an engagement diagnostic, not evidence or a gate on the fixed
  hypothesis. Independent implementation re-review remains required before the
  full run.
- **Full completion:** terminal source-availability status for all 3,316
  manifest rows, followed by extraction status for all 3,291 published raw
  archives and all 146,177 raw-available declared steps; exact one-to-one source
  step-ID alignment within every
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
  with positive paired 95% intervals; its R@30%, work@50%, full inspection
  curve, frequency-matched partition null, and outcome null support a semantic rather
  than generic-coarsening interpretation; and the effect is not driven by one
  framework. Admit this coding-agent condition as direct RQ2 evidence and
  replicate the frozen construction.
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
