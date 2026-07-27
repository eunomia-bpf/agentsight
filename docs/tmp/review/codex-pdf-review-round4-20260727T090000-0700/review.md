# AAAI Review: AgentProf: Semantic Profiler for Long Horizon AI Agents

## Review basis

This review is based only on the compiled 15-page PDF. I did not consult an artifact, repository records, prior reviews, or external sources. Accordingly, I assess novelty as it is established by the paper's own related-work discussion rather than independently verifying every citation or priority claim.

## Summary

The paper argues that “Agent observability needs profiling, not only debugging.” Its central abstraction is a semantic operation stack over agent trajectories. A source adapter retains native session, prompt, LLM-call, tool-call, and effect structure; an interchangeable annotation backend assigns nested semantic responsibilities; and a deterministic compiler folds additive measures such as operation count, tokens, elapsed time, file effects, and network effects into standard pprof profiles. The intended benefit is population-level aggregation across executions whose natural-language intentions and runtime structures otherwise lack stable shared identity.

The system is evaluated through four research questions. RQ1 demonstrates exact conservation and replays a fixed hierarchy under different resource measures, including a three-run Git case and a 440-session population. RQ2 combines profiles with three problem-localization benchmarks, conducts an LLM profile-guided reading study, and presents a bad-versus-good differential profile. RQ3 evaluates several annotation backends on stage partitions, adjacent boundaries, task families, and action labels. RQ4 measures deterministic profile construction and automatic-annotation costs. The paper also profiles 42 development sessions from the authors' workstation.

The core idea is useful and memorable: replace unstable raw trajectory identity with a recursively annotated, evidence-preserving semantic stack, then reuse mature profiling tools. The implementation discipline is also attractive: one standard pprof artifact, exact mass conservation, and source evidence retained below semantic frames. However, the evaluation does not yet validate the most load-bearing property—whether recurring semantic names are correct and stable across runs. The principal RQ2 MAP gains are matched by a raw-action/evidence control, and the paper explicitly concedes that they do not isolate the semantic prefix. RQ1 demonstrates that changing a measure can change a bottleneck, but not that semantic profiling improves attribution correctness or developer decisions. The long-horizon evidence is descriptive rather than accuracy-bearing, and a key LLM-reader experiment is insufficiently specified for reproducibility.

## Strengths

1. **Important and well-motivated problem.** Population-level diagnosis, safety analysis, and resource attribution for agent histories are increasingly important. The distinction between per-run debugging and cross-run profiling is clear and potentially durable.

2. **Simple, compositional abstraction.** The separation among an ordered source tree, nested semantic annotations, and weighted pprof stacks is clean. The design preserves source-native evidence while allowing an annotation backend to change independently of the profiler.

3. **Strong interoperability choice.** Emitting standard pprof rather than introducing a bespoke viewer is a meaningful engineering and usability decision. Exact conservation across measures is an appropriate invariant, and preserving raw identities as labels avoids fragmenting visible aggregation.

4. **Unusually candid negative and matched-control reporting.** The paper reports null results rather than hiding them. In particular, it acknowledges that the information-matched raw-action/evidence baseline ties the semantic-prefix ranking result, that the recursive looping detector is not superior to a fixed-chain detector, and that the long-horizon self-profile is descriptive.

5. **Broad empirical effort and useful cost accounting.** The evaluation spans several public populations, multiple structural and literal metrics, a population differential case, system-effect views, and explicit annotation token/time costs. Clustered bootstrap intervals and exact population counts are often provided.

6. **Good claim qualification in several local passages.** Figure 4 is explicitly described as diagnostic rather than causal, RQ2 excludes end-user diagnosis time, and the paper distinguishes fixed-mark materialization cost from automatic annotation.

## Major concerns, ranked

### 1. The central cross-run semantic-identity property is not directly validated

The design requirement that makes this more than ordinary grouping is explicit:

> “Responsibilities that recur in different sessions need the same short semantic name so that their costs fold together rather than remaining session-local.”

Yet the strongest direct-Agent evaluation measures within-trajectory partitions and boundaries:

> “Ordinary operation-level B3 measures the induced leaf partition, while exact adjacent-boundary F1 measures transition placement.”

