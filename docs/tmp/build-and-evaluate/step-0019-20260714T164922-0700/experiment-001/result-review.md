# Independent Result Review: RQ2 Fixed Reader

**Review scope:** completed Step 0019 `experiment-001` only
**Selected RQ:** “Does profiler output correspond to real problems?”
**Reviewed artifacts:** approved plan and plan review, real-preflight report,
`script/r315_llm_reader_eval.py`, all 66 raw response records, the collection
summary, hidden R315 key, source R316 scores, all four emitted CSV files,
`summary.json`, and `result-report.md`.

## Independent Judgment

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional RQ evidence
next paper decision: Add the bounded fixed-reader comparison to RQ2, including all six paired task rows and the inspection-work context. Do not change the thesis or RQ, and do not promote this result into a human-productivity, remediation, raw-action-superiority, universal-view-dominance, lower-work, or whole-RQ claim.
```

The run meets the plan's registered deterministic decision rule: both primary
metrics have a positive median operation-stack-minus-fixed-session delta and
improve on at least four of six tasks. This is one new downstream decision
result toward RQ2, not an answer to all of RQ2. I classify its research value
as **supporting**, rather than adopting the scorer-generated `decisive` label:
the comparison is useful and non-redundant, but it covers one reader, six
related tasks, preselected top-five packets, and no matched raw-action view or
human analyst.

## Completion, Configuration, And Deviations

- The full matrix contains exactly 66 unique presentations: twelve non-flat
  packets at five rotations each and six flat packets once each, spanning all
  18 R315 packets and all six tasks.
- All 66 records have `status=success`, all completed on API attempt one, and
  no row was dropped, imputed, retried into an observation, or excluded.
- Every request used `qwen3.6-27b`, temperature `0`, seed `20260714`, maximum
  1024 output tokens, reasoning disabled, and the reviewed prompt and
  three-group budget (one group for flat). The collection summary reports
  517.65 seconds for the complete run.
- The raw requests contain five unique aliases for every non-flat packet and
  one alias for flat. The model returned exactly three distinct valid aliases
  for every non-flat presentation and the sole alias for every flat one.
- I found no material deviation from the approved plan. The preflight and full
  run used separate output directories, and the full run did not reuse the
  five preflight responses.

## Independent Metric Recalculation

I independently joined each raw selected original group ID to the R315 hidden
key, summed selected operations and positive operations, used the flat hidden
case for each task's total operations and positives, averaged the five
rotations within each task/view, and only then formed the six paired deltas.
The independently recomputed presentation values match
`presentation-scores.csv` exactly (maximum absolute difference `0` for recall,
precision, and work), and the following task aggregates match the emitted
paired CSV and JSON summary.

| Task | Recall delta | Precision delta | Work-fraction delta |
|---|---:|---:|---:|
| AgentNet incorrect step | -0.004805 | +0.009599 | -0.002229 |
| AgentNet redundant step | +0.008186 | +0.061404 | +0.001589 |
| Agent Reward looping | +0.361111 | -0.105263 | +0.293553 |
| Agent Reward side effect | +0.064356 | +0.159329 | -0.000549 |
| OSWorld group start | +0.356545 | -0.177203 | +0.376714 |
| SATraj unsafe | +0.096785 | +0.369412 | +0.011015 |
| **Median paired delta** | **+0.080571** | **+0.035501** | **+0.006302** |
| **Improved / tied / worse** | **5 / 0 / 1** | **4 / 0 / 2** | **4 / 0 / 2** |

Thus the registered recall condition passes and the registered precision
condition passes, so the tested hypothesis is **supported**. The accurate
reader-facing interpretation is a median improvement of **8.06 percentage
points in selected-positive operation recall** and **3.55 percentage points in
selected-positive operation precision** at the fixed three-group budget. The
six task rows, not merely the aggregate, must remain available because the two
precision losses and one small recall loss are part of the complete result.

The run does **not** show reduced inspected operation work: the median work
fraction delta is +0.006302, work is higher on four tasks, and two large tasks
have much higher operation coverage under operation-stack groups. Work is a
necessary interpretation variable, not a third passing primary metric.

## Order Balance, Leakage, And Mechanism Engagement

- For every non-flat packet, every original visible group occupies each alias
  position `G01` through `G05` exactly once. Rotation metrics are averaged
  before the task comparison. Five rotations are an order-balance control, not
  five independent scientific replicates.
- A direct scan of all serialized model requests found no original group ID
  and none of the excluded keys (`packet_id`, `view`, `ranker`, `rank`, hidden
  positive counts/rates, or oracle fields). The alias map and selected original
  IDs exist only outside the model request for later scoring.
- Collection code has no hidden-key input; the scoring command loads the key
  only after the complete response file exists. Ground-truth positives come
  from the pre-existing benchmark annotations and do not depend on the
  reader's selection or the profile's score, so recall and precision are not
  circularly defined by the evaluated output.
- The target problem and `analysis_task` name remain visible in every group of
  the same packet. They disclose the question, as required, but not which
  groups are positive and therefore do not distinguish candidate groups.
- All 66 responses include non-empty visible-field rationales. Across the
  twelve non-flat packets, six produce one stable selected original-group set
  across all rotations and six produce two or three sets. This shows that
  the reader engaged visible content while the rotation control also exposed
  residual ordering sensitivity. Rationales are explanatory model output, not
  independently verified diagnoses or a scored endpoint.

## Baseline And Control Audit

### Fixed-session main baseline

The fixed-session comparison engaged its intended mechanism and is fair for
the **bounded packet-view claim**. Both views use the same problem, five-group
packet, visible field categories, examples, prompt, model, decoding, five
balanced positions, and exactly-three-group decision budget. Mean serialized
user-request sizes are also close: 14.9 KB for operation stack and 14.7 KB for
fixed session, with neither near the model context limit. There was no
baseline interface failure or smaller response budget.

The comparison is nevertheless a pipeline-level view comparison, not an
isolated reader ablation. R315 supplies the query-aware top five separately for
each view; those candidate sets cover different operations and positive
operations before the reader selects three. The reader result therefore
combines upstream grouping/candidate construction with content-based
selection. That is consistent with the registered hypothesis about the
packets, but a paper sentence must not claim that the LLM reader alone caused
the gain or that equal group count means equal inspected-operation work.

### Flat and R316 controls

Flat behaves as the declared non-selective lower-bound control: selecting its
sole all-task group gives recall and work equal to one, with precision equal to
task prevalence. It is not a granularity-matched baseline and supplies no
superiority claim.

The deduplicated R316 control correctly collapses eight identical assignment
rows per packet into one of 18 unique packet rows. Its visible-order top-three
control already favors operation stack in recall on five of six tasks (median
delta +0.1333), while precision improves on three, ties on one, and worsens on
two (median delta +0.0142). The new rank-hidden reader changes selections and
crosses the registered four-task precision condition; it therefore adds a
different downstream decision, but the R316 direction also shows that part of
the result originates in the query-aware candidate pipeline rather than a
newly discovered reader effect.

No matched R315 raw-action packet exists. Consequently this experiment cannot
support superiority to raw action, and R316 must remain a control rather than
being presented as an external main baseline.

## Uncertainty And Competing Explanations

- The scientific units are six task pairs, but they come from four dataset
  families; the two Agent Reward tasks and two AgentNet tasks reuse underlying
  trace populations. The win counts and medians are descriptive, not six fully
  independent draws from a broad population.
- There is one quantized local model configuration and one fixed seed. Position
  balance controls one known nuisance, but the run does not establish
  cross-model, prompt, stochastic, or human generality.
- Candidate packets contain only each view's query-aware top five. The result
  does not evaluate full-profile browsing, end-to-end root-cause diagnosis, or
  repair success.
- Oracle granularity differs across tasks: some annotations identify
  step/operation events, whereas Agent Reward labels describe trajectories and
  are propagated to their operations. “Positive operation” must therefore be
  described as the benchmark-derived scored unit, not uniformly as the exact
  causal faulty action.
- Operation-stack recall is partly enabled by grouping more underlying work
  into three selected summaries. The simultaneously positive precision result
  prevents this from being only indiscriminate expansion, but the higher work
  rows rule out a lower-inspection-work conclusion from this run.

These limitations bound the evidence without invalidating the registered
fixed-reader hypothesis.

## Paper-Number And Decision Audit

The following are supported paper numbers when accompanied by the exact
scope: 66 presentations; 18 packets; six paired tasks; median paired recall
delta +0.080571 with 5/6 task improvements; median paired precision delta
+0.035501 with 4/6 task improvements; and the six task rows above. Mean deltas,
secondary lift/hit outcomes, and flat/R316 controls are reproducible, but they
should not replace the registered medians or imply population-level
significance. Any figure must identify rotations as order controls and tasks as
the paired units.

Return this valid result to the orchestrator for a targeted RQ2 evaluation
update. Preserve the fixed thesis and all four RQs. No rerun is required to use
this bounded result, and repeating the same packet study with cosmetic prompt,
cutoff, or model changes would not by itself add higher paper value. The next
outer-loop experiment should address the strongest remaining paper-level gap,
not retroactively widen this result's scope.
