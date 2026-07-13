# Experiment Plan: RQ2 Revision 1 — Scope Before Localization

## Research Question And Claim

- **Immutable RQ:** Does profiler output correspond to real problems?
- **Paper-level ID:** RQ2 of 4.
- **Parent:** RQ2 revision-0 admitted contradiction; risk-ranked induced leaf
  partitions failed on AgentRx and TELBench.
- **Current expected conclusion claim:** Across heterogeneous real agent traces,
  a query-conditioned semantic operation tree with risk-guided navigation
  concentrates real failures into small navigable scopes, and coarse-to-fine traversal improves
  final failure localization at equal inspection cost over flat scores, fixed
  windows, fixed-field and source-native hierarchies, random/matched scopes, and
  the revision-0 leaf-only method.
- **Conclusion-claim revision:** 1 of at most 2.
- **Plan review round:** 5.
- **Scope:** Structure-first failure-scope selection and downstream localization
  on fresh public Who&When and TRAIL traces. AgentRx/TELBench are now
  development/diagnostic data, not untouched confirmation.
- **Why it matters:** Revision 0 flattened every semantic path to a leaf. It
  therefore tested partition ranking rather than the proposed multi-resolution
  operation stack. This experiment tests the hierarchy itself without changing
  or narrowing RQ2.

## Hypothesis

- **Main hypothesis:** The first useful unit of debugging is a failure-containing
  semantic scope, not an independently ranked operation or leaf. The existing
  query-conditioned semantic boundaries expose multiple resolutions; expanding
  their highest-risk frontier recursively will localize errors with less trace
  inspection and fewer localizer tokens.
- **Strongest competing explanation:** Any gain comes only from selecting fewer
  operations, group width, the shared operation-risk model, or a generic
  two-stage prompt. Fixed/matched scopes, explicit field trees, or flat top-risk
  operations would perform equally well at the same operation/token budget.
- **Falsifying result:** On either fresh benchmark family, the proposed tree
  fails the predeclared scope, downstream localization, or
  hierarchy-beyond-cardinality criterion; or its advantage disappears against
  the same-risk matched tree/leaf-only ablation.

## External Grounding

- **SDBL, AAAI-26:** “Scope Delineation Before Localization” evaluates
  failure-containing scopes with Hit@K and then exact agent/step localization on
  Who&When. We reuse the two-stage construct, Hit@K, and same-localizer
  comparison. Its linked repository at commit
  `9734e4c26b34e677997df2f750a74ae69dd21e41` currently contains only “We will
  release it soon,” so any SDBL protocol baseline is explicitly a faithful
  reimplementation, not official code.
- **Who&When, ICML 2025:** Official repository commit
  `b2bae5c5b06d681d04ea5e9b63b7a30525c04925` provides 184 labeled failures,
  its evaluator, and all-at-once, step-by-step, and binary-search baselines.
- **TRAIL:** Official repository commit
  `0ffbed9db859b4a66250dc783fa4dccf86869595` provides 148 real OTel traces,
  exact error-span/category annotations, official prompts, and evaluator.
- **AgentRx and DRIFT/TELBench:** Their constraint/claim-centric diagnostic
  protocols motivate evidence-bearing scopes and supply consumed development
  families. They are not relabeled as fresh confirmation.
- **Custom code boundary:** Conversion, score materialization, equal-budget scope
  adapters, and metric aggregation are thin experiment glue. Risk-conditioned
  induction and multi-resolution navigation belong in the real Rust `agentpprof`
  path, not a toy Python replacement.

## Proposed Method

1. Convert each trace into chronological visible operations. Materialize one
   operation-risk score from a model trained only on the prior development
   families.
2. Preserve the existing Rust structural, label-quality, query, balance, and
   semantic-shift boundary objective. Supply a declared numeric
   `diagnostic_risk` field only to navigation and force it out of induction
   candidates; confirmation labels never become fields or objective inputs.
