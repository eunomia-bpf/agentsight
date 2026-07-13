# Independent Full Result Review: RQ2 ToolSafe

**Review time:** 2026-07-13  
**Protocol:** `research-experiment-design` / RESULT REVIEW  
**Approved input:** Experiment Plan Revision 3  
**Execution reviewed:** complete ToolSafe full run  
**Paper, story, RQ, hypothesis, and skill edits:** none

## Independent verdict

```text
run status: VALID
tested hypothesis: CONTRADICTED
research value: SUPPORTING
paper impact: MECHANISM/WORKLOAD BOUNDARY
next paper decision: Keep the fixed hypothesis, RQ2, four-RQ program, thesis,
  story, and paper unchanged. Retain this negative construction result only in
  internal experiment history and select a materially different real
  tool-effect/localization experiment. Do not tune this ToolSafe construction
  or write its negative result into the paper.
```

The full execution is complete and scientifically interpretable. The automatic
`CONTRADICTED` classification exactly follows Revision 3's predeclared rule that
this construction is contradicted when the main strict direction reverses in
any held-out family. It is not caused by a missing run, target-label leakage,
an AgentProf failure, a partition error, a confidence-interval calculation
error, or a stale report boolean.

This verdict applies only to the tested construction: cross-family problem
density attached to ToolSafe's published
`malicious_request -> being_attacked -> harmfulness_rating` tuple. It does not
answer all of RQ2 and does not directly challenge the paper thesis, **“Agent
observability needs profiling, not only debugging.”**

## Material reviewed

- `experiment-plan.md`, including Revision 3's population, boundary, metric,
  bootstrap, success, mixed, contradiction, and routing rules;
- `script/toolsafe_agentprof_eval.py`, especially preparation, prediction,
  AgentProf invocation/count checking, conservative metrics, paired clustered
  bootstrap, verdict logic, and coordinator subprocess boundaries;
- `full-run-report.md`;
- `docs/visexp/out/toolsafe-rq2/full/metrics.json`;
- `docs/visexp/out/toolsafe-rq2/full/report.md`;
- `docs/visexp/out/toolsafe-rq2/full/execution-status.json`;
- all three fold prediction/status/count files, all 84 generated AgentProf
  profile maps, all operation files, and representative bootstrap records;
- the projection and three family-separated label files used to independently
  rebuild coverage, labels, predictions, metrics, and verdict inputs.

## 1. Terminal coverage and exact population

The full run reached every planned terminal condition.

| Check | Independent observation | Judgment |
|---|---:|---|
| Released projection rows | 7,182 | PASS |
| Primary real operations | 6,786 | PASS |
| Compatibility-only non-operations | 396, all in ASB | PASS |
| AgentHarm target predictions | 731 | PASS |
| ASB target predictions | 5,231 | PASS |
| AgentDojo target predictions | 1,220 | PASS |
| Unique projection IDs | 7,182 | PASS |
| Unique label IDs | 7,182 | PASS |
| Unique prediction IDs | 7,182 | PASS |
| Projection = label = prediction ID set | exact equality | PASS |

The raw partition is therefore exact, not inferred from the final summary. The
projection contains 523 case-sensitive tool values including the one declared
non-operation marker, hence 522 real-operation tool strings. There are 2,543
operation rows whose raw tool identity contains uppercase characters, so
lowercasing would materially change the partition; the executed path preserved
their original case.

The primary result excludes only visible `None`, empty, or `Final Answer`
non-operations. The compatibility analysis restores exactly those 396 rows.
No positive operation label was removed by a hidden-label rule.

## 2. Target-label boundary and metric non-circularity

The prediction boundary is valid for the approved plan.

1. The allowlisted projection has no `score`, `meta_sample`, `attack_success`,
   `aggressive`, `attacker_tool`, `label`, or `labels` field.
2. A `predict-fold` process requires exactly the two non-target family label
   files and rejects a reference set containing a target record ID.
3. Each saved prediction contains only `record_id`, family/cluster identity,
   the visible operation flag, published detector risk, grouping keys, and
   source-learned score/support/fallback entries. It contains no target label.
4. The coordinator waits for each prediction subprocess to finish before
   invoking `score-all` with target-family labels.
5. I independently rebuilt all 139,680 saved semantic, risk+tool, risk-only,
   exact-tool, and cause score/support/fallback entries from only the projection
   and the two reference-family label tables. Every entry matched exactly.

