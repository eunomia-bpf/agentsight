# Source-Grounded Full-Paper Assessment

**Timestamp:** 2026-07-23T23:16:24-07:00
**Parent:** Step 0076 REVIEW gate, milestone review 001
**Objective:** Reread the complete paper after external verification and issue
a cross-domain AAAI/systems/ML scientific assessment.

## Inputs and method

I reread the full `main.tex` after search, rechecked every claim-bearing table
and figure, inspected `references.bib` entries needed for the central claims,
and reconciled the paper with independently reviewed Step 0072, 0075, and 0076
results. I also read the complete fixed thesis/RQ history in
`docs/idea-story.md` and the complete user-instruction log.

## Overall assessment

The paper has a strong, simple, and durable thesis:

> Agent observability needs profiling, not only debugging.

The source-linked, mass-conserving operation stack is a coherent system design.
The paper is substantially better than a trace visualization paper because it
defines responsibility independently of occurrence identity and preserves
evidence under different additive widths.

The current submission nevertheless does not meet the AAAI-27 acceptance bar.
The strongest reasons are not implementation bugs. They are:

1. two missing closest works occupy much of the broad semantic
   hierarchy/profile claim;
2. the strongest matched RQ2 experiment does not isolate an advantage from
   semantic ancestry;
3. RQ1 remains a post-hoc case rather than an independent attribution result;
4. A2 generalization/stability and end-to-end annotation cost remain
   incomplete; and
5. the PDF violates the official page limit.

## Contribution decomposition

| Claim layer | Evidence | Verdict |
|---|---|---|
| Systems model and invariant | Defined source tree, annotation intervals, operation stack, nonnegative additive measures, mass-conserving fold | Strong |
| Artifact | Rust CLI, source adapters, annotation workspace, pprof output, stock-tool readback | Strong supporting contribution |
| Automatic AI backend | A2 .704 B³/.394 boundary on CodeTrace development population; other backend-specific results | Promising but adaptively scoped |
| User consequence | Git and AgentReward cases; Direct+AgentProf improves over Direct-only but ties matched raw+evidence | Partial |
| Practicality | 1.16–1.17 s replay; 501.64 s packet construction; 3.54 s deterministic postprocessing | Deterministic path supported; automatic inference incomplete |

## RQ1 verdict — partial support, not a complete comparative answer

### Evidence

- 41 real long-horizon trajectories, with three independent Git-deployment
  executions selected for focused analysis.
- Focused family: 489 operations and 4,558,192 provider-reported tokens.
- Fixed SSH-diagnosis subtree: 105 operations (21.47%) and 2,103,587 tokens
  (46.15%).
- Step 0076 reconstructs native, coarse, and semantic count/token profiles
  from identical rows and weights; all conserve exact mass and retain source
  evidence.
- The selected 105 members occupy 105 source calls, six coarse action kinds,
  and a generic `run` branch mixed with 97 unrelated operations.

### What is established

For a fixed candidate-defined responsibility, semantic organization supplies
one focusable cross-run attribution axis that native call identity and generic
action labels do not directly name. Switching width changes the bottleneck
importance without changing membership. This is a legitimate profiling
capability and a useful case study.

### What is not established

The responsibility and task family were selected after observing the semantic
profile. The experiment does not test independent responsibility discovery,
population-level attribution accuracy, inspection effort, or superiority over
every profiler interface. It therefore only partially answers the word
“improve” in RQ1.

### RQ1 verdict

**PARTIAL SUPPORT / major evidence gap.**

The repair should preserve the ambitious RQ: predeclare a real population-level
resource or risk question, compare semantic/native/raw/recurrence views under
information parity, and measure whether the correct recurring responsibility
is found or prioritized earlier.

## RQ2 verdict — practical complementarity supported; semantic-prefix effect not supported

### Evidence and statistics

All 1,756 trajectories and 27,346 operations are consumed. MAP is computed on
1,234 target-bearing queries; 522 zero-positive queries are loaded for
coverage but excluded because AP is undefined.

| Workload | Direct+AgentProf | Direct+Raw+Evidence | Direct-only | AgentProf-only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .894 | .893 | .863 | .791 |
| HINTBench | .517 | .518 | .411 | .432 |
| TraceElephant | .326 | .324 | .209 | .259 |

Candidate-minus-Direct intervals are wholly positive:

