# Root Disposition — `iter-refine-ideas`

- Timestamp: `2026-07-13T07:31:40-07:00`
- Parent: `cycle-0002-20260712T201943-0700 / WRITE`
- Entry paper: `docs/paper/main.tex`
- Authoritative story: original AgentProf submodule plus the user-selected attachment
- Rounds received: 3/3, serial and independent
- Overall decision: **KEEP CANONICAL; NO IDEA-STORY EVOLUTION**

## Procedure audit

All three discussants read the same complete entry snapshot and were denied the earlier rounds' outputs. Each discussion was read-only and used no Git. Every memo compared the permanent Initial Narrative, the current canonical story, and a larger proposed direction; preserved the exact thesis and four fixed RQs; offered unexpected directions; named the most important unasked question; and gave an explicit disposition.

Round 3 additionally used `research-literature-novelty` and primary papers or official product/project sources for its closest-work map.

Snapshot after all three rounds:

| Artifact | Entry SHA-256 | Post-discussion SHA-256 | Status |
|---|---|---|---|
| `docs/paper/main.tex` | `5206a19142c97171d03444a2d1aaebde251414b9f629ef536d9a8603d3c54629` | `5206a19142c97171d03444a2d1aaebde251414b9f629ef536d9a8603d3c54629` | unchanged |
| `docs/paper/references.bib` | `f044ea5eb5a5e3dba7aee92e2bbb8e634cad484b60428ae379e10cf48eca70c3` | `f044ea5eb5a5e3dba7aee92e2bbb8e634cad484b60428ae379e10cf48eca70c3` | unchanged |
| `docs/idea-story.md` | `361048311c9752da4e85a5fb4c2d00e8371d85f26defbc37fbd450ef17fd5036` | `361048311c9752da4e85a5fb4c2d00e8371d85f26defbc37fbd450ef17fd5036` | unchanged |
| `docs/user-instruction.md` | `c7a41fbbca65d9c5415dfe93a2219c1d8989dc1d0f49f9c69b9a3a684a8f4bd9` | `c7a41fbbca65d9c5415dfe93a2219c1d8989dc1d0f49f9c69b9a3a684a8f4bd9` | unchanged |
| `docs/evaluation.md` | `96b130dcf72999bd3547a02a3fe9876825dca84980b902ede44926a953814ea5` | `96b130dcf72999bd3547a02a3fe9876825dca84980b902ede44926a953814ea5` | unchanged |

## Convergence

All three rounds independently reached **KEEP CANONICAL**.

They agree that the durable scientific idea is population-level agent profiling, not hierarchy selection, semantic clustering, a particular ranker, or a visualization:

> **Agent observability needs profiling, not only debugging.**

The original problem is already larger than the later alternatives: individual traces are samples from a growing operational workload, while developers need recurring responsibility categories that attribute quality failures, unsafe effects, wasted work, and resource consumption across executions.

They also agree that only two core abstractions are needed:

1. an **operation**, the fielded evidence unit carrying additive measures; and
2. an **operation stack**, the query-time responsibility path used to fold those measures.

Taggers, mappings, filters, weights, stack induction, rankers, pprof serialization, and flamegraphs remain supporting mechanisms. None is promoted to a new contribution.

## Fixed scientific state

The following remain immutable in this WRITE cycle:

- thesis: **“Agent observability needs profiling, not only debugging.”**
- RQ1: attribution;
- RQ2: real-problem localization;
- RQ3: tag accuracy;
- RQ4: profiling cost;
- positive hypothesis under each RQ;
- broad quality, safety, failure, wasted-work, and cost stakes;
- problem → two-object model → AgentProf system → four-RQ evaluation architecture.

One experiment evaluates one tested hypothesis within an RQ. Neither of the two AgentProcessBench score constructions answers RQ2. Their internal `VALID / INCONCLUSIVE` status does not alter the thesis, RQ2, its positive hypothesis, or the final paper story.

## Accepted guidance for the writing loop

These items clarify the canonical story without changing its scientific meaning:

1. Make the population-level transition explicit: per-run traces record occurrences; profiling aggregates recurring responsibility across many executions.
2. Keep the concrete decision stakes—what to optimize, inspect, or constrain—visible as motivation for RQ1/RQ2, without adding a fifth RQ or a “decision layer.”
3. Keep operation and operation stack central; present all other components as mechanisms beneath them.
4. Clarify that an operation stack is a query-time responsibility path, not a claim that agents literally lack execution trees.
5. Do not equate semantic grouping with correct attribution, diagnosis, or causal proof.
6. In RQ2 prose, name the independent measurement or ranking signal rather than implying that grouping itself predicts failures.
7. State the dependency that RQ3 validates semantic fields used in RQ1/RQ2 and RQ4 tests practical repeated use, without changing RQ order or meaning.
8. Avoid requirement labels that can be confused with RQ numbering.
9. Avoid categorical closest-work wording that is factually stale. Datadog and LangSmith already aggregate cost and semantic/tag metadata; AgentProf must distinguish cross-layer operations, query-time responsibility paths, system effects, and measured decision value.
10. Preserve the exact conclusion thesis sentence.

These are authorized presentation and factual-precision targets only. They do not authorize new numerical claims, changed RQ meanings, new hypotheses, narrowed scope, or insertion of internal results.

## Accepted guidance for later REVIEW/EXPERIMENT

The larger story should be earned through complete external evidence rather than asserted early:

- **fleet-level profiling:** multiple real agents/frameworks and multiple measured resources;
- **differential profiling:** compare versions/configurations and locate recurring categories responsible for a regression;
- **profile first, diagnose second:** use a fleet profile to allocate a bounded diagnosis budget to a few recurring groups;
- **profile-to-intervention:** apply one profile-selected repair and measure improvement on a complete held-out workload.

The preferred next RQ2 source screen is the official ClawTrace artifact/protocol because it is a close cost/redundancy and intervention baseline. If it is not fully runnable, continue autonomously to a complete fresh source such as TrajAD/TrajBench or AgentLocate. Do not construct a third score on AgentProcessBench.

This experiment ordering is not a paper claim and does not change the current WRITE gate.

## Rejected proposals and reasons

| Proposal | Disposition | Reason |
|---|---|---|
| Replace thesis with execution-tree authority, representation choice, cross-run recurrence, or decision-oriented aggregation | Reject | All are supporting observations or implications and are smaller/less memorable than the canonical thesis. |
| Add lineage graph, decision hierarchy, scope tree, confidence layer, profile contract, or another named abstraction | Reject | Operations and operation stacks already cover the scientific model; added objects create jargon without an independent necessity. |
| Make semantic grouping, stack induction, a scorer, or pprof output the main contribution | Reject | These are mechanisms and cannot carry the broad profiling claim. |
| Add a fifth RQ for intervention or decision utility | Reject | Decision value is the interpretation of RQ1/RQ2 and can be tested within them. |
| Narrow RQ2 around AgentProcessBench or publish its inconclusive internal result | Reject | One tested construction does not answer the RQ, and internal negative results do not belong in the positive paper story. |
| Claim existing tools cannot aggregate semantically or by cost | Reject | Current official product documentation contradicts the categorical statement; the stronger differentiation is what is represented, attributed, and made actionable. |
| Immediately insert fleet/differential/intervention claims | Reject for now | They are attractive evidence targets but require complete real experiments first. |

## Why no `docs/idea-story.md` entry is added

The idea skill returns proposals; it does not automatically mutate the story. This root disposition accepts no new thesis, RQ, hypothesis, contribution, or model abstraction. The canonical story is preserved rather than evolved. Adding an evolution entry for unchanged science would create a misleading record of narrative movement and make future agents re-litigate an already resolved baseline.

The three detailed discussion reports and this disposition provide the auditable record of why the story stayed fixed.

## Handoff to `iter-refine-writing`

The writing loop may now improve structure, flow, abstract/introduction expression, factual consistency, terminology, language, and citations under the following locks:

- no scientific idea change;
- no RQ or hypothesis change;
- no numerical-result change;
- no evidence-status change;
- no paper claim derived from the internal AgentProcessBench results;
- no edit to `docs/idea-story.md` or `docs/agentpprof-paper`;
- no Git operation.

Every accepted edit must make the canonical story clearer, simpler, and more attractive—not smaller.
