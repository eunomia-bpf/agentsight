# Idea Round 3 — Contributions, Goals, and Research Questions

## Context

- **Started:** 2026-07-11T20:59:00-07:00.
- **Recovered:** 2026-07-11T21:12:32-07:00; see
  `recovery-20260711T211232-0700.md`.
- **Completed:** 2026-07-11T21:26:16-07:00.
- **Cycle / gate / node:** cycle 0001 / WRITE_GATE /
  `iter-refine-ideas` Round 3.
- **Parent:** `round-02h-final-reattack.md`.
- **Final status:** `PASS` after three independent review/fix passes.

The node reviewed the complete current paper against Sections 3--4 of the
idea-quality checklist. It was restricted to contribution statements, G1--G3,
the paper-level RQ set, their ownership of admitted and planned evidence, and
current-versus-target status. It did not treat missing future experiments or
AAAI page pressure as a reason to shrink the idea. The active user instruction
requires preserving cross-run semantic profiling, the multi-resolution
navigator, real-problem correspondence, and full cost rather than replacing
them with an easier leaf-group or failure-only paper.

## Entry Evidence And Method

The review read the full `docs/paper/main.tex`, current bibliography, admitted
RQ2 revision-0 result, and the idea-quality checklist. Reviewers were read-only;
the main agent applied changes and compiled the whole paper after each repair.
Formal review and repair state remained in Markdown. The English source
subproject under `docs/agentpprof-paper/` stayed read-only at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

The first reviewer found seven concrete breaks:

1. G1--G3 still described the older fixed-stack story, omitting single
   recorded-correlation inheritance, mass conservation, induced-prefix
   identity, and bounded navigation.
2. Intent-attribution prose incorrectly routed clustering validation to the old
   RQ3 and retained an unsupported “under 5% in 5--10 rounds” workflow number.
3. Contributions did not explicitly map to RQs.
4. The evidence contribution stopped at the negative flattened-leaf result and
   left fresh full-hierarchy RQ2 and complete cost outside the target paper.
5. RQ1 read as complete although stable induced identity was unvalidated.
6. The architecture caption did not separate the implemented pipeline from the
   specified-but-pending stable identity and navigator stages.
7. A stale bilingual comment still assigned mapping transfer to cost RQ3.

After those repairs, a second full-paper reviewer found that the scope-tree
contract and navigator were two independently rejectable deliverables packed
into Contribution 1, while navigator ownership was duplicated across
Contributions 1 and 2. It required a three-part scientific decomposition:

- C1: semantic scope-tree model and contract;
- C2: AgentProf system plus complete-scope navigator;
- C3: claim-facing evidence.

A third fresh reviewer then applied the checklist's RQ split and coverage tests.
It found two deeper defects:

- the then-RQ1 combined cross-layer inheritance/conservation and cross-family
  identity transfer even though either can fail independently and each has
  different evidence;
- the immutable RQ2 promised failures, safety violations, and wasted effort, but
  both admitted and planned evidence covered only failure localization.

The latter could not be repaired by narrowing “real problems” to failures. That
would violate the paper's quality/safety/cost motivation and the recorded user
instruction. Primary external sources were therefore opened to identify
method-independent, step-level safety and waste benchmarks:

- [ToolSafe / TS-Bench, Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.1850/),
  which provides step-level unsafe-tool-invocation labels;