3. Preserve every internal prefix and its original-operation membership. Do not
   collapse paths to leaf keys.
4. Treat the root as navigation state, never as a selected scope. Maintain a
   disjoint frontier ordered by node mean risk. Expanding an internal node exposes
   no operation content to the localizer and replaces that frontier node with its
   children. Expanding a terminal node emits one non-overlapping scope containing
   its original operations. Ties use incoming split score, narrower width, then
   structural node ID. This yields one deterministic order over terminal scopes
   and, within each terminal scope, operations by risk then original position.
5. Define two comparable outputs from that order. `Step-Hit@K` uses exactly the
   first `K` emitted atomic operations, matching the published Who&When/SDBL
   construct. `GoldRecall@B` and downstream localization use exactly the first
   `B` unique atomic operations; when a budget ends inside the next terminal
   scope, only its highest-risk remaining operations fill the budget. A separate
   descriptive `ScopeHit@n` reports the first `n` whole terminal scopes together
   with their actual operation and token work; it is never compared to
   SDBL's step-level `Hit@K` or used alone to pass the claim.
6. In the primary same-localizer comparison, give Qwen2.5-7B-Instruct only the
   query and selected original operations in their source order. Internal
   summaries and semantic breadcrumbs are not shown, so unseen operation content
   cannot enter through an uncharged summary. A secondary labels-enabled analysis
   may expose each method's native scope label, charged by serialized tokens, but
   cannot establish the primary claim. Use strict dataset-specific output schemas
   and exact scorers for final locations/categories.

Budget construction is deterministic per trace. An operation fraction `f` uses
`max(1, ceil(f * number_of_eligible_operations))` complete operations. A token
fraction uses `max(1, floor(f * complete_scrubbed_trace_tokens))` tokens; walk the
method's ordered operation list and stop before the first complete serialized
operation that would exceed the cap—never truncate it and never skip it to admit
a later operation. The localizer still runs when this yields zero operations.
Quality AUC is the trapezoidal integral through the directly measured points
`{5%,10%,15%,20%,30%}`, divided by `0.30-0.05`; use linear segments only between
adjacent observed points and no extrapolation.

Development selects only: maximum depth from `{2, 3, 4}`; minimum child weight
from `{2, 3, 5}`; navigation aggregation from `{max, mean, top-quartile mean}`;
and scope budgets from the published SDBL `K={3,5,7,9}` plus operation fractions
`{5%,10%,15%,20%,30%}`. Confirmation never changes these choices. The primary
navigation rule remains plain mean risk unless development clearly selects a
different predeclared aggregation.

## Data, Visibility, And Leakage

### Development and mechanism selection

Use only the already consumed AgentRx and TELBench families for revision-1
configuration selection. Select exactly one cross-family configuration; never
select separate settings for Who&When and TRAIL. No Who&When or TRAIL outcome,
label, subgroup result, or context-failure pattern can change it. Revision-0
results remain visible as negative development evidence.

The operation-risk scorer is fixed before confirmation. It is scikit-learn
TF-IDF over lowercased word unigrams/bigrams (`min_df=2`, at most 12,000
features) followed by class-balanced logistic regression (`liblinear`, at most
1,000 iterations, seed 410). Development positives are the official AgentRx root
cause step and every TELBench annotated error span; all other eligible operations
are negatives. Each record contains only the task question and the shared visible
fields `role`, `tool`, `action`, `phase`, `op`, `repeat_signal`, `repeat_state`,
`tool_status`, `length_bucket`, `query_overlap`, and scrubbed operation content.
No benchmark/file/span/step ID or outcome field enters text or features.

