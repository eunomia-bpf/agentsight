# WRITE report — historical-protocol removal and backend-name sweep

Status: complete  
Edited paper source: `docs/paper/main.tex`  
Other requested deliverable: this report  
Git commands: none

## 1. Main issues

The paper mixed the current direct Agent backend with a historical adopted
artifact. This created three provenance risks:

1. RQ3 retained a historical 0.704/0.394 result and a direct-versus-historical
   comparison even though the current paper answer is the direct-versus-
   recurrence result.
2. RQ4 described 3.54 s assembly, 1.17 s replay, and a 54.36 min artifact
   envelope from the historical marks next to current-backend measurements.
3. Backend-specific names and reconstruction details remained in RQ3, RQ4,
   appendix prose, a subsection title, and a label/reference pair.

## 2. Revision strategy

- Delete historical protocol comparisons and research-history prose.
- Remove every `A2` token from the paper and its bilingual comments.
- Do not neutrally relabel measurements made only on historical marks.
- Retain 501.64 s only because Step 0087 demonstrably reuses the exact source
  packets whose construction Step 0075 timed.
- Replace stale mark/canonicalization counts with Step 0087 current-direct-
  backend counts.
- Use Step 0087's separately measured 11.516 s full deterministic downstream
  pipeline, without presenting it as an equivalent relabel of the historical
  3.54 s assembly or 1.17 s replay values.
- Preserve the thesis, four RQ titles, current-backend results, citations, and
  figures.

## 3. Revised LaTeX text and provenance decisions

### Deletions and relabels by paper location

| Location | Change | Provenance decision |
|---|---|---|
| Design, evaluated-backend paragraph | Deleted the sentence saying an earlier interval-recursive protocol remained in the research record and was outperformed, plus its Chinese text. | Historical development record, not part of the current evaluated backend. No number was retained or relabeled. |
| RQ3 result paragraph | Deleted the comparison to the prior artifact: 0.704 B-cubed F1, direct delta +0.059, and 95% interval [0.048, 0.073], plus the matching Chinese clause. | Step 0087 verifies these as a comparison against the stored historical artifact. The task requires deleting this historical comparison. |
| RQ3 result paragraph | Deleted the sentence that the earlier protocol reached 0.704 B-cubed F1 and 0.394 boundary F1 and was retained for continuity, plus the matching Chinese sentence. | Historical-only result; not relabeled to the direct backend. |
| RQ3 setup | Removed historical-mark details: 149 repaired leaf groups; 5,752 marks; depth counts 51/5,608/93. Replaced them with the direct backend's 4,496 marks and depth counts 3/2,873/1,588/32. | Current values come from Step 0087 `assembled/summary.json` and are independently covered by the Step 0087 result review. This is a current-backend replacement, not a neutral relabel of old values. |
| RQ3 setup and canonicalization appendix | Removed the historical 5,537-to-1,434 name replay. Replaced it with the direct backend's 3,895-to-783 replay and neutral phrases `the adopted marks` / `Agent annotation`. | Current values come from Step 0087 `assembled/summary.json`, `canonical/canonicalization-report.json`, and `raw-results.json`. The report verifies zero remaining adjacent collisions and an unchanged temporal partition. |
| RQ4 opening Chinese comment | Replaced the historical-artifact description with the current Agent annotation's observable construction path. | Wording-only relabel; no historical number was transferred. |
| RQ4 deterministic-cost paragraph | Deleted the 506.35 s historical composite and both historical 1.17 s replay claims. Replaced the paragraph with 501.64 s shared packet construction and the direct backend's 11.516 s full downstream pipeline. | 506.35 s includes historical-only 3.54 s and 1.17 s components and was not eligible for neutral attribution. The replacement measurements have separate verified provenance below. |
| RQ4 AgentRewardBench Chinese comment | Deleted the trailing historical 1.17 s replay clause. | Historical-mark replay only; no current-backend relabel. |
| RQ4 historical-envelope paragraph | Deleted the entire 54.36 min historical artifact-envelope paragraph and its Chinese text. | Step 0075 and Step 0087 both state that this is mutable artifact chronology, not model or backend time. It has no equivalent current-backend interpretation. |
| Canonicalization appendix | Replaced `prior A2 display identity` and `prior A2 representation repair` with `Agent annotation's display identity` and `adopted-mark representation repair`; updated the bilingual comments. | The direct backend uses this same downstream repair/canonicalization path in Step 0087, so neutral current wording is supported. |
| Cost appendix title and label | Renamed `Prior A2 Reconstruction Cost Detail` to `Agent-Mark Reconstruction Cost Detail`; renamed `app:a2-reconstruction` to `app:agent-mark-reconstruction` and updated its only reference. | Removes the backend-specific identifier while retaining a valid appendix pointer. |
| Cost appendix body | Rewrote the subsection around the shared 501.64 s packet construction, the direct run's 4,496 adopted marks, and its 11.516 s downstream pipeline. Deleted 3.54 s, both 1.17 s values, historical byte-identity wording, and all historical artifact names. | Each retained or introduced number is tied to the records below. No prior-marks timing is attributed to the direct backend. |
| Extended Scope and Limitations | Replaced the historical deterministic-path/envelope wording with fixed-input replay, direct-backend wall/token cost, shared source-packet construction, and current deterministic downstream cost. Deleted the 54.36 min reference. | Aligns scope with the current measurements already reported in RQ4. |

