# Main-Agent refinement of automatic operation marks

Timestamp: 2026-07-22T18:10:00-07:00

## Question

Can a root Agent improve the complete 405-session automatic-backend result by
reading source-only trajectories and revising semantic boundaries, without
using official stage labels to make those decisions?

## Variants

- **A0** is the independently reviewed automatic-Agent result: 5,901 marks.
- **A2 root repair** applies one deterministic representation correction. If a
  session begins with a one-turn task-root-only mark and the next mark extends
  that same root with the first responsibility, the first source turn receives
  the complete `task -> responsibility` path and the artificial root-only leaf
  is removed. This decision uses annotation shape and source-turn order only.
- **A3 main-Agent pass** adds source-only semantic revisions for four complete
  long sessions: one Git deployment, password reverse engineering, MuJoCo
  tuning, and HTML-filter bypass. The decisions are stored verbatim in
  `.agentsight/experiments/main-agent-refine-v1/git-multibranch.annotation.json`.

The official CodeTrace stages were opened only by the existing scorer after
each prediction file was materialized.

## Complete-population results

| Variant | Marks | B³ P | B³ R | B³ F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| A0 automatic Agent | 5,901 | .841742 | .599076 | .699974 | .389103 |
| A2 root repair | 5,752 | .839025 | .606577 | **.704113** | **.393916** |
| A3 root repair + four main-Agent revisions | 5,735 | .834918 | .608582 | .704006 | .394005 |

A2 improves B³ F1 by .00414 and boundary F1 by .00481 over A0 while removing
149 artificial root-only leaves. Its task-clustered A2-minus-recurrence B³
delta is .04111 with a 10,000-resample 95% interval [.02137, .06060].

The four manual revisions do not materially improve B³ beyond A2. They make
product questions clearer—for example, the Git case treats alternate ports,
key authentication, forwarding attempts, and repeated clone checks as evidence
inside one sustained SSH-diagnosis responsibility—but that broader product
responsibility is not identical to the benchmark's finer flat stages.

## Decision

Adopt A2. It corrects a representation error with a simple, source-only rule
and improves both standard metrics. Do not adopt A3 as the primary scored
constructor, and do not select individual manual overrides after reading their
score. Keep the manual annotations as an auditable automatic-backend attempt
and as product-case evidence.

This experiment also establishes that “merge more boundaries” is not a general
route to a large score increase. Further progress requires a stronger semantic
transition decision, not a global contraction rate or benchmark-specific
cutoff.

## A2 fixed-input construction cost

The release binary replayed the fixed 20,866-operation A2 inputs three times
per width. Operation-count construction took 0.61/0.63/0.61 seconds (median
0.61) with maximum RSS 316,272 KiB. Token construction took 0.60/0.61/0.62
seconds (median 0.61) with maximum RSS 316,248 KiB. Stock pprof reports exact
masses of 20,866 operations and 494,862,929 tokens. This measures parsing,
mark replay, folding, and serialization after annotations are fixed; it does
not measure Agent inference.
