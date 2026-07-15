# Experiment Plan: RQ3 Multi-Step Grammar Recurrence

## Research Question

- **RQ exactly as written in the paper:** **RQ3: How accurate are the tags?**
- **Specific uncertainty tested here:** whether recurring multi-action motifs,
  learned from label-free reference sessions and applied unchanged to held-out
  sessions, recover human/source-authored operation groups more faithfully than
  the current adjacent-transition recurrence constructor.
- **Why the answer matters:** Step 0024 is the current automatic constructor,
  but Step 0026 shows that the same visible action pair has mixed boundary
  labels for 91.2% of OSWorld-Human and 99.7% of CodeTraceBench decisions. A
  flat pair score therefore discards sequence context that may distinguish a
  recurring operation from an accidental transition. The paper needs a simple,
  principled constructor rather than another score term or cutoff.

This is one supporting group-boundary experiment inside fixed RQ3. It does not
change, split, rename, narrow, or answer all of RQ3. It does not test literal
semantic names, all tag backends, or a new RQ. The exact thesis remains
**“Agent observability needs profiling, not only debugging.”** The original
AgentProf story, four RQs, and contribution surface remain fixed.

## Paper-Value Admission

- **Planned role:** supporting automatic-construction evidence for RQ3.
- **Largest credible paper story this experiment could unlock:** AgentProf can
  construct reusable operation motifs from cross-run recurrence without
  assuming that a single adjacent transition or manually selected context
  window defines an operation.
- **Strongest reviewer reject argument addressed:** the released constructor
  is a post-hoc pairwise heuristic whose CodeTraceBench B-cubed score remains
  slightly below source-provided phase change, and the repository's own audit
  shows pair identity is highly ambiguous.
- **Different evidence calculation beyond prior runs:** a different published
  sequence-model family applied to the complete, already-normalized
  OSWorld-Human and CodeTraceBench populations under the same reference/target
  separations and official partitions. At execution time no target label enters
  rule learning or application. The family was nevertheless selected after
  agents had seen both populations' earlier label-based results, so both new
  results remain adaptive post-hoc mechanism-development evidence.
- **Why this is not another closed tweak:** it does not change the NPMI score,
  cutoff, score sign, support cutoff, fixed window, margin, or source field.
  Recursive pair replacement creates variable-length motifs; Step 0026 closed
  only flat action-pair/small-window decisions and explicitly left future
  sequence models open. Step 0028's supervised scalar fitting is not used.
- **Paper decision if positive:** replace the Step 0024 automatic constructor
  with this simpler published grammar principle, synchronize only the
  implementation and RQ3 constructor/result paragraphs, and retain the
  post-hoc development-evidence boundary.
- **Paper decision if mixed or contradictory:** restore Step 0024 exactly,
  record the complete mechanism result internally, and return the paper-level
  decision to REVIEW. Do not add a second grammar variant, tune on target
  outcomes, shrink RQ3, or change the story.
- **Best alternative experiment:** direct phase/action/literal-name accuracy or
  an end-to-end RQ2 repair consequence has higher coverage of the remaining
  whole-paper gaps. This experiment wins the immediate decision because the
  user explicitly requested an algorithm improvement on existing trajectories,
  the current failure diagnosis points to missing multi-step structure, and all
  real inputs and official scorers already exist.

## Expected And Alternative Outcomes

- **Current expected answer:** multi-step grammar recurrence improves
  operation-weighted B-cubed F1 over Step 0024 on both complete populations and
  remains above the strongest simple OSWorld control.
- **Strongest competing explanation:** coarse action vocabularies alias entire
  multi-step motifs, not only pairs, so lossless repetition structure still
  does not correspond to human/source-authored operation stages.
- **Result that contradicts the expectation:** the candidate fails to improve
  B-cubed F1 on either complete population or lowers either population.

## Published Precedent And Real Assets

