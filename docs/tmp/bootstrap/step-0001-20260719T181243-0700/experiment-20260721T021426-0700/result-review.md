# Independent Result Review

Reviewed: 2026-07-21

Scope: no-model preparation, task-058 P0, and the fixed six-task headroom gate
Reviewer role: read-only protocol/result auditor, not a semantic annotator or gold source

## Verdict

- **PASS:** the six-task headroom gate is valid and the decision
  `full_matrix_admitted=false` is correct.
- **BLOCK:** P0 must not be described as a retrieval-mechanism preflight pass.
  It validates checkpoint, isolation, fork, continuation, and executable-oracle
  plumbing only.
- **BLOCK:** the current local branch tip is not publishable because local-only
  commit `47893046f` contains nine runtime credential blobs. The tracked remote
  branch contains none. The local commit must become unreachable from the tip
  that is pushed; a later deletion commit is insufficient.

## Independent score recomputation

The reviewer recomputed every score from the six retained official
`final/oracle.json` files:

| Task | Recomputed score | Below 0.95 |
|---|---:|---:|
| `057-interruption-resume` | `0.8 / 1.3 = 0.6154` | yes |
| `058-multiday-project-state` | `1.1 / 1.28 = 0.8594` | yes |
| `059-event-update-replan` | `1.0` | no |
| `060-task-cancellation-cleanup` | `1.0` | no |
| `103-policy-update-replan-diff` | `1.0` | no |
| `105-partial-batch-resume-ledger` | `0.499375 -> 0.4994` | yes |

For task 105, the full recomputation is:

```text
1.0*0.30 + 0.35*0.30 + 0.10*0.25
+ (0.45*0 + 0.30*1 + 0.25*0.65)*0.15
= 0.499375
```

Only tasks 057, 058, and 105 are below the registered threshold: 3/6 rather
than the required 4/6. The aggregate
`raw/headroom/headroom-report.json` is correct, and no full effect matrix may
run.

## Protocol audit

- The six tasks, order, threshold, and 4/6 rule were fixed in `plan.md` before
  results. No task replacement or threshold change was found.
- P0 and headroom task 058 used different fresh prefix sessions. P0 and all six
  headroom checkpoints are excluded from any effect estimate.
- The benchmark checkout is clean at
  `1025086a446653702b80cfb48babbeec35db6b2c`.
- P0 has identical per-condition manifest, prompt, argv, and environment hashes.
  Its real worker isolation probe passed workspace read/write, hidden-path
  denial, DNS denial, and network denial.
- Failed P0 attempts remain under `raw/preflight/attempts/`; the accepted report
  points only to the final forks. No evidence of result-selective headroom reruns
  or reuse was found.
- `rubric_provider_requests=0` agrees with the driver calling only the official
  `run_oracle` and with every selected task having `outcome_llm_weight=0`.
  However, that count is currently a hard-coded assertion rather than an
  independently measured request counter.
- `oracle_twice` executes the official oracle twice and rejects unequal
  canonical JSON, but retains only the first payload plus a count of two. The
  score is independently reproducible; the second payload/hash is an
  auditability gap that must be closed in the next protocol.

## P0 treatment-engagement failure

The Generic, Raw, and Trajectory ledgers all report:

```text
tool_calls = 0
tool_response_tokens = 0
tool_response_bytes = 0
exposed_source_ids = []
```

Therefore neither Full Raw Retrieval nor Workspace Trajectory Retrieval was
used by the actual supervisor model. The four P0 outcomes cannot be interpreted
as an H6 representation comparison. Generic advice also named the
supervisor-only `read_current` tool in a worker-facing message. A new protocol
must require real, matched tool engagement and reject supervisor-tool names in
worker advice before any model call. It must not repair the query and rerun the
same inspected tasks as a result-rescue exercise.

## Security and publication boundary

Runtime `auth.json` files were inaccessible inside the worker tool sandbox, so
they did not change the condition comparison or headroom scores. They were,
however, incorrectly retained as artifacts. The root removed all runtime
credential files without reading them and added post-adapter cleanup. Because
the local-only commit already contains nine such blobs, publication additionally
requires rewriting the unpushed local tip and verifying the push range, index,
and output tree contain no credential path. Origin was independently verified
to contain zero such paths.

## Next experiment

Close the current six-task matrix. The highest-value next experiment is a newly
preregistered cross-domain checkpoint-continuation workload using:

- SWE Context Bench related-task sequences for coding; and
- CORE-Bench paper-reproduction tasks for scientific work.

Official tests/evaluators remain the only truth. Eligibility must follow a
fixed structural manifest rather than observed worker scores. No-op, Generic,
Full Raw, and Workspace Trajectory remain mandatory, with matched budgets,
real tool engagement, and both oracle payloads/hashes retained.

The following are prohibited outcome-driven tuning: selecting only 057/058/105,
changing the gate to 3/6, rerunning no-op until a low score appears, changing
queries and retesting the same inspected tasks, weakening Generic, or including
P0/P1 scores in an effect estimate.

Final classification: headroom valid; P0 retrieval mechanism incomplete; H6
inconclusive and not yet actually tested; current result is dependency-only.
