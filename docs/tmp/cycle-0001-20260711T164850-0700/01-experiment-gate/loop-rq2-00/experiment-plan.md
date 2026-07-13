# Experiment Plan: RQ2 Cross-Family Problem Localization

## Research Question and Claim

- **Immutable RQ:** Does profiler output correspond to real problems?
- **Paper-level RQ ID:** RQ2 of 4.
- **Parent hypothesis:** Query-time operation stacks are not merely a rendering
  format; their multi-resolution grouping should concentrate failures, unsafe
  actions, repetition, and redundant work into inspectable profile groups across
  heterogeneous agent trajectories.
- **Current expected conclusion claim:** With the target trajectory family fully
  held out, AgentProf's visible-field operation-stack profiler achieves a better
  localization/inspection/fragmentation Pareto tradeoff than flat summaries,
  session drilldown, fixed sequential/native hierarchies, raw-action grouping,
  and equally informed SQL/tag aggregation.
- **Conclusion-claim revision:** 0.
- **Plan review round:** 4.
- **Scope:** Public real-world agent and human-agent trajectories with
  dataset-provided problem annotations. Human boundary labels are excluded from
  this experiment because a boundary is not itself a problem.
- **Decision informed:** Whether the paper can retain RQ2 as a central positive
  empirical contribution for AAAI-27, and whether the novelty is the adaptive
  operation-stack mechanism rather than ordinary multi-column aggregation.

## Hypothesis

- **Main hypothesis:** Given identical label-free per-operation risk scores,
  adaptive operation-stack groups concentrate positives at lower inspection work
  and lower fragmentation than fixed grouping shapes on unseen trajectory
  families.
- **Strongest competing explanation:** All apparent gains come from task-specific
  visible features or post-hoc ranker choices; an equally informed SQL rollup,
  fixed hierarchy, raw-action view, or session view performs as well or better.
- **Falsifying result:** On held-out families, adaptive operation stacks are not
  on the non-oracle Pareto frontier, or they fail to improve either work-to-fixed-
  recall or groups-to-fixed-recall without losing AP/AUPRC relative to the
  strongest fixed baseline.

## External Grounding

- **Published protocols:** AgentRewardBench evaluates 1,302 expert-reviewed web
  trajectories with success, side-effect, and repetition annotations; AgentRx
  evaluates critical failure-step localization on 115 manually annotated failed
  trajectories across API, incident-management, and multi-agent web/file domains;
  TELBench/DRIFT uses span-level localization on real deep-research trajectories.
  This experiment reuses their principle that trajectory diagnosis must be scored
  against annotations hidden from the diagnostic method.
- **Official assets:** Existing official-source conversions for AgentRewardBench,
  SATraj-OS, and AgentNet are development data. Confirmatory evaluation uses two
  previously unused official releases: Microsoft's AgentRx repository and its
  manually annotated critical failures, and NJU-LINK's 1,000-instance TELBench
  release with ordered semantic spans and harmful-error-span annotations.
  OSWorld-Human grouped boundaries remain outside RQ2.
- **Reused procedure:** Family-held-out scoring, step/operation-level labels,
  per-task localization metrics, and three-run/uncertainty reporting where the
  learned ranker is stochastic.
- **Necessary deviation:** AgentProf ranks groups rather than predicting exactly
  one critical step. AgentRx step labels are therefore scored both at operation
  rank and at group-inspection rank. The public AgentRx release currently exposes
  44 Magentic-One and 29 Tau ground-truth trajectories; this experiment makes no
  claim about the unreleased third domain. The primary AgentRx positive is the
  single failure referenced by each row's official `root_cause.failure_id`;
  localization of any annotated recoverable-or-critical failure is secondary.
  Thin custom code only converts released trajectories to AgentProf operations
  and computes the common metrics.

## Comparison

- **Proposed method:** AgentProf adaptive operation-stack induction over visible
  operation fields, with maximum depth selected only from non-target families.
  Query terms come from the task description, not hidden labels or target
  outcomes.
