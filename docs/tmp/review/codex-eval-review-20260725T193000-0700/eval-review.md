# Independent Evaluation Audit

## Verdict

**Verdict: weak reject / high accept risk (AAAI-style confidence: high).**

The evaluation is unusually broad and, with one important exception, numerically
well recorded: the four RQ tables reproduce from the experiment records under
documented rounding, the abstract and introduction repeat the body numbers
correctly, and all explicit appendix/figure references resolve. The central
acceptance risk is claim scope rather than arithmetic.

The strongest defensible result is that AgentProf can encode a recursively
annotated hierarchy in standard pprof, conserve additive measures, replay it
cheaply, and use it as an index over source evidence. The current evidence does
not yet establish the broader implications that (i) semantic profiling improves
resource-attribution decisions, (ii) the semantic hierarchy improves target
ranking over an information-matched raw hierarchy, (iii) profile-guided reading
is cheaper overall, or (iv) a final-quality automatic hierarchy can be
constructed at the reported end-to-end annotation cost. The “Long Horizon”
title also scopes the paper more narrowly and more strongly than the evaluation:
only one selected 41-session cohort and one three-run case directly exercise
long trajectories, and no main accuracy, reader, or cost result is stratified by
horizon.

One provenance defect needs correction before submission. The current Case
Study 2 recovery counts (`3,286` bad and `455` good) cannot be found in a
durable source record under `docs/tmp/build-and-evaluate/`. Its current
bootstrap intervals are repeated by a review narrative, but the primary
result record contains older values. All other audited headline values are
traceable.

## Provenance key

The traceability table uses the following exact source files:

- **S65-CS2:** `docs/tmp/build-and-evaluate/step-0065-20260721T234809-0700/experiment-001/case-study-2-protocol.md`
- **S66-LH:** `docs/tmp/build-and-evaluate/step-0066-20260722T004313-0700/step-report.md`
- **S67-CS:** `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/write-consistency-review.md`
- **S67-RQ1:** `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-001/full-results.md`
- **S67-CS2R:** `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-003/result-review.md`
- **S70-A:** `docs/tmp/build-and-evaluate/step-0070-20260723T003932-0700/outer-audit.md`
- **S71-RQ3:** `docs/tmp/build-and-evaluate/step-0071-20260723T015043-0700/experiment-001/results.md`
- **S71-RQ3R:** `docs/tmp/build-and-evaluate/step-0071-20260723T015043-0700/experiment-001/independent-result-review.md`
- **S71-RQ4:** `docs/tmp/build-and-evaluate/step-0071-20260723T015043-0700/experiment-002/results.md`
- **S71-RQ4R:** `docs/tmp/build-and-evaluate/step-0071-20260723T015043-0700/experiment-002/independent-result-review.md`
- **S72-RQ2:** `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/experiment-001/full-run-report.md`
- **S72-RQ2R:** `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/experiment-001/independent-result-review.md`
- **S72-P:** `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/experiment-001/experiment-plan.md`
- **S75-A2:** `docs/tmp/build-and-evaluate/step-0075-20260723T214459-0700/experiment-001/full-run-and-result.md`
- **S75-A2R:** `docs/tmp/build-and-evaluate/step-0075-20260723T214459-0700/experiment-001/independent-result-review.md`
- **S76-RQ1:** `docs/tmp/build-and-evaluate/step-0076-20260723T224718-0700/experiment-001/full-run-and-result.md`
- **S76-RQ1R:** `docs/tmp/build-and-evaluate/step-0076-20260723T224718-0700/experiment-001/independent-result-review.md`
- **S76-REV:** `docs/tmp/build-and-evaluate/step-0076-20260723T224718-0700/03-review-gate/milestone-review-001/03-source-grounded-full-paper-assessment.md`
- **S77-C:** `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/code-review-001.md`
- **S77-F:** `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`
- **S77-G:** `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/git-convergence-result.md`
- **S77-T:** `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/terminal-case-answerability-and-cost-audit.md`
- **S78-RQ1:** `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/experiment-001/results.md`
- **S78-RQ1R:** `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/result-review.md`
- **S79-READ:** `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/results.md`
- **S79-READR:** `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/result-review.md`
- **S80-SEM:** `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/results.md`
- **S80-SEMR:** `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/result-review.md`
- **S81-RAW:** `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/results.md`
- **S81-RAWR:** `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/result-review.md`
- **S06-OSW:** `docs/tmp/build-and-evaluate/step-0006-20260714T031808-0700/01-experiment-gate/loop-001-rq3-osworld-boundary-fidelity/009-full-run-result-report-20260714T033856-0700.md`
- **S08-PART:** `docs/tmp/build-and-evaluate/step-0008-20260714T083320-0700/01-experiment-gate/loop-001-rq3-task-phase-action-reuse/full-result-report.md`
- **S24-REC:** `docs/tmp/build-and-evaluate/step-0024-20260715T042557-0700/experiment-001/full-run.md`
- **S30-REF:** `docs/tmp/build-and-evaluate/step-0030-20260715T161256-0700/experiment-001/experiment-result.md`
- **S31-TASK:** `docs/tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-002/result-report.md`
- **S32-ACT:** `docs/tmp/build-and-evaluate/step-0032-20260716T010251-0700/experiment-001/result-report.md`

