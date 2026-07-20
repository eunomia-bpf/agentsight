# Experiment 003 Plan Review 1

**Reviewer:** Grok 4.5, read-only senior AI/agent-systems review  
**Verdict:** **APPROVE**  
**Must-fix:** None

The reviewer read the complete paper scientific body and RQ3 construct,
complete idea story, Experiment 001's plan/full-run/result review, all
Experiment 002 plan/preflight/full-run records, and the Experiment 003 plan.
It made no edits and introduced no new RQ or story.

## Single-Frame Transition

The reviewer found that V1 failed because arbitrary `append[]` let a 3B model
invent an unbounded same-step frame list, not because variable total depth was
wrong. The V2 rule

```text
S_t = prefix(S_(t-1), keep_depth) + at most one new frame
```

is the minimal causal repair. It retains stay, one-level push, arbitrary
multi-pop, sibling replacement, and unbounded total depth across operations.
One observed operation can evidence at most one newly active goal, whereas the
same evidence may reveal completion of several ancestors. Fixed depth,
max-N lists, retry, clamp, or truncation would be less simple or less causal.
Fresh V2 caches correctly treat it as a new experiment.

## Scientific Contract

The exact thesis and four RQs remain unchanged. The model sees only root task,
current stack, preceding observation, and current action. Stages, future
operations, resource weights, and scores remain hidden until a separate scorer
runs after complete predictions. Leaf instances are evaluated against flat
human stages; literal open-vocabulary names and full nested-tree accuracy are
not claimed. The richer-text system comparison is explicitly not matched-
input algorithmic superiority or proof that the stack alone causes gains.

Ordinary unweighted per-operation B-cubed is an appropriate primary metric;
exact adjacent boundary F1 is an appropriate secondary metric. The completed
multi-resolution recurrence, released recurrence, source phase, and raw action
are sufficient baselines. The task-cluster bootstrap and predeclared adoption
branches are sufficient.

## Authorization And Optional Notes

Implementation and REAL PREFLIGHT are scientifically authorized. Preflight may
repair enforcement bugs but may not tune semantics from stages or scores.

The reviewer listed a flat same-model control, non-contiguous-leaf diagnostic,
and explicit grammar/cache keys as optional—not conditions of validity. It
explicitly rejected adding another RQ, custom semantic judge, second benchmark,
or mandatory baseline arm.
