# Source-grounded full-paper assessment

## Review contract

- **Target:** cross-domain AAAI/MLSys paper.
- **Review stage:** whole-paper scientific assessment after a blind read and targeted primary-source verification, but before inspecting the current cycle's experiment and write reports.
- **Material assessed:** the complete active paper, figures, bibliography, reproducibility checklist, paper README, project idea/story, and user instructions.
- **Decision scale:** Accept / Weak Accept / Borderline / Weak Reject / Reject.
- **Provisional decision:** **Reject (major scientific revision)**.
- **Routing implied by the scientific record:** **EXPERIMENT_GATE**, followed by a focused WRITE gate only after the experiment succeeds.

This is not a judgment that the project should be abandoned or reduced to an
artifact note. The paper has a defensible central insight and a substantial
system. The rejection is because the current evidence does not yet isolate the
scientific consequence of the proposed semantic hierarchy from the evidence,
scoring, and canonicalization that accompany it.

## One-sentence principle

If semantic hierarchy is the contribution, then an information-matched
experiment must show that hierarchy itself changes a consequential profiling
outcome, rather than merely showing that a configuration containing hierarchy
beats a deliberately weaker raw-action view.

## Paper thesis and contribution as I understand them

The strongest version of the paper is:

> Agent histories can be compiled into a conserved, source-drillable population
> profile by assigning stable, recursive semantic responsibility over native
> trace evidence; this representation should make recurring quality, safety,
> and cost problems easier to attribute than information-matched
> occurrence-local views.

That thesis has three separable parts:

1. **Representation/model:** recursively annotated source intervals become
   stable semantic operation stacks while preserving native evidence and
   additive measures.
2. **System realization:** AgentProf accepts interchangeable annotation
   backends and emits deterministic pprof-compatible profiles.
3. **Scientific consequence:** the semantic hierarchy provides a useful
   attribution or diagnosis advantage, not just a valid serialization.

The first two are plausible and substantially implemented. The third is not
yet established under the strongest control introduced in this cycle.

## Source-grounded novelty assessment

### What remains differentiated

The combination of the following properties is more distinctive than any one
property alone:

- variable-depth semantic intervals within a trajectory;
- deterministic composition with the source-native session/prompt/LLM/tool
  structure;
- exact conservation of arbitrary additive measures;
- retained evidence for drilldown;
- backend-neutral annotation replay;
- emission into standard pprof tooling.

This combination is worth defending. It is deeper than merely rendering a
flame graph and more useful than treating a trajectory as an unstructured bag
of canonical actions.

### What can no longer carry novelty by itself

Primary sources show that several broad claims are already established:

- Datadog Patterns and LangSmith Insights derive cross-trace hierarchical
  categories, aggregate cost/latency/evaluation metrics, and permit drilldown.
- NeMo Agent Toolkit profiles instrumented agent workflows.
- OpenTelemetry Profiles links profile samples with traces and spans.
- pprof already supports labels and promotion of tags to pseudo-frames.
- TraceProbe, Graphectory, Hodoscope, and TraceGraph provide canonicalized
  process views, recurring structures, human-review comparisons, or recovery
  consequences.
- CHIEF uses hierarchical task decomposition in agent diagnosis.
- ACT*ONOMY constructs a three-level action taxonomy automatically and uses it
  for agent/trajectory behavioral profiles.

Therefore, “hierarchical grouping,” “population metric rollups,” “profiling
agents,” “canonical action names,” and “pprof compatibility” are not
individually novel claims. The paper must make the narrower distinction above
precise and then demonstrate its consequence.

### Missing closest-work blocker

ACT*ONOMY is a direct novelty threat because it provides a three-level
hierarchical action taxonomy, an automatic quote-grounded construction
pipeline, and behavioral profiles across agents and trajectories. It is absent
from the paper. A reviewer cannot currently determine whether AgentProf's
recursive intervals, source-tree composition, conserved measures, and
standard-profile replay are a substantive advance over this closest work or
just a different packaging of hierarchical action profiling.

This is a **blocker**, not a citation-polish item. The related-work comparison
needs a claim-by-claim matrix and, where artifacts permit, an empirical
baseline or explicit capability comparison.

## RQ-by-RQ scientific assessment