## Number traceability

“Exact” includes formatting and documented rounding in the paper. “Partial”
means the value appears only in a later narrative or an older incompatible
result, not in a reproducible primary record.

### RQ1 and Case Study 1

| Paper number(s) | Source | Match |
|---|---|---|
| 41 trajectories; 3,146 turns; 5,750 operations | S67-RQ1; the top-decile definition and 95–275 operations/session range are in S66-LH | **Exact.** The paper omits the 95–275 range that gives “long-horizon” operational meaning. |
| Three repeated Git executions | S67-RQ1, S76-RQ1 | **Exact.** |
| 96 recursive annotations; 735 source nodes; depth 5; 0 unary, 0 flat-fan-out, 27 coarse-leaf warnings | S67-CS | **Exact.** S76-RQ1 reports a later matched projection with 79 transitions; that is a different artifact, not a contradiction. |
| 489 operations; 4,558,192 provider-reported tokens | S67-RQ1, S76-RQ1 | **Exact.** All six matched projections in S76 conserve both masses. |
| Terminus2 56.24%; OpenHands 43.76%; OpenHands 86.62% of tokens | S67-RQ1 | **Exact** (`275/489`, `214/489`, and `3,948,391/4,558,192`). |
| Direct SSH focus: 97 operations and 1,936,828 tokens | S67-RQ1 | **Exact.** |
| Recursive SSH subtree: 105 operations and 2,103,587 tokens; 21.47% and 46.15% | S67-RQ1 | **Exact** under rounding. |
| Six coarse action kinds; largest 39.42%; 102/105 are `run`; 97 unrelated operations | S76-RQ1, S76-RQ1R | **Exact** under rounding. |
| AgentRewardBench: 440 sessions, 125 tasks, 7,229 operations, 51,904,621 tokens | S78-RQ1 | **Exact.** |
| 77 rankable tasks; 10,000 bootstrap draws | S78-RQ1 | **Exact.** |
| Kendall tau-b .886 [.857,.915]; Spearman rho .935 [.917,.953]; pooled tau-b .929 | S78-RQ1, S78-RQ1R | **Exact** after rounding from `.8863 [.8568,.9147]`, `.9350 [.9166,.9527]`, and `.9286`. |
| 10/77 tasks below tau-b .7; Git importance changes by more than 2× | S78-RQ1; S67-RQ1 | **Exact.** |

### RQ2

