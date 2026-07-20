# Literature Search And Experiment Handoff — Incremental Semantic Task Stacks

**Searched:** 2026-07-19T20:42:17-07:00  
**Paper RQ:** RQ3 — How accurate are the tags?  
**Scope:** determine whether an LLM-maintained variable-depth semantic task
stack is a principled replacement candidate for action-transition recurrence;
do not change the thesis, four RQs, original AgentProf story, or two-object
model.

## Claim Questions

The search stripped away the AgentProf name and tested three plain claims:

1. Can a sequence of language and actions be incrementally represented by a
   stack of active intentions, with new subordinate purposes pushed and
   completed or abandoned purposes popped?
2. Is hierarchical abstraction of low-level events into higher-level activity
   instances already established?
3. Is a small local instruction model a credible fixed structured-output
   backend for one transition decision at a time?

The candidate paper claim is deliberately narrower than any answer to these
three generic questions: a local model can construct useful semantic
responsibility stacks from real agent histories, and the resulting stacks can
carry conserved profiling measures across runs.

## Search Log

| Query/source | Purpose | Verified result |
|---|---|---|
| `hierarchical task segmentation benchmark agent trajectories LLM` | Find direct agent-stack benchmarks and same-claim work | No verified work found that combines incremental semantic task-stack induction with conserved cross-run agent profiles. CodeTracer is the closest released agent-stage source. |
| `plan recognition hierarchical task decomposition benchmark` | Find hierarchy/goal-recognition precedent | Blaylock and Allen, AAAI 2006, recognize simultaneous goals at multiple levels of a hierarchical plan; generic hierarchical goal recognition is not novel. |
| `hierarchical event abstraction activity instance ICPM 2021` | Find event-abstraction precedent | Li, van Zelst, and van der Aalst, ICPM 2021, formalize hierarchical abstraction over activity instances; generic hierarchical event abstraction is not novel. |
| `focus stack task-oriented dialogue push pop` | Find the closest conceptual mechanism | Grosz and Sidner, Computational Linguistics 1986, model dynamic attentional state as a stack of focus spaces associated with discourse-segment purposes. A subordinate purpose pushes; returning to a dominating purpose can pop multiple spaces. The intentional structure is open-ended and evolves during discourse. |
| `Qwen2.5 3B Instruct structured output model card` | Verify the proposed local backend | The official Qwen model card identifies Qwen2.5-3B-Instruct as a 3.09B instruction model and explicitly calls out improved structured/JSON output. It documents llama.cpp-compatible quantizations. |
| CodeTracer / CodeTraceBench official paper and local artifact | Verify the real experiment source | CodeTracer releases trajectories from four coding-agent frameworks with human-verified stage supervision. The local complete source-valid target already contains 405 trajectories, 20,866 operations, and 2,948 stages. |

## Primary Sources Opened

- Barbara J. Grosz and Candace L. Sidner, “Attention, Intentions, and the
  Structure of Discourse,” *Computational Linguistics* 12(3), 1986,
  <https://aclanthology.org/J86-3001/>. The authoritative PDF states that the
  focusing structure is a stack, that its spaces include discourse-segment
  purposes, that a subordinate purpose pushes, and that returning higher in
  the dominance hierarchy pops one or more spaces.
- Nate Blaylock and James Allen, “Fast Hierarchical Goal Schema Recognition,”
  AAAI 2006, <https://cdn.aaai.org/AAAI/2006/AAAI06-126.pdf>.
- Chia-Yen Li, Sebastiaan J. van Zelst, and Wil M. P. van der Aalst, “An
  Activity Instance Based Hierarchical Framework for Event Abstraction,” ICPM
  2021, DOI `10.1109/ICPM53251.2021.9576868`.
- Han Li et al., “CodeTracer: Towards Traceable Agent States,” arXiv:2604.11641
  v3, <https://arxiv.org/abs/2604.11641>.
- Qwen Team, Qwen2.5-3B-Instruct official model card,
  <https://huggingface.co/Qwen/Qwen2.5-3B-Instruct>.

## Novelty And Mechanism Judgment

The user's proposal is more principled than the current recurrence constructor.
It does not invent a new mathematical stack idea: dynamic intention/focus
stacks have strong prior precedent. That precedent is an advantage because it
replaces NPMI, two calibrations, transition-frequency assumptions, and motif
construction with one established semantic invariant:

> Preserve the active prefix whose purposes still contain the current work,
> remove purposes that no longer contain it, and append newly active
> subordinate purposes.

The name-free novelty opportunity is the combination, not the data structure:
construct that semantic responsibility stack from heterogeneous agent history
with a small local model, attach every weighted operation and downstream effect
to the active path, and fold recurring paths into conventional profiles. Same-
claim risk is **medium**: discourse and plan recognition establish the stack;
event abstraction establishes hierarchy; current agent tools establish
semantic trace grouping. No verified closest work in this search establishes
the complete agent-profiling conjunction.

## Baseline And Evaluation Handoff

The complete existing CodeTraceBench run is the best immediate real experiment.
Its raw public archives contain the actual agent actions and observations, and
its official stage intervals are independently annotated. No new trajectories,
hand labels, or toy harness are needed.

Required comparisons are the current released recurrence, the completed
multi-resolution recurrence candidate, the official-source phase grouping, and
raw-action grouping. Ordinary per-operation B-cubed remains the primary
standard partition metric; exact boundary F1 remains secondary. The candidate
must be fixed before official stages are loaded.

The experiment can validate leaf-instance partition fidelity and variable-
depth behavior, but CodeTraceBench does not provide gold open-vocabulary frame
names or a gold nested hierarchy below `task -> stage`. Therefore this one run
cannot claim literal semantic-name accuracy or complete hierarchical fidelity.
Those are residual uncertainties, not reasons to reduce the paper's RQ3.

## Search-Tree Update

The mechanism branch changes from “find a better transition statistic” to
“infer the currently active semantic intention path.” Further NPMI thresholds,
fields, windows, or recurrence variants are not admitted before this candidate
is completely tested. The next node is the reviewed experiment plan in
`experiment-002/experiment-plan.md`.

