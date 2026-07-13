# Serial Experiment-Plan Review

## Round 1 — Scientific Estimand, Leakage, And Metric Review

**Started:** 2026-07-12T20:35:00-07:00  
**Completed:** 2026-07-12T20:43:00-07:00  
**Reviewer:** fresh independent subagent explicitly using
`research-experiment-design`  
**Plan reviewed:** revision 0  
**Verdict:** **REVISE**

### Material findings

The reviewer accepted CodeTraceBench as the correct real public source and
accepted that one complete experiment may test only one construction inside
fixed RQ2. It found eight blocking defects:

1. CodeTraceBench's annotation protocol is outcome-dependent: failed runs carry
   backward-traced incorrect/error-critical steps, while successful runs are a
   main source of redundant/unuseful annotation. A single failed-minus-success
   score cannot make `incorrect`, `unuseful`, and their union one homogeneous
   primary estimand.
2. Framework-only differential scoring did not control model, difficulty, or
   task/category composition; the semantic stack also received task category
   while other views did not.
3. flat-step and per-session groups degenerated into singleton outcome proxies
   rather than meaningful strongest baselines.
4. stable-hash tie breaking invented within-group localization that the profile
   did not produce and interacted unfairly with grouping granularity.
5. CodeTracer publishes per-instance P/R/F1 equations and a shared fixed
   implementation budget, not a 30% cutoff. Zero-positive trajectories and
   empty predictions were undefined.
6. the proposed null preserved group/cohort association instead of breaking it;
7. the official code contains annotation-reading paths, including
   `build_from_annotation`; the parser whitelist, target-blind phase definition,
   and exact step-ID alignment rule were too weak;
8. the intended top-level runner and exact command did not yet exist.

### Root response and revision decision

All eight findings are accepted as scientific or executability defects. Plan
revision 1 makes the smallest coherent repair:

- primary target becomes hidden `incorrect` steps in failed verified runs;
  `unuseful` and union remain predeclared secondary analyses and cannot decide
  the primary verdict;
- the disjoint 3,316-trajectory full split becomes the outcome-bearing reference
  corpus; verified-run outcome and operations never estimate their own scores;
- scoring strata use agent, model, difficulty, and category, with a predeclared
  fallback, while category is removed from the semantic stack;
- main baselines become raw-action and the official target-blind CodeTracer
  tree; flat and session are controls;
- metrics advance by complete equal-score group blocks with fractional
  interpolation, never hash order;
- primary metrics are pooled tie-aware AP, recall at 30% work, and work to 50%
  recall over failed verified runs; per-instance CodeTracer P/R/F1 equations are
  compatibility analyses on positive-bearing trajectories, and zero-positive
  false-positive burden is separate;
- the null permutes full-split `solved` outcomes at trajectory level within
  matching strata and recomputes the complete score;
- only official seed parsers, `TreeBuilder.build`, and an isolated empty
  classification store are permitted; annotation paths/functions are forbidden;
- any missing, duplicate, reordered, or mismatched source step ID invalidates
  the affected framework cell;
- the execution command and stack fields are fixed in revision 1; implementation
  must exist and pass later review before preflight.

This revision does not narrow RQ2 or change the paper story. It makes one
decisive experiment scientifically identifiable.

## Round 2 — Source Identity, Matching, Baseline, And Execution Review

**Started:** 2026-07-12T20:48:00-07:00  
**Completed:** 2026-07-12T20:56:00-07:00  
**Reviewer:** fresh independent subagent explicitly using
`research-experiment-design`  
**Plan reviewed:** revision 1  
**Verdict:** **REVISE**

### Decisive source-fidelity finding

The reviewer queried the official `full` and `verified` Parquet manifests rather
than trusting their split names. `verified` is an exact subset of `full`:

- all 1,000 verified `traj_id` values occur in full;
- all 1,000 projected rows are column-for-column identical;
- 993 non-null artifact paths and 989 non-null source paths overlap;
- the union is 3,316 unique trajectories and 147,628 steps, not 4,316 and
  194,167.

Revision 1 therefore put every target trajectory's own operations and `solved`
outcome into the profile used to score that trajectory. This is direct feature
and outcome leakage even though hidden step annotations were withheld.

As a diagnostic, removing the complete verified subset leaves 2,316 reference
trajectories and 101,089 steps. Of the 468 failed targets, 28 then lack both
outcome cohorts even at `(agent,model)` and half of the 440 matched targets have
at most two trajectories in their smaller cohort. Revision 1's advertised
matching coverage was inflated by self-inclusion.

