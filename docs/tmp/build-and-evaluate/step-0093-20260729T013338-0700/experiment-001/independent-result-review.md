# Independent Result Review

## Round 1 verdict

**ACCEPT computations; REJECT paper admission.**

The reviewer independently parsed the frozen Step 0087 inputs without importing
or invoking `score.py` and without trusting generated per-query or per-task rows.
It reproduced:

- 20,866 unit-weight operation keys with exact source/pre-canonical/canonical
  key and framework equality;
- 405 sessions, 251 tasks, four frameworks;
- 94 eligible tasks, 240 queries;
- 192--377 candidates and 1--4 relevant candidates per query.

### Independent primary recomputation

| Representation | Task-macro MAP |
|---|---:|
| Pre-canonical full | 0.24523794277022101 |
| Canonical full | 0.19485401862929108 |
| Canonical root-only | 0.13897326403565838 |
| Canonical root-stripped | 0.13511505027253934 |
| Root-stripped + generic removal | 0.12256785735487624 |
| Action-kind | 0.09272277101124944 |
| Raw-action-key | 0.053992411501601625 |
| Phase | 0.03581109244279442 |
| Operation count | 0.022768461418184577 |

### Independent gate recomputation

| Comparison | Delta | 95% task-bootstrap interval | Gate |
|---|---:|---:|---|
| full − action-kind | +0.10213124761804165 | [+0.047244662282919354, +0.15765797636490633] | pass |
| full − raw-action-key | +0.14086160712768947 | [+0.08253505879070906, +0.20085310933173425] | pass |
| full − root-only | +0.05588075459363270 | [−0.000879256308729637, +0.11184923974240413] | **fail** |
| root-stripped − action-kind | +0.04239227926128991 | [−0.013652413035117212, +0.10011057497376029] | **fail** |
| root-stripped − raw-action-key | +0.08112263877093771 | [+0.029879060033287524, +0.13608280068636688] | pass |
| root-stripped generic − action-kind | +0.029845086343626804 | [−0.021297202962057758, +0.08182256424698356] | **fail** |
| root-stripped generic − raw-action-key | +0.06857544585327462 | [+0.023560532880111337, +0.11675331083157679] | pass |
| full − pre-canonical | −0.050383924140929924 | [−0.12333202354396028, +0.023940090356657638] | no canonicalization credit |

Full minus phase and full minus operation count also reproduced exactly with
wholly positive intervals.

### Validity audit

- Tie-aware AP, Top-1, and MRR are correct; the reviewer exhaustively enumerated
  relevance permutations through tie size seven.
- Candidate/relevance construction, framework exclusion, root stripping,
  generic-frame removal, task-macro averaging, and complete-task bootstrap are
  correct.
- Task-bearing session IDs never order ties.
- No eligible canonical representation contains its exact task identifier. The
  only literal overlap elsewhere was the ineligible task `mailman`.
- Minor non-gating issue: the random control hashed task-bearing session IDs
  despite the plan saying the task field would not enter its seed. Cryptographic
  hashing makes the output effectively random and the control is not a gate
  comparator, so it does not change the verdict.

### Round 1 paper decision

The positive gate definitively fails. The result cannot establish non-root
consistency, operation equivalence, or a canonicalization benefit and must not
enter the paper as positive RQ3 evidence.

## Disposition of the minor issue

Accepted for cleanup. The random-control uniqueness keys will be replaced by
numeric source-order indices before the final artifact is frozen. No primary,
gate, or bootstrap representation uses this control. Per the plan, the scorer
will be rerun and the reviewer will confirm that the gate results remain
unchanged.

## Round 2 finalization

**ACCEPT implementation and final artifacts; REJECT paper admission.**

The reviewer confirmed that the revised random control uses numeric source-order
indices only and independently reproduced its final task-macro MAP
`0.018034810986173207` and query-micro MAP `0.018386270164212265`. Final hashes
match `execution-log.md`; the bootstrap digest and every primary/gate result are
unchanged. No scoring or leakage defect remains.