These metrics are permutation-invariant with respect to label names. They can show whether turns are divided similarly to human stages, but they cannot show that an annotation called, for example, `diagnose authentication` means the same thing in different sessions, that two distinct responsibilities were not falsely merged, or that paraphrased instances of the same responsibility were not split. This is especially consequential because the appendix states:

> “Equal canonical names receive one stable operation ID across sessions.”

and

> “The complete replay reduces 3,895 open-vocabulary names to 783 two- or three-word identities with zero adjacent path collision, while preserving every temporal mark occurrence.”

Zero *adjacent display-path collision* is not evidence of semantic merge precision across nonadjacent or cross-session occurrences. The reported direct-Agent boundary F1 is only 0.480, with substantial over-segmentation, making the absence of a direct cross-run identity evaluation even more important. The closed-label AgentBoard and ASE experiments use separate evaluation-only backends and different output spaces; they do not validate the open-vocabulary names used by the main recursive profiler.

This is a blocker for the headline scientific claim. The paper needs a repeated-task, multi-session benchmark with independently annotated semantic equivalence classes and hierarchical relations. It should report false-merge and false-split rates, name/meaning accuracy, hierarchy accuracy, and stability across annotation runs, models, and trajectory paraphrases. At least some evaluation should weight errors by tokens or other profiled mass, because a small number of high-mass false merges can dominate a profile.

### 2. The headline RQ2 ranking gains do not isolate semantic profiling

The abstract foregrounds:

> “On three complete localization workloads, AgentProf raises MAP over benchmark-native direct diagnostics by 0.031, 0.107, and 0.117.”

Numerically, Direct+AgentProf does raise MAP by refining exact ties in the direct diagnostic. However, the matched baseline removes the claimed semantic advantage:

> “Candidate-minus-baseline intervals are [-.0003,.0029], [-.0116,.0103], and [-.0247,.0280], so this experiment does not establish that the semantic-operation prefix ranks targets better when both views retain the same source evidence.”

The next sentence states the implication correctly:

> “The matched result attributes the ranking gain to group/evidence refinement in the complete profile, not specifically to its semantic prefix.”

Thus, the main MAP result validates propagation and aggregation of retained evidence, not the semantic names or recursive semantic hierarchy that constitute the paper's central novelty. The result remains useful as a systems result, but its current prominence in the abstract and conclusion encourages a stronger semantic interpretation than the ablation supports.

The TraceElephant reading study offers a more specific semantic result—equal ranking quality while opening less evidence than a raw-action skeleton—but it depends on one external LLM reader and does not validate human debugging. A stronger evaluation would compare semantic, raw-action, native, and strong cross-trace baselines under identical evidence and information budgets, on questions that require cross-run responsibility rather than per-trajectory localization. It should measure both answer correctness and evidence/time cost.

### 3. RQ1 does not establish “improved resource attribution”

The paper itself reveals the construct gap:

> “RQ1 asks whether semantic profiling improves resource attribution. We test one necessary consequence: whether a fixed semantic hierarchy reveals materially different bottlenecks when the additive resource measure changes.”

Showing that counts, time, and tokens assign different widths is a useful capability demonstration, and exact conservation is an important invariant. It is not, by itself, evidence that semantic attribution is more correct than native-session, prompt, action-kind, or other hierarchies. Different measures can naturally reorder any grouping. The three-run Git example is compelling as an illustration, but it is a selected case with no independent ground truth for the recursive responsibility names or for the engineering decision that should follow. At population scale, most count/token rankings are highly correlated, which establishes stability but not improvement.

RQ1 should test attribution against independent responsibility labels or downstream decisions. For example, evaluators could answer blinded resource-cause questions, select optimization targets, or predict intervention effects from semantic versus native/coarse profiles. The experiment should cover many repeated tasks and report whether semantic attribution improves correctness, time-to-answer, or intervention value—not merely whether a resource selector changes widths.

### 4. The thesis is not tested against a realistic debugging or observability workflow

The memorable thesis is:

> “Agent observability needs profiling, not only debugging.”

However, no developer or operator study compares AgentProf with trace search, dashboard aggregation, raw trajectories, or a closest cross-trace analysis tool on the population-level questions used to motivate the paper. The localization benchmarks are per-query ranking tasks, not population profiling tasks. The profile-guided reader is an LLM proxy, and the differential-profile case shows an association whose fixed-chain control is at least as predictive. The appendix concedes:

> “RQ2 does not measure end-user diagnosis time.”