| Paper number(s) | Source | Match |
|---|---|---|
| 614, 400, and 220 target-bearing queries; 522 zero-positive trajectories | S72-P, S72-RQ2, S72-RQ2R | **Exact.** The complete populations are 1,000, 536, and 220 trajectories; 1,234 are target-bearing and 522 are zero-positive. |
| Table: AgentProcessBench `.894/.893/.863/.791` | S72-RQ2 | **Exact** from `.8943/.8931/.8632/.7906`. |
| Table: HINTBench `.517/.518/.411/.432` | S72-RQ2 | **Exact** from `.5175/.5180/.4106/.4324`. |
| Table: TraceElephant `.326/.324/.209/.259` | S72-RQ2 | **Exact** from `.3255/.3239/.2087/.2593`. |
| MAP gains over Direct-only: .031 [.024,.039], .107 [.093,.120], .117 [.088,.148] | S72-RQ2, S72-RQ2R | **Exact** after rounding from `.0311 [.0237,.0393]`, `.1069 [.0934,.1204]`, and `.1168 [.0876,.1479]`. |
| Raw-evidence matched MAP `.893/.518/.324` | S72-RQ2 | **Exact.** |
| Candidate-minus-raw intervals `[-.0003,.0029]`, `[-.0116,.0103]`, `[-.0247,.0280]` | S72-RQ2, S72-RQ2R | **Exact.** These intervals all include zero. |
| Reader study: 220 queries; full reader MAP .502; Direct-only .209; Direct+AgentProf .326; 12,615 input tokens/query | S79-READ, S79-READR | **Exact** under rounding. The same record reports 29.9 seconds/query, which the paper does not report. |
| Profile-guided reader: at most 5 groups; MAP .455; 53.0% source content; no stage-one fallback | S80-SEM, S80-SEMR | **Exact.** |
| Raw skeleton: MAP .465; raw-minus-semantic +.010 [-.021,+.042] | S81-RAW, S81-RAWR | **Exact** from `.465129` versus `.455333` and `+.009795 [-.020767,+.042417]`. |
| Raw 65.0% versus semantic 53.0%; delta +.120 [+.103,+.137] | S81-RAW, S81-RAWR | **Exact** from `.6501/.5301` and `+.1200 [.1034,.1367]`. |
| Raw opens 2.80 [1.96,3.60] more evidence operations | S81-RAW, S81-RAWR | **Exact.** |
| Repeated Git task 4,558,192 tokens | S67-RQ1, S76-RQ1 | **Numerically exact, but the RQ2 reader was not run on this task.** Also, this is the aggregate over three executions, not a demonstrated single-query packet size. |

The reader paragraph omits two load-bearing measured costs. S80-SEMR reports
`4,837 + 11,154 = 15,991` logical input tokens/query for the semantic two-stage
reader versus `12,615` for the full reader (1.27×), and S80-SEM reports 50.2
seconds/query versus 29.9 seconds/query in S79-READ. Therefore “opening 53% of
source content” is correct, but it is not an overall token- or latency-saving
result.

### Case Study 2

| Paper number(s) | Source | Match |
|---|---|---|
| 440 trajectories; 125 tasks; 338 pairs; 24/102/144/68 by benchmark; 202 success and 238 failure sessions | S65-CS2, S67-CS | **Exact.** Pair-occurrence weighting is correctly disclosed. |
| Three workers; 2,131 annotations; 7,229 source operations; depth 4; 338 bad and 338 good members | S67-CS, S77-C | **Exact for the frozen paper artifact.** The later fresh pass in S77 used a two-worker schedule and produced 2,193 annotations, so these must not be described as the current fresh-pass output. |
| 3,286 bad versus 455 good occurrences under `recover interaction` | No matching primary record found under `docs/tmp/build-and-evaluate/` | **Untraced.** S67-CS contains the older `2,993/392` values. `rg` over the experiment tree finds no durable `3,286` record. This is the clearest provenance failure. |
| 135 bad versus 191 good under `report completion` | S67-CS | **Exact.** |
| 7,366 bad and 3,780 good total occurrences | S77-T | **Exact.** |
| Recovery 44.6% bad versus 12.0% good; completion 1.8% versus 5.1% | S70-A for the current percentages; S67-CS for completion | **Partial.** The recovery percentages appear in S70-A, but their implied counts are not preserved in a primary result. S67-CS instead reports the older recovery values 40.6% and 10.4%. |
| 435 consensus-labeled trajectories; recursive AP .634; prevalence .398 | S77-T | **Exact** for the frozen paper hierarchy. |
| AP-minus-prevalence [.181,.293]; fixed-chain AP .656; recursive-minus-fixed [-.107,.061] | S76-REV and S77-T | **Partial.** S77-T preserves `.634/.398/.656` but not the two intervals. The intervals are stated in the later review narrative S76-REV, not in a current primary result artifact. S67-CS2R contains an older recursive AP `.613735` and older intervals `[.162023,.273910]` and `[-.127370,.041557]`. |

The frozen case hierarchy and the later fresh automatic backend are materially
different. S77-T reports that the fresh terminal annotation lacks the shared
recovery parent and falls to prevalence AP (`.397701`), while the paper reports
the frozen hierarchy's `.634`. That does not invalidate the frozen case study,
but it makes artifact/version identity a load-bearing disclosure.

### RQ3

