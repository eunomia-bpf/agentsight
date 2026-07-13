# Serial implementation review: AgentNet cross-platform RQ2

The same independent subagent performed four serial, read-only reviews and
explicitly applied `research-experiment-design`. The reviewer never edited a
file. The root accepted each scientific or executable must-fix, made the
smallest corresponding implementation change, reran tests, and requested a new
review of the current files.

## Round 1 — REVISE

The reviewer found that preflight and full shared unsafe mode boundaries:
preflight could emit a scientific verdict, full could accept a subset, and
full did not prove complete task and label coverage. It also requested the
approved exact AgentProf version, a real target-label swap/withhold test, and
the already-planned base secondary diagnostics.

### Disposition

- Preflight now uses a fixed small subset and emits only
  `NOT_EVALUATED_PREFLIGHT`.
- Full rejects subsets and validates complete task and exact label-operation
  coverage.
- AgentProf must be exactly 0.2.37.
- The tests exercise alternate, wrong-platform, and absent target labels.
- Base group, session, annotation, risk-mass, and domain diagnostics were added
  without entering the bootstrap or verdict.

## Round 2 — REVISE

The reviewer found a deeper target-label dependency: the original coordinator
saved only the requested valid-draw count and could append more draw specs after
the scorer had read target labels. This violated the plan even though the draw
seed rule itself was deterministic. The reviewer also required the exact full
10,000/50,000/4204 settings and an explicit final valid-draw count.

### Disposition

- Each predictor now writes the complete maximum-attempt draw sequence before
  any target label is passed to a scorer.
- The scorer processes the fixed sequence in batches, keeps the first required
  valid draws, and never calls the predictor or appends a draw.
- Full accepts only 10,000 valid draws, 50,000 attempts, and seed 4204, and
  verifies exactly 10,000 valid draws per held-out fold.

## Round 3 — REVISE

All primary boundaries passed. The only remaining mismatch was that additive
risk-mass ranking reused operation AP/recall/work metrics, although the approved
plan says mass answers only a per-group-opening cost question.

### Disposition

Mass ranking is now base-only and reports complete-tie group-opening quantities:
total/scored groups, groups-to-50% positives, hot-score tie groups, and sessions
per hot group. It exposes no operation AP, recall@30, or work-to-50 and cannot
participate in bootstrap or verdict logic.

## Round 4 — PASS

**Reviewed:** current implementation and 9/9 dedicated tests  
**Disposition:** `PASS`; zero must-fix; authorize REAL PREFLIGHT.

The reviewer confirmed:

- target-label and pure-helper boundaries;
- complete draw generation before target scoring and first-N-valid selection;
- exact full 10,000/50,000/4204 settings and AgentProf 0.2.37;
- reciprocal folds without cross-model pooled ranking;
- exact ties, full-population validation, count/risk conservation, and verdict
  logic;
- group-opening-only additive mass diagnostics; and
- the rule that preflight can judge execution only, not the hypothesis.

**Files modified by reviewer:** none.
