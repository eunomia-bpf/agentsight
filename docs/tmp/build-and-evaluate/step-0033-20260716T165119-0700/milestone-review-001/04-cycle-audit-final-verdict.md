# Step 0033 Milestone Review 001 — Cycle Audit and Final Verdict

**Timestamp:** 2026-07-16T17:40:41-07:00
**Parent node:** Step 0033, `REVIEW_GATE`, milestone review 001
**Objective:** Audit Step 0033 against explicit user intent, the complete idea history, the approved experiment, raw results, independent reviews, the targeted WRITE report, the current cycle diff, and the rendered full paper; separate cycle-closing repairs from broader next-cycle research opportunities and issue an exact route.

## Mandatory sequence and inputs

The audit followed the required order:

1. blind full-paper and bibliography read;
2. primary/official external search;
3. source-grounded complete-paper reread, including every table and figure;
4. only then, complete read of `docs/user-instruction.md`, `docs/idea-story.md`, all Step 0033 experiment/review/write reports, the standard-metric adapter and raw summary, and the current read-only diff/status.

The internal artifacts read in phase 4 were:

- `docs/tmp/build-and-evaluate/step-0033-20260716T165119-0700/experiment-001/experiment-plan.md`;
- `experiment-001/plan-review.md`;
- `experiment-001/result-report.md`;
- `experiment-001/result-review.md`;
- `step-report.md`;
- `write-report.md`;
- `script/rq2_standard_localization_metrics.py`;
- `.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/full/summary.json` and the declared full-output file inventory;
- the current diff for `docs/paper/main.tex`, `docs/evaluation.md`, `docs/user-instruction.md`, and generated `docs/paper/main.pdf`;
- the pre-Step-0033 committed PDF, used only to determine whether the page spill was introduced or worsened by this cycle.

No paper, code, skill, branch, submodule, or prior report was changed during this review. Only the four authorized milestone-review reports were created.

## Explicit user-intent contract

The complete instruction history establishes the following load-bearing constraints:

1. Preserve the exact thesis: **“Agent observability needs profiling, not only debugging.”**
2. Preserve exactly four RQs: resource attribution, real-problem localization/correspondence, tag accuracy, and cost.
3. Preserve the submodule-derived problem, gap, insight, two-object model, system direction, contribution chain, and positive research program; do not let local experiment outcomes or reviewer objections silently replace the story.
4. Keep operations and operation stacks as the only core abstractions unless a genuinely new abstraction is implemented and decisively justified.
5. Prefer a larger, simpler, more consequential research story; be bold in hypothesis and careful in validation. A local result tests one hypothesis and does not answer or rewrite the whole RQ.
6. Reuse real, complete benchmarks and existing trajectories when they answer the question; do not switch benchmarks or invent unnecessary micro-experiments.
7. Use standard metrics where appropriate and explain what they estimate.
8. Do not hide evidence boundaries by claiming universal dominance, but do not turn intermediate negatives into the paper's narrative center.
9. Keep paper writing and review free of Git mutation; do not create or switch branches.
10. Do not modify the read-only paper submodule.

Step 0033 is strongly aligned with these instructions. It reused three complete public workloads and the already-computed fixed scores, used an official standard AP implementation, kept the four RQs and positive RQ2 hypothesis, and changed only the evidence presentation. It did not create a new benchmark, change a target, tune a cutoff, invoke a model, or invent a new story.

## Idea-story compliance

### Initial, immediately previous, and current comparison

The Initial Narrative defines a broad population-level profiling problem spanning quality, safety, cost, failures, unsafe effects, and wasted work. Its core is operations plus query-time operation stacks, not one localization algorithm. The immediately previous frontier before Step 0033 already retained this narrative and treated Step 0019's reader evidence as a bounded RQ2 result. Step 0033 changes only how three existing localization populations are summarized.

The current paper remains closer to the Initial Narrative than to the rejected reviewer-driven representation story:

- the thesis sentence is identical;
- long-running/many-trajectory stakes remain in the Abstract and Introduction;
- the problem is profiling rather than a new localizer;
- operations and operation stacks remain the two core abstractions;
- AgentProf remains an offline profiler producing pprof-compatible profiles;
- exactly four RQs remain in the same attribution/localization/tag/cost order;
- the three contribution categories remain model, system, and evaluation.

Step 0033 did not add an idea-story evolution entry. That is correct: changing the metric used to summarize fixed RQ2 evidence is an evidence-frontier update, not a change to the problem, thesis, contributions, system direction, scope, or RQs.

