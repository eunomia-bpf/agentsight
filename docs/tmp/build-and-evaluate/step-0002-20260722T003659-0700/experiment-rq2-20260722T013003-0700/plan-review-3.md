# RQ2 Plan Review — Round 3

**Reviewed:** 2026-07-22  
**Verdict:** **PASS**

The three Round 2 execution gaps are closed:

1. `raw/rq2-trajectory.csv` is now a preregistered event-level worktree-lane
   artifact alongside cycle and coverage tables, so F5 Panel A can be rendered
   from frozen derived rows rather than reopening source data during plotting.
2. The six event-source SHA-256 values and mutation-CSV hash are explicit; the
   analyzer must read the verified `.json.gz` streams directly, and the exact
   real command, analyzer path, output directory, media names, reconciliation,
   and output-hash requirements are fixed.
3. Artifact-type stratification is explicitly deferred to RQ5's independently
   frozen classifier. The plan now states that this experiment supplies only
   RQ2's cadence/accumulation facet and cannot alone close canonical RQ2.

The earlier scientific repairs also remain intact: all cycles, action ranks,
and censoring are worktree-local; co-observed validation-command mutations are
separated without inventing within-event order; accumulation is not called
coverage or backlog; the predetermined 3/6 gate limits the result to supporting
within-case and source-coverage evidence; and F5 cannot pool cycle rows as
independent project replications.

Implementation may start. During preflight, verify that
`rq2-trajectory.csv` contains the declared identity, rank, timestamp, session,
attempt-status, per-event mutation, co-observed mutation, and cumulative fields,
and that the plotting phase actually reopens the written CSVs. Use the literal
legend label `status=observed (outcome unknown)` as the already noted
non-blocking precision fix.
