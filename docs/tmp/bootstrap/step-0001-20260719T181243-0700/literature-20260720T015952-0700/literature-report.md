# Closest-Work Audit: Graph Diagnosis And Long-Trajectory Retrieval

Started: 2026-07-20T01:59:52-07:00
Gate: BOOTSTRAP / EXPERIMENT_GATE literature dependency
Scope: read-only claim, method, artifact, and baseline audit after the static RQ1 preflight veto

## Objective And Coverage Boundary

This audit asks whether the proposed algorithm can claim novelty from (1)
representing Agent actions as a temporal/dependency graph, (2) navigating long
traces through retrieval, or (3) using structured history for automatic
diagnosis. It searches direct Agent diagnosis, dynamic temporal graph retrieval,
long-trajectory navigation, and graph-based retrieval. It does not survey human
visual analytics, visualization layout, or coding-Agent outcome benchmarks,
because the current consumer is an automatic supervisor Agent and the force
layout is not the paper algorithm.

Candidate claims were searched without the Agent Nebula name:

1. dependency-aware action graphs improve automatic Agent failure diagnosis;
2. event-centric temporal graphs improve long-history retrieval;
3. a bounded Agent can inspect full-fidelity long trajectories on demand; and
4. persistent workspace transformations across top-level sessions and goals add
   diagnostic evidence beyond run-local traces at a matched access budget.

## Search Strategy And Verification

| Time | Query/source family | Verification | Result |
|---|---|---|---|
| 2026-07-20 | `graph guided diagnosis runtime intervention LLM agent` | arXiv abstract and complete local PDF | AgentTether is direct same-mechanism work for transition graphs, graph-guided localization, diagnosis, repair memory, and intervention. |
| 2026-07-20 | `long horizon agent trajectory search segment retrieval aggregation` | complete AggAgent PDF and official repository HEAD | AggAgent supplies a strong full-fidelity navigation interface: final solution, trajectory search, and exact segment read under one context. |
| 2026-07-20 | `dynamic graph RAG event temporal reasoning` | arXiv abstract, complete local PDF, official repository HEAD | DyG-RAG already claims event units, temporal/causal graph links, and time-aware traversal. |
| 2026-07-20 | `graph retrieval personalized PageRank long term memory` | NeurIPS 2024 proceedings page and official repository HEAD | HippoRAG establishes graph retrieval with Personalized PageRank; PPR is an absorbable standard ranking method, not novelty here. |
| 2026-07-20 | prior OCPM, AgentRx, TrajAudit, HarnessFix audit | canonical background file and retained PDFs | Object/event lifecycle graphs and structured Agent diagnosis were already rejected as standalone novelty. |

Primary artifact checks:

- AgentTether: arXiv:2607.06273, PDF SHA-256
  `cea3202f209976220a0269ff6b047f6bfb6c0b5293e9065d751df768cedc8916`.
  The paper names an anonymous artifact URL, but a cloneable public repository
  was not available during this audit.
- AggAgent: arXiv:2604.11753, PDF SHA-256
  `cff96aab0f97e43de7c61b6fafe4107e0c841a00c5f08776642e932ebb034088`;
  `princeton-pli/AggAgent` HEAD
  `9638f7d88aee01eb636c02841e13a05bb2e3c449`.
- DyG-RAG: arXiv:2507.13396, PDF SHA-256
  `d41a70db49ce29d69ac7cdcde29fe5ea7686ba36aab76cb975f07b17cfb7e164`;
  `RingBDStack/DyG-RAG` HEAD
  `ca37e449f0bfba188644bd5e66809473578c30bf`.
- HippoRAG: NeurIPS 2024 proceedings and `OSU-NLP-Group/HippoRAG` HEAD
  `1e8f60981bf760b64003aa5bf5668126d0c106b3`.

## Closest Work Findings

### AgentTether

AgentTether partitions a run into Transition Units, each organized around an
Observation--Belief--Action--Feedback cycle. It constructs a Critical
Transition Graph with temporal order and dependency edges, including shared
artifacts and errors. An offline heterogeneous graph transformer models normal
execution; a run-local Isolation Forest uses fixed-dimensional transition
features; an analyst model converts localized subtrajectories into guidance and
repair memory. The paper evaluates 261 tau-bench tasks and reports repair under
Qwen3.7-max and cross-model transfer to GPT-5.4.

This is a direct threat to any claim that transition units, dependency-aware
graphs, graph-guided diagnosis, anomaly localization, or diagnosis-guided
retry/intervention are new. Its current unit is one run in a tool/API-state
environment, however. The paper does not reconstruct exact persistent file
state across independent top-level sessions and goals, compare coding with
auto-research workspaces, or isolate the incremental diagnostic value of
cross-goal workspace history against a same-evidence retrieval baseline.

### AggAgent

AggAgent treats long parallel trajectories as an environment instead of
concatenating them. Its Agent can retrieve final solutions, keyword-search a
trajectory using ROUGE-L ranking, and read an exact contiguous segment. This
preserves full-fidelity access while bounding the aggregation process by one
context window. The method addresses aggregation, not diagnosis, and its
trajectory set is parallel rollouts rather than a persistent workspace across
goals.

Nevertheless, it is the strongest interface precedent for the RQ1 Raw
baseline. A Raw condition that simply truncates, summarizes, or statically
serializes the source would now be knowingly weak. Raw Retrieval should reuse or
faithfully adapt AggAgent's search-and-segment navigation, then add exact-record
access needed for evidence IDs.

### DyG-RAG And HippoRAG