Assess that fixed scorer and every structural candidate in both leave-one-family-
out directions. For each family and candidate, compute
`0.5 * GoldRecall@20% + 0.5 * normalized recall/work AUC through 30%`; select the
candidate maximizing the lower of the two family scores. Break ties by larger
equal-weight family mean, then fewer expanded nodes at 20% work, then shallower
depth, larger minimum-child weight, and lexical aggregation name. Use the same
objective to choose one fixed-window size. Then fit once on the union of AgentRx
and TELBench and store the vectorizer/model, training summary, and selected
configuration under
`docs/visexp/out/rq2-scope-before-localization-r1/development/`. Seeds 411–412
are sensitivity runs, not model selection. The confirmation checkpoint is never
refit. Every equal-information structural method receives the identical stored
per-operation scores. Report scorer training/inference time once as shared cost
and include it in end-to-end AgentProf cost, not as a differential advantage.

### Fresh confirmation A: Who&When

- All 184 released files: 58 Hand-Crafted and 126 Algorithm-Generated.
- Primary visible fields: `question`, chronological `history` content, actor
  `name` or `role`, source order, subset, and file ID. `system_prompt`, `level`,
  and `question_ID` are excluded from ranking and localization; `question_ID` is
  used only to cluster uncertainty.
- Hidden until final scoring: `mistake_agent`, `mistake_step`, `mistake_reason`,
  `is_correct`, and `is_corrected`. `ground_truth` is also absent from the
  primary selector and every primary downstream localizer. A secondary
  source-compatibility regime supplies `ground_truth` equally to all localizers,
  because the released Who&When runners hard-code it; this regime cannot support
  the primary deployment-style claim.
- Ground truth: one responsible agent and decisive step per trace.

### Fresh confirmation B: TRAIL

- All 148 released traces: 117 GAIA and 31 SWE-Bench.
- Primary visible input is a deployment-style scrubbed projection of the official
  raw recursive OTel tree. Preserve source-native span names, parent/child
  relation, timestamps, execution attributes, events, logs, agent-generated
  outputs, status, and duration, but recursively remove offline dataset oracle
  metadata before every method runs: GAIA `true_answer` and `Annotator Metadata`,
  and SWE-Bench reference `patch` and `test_patch` fields. The scrubber targets
  source dataset-record metadata, not patches or answers generated by the traced
  agent itself. Unique LLM/TOOL spans are atomic localization operations;
  CHAIN/AGENT/internal spans may define native scopes but are not gold leaves.
  `span_id` is identity only and never a lexical ranking feature.
- Hidden until scoring: all files under `processed_annotations_*`, including
  error locations, categories, evidence, impact, and scores.
- Ground truth: one or more exact error span IDs and categories per trace.

At the pinned commit, 3 GAIA and 1 SWE-Bench traces have an empty `errors` set.
Keep all four in inference, prediction coverage, micro false-positive counts,
exact-set match, and no-error specificity. Exclude them only from gold-
conditional scope hit/recall and work-to-gold denominators, which are undefined
without a gold span. For per-trace localization metrics, empty-gold/empty-
prediction has precision=recall=F1=1 and exact-set match=1; empty-gold/nonempty-
prediction has precision=F1=0, recall=1, and exact-set match=0. Pooled micro
precision/recall/F1 uses aggregate TP/FP/FN, so predictions on these traces add
false positives. Report the four trace IDs and their no-error results directly.

Use all 148 traces at the pinned release commit. Apply only three declared
source-native corrections: permissively parse the one annotation with a trailing
comma; deduplicate the byte-identical repeated span ID in trace
`72822db6e120878d916b515c2501246b`; and retain the two affected SWE-Bench traces
while excluding only their literal `Span ID not found for this shard` records
from location scoring. Every other valid label remains. Raw per-trace
`evaluations` and `annotations` arrays are verified empty; if non-empty, remove
them from every method before processing.

The official unmodified raw-trace prompt is retained as a compatibility regime
because the released TRAIL runner consumes those fields; it is labeled
`official-raw/oracle-metadata-present` and cannot support the primary claim.
Primary proposed/control/localizer comparisons all use the same scrubbed input.