### No unauthorized thesis or RQ rewrite

The diff changes one Introduction result sentence and the RQ2 evaluation protocol/table/prose. It does not touch the Abstract's thesis, Background and Motivation, Design, Implementation, RQ headings, Scope and Limitations, Related Work, or Conclusion source. `docs/idea-story.md` is unchanged. There is therefore no covert story replacement.

The new RQ2 statement remains subordinate to the paper's larger claim. It does not replace “profiling” with “ranking,” promote MAP into a new abstraction, or claim that one benchmark outcome settles the whole RQ.

## Experiment-plan and execution audit

### Plan quality and revisions

The formal plan begins with the exact paper RQ and narrows only the tested uncertainty: whether fixed AgentProf scores improve trajectory-level MAP over matched raw action on three completed localization workloads. It cites NIST TREC for AP/MAP and uses `sklearn.metrics.average_precision_score` rather than inventing a custom primary score.

The independent plan review found three concrete issues and resolved them before execution:

1. AgentProcessBench uncertainty changed from independent trajectories to task-cluster resampling within family, carrying the five task executions together.
2. HINT's ordinal native view was removed from the scalar-MAP matrix because encoding its ordering would violate the no-tie-break metric contract.
3. Qualitative “material” verdict language was replaced by an exact predeclared three-workload sign rule, and one stale contradiction sentence was then removed.

After these focused revisions, the plan returned PASS. The plan did not accumulate implementation packets, freeze contracts, multiple evaluator roles, or unrelated experiments.

### Real preflight and complete run

The real preflight exercised one target-bearing trajectory and both AgentProf/raw scores from each of the three actual source families and made no scientific decision. The full run then loaded exactly 1,756 trajectories and 27,346 operations:

- AgentProcessBench: 1,000 trajectories, 8,509 operations, 614 target-bearing queries;
- HINTBench: 536 trajectories, 12,877 operations, 400 target-bearing queries;
- TraceElephant: 220 trajectories, 5,960 operations, 220 target-bearing queries.

This is a complete reuse experiment, not a smoke test or a dataset switch. The adapter is necessary glue around the standard scikit-learn metric. It reads existing result roots and writes ordinary JSON/JSONL/Markdown outputs. No profiler, model, tagger, localizer, benchmark generator, score, cutoff, or stack constructor was rerun or modified.

### Metric correctness and population handling

The adapter computes non-interpolated AP once per target-bearing trajectory and arithmetic-mean MAP across those queries. Equal scores are left tied at the score threshold. No ID, timestamp, or file-order tie break enters the score.

The conditional population is explicit in the plan and result artifacts. The 386 zero-positive AgentProcessBench trajectories and 136 safe/no-positive HINTBench trajectories are excluded from per-query MAP and retained as nonrelevant operations in pooled AP. HINTBench has 938 official targets, 935 mapped to displayed operations; the registered sensitivity counts the remaining three as unretrieved and preserves the result.

The MAP definition is standard. The pooled operation AP is also standard AP but estimates a different, length-weighted population quantity; the paper correctly keeps it secondary. Work@80/Work@50 are operational derived measures and remain secondary. Boundary F1 and B3 F1 in RQ3 remain standard measures of boundary detection and partition agreement, respectively; they are not substitutes for RQ2 MAP.

### Source separation and leakage

The result review traced each fixed-score path:

- AgentProcessBench profiles are constructed before human labels are loaded;
- HINTBench test profiles are constructed before test targets are loaded;
- TraceElephant materializes method scores before the scorer opens official targets.

Raw action uses the same operations and underlying fixed evidence signal. Thus the main comparison isolates grouping/redistribution under a shared score. It does not establish independent content diagnosis, and the paper does not claim that it does.

### Source-to-paper value audit

| Quantity | Raw summary | Result review | Paper | Audit |
|---|---:|---:|---:|---|
| AgentProcessBench queries | 614 | 614 | 614 | match |
| AgentProcessBench MAP, AgentProf/raw | 0.788919 / 0.773170 | same | .789 / .773 | match after rounding |
| AgentProcessBench paired interval | [0.004727, 0.027081] | same | [.005, .027] | match after rounding |
| HINTBench queries | 400 | 400 | 400 | match |
| HINTBench MAP, AgentProf/raw | 0.452852 / 0.281491 | same | .453 / .281 | match after rounding |
| HINTBench paired interval | [0.154534, 0.188739] | same | [.155, .189] | match after rounding |
| TraceElephant queries | 220 | 220 | 220 | match |
| TraceElephant MAP, AgentProf/raw | 0.230168 / 0.121270 | same | .230 / .121 | match after rounding |
| TraceElephant paired interval | [0.078010, 0.141302] | same | [.078, .141] | match after rounding |
| Pooled AP, AgentProcess/HINT/Trace | .691779/.668811; .249714/.180484; .077569/.052791 | same | .692/.669; .250/.180; .078/.053 | match after rounding |
| Atomic MAP, AgentProcess/HINT/Trace | .863171/.410559/.208713 | same | .863/.411/.209 | match after rounding |

