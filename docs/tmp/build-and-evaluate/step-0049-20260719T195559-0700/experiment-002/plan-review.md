# Independent Pre-Implementation Plan Review — Experiment 002

**Reviewer:** Grok 4.5, read-only senior review across AI/ML, agent systems,
profiling, discourse/plan recognition, and empirical methodology  
**Reviewed:** 2026-07-19  
**Mode:** complete paper and plan read; no file edits, model run,
implementation, or unseen target-label inspection

## Verdict: REVISE

The scientific direction is sound and paper-aligned. Three small but
load-bearing algorithm contracts are under-specified, so two faithful
implementers could produce different backends and scores. Repair only those
contracts, then implementation and REAL PREFLIGHT may begin. No additional
baseline, metric, RQ, story change, toy data, or unrelated benchmark is a
condition of approval.

## Scientific Judgment

The variable-depth semantic task stack is simpler and more aligned with the
AgentProf model than recurrence. Recurrence first produces contiguous flat
segments from action-transition NPMI, two calibrations, a cross-action rule,
and optionally a second resolution; only then does AgentProf make a frame.
The proposed backend directly maintains the object the paper needs: a semantic
operation stack. Its one invariant is to retain the purpose prefix that still
contains current work, remove completed purposes, and append newly active
subordinate purposes. Grosz and Sidner supply the conceptual push/pop
precedent, so the paper need not invent terminology or claim the stack itself.

Experiment 001's multi-resolution recurrence is a real supported improvement
on the same CodeTrace population. It appropriately raises the comparison bar:
the semantic stack must beat that candidate rather than only the released
coarse recurrence.

## Contract Review

### Transition completeness

`keep_depth + append[]` covers every required transition:

| Intent | Transition |
|---|---|
| Stay | retain all, append nothing |
| Push | retain all, append one or more frames |
| Multi-pop | retain a shorter prefix, append nothing |
| Sibling/branch replacement | retain the parent prefix, append a new suffix |
| Variable depth | stack length changes only through the same rule; no depth cap |

Retained labels should not be copied by the model. The transition function
itself retains prior labels and frame-instance identities; the model proposes
only the appended suffix.

### Causal evidence

Current action plus the preceding observation is the correct causal window for
assigning the current operation. The current operation's result is future
evidence and must remain excluded. Human stages may occasionally reflect an
outcome visible only later; that can make the task harder but does not create
circularity.

### Partition scoring

Open-vocabulary labels do not make B-cubed ambiguous. Every append creates a
fresh within-trajectory frame-instance ID, and each operation's predicted
cluster is its active leaf instance. Re-pushing the same phrase after a pop is
a new instance. Ordinary B-cubed then compares predicted and official
partitions over the same operations without using label-string equality.

A returned ancestor may make one predicted leaf instance non-contiguous while
official stages are contiguous. B-cubed remains defined. The result cannot be
claimed as gold nested-hierarchy or literal semantic-name accuracy.

### Comparison and ablation

Richer task, action, and preceding-observation text does not invalidate the
comparison; it makes it a system-level backend comparison rather than a
matched-action-only algorithm comparison. A same-Qwen flat or forced-depth
control would distinguish stack discipline from language understanding, but it
is optional mechanism analysis and not required to decide the registered
end-to-end hypothesis or release constructor.

The comparison set and adoption rule are strong: candidate, multi-resolution
recurrence, released recurrence, phase, and raw action; candidate must beat all
of them with a wholly positive task-cluster interval against the strongest and
non-negative effects in all four frameworks.

### Full-run feasibility

The complete 405-trajectory, 20,866-operation execution is feasible with the
pinned Qwen2.5-3B Q4_K_M model, llama.cpp, the available 32-GiB RTX 5090,
trajectory-level concurrency, and retained-response resumption. One complete
run after adapter preflight is appropriate; a few-session smoke result cannot
substitute for it.

## Must-Fix Issues

### MF-1 — Complete state and validity predicate

State explicitly:

```text
S_0 = []
keep_depth is an integer in 0..|S_(t-1)|
every appended label is a non-empty lowercase short verb phrase
S_t = prefix(S_(t-1), keep_depth) + fresh instances for append[]
|S_t| >= 1
operation t receives the leaf instance of S_t
any violation makes the run incomplete; there is no repair/default transition
```

### MF-2 — Freeze evidence ordering and concrete truncation budgets

The plan says truncation is fixed before preflight but does not state its
values. Specify root-task, current-action, preceding-observation, and stack
serialization ordering and budgets, plus deterministic truncation behavior.

### MF-3 — State the system-comparison claim boundary

State next to the hypothesis that the candidate uses richer visible language
than recurrence. A supported result authorizes adoption of the complete backend
on this population, not matched-input action-only superiority, gold nested
hierarchy, literal frame-name accuracy, or proof that stack discipline alone
caused the gain. Include raw action in the hypothesis if adoption requires
beating every listed comparison.

## Optional, Not Required

- same-model flat/depth-one ablation;
- non-contiguous predicted-leaf rate as a diagnostic;
- dynamic JSON-schema upper bound for `keep_depth`;
- an OSWorld arm in a separate admitted experiment.

None is required for approval of this plan.

## Authorization

Implementation and REAL PREFLIGHT may not begin until MF-1, MF-2, and MF-3 are
written into the plan. After those textual repairs, implementation and REAL
PREFLIGHT may begin under the existing one-hypothesis, complete-population,
stage-hidden, standard-metric contract.