Dataset qualification inspected label schemas and verified valid IDs/counts; it
did not select mechanisms or weights from confirmation outcomes. A separate
process writes label-free confirmation inputs and exits before profiling.

## Comparisons

### Equal-information structural/scope baselines

All use the identical visible operations, query, materialized risk scores,
scope-size budget, and downstream Qwen localizer:

1. semantic hierarchy with best-first risk navigation (proposed);
2. semantic leaf-only ranking using the identical induced terminal scopes and
   risk scores but discarding parent/child navigation;
3. flat top-risk operations;
4. contiguous fixed windows, with one size selected on development data;
5. source-native fixed-field rollup: actor x derived action for Who&When and
   OpenInference kind x span/service for TRAIL;
6. source-native hierarchy: actor/role scopes for Who&When and the released OTel
   parent/child tree for TRAIL;
7. an induction-query-free tree with identical frozen risk scores and navigation:
   do not pass task question terms and remove `query_overlap` plus every other
   explicit question-derived field from the Rust induction input; the navigation
   risk field remains but is excluded from split candidates;
8. the same query-conditioned tree with FIFO and width-first navigation;
9. 100 matched random hierarchies preserving each trajectory's depth, node count,
   terminal-width multiset, and operation membership;
10. whole session as a 100%-work anchor and an oracle as a non-deployable ceiling.

### Published/official diagnostic baselines

- Run Who&When all-at-once, step-by-step, and binary-search methods with the same
  Qwen2.5-7B model. The primary paper-faithful adapter removes the task answer,
  uses temperature 0, and scores exact normalized agent and integer step equality.
  The released with-answer/temperature-0.6 path and substring evaluator are
  reported only as compatibility rows and labeled with both deviations.
- Reproduce SDBL random scope exactly from its published definition; label SSD
  and EASD as `paper-faithful replication`, never official execution. The
  unreleased code and published 54-versus-released 58 handcrafted mismatch are
  explicit limitations.
- Run TRAIL's official all-at-once prompt and evaluator with the same Qwen model.

Published stronger-model rows remain cited context, not substitutes for local
runs. Primary localizer comparisons within each dataset use temperature 0, the
same model weights, dataset-specific output allowance, prompt taxonomy, and
strict exact evaluator. Record input/output tokens, fallbacks, and wall time. A
model/context failure is a terminal miss in the all-trace intent-to-treat result,
not an empty successful prediction; complete-case results are sensitivity only.

Who&When reports SDBL in two non-conflated forms. The paper-faithful SSD/EASD
replications give the localizer the full log plus the flagged scope and report
total scope-delineation plus localization tokens. The primary fair adaptation
uses the replicated EASD scope selector, passes only its selected operations to
the identical common localizer used by AgentProf and all structural controls,
and charges both delineation and localization tokens. This adapted EASD row is a
mandatory candidate for the strongest Who&When comparator in scope, downstream,
and equal-cost criteria; it is explicitly not an official SDBL execution.

## Workloads And Metrics

### Primary scope metrics

- Who&When: exact `Step-Hit@3` for algorithm-generated traces and
  `Step-Hit@3/5/7/9` for handcrafted traces; failure-step recall at exactly
  5/10/15/20/30% unique-operation work; recall/work AUC through 30%; and
  work/nodes to the gold step.
- TRAIL: macro and micro gold-span recall at exactly 5/10/15/20/30% unique-operation
  work, trace-any-hit, recall/work AUC through 30%, and work/nodes to 25/50/80%
  gold recall. Gold-conditional scope metrics use the 144 traces with at least
  one valid gold span; all downstream and coverage metrics retain all 148 under
  the empty-set conventions above.
- Both: `ScopeHit@1/3/5` only with corresponding actual unique-operation and
  token work; unique operations exposed; serialized visible tokens; expanded
  tree nodes. No operation is counted twice.

### Primary downstream metrics

- Who&When exact integer-step accuracy is primary; normalized actor accuracy and
  exact joint actor-step accuracy are secondary. Report +/-1 and +/-2 tolerance
  and the released substring score only as compatibility metrics.
