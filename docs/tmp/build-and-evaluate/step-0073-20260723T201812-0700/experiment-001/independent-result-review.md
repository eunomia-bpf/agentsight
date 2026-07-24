# Independent Result Review — RQ3 Fixed-Instruction Follow-On

**Review status:** complete
**Run status:** **VALID**
**Tested hypothesis:** **INCONCLUSIVE**
**Research value:** **SUPPORTING**
**Paper impact:** **mechanism/workload boundary and additional RQ3 evidence**
**Primary decision:** the registered positive A2-over-recurrence B-cubed
hypothesis is not supported and is not contradicted under its predeclared rule.

## Independent reconstruction

This review did not import or execute
`script/rq3_fixed_instruction_followon_eval.py`. It read the two packet
manifests and packet metadata, filtered the current full-population operation
and pair rows itself, implemented ordinary item-level B-cubed and binary
adjacent-boundary scoring independently, and reran the declared task-cluster
bootstrap with Python's seeded `random.Random(...).choices` semantics.

The population reconstruction passed every material check:

- the follow-on manifest contains 364 unique session IDs in 12 non-overlapping
  batches, 15,116 operations, and 14,002 source-native turns;
- packet-level operation and turn sums equal the manifest declarations, and
  the per-session operation range is 20--93;
- the initial manifest contains 41 unique sessions, 5,750 operations, and
  3,146 turns, with a per-session operation range of 95--275;
- the two manifest session sets have zero overlap and their union is exactly
  the 405 sessions in both full-population raw-row files;
- filtering the 20,866 full operation rows produces exactly 15,116 follow-on
  rows and 5,750 initial rows;
- filtering the 20,461 full adjacent-pair rows produces exactly 14,752
  follow-on pairs and 5,709 initial pairs;
- every follow-on session has exactly `operations - 1` pair rows, complete
  method/reference fields, one framework, one task name, and unique operation
  and pair keys;
- the follow-on rows contain 238 distinct task-name clusters and framework
  session counts of 202 OpenHands, 71 mini-SWE-agent, 65 Terminus2, and 26
  SWE-agent;
- the independently filtered operation and pair rows are identical, in the
  same order, to the two raw subset files written by the full run.

The initial 41 sessions are therefore excluded exactly, not approximately or
by a secondary heuristic.

## Independently recomputed metrics

B-cubed precision is the unweighted mean, over operations, of the fraction of
each predicted cluster that shares the operation's official stage. Recall is
the corresponding fraction of the official stage recovered by the predicted
cluster; the reported F1 is the harmonic mean of those two corpus means.
Boundary scores are ordinary precision, recall, and F1 over all within-session
adjacent pairs. No token weighting, depth score, or cross-session semantic-name
matching enters either result.

### Complete follow-on population

| Method | Pred./official groups | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current automatic Agent A2 | 5,198 / 2,382 | .910237 | .535911 | .674628 | .285478 | .683845 | .402802 |
| Multi-resolution recurrence | 4,131 / 2,382 | .758227 | .627664 | .686795 | .221927 | .414272 | .289023 |
| Native source tree | 11,289 / 2,382 | .977391 | .269893 | .422985 | .169336 | .916749 | .285869 |
| Source-native turn | 14,002 / 2,382 | .993477 | .196407 | .327974 | .144523 | .976710 | .251788 |

The A2 boundary confusion counts are `TP=1,380`, `FP=3,454`, `FN=638`, and
`TN=9,280`; recurrence has `TP=836`, `FP=2,931`, `FN=1,182`, and `TN=9,803`.
A2 has 1,623 singleton predicted occurrences, or 31.2% of its 5,198 predicted
groups. These counts reproduce the report's precision/fragmentation diagnosis.

### Per-framework recomputation

