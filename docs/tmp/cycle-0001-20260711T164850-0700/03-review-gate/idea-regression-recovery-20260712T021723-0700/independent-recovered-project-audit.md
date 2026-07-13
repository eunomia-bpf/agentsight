# Independent Audit Of The Recovered AgentProf State

**Audit timestamp:** 2026-07-12  
**Role:** independent, read-only reviewer  
**Inputs:** complete current paper, verbatim user instructions, current idea,
evaluation, design, implementation, and literature frontiers, admitted RQ2
result, and original `docs/agentpprof-paper/` sources  
**Excluded:** earlier recovery verdicts, round reports, and recovery plan  
**Repository actions:** none; no files edited and no Git commands run

## Verdict

**Idea recovery: PASS.** The project did not shrink the idea. It preserves the
original operation and operation-stack abstractions and advances the larger,
principled position that an execution tree is evidence about one run but need
not be the canonical profiling index for recurring behavior across runs. The
position remains simple, broad across cost/regression/safety/failure/waste, and
falsifiable because native, flat, or recursive semantic views may win.

**Evidence and experiment state: REVISE.** The negative AgentRx/TELBench result
is represented honestly and the old proposal machinery is not claimed as
implemented. The paper is nevertheless research-in-progress rather than
top-conference complete because the central matched representation comparison
has not run. Several wording issues and experiment-definition ambiguities must
be corrected before the Hodoscope experiment.

## Evidence Integrity

The audit independently checked the admitted result:

- AgentRx AP 0.02584 versus prevalence 0.02236; the improvement interval crosses
  zero;
- TELBench AP 0.21487 versus prevalence 0.21384; the improvement interval also
  crosses zero;
- width-only ranking is stronger on TELBench;
- all predeclared positive criteria failed.

The same numbers and conclusion appear in the current paper. The paper correctly
limits falsification to the tested flattened induced leaves rather than all
operation stacks. It also correctly separates conservation from lineage,
declared-category separation from semantic correctness, mapping agreement from
diagnostic value, and component timing from end-to-end decision value.

## Must-Fix Findings

### M1 — RQ2 subsection narrows the canonical question

Canonical RQ2 asks when a semantic or differential operation-stack profile
improves a real cross-run cost, regression, safety, or failure decision over
flat and source-native views under matched information and effort. The paper's
RQ2 subsection instead begins with top-ranked groups corresponding to failures,
safety violations, or wasted effort. That is the old localization framing and
omits cost, regression, direct measures, native/flat comparison, and matched
effort.

**Required correction:** state canonical RQ2 at the subsection start, then
present AgentRx/TELBench explicitly as one narrow partial test.

### M2 — Two sentences overstate what has been tested

The contribution list says the paper “formulates and tests” the representation
mismatch by comparing native, flat, and recursive indices, but that decisive
comparison has not run. The background also says RQ1 tests cross-layer
attribution, although the RQ1 section states that present evidence does not test
lineage correctness.

**Required correction:** use “formulates and begins testing” and state that RQ1
currently tests conservation/category separation while independent cross-layer
attribution remains open.

### M3 — The Hodoscope candidate conflates two official protocols

The official walkthrough/demo samples 50 trajectories per model with seed 42,
forming five cohorts and 250 trajectories. The paper's quantitative evaluation
uses a fresh 50% subsample per group, reruns projection over ten seeds, and
reports the mean and standard deviation of rank-to-first-hit.

**Required correction:** separate:

1. an exact reproduction of Hodoscope's published ten-seed quantitative
   ranking protocol; and
2. an all-250 AgentProf comparative extension over the official demo corpus.

The extension must not be described as a strict reproduction, and the official
Hodoscope quantitative result must still be reproduced separately.

### M4 — Group views do not yet define a comparable raw-action order

The primary metric is raw actions inspected before the first positive action.
Hodoscope produces action order through density-weighted farthest-point
sampling, while native and semantic profiles produce groups or nodes. The
current candidate does not state:

- how a group becomes an action order;
- the tie/order rule within a group;
- whether opening a group charges one representative or every member;
- how native and semantic nodes receive comparable scores;
- whether all views use one sampler after representation.

These choices can dominate the result independently of representation.

**Required correction:** every matched view must deterministically emit one
complete permutation of the same target raw actions. Charge one inspected raw
action per position. Use the same cohort-difference score and action-selection
rule wherever mathematically possible, with deterministic tie-breaking fixed
before oracle labels are joined.

### M5 — “Flat per-action” is not a strong matched flat-semantic baseline

Unique raw actions provide no cross-run aggregation. If summaries or behavior
clusters are used, the plan must say so. A semantic-stack win is uninterpretable
if features or ranker capacity change together with hierarchy.

**Required correction:** for the matched views, use the same action records,
summaries/embeddings, cohort labels, development data, and cohort-difference
score. Define the flat semantic view as one terminal semantic unit per action
or behavior cluster with no recursive parents; define the recursive view by
adding only the prespecified stack hierarchy.

### M6 — The exploit oracle and counts are conflated

The official demo reports 79 literal `git log` actions among 4,006 actions. The
paper's quantitative appendix reports 132 oracle-positive `git log` or
`git show` actions among the same 4,006 actions. Neither automatically means a
human-confirmed future-patch exploit.

**Required correction:** reproduce the published rigid `git log|git show`
oracle and call it an oracle-positive action. If reporting confirmed exploit,
add an independent transcript-level annotation and report its agreement with
the published oracle. Do not use 79 and 132 interchangeably.

### M7 — The source-native baseline needs a demonstrated adapter

AgentProf can preserve native hierarchy when adapters supply trajectory,
turn/tool, or trace/span fields. Its general trace importer does not reconstruct
arbitrary span nesting automatically.

**Required correction:** construct a thin evidence-faithful adapter from each
official raw source to `trajectory -> turn -> tool/action`, record exact source
fields used, and validate a sample of parent/order relationships before the
full run. Do not imply general automatic nesting recovery.

### M8 — A last proposal-only term remains

The RQ3 section says a failed result should not trigger “a new identity
subsystem.” The term is unexplained and re-primes the discarded proposal.

**Required correction:** state directly that failure supports task dependence
or native-tree sufficiency.

## Should-Fix Findings

1. Canonical documents repeat the names of discarded stable-identity,
   scope-tree, navigator, bundle, and cost machinery. Keep one compact statement
   that reviewer-generated mechanisms are archived and not current
   contributions; leave names/details in the archive.
2. Replace the introduction's absolute statement that teams “cannot” rank
   categories with the evidence-backed claim that execution-tree-only
   inspection fragments recurring behavior and makes ranking expensive.
3. Replace “materially changes the analysis surface” with the exact observation
   that depth changes the grouping surface; reserve materiality for a decision
   result.
4. Call the five-cohort source the official walkthrough/demo, not the paper's
   quantitative protocol.
5. Treat one SWE-bench exploit experiment as decisive evidence in one RQ2
   condition, not a complete answer to “when” across all domains.

## Valid Open Uncertainties

These are recorded and resolved autonomously where possible; they are not
reasons to wait for human intervention:

- availability of the four pinned Docent collections and iQuest archive;
- official API cost and whether author-released summaries/embeddings can avoid
  a model substitution;
- whether a semantic hierarchy chosen without target exploit labels is useful;
- fidelity of the source-native trajectory/turn/tool reconstruction;
- representation-versus-ranker confounding;
- implicit known-behavior bias because the exploit is already public;
- transfer beyond a behavior concentrated in one model cohort;
- unresolved RQ1 lineage and local prompt-tag validity.

## Final Assessment

The recovery succeeded at the most important level: it restored a large,
simple, attractive thesis without erasing contradictory evidence. The immediate
direction is also scientifically strong because Hodoscope is a real public
system with real public trajectories and a human-review metric. The candidate
becomes execution-ready only after protocol identity, common raw-action
ordering, flat baseline, oracle, and source-native adapter are defined. Then a
full run can identify representation value rather than merely compare unrelated
ranking pipelines.