- **Strongest runnable baselines:**
  1. random operation inspection;
  2. flat summary;
  3. per-session grouping;
  4. dataset-native hierarchy;
  5. raw action/status grouping;
  6. fixed sequential hierarchy (trajectory, development-selected chronological
     window, operation), which gives both confirmatory families a fixed-boundary
     trace-shaped control without inventing parent/child metadata;
  7. equally informed multi-column SQL/tag grouping and SQL `ROLLUP` over the same
     visible fields;
  8. query/text tag grouping: bin the identical precomputed operation-risk score
     with development-selected thresholds, then group by role plus risk tag;
  9. explicit fixed-depth AgentProf operation stack;
  10. oracle label drilldown as a non-deployable upper bound.
- **Native closest-work rows:** On all 1,000 TELBench cases, run the official
  NJU-LINK evaluator for both official `bare` and `drift` settings using the same
  local Qwen2.5-3B-Instruct GGUF served through llama.cpp's OpenAI-compatible
  endpoint. These native LLM rows are separate from the shared-score grouping
  ablation and report macro/micro precision, recall, F1, first-error accuracy,
  tokens, and wall time. The TELBench paper's published stronger-model results are
  contextual anchors, not substituted for local runs. AgentRx's official code
  supports Azure, TRAPI, or Copilot backends, none currently available in this
  environment; unless a repository-supported backend becomes available before
  execution, its published same-dataset numbers are explicitly non-head-to-head
  context and AgentProf does not claim superiority over AgentRx.
- **Information and tuning fairness:** Every deployable view receives the same
  normalized operations, visible fields, task description, operation-level risk
  scores, and non-target-family tuning budget. Only the grouping shape differs.
  The SQL baseline may use every field AgentProf uses. Depth, aggregation, and
  rank aggregation choices are selected on training families and applied unchanged
  to the held-out family.
- **SQL definition:** Development chooses one disjoint SQL partition from a
  bounded list of canonical allowlisted columns: `(role)`, `(role, action)`,
  `(role, action, tool_status)`, or `(role, phase, action, tool_status)`.
  Missing values use one common `unknown` value. The chosen `GROUP BY` is applied
  unchanged to both confirmatory families. SQL rollup prefix levels are each
  scored separately and never mixed into one ranking, so an operation is counted
  once per reported view.
- **Development/confirmation split:** AgentRewardBench, SATraj-OS, and AgentNet
  are explicitly development-only because prior R320/R329/R403/R404 work has
  inspected their outcomes. They may select the single ranker, score aggregation,
  induced depth, and explicit stack. AgentRx and TELBench are confirmatory and
  are not used for those choices.
- **Leakage rule:** Existing hand-written task-ID rankers are not used. A
  deployment-time provenance allowlist admits only raw operation order/time,
  actor/role, event-native tool/action names, redacted tool arguments or span
  text, event-native tool errors, and fields derived from those values without
  labels. It excludes benchmark reward, final success/status, annotations,
  critiques, judge output, failure reasons/categories, root-cause indices,
  looping/side-effect/safety labels, correctness/redundancy labels, human-group
  labels, and converter fields derived from any of them. Oracle values are joined
  only by the scorer after every group order has been produced.

## Workloads and Metrics

- **Development families/tasks:**
  - AgentRewardBench: looping and side-effect localization;
  - SATraj-OS: unsafe-operation localization;
  - AgentNet: incorrect-step and redundant-step localization;
- **Confirmatory families/tasks:**
  - AgentRx: critical-failure-step localization in each released domain with
    usable trajectory/annotation alignment (73 expected ground-truth rows across
    44 Magentic-One and 29 Tau rows in the current public repository);
  - TELBench: harmful semantic-span localization over all 1,000 released
    deep-research trajectories.
- **Primary metrics:** per-task AUPRC/AP; recall at 10%, 20%, and 30% inspected
  operations; work to 25% and 50% positive recall; groups to 25% and 50% positive
  recall. The headline result is a Pareto surface over recall, inspected work,
  and groups, not a single favorable metric.
