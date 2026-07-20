# Experiment Plan: RQ3 Causal Exact Task-Identity Invariant

## Research Question

- RQ exactly as written in the paper: **RQ3 — How accurate are the tags?**
- Specific uncertainty: whether enforcing exact identity continuity for a
  continuing active task causally removes enough duplicate nesting to make the
  source-native online task-stack constructor exceed the current recurrence
  constructor.
- Why it matters: the task-semantic profile should represent a continuing
  concrete goal once, even when a small local controller proposes a fresh frame
  with exactly the same visible goal label.

## Paper-Value Admission And Stop Rule

- Planned role: final causal mechanism experiment in the online Qwen2.5-3B
  task-stack branch.
- One tested hypothesis: applying an exact same-leaf `push` or `replace` as
  identity-preserving `stay` improves exact visible-path stage fidelity enough
  to clear the existing recurrence adoption comparison.
- Why it is not the Step 0055 contraction diagnostic: changing the applied
  stack changes the full context presented to every later model turn. Post-hoc
  path contraction cannot reconstruct those causal decisions.
- Positive decision: adopt this online constructor only if exact-visible-path
  B-cubed F1 exceeds recurrence and the paired task-cluster 95% interval is
  wholly above zero.
- Negative or inconclusive decision: close this online Qwen2.5-3B branch. Do not
  tune another prompt, equality rule, threshold, model, field, phase filter,
  depth policy, contraction, or benchmark variant. Return to a non-equivalent
  globally contextual task-structure mechanism without changing the thesis,
  RQs, positive RQ3 hypothesis, or target hierarchy.

## Sole Intervention

For each source-native turn, the unchanged model returns one transition under
the unchanged Step 0054 grammar. Let the active visible leaf be the exact label
of the current subtask frame, or the immutable concrete-task root when no
subtask exists.

```text
if proposal.kind in {push, replace}
and proposal.label == active_leaf.label byte-for-byte:
    applied_transition = stay
else:
    applied_transition = proposal
```

The original proposal and applied transition are both recorded. For an
invariant application, no frame is created, no ancestor is removed, and the
next frame counter is unchanged. Every other transition retains the Step 0054
semantics exactly. Equality is case-sensitive and byte-exact; there is no
canonicalization, edit distance, embedding, stemming, ancestor search, or
phase/status interpretation.

## Fixed Inputs, Model, And Output Identity

- same complete CodeTraceBench source-valid population: 405 trajectories,
  17,148 source-native turns, 20,866 operations, 251 task clusters, and 2,948
  verified session-local stage occurrences;
- same public source archives and source-native intent/progress/action/result
  reconstruction;
- same immutable root, complete active label stack, one transition per native
  turn, no depth cap, and no stack truncation;
- same Qwen2.5-3B-Instruct Q4_K_M model, llama.cpp endpoint, system prompt,
  grammar, seed, temperature, output budget, and evidence clipping;
- human stage, recurrence assignment, current result, phase/action-kind,
  agent/model/session/status remain absent from inference; and
- primary candidate identity is the exact complete ordered visible task-label
  path established by Step 0055. Hidden instance identity and adjacent
  contraction are behavior diagnostics only.

## Exact-Request Reuse

Step 0054 raw responses may be reused only while the complete request hash at
the same turn—including model, prompt, active visible stack, grammar, seed, and
settings—matches exactly. The response at the first invariant application may
be reused because its request precedes the changed state. After applying that
intervention, every later turn in the session is newly inferred; no suffix is
borrowed from a non-identical context. Sessions whose complete sequence never
triggers the invariant may reuse all exact responses.

Each cache records whether a proposal came from exact-request reuse or a new
model call. This is ordinary deterministic compute reuse, not a score condition
or a second algorithm.

## Comparisons And Metrics

- Primary incumbent: fixed multi-resolution recurrence on the same operations.
- Causal baseline: Step 0055 exact visible paths from the unmodified online
  policy, which isolates the invariant's effect.
- Primary standard metric: ordinary operation-level B-cubed precision, recall,
  and F1 against session-local verified workflow-stage occurrences.
- Primary adoption uncertainty: paired 10,000-resample task-cluster bootstrap
  for causal candidate minus recurrence B-cubed F1.
- Causal mechanism effect: a second paired bootstrap for causal candidate minus
  Step 0055 exact visible path.
- Standard secondary diagnostics: adjacent-boundary and exact-span F1.
- Per-framework deltas, proposed/applied transition counts, invariant
  applications, depth, pop frequency, new-frame rate, exact phase-like labels,
  model-call/reuse counts, and global path recurrence are diagnostics, not
  additional adoption gates.

Session namespaces the occurrence-level accuracy score but never enters the
semantic path. Global identical-path counts are profile behavior only and do
not validate cross-run semantic equality.

## Planned Runs

| Run | Population | Purpose |
|---|---|---|
| real preflight | one complete invariant-triggering trajectory per source layout | validate exact-request prefix reuse, first intervention, new suffix inference, complete assignment, and scorer |
| full causal replay | all 405 trajectories and 17,148 turns | primary constructor decision |
| standard score | all 20,866 operations | exact-visible-path comparison and uncertainty |

The preflight may reveal scientific behavior but cannot tune the intervention,
prompt, or model. The full run must complete every trajectory; no smoke result
or favorable framework slice can stop execution.

## Execution And Artifacts

- Implement a thin causal evaluator by reusing the Step 0054 source adapters,
  prompt, grammar, parsers, and standard scorers. Do not modify the Step 0054
  evaluator or its artifacts.
- Preflight and full outputs:
  `.agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/`.
- Full completion requires one valid proposal and applied transition per turn,
  every operation exactly once, exact request-source provenance, standard
  metrics and both paired intervals, complete behavior diagnostics, and an
  independent raw result review.

## Interpretation Boundary

The experiment tests only one fixed online transition policy and the flat exact
visible-path partition. A positive result would not validate ancestor topology,
arbitrary-depth meaning, generated label semantics, root canonicalization,
cross-run equivalence, or the lower phase/action/object/result suffix. A
negative result closes this algorithm branch, not the task-semantic hierarchy,
thesis, RQ3, or its positive paper hypothesis.