### RQ1: Can AgentProf recover useful operation structure?

**Current evidence:** 405 reconstructable failed CodeTraceBench development
trajectories; ordinary B³ F1 of 0.704 for automatic Agent annotation versus
0.663 recurrence and 0.541 raw action; additional macro-F1 and
OSWorld-Human boundary/partition results.

**Scientific problem:** the evaluation often scores AgentProf against
structures that are not gold semantic-responsibility hierarchies.

- CodeTraceBench stages are failure-localization stages. They are a flat
  partition and do not validate recursive semantic identity or topology.
- OSWorld-Human action groups are consecutive actions executable from the same
  visual observation, introduced to reduce planning/model calls. They are not
  annotations of semantic responsibility.
- AgentBoard/ASE task-family and action labels establish field recovery on
  named datasets, not the necessity of a recursive stack model.

The results establish that backends can reconstruct useful partitions and
categories. They do not establish that the proposed representation improves
over simpler canonical labels, flat intervals, or native spans for the paper's
population-level profiling objective.

**Required repair:** add an untouched-family evaluation with an annotation
protocol that directly represents the claimed construct: variable-depth
responsibility, shared identity across trajectories, coverage of source
evidence, and parent/child relations. Report annotator agreement and compare
flat canonical labels, native nesting, recurrence, and the recursive AgentProf
model. This should be a real confirmation set, not another development-only
reuse of the CodeTraceBench population.

**Severity:** **major**.

### RQ2: Does semantic profiling improve localization/ranking?

**The matched baseline is scientifically sound.** A Local+Raw+Evidence control
with the same evidence, local score, ranker, population, and statistical
procedure is the right way to test whether semantic identity or hierarchy adds
information. It is not “too strong”; it removes evidence and scoring as
alternative explanations. TraceElephant itself shows that access to complete
inputs and metadata can materially change attribution accuracy, which makes
information parity essential.

**The observed parity is scientifically decisive.** The matched comparison
does not show a reliable advantage for Local+AgentProf over
Local+Raw+Evidence on any of the three complete workloads. Consequently:

- The paper may retain the semantic hierarchy as a representation and systems
  contribution.
- It may not claim that automatic semantic identity improves matched
  localization ranking across those workloads.
- Older raw-action comparisons remain descriptive ablations of a weaker view,
  not evidence of hierarchy-specific benefit.

The abstract and conclusion still foreground “improving over raw action on
every workload” and “localization MAP over raw action,” which invites exactly
the causal interpretation that the matched experiment rejects. Adding the
sentence about paired intervals does not cure the headline framing.

**Metric validity is also unresolved.** The three public benchmarks do not
officially use the trajectory-MAP protocol adopted by AgentProf:

- AgentProcessBench uses ternary step-level process quality.
- HINTBench evaluates risk detection/localization/type, including strict and
  localization F1 metrics.
- TraceElephant reports responsible-agent and decisive-step accuracy.

MAP can be a reasonable profiler-oriented metric, but it is a new
reformulation. The paper needs construct validation against each benchmark's
official outcome and must show that improved MAP corresponds to less review
effort, faster confirmed diagnosis, better intervention selection, or another
decision-level benefit. Hodoscope and Graphectory demonstrate that the adjacent
literature already measures review effort or intervention outcomes.

**Required repair:** run an information-matched semantic-versus-raw/native
experiment with:

- identical evidence, occurrence-local scores, ranker, and candidate set;
- a predeclared primary outcome tied to review/decision utility;
- official benchmark metrics as secondary outcomes;
- untouched task-family confirmation;
- robust paired uncertainty and multiple-comparison handling;
- full annotation and inference cost.

If semantic hierarchy remains tied, test where aggregation should matter:
cross-trajectory recurrence, repeated semantic responsibility under lexical
variation, and resource- or risk-weighted population triage. A positive result
on that targeted setting would be more aligned with the paper than another
local step-ranking sweep.

**Severity:** **blocker**.

### RQ3: Why and when does the structure help?

The paper currently combines several different mechanism probes:

- CodeTraceBench stage agreement;
- declared hierarchy localization;
- canonical Agent+Evidence identities;
- OSWorld-Human recurrence and boundary grouping;
- task-family/action classifiers;
- population case studies.