| Framework | Method | Ops / pairs | Pred./official groups | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OpenHands | A2 | 8,647 / 8,445 | 2,928 / 1,354 | .907018 | .530670 | .669585 | .278430 | .658854 | .391439 |
| OpenHands | Recurrence | 8,647 / 8,445 | 2,250 / 1,354 | .740572 | .637056 | .684925 | .218262 | .388021 | .279375 |
| OpenHands | Native tree | 8,647 / 8,445 | 6,253 / 1,354 | .973392 | .277675 | .432090 | .173029 | .908854 | .290712 |
| OpenHands | Native turn | 8,647 / 8,445 | 8,647 / 1,354 | 1.000000 | .156586 | .270773 | .136412 | 1.000000 | .240075 |
| SWE-agent | A2 | 1,216 / 1,190 | 412 / 173 | .900329 | .520097 | .659321 | .240933 | .632653 | .348968 |
| SWE-agent | Recurrence | 1,216 / 1,190 | 231 / 173 | .712422 | .740271 | .726080 | .278049 | .387755 | .323864 |
| SWE-agent | Native tree | 1,216 / 1,190 | 831 / 173 | .963067 | .277947 | .431391 | .157764 | .863946 | .266807 |
| SWE-agent | Native turn | 1,216 / 1,190 | 1,216 / 173 | 1.000000 | .142270 | .249100 | .123529 | 1.000000 | .219895 |
| Terminus2 | A2 | 3,078 / 3,013 | 930 / 451 | .903377 | .573964 | .701945 | .313295 | .702073 | .433253 |
| Terminus2 | Recurrence | 3,078 / 3,013 | 999 / 451 | .831067 | .547498 | .660118 | .220557 | .533679 | .312121 |
| Terminus2 | Native tree | 3,078 / 3,013 | 2,479 / 451 | .991923 | .238173 | .384115 | .153273 | .958549 | .264286 |
| Terminus2 | Native turn | 3,078 / 3,013 | 1,964 / 451 | .967968 | .337193 | .500156 | .178515 | .878238 | .296718 |
| mini-SWE-agent | A2 | 2,175 / 2,104 | 928 / 404 | .938287 | .511734 | .662271 | .299883 | .771772 | .431933 |
| mini-SWE-agent | Recurrence | 2,175 / 2,104 | 651 / 404 | .750942 | .640818 | .691523 | .217241 | .378378 | .276013 |
| mini-SWE-agent | Native tree | 2,175 / 2,104 | 1,726 / 404 | .980736 | .279341 | .434830 | .184894 | .918919 | .307847 |
| mini-SWE-agent | Native turn | 2,175 / 2,104 | 2,175 / 404 | 1.000000 | .185747 | .313300 | .158270 | 1.000000 | .273287 |

Thus A2 has higher boundary F1 in all four frameworks, but higher B-cubed F1
only in Terminus2. The primary B-cubed result loses in OpenHands, SWE-agent,
and mini-SWE-agent.

## Independent bootstrap and decision

For each method, the review first computed every operation's ordinary B-cubed
precision and recall contribution. It then grouped those contributions by the
238 sorted task names. Each of 10,000 draws sampled 238 task names with
replacement using seed `20260723`, included every session and operation of a
sampled task with its sampling multiplicity, recomputed corpus B-cubed P/R/F1,
and recorded A2 F1 minus recurrence F1.

The independent result is:

- point delta: `-0.012167365972`;
- bootstrap mean delta: `-0.012090888712`;
- linear-percentile 95% interval: `[-0.027265877931, +0.003221064661]`;
- positive-draw fraction: `0.0577`.

All 10,000 independently generated deltas agree with the stored draws to a
maximum absolute difference of `6.66e-16`, attributable only to floating-point
summation order. The point estimate is negative and the interval crosses zero.
The approved decision rule therefore yields **INCONCLUSIVE**, exactly as
reported. The higher secondary boundary F1 cannot override this primary
decision.

## Fairness, leakage, and adaptivity audit

