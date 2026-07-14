# Review 001 / Node 300 — Full-Paper Reread and Scientific Assessment

**Started:** 2026-07-13 16:22:03 PDT
**Completed:** 2026-07-13 16:25:18 PDT
**Parent:** [`200-external-search-and-source-verification.md`](200-external-search-and-source-verification.md)
**Node status:** complete
**Paper edit authority:** none

## Objective

Reread the entire authoritative paper after source verification, test every
load-bearing inference against current closest work and the implemented
artifact, and determine whether the paper is ready for AAAI or which evidence
class must run next. Final source routing remains provisional until the
independent convergence review in Node 400.

## Inputs and method

The reread covered:

- all of `docs/paper/main.tex`, bibliography, figures, tables, and rendered
  pages;
- the exact submodule authority comparison;
- the primary sources verified in Node 200;
- focused implementation inspection under `agentpprof/src/`,
  `agentpprof/tests/`, and the current `docs/implementation.md`;
- the completed Cycle 0003 HINTBench plan, preflight, full result, and two
  independent result audits;
- current AAAI-27 official rules and the actual PDF page boundary.

The method was to reconstruct the full causal chain, attack alternative
explanations, distinguish scientific from writing/format defects, and preserve
the fixed thesis/RQ contract while selecting the highest-value evidence route.

## Source-grounded causal chain

The paper asks the reader to accept:

```text
many heterogeneous agent executions
-> per-execution structure is insufficient for population responsibility
-> uniform operations preserve intent/effect facts and additive measures
-> stable semantic fields and operation stacks aggregate recurring responsibility
-> the profile correctly attributes resources and concentrates real problems
-> analysts improve cost, safety, and quality decisions
```

The current paper demonstrates that records can be converted, projected, and
folded, and that the artifact can emit useful visual formats. The two hardest
edges remain under-supported:

1. semantic/cross-layer responsibility is correct rather than a grouping
   construction; and
2. the profile produces a better real-problem inspection decision under a
   target-blind, information-equivalent protocol.

## Ranked final findings

### Blocker 1 — reader-facing RQ2 is target-informed

The exact paper protocol ranks groups by hidden-positive density. This directly
uses the outcome that localization is supposed to discover. Task-specific
field/rank/depth reruns compound the threat. The visible headline work number
is also not matched to the same recall as competing methods.

This is the strongest AAAI reject argument because it invalidates the paper's
main evidence that profiling changes a real decision. It requires a new
EXPERIMENT, not prose calibration or claim shrinkage.

### Blocker 2 — RQ1 does not independently establish responsibility

Adding the category identifier to the grouping key necessarily removes mixing
with respect to that category. The paper demonstrates configurable separation
and association, but not correct causal or semantic ownership of the downstream
resource/effect observations.

A later RQ1 experiment must compare against an independent task/effect lineage
or controlled responsibility reference and information-equivalent trace/query
baselines. This blocker remains after the next RQ2 experiment, but RQ2 is
selected first because a strong official external source is currently
available and directly attacks reviewer decision value.

### Blocker 3 — RQ3 does not test the load-bearing taggers

Structured action-to-phase mapping is not natural-language intent tagging.
The current experiment does not establish held-out semantic adequacy,
stability, abstention, or downstream robustness for regex, local-LLM, or
clustering backends. This needs a later complete experiment under fixed RQ3.

### Major 1 — RQ4 omits full cold-path accounting

The paper separates profile execution from 35,136 uncached tag calls, so the
`1.6 s` number is not complete first-time profiling cost. A later RQ4 run must
measure cold and warm end-to-end time, memory, output size, and scaling over
complete workloads.

### Major 2 — paper and artifact mechanisms disagree

Focused source inspection verifies:

- the current Rust inducer computes a token-set/Jaccard semantic shift plus
  field changes and other visible signals, not TF-IDF cosine similarity;
- TF-IDF/K-Means exists in the optional Python clustering backend, not the Rust
  operation-stack inducer;
- the CLI imports local agent sessions, operation JSONL, portable
  agent-session traces, and standard/Chrome traces;
- no direct AgentSight-recording reader appears in the current CLI;
- current implementation memory explicitly requires AgentSight evidence to be
  converted and does not claim verified trigger lineage.

The paper's direct-AgentSight reader, triggered-effect reconstruction, and
TF-IDF-induction sentences are therefore factual mismatches. This is not a
reason to change the thesis or model. It is later targeted implementation or
WRITE work, after the evidence gate decides which implementation is final.

### Major 3 — closest-work positioning is inaccurate

Phoenix, Datadog, Hodoscope, AgentDiagnose, and systems trace-query work mean
that cross-run evaluation, semantic clustering, and flexible aggregation
cannot be described as absent. The stronger story is not smaller:

> Existing tools can trace, evaluate, cluster, and query agent behavior, but
> have not established an agent profiling abstraction that preserves additive
> responsibility across intent and system effects and reduces population-level
> inspection under a target-blind protocol.

