# Full Run — Variable-Depth Semantic Task Stack V1

**Stopped:** 2026-07-19T21:35:05-07:00  
**State:** Invalid/incomplete; not scored and not eligible for paper adoption  
**RQ:** RQ3 — tag accuracy

## Executed Scope

The approved Qwen 2.5 3B inference process started all 405 public
CodeTraceBench trajectories with eight trajectories concurrent and each
trajectory sequential. Before shutdown it retained 18,776 valid transitions
across 404 session caches. Of those caches, 341 trajectories were complete and
63 were partial; one trajectory failed before writing a first valid
transition. No official stage manifest, stage interval, B-cubed score, or
boundary score was opened.

All retained responses use the fixed model SHA, prompt, visible evidence,
temperature, seed, transition rule, and `direct-gbnf-v1` output contract. They
remain under
`.agentsight/experiments/rq3-qwen3b-semantic-task-stack-v1/full/inference/`
as evidence of the failed candidate and will not be reused by another
transition contract.

## Failure

V1 allowed `append` to contain zero or more new frames in one transition. The
direct grammar correctly bounded each label to 48 characters, but the approved
contract did not bound the number of array elements. Qwen repeated
`"implement eigenvectors from eigenvalues research"` as successive frames
until the fixed 128-token response budget ended before the JSON array closed.
The independent parser therefore rejected the truncated response and the run
became incomplete exactly as the plan required. There was no retry, completion,
clamp, fallback, or inferred default.

The executor waited for already submitted worker tasks during shutdown, which
is why other session caches continued to make progress after the first failed
future. Their presence does not turn this into a complete run, and no partial
population score is allowed.

## Source-Visible Diagnostic

Before failure, the candidate frequently used multiple appended frames to
encode action fragments rather than nested, temporally extended goals. One
observed 25-deep stack included labels such as `find files`, `test`, `run`,
`cd`, function names, and argument values. Across an earlier 6,205-operation
snapshot, every operation created a new leaf through push or suffix
replacement. These are source-visible transition diagnostics, not target-label
or score feedback.

The failure does not show that variable depth is wrong. It shows that allowing
a small model to invent an arbitrary number of levels from one operation is
both unnecessarily complex and causally weak: one new operation supplies
evidence for at most one newly active semantic goal, while returning to an
ancestor may still pop several completed goals.

## Decision

Experiment 002 is classified **invalid/incomplete** and will not be scored,
implemented in the release path, or written as positive evidence. The exact
paper thesis and four RQs remain unchanged. A new experiment may test the
simpler online transition

```text
S_t = prefix(S_(t-1), keep_depth) + optional_new_frame
```

where `optional_new_frame` is either one semantic frame or none. This retains
unbounded total variable depth across time, arbitrary multi-pop, stay, push,
and sibling replacement, while eliminating unprincipled same-step frame-list
generation. Because that is an algorithm change, it requires a new plan,
fresh empty caches, and independent review rather than a silent V1 repair.
