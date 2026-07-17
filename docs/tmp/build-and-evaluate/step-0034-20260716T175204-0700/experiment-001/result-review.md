# Independent Result Review: RQ3 Cross-Domain Percentile Calibration

## Scope and verdict basis

I reviewed the complete user instruction, approved experiment plan, both plan-review rounds, result report, and the full 1,115-line evaluation implementation. I streamed and parsed all 68,996 requested raw records: 24,844 operation assignments, 24,152 pair decisions, and 20,000 bootstrap draws, as well as `summary.json`. I also independently reconstructed all 24,152 unscored predictions from the original visible-operation inputs. I did not import the experiment's metric, NPMI, CDF, cutoff-fitting, or bootstrap functions for the independent calculations.

The run is complete for the registered negative path. The preflight and full artifact trees have the expected mode fields and a coherent timestamp sequence. The report gives the approved commands, and the recorded inputs equal the script defaults. There is no command transcript that proves the literal shell invocation, but the emitted modes, paths, full populations, and deterministic outputs are consistent with those commands; I found no scientific or configuration deviation that changes a result. Because the registered positive rule fails, the plan does not require the conditional Rust port or replay. No Rust source path was modified.

## Population, key, and mechanism checks

The independently observed target populations are exactly the registered ones:

- OSWorld-Human: 287 sessions, 3,978 operations, 3,691 adjacent pairs, 2,042 oracle groups, and fold strata of 45/55/60/62/65 sessions.
- CodeTraceBench: 2,229 unlabeled score-reference sessions with 87,703 operations; 483 solved calibration sessions with 18,152 operations and 2,886 stages; and 405 failed target sessions with 20,866 operations, 20,461 pairs, and 2,948 stages. Target framework strata are 213 OpenHands, 28 SWE-agent, 93 Terminus2, and 71 mini-SWE-agent sessions.

Every `(session, operation_index)` and `(session, position)` key is unique and complete. Operation indices and pair positions are consecutive within every session; each session has exactly one fewer pair than operations. All oracle and predicted group identifiers are session-scoped. For all 24,152 pairs, each stored oracle boundary exactly equals the change between adjacent oracle assignments, and every method boundary exactly equals the change between that method's adjacent assignments. The unscored and scored pair keys and all three decisions agree exactly. Thus every method is evaluated on identical target rows with no missing or duplicated operation.

The mechanism engaged materially. Percentile transfer changed 329 of 3,691 OSWorld decisions and 2,784 of 20,461 CodeTrace decisions relative to direct raw-cutoff transfer. It differed from label-free recurrence on 1,340 and 6,044 decisions, respectively. OSWorld had 95 unseen target-reference pairs (2.574%), all handled as boundaries as registered; CodeTrace had none.

The word "complete" must retain the approved eligibility scope. The OSWorld source artifact contains 6,010 rows from 369 sessions; the registered population excludes 1,999 content/length-mismatch rows and 33 exact-alignment singleton rows, leaving the complete exact-aligned, multi-operation population above. CodeTrace uses all 405 source-valid failed sessions in its target artifact; 112 manifest sessions are absent from the pre-existing operation extraction, including 63 additional failed sessions. No operation or session was dropped post hoc from either registered target population.

## Empirical-CDF and source-fit audit

An independent NPMI implementation reproduced the source/reference associations. The OSWorld source CDF contains 3,691 transition occurrences and 110 distinct scores over `[-0.453050, 1.0]`; the CodeTrace reference CDF contains 85,474 occurrences and 78 distinct scores over `[-0.362075, 0.747220]`. For each association, independently sorting occurrence scores and applying `count(score <= x) / occurrences` reproduced every persisted target NPMI and percentile. All values are finite, bounded in `[0,1]`, and monotone. Candidate continuation is exactly `percentile >= q`; missing pairs are boundaries.

Independent source fitting also reproduced the selected cutoffs, tie counts, and source B-cubed optima:

| Grouped source | Percentile cutoff | Raw cutoff | Source B-cubed F1 | Best ties |
|---|---:|---:|---:|---:|
| CodeTrace solved | 0.223272574 | -0.098246630 | 0.695599516 | 1 |
| OSWorld-Human | 0.702384178 | 0.266551353 | 0.804589049 | 1 |

The percentile and raw cutoffs induce identical source partitions, as required of a monotone transform. One harmless representation nuance should be recorded: the shared cutoff fitter chooses separating midpoints, whereas the plan describes selecting over finite observed CDF values. The two percentile cutoffs lie between `0.222278120/0.224267029` and `0.702248713/0.702519642`, respectively. No target percentile lies in either midpoint-to-next-observed gap, so choosing the corresponding observed separator produces exactly the same target decisions and cannot affect this result.