The target metric is the released ToolSafe score, while method scores are
Laplace-smoothed densities learned from other families. The correctness signal
is therefore not defined by the tested profile's output. The use of authors'
published TS-Guard judgments is a valid external signal rather than a
tautological label join. It does, however, bound the interpretation: this run
tests whether an existing detector's judgments form a transferable profile; it
does not show that AgentProf independently detects unsafe actions or that the
tuple is intrinsically causal.

## 3. Real AgentProf engagement, counts, and raw identity

Running the reviewed binary directly reports `agentpprof 0.2.37`, matching all
three fold count files and the full metrics/status artifacts.

I independently reconstructed every AgentProf stack counter from each emitted
operation JSONL and compared it with the corresponding profile JSON:

- three folds;
- primary and compatibility populations;
- target and reference sides;
- semantic, risk+tool, risk-only, exact-tool, causes, interaction, and flat
  profiles.

This covers 84 profile maps and 41,904 fold/population operation rows. Every
stack key, integer weight, total weight, and unique-stack count matched; there
were zero discrepancies. For every operation-file row, decoding the
`utf8hex_...` tool frame reproduced the exact case-sensitive raw tool in the
source projection. The AgentProf comparison therefore engaged the planned
hierarchies rather than a toy or emulated substitute.

## 4. Bootstrap completion and paired uncertainty

Each fold bootstrap artifact contains one header plus attempts `0..9999`.
Attempt IDs are aligned across all three target families, and each target draw's
multiplicities sum to the complete family cluster count. Independent class
coverage checks found zero invalid attempts in every cell:

- primary / strict: 10,000 valid;
- primary / unsafe-only: 10,000 valid;
- compatibility / strict: 10,000 valid;
- compatibility / unsafe-only: 10,000 valid.

Thus the run obtained 10,000 valid paired replicates in each of the four
population-by-label cells in exactly 10,000 supplied attempts. It did not stop
on a partial prefix or supplement failed attempts selectively.

I independently streamed all 10,000 primary/strict attempt records, rebuilt the
pooled whole-tie blocks from the saved cluster multiplicities and
reference-derived densities, recomputed the three conservative metrics for all
main methods, and then recomputed paired percentile intervals. All method means,
paired means, and interval endpoints matched `metrics.json` to floating-point
precision.

| Semantic minus baseline | Metric | Mean | Paired 95% interval |
|---|---|---:|---:|
| risk + raw tool | AP | +0.029228 | [-0.005450, +0.058494] |
| risk + raw tool | R@30 | -0.252180 | [-0.321841, -0.004045] |
| risk + raw tool | Work@50 | +0.056169 | [+0.015013, +0.127090] |
| risk only | AP | +0.030343 | [-0.004953, +0.060037] |
| risk only | R@30 | -0.141398 | [-0.323159, +0.137168] |
| risk only | Work@50 | +0.047454 | [+0.001751, +0.127464] |

Neither AP interval is strictly positive. Against risk+tool, semantic profiling
has an entirely negative R@30 interval and an entirely positive Work@50
interval; positive Work@50 means more inspection work and is worse. The
risk-only Work@50 interval is also entirely positive. These are genuine paired
outcomes under the planned cluster resampling, not uncertainty omitted from a
point-estimate comparison.

## 5. Independent point-metric reconstruction

Recomputing the predeclared whole-tie conservative metrics directly from saved
predictions and the separated labels produced the following exact primary
results.

### Strict labels

| Method | AP | R@30 | Work@50 |
|---|---:|---:|---:|
| Semantic triple | 0.930871 | 0.233705 | 0.321839 |
| Risk + raw tool | 0.892672 | 0.534645 | 0.282051 |
| Risk only | 0.891822 | 0.241926 | 0.304892 |

The semantic AP point estimate is larger, but its early recall and work to 50%
recall are worse than both matched baselines. The result therefore fails the
predeclared operation-localization requirement independently of compression.

### Unsafe-only labels

| Method | AP | R@30 | Work@50 |
|---|---:|---:|---:|
| Semantic triple | 0.529137 | 0.482801 | 0.366048 |
| Risk + raw tool | 0.646298 | 0.760442 | 0.247126 |
| Risk only | 0.600268 | 0.730958 | 0.243442 |

The pooled unsafe-only direction reverses against both main baselines. Semantic
AP also loses to risk+tool in AgentHarm, ASB, and AgentDojo separately. This
forbids an unconditional unsafe-operation interpretation even apart from the
strict-family contradiction.

The independently recomputed official strict TS-Guard accuracy, F1, and recall
for all 731 AgentHarm, 5,231 ASB, and 1,220 AgentDojo rows match the checked
official values exactly. This closes the end-label mapping and complete-source
coverage check.

