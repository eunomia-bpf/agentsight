# Independent Full-Paper REVIEW Gate

**Timestamp:** 2026-07-12T05:42:00-07:00  
**Reviewer:** fresh read-only `iter-review-critique` subagent  
**Simulated decision:** Reject, 3/10  
**Confidence:** 4/5  
**Taste:** incomplete but promising; not yet a complete simple-but-deep paper

## Bottom Line

The paper has recovered a clear and important principle:

> In AI-agent observability, analysis hierarchy is not truth supplied by the
> trace. Like the measure, it is part of profiling semantics and must be
> validated against the real decision.

The reject reason is not idea shrinkage or negative results. It is evidence
completeness. RQ1 currently has conservation/category-separation evidence, RQ2
has two real negative conditions, and RQ3 has a mapping proxy. The paper does
not yet establish which signal properties select native, flat, or recursive
profiling. The next outer transition is EXPERIMENT, not more prose polishing and
not a smaller contribution.

## Strongest Novelty Threat

Most mechanisms are strongly precedented:

- domain-specific profiling constructs hierarchical models over domain events
  and developer-selected dimensions;
- pprof supports weighted hierarchies, labels, tag-derived frames, and diffs;
- Pivot Tracing performs query-time cross-component selection/filter/grouping;
- Hodoscope establishes semantic cross-run behavior discovery;
- AgentDiagnose uses action embeddings, t-SNE, and state-transition views;
- ARIA projects actions into intention space and aggregates reward across
  semantically similar trajectory prefixes.

Therefore operation + configurable stack + semantic grouping + profiler output
is insufficient novelty alone. The live contribution is a conditional empirical
law: whether signal support, recurrence, fragmentation, and inspection objective
predict the winning profiling index.

## Blockers

### B1. All three RQs remain incomplete

- RQ1 lacks independently verified lineage.
- RQ2 has no condition demonstrating positive or sharply conditional value and
  lacks end-to-end cost.
- RQ3 lacks unchanged transfer and a view-selection rule.

The reviewer cannot yet decide when AgentProf should be used, which view should
be selected, or the decision loss from selecting incorrectly.

### B2. Hodoscope is a valid bundle boundary, not the selection law

The run validly establishes that official Hodoscope beats the tested recursive
bundle, recursive parents have no stable matched advantage, turn position is
not a full native tree, and cost begins after shared t-SNE. Because Hodoscope
also changes KDE contrast, normalization, and FPS, it cannot establish why the
bundle wins. The next experiment must start with a directly recorded additive
regression/effect.

### B3. The recursive experiment is under-specified relative to the system

The paper describes a Rust inducer based on chronological splitting, TF-IDF
shift, visible field changes, balance, and query terms. The Hodoscope evaluation
uses fixed 8/32/128 nested clustering. The paper must minimally define fit/apply,
node contrast, action ordering, and whether this is the AgentProf path, a thin
evaluation adapter, or an external instantiation of the abstraction. No new
mechanism name is needed.

### B4. No genuine source-native tree is directly compared

The core belief challenge still lacks a controlled result over a preserved
`trajectory -> message/turn -> tool/action` tree. Turn ordinal cannot substitute
for that baseline.

### B5. The belief challenge risks a strawman

Existing systems already regroup traces. The stronger, testable challenge is
not “execution tree is not the only view,” but:

> Neither execution hierarchy nor a semantically plausible hierarchy earns
> authority from structure alone; each must compete on the measure and decision.

The paper now states this well but needs evidence to make it more than a
reasonable position.

### B6. RQ1's headline statistic is circular accounting evidence

Prompt tags participate in both grouping and the separation oracle. The paper
acknowledges this, but the 36.7% versus 84.4% result cannot establish intent or
lineage. RQ1 needs independent tool/span and process lineage, with precision,
recall, unassigned, duplicated, and lost mass.

### B7. RQ3's mapping transfer does not answer RQ3

V-measure/boundary-F1 between a predefined taxonomy and native action labels
does not show decision value, predictable view selection, unchanged constructor
transfer, or superiority to arbitrary/native grouping. After a decisive RQ2
condition, apply the same mapping/stack unchanged to an untouched family.

## Major Paper Issues

