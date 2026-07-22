# Independent plan review

## Round 1 — REVISE

The reviewer used `research-experiment-design` and accepted the core recursive
STOP/SPLIT mechanism, strict interval shrinkage, absence of numerical/depth/
leaf/minimum-length caps, complete real workload, retained comparisons, fixed
thesis, and fixed RQ.

Four must-fix contract gaps were identified:

1. semantic usefulness depended on an unfixed post-hoc review;
2. root naming ambiguously referenced a source-path identity while official
   task clusters were meant to remain hidden;
3. invalid/out-of-interval decisions, timeout, and context overflow had no
   explicit terminal policy; and
4. the B-cubed candidate cluster key was not mechanically specified.

The plan now fixes two multi-session collections and four pprof questions,
defines semantic failure, limits all model-visible task text and the shared pool
to the raw first user request plus target-blind visible turns, fails closed on
all invalid/runtime/context cases without silent STOP or truncation, and defines
the predicted B-cubed key as the complete visible operation-ID path scoped to a
trajectory under Bagga--Baldwin B-cubed.

## Round 2 — REVISE

Round 2 confirmed that the fixed collections/questions, target-blind name pool,
fixed source projection, no dynamic truncation, runtime fail-closed behavior,
complete visible-path B-cubed key, workload, metrics, and thesis/RQ boundaries
resolved Round 1.

Two inconsistencies remained. Child-name collisions were described both as a
silent STOP and as an inference error, and the semantic review required every
individual split to receive zero objections. The plan now makes only an
explicit model STOP terminal; every invalid SPLIT fails closed and emits no
marks. Reviewers record local semantic errors, while collection usefulness
fails only for whole-session/turn-singleton degeneration, irreversible source
lineage, or inability to answer a fixed user question. No error-ratio threshold
was added.

## Round 3 — PASS

The reviewer found the Round 2 contradictions resolved and no remaining
must-fix. The plan is simple, executable, target-blind, fail-closed, complete at
the real-workload level, and aligned with the requested recursive STOP/SPLIT
mechanism without a hidden numerical, depth, leaf-count, or interval-length
limit.

## Round 4 — REVISE after case-study correction

After the user required every paper case to aggregate many sessions, the plan
replaced the four-session and three-session case candidates with the complete
405-session collection and a source-visible longest-decile collection of 41
sessions. The reviewer accepted the leakage-free membership rule and the use
of stock pprof, but identified two scope inconsistencies. Requiring review of
every recursive split over all 405 sessions was not executable, and the text
simultaneously required two collection profiles and one output artifact while
unconditionally requiring a paper figure even for a contradicted backend.

The plan now reviews every source drilldown actually reported by four fixed
aggregate queries without claiming an exhaustive semantic error rate. It also
specifies two ordinary AgentPProf invocations, each producing one `.pb.gz`, and
requires paper inclusion only for a result that passes the registered
scientific and collection-level semantic interpretation.

## Round 5 — PASS

The reviewer found both Round 4 issues resolved. The complete and long-horizon
collections are fixed before inference from source-visible counts, the retained
AgentReward differential is reuse rather than a second experiment, and the
bounded stock-pprof review can support case-study utility without replacing
the standard metric or claiming general user productivity.

## Round 6 — REVISE after real source-only preflight

Before any manifest, stage, or score was opened, the real mini-SWE-agent
preflight showed that a binary split naturally used the current root operation
for one side and a new subtask for the other. Strengthening wording did not
change this behavior. Rejecting it forced the backend either to fail or invent
a synonym for continuing the current responsibility.

The root proposed a current-continuation exception: equality with the current
operation recursively shrinks the interval without pushing a duplicate frame;
a new child pushes a real frame; left and right remain distinct; equality with
an earlier ancestor remains invalid.

## Round 7 — PASS

The reviewer found this revision principled and minimal. It preserves one real
boundary per SPLIT, strict interval shrinkage, explicit STOP, complete visible-
path B-cubed, boundary F1, stable-ID marks, and pprof folding. It also encodes
`current -> child -> current` without a repeated frame and lets noncontiguous
current-path occurrences aggregate as recurrence. The algorithm/cache identity
must change and tests must cover both continuation directions, earlier-ancestor
rejection, no duplicate frame, strict shrinkage, marks, and pprof replay.

## Round 8 — PASS for unified stay/pop/push

The v2 source-only replay next returned the current operation on one side and
an earlier root operation on the other while decomposing a nested interval.
This is the user's original pop action, not an invalid semantic label. Before
opening any manifest, stage, or score, the plan was reopened again.

The reviewer approved a unified resolver. A child matching current stays; a
child matching an earlier active frame pops to that frame; a name absent from
the active path pushes one new frame. Both child intervals strictly shrink,
only explicit STOP or the one-turn base case terminates, and resolved full paths
must differ. The sparse full-path mark, B-cubed, boundary, and pprof contracts
remain unchanged. No replace operation is added.

## Round 9 — PASS for emitted-path canonicalization

The reviewer identified one structural consequence: a nested pop may produce
two adjacent raw recursion leaves with the same resolved full path across a
parent split. The approved materialization emits a mark only at sequence start
or when the canonical full path changes, coalescing only exact adjacent equal
paths. Raw decisions remain auditable. This is deterministic representation
canonicalization—not semantic contraction—and changes neither assignments,
B-cubed, boundaries, pprof mass, nor any user-visible stack.

## Round 10 — REVISE for identical resolved siblings

The next source-only v3 replay returned a raw `SPLIT` whose two names both
resolved to the unchanged current root path. Treating every pair of identical
resolved siblings as an error makes the controller partial on a semantically
auditable no-op; treating every identical pair as STOP would be too broad.

Independent review allowed exactly one normalization:
`left_path == right_path == active_path` becomes the separately reported
`degenerate_current_split_stop`. The raw `SPLIT` remains cached, and the
controller emits the current path with no boundary or additional mark. If the
same resolved siblings are a new child or an earlier ancestor, inference still
fails closed. The algorithm/cache identity must advance to v4, and focused
tests must prove both the allowed and rejected cases plus unchanged assignment,
mark, metric, and pprof mass contracts. Re-review is required before preflight.

## Round 11 — PASS for exact v4 totalization

After the plan, fail-closed policy, preflight record, step report, tests, and
cache identity were made consistent, independent re-review returned PASS. The
exception is limited to `left_path == right_path == active_path`; equal new or
earlier paths remain errors. The raw split, separate controller resolution,
and four disjoint decision counts keep the event auditable without changing
assignments, marks, metric mass, workload, RQ, thesis, or paper authorization.