### Per-cost-number provenance

| Number | Decision | Evidence |
|---|---|---|
| 501.64 s | **Retained and neutrally attributed to source-packet construction.** | Step 0075 measures three full packet reconstructions at 500.07/505.64/501.64 s, median 501.64 s. Step 0087's task specification requires the same packets, and both `direct_annotation/annotate.py` and `postprocess.py` load `.agentsight/experiments/rq4-end-to-end-cost-v1/full/source-packets-rep-1`. Therefore the measurement is for an input artifact the current backend actually reuses. Sources: Step 0075 `experiment-001/full-run-and-result.md` and `independent-result-review.md`; Step 0087 `experiment-001/task-spec.md` and harness code. |
| 3.54 s | **Deleted everywhere.** | Step 0075 defines it as matched assembly plus canonicalization over the historical fixed marks. Step 0087 does not report an equivalent isolated direct-backend component. It was not renamed or attributed to the direct backend. |
| 1.17 s | **Deleted everywhere.** | Step 0075 measures fixed-mark operation/token replay for the historical marks. Although Step 0087 contains its own profile-building calls, the reviewed report exposes the complete direct downstream stopwatch rather than a replicated median replay experiment. The historical 1.17 s sentence was therefore deleted rather than relabeled. |
| 506.35 s | **Deleted everywhere.** | Step 0075 explicitly defines this backend-specific accounting convenience as 501.64 + 3.54 + 1.17 s. Because two terms are historical-mark-only, the total cannot be neutrally attributed to the direct backend. |
| 54.36 min / 3,261.89 s | **Deleted everywhere.** | Step 0075 calls it a historical artifact-time workflow envelope and states that model/provider inference time and tokens are unavailable. Step 0087 repeats that it is not comparable to backend request wall. It was never attributed to the direct backend. |
| 11.516 s | **Added as the current direct backend's full deterministic downstream pipeline.** | Step 0087 `raw-results.json` records `pipeline_wall_seconds = 11.515914128976874`; `cost-record.md` rounds it to 11.516 s; the independent review states that it covers assembly, canonicalization, two profile builds/readbacks, scoring, and paired analysis. It is presented as its own aggregate, not as a relabel of 3.54 s or 1.17 s. |
| 2,215.858 s | **Preserved unchanged.** | Step 0087 reconstructs the union of active backend-call intervals as 2,215.858 s and explicitly excludes the interruption gap. |
| 12,050,384 input / 231,886 output tokens | **Preserved unchanged.** | Step 0087 sums retained direct-backend telemetry over 415 calls and all 405 valid trajectories. |

### Current RQ3 values preserved

- Direct Agent annotation remains 0.764 ordinary B-cubed F1 and 0.480
  boundary F1.
- Multi-resolution recurrence remains 0.663 B-cubed F1 and 0.266 boundary F1.
- The direct-minus-recurrence B-cubed delta remains +0.101 with 95% interval
  [0.087, 0.116].
- Exact conserved mass remains 20,866 operations and 494,862,929
  provider-reported tokens.

## 4. Remaining TODOs or risks

No task-scoped TODO remains.

Validation:

- `make` in `docs/paper/` completed successfully: BibTeX plus three pdflatex
  passes produced a 13-page `main.pdf`.
- The final log contains no undefined references, undefined citations, LaTeX
  errors, or fatal warnings. Only pre-existing underfull-box layout
  diagnostics remain.
- `A2`/`a2-` occurrences in `main.tex`: 0.
- Historical values/phrases `0.704`, `0.394`, `0.059`, `[0.048, 0.073]`,
  `506.35`, `3.54`, `1.17`, `54.36`, `interval-recursive`, and
  `earlier Agent protocol`: 0.
- Exact thesis occurrences: 3.
- All four RQ subsection titles remain unchanged.
- All figure inclusion commands remain present.
- No citation command or citation key was edited; BibTeX completed without an
  undefined-citation diagnostic.
