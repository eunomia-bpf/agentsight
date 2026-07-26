# Task: Rerun RQ1-RQ4 recompute at FINAL HEAD (post event-workdir fix) and diff

Context: an earlier recompute (docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/, delta-report.md inside) ran at a HEAD that did NOT yet include the final event-workdir projection fix (agent-session/src/parser.rs: per-record cwd now overrides session-initial cwd; see docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/workdir-fix/result.md). A reviewer correctly notes the paper's numbers must come from the final revision.

Do:

1. Rebuild agentvis at current HEAD (cargo build --release --locked --manifest-path agentvis/Cargo.toml).
2. Rerun the EXACT same pipeline as the 20260725 recompute (see docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/commands.log and delta-report.md): `agentvis research-rq1 --cutoff-ms 1784708569241 --output <new raw dir> <the 6 roots>` then the RQ2-RQ4 steps, all outputs to docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/.
3. Diff every headline number against the 20260725 recompute: sessions, total/attributed actions, artifacts, mutations, reuse range, Spearman rho, persistence-qualified count, validation coverage (F5), RQ3 eunomia.dev numbers (repeat fraction, unknown_create births), RQ4 components/boundaries per project and totals.
4. ALSO resolve two known numeric inconsistencies and state the correct values with evidence:
   a. RQ2 validation coverage: is it 6/6 or 3/6? (the 20260725 recompute's coverage table said 6/6 but a canned result.md header said 3/6)
   b. RQ4 totals: the paper says 121 components/108 boundaries but per-project values were reported summing to 120/110 — recompute the exact totals and per-project breakdown.
5. Write docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/delta-report.md: old (20260725) vs new (final HEAD) for every number, marking UNCHANGED/CHANGED, plus the two resolved inconsistencies.

If any headline number CHANGED, flag it at the top of the report — the paper is being restructured in parallel and will need the final values. Do not edit docs/paper/*, do not touch frozen dirs, no git commands. Note another worker may be running cargo builds concurrently; if the target dir is locked, wait for it.