The comparison itself is technically fair. A2 and recurrence are complete on
the same operations and official references; recurrence engages its intended
visible-action recurrence mechanism and does not fail through an avoidable
interface or implementation defect. Candidate and official identities are
separate in the raw rows, so the metric is not circularly defined by A2 output.
Native tree and native turn remain comparisons/diagnostics rather than being
misrepresented as the decisive external baseline.

The available provenance also supports a bounded source-only statement:

- the initial and follow-on packet files expose task text, source-native turn
  summaries, operation IDs, and source references but no official-stage field;
- both collections use the same collection question and sparse complete-path
  annotation contract;
- the fixed annotation guide explicitly forbids official stages, scores,
  outcomes, recurrence/Qwen outputs, the first 41 annotations, and other
  workers' annotations;
- the current inference summary records that official manifests and stages
  were not opened before annotation completion.

This is good leakage control, but it is execution provenance rather than a
cryptographic guarantee of what every annotation worker accessed. The review
can verify absence of gold fields from the supplied packets; it cannot
independently reconstruct every worker's complete tool history.

The statistical and paper scope is necessarily adaptive:

1. This 364-session complement hypothesis and its decision rule were written
   after the complete 405-session aggregate had been observed. The interval is
   a useful cluster-resampled sensitivity interval, not preregistered
   confirmatory evidence.
2. The 364 sessions were annotated later under fixed instructions, but they
   belong to the same already observed CodeTrace family. They are not an
   untouched external benchmark or an independent task family.
3. The initial 41 sessions were selected as the longest trajectories, not
   randomly held out: they contain 95--275 operations each and are
   Terminus2-heavy (28 Terminus2, 11 OpenHands, 2 SWE-agent, no
   mini-SWE-agent), while the complement contains 20--93 operations and is
   OpenHands-heavy. The split therefore changes length, framework, model/task,
   and annotation-batch composition together.
4. Independent recomputation gives an initial-subset B-cubed delta of
   `+0.139563`, a follow-on delta of `-0.012167`, and a union delta of
   `+0.041373`. This proves that the positive union comparison is
   selection-sensitive. It does not isolate whether length, framework/task
   mix, annotation-batch behavior, or product-design inspection caused the
   difference.

There is one workflow-only deviation: four plan-review files were produced
even though the experiment skill permits the original review plus at most two
follow-ups. Round 04 merely confirmed removal of an unnecessary
draw-by-draw-equivalence requirement; it changed no population, metric,
baseline, result, or decision and does not invalidate the run.

## Claim audit and exact admissible interpretation

The supported paper-facing sentence proposed in the plan is **not admissible**:
A2 does not retain higher ordinary B-cubed F1 than recurrence on the follow-on
population, and the registered interval does not support a positive effect.
Likewise, this run cannot establish universal tag accuracy, correct nested
topology, semantic-name identity, cross-session equivalence, cross-family
generalization, or superiority in every session or framework.

The exact admissible interpretation is:

> On the complete manifest-defined 364-session CodeTrace follow-on complement,
> current automatic Agent A2 has higher exact adjacent-boundary F1 than
> multi-resolution recurrence (.403 versus .289), but lower ordinary
> operation-level B-cubed F1 (.675 versus .687). The task-cluster bootstrap
> interval for the B-cubed difference is [-.0273, +.0032], so the registered
> positive structure-fidelity hypothesis is inconclusive. A2's .910 precision,
> .536 recall, 5,198 predicted occurrences for 2,382 official stages, and
> 1,623 singleton occurrences are consistent with oversegmentation on this
> shorter, differently composed complement. Because this was a post-aggregate
> analysis within the already observed CodeTrace family, it is sensitivity and
> mechanism-boundary evidence, not untouched generalization.

No thesis or RQ change follows. The next paper decision is to withhold the
planned positive A2-over-recurrence B-cubed claim, retain the result as an
internal algorithm/generalization boundary, and require a genuinely fixed
future backend on an appropriate complete population before making a broader
positive automatic-structure claim. The full-run report's suggested Qwen run
is one possible future experiment, not evidence from this run and not a
required consequence of this review.