| Paper number(s) | Source | Match |
|---|---|---|
| CodeTraceBench: 405 trajectories; 20,866 operations; 2,948 stages; 17,148 turns | S71-RQ3, S71-RQ3R | **Exact.** |
| Repair removes 149 artificial leaf groups; 5,752 marks at depths 1/2/3 = 51/5,608/93 | S71-RQ3 | **Exact.** |
| 5,537 open names mapped to 1,434 canonical IDs; no adjacent collision | S71-RQ3, S71-RQ3R | **Exact.** |
| CodeTrace table, Automatic Agent: `.839/.607/.704/.394` | S71-RQ3 | **Exact** from `.839025/.606577/.704113/.393916`. |
| Recurrence: `.782/.575/.663/.266` | S71-RQ3 | **Exact** from `.782026/.575029/.662740/.265571`. |
| Native source tree: `.975/.249/.397/.259`; source-native turn: `.983/.221/.361/.246` | S67-RQ1 | **Exact** under rounding. |
| Raw-action B3 `.541` | S71-RQ3 | **Exact** under rounding. |
| Agent-minus-recurrence .0414 [.0214,.0606]; Agent-minus-raw .163; boundary .394 versus .266 | S71-RQ3, S71-RQ3R | **Exact** under rounding. |
| Conserved 20,866 operations and 494,862,929 tokens | S71-RQ3, S75-A2 | **Exact.** |
| OSWorld: 287 sessions; 3,978 operations; 3,691 pairs; 2,042 groups | S06-OSW | **Exact.** |
| OSWorld supervised `.700/.782/.739/.816` | S06-OSW | **Exact** from `.699796/.782336/.738768/.816019`. |
| Reference-calibrated `.610/.922/.734/.801` | S30-REF | **Exact** from `.609646/.921937/.733953/.801087`. |
| Label-free `.592/.799/.680/.786` | S24-REC | **Exact** under rounding. |
| Always-boundary `.476/1.000/.645/.678`; action-change `.386/.626/.477/.659`; phase-change `.441/.268/.334/.665` | S06-OSW | **Exact** under rounding. |
| Mind2Web: 9 sessions, V=.557; ScienceWorld: 100 sessions, V=.815 | S08-PART | **Exact** from `.5565` and `.8151`. |
| Task family: 27B evaluation backend; 1,012 goals, 9 classes; `.695/.733` versus `.044/.248`; 3 identical runs | S31-TASK | **Exact** under rounding. |
| Action: 27B backend and 8 definitions; 2,737 labels, 120 trajectories; `.498/.628` versus `.061/.323`; gain `.437 [.380,.494]`; 2 identical runs | S32-ACT | **Exact** under rounding. |
| 39 `Locate` inputs; after exclusion `.490/.622` | S32-ACT | **Exact** under rounding. |

### RQ4

| Paper number(s) | Source | Match |
|---|---|---|
| Cost table rows: `729/.04/.03/19.3`, `4,285/.17/.14/73.9`, `6,010/.24/.21/109.1`, `16,741/.70/.58/279.3`, union `27,765/1.16/.97/465.2` | S71-RQ4, S71-RQ4R | **Exact.** |
| Three runs; `agentpprof 0.2.37`; 24-core Core Ultra 9 285K; 125 GiB RAM; Linux 6.15.11 | S71-RQ4 | **Exact.** |
| Slope .0418 ms/op; R2 .9997; 23,935 operations/s | S71-RQ4 | **Exact** from `.041825`, `.999679`, and `23,935`. This is a five-point descriptive fit across heterogeneous workloads, not a controlled same-workload scaling law. |
| Union overhead 190 ms/19.6% and 5.25 MiB/1.14% | S71-RQ4 | **Exact.** |
| A2 first-construction total 506.35 s; both widths replay in 1.17 s; byte-identical artifacts; 405 sessions | S75-A2, S75-A2R | **Exact.** Components are 501.64 s packet construction, 3.54 s assembly/canonicalization, and 1.17 s replay. |
| AgentRewardBench fresh pass: 440 sessions, 12 batches, 3,521.6 s/58.7 min, 6,661.7 worker-seconds, 12,039,417 actual input, 10,929,408 cached, 312,433 output, 27,362/710 per session | S77-F, S77-T | **Exact** under rounding. **Scope caveat:** S77-T explicitly says this is a fresh pass only, not clean fresh-to-terminal convergence. |
| Git fresh pass: 3 sessions, 466.9 s, 832,544 input tokens | S77-G | **Exact.** |
| Materialization .26 s operations/.25 s tokens | S77-F | **Exact.** |
| Prior artifact envelope 54.36 min | S75-A2 | **Exact.** |