### M1–M8 disposition

1. **M1 partially closed, still blocking:** `incorrect` is now the sole primary
   target, but reference/test self-inclusion invalidates the estimator.
2. **M2 not closed:** category left the semantic stack, but one- and two-row
   cohorts make the nested matching unstable; the phrase “macro-average where a
   group appears” did not assign a unique score table to each target.
3. **M3 partially closed:** flat and session are now controls and raw-action is
   credible. `TreeBuilder.build`, however, creates a per-run navigation tree
   with action-derived labels and step IDs, not a published recurrent grouping.
4. **M4 partially closed:** hash ordering was removed, but atomic tie-block
   exposure contradicted fractional interpolation through the same block.
5. **M5 mostly closed:** 30% is correctly an AgentProf operating point and
   zero-positive handling is explicit, but three arbitrary conjunctive metric
   gates were unnecessarily brittle.
6. **M6 incomplete:** outcome permutation is sound in direction, but nested
   fallback strata are not mutually exclusive permutation cells.
7. **M7 partially closed:** parser restrictions improved, but the `action_kind`
   vocabulary lacked frozen ordered rules, CodeTracer tree mapping was missing,
   and 25 full rows—including eight verified rows—had null artifact paths.
8. **M8 not closed:** the named runner still did not exist, although the current
   AgentProf operation-file and stack primitives make implementation feasible.

The reviewer also required a frequency/cardinality-matched non-semantic control
so a win over raw actions cannot be explained merely by compressing thousands
of keys into 18 buckets; paired method-difference bootstrap intervals; one
mutually exclusive permutation partition; exact raw-action normalization; and
resolution of raw artifact availability before full execution.

### Root response and revision-2 decision

All scientific findings are accepted. The reviewer proposed `full - verified`
as the smallest fixed reference. The root instead adopts the reviewer's
explicitly valid stronger alternative: **per-target leave-task-out scoring**.
For each target, every full row with the same `task_name` is removed, so neither
the target nor a same-task near-neighbor contributes features or outcome. A
manifest-and-Hub audit also proves that 25 manifest rows have no published raw
archive, including eight verified rows and seven failed verified rows. They are
excluded by source availability before label projection, leaving 3,291 raw-
available full rows and 461 failed primary targets. A 10-per-outcome support
minimum assigns all 461 targets without coarser-than-`(agent,model)` fallback:
134 at `(agent,model,difficulty,category)`, 83 at `(agent,model,category)`, and
244 at `(agent,model)`.

Revision 2 additionally:

- corrects all unique population and step counts and records the source error in
  the literature node;
- freezes the ordered semantic regex table and exact raw-action normalization in
  Markdown before label join;
- makes raw-action and official CodeTracer phase-only grouping the two main
  baselines, demotes the per-run CodeTracer tree to a control, and adds a fixed
  18-bucket SHA-256 non-semantic control;
- uses complete tie blocks with no interpolation or invented within-block order;
- makes block AP the sole inferential metric and keeps R@30%, work@50%, and the
  full curve as operating summaries;
- uses mutually exclusive `(agent,model)` outcome-permutation blocks and joint
  task-clustered paired bootstraps with full score recomputation.

The fixed RQ2, four-RQ program, positive hypothesis, and AgentProf thesis are
unchanged. Revision 2 now requires an independent Round-3 review before any
runner implementation or preflight.

## Round 3 — Executable Mapping And Null Semantics Review

**Started:** 2026-07-12T21:03:00-07:00  
**Completed:** 2026-07-12T21:08:00-07:00  
**Reviewer:** fresh independent subagent explicitly using
`research-experiment-design`  
**Plan reviewed:** revision 2  
**Verdict:** **REVISE**

The reviewer independently reproduced the exact full/verified subset relation,
3,291/992 raw-availability boundary, 461-target primary population, task-held-
out exclusion, and 134/83/244 supported fallback counts. It accepted the
complete-block metrics, zero-positive handling, task-clustered paired bootstrap,
and absence of the runner as an implementation dependency rather than a reason
to reject the scientific plan. Three definitions remained blocking:

1. **B1 — regex engine and SWE-agent engagement.** Revision 2 used POSIX
   whitespace syntax that Python `re` does not implement as intended and did
   not recognize official SWE-agent actions such as
   `str_replace_editor view` and `str_replace_editor str_replace`. This would
   collapse real inspection and editing into `explore -> execute`.
2. **B2 — falsely “cardinality-matched” control.** One 18-bucket hash seed
   matched only a theoretical maximum group count, not occupied groups, group
   mass, target-specific sizes, or random-partition variation. It could not
   support a semantic-versus-generic-coarsening conclusion.