No source-to-paper numerical mismatch was found.

### Independent result review

The result reviewer independently reconstructed all three source populations, all 1,234 query rows, threshold-level AP including ties, pooled AP, HINT target coverage, score-source separation, and 30,000 bootstrap draws. It found no result-invalidating issue and returned `result status: PASS`. The current outer audit agrees with that result-level judgment.

## Current diff audit

### `script/rq2_standard_localization_metrics.py`

The new adapter is scoped to the approved reanalysis. It contains explicit expected population counts, reconstructs the fixed per-operation scores, calls scikit-learn AP, performs the approved stratified/clustered bootstrap, records query rows and raw draws, and implements the predeclared sign rule. It does not alter source roots. No unnecessary experimental mechanism was found.

### `docs/evaluation.md`

The RQ2 frontier changes from a mixed AP/Work synthesis to the admitted common MAP answer and records exact values, intervals, query populations, pooled AP, target coverage, and interpretation boundaries. It explicitly says not to reopen another RQ2 metric, cutoff, score, or benchmark variant. This is a useful stop condition against the prior pattern of repeatedly switching variants.

The fixed RQ2 positive hypothesis remains unchanged. The cumulative answer is bounded to ranking/group prioritization and does not claim universal lower work or view dominance. This is not hypothesis shrinkage; it distinguishes the tested answer from the still larger research hypothesis.

### `docs/paper/main.tex` and `main.pdf`

The source diff is limited to:

- replacing one mixed AP/Work Introduction sentence with three trajectory-MAP values;
- defining the trajectory-as-query AP/MAP protocol;
- replacing the former mixed-metric RQ2 table with a common MAP table;
- adding pooled AP and atomic-score boundaries;
- retaining the earlier Work and fixed-reader evidence.

No story section was rewritten. The generated PDF values match the source and reports.

The current rendered PDF has an important format defect: page 8 begins with Related Work prose and then the Conclusion before References. Read-only comparison with the pre-Step-0033 committed PDF shows that the defect was **already present before this cycle**: the prior page 8 began with the final agent-diagnosis Related Work paragraph and Conclusion. Step 0033's longer RQ2 presentation worsened the spill, moving additional Related Work text onto page 8. Therefore this is not an invented Step 0033 scientific problem, but it is a current submission blocker that this cycle must repair before outer closure.

### `docs/user-instruction.md`

The only diff appends the user's latest two metric questions. It does not alter or delete earlier constraints. The standard-metric experiment and this review directly answer those questions.

### Worktree scope and submodule

The read-only status shows the expected paper/evaluation/PDF/user-instruction changes, the Step 0033 report directory, and the new metric adapter. It does not show a modified paper submodule, skill repository, or unrelated source file. No branch was created or switched.

## Cycle-change audit against the full paper

### What improved

1. RQ2 now uses one standard, trajectory-equal primary metric across all three public localization workloads instead of a headline mixture of macro AP and selected Work points.
2. All three matched AgentProf-versus-raw effects are positive, and all paired intervals have positive lower endpoints.
3. Pooled AP keeps zero-positive operations in a secondary direction check.
4. Existing Work measures remain visible, so standard ranking quality is not confused with inspection cost at one operating point.
5. The atomic boundary remains visible: grouping is not claimed to dominate a strong per-operation signal everywhere.
6. The experiment reused complete real artifacts and closed the RQ2 metric-variant branch rather than switching benchmarks again.

### What did not change

- exact thesis;
- four RQs and their meanings;
- positive RQ2 hypothesis;
- operations and operation stacks as the two core abstractions;
- three contribution categories;
- system design and implementation;
- RQ1, RQ3, and RQ4 evidence;
- submodule-derived Abstract/Introduction/Background/Design story spine;
- read-only paper submodule.

### What still needs repair

The metric is scientifically valid and the numerical result is admitted. The remaining defects are both WRITE issues:

1. the paper is not within the technical-page allocation because non-reference prose remains on page 8;
2. the headline language can still make target-bearing MAP look like an all-trajectory average.

No new experiment is needed to repair either defect.

## Ranked current-cycle must-fixes

### 1. [Blocker, WRITE] Fit all technical content into the allowed technical pages

Page 8 contains Related Work and Conclusion text. The issue predates Step 0033 but the current RQ2 expansion worsened it, and a full-paper outer review cannot declare the current PDF submission-ready. Recover the small spill through meaning-preserving prose/table economy. Do not delete the thesis, any RQ, any contribution, the MAP table, pooled-AP boundary, Work evidence, or atomic boundary; do not change font, margins, line spacing, or template internals.

The WRITE report and step report must then record the actual rendered allocation, not merely “nine pages” and absence of LaTeX warnings. A warning-free build does not prove page-limit compliance.

### 2. [Major precision, WRITE] State the target-bearing MAP denominator wherever the result is headlined

The Introduction says “Across three complete public benchmarks ... trajectory MAP,” the table caption says “complete RQ2 workloads,” and the RQ2 prose says “Across all three complete populations.” Although the protocol and query-count column disclose 614/400/220, these headlines can be read as averaging all 1,756 trajectories.

The repair should state, compactly and consistently, both facts:

- all 27,346 operations from all three complete workloads were scored;
- trajectory MAP is averaged over the 614, 400, and 220 target-bearing queries.

This must not be “fixed” by assigning arbitrary AP values to no-positive queries or by replacing standard MAP. Pooled AP already carries the full zero-positive operation population as the secondary safeguard.

## Broader next-cycle major opportunities — not Step 0033 blockers

These issues affect eventual AAAI strength but should not cause another RQ2 metric/cutoff/benchmark iteration inside Step 0033:

1. **Closest alternative and novelty.** LangSmith Insights and Datadog Patterns already build cross-trace hierarchies with cost/error aggregates; NeMo already profiles nested agent workflows; pprof already promotes tags. A future high-value comparison should demonstrate a decision enabled by source-linked selectable operation projections that these nearest structures do not express. AgentDiagnose is a concrete missing adjacent citation.
2. **Complementarity with diagnosis.** AgentRx, TELBench/DRIFT, and TraceElephant show strong content-aware diagnosis protocols. A decisive future experiment could hold a strong diagnostic score fixed and test whether semantic profiling improves cross-run triage. This is preferable to another custom cutoff or benchmark swap.
3. **RQ1 construct validity.** Mixed-weight reduction partly follows from including the grouping category. A future experiment should tie source-linked resource attribution to a consequential optimization or safety decision.
4. **Automatic-constructor principle.** The operation-stack abstraction is simpler than the current NPMI/two-cutoff recurrence implementation. A future mechanism study should simplify/ablate the constructor and prospectively fix it before a new family, rather than add more thresholds.
5. **Abstract emphasis and figure quality.** The Abstract currently omits the strongest direct RQ2 MAP result, while Figure 1 has small/truncated labels and implementation-name inconsistency. These are high-value presentation improvements after the blocking page repair, preferably by replacement and simplification rather than added length.

These are genuine top-conference opportunities, but none invalidates the Step 0033 computation or authorizes story shrinkage. The first two are the most consequential future research choices; the remaining items should not all be opened simultaneously.

## Exact routing

1. **Return to a focused `WRITE_GATE` within Step 0033.** Make only the two ranked repairs: page allocation and explicit target-bearing MAP wording. Use concise prose/table economy; preserve thesis, four RQs, contribution chain, standard metric, all admitted numbers, Work evidence, pooled AP, and atomic boundary.
2. **Rebuild the PDF and inspect rendered page boundaries.** Technical prose must end by page 7 under the applicable AAAI author kit; later pages must be references only. No template/style tricks.
3. **Run a fresh read-only outer re-audit.** It should verify the two repaired locations, full-paper meaning preservation, exact values, and rendered page allocation. It need not rerun the experiment or repeat the full closest-work search unless the paper changes beyond these repairs.
4. **If those two repairs close with no new must-fix, close Step 0033 and choose the next outer-cycle question.** Do not open another RQ2 metric, cutoff, score, or benchmark variant. The highest-value next research branch is closest-alternative/complementarity evidence, selected by the root under the unchanged thesis and four RQs.

## Final verdict

The Step 0033 experiment is valid, complete, standard-metric, and scientifically useful. It strengthens RQ2 without changing the thesis, RQs, abstractions, contribution chain, or original AgentProf story. The result-review PASS remains valid.