- **Published algorithmic precedent:** Larsson and Moffat's Re-Pair repeatedly
  replaces a most frequent adjacent symbol pair with a nonterminal until no
  pair repeats ([Proceedings of the IEEE
  2000](https://doi.org/10.1109/5.892708)); the authors' research implementation
  likewise emits a phrase hierarchy and compressed sequence
  ([Re-Pair/Des-Pair](https://github.com/rwanwork/Re-Pair)). Step 0029 fixes one
  **multi-session, reference-to-target adaptation of Re-Pair**. Three deviations
  are deliberate and load-bearing: pair priority is distinct-session support
  rather than single-text occurrence frequency, session boundaries are hard,
  and the ordered dictionary learned from reference sessions is transferred
  unchanged to target sessions. This adaptation encodes cross-run recurrence
  and target-label isolation; it is not standard Re-Pair or SEQUITUR and receives
  no new branded name.
- **OSWorld-Human:** the established loader retains all 287 eligible sessions,
  3,978 operations, 3,691 adjacent pairs, and 2,042 official human groups under
  the unchanged five session folds.
- **CodeTraceBench reference:** the established source loader and target-ID
  exclusion retain exactly 2,229 reference sessions and 87,703 operations.
- **CodeTraceBench target:** all 405 existing source-valid failed trajectories,
  20,866 operations, 20,461 adjacent pairs, and 2,948 complete official stages
  across four frameworks.
- **Necessary project code:** the product implementation and thin equivalence
  adapters are necessary because no maintained Rust crate in the current
  dependency graph implements this grammar induction contract. The official
  benchmark loaders, official partition scorer, current binary interface, and
  real operation files remain in use; no new benchmark or synthetic workload
  is introduced.

## The One Algorithm Change

Replace Step 0024's NPMI/two-means boundary rule with one deterministic,
reference-only multi-session Re-Pair adaptation over the same visible `action`
sequences:

1. Treat each reference session as a separate sequence of action terminals.
   No adjacent pair crosses a session boundary.
2. For every adjacent symbol pair in the current compressed reference, compute
   its non-overlapping occurrences separately in each session. The exact scan
   starts at position zero; a match increments the count and advances by two
   symbols, while a non-match advances by one. Session support is the number of
   sessions with at least one such match. A pair is eligible only when its
   session support is at least two. This fixed rule defines cross-run recurrence
   and is not a support sweep.
3. Select one eligible pair by the total key: descending session support;
   descending total non-overlapping occurrences; ascending structured
   `(fully-expanded-left-actions, fully-expanded-right-actions)`; then ascending
   stable symbol identity, where terminals use `(0, action-text)` and rules use
   `(1, creation-index)`. Create the next rule ID monotonically from zero and
   replace that pair non-overlapping left-to-right in every reference session.
4. Repeat Steps 2--3 until no pair has support in two sessions. Each rule makes
   at least one replacement in two sessions, reducing the total reference
   symbol count by at least two, so the algorithm terminates without a grammar-
   size, depth, or motif-length cap. The direct deterministic implementation
   rescans current sequences per rule: `O(RN)` time and `O(N+R)` space for `N`
   input symbols and `R <= N/2` rules (`O(N^2)` worst case). The complete
   87,703-operation reference must finish under this uncapped contract.
5. Apply every learned rule to each target **exactly once in creation order**.
   Each application performs the same single non-overlapping left-to-right
   scan; it is not repeated to a fixed point. Because later rules contain only
   terminals or earlier rule IDs, creation-order application exposes every
   applicable higher-order motif deterministically.
6. Each symbol remaining in a target sequence spans one predicted operation
   group. Its fully expanded, run-length-compressed action sequence supplies
   the ordinary `operation` frame label. Every target operation belongs to
   exactly one contiguous group and retains its original additive weight.
   Resource weight, target group/stage labels, phase, benchmark, framework,
   outcome, and paper metrics never enter a rule or its application.

There is no NPMI, two-means cutoff, numeric support parameter, maximum motif
length, maximum grammar depth, field sweep, window sweep, per-benchmark rule,
target retry, learned label name, or second candidate. The algorithm is
described as **grammar-based operation-stack induction**, with the multi-session
Re-Pair adaptation stated once; no new AgentProf-specific algorithm name or
competing grammar variant is introduced.

### OSWorld-Human Isolation

Use the unchanged five deterministic session folds from Steps 0020--0024. For
target fold `f`, learn the complete grammar from the other four folds' visible
`action` sequences, apply it once to fold `f`, persist predictions, and only
then read fold `f` human groups for scoring. Every eligible session is a target
exactly once. `group_alignment=exact` is applied before the established loader
silently excludes sessions with fewer than two eligible operations; this loader
is imported rather than reimplemented. This is execution-time label isolation,
not a claim that the algorithm family was chosen before prior OSWorld labels
were observed.

### CodeTraceBench Isolation

Use the established `load_visible_operations()` path. Load target IDs without
stages, remove all 405 target IDs from the broad reference operations, assert
the exact 2,229-session/87,703-operation reference, learn one grammar, apply it
once to all 405 targets, persist predictions, and only then call the existing
`load_stages_after_prediction()` scorer path. The labels have already been
observed in prior project steps, so a positive result remains post-hoc
mechanism-development evidence rather than untouched confirmation.

## Comparisons

- **Proposed method:** cross-session grammar recurrence over visible actions.
- **Main baseline:** Step 0024 monotone NPMI recurrence under the exact same
  reference and target populations. Its complete raw results are reused, while
  the evaluator also verifies the expected baseline identifiers and counts.
- **OSWorld comparators:** the existing supervised nine-field boundary
  predictor and the unchanged always-boundary, action-change, phase-change, and
  one-session-block controls.
- **CodeTrace comparators:** unchanged phase-change, action-change,
  always-boundary, and one-session-block controls, including per-framework
  results.
- **Conclusion if a comparator wins:** candidate adoption still requires the
  fixed candidate-versus-Step-0024 rule below; comparator wins constrain any
  “best” wording and cannot be hidden.
- **Information fairness:** candidate and Step 0024 receive the same reference
  and target `session`/`action` sequences. At execution time the candidate
  receives no extra semantic field, annotation, score, or target-time option:
  OSWorld held-out groups and CodeTrace target stages load only after persisted
  predictions. The decision to test grammar induction is adaptive because
  earlier label-based outcomes on both populations motivated it; no result may
  be called target-naive, untouched, or independent confirmation.

## Workloads, Metrics, And Fixed Interpretation

- **Primary outcome:** operation-weighted B-cubed F1, reported separately for
  each complete population.
- **Diagnostics:** B-cubed precision/recall, boundary precision/recall/F1,
  per-fold/per-framework metrics, grammar rules/depth/compression, singleton
  coverage, segment/motif counts, target coverage, Rust/Python equivalence, and
  additive-weight conservation.
- **Repetitions:** deterministic; one complete execution after preflight.
- **Cost:** local CPU over existing files; no API, model, agent, or environment
  rerun.

The tested hypothesis is:

- **SUPPORTED:** candidate B-cubed F1 is no lower than Step 0024 on both
  complete populations and strictly higher on at least one.
- **MIXED:** candidate is higher on one complete population and lower on the
  other.
- **CONTRADICTED:** every other valid complete relation.
- **INVALID/INCOMPLETE:** population or label isolation fails; a planned target
  is missing; the Rust and independent evaluator disagree on any group; a
  target label affects construction; or any operation/weight is lost or
  duplicated.

No aggregate mean can hide a population regression. Boundary F1 and grammar
size are diagnostics, not alternative promotion criteria. A valid negative or
mixed result closes this one candidate and changes neither RQ3 nor the paper
story.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| OSWorld full | candidate + controls | 287 sessions / five held-out folds | grammar recurrence, Step 0024, existing controls | 1 | complete-population B-cubed relation and OSWorld control condition |
| CodeTrace full | candidate + controls | 2,229 reference → 405 failed targets | grammar recurrence, Step 0024, existing controls | 1 | complete-population and four-framework B-cubed relation |
| equivalence | correctness | every target operation above | Rust versus independent Python implementation | 1 | validity only |

## Execution

- **Implementation scope:** replace the candidate induction internals and report
  schema in `agentpprof/src/profile.rs`; make the minimum truthful NPMI-to-
  grammar CLI help/status changes in `agentpprof/src/main.rs`; adjust focused
  existing Rust/CLI tests; and add
  `script/rq3_grammar_stack_induction_eval.py`,
  `script/rq3_grammar_stack_rust_equivalence.py`, and
  `script/rq3_grammar_codetracebench_stage_fidelity_eval.py`. The OSWorld
  scripts import `load_operations()`, `group_sequences()`,
  `group_alignment=exact`, singleton exclusion, fold assignment, B-cubed, and
  controls from the established evaluator modules. The CodeTrace script imports
  `load_visible_operations()` and `load_stages_after_prediction()` rather than
  reimplementing population or oracle logic. Do not edit the paper, idea story,
  user instructions, skills, branch, KVM files, or submodule during EXPERIMENT.
- **Product command retained:** evaluator-generated reference and target JSONL
  use the existing normal interface; no candidate-only flag is added:

  ```bash
  agentpprof --operation-file TARGET.jsonl \
    --induce-operation-stack \
    --induce-reference-operation-file REFERENCE.jsonl \
    --view operations --format json --deterministic-output \
    --output PROFILE.json
  ```

- **Minimum induction report:** policy/objective; selected `session`/`action`
  fields; exact reference/target sessions, operations, and symbol counts; the
  ordered rules with IDs, child symbols, expanded actions, session support,
  non-overlapping occurrence count, and before/after reference symbol counts;
  rule count and maximum depth; target segments and motifs; predicted-group and
  singleton counts; excluded-oracle fields; and complete assignment/mass
  coverage. NPMI, cutoff, calibration, and promotion booleans are removed rather
  than retained with changed meanings.
- **Existing result baselines:** the main baseline is read from
  `.agentsight/experiments/rq3-monotone-recurrence-v1/full/summary.json` and
  `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json`.
  The OSWorld supervised comparator is read from
  `.agentsight/experiments/rq3-osworld-boundary-fidelity-v1/full/summary.json`;
  simple/phase/action/session controls are reused from the two Step 0024
  summaries. No modified-binary run is labeled as a Step 0024 baseline.
- **Implementation review:** a fresh read-only reviewer checks exact agreement
  with the approved rule order/ties, reference-target separation, established
  loader reuse, absence of hidden parameters/fields, default CLI compatibility,
  and that no candidate metric ran during implementation.
- **REAL PREFLIGHT:** one actual OSWorld held-out fold and the
  lexicographically first complete CodeTrace target go through the real binary,
  persisted prediction path, existing scorer, and independent equivalence path.
  Preflight establishes end-to-end execution only and cannot modify the plan.
- **FULL RUN:** all five OSWorld folds and all 405 CodeTrace targets finish;
  every planned baseline/control row is reported; exact product/evaluator
  assignments and mass conservation are checked before interpretation.
- **Raw roots:** `.agentsight/experiments/rq3-grammar-recurrence-v1/`,
  `.agentsight/experiments/rq3-grammar-recurrence-codetracebench-v1/`, and
  `.agentsight/experiments/rq3-grammar-recurrence-rust-equivalence-v1/`.
- **Recovery:** only a systematic implementation/execution defect may rerun an
  affected planned cell. Target outcomes cannot change the algorithm, tie
  rules, population, metric, or promotion rule.

### Approved Commands After Implementation Review

```bash
python3 script/rq3_grammar_stack_induction_eval.py \
  --mode preflight \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --current-summary .agentsight/experiments/rq3-monotone-recurrence-v1/full/summary.json \
  --out-dir .agentsight/experiments/rq3-grammar-recurrence-v1/preflight

python3 script/rq3_grammar_stack_induction_eval.py \
  --mode full \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --current-summary .agentsight/experiments/rq3-monotone-recurrence-v1/full/summary.json \
  --out-dir .agentsight/experiments/rq3-grammar-recurrence-v1/full

python3 script/rq3_grammar_stack_rust_equivalence.py \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --out-dir .agentsight/experiments/rq3-grammar-recurrence-rust-equivalence-v1/full

python3 script/rq3_grammar_codetracebench_stage_fidelity_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --current-summary .agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json \
  --out .agentsight/experiments/rq3-grammar-recurrence-codetracebench-v1/preflight

python3 script/rq3_grammar_codetracebench_stage_fidelity_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --current-summary .agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json \
  --out .agentsight/experiments/rq3-grammar-recurrence-codetracebench-v1/full
```

Terminal completion requires all five OSWorld folds, 287 sessions, 3,978
assignments, and exact Rust/Python grouping equivalence for every operation;
plus all 405 CodeTrace targets, 20,866 assignments, all 20,461 adjacent
decisions derived from complete segments, and complete per-target grouping
equivalence. Every planned comparator row and all mass must be present.

## Result Review And Writing Boundary

A fresh result reviewer must reconstruct population counts, target-label timing,
grammar construction, every predicted group, both primary metrics, all planned
controls, and mass conservation from raw files. Only `VALID / COMPLETE /
SUPPORTED` authorizes retaining the product candidate and a targeted
implementation/RQ3 paper sync. Any other valid answer restores Step 0024 and
remains internal evidence history. No outcome authorizes changes to the thesis,
four RQs, abstract/intro/motivation/contribution story, or read-only submodule.