3. **B3 — covariate-breaking outcome null.** Permuting only within
   `(agent,model)` destroyed difficulty/category composition that the observed
   estimator conditions on, potentially making ordinary cohort composition look
   significant.

### Root response and revision-3 decision

All three findings are accepted and repaired without changing the experiment:

- the plan names Python 3 `re` with `re.IGNORECASE`, replaces every POSIX class
  with executable syntax, and adds frozen target-blind SWE-agent view/edit
  rules;
- a source-only audit using one official raw archive per framework confirms 10,
  5, 9, and 9 distinct semantic stacks for MiniSWE, OpenHands, Terminus2, and
  SWE-agent respectively before any label join;
- the single hash row is replaced by 200 pre-label random partitions selected
  from 10,000 seeds to match both occupied semantic cardinality and sorted
  operation-mass shares as closely as possible;
- outcome permutation now occurs inside mutually exclusive
  `(agent,model,difficulty,category)` cells and then recomputes the complete
  support/fallback estimator.

Revision 3 requires Round-4 independent review. No runner implementation begins
until that verdict is recorded.

## Round 4 — Source-Unit And Determinism Review

**Started:** 2026-07-12T21:13:00-07:00  
**Completed:** 2026-07-12T21:18:00-07:00  
**Reviewer:** fresh independent subagent explicitly using
`research-experiment-design`  
**Plan reviewed:** revision 3  
**Verdict:** **REVISE**

Round 4 accepted the repaired Python-regex/SWE engagement, pre-label frequency-
matching principle, and exact-cell outcome-null principle, but found three
remaining execution ambiguities:

1. permitting thin adapters did not specify which raw units MiniSWE, OpenHands,
   and Terminus2 include; matching only final `step_count` could create a false
   alignment;
2. the frequency null did not identify whether its key was the full action or
   normalized baseline key, nor its byte encoding, digest-to-bucket rule, or
   deterministic cutoff tie-break;
3. the Planned Runs table retained stale `(agent,model)` permutation text even
   though the normative section had moved to exact four-covariate cells.

### Root response and revision-4 decision

All three are corrected mechanically:

- four source-format step rules now fix inclusion, exclusion, ordering, and IDs.
  MiniSWE uses visible numbered action segments plus an explicit terminal raw
  event only for the observed `N+1` form; OpenHands includes all non-bookkeeping
  agent actions; Terminus2 emits each ordered `commands[]` element and excludes
  its non-JSON bootstrap response; SWE-agent emits each `.traj` element;
- the partition null now hashes the normalized raw-action baseline key using
  UTF-8 `decimal_seed + NUL + key`, the first eight SHA-256 bytes as an unsigned
  big-endian integer modulo `K`, and ranks candidates by `(L1 distance, seed)`;
- the Planned Runs table now repeats the exact
  `(agent,model,difficulty,category)` permutation cells.

Revision 4 requires Round-5 independent review. The RQ, tested hypothesis,
metrics, population, and paper story remain unchanged.

## Round 5 — Final Executability Review

**Started:** 2026-07-12T21:22:00-07:00  
**Completed:** 2026-07-12T21:27:00-07:00  
**Reviewer:** fresh independent subagent explicitly using
`research-experiment-design`  
**Plan reviewed:** revision 4  
**Verdict:** **PASS**

The final reviewer read the complete plan, all prior rounds, and both source
audits. It found all Round-4 blockers closed:

- the four source-step adapters uniquely specify inclusion, exclusion, order,
  one-based IDs, target-blind fields, and invalidation on mismatch;
- the frequency-matched partition null uniquely fixes normalized key, UTF-8
  seed/NUL/key bytes, SHA-256 interpretation, modulo bucket assignment, empty-
  bucket rejection, mass-distance ranking, seed tie-break, and retained set;
- both the normative outcome-null definition and Planned Runs table use exact
  `(agent,model,difficulty,category)` cells with full estimator recomputation.

It also confirmed that the 461-target estimand, task-held-out estimator, source
availability boundary, supported matching, information-fair baselines, block
metrics, paired task bootstrap, annotation boundary, command, completion rules,
and paper decisions are all defined. The runner's absence and real adapter
validation are correctly next-stage dependencies, not reasons for another plan
revision.

**Decision:** plan review is closed after five serial rounds. Proceed to runner
implementation, independent implementation review, REAL PREFLIGHT, and then the
complete run. No RQ, thesis, contribution, or paper-story change is authorized.