- [RedundancyBench, arXiv:2605.29893](https://arxiv.org/abs/2605.29893),
  which provides externally annotated redundant trajectory steps.

Existing SATraj-OS, AgentRewardBench, and AgentNet assets were not promoted to
fresh confirmation because they have already informed this repository's method
and prior experiment development.

## Paper Revisions

### Goals and design ownership

The old goals were broadened without adding a fourth named abstraction:

- **G1:** cross-layer inheritance along recorded correlations, exactly-once
  assignment, and additive-measure conservation;
- **G2:** stable cross-run identity for natural-language variants and induced
  prefixes under a vocabulary frozen before confirmation;
- **G3:** query-selectable mass-conserving trees and bounded, cost-normalized
  navigation whose advantage must beat native, fixed, matched, and current-log
  scopes empirically.

The Design opening now maps uniform operations and inheritance to G1, intent
attribution and the frozen labeler to G2, and constructors plus navigator to G3.
It immediately distinguishes the implemented parse/enrich/construct/fold/render
pipeline from pending stable induced identity and navigation.

### Contributions

The paper retains exactly three target contributions, each independently
rejectable:

1. the semantic scope-tree model/contract;
2. AgentProf plus its complete-scope navigator;
3. claim-facing evidence.

An adjacent current-status paragraph prevents target contributions from being
mistaken for completed results. It states that the contract is specified, the
current compiler and trace-local constructors exist, stable induced identity and
the navigator remain unimplemented, and fresh RQ2 plus complete cost evidence
has not run.

### Four-RQ architecture

The paper now maintains four explicit paper-level RQs, within the required
two-to-five range:

1. **RQ1:** Does semantic identity preserve cross-layer attribution?
2. **RQ2:** Does profiler output correspond to real problems?
3. **RQ3:** Do semantic identities transfer across heterogeneous agents?
4. **RQ4:** What is the complete profiling cost?

RQ2's wording remains exactly unchanged from the admitted experiment. The
ownership chain is explicit:

- G1 -> C1 inheritance/conservation -> RQ1;
- G2 -> C1 stable identity -> RQ3;
- G3 -> C2 navigator -> RQ2;
- practical C2 realization and complete cost -> RQ4;
- C3 aggregates evidence from RQ1--RQ4.

The frozen-transfer RQ2 experiment also exercises induced identity, but RQ3
remains the canonical owner of that claim.

The former mixed RQ1 evidence was separated. RQ1 now closes with the supported
accounting result: exactly-once assignment and total-weight conservation under
declared prompt categories, with 84.4% to 36.7% mixed-weight separation, without
claiming semantic correctness or diagnostic utility. RQ3 separately reports the
deterministic nine-dataset mapping transfer and marks stable induced-scope
identity unanswered.

### Complete RQ2 outcome program

The admitted AgentRx/TELBench result is now explicitly a partial negative answer
for failure localization, not an answer to all real problems. The preserved
larger RQ2 requires one semantic vocabulary, risk function, and navigator frozen
before three non-substitutable fresh outcome families:

- failures: Who&When and TRAIL;
- unsafe actions: ToolSafe's TS-Bench;
- wasted effort: RedundancyBench.

Every dimension uses whole-candidate-scope coverage of external gold operations
or spans, matched operation/token and end-to-end cost, and semantic-leaf,
chronological, fixed-field, native-tree, matched-shape, and published native
baselines. Results must be reported separately; an average cannot conceal a
failed dimension. This grows the evidence program to match the original RQ
instead of shrinking the RQ to match the easiest existing data.

### Source-fidelity and status repairs

- Removed the unsupported regex-authoring convergence number.
- Changed clustering status to “not validated in the current paper.”
- Marked RQ1/RQ3 partial or complete only at the construct actually tested.
- Corrected the RQ1 figure caption to session-only 84.4% -> prompt-tag 36.7%.
- Marked the architecture figure as the current implemented pipeline.
- Updated cost ownership from old RQ3 to RQ4 everywhere, including Conclusion.
- Added verified primary bibliography records for ToolSafe and RedundancyBench.

## Independent Final Review

The final fresh reviewer re-read the complete paper and checklist Sections 3--4
without write-gate reports. Verdict: **PASS**, zero idea/scientific must-fixes.
It confirmed:

- four distinct, load-bearing RQs;
- unchanged RQ2 wording;
- unique G1--G3 -> C1--C3 -> RQ1--RQ4 -> evidence ownership;
- separately owned failure, safety, and wasted-effort evidence;
- explicit current-versus-target status;
- no negative result presented as support;
- no silent narrowing of cross-run profiling, full hierarchy, real-problem
  breadth, or end-to-end cost.

The reviewer classified implementation of the frozen labeler/navigator, fresh
RQ2 execution, stable induced-identity validation, and RQ4 scale/cost execution
as future experiment gaps rather than idea-layer defects.

## Compilation And Artifact Evidence

Commands:

```text
cd docs/paper
make clean
make all
pdflatex -interaction=nonstopmode main
pdfinfo main.pdf
```

The final build exits successfully, uses US Letter, resolves all citations and
cross-references, and emits a 10-page PDF. Two overfull boxes remain (8.11 pt in
G3 and 0.99 pt around the RQ2 table). More importantly, scientific content still
extends past AAAI's seven-page content limit. This is recorded as a mandatory
later writing/layout repair; it is not grounds for deleting contributions,
outcome dimensions, or missing-evidence disclosures.

## Decision, Alternatives, and Next Node

Rejected alternatives:

- retain the compound old RQ1 for compactness;
- rename or narrow RQ2 to failure localization;
- count development-used SATraj-OS/AgentRewardBench/AgentNet as fresh
  confirmation;
- hide unimplemented stages to make contributions look complete;
- remove scientific status text merely to recover page space.

Round 3 is complete. The next node is Round 4 cross-alignment: a fresh reviewer
must read the entire paper and test problem -> challenged belief -> principle ->
goals -> contributions -> RQs -> evidence blocks for one coherent story. It
must especially check that Abstract, Introduction, Related Work, and Conclusion
have caught up with the new scope-tree/navigator mechanism and four-RQ evidence
program. Only after Round 4 and the Round 5 reject stress test pass may the idea
loop request its independent outer audit and hand off to `iter-refine-writing`.