Consequently, the paper demonstrates that profiles can be constructed and contain interesting patterns, but not yet that profiling materially improves a real user's diagnosis, safety investigation, or resource decision. This also weakens the broad AI significance at AAAI: the paper currently looks like a promising representation and tooling contribution whose claimed workflow advantage remains inferred.

A decisive study would pose blinded population questions over real repeated tasks, compare AgentProf with raw traces, metadata aggregation, raw-action grouping, and a strong existing cross-run representation, and measure accuracy, time, evidence opened, and confidence for both human developers and an automated reader. It should include negative cases where semantic folding is misleading.

### 5. The “long horizon” claim is not supported by long-horizon accuracy evidence

The paper accurately discloses:

> “Per-workload mean operations per trajectory are 8.5 (AgentProcessBench), 13.9 (OSWorld-Human), 24.0 (HINTBench), 27.1 (TraceElephant), and 51.5 (CodeTraceBench), so benchmark trajectories are short-to-medium horizon while the 42-session workstation population—whose longest sessions span tens of hours—supplies the long-horizon regime.”

But the only explicitly long-horizon population is the authors' own development history, for which:

> “This case establishes descriptive feasibility on real long-horizon sessions without outcome labels.”

Therefore, the accuracy results do not establish that recursive boundaries or cross-run names remain reliable on the regime named in the title. The protocol also says:

> “The evaluated Agent backend reads each trajectory’s complete source-only packet once and directly emits sparse complete-path marks at the transition points it identifies, naming every enclosing responsibility.”

Per-field preview limits do not explain the total packet/context limit, how a tens-of-hours trajectory fits, what is dropped when it does not fit, or how one-pass annotation degrades with length. The self-profile's 70.4% of token mass remaining at mandatory prompt depth further suggests that semantic refinement can be shallow precisely where token attribution matters.

The paper needs long-horizon ground truth or carefully designed human annotations, accuracy versus trajectory length, context-size and truncation ablations, and an incremental/chunked alternative. Without this, “Long Horizon” is a feasibility claim rather than a validated quality claim.

### 6. A key semantic-benefit experiment is not reproducible or statistically robust enough

The TraceElephant study says:

> “On the complete 220 target-bearing TraceElephant queries, a fixed external Grok-family CLI reader receives target-blind packets—task text, operation IDs, and source-visible content—with unranked operations appended in original order deterministically and one single-turn call per stage.”

“Grok-family CLI reader” does not identify an exact model/version, decoding configuration, prompt, tool version, or provider snapshot. The paper does not report repeated reader runs, run-to-run variance, or human calibration. These omissions matter because the 53% versus 65% evidence-opening result is the clearest experiment that attributes a distinct benefit to semantic naming rather than generic evidence grouping.

The paper should provide the complete reader prompt/configuration and exact version, run multiple samples or justify deterministic decoding, report selection stability, and calibrate the reader against humans or a deterministic oracle on a subset. Similar provenance should be tabulated for every Agent/LLM backend used across the case studies.

## Minor issues

1. The evaluation is difficult to synthesize because “tag,” “operation,” “responsibility,” “stage,” “group,” “partition,” and “boundary” refer to different targets across different backends and datasets. A single table mapping each RQ to backend, input visibility, target construct, metric, population, and claim would help substantially.

2. The title should be “Long-Horizon AI Agents.” More importantly, the title currently suggests validated long-horizon annotation quality, whereas the PDF establishes only descriptive feasibility in that regime.

3. The privacy discussion is too narrow. Bounded previews, semantic names, source labels, commands, and exact file/network targets can still contain secrets or personal data. Hosted annotation explicitly sends preview-truncated packets to a provider, but the paper gives no redaction policy, threat model, retention assumptions, or empirical privacy analysis.

4. The safety motivation is not carried through. The abstract asks which workflows trigger unsafe effects, but the evaluation demonstrates file/network attribution and problem correspondence rather than unsafe-effect detection or safety outcomes.

5. Peak RSS of 465.2 MiB for 27,765 operations is nontrivial, and the paper does not test substantially larger populations or report output size. The near-linear timing fit over this range is not enough to establish production-scale storage and query behavior.

6. The formal model defines nonnegative additive weights, whereas the differential case emits signed sample values. The subtraction is intuitively reasonable, but the formal object should either include signed comparison profiles or distinguish base profiles from comparison operators and state which pprof operations remain valid.

