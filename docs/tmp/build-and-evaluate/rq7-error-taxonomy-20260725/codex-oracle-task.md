# Task: Corrected RQ7 oracle and conformance re-assessment

You are in a research repo studying longitudinal AI-agent workspace behavior. A conformance experiment ("RQ7", frozen at `docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/`) tested whether the repo's artifact-linked trajectory projection can answer 120 source-verifiable questions (6 projects × 20; families A action-only, B artifact-linked, C cross-session, D final-state). Ground truth = an independent source-direct oracle; current version is `agentvis/research/rq7_source_oracle_check.py` (SPEC_VERSION "native-root-conformance-v3").

Prior audit (already done, trust it): docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/taxonomy.md and docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD/result.md. Key facts:

- At HEAD, trajectory answers 51/60 B+C correctly; 9 rows still mismatch the frozen oracle.
- 3 of the 9 are ORACLE-side artifacts, not projection bugs: agentsight-B1/B2 (oracle's `plain_operands` treats `-n` as argument-taking for every command, dropping the operand of `cat -n <file>`), academic-C2 (oracle doesn't track inline `cd`, fabricates repo-root paths from `cd third_party/... && cat README.md`, counts `rmdir` which is not in the spec's MUTATORS, and resolves a `cd /tmp/...` create into the repo).
- The remaining 6 (ActPlane-C1/C2/C5, bpf-developer-tutorial-C1/C2/C5) are largely driven by an open oracle defect: `unwrap_exec` in rq7_source_oracle_check.py (line ~159) cannot resolve codex exec JS wrappers like `const patch = "*** Begin Patch\n..."`, hiding ~480 real mutations from the oracle.

Frozen question semantics: `docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/private/question-spec.md` (read it; redirection/heredoc segments contribute no artifact edge, lexical relative-path resolution, globs/variables excluded, etc.).

## What to do

1. Fix the open defects in `agentvis/research/rq7_source_oracle_check.py`:
   a. `unwrap_exec`: resolve codex exec JS wrappers containing `*** Begin Patch` so the wrapped apply_patch content is parsed like a normal apply_patch call.
   b. Track inline `cd` within shell commands so subsequent relative path operands resolve against the cd'ed directory (and paths outside the worktree are excluded per spec).
   c. Verify the `-n`/option-arity and sed-program-as-path handling already present are correct per spec.
   Bump SPEC_VERSION (e.g. v4) and keep a changelog comment at the top of the file.
2. The oracle is GROUND TRUTH: every change must be justified with before/after evidence from the frozen source rows. Log each justification.
3. Re-derive expected answers for ALL 120 questions with the corrected oracle against the SAME frozen data used by the rerun (see docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD/ and its scripts/ for how the freeze is read at HEAD; the v2 freeze in experiment-001/private cannot be read by HEAD tooling directly — reuse the rerun's approach). Check whether any previously-correct question's expected value shifts.
4. Compare HEAD trajectory answers (docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/rerun-at-HEAD/method-results.csv) against your corrected expected answers. Report: how many of the 9 mismatches dissolve, any newly-mismatching rows, final per-family totals, per-project B+C conditional accuracy, and the Trajectory−ProcGrep B+C coverage contrast (project-block bootstrap, same method as rerun-at-HEAD/result.md).
5. For any row that STILL mismatches after oracle correction, state the residual cause precisely (projection broader shell/scope semantics vs remaining bug, on which side), with code and data evidence.

## Hard constraints

- DO NOT modify anything under docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/ (frozen artifact).
- DO NOT modify agentvis/research/rq7_measurement.py or any projection-side code (agentvis/src/, agent-session/); this task is oracle-side only.
- Write all new outputs to docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/ (result.md with tables + per-change justification log; preserve your scripts there too).
- Do not run git commit/push.

## Final message

Return a compact summary: final conformance numbers (trajectory vs corrected oracle), what still mismatches and why, and what (if anything) still blocks a defensible exact-fact capability claim for the projection.