There is a terminology inconsistency in the final cost paragraph. The
3,521.6-second wall clock includes provider calls and is presented as
“end-to-end,” yet the paragraph concludes that “model/provider inference
remains outside the instrumented timing.” The source records support the
narrower statement that provider inference is included in aggregate wall time
but is not separately isolated.

The RQ4 row labeled “AgentRewardBench” has 729 operations, whereas the complete
mixed-outcome AgentRewardBench case has 7,229 operations. Both values reproduce
from their respective records, but calling both a “complete” workload without
identifying the snapshot/projection makes the scope internally ambiguous.

## Top five reviewer attack points

### 1. The reported automatic-annotation cost is not the cost of obtaining the final accepted hierarchy

> “A fully instrumented end-to-end automatic annotation now exists.”

The reported 3,521.6 seconds and 12,039,417 input tokens cover one fresh pass.
S77-T explicitly states that they are **not** a clean fresh-to-terminal
measurement. The same audit records seven nonconvergent review rounds consuming
191,838,723 provider input tokens and 21,166.766 seconds, followed by a
3,691,400-input-token, 387.202-second no-change check. Those failed-policy costs
should not replace the fresh-pass number, but they prove that the paper has not
measured the cost of reaching its frozen final-quality hierarchy. This matters
because the fresh terminal hierarchy also loses the shared recovery parent used
by Case Study 2. The claim should be “instrumented fresh first pass,” and the
paper needs either a clean fresh-to-final run or an explicit statement that
final-quality construction cost is unknown.

### 2. RQ1 demonstrates replay and a post-hoc organization, not improved attribution correctness or an engineering decision

> “This repeated real task supports RQ1's multi-resource attribution hypothesis: one shared responsibility path reunites the SSH work across executions, while the selected additive measure changes its attributed importance.”

The mass conservation and count/token differences are real, but the SSH
responsibility was selected from the prior semantic case. The matched replay is
therefore a visualization/organization control, as the paper itself admits, not
independent discovery or attribution accuracy. Population-wide count/token
rank agreement is very high (tau-b .886), and no developer decision, diagnosis
time, correctness judgment, or independent responsibility gold standard is
measured. The later sentence “The regimes where selecting the measure changes
the engineering decision are exactly where multi-measure replay pays” is
stronger still: no engineering decision was observed. RQ1 supports
multi-measure replay under one hierarchy; “improves resource attribution”
remains untested.

### 3. “Less evidence opened” is not lower reader cost

> “Semantic naming's measured contribution in this regime is attention concentration at equal quality.”

This is defensible only if “attention concentration” is defined strictly as
source content opened. The semantic reader consumes 15,991 logical input
tokens/query versus 12,615 for the full reader (1.27×) and takes 50.2 seconds
versus 29.9 seconds, because it makes two calls. Its MAP is also .455 versus
.502 for full reading. Against the raw skeleton, ranking is statistically
tied and semantic naming opens less source, which is a useful mechanism result;
however, the abstract and RQ2 prose omit the total-token and wall-time reversal.
The evaluation needs an equal-total-token/equal-latency comparison, or it must
say “opens fewer source characters/operations” rather than imply lower reading
cost.

### 4. Case Study 2's explanatory result is artifact-sensitive, weaker than its fixed-chain detector, and incompletely sourced

> “This case answers RQ2 at collection scale: a target-blind recursive profile exposes failed-side recovery and successful-side completion under shared responsibilities, and its recovery signal corresponds to an independently annotated real problem.”

The frozen recursive score corresponds to looping (AP .634 versus prevalence
.398), but the registered fixed chain is numerically better (.656), the
recursive-minus-fixed interval includes zero, and AgentRewardBench has no gold
nested hierarchy. More seriously, the current `3,286/455` recovery counts are
not traceable to a primary result record, the current confidence intervals
appear only in a review narrative, and S77-T says the fresh terminal hierarchy
loses the shared recovery parent and falls to prevalence AP. The case supports
a qualitative, source-drillable explanation for one frozen artifact—not
backend-stable recursive superiority, topology accuracy, or causality. The
paper needs to identify the exact frozen artifact and restore a primary raw
result/manifest for every displayed count and interval.

