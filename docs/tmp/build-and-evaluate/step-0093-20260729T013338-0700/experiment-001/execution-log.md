# Execution Log

## Protocol review

- Round 1 independent plan verdict: `BLOCK`.
- Blocking defects: task-bearing session-ID tie order, insufficient root-label
  control, over-broad claim and interval interpretation.
- The plan was amended before implementation.
- Round 2 verdict: `APPROVE`.

## Preflight

Command:

```bash
python3 -m py_compile score.py
python3 score.py preflight
```

Outcome: pass.

- 20,866 source operation rows.
- 20,866 pre-canonical predictions.
- 20,866 canonical predictions.
- Exact `(session, step_id)` key equality.
- Unit weights and source/prediction framework equality passed.
- All 18 representations and the analytic tie-metric self-test executed for one
  real eligible query.

## Full execution

Command:

```bash
/usr/bin/time -f 'elapsed=%E maxrss_kb=%M' python3 score.py full
```

Outcome: pass at `2026-07-29T01:50:30-07:00`.

- Wall time: 3.41 seconds.
- Maximum resident set: 233,072 KiB.
- 405 sessions, 251 tasks, and four frameworks.
- 94 eligible cross-framework tasks and 240 eligible queries.
- Every query ranked the full different-framework candidate library.
- 10,000 complete-task bootstrap replicates, seed `20260729`.

## Determinism check

The initial full command was executed a second time and all output digests were
unchanged. The independent reviewer then identified one non-gating hygiene
issue: the random control hashed task-bearing session IDs as uniqueness keys.
The scorer was amended to hash numeric source-order indices only, and preflight
plus the full execution were repeated.

Final artifact SHA-256 digests are:

- `raw-results.json`:
  `b22c6da19ebccd30acd7651c2d849db2806c560655efc0482d1ebbe8cc9bb69a`
- `per-query.jsonl`:
  `1e783f45d9ef00d5cb280b6948a34bc0d30767a9da7f2360871b1226a55457f9`
- `per-task.jsonl`:
  `160af426924269fa271d145c3a01eb26afc86f10c88bf0ad1cc47621ed00d0cd`
- `bootstrap-summary.json`:
  `b6927b36b7e05db3e17a7b2c7f7f13cbcd612e4eb3062f767c8567387018998a`

The authoritative scorer SHA-256 is
`b3e1c5d2e58ccfc748d189f66160293533077b3bca6c13119e562d3c6b1ccad0`.
The bootstrap digest and every primary/gate value were unchanged; only the
non-gating random-control rows changed.