The current paper is not yet ready for outer PASS because it has two focused WRITE defects: technical prose on page 8 and ambiguous headline wording around the target-bearing MAP population. Neither requires new evidence or claim reduction.

outer review status: REPAIR WRITE

## Focused repair follow-up — 2026-07-16T17:41:43-07:00

**Scope:** Read-only verification of only the two previously ranked WRITE
repairs and meaning preservation of the compression used to make them. I
inspected the current `docs/paper/main.tex`, the current rendered
`docs/paper/main.pdf`, and the complete paper-source diff. I did not reopen
external search, rerun an experiment, inspect a new research branch, or modify
the paper, code, skills, branch, or submodule.

### 1. Rendered technical-page allocation — closed

The rebuilt PDF remains nine US-letter pages. Page 7 now contains the complete
Scope and Limitations, complete Related Work, the `Conclusion` heading, and the
exact conclusion sentence. The page break occurs only after that sentence.
Page 8 begins with the `References` heading and contains bibliography entries;
no Abstract, body section, caption, footnote, Related Work continuation, or
Conclusion text appears on page 8. Under the same applicable AAAI allocation
used in the prior audit, all technical prose now ends on page 7 and pages 8--9
are reference-only.

The repair used source compression. The diff contains no margin, font, spacing,
page-geometry, template, or style manipulation, and `git diff --check` reports
no whitespace error.

### 2. Scored population versus MAP query population — closed

The repaired paper makes the distinction at every load-bearing location:

- **Introduction:** “Across all 27,346 operations in three complete public
  workloads” is immediately followed by “target-bearing-trajectory MAP
  (614/400/220 queries).” Thus completeness describes scored operations, not
  the MAP denominator.
- **Table 1 caption:** MAP is explicitly “over target-bearing queries after
  scoring every operation in each complete workload.” The query-count column
  reports 614, 400, and 220.
- **Protocol:** each target-bearing trajectory is the query, operations are
  ranked items, annotated problems are relevant items, and the reported primary
  quantity is mean non-interpolated AP (MAP). Test targets remain hidden until
  scoring.
- **RQ2 synthesis:** it says AgentProf improves
  “target-bearing-query MAP,” while pooled AP is separately defined over every
  operation.

The repaired wording therefore preserves the scientifically correct split: all
27,346 operations enter scoring, primary MAP averages 1,234 target-bearing
queries, and pooled operation AP retains the zero-positive population as a
secondary estimand. No arbitrary AP value is assigned to no-positive queries,
and no metric or number changed.

### 3. Meaning-preservation audit — closed

The compression does not alter the scientific story or evidence boundaries:

- The exact thesis remains **“Agent observability needs profiling, not only
  debugging.”** It remains in the Abstract, Introduction, and Conclusion.
- The Evaluation still explicitly lists exactly four paper-level RQs:
  attribution, problem correspondence, tag accuracy, and profiling cost. All
  four corresponding subsections remain.
- The Introduction still enumerates exactly three contributions: semantic
  operation-stack model, AgentProf system, and evaluation. The two core
  abstractions remain operations and operation stacks.
- RQ2 still retains the atomic boundary: the atomic score wins on
  AgentProcessBench but not HINTBench or TraceElephant. It retains HINT and
  Trace inspection-work boundaries, the prospective Trace Work@80 tied-tail
  limitation, and the reader result's nonclaims about lower work, reader-only
  causality, human utility, and universal dominance.
- Scope and Limitations still preserves offline/capture scope, the fixed RQ1
  task and process/tool boundary, manifest categories as inputs, the named
  backend and declared task/action label sets, the literal-phase and
  unknown-label exclusions, and the post-hoc CodeTraceBench boundary.
- Related Work still distinguishes three categories rather than collapsing
  them: agent-observability/cross-trace/workflow aggregation, traditional stack
  or event profiling, and agent diagnosis/state reconstruction. AgentProf's
  stated distinction remains selectable conserved pprof projections over
  heterogeneous source-linked histories plus recurring semantic-responsibility
  folding. The compression reduces citation enumeration but does not invent a
  broader absence claim or change these category distinctions.

The source diff introduces no repair-created scientific, consistency, or
submission blocker. Both prior must-fixes are closed; the Step 0033 experiment
and result-review PASS remain valid. No further Step 0033 experiment, metric,
cutoff, score, benchmark variant, or WRITE repair is required.

outer review status: PASS