### 5. The long-trace extrapolation—and therefore the new title—is not experimentally tested

> “A per-query full read is bounded by the model context window: populations such as the 4,558,192-token repeated Git task cannot be read whole, whereas skeleton-guided drilldown remains available at any trace length.”

The 4,558,192 tokens aggregate three executions, while the reader study uses
220 much shorter TraceElephant queries. No reader is run on the Git case, no
single-trajectory context size is reported here, and “any trace length” is an
unbounded system claim with no depth/size stress test. The title elevates this
extrapolation to the paper's scope even though RQ2, RQ3, and RQ4 do not report
performance by trajectory length. Replace “at any trace length” with the
mechanical claim that the stored skeleton supports selective drilldown, or add
an over-context long-trajectory reader and scaling experiment.

## Other claim-evidence mismatches

These are additional to the top five and should be narrowed or supported:

| Targeted claim | Why the evidence is narrower |
|---|---|
| “RQ1 asks whether semantic profiling improves resource attribution.” | The experiment tests whether two additive weights change widths under a fixed hierarchy. It does not compare attribution correctness, diagnostic decisions, or developer outcomes against another profiler/interface. |
| “Only the semantic organization yields one focusable cross-run responsibility, exposing a bottleneck an operation-count view understates.” | “Only” is true among the three post-hoc projections, but the responsibility was selected from the semantic case. This is not a blind discovery comparison. |
| “Thus the profile adds clear ranking information after a fixed trajectory reader on all three complete workloads.” | The profile-plus-evidence refinement improves over Direct-only, but the information-matched raw-plus-evidence condition ties it. The gain is not attributable to the semantic prefix. |
| “This tie is the expected mechanism boundary.” | The tie is observed, but “expected” is a post-hoc mechanism interpretation unless a preregistered prediction identifies it. |
| “Full-trace reading reaches MAP .502 … at a mean 12,615 input tokens per query.” | The reader is a single Grok-family CLI configuration on one benchmark and is stronger than the benchmark localizer. It is not a general human or model-reader result. |
| “skeleton-guided drilldown remains available at any trace length” | Availability at unbounded length is not measured; parsing, model selection over the skeleton, nesting depth, and packet limits can all scale with length. |
| “The Agent-assisted backend is the strongest tested automatic constructor on this complete population” | True only for a complete **development** population and the listed controls. CodeTrace is not an untouched test population, and stronger segmentation/canonicalization baselines are absent. |
| “construction cost is dominated by the automatic backend, and replay remains sub-second” | The reported operations/tokens materializations are sub-second, but the A2 replay is 1.17 seconds. “Replay remains near one second” is internally safer. |
| “Both time curves are monotonic … slope … R2=.9997” | The five points are different workloads with different record structure, not controlled rescalings of one workload. The fit is descriptive and cannot establish asymptotic scaling. |
| “current binary … practical construction cost” and conclusion-level “making population profiling practical” | Fixed-mark replay is fast, but initial annotation consumes about an hour and 12M input tokens for 440 sessions; final-quality convergence cost is unknown. “Practical” needs a workload/cost budget or user study. |
| Abstract: “guides a strong trajectory reader to equal ranking quality while opening 53.0% … versus 65.0%” | Equal quality is relative to raw skeleton, not full reading; full reading is .502 versus .455. The abstract should name the comparator and disclose that lower opened source does not lower total input or latency. |
| Abstract: “drilldown remains available beyond the context window where whole-trace reading fails” | Mechanically plausible but not evaluated on an over-context trace. |
| Conclusion-level population claims | The evaluation spans several public populations, but backend protocols differ materially and several are development populations. They should not be combined into a generalization claim about unseen agents or long-horizon behavior. |

## Missing baselines and experiments a skeptical reviewer will request

### RQ1

- An independent responsibility/attribution ground truth, or a blinded
  developer task measuring bottleneck identification, correctness, time, and
  resulting engineering decision.
- A direct comparison with native trace trees, raw/coarse groupings, and a
  conventional observability view at population scale, not only a selected
  post-hoc Git responsibility.
- Replication on more than one repeated task and on an untouched population,
  with a predeclared condition under which changing count to tokens should
  change the diagnosis.

### RQ2 and the reader study

- Full-reader and profile-reader results on AgentProcessBench and HINTBench, not
  only TraceElephant.
