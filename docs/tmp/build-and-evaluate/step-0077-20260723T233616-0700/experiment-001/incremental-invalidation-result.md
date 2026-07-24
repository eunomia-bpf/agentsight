# Incremental invalidation result on AgentReward

Timestamp: 2026-07-24T07:12:00-07:00
Status: complete outcome-blind terminal result

## Result

Stable diagnostic identities plus local invalidation terminate where repeated
fresh full review did not.  The final implementation hashes the review item's
semantic parent, range metadata, and a deterministic digest of the bounded
source interval.  Unchanged source intervals are not serialized repeatedly;
canonical node digests and composable range hashes keep diagnosis linear in
the trace plus emitted diagnostics.

Comparing full-review iteration 006 with iteration 007 invalidated:

- 5 of 266 hierarchy issues;
- 11 of 481 retained tag-reuse rows; and
- 0 of 14 retained near-name candidates.

The other 261 hierarchy, 470 tag-reuse, and 14 near-name decisions remained
valid.  Eight tag names disappeared after normalization and therefore needed
no decision in the new state.

Two incremental backend calls reviewed all 16 invalidated rows.  Every decision
was `keep`, supported by the supplied source context; neither call changed
`annotation.json`.  A final regeneration therefore had no invalidated item
left and reproduced the same state:

| Quantity | Terminal value |
|---|---:|
| Sessions | 440 |
| Source nodes | 15,338 |
| Source operations | 7,229 |
| Profiled trace tokens | 51,904,621 |
| Annotations | 2,228 |
| Optional tag names | 481 |
| Cross-session tag names | 289 |
| Singleton tag names | 192 |
| Hierarchy diagnostics | 266 |
| Near-name candidates | 14 |
| Unique operation stacks | 6,985 |
| Unique token stacks | 6,938 |
| Semantic depth | 2--4 |

All source operation and token mass is conserved.  Operation and token profiles
regenerate in 0.27 seconds each with approximately 100 MiB peak RSS.

## Incremental review cost

The two packets contained 634 source-node presentations and 482 unique source
nodes, 3.14% of the complete trace.  The first call reviewed five hierarchy
and eight naming rows; the second reviewed three additional naming rows exposed
when the code-review fix made range invalidation complete.

| Quantity | Incremental total |
|---|---:|
| Backend calls | 2 |
| End-to-end elapsed | 387.202 s (6.45 min) |
| Provider input tokens | 3,691,400 |
| Provider cached input tokens | 3,463,424 |
| Derived uncached input tokens | 227,976 |
| Provider output tokens | 14,859 |
| Reasoning output tokens | 4,879 |
| Exact packet logical input tokens | 259,167 |
| Markdown decision-report logical tokens | 1,616 |

Relative to full-review iteration 007, incremental review reduced elapsed time
by 83.3%, provider input by 84.4%, and packet logical input by 93.9%.  These are
same-population, same-model comparisons.  They do not imply that 3.69 million
provider input tokens is cheap; provider totals still include repeated
orchestration and growing cached context.  RQ4 must report this remaining cost
and compare it with direct trace reading and query amortization.

## Scientific interpretation

The result rejects the initial assumption that repeatedly assigning every
warning to a fresh reviewer is a convergence algorithm.  That policy consumed
seven complete revision passes and still changed the annotation.  Stable
source-grounded decisions plus local invalidation supply the missing state:
unchanged accepted contexts remain accepted, while any changed parent, range,
name occurrence, or source evidence reopens only the affected question.

This experiment establishes mechanism termination and a large cost reduction
on the complete AgentReward population.  It does **not** establish improved
boundary accuracy or case-study answerability.  Those outcomes require the
predeclared masked case comparison and standard RQ3 scoring after the terminal
annotation is frozen.

No success/failure label, pair side, reward, prior signed profile, expected
case answer, or human stage was visible before this terminal state.

## Verification

- Full `agentpprof` test suite: 88 tests passed across unit and CLI suites.
- Independent focused code review: PASS after two must-fix invalidation
  findings were corrected.
- Product format remains `.pb`/`.pb.gz`; no frontend, new required workspace
  file, Git binding, seal, or attestation was added.
