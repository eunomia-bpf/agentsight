# RQ2 Mechanism Search Before Claim Revision 01

## Status

This is a source-grounded search node, not an approved experiment plan and not
an admitted paper result. It records a mechanism candidate while revision-0
RESULT REVIEW is still completing.

The immutable RQ remains:

> Does profiler output correspond to real problems?

The user-intended contribution remains a multi-resolution, agent-independent
semantic operation stack. Negative revision-0 evidence must not be converted
into a smaller leaf-grouping claim or used to remove the hierarchy.

## Trigger From Revision-0 Evidence

The complete AgentRx/TELBench point matrix shows that ranking induced leaf
partitions by the mean learned operation risk does not outperform strong
session, tag, SQL, action, or fixed-window baselines. The especially diagnostic
TELBench ablation is that ranking the same induced leaves by group width
produces higher AP than the learned risk ranker. This suggests that the current
failure is not merely a bad split depth: the experiment discarded the
hierarchy and asked a flat leaf ranker to solve a two-stage debugging problem.

## Primary External Sources

### Scope Delineation Before Localization (AAAI-26)

- Official paper: <https://ojs.aaai.org/index.php/AAAI/article/view/40594/44555>
- Official code link reported by the paper: <https://github.com/Wen-qiangLi/SDBL>
- The method explicitly separates failure-scope identification from exact-step
  localization and reports up to 24.27 percentage points of improvement in
  step accuracy on the real Who&When benchmark.
- Its evaluation exposes the intermediate scope with Hit@K rather than treating
  scope construction and final localization as one flat ranking.
- Scientific implication for AgentProf: a semantic operation stack should be
  evaluated as a coarse-to-fine navigation index, not collapsed to leaf keys.

### Who&When (ICML 2025)

- Official paper: <https://proceedings.mlr.press/v267/zhang25cq.html>
- Official code/data link reported by the paper:
  <https://github.com/mingyin1/Agents_Failure_Attribution>
- The benchmark contains failure logs from 127 LLM multi-agent systems with
  responsible-agent and decisive-step annotations. Existing methods reach only
  14.2% step accuracy in the original study, making it a discriminating fresh
  confirmation surface rather than an easy toy workload.

### AgentRx

- Primary paper: <https://arxiv.org/abs/2602.02475>
- AgentRx synthesizes constraints, evaluates them step by step, and gives an LLM
  judge an evidence-bearing validation log. This is a stronger comparison than
  plain prompting and confirms that intermediate structure must carry
  diagnostic evidence, not only reduce cardinality.

### TELBench / DRIFT

- Primary paper: <https://arxiv.org/abs/2606.02060>
- DRIFT is claim-centric: it tracks claims, tests trajectory support, and then
  marks harmful spans. This again decomposes scope/evidence construction from
  final span localization.

### ECHO

- Primary publication page:
  <https://www.amazon.science/publications/where-did-it-all-go-wrong-a-hierarchical-look-into-multi-agent-error-attribution>
- ECHO reports a hierarchical context representation followed by objective
  evaluation and consensus. It independently supports hierarchy as an active
  reasoning interface rather than a flat visualization.

### REFLECT

- Primary paper: <https://arxiv.org/abs/2606.09071>
- REFLECT tests a candidate attribution through controlled replay and feeds an
  observed outcome flip back into attribution. This supplies a stronger future
  validation axis: correspondence should eventually predict interventions, not
  stop at retrospective label overlap.

### TRAIL

- Primary paper: <https://arxiv.org/abs/2505.08638>
- TRAIL contributes 148 human-annotated real software-engineering and
  information-retrieval traces. The reported low performance of long-context
  LLM debuggers makes it another potential fresh external workload, subject to
  verifying that its released labels support the exact navigation metrics.

## Candidate Principle

**Scope before localization.** A semantic operation stack corresponds to real
problems only if its internal nodes let a debugger first select a small,
evidence-bearing failure scope and then refine within that scope. Leaf-only
ranking destroys the proposed abstraction before testing it.

This principle is simple, non-obvious in the context of profiling, falsifiable,
and larger than the failed revision-0 mechanism. It predicts both an
intermediate property (failure-containing scope Hit@K under bounded work) and a
downstream property (better exact-step/span localization after hierarchical
navigation).

## Candidate Mechanism, Not Yet Approved

1. Preserve every prefix of each induced semantic path.
2. Rank internal scopes using development-only signals that combine operation
   risk, risk concentration, width, and semantic coherence.
3. Allocate a fixed inspection budget coarse-to-fine: inspect a ranked internal
   scope, then its children, then operations within the selected leaf.
4. Keep all confirmatory labels outside induction and navigation.
5. Measure scope Hit@K, exact localization, inspected operations, and inspected
   nodes against flat/session, fixed windows, SQL rollups, SDBL-style random
   and expertise scopes, and official native methods where executable.

## Fresh-Confirmation Requirement

AgentRx and TELBench have now informed mechanism diagnosis, so a revised
mechanism must not present a retuned rerun on those two datasets as untouched
confirmation. Use the released Who&When benchmark as the first fresh external
confirmation candidate. Qualify TRAIL or another released annotated trace
benchmark as a second family. AgentRx/TELBench may remain explicit
development/diagnostic families and later external-validity replications.

## Decision Pending RESULT REVIEW

If revision-0 evidence passes validity review, propose claim revision 01 around
coarse-to-fine semantic navigation, then write and review a new experiment plan
for the same immutable RQ through three to five rounds before implementation.
Do not change the RQ, remove the multi-resolution contribution, or claim that
this search alone validates the new mechanism.

## Source Qualification Update

The primary repositories were cloned read-only outside the project for
qualification:

- SDBL commit `9734e4c26b34e677997df2f750a74ae69dd21e41` currently contains only
  a README stating “We will release it soon.” The AAAI paper is a citable
  published protocol, but no experiment may claim to run an official SDBL
  implementation unless that repository later releases one. A faithful thin
  reimplementation, if needed, must be labeled as such.
- Who&When / Agents Failure Attribution commit
  `b2bae5c5b06d681d04ea5e9b63b7a30525c04925` contains the original inference
  and evaluation code plus 184 released JSON trajectories: 58 hand-crafted and
  126 algorithm-generated. Every released `mistake_step` is within the
  corresponding history; trajectories contain 5–130 steps. The repository is
  therefore a viable real fresh-confirmation asset and its original all-at-once,
  step-by-step, and binary-search paths are executable baseline candidates.

The source count supersedes the earlier paper-derived shorthand in this report;
an approved revision-1 plan must use the exact 184 released files or document
source-native exclusions.

- TRAIL commit `0ffbed9db859b4a66250dc783fa4dccf86869595` contains the
  complete 148-trace benchmark and evaluator: 117 GAIA information-retrieval
  traces and 31 SWE-Bench software-engineering traces. Every trace has a
  corresponding processed annotation file with error categories and exact span
  locations. It is therefore qualified as a second, distinct fresh confirmation
  family for hierarchical scope Hit@K and span localization, not merely as a
  paper-only contextual citation.