7. The closest-work comparison is a property checklist in prose. Even within the paper's own evidence, “No compared system provides all four” does not establish that the four-way combination is the right or necessary construct. A same-input qualitative or quantitative comparison with at least one closest cross-run method would make the novelty and practical distinction clearer.

8. The authors' 42-session self-profile is useful as an existence proof but carries selection and interpretation bias. It should not substitute for an independent long-horizon population.

9. HINTBench is called complete while using 536 of 629 paper-reported trajectories. The PDF explains that this is the complete released test snapshot, but the abstract's unqualified “three complete public localization benchmarks” should be made precise.

10. Several strong results are “with marks fixed,” while annotation dominates wall time and token cost. The separation is technically correct, but conclusions should consistently distinguish fast profile replay from expensive semantic construction.

## Questions for the authors

1. How do you measure false semantic merges across sessions? Is there any independent evidence that two occurrences assigned the same canonical operation ID express the same responsibility?

2. How stable are the open-vocabulary paths across repeated annotation runs, model versions, prompt paraphrases, and different agent frameworks? What fraction of high-token mass changes parent or name?

3. What exact source-only canonicalization map reduces 3,895 names to 783 identities, and how was it designed without looking at human stages or evaluation outcomes? Could this map itself encode a task-specific taxonomy?

4. Why is RQ1 phrased as improved attribution rather than multi-measure replay? What is the ground truth or downstream decision by which one attribution is judged better?

5. For the longest sessions, what is the total packet token count and model context limit? Are all turns present, and what happens when the packet exceeds the context window?

6. What exact Grok model, CLI version, prompt, decoding configuration, and provider date were used? Were repeated calls deterministic, and are the raw ordered group selections available?

7. How would a human operator use the standard pprof interface to answer the motivating population questions, and how does task accuracy/time compare with a trace browser or metadata dashboard?

8. Can all stock pprof views and operations safely handle the signed differential profiles, or only selected renderers/queries?

9. Why are only 536 of the 629 paper-reported HINTBench trajectories in the released test snapshot, and do the missing trajectories differ systematically?

10. What artifact will be released to reproduce source reconstruction, annotation, canonicalization, all profile files, and the reader study while respecting the privacy constraints?

## Final assessment

**Overall recommendation: Weak Reject (4/10).**  
**Confidence: 4/5.**

The paper's principle, in plain language, is: recursively assign stable semantic responsibilities to heterogeneous agent events so that evidence and additive costs can be folded across runs with standard profiling tools. This is a strong and potentially lasting idea. The challenged belief is that rich per-run traces and debugging views are enough for agent observability; the paper plausibly argues that they do not provide reusable population-level semantic responsibility.

The strongest alternative explanation for the results is that most measured benefit comes from LLM preprocessing, group-level propagation, and retained evidence—not from accurate shared semantic identity or recursive semantic hierarchy. The paper's own matched RQ2 control supports this explanation. The largest defensible claim today is that AgentProf is a useful, interoperable representation and reading index for grouping source-linked trajectory evidence under replayable measures. The stronger claim that it provides accurate cross-run semantic profiling and improves resource attribution is not yet established.

The decisive experiment is an independently annotated long-horizon, repeated-task population spanning agents and models, with gold cross-run semantic equivalence and hierarchy. AgentProf should be compared against native, raw-action, and a strong cross-trace baseline on blinded resource-attribution and diagnosis tasks, measuring semantic false merges/splits, operator or reader correctness, time/evidence cost, robustness across model runs, and annotation cost. This would directly test the paper's central causal chain.

I view the work as **incomplete but promising**, not complicated-but-shallow. The core abstraction is simple and useful, and the paper shows commendable empirical and reporting discipline. However, the missing validation concerns the very property that makes the artifact a *semantic cross-run profiler*. I would encourage resubmission after that evidence is added and the headline RQ2/RQ1 claims are recalibrated.

Terms that could be merged or clarified without losing content include “tag,” “semantic operation,” and “responsibility” when they denote the same predicted path element. “Group,” “stage,” “partition,” and “boundary” should remain distinct, but the paper should state explicitly that they are evaluation surrogates rather than interchangeable definitions of semantic accuracy.

## Internal inconsistencies or defects visible in the PDF

