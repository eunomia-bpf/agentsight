# Result Report: RQ3 Cross-Domain Calibration Of Existing Recurrence Scores

## Run Identity

- **RQ:** **RQ3: How accurate are the tags?**
- **Tested hypothesis:** An occurrence-weighted empirical-CDF scale lets one
  grouped source domain calibrate the unchanged recurrence score for another
  domain while preserving or improving its operation partition.
- **Approved plan:** [`experiment-plan.md`](experiment-plan.md)
- **Plan review:** [`plan-review.md`](plan-review.md), round-two `PASS`
- **Implementation:**
  [`script/rq3_cross_domain_percentile_calibration_eval.py`](../../../../../script/rq3_cross_domain_percentile_calibration_eval.py)
- **Raw root:**
  [`.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/`](../../../../../.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/)
- **Full summary:**
  [`full/summary.json`](../../../../../.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/full/summary.json)

## Execution

The approved preflight and full commands completed without a scientific or
configuration change:

```text
python3 script/rq3_cross_domain_percentile_calibration_eval.py \
  --mode preflight \
  --out .agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/preflight

python3 script/rq3_cross_domain_percentile_calibration_eval.py \
  --mode full \
  --out .agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/full
```

Preflight processed one real target session in each direction and returned
`run_status: valid`, `tested_hypothesis: not tested`. The full run used all 287
OSWorld-Human sessions and all 405 source-valid failed CodeTraceBench sessions.
It emitted 3,978/20,866 operation assignments, 3,691/20,461 pair decisions,
and 10,000 paired session-bootstrap draws per target. No preflight value was
used to revise the method, source cutoff, outcome rule, or full population.

## Information Separation And Completion

The run first used the disjoint solved CodeTrace source to fit one percentile
cutoff and wrote every CT-to-OSWorld target prediction before constructing the
selected OSWorld oracle mapping. The initial OSWorld eligibility loader does
parse label-bearing rows to enforce the fixed `group_alignment=exact`,
non-singleton population, but it returns only ordered actions; no group identity
or boundary reaches fitting, CDF construction, or prediction. After the
persistence point, OSWorld groups become source information for the reverse
direction. The run wrote every OSWorld-to-CodeTrace target prediction before
loading any failed-target stage. File timestamps and the implementation order
preserve the two method-information separation points.

Every operation has exactly one candidate, raw-transfer, label-free, and oracle
assignment. Every adjacent pair has exactly one decision from each method.
Empirical CDFs are finite, bounded in `[0,1]`, right-continuous, occurrence
weighted, and monotone. Recomputed label-free B-cubed and exact boundary F1
match the existing Step 0024 summaries bit-for-bit on both complete targets.
The reader-facing paper submodule remains clean and untouched.

The shared source fitter represents a separating cutoff by the midpoint between
adjacent observed scores, while the plan describes selection over finite
observed CDF values. The selected midpoints lie in empty target-percentile
intervals, so using the corresponding observed separator reproduces every
target decision. This representation deviation does not alter a population,
comparison, metric, interval, or outcome.

## Source Fits

| Grouped source | Target score scale | Percentile cutoff | Direct raw cutoff |
|---|---|---:|---:|
| CodeTraceBench solved | OSWorld-Human held-out folds | 0.223273 | -0.098247 |
| OSWorld-Human | CodeTraceBench failed | 0.702384 | 0.266551 |

The two percentile cutoffs differ substantially even after rank normalization.
That observation is descriptive only; the registered target comparisons below
determine the hypothesis.

## Complete Standard-Metric Results

| Target | Method | B-cubed P | B-cubed R | **B-cubed F1** | Exact boundary F1 | Groups |
|---|---|---:|---:|---:|---:|---:|
| OSWorld-Human | percentile transfer | 0.575011 | 0.824768 | **0.677607** | 0.368534 | 1,316 |
| OSWorld-Human | direct raw transfer | 0.505448 | 0.874150 | 0.640531 | 0.306314 | 987 |
| OSWorld-Human | current label-free | 0.855872 | 0.726966 | **0.786170** | 0.679922 | 2,656 |
| CodeTraceBench | percentile transfer | 0.947623 | 0.315368 | **0.473242** | 0.267524 | 12,941 |
| CodeTraceBench | direct raw transfer | 0.978517 | 0.250214 | 0.398523 | 0.256284 | 15,725 |
| CodeTraceBench | current label-free | 0.828579 | 0.533630 | **0.649173** | 0.287106 | 6,897 |

| Target | Candidate - label-free B-cubed | Paired 95% interval | Candidate - raw transfer | Paired 95% interval |
|---|---:|---:|---:|---:|
| OSWorld-Human | -0.108562 | [-0.138246, -0.078428] | +0.037077 | [+0.019693, +0.055919] |
| CodeTraceBench | -0.175931 | [-0.189732, -0.161417] | +0.074719 | [+0.057926, +0.094771] |

The bootstrap resamples target sessions with replacement, paired across all
three methods and stratified by the five OSWorld folds or four CodeTrace agent
frameworks. B-cubed is reconstructed from per-session precision/recall
sufficient statistics before the harmonic mean, preserving the pooled
operation-weighted definition.

## Registered Interpretation

**Run status proposed for independent review:** `valid`

**Tested hypothesis proposed for independent review:** `contradicted`

Percentile normalization strictly improves over directly transferring a raw
NPMI cutoff on both targets, with positive paired intervals. It therefore fixes
part of the raw numerical-scale mismatch. It remains substantially below the
current label-free constructor on both complete populations, with wholly
negative paired intervals. The dominant error differs by target: it over-merges
OSWorld to 1,316 groups and over-fragments CodeTrace to 12,941 groups. The
strongest explanation is that grouped-source thresholds encode different
operation-group semantics, not merely differently scaled NPMI values.

This contradicts the one tested cross-domain calibration mechanism. It does
not contradict RQ3 as a whole, the operation-stack model, either core paper
abstraction, or the profiling thesis. Per the approved terminal rule, this
branch is closed without another normalization, target-specific percentile,
Rust port, or reader-facing negative row. Step 0024 remains the label-free
default and Step 0030 remains the optional per-domain grouped-reference mode.

## Proposed Paper Decision

- **Research value:** supporting mechanism boundary.
- **Paper impact:** mechanism boundary, not a thesis or whole-RQ answer.
- **Next paper decision:** no reader-facing paper change; preserve the complete
  negative mechanism record in `docs/evaluation.md` and this step history.
- **Remaining RQ3 frontier:** literal phase identity, unknown label sets, and
  broader cross-framework tag accuracy remain unresolved. This result gives no
  authority to narrow those hypotheses or change the story.