Target-label separation is adequate for the scientific comparison, with one literal reporting qualification. For CodeTrace, the unscored predictions were persisted at 18:16:25.912; target-stage ID selection and extraction began afterward, at 18:16:25.914 and later. The initial manifest read excludes the `stages` column, so failed-target stage labels are unavailable to prediction. For OSWorld, however, `osworld_source()` reads the label-bearing JSON rows and uses `human_group` presence plus `group_alignment=exact` to form the predeclared eligible population before prediction. It returns only ordered action sequences, and no group identity or boundary reaches NPMI, fitting, CDF construction, or prediction; the oracle mapping is separately built after persistence. Therefore the report's literal statement that OSWorld labels are first *loaded* after prediction is too strong, but the registered fixed-population selection does not leak target group values into a method or alter comparative information. I treat this as a provenance wording deviation, not an outcome-invalidating leak. The booleans in `summary.json` alone would not establish this conclusion; it follows from the data flow and raw artifact ordering.

## Independent metric recomputation

I computed standard operation-weighted B-cubed precision and recall from cluster intersections, then their harmonic mean. I separately derived exact boundary confusion counts, precision, recall, and F1 from the raw pair decisions. The results match the authored summary (the largest floating difference is rounding-level):

| Target | Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary P | Boundary R | Boundary F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| OSWorld | percentile | 0.575011 | 0.824768 | 0.677607 | 0.498542 | 0.292308 | 0.368534 |
| OSWorld | raw transfer | 0.505448 | 0.874150 | 0.640531 | 0.537143 | 0.214245 | 0.306314 |
| OSWorld | label-free | 0.855872 | 0.726966 | 0.786170 | 0.591811 | 0.798860 | 0.679922 |
| CodeTrace | percentile | 0.947623 | 0.315368 | 0.473242 | 0.160897 | 0.793158 | 0.267524 |
| CodeTrace | raw transfer | 0.978517 | 0.250214 | 0.398523 | 0.149413 | 0.900118 | 0.256284 |
| CodeTrace | label-free | 0.828579 | 0.533630 | 0.649173 | 0.199784 | 0.510028 | 0.287106 |

Label-free recurrence is a fair current-practice baseline: it uses the same target-visible action sequences, target score-reference population, folds/strata, and target rows, but no grouped source labels. Its complete-population B-cubed and boundary values reproduce the existing Step 0024 records. Raw transfer is the claim-critical equal-information comparison: it receives exactly the same source labels, target association, target rows, and scalar-decision budget as percentile transfer. The higher-information per-domain control is correctly kept separate and is also consistent with its source summary (B-cubed F1 0.801087 on OSWorld and 0.666564 on CodeTrace).

## Bootstrap and registered interpretation

I first replayed all 10,000 stored draws per target from independently derived per-session B-cubed sufficient statistics. Every stored candidate, raw, label-free, and delta value agrees, with maximum absolute error `2.22e-16`. The saved empirical percentile intervals are therefore correctly computed from the raw operation assignments:

| Target | Contrast | Point delta | Saved paired 95% interval | Independent paired 95% interval |
|---|---|---:|---:|---:|
| OSWorld | percentile - label-free | -0.108562 | [-0.138246, -0.078428] | [-0.138561, -0.077852] |
| OSWorld | percentile - raw | +0.037077 | [+0.019693, +0.055919] | [+0.019549, +0.056646] |
| CodeTrace | percentile - label-free | -0.175931 | [-0.189732, -0.161417] | [-0.189822, -0.161459] |
| CodeTrace | percentile - raw | +0.074719 | [+0.057926, +0.094771] | [+0.058240, +0.094136] |

The independent intervals use a separate NumPy generator and vectorized stratified resampler, still with seed `20260716`, paired methods, session units, five OSWorld folds, four CodeTrace frameworks, and 10,000 draws. Their close agreement confirms that the conclusion is not an artifact of the stored draw sequence. Repeated sessions contribute repeated per-session sufficient statistics, which is equivalent to replica-unique session cluster IDs because all group IDs are session-scoped.

The registered classification is mutually exclusive for this outcome. Support fails because candidate-minus-label-free is negative in both targets and both intervals are wholly negative. Mixed fails because the label-free signs are negative in both targets and the raw-transfer signs are positive in both. The contradictory rule then applies because percentile transfer improves neither target over label-free. Inconclusive is not reached because the positive point ordering itself fails. The authored `contradicted` classification is therefore correct.

Percentile normalization nevertheless beats raw scalar transfer in both domains with positive intervals, so score-scale mismatch was real and the normalization engaged. Its remaining failure is large and directionally different: it over-merges OSWorld into 1,316 groups but over-fragments CodeTrace into 12,941 groups. This is consistent with the registered competing explanation that the source thresholds encode different operation-group semantics rather than only differently scaled NPMI. Two reused domains cannot uniquely prove that causal explanation, but they decisively reject this specific bidirectional calibration rule against the current label-free constructor.

The reader-facing `docs/agentpprof-paper` submodule is clean at its registered gitlink and HEAD `7f80c433c9555317a2aa45a78d0ff93518f4c12c`; the `bpftool` gitlink is also unchanged. No Rust port is required or present. The valid result supports only the predeclared mechanism boundary: retain Step 0024 label-free recurrence as default, retain Step 0030 per-domain grouped calibration as optional, record this negative branch in evaluation history, and make no reader-facing paper, thesis, RQ, hypothesis, or story change.

run status: valid

tested hypothesis: contradicted

research value: supporting

paper impact: mechanism or workload boundary

next paper decision: keep the label-free default and optional per-domain calibration, close cross-domain percentile transfer, and make no reader-facing paper or story change