This wording remains a later WRITE responsibility. REVIEW does not edit it.

### Major 4 — the complete four-RQ paper is not empirically complete

All four RQs are explicit and well organized, which is a strength. None yet has
fully independent, load-bearing evidence at the scope claimed. Submission
readiness therefore cannot be inferred from prose quality or a clean build.

### Minor — presentation and reproducibility

- The architecture figure should eventually expose operation construction,
  source/effect correlation, field derivation, projection, and folding more
  clearly.
- The flame graphs illustrate three resource views but do not by themselves
  demonstrate an analyst decision.
- Limitations and threats need a compact treatment.
- Grammar issues remain.
- The official reproducibility checklist exists in the paper directory but is
  not yet a completed submission artifact.

## Cycle 0003 HINTBench assessment

Cycle 0003 completed the declared scope:

- 80/80 validation and 536/536 test trajectories;
- 12,877/12,877 test operations;
- 616/616 terminal Qwen3.6-27B outputs;
- all 24 validation field orders;
- AgentProf plus native, independent-step, per-session, raw-action, flat, and
  width controls;
- 10,000 paired complete-trajectory bootstrap replicates;
- two independent exact result reconstructions.

AgentProf reached 80% macro recall at `41.5702%` atomic-step work versus
`46.2918%` for raw action, but the paired interval against raw action was
`[-0.293709, +0.008566]`. The predeclared all-baseline positive condition did
not pass. The result is valid and scientifically informative but
**INCONCLUSIVE** for the tested hypothesis.

The experiment therefore establishes a mechanism boundary: the current
action/environment/phase/status construction did not add decisive evidence
over action alone on this population. It is not a direct thesis challenge. It
does not authorize RQ/story shrinkage, target retuning, or a paper result.

## Story and authority audit

After newline normalization, the user-supplied authoritative attachment and
`docs/agentpprof-paper/main.tex` are identical. The active paper differs only
in venue packaging. No Cycle 0003 paper edit followed the inconclusive result.

| Invariant | Assessment |
|---|---|
| Exact thesis retained | yes |
| Exactly four fixed RQs retained | yes |
| Original abstract/introduction/background/design retained scientifically | yes |
| Contribution narrowed or replaced | no |
| HINTBench mixed result inserted into paper | no |
| Submodule modified | no |

## AAAI format audit

The current PDF has eight pages on US-letter paper. Main content ends on page
seven and the remaining page contains references. This complies with the
official seven-page-main/nine-page-total rule. The paper uses the AAAI-27 style
and anonymous metadata. Format is therefore not the current blocker.

## Scientific character and verdict

- **Problem:** important and recurring.
- **Principle:** simple and potentially durable.
- **Belief challenge:** real when stated as per-execution insufficiency for
  population responsibility.
- **Strongest alternative explanation:** curated semantic fields,
  target-informed ranking, and task-specific tuning explain the visible gains.
- **Largest claim worth defending:** AgentProf turns heterogeneous executions
  into population profiles that correctly attribute additive costs/effects and
  concentrate recurring real problems in substantially less inspection work.
- **Current AAAI verdict:** **Reject / major experimental revision**.
- **Taste classification:** incomplete-but-promising.

The paper can become top-venue work, but it is not submission-ready now. Its
story is already large enough; the next action must earn it.

## Provisional route

The highest-value next route is one fixed-RQ2, fresh, complete,
target-blind experiment on TraceElephant. It has better source/mechanism fit
than Who&When because it contains the full inputs, tool/environment responses,
status, system metadata, and multiple architectures needed to test whether
context beyond raw action produces useful cross-run profiles.

The detailed plan, metric, baselines, completion rule, and success criterion
belong to Node 400 and the next `research-experiment-design` PROPOSE loop after
independent route convergence.

## Paper and claim impact

No paper edit is authorized. The final result of the next experiment, not this
review, determines whether any quantitative RQ2 statement can be replaced or
added. Mechanism facts and related work require later targeted fixes, but those
fixes must preserve the exact story.

## Tree and search updates

- close HINTBench test to any further field, prompt, metric, or threshold
  tuning;
- retain its result as a mechanism boundary;
- open TraceElephant as the fresh full-observability RQ2 branch;
- retain Who&When as closest prior work and partial-observability context;
- keep RQ1 responsibility truth, RQ3 real tag accuracy, and RQ4 cold/warm cost
  as later sibling evidence blockers.

## Project-memory updates

No canonical file is edited in REVIEW. The final route report must list stale
frontier pointers and hand them to the top-level orchestrator for one coherent
post-review update.

## Completion assessment and next node

The source-grounded full-paper assessment is complete. Node 400 must compare
independent reviewers, settle TraceElephant versus Who&When, audit Cycle 0003
process drift, select exactly one next experiment, and state the transition
without modifying paper or submodule.