- AgentProcess: +.031 `[.024,.039]`;
- HINT: +.107 `[.093,.120]`;
- Trace: +.117 `[.088,.148]`.

Candidate-minus-Direct+Raw+Evidence intervals all include zero:

- `[-.0003,.0029]`;
- `[-.0116,.0103]`;
- `[-.0247,.0280]`.

The paired stratified/clustered bootstrap and target-blind score construction
were independently reconstructed. No leakage was found. The fixed local-first
rule and source-only paths were developed on these populations, so the result
is adaptive mechanism evidence.

### Direct-reader fairness

`Direct` is a fair and substantively strong baseline, not a renamed weak
heuristic. AgentProcess uses the released process-judge risk units; HINT and
Trace use benchmark-native trajectory-localizer decisions; the TraceElephant
reader receives the full trace and reference answer. Candidate scores may
refine exact Direct ties but cannot overturn a strict Direct ordering. Giving
the matched control the same raw action and source-evidence channels is also
necessary: the TraceElephant primary paper itself reports a large attribution
gain from full rather than partial traces. Therefore both comparisons belong
in the main result: Direct-only establishes complementarity, while
Direct+Raw+Evidence tests whether semantic ancestry adds value at information
parity.

### What is established

A complete grouped profile can refine ties in an existing trajectory
judge/localizer and improve ranking over that direct signal alone. The
AgentReward population case also links recovery exposure to expert looping
labels: AP .634 at prevalence .398, with AP-minus-prevalence interval
`[.181,.293]`.

### What is not established

The information-matched raw+evidence view performs equivalently. The recovery
fixed-chain baseline has AP .656, and recursive-minus-fixed interval
`[-.107,.061]`. Thus neither main RQ2 result establishes a hierarchy-specific
diagnostic advantage.

The MAP protocol is a reasonable standard metric but a new cross-benchmark
task construction, not the official evaluation of all three source
benchmarks. Its connection to review effort or official localization accuracy
is not independently validated.

### RQ2 verdict

**SUPPORTED for complementing Direct-only; NOT SUPPORTED for a semantic-prefix
advantage over information-matched raw grouping.**

The abstract, introduction, contribution list, and conclusion must lead with
this strongest matched interpretation, not the weaker “beats raw action”
headline.

The minimum claim-surface repair is one evidence-level replacement, not a new
story or RQ: “Direct+AgentProf raises MAP over Direct-only by
`.031/.107/.117` on the three complete workloads; it is statistically
indistinguishable from Direct+Raw+Evidence.” The AgentProf-only values
`.791/.432/.259` can remain in the Evaluation as component evidence, but
should not be the abstract/Introduction causal headline.

## RQ3 verdict — positive development evidence, incomplete generalization

### Evidence and statistics

On all 405 reconstructable CodeTrace trajectories:

- A2: B³ P/R/F1 `.839/.607/.704`, boundary F1 `.394`;
- recurrence: `.782/.575/.663`, boundary `.266`;
- A2 minus recurrence B³: +.0414, task-clustered 95% interval
  `[+.0214,+.0606]`;
- raw-action B³: `.541`;
- native source tree B³: `.397`;
- source-native turn B³: `.361`.

On OSWorld-Human, supervised/reference-calibrated/label-free methods reach
boundary F1 `.739/.734/.680` and B³ `.816/.801/.786`, respectively. Additional
task/action backends use standard literal-label metrics.

### Baseline sufficiency

The paper now includes meaningful simple and non-LLM controls. Recurrence is a
strong no-label population baseline, while native source, source turns, and
raw action test obvious alternatives. These are sufficient to show A2 is not
winning only against a trivial singleton or action-change baseline.

They are not sufficient to establish broad generalization:

- A2 sees source-only task text and interval-wide turn summaries, while
  recurrence sees action transitions; the comparison is a method-class
  comparison, not information/compute parity.
- CodeTrace is explicitly the A2 development population.
- The Step 0073 split is selection-sensitive: on the 364-session follow-on,
  A2 B³ `.6746` is statistically inconclusive against recurrence `.6868`,
  despite higher boundary F1; the union's positive result is driven by the
  earlier 41-session subset.
- Only one A2 annotation output is reported. Model/version, prompt/config,
  repeated-run stability, and disagreement are not fully quantified.
- CodeTrace stages validate a flat failure-analysis partition, not recursive
  semantic-name identity or parent/child topology.