The following are visible from the PDF itself. Some are claim/evidence mismatches rather than arithmetic contradictions.

1. **The core RQ1 wording exceeds the tested construct.**

   > “RQ1 asks whether semantic profiling improves resource attribution. We test one necessary consequence: whether a fixed semantic hierarchy reveals materially different bottlenecks when the additive resource measure changes.”

   Testing one necessary consequence does not answer the stated comparative question of whether attribution improves.

2. **The abstract's RQ2 headline is numerically true but does not expose the matched semantic null result.**

   > “On three complete localization workloads, AgentProf raises MAP over benchmark-native direct diagnostics by 0.031, 0.107, and 0.117.”

   versus:

   > “Candidate-minus-baseline intervals are [-.0003,.0029], [-.0116,.0103], and [-.0247,.0280], so this experiment does not establish that the semantic-operation prefix ranks targets better when both views retain the same source evidence.”

   The PDF later explains that the gain is attributable to group/evidence refinement, but the abstract can readily be read as evidence for the semantic hierarchy.

3. **“Tag accuracy” does not consistently evaluate the semantics of tags.**

   > “RQ3: How Accurate Are the Tags?”

   versus:

   > “A backend output is evaluated at the level it predicts: literal names, permutation-invariant leaf partitions, or adjacent interval boundaries.”

   The main direct-Agent result is a permutation-invariant partition/boundary result. It does not evaluate whether its open-vocabulary tag names are semantically correct or share identity across runs.

4. **The completeness claim is ambiguous for HINTBench.**

   > “We evaluate AgentProf on 405 human-staged CodeTraceBench trajectories, three complete public localization benchmarks, 287 OSWorld-Human sessions, three population case studies, and four public cost workloads.”

   versus:

   > “We run complete AgentProcessBench, HINTBench (the complete released test snapshot, 536 of the paper-reported 629 trajectories), and TraceElephant workloads”

   “Complete released test snapshot” is a defensible scope, but “three complete public localization benchmarks” is too unqualified when one population is 536 of 629 paper-reported trajectories.

5. **The formal profile domain is nonnegative, while a showcased output is signed.**

   > “We formalize a resource profile as (φ, σ, wr): predicate φ(n) selects source nodes, σ(n) supplies the composed stack, and wr(n) = mn[r] ≥ 0 selects one additive resource.”

   versus:

   > “Formally, the signed profile is the difference of two nonnegative profiles, (φ, σ, wr)bad − (φ, σ, wr)good; each side satisfies the model’s nonnegative additive-measure definition, and pprof renders the subtraction as positive and negative sample values.”

   The subtraction is explained, but the resulting signed object is outside the stated resource-profile definition. The formalism should include a comparison-profile operator or explicitly define a second object.

6. **The title's long-horizon implication is not matched by accuracy evidence.**

   > “Per-workload mean operations per trajectory are 8.5 (AgentProcessBench), 13.9 (OSWorld-Human), 24.0 (HINTBench), 27.1 (TraceElephant), and 51.5 (CodeTraceBench), so benchmark trajectories are short-to-medium horizon while the 42-session workstation population—whose longest sessions span tens of hours—supplies the long-horizon regime.”

   and:

   > “This case establishes descriptive feasibility on real long-horizon sessions without outcome labels.”

   Thus the long-horizon regime supplies feasibility, not validated semantic accuracy.

7. **The practicality conclusion depends on excluding the dominant construction cost.**

   > “With marks fixed, AgentProf builds a 27,765-operation profile in 1.16 seconds, making population profiling practical alongside per-run debugging.”

   versus:

   > “Deterministic materialization of the full 440-session population takes 0.26 s (operations) and 0.25 s (tokens): construction cost is dominated by the automatic backend, and materializing this population remains sub-second.”

   The “with marks fixed” qualification is present and prevents a numerical contradiction, but the conclusion conflates cheap replay with end-to-end practicality unless annotation cost and update frequency are considered.

8. **The motivating safety scope is not answered by an evaluation RQ.**

   > “AI agents produce growing populations of execution histories, and developers need population-level answers about where failures concentrate, which workflows trigger unsafe effects, and which task categories consume the most budget.”

   The four RQs cover resource attribution, correspondence to real problems, tag accuracy, and profiling cost. File/network target conservation demonstrates effect attribution, but the PDF contains no unsafe-effect ground truth or safety decision evaluation.