1. Hodoscope's live paper reports the iQuest effect at about three actions; the
   pinned script yields 2.9 +/- 0.3. Say that the first-hit-at-about-three effect
   reproduces, rather than implying identical printed mean/SD. Clarify that
   Phase B fits on 11,855 actions but ranks the 4,006 target actions.
2. The 15-family/47,590-operation inventory and its relationship to the
   13,265-operation figure need a compact table or appendix pointer.
3. Both negative experiments need enough constructor, scorer, baseline, and
   bootstrap detail to reproduce the results.
4. The system contribution lacks import correctness, trace fidelity,
   throughput/memory/storage scaling, pprof compatibility, and malformed-input
   behavior. It may remain an enabling artifact if the empirical principle
   becomes strong.
5. Related work should explicitly discuss ARIA and AgentDiagnose; Sifter is a
   lower-priority trace-sampling precedent.
6. Rendered `\S\ref{...}` section references appear as empty section signs under
   the AAAI template. Replace them with robust named references or fix the
   template-compatible numbering.

Minor defects include “Inclusive inclusive mass,” incomplete RQ1 figure-caption
values, and the need to distinguish Phase B algorithmic randomness from
cross-task uncertainty.

## Cycle-Change Audit

All critical recovery boundaries pass:

- Hodoscope is completed, not future work.
- Bundle comparison and hierarchy-only isolation are separated.
- No flatness/continuous-geometry causal claim is made.
- Turn position is not called a full execution tree.
- Cost is limited to post-t-SNE components.
- AgentRx/TELBench and Hodoscope negatives remain visible.
- Cost, regression, safety, and failure remain in RQ2.
- No identity/scope/navigator mechanism stack returned.
- Operation and operation stack remain the only core abstractions.
- The paper has not regressed into a leaf-localization paper.

The remaining risk is allowing “no hierarchy has automatic authority” to become
a polished meta-conclusion that replaces the larger empirical goal. The next
experiment must sustain the bold claim with new evidence.

## Primary External Sources

- [Domain-specific profiling](https://inkytonik.github.io/assets/papers/scp14.pdf)
- [pprof documentation](https://github.com/google/pprof/blob/main/doc/README.md)
- [Pivot Tracing](https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/)
- [Differential Flame Graphs](https://asgaard.ece.ualberta.ca/papers/Conference/SANER_2015_Bezemer_Understanding_Software_Performance_Regressions_using_Differential_Flame_Graphs.pdf)
- [Hodoscope live paper](https://hodoscope.dev/blog/livepaper.html)
- [OpenInference specification](https://arize-ai.github.io/openinference/spec/)
- [AgentRx](https://arxiv.org/abs/2602.02475)
- [AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/)
- [ARIA](https://arxiv.org/abs/2506.00539)
- [tau-bench paper](https://openreview.net/pdf?id=roNSXZpUDN)
- [tau2-bench repository](https://github.com/sierra-research/tau2-bench)

## Next Decisive Experiment

Run the official tau-bench source/data preflight first, then—only if it
passes—one paired additive-regression experiment:

> When matched real tasks produce excess tool work, which hierarchy most
> efficiently attributes that recorded measure to actionable recurring
> behavior?

Preflight must confirm matched trajectories, a faithful
`trajectory -> message/turn -> tool call -> tool result` structure, a directly
recorded additive measure, linkable official action/effect checks if a
first-fault metric is claimed, and one semantic mapping fixed outside the target
subset.

The complete experiment compares only:

1. flat terminal tool/action;
2. genuine source-native conversation/tool hierarchy;
3. one fixed semantic task/phase/action stack.

All use identical operations, measure, pairing, and inspection accounting. A
semantic, native, or flat win is scientifically valuable if its condition is
clear. A failed preflight is recorded as a source rejection and returns to data
search; it does not authorize a toy regression.

## Final Route

**REVIEW_GATE: below submission bar.**  
**Next node: EXPERIMENT_GATE — tau-bench source/data preflight, then one complete
real additive-regression comparison.**

Do not narrow the RQs, remove negative results, or add abstractions. The missing
ingredient is evidence that turns “hierarchy is a hypothesis” into a predictive
result about which hierarchy should win.