## 6. Mandatory family direction and automatic verdict

The decisive strict family APs are:

| Held-out family | Semantic | Risk + raw tool | Risk only | Predeclared direction result |
|---|---:|---:|---:|---|
| AgentHarm | 0.865998 | 0.864149 | 0.867093 | loses to risk only |
| ASB | 0.949481 | 0.950302 | 0.950302 | loses to both |
| AgentDojo | 0.904165 | 0.812525 | 0.844164 | beats both |

Revision 3 says to classify this construction as contradicted if “the main
strict direction reverses across families.” The implementation defines that
condition as any held-out family in which semantic AP is below either main
baseline and evaluates the verdict in this order:

```text
if full population is absent: NOT_EVALUATED_PREFLIGHT
else if semantic fails pooled raw AP
     or strict family reversal
     or compatibility-only improvement: CONTRADICTED
else: evaluate the predeclared support/mixed branches
```

For this full run:

- full population is present;
- semantic does beat risk+tool in pooled strict AP;
- compatibility-only improvement is false;
- strict family reversal is true because ASB loses to both baselines and
  AgentHarm loses to risk only.

Therefore `CONTRADICTED` follows the plan exactly. The classification does not
depend on the report's cached boolean: the family APs rebuilt from raw saved
predictions independently reproduce the triggering condition. The rule is
strict—any negative family direction triggers it—but it was explicit before
the full run, so applying it is not a post-hoc conservative reinterpretation.

## 7. Baselines, fallback, and artifact explanations

The risk-only baseline is fully engaged and is the strongest matched competing
answer that the detector's scalar score already contains the transferable
signal. The risk+raw-tool baseline uses the same reference labels, smoothing,
and risk signal as planned; it adds exact case-sensitive tool identity and
backs off only when that cross-family joint key is absent.

Primary fallback counts reconstructed from the predictions are:

| Method | Exact | Risk backoff | Global backoff |
|---|---:|---:|---:|
| Semantic | 6,786 | 0 | 0 |
| Risk + raw tool | 235 | 6,551 | 0 |
| Risk only | 6,786 | 0 | 0 |
| Exact-tool control | 250 | 0 | 6,536 |

The 96.5% risk backoff for risk+tool is not an implementation failure: it is
the measured consequence of exact raw tool names transferring poorly across
these benchmark families under the predeclared key. It limits any broad claim
that raw-tool organization is generally inferior, because this workload rarely
allows its exact cross-family mechanism to engage. It does not invalidate the
tested construction's contradiction: the fully engaged risk-only baseline is
competitive, semantic fails the early-work criteria, and the family/unsafe-only
directions reverse.

The semantic view does compress the primary strict population to 30
family-scoped groups versus 826 risk+tool groups and 3,326 interaction groups,
meeting the planned 10x check. This is a valid compression observation, not a
localization win. Revision 3 explicitly prevents compression from overriding
worse operation-level evidence.

The compatibility population has the same pooled method directions as the
primary population: semantic is above both baselines for strict AP and below
both for unsafe-only AP. `compatibility_only_improvement` is therefore false.
The 396 ASB non-operation rows do not create either the strict pooled advantage
or the unsafe-only reversal.

## 8. Scientific classification and required routing

This is a valid, non-redundant supporting experiment with a negative result for
one proposed constructor. It establishes a useful mechanism/workload boundary:
on released ToolSafe/TS-Bench leave-one-family-out transfer, the published
three-field TS-Guard decomposition does not provide the stable cross-family,
low-work localization promised by the tested hypothesis. Its strongest gains
are concentrated in AgentDojo; scalar risk remains competitive, and exact tool
identity has little cross-family overlap.

It is not a direct thesis challenge. The experiment neither tests all possible
semantic hierarchies nor the paper's positive AgentProf construction on a
direct real tool-effect/localization task. Under `research-experiment-design`,
the only permitted next action is therefore:

1. preserve the tested positive hypothesis, fixed RQ2, all four RQs, thesis,
   canonical story, and paper;
2. keep this ToolSafe negative result in internal experiment history rather
   than adding it to the paper;
3. do not tune ToolSafe tuple cells, labels, thresholds, family weights, or
   fallback rules to rescue this run;
4. return to the EXPERIMENT decision and admit a materially different real
   experiment whose mechanism, benchmark, and metric directly test useful
   tool-effect/problem localization.

No rerun of this approved matrix is required: execution is VALID, not invalid
or incomplete.