- Equal-total-input-token, equal-number-of-calls, and equal-wall-time controls.
  Opened source percentage is not an end-to-end efficiency metric.
- Flat, random, largest-group-first, and size-matched skeleton controls in
  addition to raw-action grouping.
- A user or analyst study measuring diagnosis accuracy/time, or at least
  multiple reader models and prompts.
- Strong current trajectory-localization baselines under the same target-blind
  input contract. The benchmark-native diagnostic is not necessarily the
  strongest available reader, as the paper's own full reader shows.

### Case Study 2

- A durable raw result/manifest for the displayed `3,286/455` counts and current
  confidence intervals.
- The native/raw differential profile as a visual and quantitative comparator,
  plus replication on a second mixed-outcome population.
- A clean run showing that the current automatic backend reconstructs the
  frozen recovery hierarchy, or an explicit versioned-artifact statement that
  the case is not representative of the current fresh backend.

### RQ3

- Stronger automatic segmentation and hierarchy-construction baselines:
  generic LLM segmentation, embedding/change-point segmentation, and the
  closest process-profile/canonicalization systems under identical inputs.
- An untouched cross-framework or cross-dataset test. CodeTraceBench is the
  complete development population, and the OSWorld recurrence design was also
  developed after corpus inspection.
- Stronger literal-label baselines than majority class (for example,
  TF-IDF/linear, embedding nearest-label, and a smaller fixed model). Majority
  is particularly weak for the action result whose macro-F1 is only .498.
- An integrated evaluation of the action adapter. The paper correctly calls it
  standalone; it therefore does not establish current AgentProf CLI behavior.

### RQ4

- Clean fresh-to-final-converged annotation wall time, provider tokens, and
  monetary cost, with cold/warm cache separated.
- Controlled same-workload scaling by number of operations, single-trajectory
  length, and nesting depth. The current union-size fit does not test
  long-horizon scaling.
- Peak-memory and latency at the largest single trajectory, not only population
  union size, and multi-query amortization of the one-time hierarchy cost.
- Clear separation of capture/conversion, packet construction, provider
  inference, orchestration, deterministic materialization, and pprof replay.

## Load-bearing scope disclosures

The following qualifications are scientifically necessary; removing or
burying them would overstate the paper:

- RQ1's 41 sessions are a longest-decile cohort selected by source-visible
  operation count; S66-LH defines the range as 95–275 operations/session.
- The Git matched projection is post hoc and measures organization, not
  independent discovery.
- The high count/token rank correlations mean most tasks do not change dominant
  responsibilities; the 10/77 tail is where the capability may matter.
- RQ2's local-first rule and paths were developed on the evaluated populations;
  the result is adaptive mechanism evidence, not untouched generalization.
- Direct+AgentProf is tied with Direct+Raw+Evidence, so semantic naming does not
  have a demonstrated target-ranking advantage in that experiment.
- The reader is one Grok-family CLI configuration on one workload, is
  query-specific, makes two calls in the semantic condition, and has higher
  total logical input and latency despite opening less source content.
- AgentRewardBench sessions are reused across bad–good pairs, so widths are
  pair-occurrence weighted.
- Case Study 2 has no gold nested semantic hierarchy and supports neither
  topology accuracy nor causality.
- Case Study 2 uses a frozen hierarchy that differs from the current fresh
  terminal automatic output.
- CodeTraceBench and OSWorld-Human are development populations; the
  reference-calibrated OSWorld method consumes group annotations.
- The task-family backend is a distinct 27B evaluation-only model, and the
  action backend is a standalone adapter rather than the integrated AgentProf
  CLI path.
- RQ4's 1.16/1.17-second figures are fixed-mark profile
  construction/replay—not automatic annotation latency.
- The 3,521.6-second annotation figure is a fresh first pass, not measured
  fresh-to-final convergence.
- The core cost table excludes capture, source conversion, annotation, and
  provider inference; the end-to-end fresh-pass wall time includes provider
  waiting but does not isolate it.

## Internal consistency

### Checks that pass

- Abstract, introduction, body, and conclusion agree on the author-fixed thesis:
  **“Agent observability needs profiling, not only debugging.”**
- Repeated headline numbers agree exactly under rounding:
  CodeTrace `405`, `.704/.663/.541`; localization gains
  `.031/.107/.117`; reader source opening `53.0%/65.0%`; OSWorld
  `.680/.786`; task/action `.695/.498`; and cost `27,765/1.16 s`.