- TRAIL exact span precision/recall/F1 (macro and micro), exact-set match, and
  prediction coverage over all 148 traces are primary. Official location recall
  and joint location-category score are compatibility metrics.
- Pareto surface over localization quality, original operations exposed,
  localizer input tokens, and expanded tree nodes.

### Secondary/mechanism metrics

- group count and size/depth distributions;
- error enrichment by depth and normalized semantic prefix;
- query-boundary and risk-navigation ablations;
- Rust induction/navigation and localizer cold/warm wall time;
- GAIA/SWE and Hand-Crafted/Algorithm-Generated disaggregation;
- Three complete repetitions for stochastic localizers; at least 100 matched-tree
  seeds; and 1,000 paired bootstrap replicates. Who&When resamples question
  clusters stratified by algorithm-generated/handcrafted; TRAIL resamples traces
  stratified by GAIA/SWE-Bench. Report all four strata and an equal-weight
  Who&When/TRAIL macro headline, never only a pooled trajectory average.

For each primary paired interval, use 1,000 nested replicates. Resample
Who&When question clusters or TRAIL traces within source stratum; within each
sampled trace, resample one of the three localizer runs; for the matched-tree
baseline, resample its 100 tree seeds and recompute the per-trace median. Point
estimates average the three localizer runs and use the median across matched-tree
seeds. In every replicate, compute the maximum comparator metric across all
eligible baselines before subtracting it from the proposed metric; confidence
intervals therefore include strongest-comparator selection rather than fixing a
post-hoc winner from the point estimate.

## Predeclared Decision Criteria

The revision-1 positive claim requires all four criteria on both confirmation
families; report each source-native subset even when the family aggregate passes.

1. **Failure-containing scope at equal work:** On both fresh families, proposed
   navigation improves GoldRecall@20% and recall/work AUC through 30% over the
   strongest non-oracle comparator by at least 0.05 absolute, with paired 95%
   interval lower bound above zero. The Who&When comparator set includes adapted
   EASD as well as every same-score structural baseline. The direction must hold
   in each of the four source-native strata.
2. **Downstream localization at equal cost:** Against the strongest equal-model,
   equal-prompt scope baseline, define quality as exact Who&When step accuracy
   and TRAIL macro exact-location F1 over all 148 traces under the empty-set rule.
   For both operation and serialized-selected-content token axes, compute the
   normalized trapezoidal quality AUC at per-trace caps `{5%,10%,15%,20%,30%}` of the
   complete scrubbed trace; include an operation only if it fits the token cap,
   never truncate its content. Constant query/template tokens are excluded from
   the cap but all inference and delineation tokens are separately reported as
   end-to-end cost. The proposed method must satisfy one branch on both families:
   (a) operation-axis AUC improves by at least 0.05 with paired lower bound above
   zero and token-axis AUC is non-inferior with margin 0.02 and paired lower bound
   above -0.02, while the ratio of paired total end-to-end input tokens summed
   through `{5%,10%,15%,20%}` has point estimate and 95% upper bound at most 1;
   or (b) AUC is within 0.02 on both axes and proposed quality at the directly
   measured 15% cap is within 0.02 of or above the strongest comparator's quality
   at its 20% cap on both axes. For branch (b), compute each family-level work
   ratio as the sum across paired traces at proposed 15% divided by the sum at
   comparator 20% for operations, selected-content tokens, and total
   delineation-plus-localization input tokens; all three point ratios must be at
   most 0.75 and paired 95% upper bounds below 1. A zero comparator denominator
   makes that efficiency branch fail rather than inventing a ratio. Comparator
   selection occurs inside each replicate by highest 20%-cap quality, breaking
   ties by lower total cost. No interpolation, unattained-target substitution, or
   extra-token allowance can pass this criterion.