DyG-RAG constructs Dynamic Event Units with explicit temporal anchors, links
events through shared entities and temporal proximity, and retrieves coherent
event timelines through time-aware traversal. HippoRAG uses a knowledge graph
and Personalized PageRank for efficient multi-hop retrieval. Their tasks are
temporal and multi-hop QA, not long-horizon Agent oversight, but together they
eliminate novelty claims based on event graphs, temporal traversal, or PPR
ranking.

If Agent Nebula later needs automatic graph ranking, a published algorithm such
as PPR or a frozen temporal traversal is preferable to hand-tuned edge weights.
It must be compared against lexical Raw search and ablated. The first RQ1 pilot
can avoid ranking entirely by exposing deterministic queries and letting the
same supervisor choose them.

## Novelty And Algorithm Consequences

The following claims are rejected:

- a new graph representation of Agent trajectories;
- a new action/dependency graph for Agent diagnosis;
- a new event-centric temporal retrieval mechanism;
- a new idea of full-fidelity interactive navigation over long traces; and
- graph retrieval or Personalized PageRank as a contribution.

The surviving candidate is narrower and falsifiable:

> For long-horizon work that crosses top-level sessions and goals, exact
> persistent-workspace transformations provide diagnostic evidence not present
> in run-local transition graphs and make that evidence more reliably
> retrievable by an automatic supervisor than an equal-budget full-fidelity Raw
> interface.

This is not yet established and has medium-to-high same-claim risk. Its distinct
unit is a workspace supervision interval, not a run; its distinctive evidence
is exact artifact version/effect state across goal boundaries, not merely a tool
call's mentioned artifact; and its hard cases include successful-but-
pathological work, not only failed runs.

The minimum non-ad-hoc algorithm is therefore:

1. parse native Agent actions through the existing `agent-session` abstraction;
2. attach only source-proven system effects with exact call/time/session/goal
   ownership, resolving each `*at` path against its decoded `dirfd`;
3. version persistent artifacts and emit deterministic order, ownership,
   effect, version, hierarchy, and source-evidence relations;
4. mark every attempted attachment as `observed`, `no_effect`, or `unknown`,
   never converting missing coverage to absence; and
5. expose exact queries over this store without classification weights,
   learned labels, visual decay, hotspot thresholds, or semantic guesses.

This construction is linear in ordered actions and effects. Its graph schema is
an implementation of established object-centric/event-process ideas, not a
novel learned model. Paper novelty must come from the problem unit, evidence
source, matched evaluation, and demonstrated incremental utility.

## Baseline And Experiment Impact

The next RQ1 plan requires one strong baseline and one structured condition:

- **AggAgent-style Full Raw Retrieval:** `search(scope, query, k)`,
  `read_record(raw_id)`, and `read_range(scope, start, end)` over all complete
  native, system, snapshot, evaluator, specification, and harness evidence.
- **Workspace Trajectory Retrieval:** the identical Raw tools plus
  `artifact_history`, `action_context`, `goal_diff`, and `validation_after`.
  Each result contains canonical Raw IDs and no generated diagnosis.

Both conditions must have the same model, neutral prompt, source membership,
total rendered token/byte budget, tool-call budget, action-ID namespace, and
output schema. The evaluation must blind condition and perturbation names and
freeze gold labels plus a working scorer before inference. State Diff and Counts
remain reduced controls.

AgentTether is the closest structured diagnosis method. If its official runtime
becomes available, run it on predeclared compatible failed-run cases. If not,
compare a faithful Critical-Transition-Graph relation/feature condition where
the source schema permits and avoid direct numerical superiority claims. OCPM
remains the standard lifecycle/process structure control; HarnessFix remains
the harness-specific structured baseline.

## Alternatives Considered

- **Repair the static serializer:** rejected. Even a compact form would remain
  an artificial context-flood baseline and would ignore AggAgent's stronger
  interface precedent.
- **Train a graph neural network immediately:** rejected. AgentTether already
  establishes this mechanism, and the project has no valid labeled corpus yet.
- **Hand-weight recency, writes, directories, or edge types:** rejected for the
  scientific core. These are visualization choices or separately ablated
  heuristics, not grounded diagnostic algorithms.
- **Use PPR as the main novelty:** rejected. HippoRAG makes it prior art. PPR is
  only an optional standard retrieval component if deterministic queries prove
  insufficient.
- **Claim a universal graph schema:** rejected. OCEL/OCPM and DyG-RAG already
  cover the general representation family.

## Remaining Uncertainty

The search found no work that combines exact file/workspace effects, independent
top-level session and goal boundaries, successful-but-pathological work, and a
same-evidence/same-budget automatic diagnosis comparison. Absence from this
search is not proof of absence. AgentTether appeared in July 2026, so the
closest-work audit must be refreshed immediately before submission. Its
anonymous artifact may also become public and change baseline feasibility.

The larger scientific risk is not novelty wording but effect size: an
AggAgent-style Raw supervisor may recover the same evidence as structured
queries. A tie would reduce the contribution to retrieval efficiency; a Raw win
would reject the representation claim. This is an informative outcome and
should be tested before any large corpus investment.

## Search-Strategy Changes And Next Node

The literature search moved from generic trajectory diagnosis to exact
same-mechanism searches: transition graph diagnosis, full-fidelity trajectory
navigation, dynamic temporal graph retrieval, and standard graph ranking. This
found closer work than the initial diagnosis/process-mining survey and narrowed
the claim accordingly.

Next node: close the source/action interval contract by reusing
`agent-session`, specify the minimal neutral query broker and AggAgent-style Raw
baseline, then submit a fresh two-domain preflight plan to independent review.
No model run or paper-effect claim is admitted by this literature node.