- Every RQ table matches its adjacent prose. No table/prose arithmetic
  disagreement was found.
- Every explicit `\ref{}` used by the audited evaluation resolves:
  `fig:flamegraph`, `tab:rq2-localization`, `app:osworld`,
  `app:partition`, and `app:a2-reconstruction`. The broader paper's explicit
  references to `fig:architecture`, `app:canonicalization`, and
  `app:recurrence` also resolve.
- All five PNG files used by the two case-study figures exist under
  `docs/visexp/out/r221-pprof-renderer-v1/`.

### Findings to fix

1. **Case Study 2 artifact/version drift.** The current recovery figure counts
   and intervals are not backed by one current primary result record, and the
   later fresh hierarchy differs from the frozen case hierarchy.
2. **“End-to-end” versus “inference outside timing.”** These phrases conflict.
   Aggregate provider waiting is inside the measured fresh-pass wall clock;
   provider inference is merely not separately instrumented.
3. **Two “complete AgentRewardBench” sizes.** Case Study 2 uses 7,229
   operations, while the RQ4 table uses 729. The paper must identify the
   different snapshot, projection, or filtered workload.
4. **Sub-second replay wording.** RQ4 reports A2 replay as 1.17 seconds. The
   0.25–0.26-second materialization numbers are sub-second; generic “replay
   remains sub-second” is not true for every replay number reported.
5. **Comparator ambiguity in the abstract.** “Equal ranking quality” refers to
   semantic versus raw skeleton (`.455` versus `.465`, statistically tied), not
   semantic versus full reading (`.455` versus `.502`). Name the comparator.
6. **Generic appendix pointers.** `app:rq2-scoring` and `app:scope` exist, but
   the corresponding RQ2 and scope disclosures are sometimes referred to only
   as “the appendix.” Explicit references would make the protocol easier to
   audit. There are no broken references.

## Title fit: “AgentProf: Semantic Profiler for Long Horizon AI Agents”

**Fit assessment: partial, presently high-risk.**

The evaluation has credible long-trajectory ingredients. The selected
CodeTrace cohort contains 41 longest-decile sessions, 3,146 turns, 5,750
operations, and 117,303,194 provider-reported tokens; S66-LH defines the range
as 95–275 operations/session. The repeated Git task aggregates 489 operations
and 4,558,192 tokens across three executions and demonstrates why a compact
index can be useful when raw evidence is large.

That is not yet enough to make “Long Horizon AI Agents” the paper-wide scope:

- The phrase is not operationally defined in the paper. “Longest decile” and
  95–275 operations/session are absent from the main RQ1 text.
- The three public localization populations average approximately 8.5, 24.0,
  and 27.1 operations per complete trajectory respectively (8,509/1,000,
  12,877/536, and 5,960/220); even the target-bearing query subsets are not
  analyzed by horizon.
- CodeTraceBench averages about 51.5 operations/trajectory
  (20,866/405), while OSWorld-Human averages about 13.9 (3,978/287).
- RQ2 does not run the reader on the long Git population. The claim about
  context-window failure is extrapolated from the aggregate token mass.
- RQ3 reports no fidelity versus length/depth bins, and RQ4 scales total
  population size across heterogeneous datasets rather than the length of one
  trajectory.
- Neither case study is replicated on an untouched public long-horizon
  population.

To support the title, the paper should:

1. Define horizon before evaluation using observable operations, turns, tokens,
   and/or duration; report median, p90, p99, and maximum for every workload.
2. Report RQ3 structure fidelity and RQ2 localization/reader utility by
   preregistered horizon bins, including an over-context subset.
3. Run profile-guided reading on one or more individual trajectories that
   exceed the full-reader context budget, under equal total-token and latency
   budgets and with repeated queries to measure hierarchy amortization.
4. Add controlled single-trajectory scaling in operation count and semantic
   depth, including peak memory and skeleton-selection quality.
5. Replicate the repeated-task diagnosis on an untouched public long-horizon
   population.

Without those additions, a safer title is **“AgentProf: A Semantic Profiler for
AI Agent Trajectories”** or **“AgentProf: Semantic Profiling Across AI Agent
Trajectories.”** If the current title is retained, “Long-Horizon” should at
least be hyphenated and the evaluation must make horizon a measured independent
variable rather than a label attached to one selected cohort.