These results are individually interesting, but they do not form one causal
mechanism story. The strongest alternative explanation is:

> Most observed gains come from canonical renaming, added evidence, or
> task-specific boundary heuristics, while recursive semantic hierarchy adds
> little once the same information is available to a raw/native view.

The current matched RQ2 outcome supports this alternative. The paper needs a
factorial or nested ablation separating:

1. evidence availability;
2. canonical renaming;
3. interval grouping;
4. hierarchy depth/topology;
5. additive cross-run folding;
6. ranker/scoring choice.

The experiment must vary these factors without changing the positive labels or
candidate population. Without this, the paper's “mechanism” is a bundle.

**Severity:** **major**.

### RQ4: Is the system practical?

The fixed-mark construction result is credible within its stated scope:
27,765 operations in 1.16 seconds, exact mass conservation, and stock-pprof
loading. But it explicitly excludes capture, source adaptation, automatic
annotation, and live-agent overhead. Those exclusions contain the likely
dominant costs and the principal source of semantic errors.

Compared with current workflow profilers, fixed-mark serialization is not the
end-to-end system question a reviewer needs answered. At minimum report:

- source adaptation time and engineering effort;
- automatic annotation latency, model/token cost, and failures;
- storage growth;
- end-to-end latency and peak memory;
- incremental/update behavior for growing populations;
- sensitivity to annotation version/model changes;
- reproducibility across repeated automatic annotations.

**Severity:** **major**.

## Cross-paper consistency and story drift

The high-level thesis and four intended questions remain coherent: structure,
localization consequence, mechanism, and cost. I do not recommend changing the
thesis or shrinking the problem to pprof serialization. The right repair is to
expand evidence around the narrow differentiator.

However, the current narrative has three forms of drift:

1. **Causal drift:** matched-baseline parity is disclosed in one sentence, but
   the abstract, introduction, contribution list, and conclusion continue to
   advertise wins over raw action.
2. **Object-count drift:** the paper alternates between a “semantic operation
   stack model,” three explicit objects (source nodes, annotations, stacks),
   backend output, and profile views. The scientific core is simpler:
   source-linked recursive semantic intervals composed into conserved stacks.
3. **Evaluation-role drift:** partition recovery, localization ranking,
   case-study findings, and construction throughput are repeatedly presented
   as mutually reinforcing evidence even when they validate different
   constructs.

The RQs should stay. Their roles should be made non-overlapping after the next
experiment:

- RQ1 validates representational fidelity on direct hierarchy annotations.
- RQ2 validates downstream decision/review utility under information parity.
- RQ3 isolates the mechanism and boundary conditions.
- RQ4 measures end-to-end practical cost.

## Terms to keep, merge, or delete

### Keep

- **semantic responsibility**: this is the central conceptual distinction.
- **operation annotation**: a useful system contract if defined once.
- **operation stack**: appropriate for the emitted attribution path.
- **source evidence / source-linked evidence**: necessary to distinguish the
  model from detached taxonomies.
- **conserved additive measure**: technically meaningful and testable.

### Merge or simplify

- Merge “ordered source tree,” “source nodes,” and “source-native hierarchy”
  into one canonical term: **source trace tree**.
- Use one name for the automatic backend. “Agent,” “Agent-assisted,”
  “automatic Agent,” and “Agent+Evidence” currently force the reader to infer
  whether these are the same mechanism or different configurations.
- Treat “session-level operation,” “prompt-level operation,” and “recursive
  operation” as interval scopes, not three new conceptual objects.

### Delete or sharply constrain

- Avoid “profiling layer missing from agent observability” as a broad novelty
  statement; existing products and research already provide hierarchical
  population profiling.
- Avoid using “human stage,” “action group,” “partition,” and “semantic
  responsibility hierarchy” interchangeably.
- Do not use “improves localization” without naming the comparator as either
  weak raw-action or information-matched raw/evidence.

## Reviewer attack map