- **Secondary metrics:** first-positive work, top-5 recall/precision, operation-
  level critical-step accuracy on AgentRx, group count, group-size distribution,
  and cold/warm execution time.
- **Ground truth:** Dataset-provided expert/human problem annotations. Labels that
  are proxies or deterministic derivations are identified per task and not pooled
  with independent expert labels without disaggregation.
- **Uncertainty:** Report every task and confirmatory domain, then macro-average
  across the two confirmatory families. Use 95% session/instance bootstrap
  intervals within each confirmatory family and three fixed training seeds. The
  development-family bootstrap is descriptive only.

## Predeclared Decision Criteria

The positive claim requires both absolute correspondence and relative advantage:

1. **Absolute correspondence:** on each confirmatory family, adaptive AgentProf
   AP/AUPRC exceeds the random/prevalence baseline by at least 0.05 absolute and
   the 95% instance-bootstrap lower bound of the improvement is above zero. It
   must also recover at least 50% of positives within 30% inspected operations.
2. **Relative tradeoff:** against the strongest deployable fixed/SQL baseline on
   each confirmatory family, adaptive AgentProf must satisfy one of three branches:
   (a) reduce work-to-25%-recall by at least 15%, with groups-to-25%-recall no
   more than 10% worse and AP loss no worse than 0.02; (b) reduce groups-to-25%-
   recall by at least 15%, with work-to-25%-recall no more than 10% worse and AP
   loss no worse than 0.02; or (c) improve AP by at least 0.03 while neither work
   nor groups is more than 10% worse. The macro result must have the same direction
   on both families.
3. **Semantic grouping beyond cardinality:** adaptive AgentProf must beat the
   median of 100 label-free contiguous matched partitions. Within each trajectory,
   each null partition preserves the exact AgentProf group-size multiset but
   randomly permutes cut-size order, keeping every group chronological and every
   operation assigned exactly once. It uses the identical materialized operation
   scores and group-score aggregation. The single primary matched-null metric is
   work-to-25%-recall: AgentProf must reduce it with the 95% matched-partition
   interval excluding equality. AP against the matched null is descriptive.

Failure of criterion 1 means profiler output has not been shown to correspond to
problems. Passing 1 but failing 2/3 supports correspondence only, not the claimed
operation-stack advantage.

## Common Label-Free Ranker

To isolate the grouping mechanism, one operation-level ranker is shared by all
deployable views. A TF-IDF plus regularized logistic
regression model consumes only normalized visible operation text/fields and the
natural-language task description. It is fitted on development families and emits
one risk probability per confirmatory operation. Those per-operation scores are
materialized before any grouping is run. Every view ranks groups with the same
single aggregation rule selected on development data; the rule is then unchanged
for AgentRx and TELBench. Width-only and unsupervised rarity are ranker ablations.
Hidden confirmatory labels never select features, model, aggregation, stack, or
depth.

## Planned Runs

| Run group | Workload | Methods | Repetitions | Purpose |
|---|---|---|---:|---|
| real preflight | One complete AgentReward development task; one unlabeled AgentRx trajectory; one TELBench case | proposed + SQL + session + raw action + matched partition; official bare + DRIFT on the TELBench case | 1 | Exercise conversion, allowlist, score materialization, grouping, matched control, scorer separation, llama.cpp, and official DRIFT paths without inspecting confirmatory outcomes |
| development selection | AgentReward + SATraj + AgentNet | all deployable views | 3 seeds | Select one ranker, aggregation, explicit stack, and induced depth without confirmatory data |
| confirmation A | AgentRx, all aligned released trajectories/domains | all deployable views + oracle upper bound + matched controls | 3 seeds | New critical-failure-step confirmation |
| confirmation B | TELBench, all 1,000 released instances | all deployable views + oracle upper bound + matched controls | 3 seeds | New harmful-span confirmation |
| native TELBench | TELBench, all 1,000 released instances | official bare + DRIFT with local Qwen2.5-3B | 1 complete run each | Same-task LLM localization baselines and cost context |
| ablation | both confirmatory families | shared ranker vs width vs rarity; induced vs explicit fixed depth | 3 seeds | Isolate ranking and adaptive grouping contributions |

