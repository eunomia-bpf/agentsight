# R337 Reuse-Audit Loop Completion

## Node metadata

- **Completed:** `2026-07-14T11:13:46-07:00`
- **RQ:** Does Profiler Output Correspond to Real Problems?
- **Revision used:** 1 of at most 2
- **Run status:** VALID
- **Tested hypothesis:** SUPPORTED
- **Independent result review:** PASS, zero must-fix
- **Next outer state:** WRITE_GATE

## Completed evidence

The loop reused the existing R333/R337 implementation and all four public
operation sources. It added no new script, dataset, benchmark, model, label,
metric, cutoff, partition, resample, policy, or human dependency. A real R337
preflight passed, the full R333 source replay completed all six tasks, and the
full R337 fixed-target replay completed all six policies and targets.

Every emitted R333 and R337 scientific CSV was byte-identical to the existing
result. Independent review directly recomputed the six task slices from the
operation sources, obtaining four datasets, 34,539 task-operation instances,
and 3,699 positives, and confirmed that visible rank fields are not derived
from the target oracle.

At the existing 25%-recall point, operation stacks reach 6/6 tasks at median
work 0.2000 and median 16 inspected groups, versus fixed-session's 0.2495 and
50. Per-task work outcomes are 4/1/1 and group outcomes are 5/0/1. Flat costs
full work; raw action is a mixed and sometimes stronger counterpoint. The
supported conclusion is therefore a recurring-versus-session compactness
operating point, not universal semantic dominance.

## Authorized paper effect

WRITE may add one compact secondary RQ2 statement containing the six-task
scope, existing 25% target, fixed-session comparison, and raw/flat
counterpoints. It may use the result to explain why a recurring responsibility
view differs from per-session fragmentation. It may not introduce a new
thesis, RQ, story, Pareto/matched-granularity claim, universal superiority,
human utility, automatic diagnosis, or intervention result.

The experiment itself did not edit the paper, idea story, user instructions,
shared skills, or canonical submodule.