3. **Hierarchy beyond risk and shape:** At 20% operation work, proposed
   navigation beats semantic leaf-only, flat risk, and the median of 100 matched
   random hierarchies by at least 0.05 recall with paired lower bounds above zero
   on both families.
4. **Both advertised mechanisms engage:** At 20% operation work, the proposed
   query-conditioned tree beats the query-free same-navigation tree, and risk
   navigation beats both FIFO and width-first on the same query-conditioned tree,
   by at least 0.03 recall on each family with paired lower bounds above zero.
   Before scoring, assert that the query-free induction input contains no task
   question, query terms, `query_overlap`, or other question-derived fields and
   that Rust selected none; the frozen per-operation risk-score input and every
   navigation configuration value must be identical between this ablation and
   the proposed tree.

The claim is contradicted if any criterion fails clearly on either family. It is
inconclusive if confirmation coverage is incomplete, more than 5% of one
localizer matrix has non-semantic execution failures, or intervals cannot
distinguish the proposed method from the strongest comparator.

## Planned Runs

| Run group | Workload | Methods | Repetitions | Purpose |
|---|---|---|---:|---|
| development | AgentRx + TELBench only | depth/min-child/risk-navigation grid and required ablations | 3 seeds, both families, 5/10/15/20/30% | select one configuration without fresh labels |
| preflight-development | one complete prior-development task | proposed + every structural baseline + localizer + scorer | 1 | exercise real Rust, Qwen, metric, and raw-output paths |
| preflight-confirmation | one unlabeled Who&When HC trace and one unlabeled nested TRAIL trace | conversion, proposed tree, scopes, official localizer prompts | 1 each | exercise both real adapters without scoring confirmation labels |
| structural confirmation | Who AG 126 + HC 58; TRAIL GAIA 117 + SWE 31 | proposed, leaf-only, flat, fixed-window, fixed-field, native, query-free, FIFO, width, session | 3 proposed seeds; deterministic controls | exact work curves and four-stratum evidence |
| shape null | all 332 traces | 100 matched random hierarchies | 100 seeds | reject width/topology explanation |
| Who published/downstream | all 184 | all-at-once, stepwise, binary, RSD, SSD/EASD replication; proposed and strongest controls | 3 localizer runs, no-answer primary; with-answer sensitivity | exact step/actor and equal-cost evidence |
| TRAIL published/downstream | all 148 | scrubbed proposed, leaf-only, fixed-window, fixed-field, native; official-raw compatibility | 3 localizer runs | exact spans/categories and equal-cost evidence without offline-answer leakage |
| uncertainty | all confirmation traces | proposed and strongest comparators | 1,000 paired cluster/trace bootstraps | intervals and subgroup robustness |

## Execution

### Implementation before real preflight

Plan PASS authorizes one implementation node before preflight. Extend the real
Rust profiler rather than simulating hierarchy in Python:

- emit a preorder structural node table with stable per-profile `node_id`,
  `parent_id`, ordered `child_ids`, depth, `[start_index,end_index)`, display
  path, weight, incoming split score, risk mean, and leaf stop reason;
- emit deterministic navigation events with visit rank, node ID, action
  (`expand` or `emit`), priority, and emitted operation indices;
- add `--navigate-operation-stack`, `--navigation-risk-field FIELD`, and
  `--induce-min-child-weight N`; the last sets minimum second-child weight to
  `N` and minimum splittable-node weight to `2N`;
- force the navigation-risk field out of induction candidates so changing only
  risk values can reorder traversal but cannot alter tree topology.

Add Rust tests for repeated semantic labels versus structural identity, preorder
interval/parent/child integrity, risk-field exclusion and topology invariance,
root-not-emitted/disjoint one-time operation coverage, deterministic ties,
minimum-child behavior, and query-free/query-conditioned topology. Create
`script/operation_hierarchical_navigation_eval.py` as the single driver for
official adapters, scrubbed projections, frozen scorer, all baselines, common
localizers, exact metrics, checkpoints, and reports. Its implementation self-
checks may validate parsing/accounting but are not experiment evidence. Run
`cargo test --manifest-path agentpprof/Cargo.toml` and a real release build before
the real-data preflight.