## Execution

- **Authoritative paths:** Rust `agentpprof` is the proposed-system executor;
  official public datasets/repositories are the data sources; DuckDB-compatible
  SQL executed through Python's embedded SQL path or an installed DuckDB binary
  is the SQL baseline. Scikit-learn supplies the standard TF-IDF/logistic model.
  The official NJU-LINK DRIFT CLI and evaluator execute the TELBench native rows;
  `/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server` serves
  `/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf`.
- **Thin glue to add:** `script/operation_family_heldout_eval.py` will orchestrate
  existing operation converters, the Rust CLI, SQL grouping, common ranking, and
  scoring. It must not contain task-ID-specific scoring rules.
- **Real preflight:** First use complete real rows for one AgentReward development
  task, train only on another development family, run AgentProf plus SQL/session/
  raw-action/tag baselines and a contiguous matched partition, and recompute AP
  plus work-to-25%-recall. Then convert one AgentRx trajectory and one TELBench
  case without joining or inspecting their labels, run the real AgentProf path,
  and send that TELBench case through both official `bare` and `drift` settings
  using the actual llama.cpp server. Preflight outputs prove execution only and
  are excluded from confirmatory metrics; the same cases still participate in
  the full run under the unchanged preflighted code.
- **Full completion rule:** All development selection cells and every AgentRx/
  TELBench confirmatory view × seed × matched-control cell reach a terminal
  result. AgentRx must align all 73 currently released ground-truth trajectories
  unless a row lacks a corresponding released raw trajectory, in which case at
  least 50 trajectories spanning both public domains must remain and every
  exclusion is reported. TELBench grouping, `bare`, and `drift` runs must each
  process all 1,000 instances. Otherwise the
  experiment is incomplete, not a smaller positive result. The primary table
  includes every deployable baseline and each confirmatory domain/task. A
  preflight or partial prefix cannot satisfy completion.
- **Raw-result path:** `docs/visexp/out/rq2-family-heldout-r410/`.
- **Recovery:** Results are written per fold and seed so a failed fold can be
  rerun without discarding completed folds. Raw group rankings and per-task metric
  tables remain available for independent recomputation.

## Interpretation

- **Supportive:** Both predeclared absolute and relative criteria pass on AgentRx
  and TELBench, and matched controls reject group cardinality/size as the sole
  explanation.
- **Contradictory:** SQL rollup, raw action, native hierarchy, or session grouping
  matches/dominates adaptive operation stacks under the shared ranker. The result
  is admitted; RQ2's current positive conclusion is contradicted and the next
  outer REVIEW must demand a stronger semantic induction/localization mechanism
  before repeating RQ2.
- **Inconclusive:** Family intervals are wide or incompatible, AgentRx alignment
  is incomplete, or gains depend entirely on one proxy-labeled family. The paper
  cannot use a pooled positive headline.
- **Next larger experiment if supported:** A profile-guided intervention on fresh
  held-out real agent runs, testing whether identified groups lead to reductions
  in failures, safety violations, token cost, or wall time.
- **Target paper artifact:** One per-family table and one Pareto plot replacing
  the current median-only RQ2 table.

## Reproducibility Notes

- Record official dataset/repository versions, exact commands, scikit-learn and
  Rust tool versions, seeds, excluded rows, and ordinary raw paths in the result
  report.
- Do not introduce Git/hash gates, frozen packets, manifests, attestation, or
  non-Markdown control files. Dataset and result files remain ordinary experiment
  artifacts.
- The paper is not edited during this experiment loop. Admitted results return to
  WRITE and whole-paper REVIEW.
