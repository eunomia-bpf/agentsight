# Measurement-Capability Plan Review

## Initial Review

**Verdict: BLOCK**

1. The prior checker was not source-direct. It reopened and hashed native
   files, but recomputed answers from `freeze.json`'s `direct_action_atoms`,
   `oracle_edges`, sessions, and anchors. It therefore did not independently
   validate the primary enumerator.
2. The frozen edge table contained redirect and heredoc tokens such as
   `2>/dev/null`, `>`, and `<<EOF` as artifacts. Those false artifacts crossed
   session boundaries and could change C1, C2, and C5.
3. Step 0003's three implementation attempts were exhausted. A continuation
   cannot describe a general instruction to keep researching as an exception
   to that frozen attempt rule.
4. The retrieval-based Raw condition was introduced after the parent plan's
   final review, so the earlier PASS did not review the current baseline.
5. The Raw command monitor did not catch traversal inside Python source such as
   `open("../...")`; a read-only sandbox alone did not prevent access to parent
   private/oracle files.

The experiment cannot support the narrow fact-coverage claim until the oracle
is independently reconstructed from native records, false shell artifacts are
removed and questions are regenerated, the retrieval baseline is reviewed as a
new experiment, and the Raw filesystem boundary is enforced by isolation
rather than command-string inspection alone.

## Follow-up Review 1

**Verdict: BLOCK**

Redirect/heredoc extraction, source-direct A--C reconstruction, the new
experiment boundary, and explicit review of the retrieval Raw condition were
closed. Two blockers remained:

1. Bubblewrap still exposed the host PID namespace and inherited environment.
2. The checker read D1--D5's normalized `status` instead of independently
   deriving it from archived cutoff evidence.

## Follow-up Review 2 — Final

**Verdict: PASS**

All five original blockers are closed:

- The checker independently reparses native records and reconstructs A--C.
- D1--D5 are independently derived from `index_entry` and `present`; indexed
  path/stage and archived content/absence evidence are verified.
- Redirect/heredoc artifacts are excluded and all 120 questions were
  rederived.
- The changed oracle, Raw baseline, and isolation form a legitimate new
  experiment rather than reopening Step 0003.
- Retrieval Raw is explicitly reviewed. Bubblewrap uses a private PID
  namespace, clears inherited environment state, and hides parent files.

The corrected oracle passes all 120 questions, its recorded checker hash
matches the current checker, and the private audit-manifest reconciles. The
plan may proceed to REAL PREFLIGHT.

## Preflight Transport Record And Reader Amendment

The approved `gpt-5.6-sol` preflight produced no scoreable answer:

1. attempt 1 could not resolve DNS because the isolated `/etc/resolv.conf`
   symlink target was absent;
2. attempt 2 completed one evidence read, then the boundary monitor mistook
   jq's `//` operator for an absolute path;
3. after both transport defects were corrected, attempt 3 maintained a live
   network connection but produced no first token before the frozen 900-second
   timeout.

No answer, accuracy value, or candidate comparison was observed. The plan now
registers `gpt-5.6-terra` at the same medium reasoning and all other fixed
budgets, permits one preflight, and stops the model baseline if that call is
unavailable. This amendment requires a fresh reviewer disposition before the
Terra call.

## Reader-Amendment Review

**Verdict: PASS**

The one-time reader replacement is scientifically admissible because all Sol
attempts produced zero scoreable answers; the final retained attempt records
900 seconds, zero output tokens, zero tool calls, and zero answers. The
experiment is frozen before scoring to `gpt-5.6-terra`, and any result applies
only to that Raw reader—not Sol or arbitrary models.

One Terra preflight is sufficient as a mechanism gate. It must complete, make
at least one local evidence read, and keep the original timeout, call, returned
byte, output, and reasoning budgets. Failure closes Raw as unavailable; no
further model or budget substitution is permitted. Corpus, questions, oracle,
repetitions, scoring, and isolation are otherwise unchanged.
