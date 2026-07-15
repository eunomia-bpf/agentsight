# Experiment Result: Multi-Step Grammar Recurrence

**Completed:** 2026-07-15T14:46:00-07:00
**RQ:** **RQ3: How accurate are the tags?**
**Run status:** **VALID / COMPLETE**
**Tested-hypothesis verdict:** **CONTRADICTED**
**Paper decision pending:** independent result review

## Tested Hypothesis And Fixed Rule

The approved hypothesis was that the one registered multi-session Re-Pair
adaptation would achieve operation-weighted B-cubed F1 no lower than Step 0024
on both complete existing populations and strictly higher on at least one.

The registered verdict rule was fixed before execution:

- **SUPPORTED:** no lower on both complete populations and strictly higher on
  at least one;
- **MIXED:** higher on one and lower on the other;
- **CONTRADICTED:** every other valid complete relation; and
- **INVALID/INCOMPLETE:** any population, oracle timing, Rust/Python
  equivalence, assignment, or mass failure.

Both complete relations are lower, so the result is **CONTRADICTED**. No fold,
framework, boundary metric, control, or aggregate average may override that
registered two-population rule.

## OSWorld-Human Complete Population

All five established held-out folds completed:

- 287 sessions;
- 3,978 operations;
- 3,691 adjacent decisions;
- 2,042 official human groups;
- 621 learned rules across folds;
- 1,492 predicted groups; and
- 3,978 exact Rust/Python assignments with complete mass conservation.

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 |
|---|---:|---:|---:|---:|---:|---:|
| Grammar candidate | 0.5560 | 0.3818 | 0.452703 | 0.664142 | 0.780897 | 0.717803 |
| Step 0024 | 0.5918 | 0.7989 | 0.679922 | 0.855872 | 0.726966 | 0.786170 |
| Supervised OOF comparator | 0.6998 | 0.7823 | 0.738768 | 0.835863 | 0.797096 | 0.816019 |
| Phase change | 0.4410 | 0.2684 | 0.333688 | 0.565077 | 0.809217 | 0.665461 |
| Action change | 0.3855 | 0.6256 | 0.477080 | 0.818318 | 0.551852 | 0.659174 |
| Always boundary | 0.4755 | 1.0000 | 0.644510 | 1.000000 | 0.513323 | 0.678405 |
| One session block | 0.0000 | 0.0000 | 0.000000 | 0.210250 | 1.000000 | 0.347449 |

The candidate's primary B-cubed delta from Step 0024 is **-0.068367**. It
creates substantially fewer groups (1,492 versus 2,656), increasing B-cubed
recall but losing much more precision. This is consistent with over-merging
repeated action motifs; it is a result interpretation, not authorization for a
second grammar variant or a target-driven threshold.

## CodeTraceBench Complete Population

The complete existing transfer completed:

- 2,229 target-disjoint reference sessions / 87,703 reference operations;
- 405 target sessions / 20,866 target operations;
- 20,461 adjacent decisions;
- 2,948 complete official stages across four frameworks;
- 2,453 learned rules with maximum rule depth 8;
- 5,187 predicted groups; and
- exact Rust/Python ordered rules, segments, all assignments, and mass.

| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed precision | B-cubed recall | B-cubed F1 |
|---|---:|---:|---:|---:|---:|---:|
| Grammar candidate | 0.195734 | 0.368069 | 0.255563 | 0.839528 | 0.509224 | 0.633931 |
| Step 0024 | 0.199784 | 0.510028 | 0.287106 | 0.828579 | 0.533630 | 0.649173 |
| Phase change | 0.164126 | 0.359811 | 0.225425 | 0.685564 | 0.626030 | 0.654445 |
| Action change | 0.160897 | 0.793158 | 0.267524 | 0.947623 | 0.315368 | 0.473242 |
| Always boundary | 0.124285 | 1.000000 | 0.221092 | 1.000000 | 0.141282 | 0.247585 |
| One session block | 0.000000 | 0.000000 | 0.000000 | 0.173563 | 1.000000 | 0.295788 |

The candidate's primary B-cubed delta from Step 0024 is **-0.015242**. The
per-framework candidate-versus-Step-0024 B-cubed F1 values are:

| Framework | Grammar | Step 0024 |
|---|---:|---:|
| OpenHands | 0.646800 | 0.661593 |
| SWE-agent | 0.647293 | 0.707955 |
| Terminus2 | 0.597383 | 0.593876 |
| mini-SWE-agent | 0.674729 | 0.683439 |

One framework improvement cannot override the lower complete-population
result. Phase change also remains the strongest simple complete-population
CodeTrace comparator at 0.654445.

## Validity And Completeness

- Both REAL PREFLIGHT paths passed on their first attempt.
- Candidate construction consumed only persisted `session`/`action` inputs.
- Python segments and per-operation assignments were persisted before scorer
  labels/stages were loaded.
- The scorer populations exactly matched the persisted visible populations.
- Retained Step 0024 summaries were bound by exact path, schema, mode, policy,
  populations, validity, and raw artifacts.
- Recomputed controls exactly matched retained Step 0024 controls globally and
  per framework where registered.
- Standalone OSWorld equivalence verified all five folds, 621 rules, 1,492
  segments, and all 3,978 assignments.
- CodeTrace verified the complete ordered grammar and every one of 20,866
  assignments before interpretation.
- No operation or additive weight was lost or duplicated.
- No cap, parameter sweep, target retry, second grammar candidate, new
  benchmark, RQ change, or story change occurred.

The raw results are:

- `.agentsight/experiments/rq3-grammar-recurrence-v1/full/`;
- `.agentsight/experiments/rq3-grammar-recurrence-codetracebench-v1/full/`; and
- `.agentsight/experiments/rq3-grammar-recurrence-rust-equivalence-v1/full/`.

## Registered Disposition

Subject to independent reconstruction, the approved plan requires restoring
Step 0024 exactly and retaining this complete result only as internal mechanism
evidence. It does not authorize narrowing RQ3, changing the thesis, rewriting
the original AgentProf story, adding negative results to the paper, or tuning a
second grammar candidate on these outcomes. The paper and read-only submodule
remain unchanged at this point.