| Finding | Category | Severity | Why it matters | Required evidence or repair |
|---|---|---:|---|---|
| Information-matched RQ2 baseline ties AgentProf on all three workloads | evidence, logic | blocker | The main consequence claim is not isolated | New predeclared, information-matched downstream experiment in the setting where cross-run hierarchy should help |
| Abstract/conclusion still headline weak-baseline wins | correctness, writing | blocker | Readers infer a causal semantic advantage contradicted by the matched result | Rewrite all headline claims after the experiment; report both controls together |
| ACT*ONOMY absent | novelty, citations | blocker | Closest known hierarchical action-profile work | Add source-grounded comparison and empirical baseline/capability audit where feasible |
| RQ2 MAP is not an official benchmark outcome | methodology, evaluation | major | Construct validity of the headline numbers is unclear | Add official metrics and review/decision outcome |
| RQ1 gold structures do not directly encode recursive semantic responsibility | methodology | major | Capability is measured against adjacent constructs | Untouched, directly annotated hierarchy set with agreement |
| RQ3 bundles evidence, naming, grouping, hierarchy, and ranker effects | methodology, logic | major | Mechanism cannot be identified | Factorial/nested ablation |
| RQ4 excludes dominant annotation/adaptation costs | systems, evaluation | major | Practicality claim is only about serialization | End-to-end cost and stability |
| Automatic CodeTraceBench backend is development-only | methodology | major | Risk of prompt/backend overfitting | Frozen backend on untouched family |
| Product comparison is prose-only | baseline, novelty | major | Status quo already has hierarchy, rollups, drilldown | Capability matrix plus import/baseline if available |
| Main PDF is 12 pages with substantive content through page 10 for an AAAI-format target | presentation, compliance | blocker for submission | The artifact is not submission-ready | Compress/restructure only after science stabilizes; verify official limit |
| Figures/tables consume disproportionate space while the causal result is buried | presentation | major | Story is harder to audit than necessary | One thesis figure, one matched-result table, one mechanism figure; move diagnostic detail to appendix |
| Privacy/security treatment is thin for retained prompts/tool evidence | ethics, systems | minor-to-major | Source drilldown can expose sensitive data | Threat model, redaction/access policy, retention discussion |

## What would change my belief?

I would change from Reject to at least Borderline if a frozen, untouched-family
evaluation showed that recursive semantic hierarchy, with identical evidence
and scoring, materially reduced confirmed-review effort or improved an official
diagnosis/intervention outcome, and if a factorial ablation attributed that
gain specifically to shared hierarchy rather than canonical names alone.

## Largest claim still worth defending

> AgentProf provides a backend-neutral way to turn heterogeneous agent traces
> into source-drillable, conserved profiles over shared, variable-depth
> semantic responsibility, and that structure can improve population-level
> attribution when recurring responsibility must be aggregated across
> lexically and structurally heterogeneous runs.

This is a larger and more interesting claim than “AgentProf exports pprof,” but
it is narrower and more defensible than “semantic profiles improve
localization on all three benchmarks.”

## Decisive next experiment

Construct or adopt a benchmark whose unit is population-level review:

1. Freeze an untouched family of trajectories containing repeated semantic
   responsibilities under lexical/action variation.
2. Provide identical source evidence and local anomaly/failure scores to all
   methods.
3. Compare raw occurrence IDs, canonical flat labels, native trace nesting,
   fixed-depth hierarchy, and AgentProf variable-depth hierarchy.
4. Rank groups for review without access to evaluation labels.
5. Measure time or operations inspected until the first confirmed issue,
   recall at fixed review budgets, correct responsibility attribution,
   official benchmark outcomes, and annotation/end-to-end cost.
6. Predeclare the primary outcome and perform paired family-level inference.
7. Include an untouched transfer family and report failures, not only average
   improvements.

The current three localization workloads can remain useful secondary evidence,
but another scoring sweep over the same development choices will not resolve
the central objection.

## Provisional verdict and routing

**Verdict:** **Reject / major revision.**

**Route:** **EXPERIMENT_GATE.**

The paper is not merely a writing pass away from acceptance. Its central
representation is promising and the new matched baseline is the correct
scientific control, but that control exposes the missing result. The next cycle
should preserve the thesis and add decisive information-matched downstream
evidence, direct hierarchy validation, and end-to-end cost. Only then should a
WRITE gate consolidate terminology, correct headline claims, compare closest
work, and bring the manuscript within the venue limit.
