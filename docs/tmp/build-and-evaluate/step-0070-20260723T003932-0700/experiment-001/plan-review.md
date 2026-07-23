# Plan Review: RQ2 Canonical Operation Identity

## Round 1 — 2026-07-23T00:45:00-07:00

**Reviewer verdict:** `REVISE`.

The reviewer accepted the fixed-boundary naming hypothesis, the current
Agent+Evidence baseline, the native comparison, and standard per-query AP/MAP.
It found five execution- or validity-blocking defects:

1. the canonicalizer's allowed inputs, vocabulary, shared cross-workload rule,
   and reproducible output were underspecified;
2. the mixed-result disposition allowed result-guided identity selection;
3. the approximate cross-workload rule was not decidable, and correctness
   failure was conflated with scientific contradiction;
4. exact roots, current/candidate rows, paired comparison commands, and the
   distinction between current Agent+Evidence and the declared/reference
   hierarchy were absent;
5. canonical-name collisions could silently remove a fixed mark boundary.

**Root response:** accepted all five. The revised plan fixes one shared
vocabulary-based candidate before scoring; limits the mapping input to old
operation names plus that vocabulary; forbids score-conditioned granularity
selection; reports workload-specific effects without an omnibus verdict; lists
exact roots and current/candidate paths; classifies correctness failure as
invalid; and rejects unresolved local canonical-path collisions before scoring.
The experiment is now explicitly adaptive/supporting current-product replay
rather than untouched decisive confirmation.

## Round 2 — 2026-07-23T01:22:00-07:00

**Reviewer verdict:** `REVISE`.

The reviewer accepted the fixed candidate, matched current-Agent baseline,
workload-local MAP reporting, and collision-invalid policy. It found three
remaining execution blockers:

1. the plan still did not say whether the mapping was manual, model-generated,
   or algorithmic, so it was not independently reproducible;
2. the referenced `prepare`/`score` implementation and exact paired-comparison
   commands did not exist;
3. the HINT scorer still let mathematically zero Wilson lower bounds become
   floating residues, and the plan tried to compare a corrected candidate to
   superseded current rows.

**Root response:** accepted all three. The candidate is now the checked-in,
target-blind, deterministic `action-object-lexicon-v1` algorithm with synthetic
tests. The preparation and comparison commands are implemented and fully
specified. The Wilson implementation returns exact zero for every zero-hit
group, and the plan reruns both the HINT current baseline and candidate through
that identical corrected scorer. No candidate mapping has been generated and
no candidate result has been scored before this revision.

## Round 3 — 2026-07-23T01:47:00-07:00

**Reviewer verdict:** `APPROVE`.

The independent reviewer read the final plan, deterministic canonicalizer and
tests, and the corrected scorer. It confirmed that all Round 2 blockers are
closed: mapping is checked-in and target-blind; the declared `prepare` and
`score` commands exist and implement the registered joins and bootstraps; and
both HINT current and candidate runs use the same exact-zero Wilson scorer.
Fixed boundaries, source evidence, mass, candidate granularity, and
workload-local interpretation remain unchanged. The experiment may enter real
preflight.

## Round 4 — 2026-07-23T02:03:00-07:00

**Reviewer input requested:** The first source-only preparation attempt stopped
before writing a complete candidate because the base two-word map would make
153 adjacent intervals identical. No packet, target, signal, outcome, profile,
per-query row, or MAP was opened. The implementation now applies one
checked-in, deterministic boundary-preserving rule: only old tags implicated
in such a collision use their last one or two normalized non-action head nouns
as the object/qualifier. Mapping remains global per old tag and at most three
words; unresolved collisions remain invalid. The reviewer must decide whether
this closes correctness without introducing result-guided tuning.

**Reviewer verdict:** `APPROVE`.

The reviewer classified this as target-blind correctness closure, not
result-driven tuning. The trigger is only equality of adjacent canonical paths;
the checked-in refinement reads only the colliding old tag text; the same tag
maps globally to the same output; and every fixed boundary, source-evidence
frame, metric, and baseline is otherwise unchanged. Because the failed
preparation produced no scientific result, execution may resume at
prepare/preflight. The final interpretation must remain adaptive/supporting
current-product replay rather than untouched confirmation.

## Round 5 — 2026-07-23T02:12:00-07:00

**Reviewer input requested:** The reviewed refinement reduced 153 collisions to
two collision pairs (four old tags) but correctly kept the candidate invalid:
`Inspect candidate source` versus `Read candidate source`, and
`Review environmental health data` versus `Review population health data`.
Still before any candidate profile or score, the final lexical rule preserves
`read` as a distinct reusable action and, when two head nouns are needed, uses
the first and last content nouns. This yields `inspect environmental data`
versus `inspect population data`. This is the fifth and final plan review;
remaining collisions will terminate the candidate rather than expand rules.

**Reviewer verdict:** `APPROVE`.

The reviewer confirmed that separating `read` from `inspect` and retaining the
first/last content nouns are global lexical-semantic rules, not target- or
score-guided changes. They preserve the three-word cap, global old-tag
identity, fixed boundaries, evidence, baseline, and metric. This authorizes one
final preparation attempt only; any remaining collision makes the candidate
`INVALID`.