- ACT*ONOMY is not positioned or compared.

### Leakage and adaptivity

The reported run hides official stages, outcomes, recurrence assignments, and
scores until materialization. The root-prefix repair and action-object
canonicalization are source-only and preserve boundaries. This is good.

However, the corpus is a declared development population, and earlier results
influenced mechanism selection. The paper discloses the development label but
does not disclose the follow-on subgroup reversal/inconclusive interval.
That omission makes the headline look more general than the evidence history.

### RQ3 verdict

**PARTIAL SUPPORT / major generalization and construct gap.**

The next confirmation should use one fixed A2 instruction on an untouched
complete family with independent structure annotations. Record repeated-run
stability and annotation telemetry during that same run. B³ and exact boundary
F1 remain suitable primary metrics for flat partitions; name and topology
quality must be scored separately if claimed.

## RQ4 verdict — deterministic path supported, automatic end to end unanswered

### Evidence

On the 27,765-operation union:

- semantic construction: 1.16 s, 465.2 MiB peak RSS;
- raw-action construction: .97 s;
- semantic overhead: 190 ms (19.6%) and 5.25 MiB (1.14%);
- throughput: 23,935 operations/s.

On all 405 CodeTrace sessions:

- source-packet reconstruction: 501.64 s median;
- deterministic assembly/root repair/canonicalization: 3.54 s;
- fixed-mark operation/token replay: 1.17/1.17 s;
- all reconstructed artifacts repeat byte-identically and conserve exact
  operation/token mass.

The historical automatic-Agent waves span 54.36 artifact minutes, but cannot
separate inference, dispatch, idle time, or writing, and cannot recover token
usage.

### Interpretation

The deterministic systems measurement is valid and materially improves the
earlier fixed-input-only answer. The paper correctly labels the 1.17 s number
as replay latency.

The load-bearing automatic component remains unmeasured. Because A2 is the
default and best-quality constructor, rejected 3B/27B backend costs cannot be
substituted for it. The current RQ4 answer is therefore incomplete at the
cross-domain bar.

### RQ4 verdict

**SUPPORTED for deterministic construction/replay; UNANSWERED for adopted
automatic annotation end to end.**

## Global logic and consistency

### Story/RQ integrity

The thesis and four RQs have not drifted. Step 0076 strengthens a bounded RQ1
case; it does not replace the story. Renaming `Local` to `Direct` makes the
existing strong reader baseline clearer and changes no evidence. Step 0075
adds an honest cost decomposition without calling the artifact envelope model
latency.

### Claim-surface inconsistency

The strongest scientific inconsistency is rhetorical rather than numerical:
the abstract, Introduction results, contribution list, and Conclusion still
foreground raw-action wins, while the Evaluation establishes no semantic
prefix advantage against information-matched raw+evidence. The numbers can all
be true simultaneously, but the headline causal implication is not.

### Related-work incompleteness

ACT*ONOMY and CHIEF are missing. TraceElephant remains cited as an arXiv
preprint even though an ACL 2026 archival version now exists. The first two are
scientific must-fixes; the metadata update is minor.

### Format

The paper is 12 pages with 10 pages before References. AAAI-27 permits seven
main-content pages and nine total. This is a hard submission blocker.

## Research-taste conclusion

- **Principle:** simple and durable.
- **Belief challenged:** native occurrence structure is not automatically the
  right cross-run responsibility hierarchy. The challenge is real, not a
  strawman.
- **Strongest alternative explanation:** canonical grouping plus source
  evidence delivers most measured value; recursive semantic hierarchy mainly
  aids visualization.
- **Largest claim worth defending:** source-linked semantic responsibility
  stacks are a general population profiling abstraction that directly improves
  attribution and diagnosis under information parity.
- **Decisive evidence:** an untouched, instrumented, hierarchy-dependent
  population decision where semantic responsibility outperforms native/raw
  controls.
- **Classification:** simple-but-deep idea, incomplete evidence.

## Provisional verdict and routing

**Verdict:** **REJECT** in the current AAAI-27 form.
**Scientific trajectory:** strong enough to continue; not a recommendation to
shrink the thesis or abandon the system.
**Routing:** **EXPERIMENT_GATE**, then a substantial venue-compliant WRITE.

## Completion assessment

The source-grounded assessment is complete. Final must-fixes and current-cycle
scope decisions are recorded in the cycle audit.