### Approved execution

- **Authoritative system path:** release `agentpprof` Rust binary with stable
  structural nodes (`node_id`, parent/children, depth, operation interval,
  display path, stop reason), a declared navigation-risk field excluded from
  split candidates, and a deterministic best-first navigation trace. The
  experiment driver only converts official data, materializes development-only
  risk, invokes the binary, calls official/local protocol localizers/evaluators,
  and aggregates metrics.
- **Planned command:**
  `python3 script/operation_hierarchical_navigation_eval.py --mode preflight|full --agentpprof-bin agentpprof/target/release/agentpprof --who-when-root /tmp/rq2_sources_revision1/Agents_Failure_Attribution --trail-root /tmp/rq2_sources_revision1/trail-benchmark --model Qwen/Qwen2.5-7B-Instruct --out-dir docs/visexp/out/rq2-scope-before-localization-r1/`
- **Real preflight:** One full development task through scoring plus one real
  label-free trace from each confirmation adapter through Rust and Qwen. Include
  a longest-context case to validate model/context executability.
- **Resource estimate before preflight:** Approximately 36,500 CPU-side
  trace/method evaluations including 100 matched trees per trace, and roughly
  35,000–50,000 local Qwen calls once iterative Who&When SSD/stepwise paths and
  three complete downstream repetitions are included. Initial envelope:
  100–300 million input tokens and 24–96 RTX-5090 GPU-hours. Preflight measures
  actual throughput and updates this estimate, but never reduces or stops the
  approved matrix; per-trace/method checkpoints support continuous completion.
- **Full completion rule:** Every development grid cell; all 184 Who&When and
  148 TRAIL traces; every proposed/control structural method and exact work
  budget; three complete localizer repetitions; both Who information regimes;
  all 100 matched trees; exact and compatibility evaluators; and all 1,000
  bootstrap draws reach a reported terminal outcome. Context failures remain
  terminal misses in intent-to-treat results. No prefix or successful subset can
  support the claim; only the three declared TRAIL source corrections apply.
- **Primary-input check:** Before preflight inference, report counts proving all
  117 GAIA projections lack `true_answer`/`Annotator Metadata`, all 31 SWE-Bench
  projections lack source-record `patch`/`test_patch`, and agent-generated
  outputs plus topology remain present. This is a scientific leakage check, not a
  separate gate artifact.
- **Raw path:** `docs/visexp/out/rq2-scope-before-localization-r1/`.
- **Recovery:** Checkpoint per trace/method and resume incomplete cells. Checkpoint
  existence is operational only and never changes scientific admission.

## Interpretation

- **Supportive:** All four criteria pass on both fresh families and no subgroup
  reverses the claimed direction without explicit scope.
- **Contradictory:** A fixed/matched/flat/leaf method matches or dominates the
  proposed tree, or hierarchy helps scope Hit but not final localization/cost.
- **Inconclusive:** The approved matrix cannot execute completely or uncertainty
  remains too wide under the stated rule.
- **Next larger experiment if supported:** Profile-guided controlled replay on
  fresh real agent runs, testing whether repairing the selected scope changes
  task outcome, following REFLECT's intervention-backed attribution principle.
- **Target paper artifacts:** One cross-family scope/localization Pareto figure;
  one source-native accuracy/cost table; one depth/ablation figure; two compact
  failure/success cases with semantic breadcrumbs.

## Reproducibility Notes

- Record exact source commits above, the final Qwen model revision/config,
  Rust command, selected development configuration, and raw commands.
- The SDBL code is unavailable; label its protocol reimplementation and report
  deviations. Do not call it an official run.
- The research control plane remains Markdown. Raw JSON/results are evidence,
  not gate contracts.
