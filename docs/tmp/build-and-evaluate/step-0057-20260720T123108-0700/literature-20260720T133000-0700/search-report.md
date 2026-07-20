# Literature Search — Task-Semantic Trajectory Ground Truth

## Node Identity

- timestamp: 2026-07-20T13:30:00-07:00
- parent: Step 0057 contradicted global Qwen2.5-3B constructor
- skill explicitly read and applied: `research-literature-novelty`
- objective: find primary published protocols and official real assets that
  can evaluate task/subtask meaning separately from flat trajectory boundaries
- scope: read-only for paper, idea story, user instructions, and thesis; one
  concise canonical update to `docs/background-related-work.md`

## Fixed Claims And Coverage Boundary

The fixed thesis and four paper RQs remain unchanged. The search strips project
names and asks three plain questions:

1. Does published work already segment complete agent trajectories into
   semantic subtasks?
2. Is there a public real-agent dataset with human task/subtask hierarchy and
   temporal alignment to actions?
3. Which official asset can separately test boundary fidelity, hierarchy/name
   fidelity, and diagnostic consequence without inventing a custom metric?

Threat categories were same problem, same mechanism, same evaluation, adjacent
process mining, hierarchical task specifications, and logical-hop
trajectories. The bounded search stopped once each category had a verified
primary paper plus official artifact status or a documented availability gap.

## Search And Primary Verification

Searches included:

```text
AI agent trajectory benchmark hierarchical subtask annotations task decomposition
GUIDE GUI agent trajectory diagnosis subtask decomposition benchmark
agent workflow trajectory segmentation benchmark stage annotations
global trace segmentation activity tree process mining
DevAI hierarchical solution requirements official repository
agent trajectory subtask segmentation human annotations dataset
```

Primary sources opened and checked:

| Work | Primary source and artifact | What it establishes | What it does not establish |
|---|---|---|---|
| GUIDE: Interpretable GUI Agent Evaluation via Hierarchical Diagnosis | [April 2026 arXiv preprint](https://arxiv.org/abs/2604.04399) | A full action-summary LLM call predicts contiguous subtask boundaries and descriptions before per-subtask diagnosis; 932 industrial, 1,302 AgentRewardBench, and 480 AndroidBench trajectories support downstream evaluator accuracy. An MLLM rates all 3.3k generated subtasks, with 99.4% judged usable; one human annotator labels a 200-subtask sample, with Cohen's kappa 0.89 agreement against binarized MLLM scores. | The human sample validates description/segment usability, not temporal boundaries or nested-tree gold. No official repository was found in the bounded search. |
| Activity Mining by Global Trace Segmentation | [paper/PDF](https://www.vdaalst.com/publications/p586.pdf), DOI `10.1007/978-3-642-12186-9_13` | Global top-down grouping of low-level event classes into higher-level activities, validated on a real ASML test-process log. | It does not name open-ended agent goals, model nested intentions, or attach LLM-agent outcomes. |
| Agent-as-a-Judge / DevAI | [ICML 2025 paper](https://proceedings.mlr.press/v267/zhuge25a.html), [official repository](https://github.com/metauto-ai/agent-as-a-judge) | 55 realistic AI-development tasks, 365 manually authored hierarchical requirements, runnable benchmark/evaluator, and task-process feedback. | Requirements specify what should be achieved; they are not human temporal assignments of each trajectory action to a requirement. |
| AgenticRAGTracer | [ACL Findings 2026 paper](https://aclanthology.org/2026.findings-acl.66/), [official repository](https://github.com/YqjMartin/AgenticRAGTracer) | 1,305 multi-hop problems with intermediate logical questions and a public evaluation path; accepted precedent for step allocation against task logic. | The trajectories are generated retrieval chains in one domain, not open-ended software/GUI responsibility stacks. |
| CodeTraceBench | [official dataset](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench) | 4,316 coding-agent trajectories; 1,000 verified rows with step-level incorrect/unuseful labels and stage spans used by the current fixed selected workload. | The released stages are flat and unlabeled in the selected manifest; they cannot score nested ancestor meaning or open-vocabulary names. |

Discovery results such as secondary paper summaries were excluded from novelty
and experiment decisions after primary sources were opened.

## Novelty And Baseline Judgment

Same-claim risk for “an LLM can decompose a completed agent trajectory into
subtasks” is **high** because GUIDE implements that mechanism directly. Step
0057's fixed 3B version is also empirically contradicted, so another local
prompt variant would be both weakly differentiated and poorly supported.

The larger defensible opportunity remains the fixed one: a profiler attaches
conserved resources and source-linked effects to task responsibility, preserves
the execution view, and aggregates recurring responsibility across runs. GUIDE
does not study resource conservation or population profiling; process mining
does not study open-ended agent goals; DevAI does not temporally align its task
hierarchy to agent actions.

## Experiment-Asset Handoff

| Candidate role | Asset/protocol | Runnable status | Fair use in the next experiment | Invalid use |
|---|---|---|---|---|
| Direct conceptual baseline | GUIDE full-trajectory action-summary segmentation | Paper protocol verified; no official code found | Cite and reproduce only if a fair comparable backbone and complete workload are available. | Claiming novelty for whole-trajectory LLM segmentation or treating its model-judge usability as human gold. |
| Boundary source | Current complete selected CodeTraceBench workload and fixed recurrence assignments | Already complete | Hold boundaries fixed while testing a distinct labeling responsibility; retain ordinary B-cubed only for the fixed flat partition. | Reusing flat B-cubed as nested hierarchy/name accuracy. |
| Human hierarchy/name source | DevAI hierarchical requirements | Official repository and dataset available | Test whether a semantic profile covers and preserves externally authored task requirements; use published evaluator outputs or standard label matching where available. | Treating requirements as temporal step assignments without an independent mapping. |
| Explicit logical sequence source | AgenticRAGTracer intermediate hops | Official code/data available | Test whether profile order and labels correspond to known logical hops in one accepted domain. | Generalizing retrieval-hop performance to arbitrary agent stacks. |
| Real process precedent | ASML activity-mining case study | Paper and method available | Cite the separation of event segmentation from later process discovery. | Calling activity mining an agent task-semantic baseline without adapting its information assumptions. |

## Decision And Search-Tree Update

No public asset found in the bounded search simultaneously supplies real
open-ended agent trajectories, human temporal task/subtask paths, nested
ancestor labels, and result semantics. That uncertainty is recorded rather
than filled by a custom metric.

The next experiment should test exactly one of two non-equivalent questions:

1. keep the current source-only recurrence partition fixed and test semantic
   labeling against an external label-bearing protocol; or
2. ingest explicit agent-native plan/delegation state as the task stack and
   test source fidelity plus downstream profiling on real sessions.

The first route has the clearest published assets (DevAI or AgenticRAGTracer)
but does not by itself validate arbitrary nested software-agent traces. The
second route is more profiler-like and avoids hallucinating a call stack, but a
public plan-bearing trajectory benchmark remains an open asset question. Final
experiment admission belongs to `research-experiment-design`; this search does
not alter the thesis, RQs, paper, or positive hypotheses.
