# Full-pass non-convergence and incremental-review amendment

Timestamp: 2026-07-24T07:10:00-07:00
Status: observed full-run result and prospective protocol amendment

## Why this amendment is necessary

The original plan repeated a complete diagnostic review until one full pass
accepted no annotation change or an exact annotation state repeated.  The
outcome-blind AgentReward run has now completed the fresh pass plus seven full
revision passes.  Neither terminal condition occurred.

The latest pass still made 13 annotation-level changes: one annotation was
added, two were removed, and ten retained annotations changed.  Optional tag
names fell from 489 to 481 and singleton names from 202 to 192, while the
number of structural issues remained 266.  All 7,229 source operations and
51,904,621 profiled tokens were preserved.  This state is **not** called
converged.

The repeated full-review policy is therefore itself a negative mechanism
result.  Fresh reviewers repeatedly reconsider already accepted, unchanged
contexts and continue to make long-tail naming choices.  Another identical
whole-population pass has no scientific reason to be expected to terminate.
Stopping the full passes is not favorable-state selection: iteration 007 is
retained as the latest state, every prior pass and its costs remain available,
and no outcome or human-stage label has been opened.

## Measured cost of the failed full-pass policy

Across the fresh pass and seven revision passes:

| Quantity | Complete measured total |
|---|---:|
| Provider input tokens | 191,838,723 |
| Provider cached input tokens | 180,865,536 |
| Derived uncached input tokens | 10,973,187 |
| Provider output tokens | 1,476,432 |
| Reasoning output tokens | 469,409 |
| Logical serialized input tokens | 35,231,169 |
| Logical output tokens | 1,963,345 |
| Sum of pass critical paths | 21,166.766 s (5.88 h) |
| Summed worker time | 35,764.119 s (9.93 h) |

The seven revision passes alone consumed 179,799,306 provider input tokens,
30,224,440 logical input tokens, and 17,645.145 seconds of pass critical-path
time.  By contrast, deterministic diagnosis and pprof construction remain
about one quarter of a second per full view.  RQ4 must report both layers and
must not use the latter as a proxy for end-to-end automatic construction.

## Amended mechanism

The candidate product mechanism becomes incremental diagnostic review:

1. AgentPProf emits a stable `review_key` and a deterministic local
   `context_fingerprint` for each hierarchy issue, tag-reuse row, and
   near-name candidate.
2. The automatic backend records `change` or `keep` for the presented key and
   fingerprint in the experiment's Markdown report.
3. A previously accepted `keep` is reused while its fingerprint is unchanged.
   It is not sent to a fresh reviewer merely because another iteration began.
4. An item reopens only when it is new or its local fingerprint changes after
   an annotation revision.  This is local invalidation, not an iteration cap.
5. Regeneration terminates when no invalidated item remains and the same
   annotations regenerate the same profile mass.  Any annotation change
   invalidates the affected local items before termination.

The annotation JSON remains the only semantic input to the CLI.  No new
required state file, artifact seal, Git binding, or product format is added.
The cache is an automatic-backend execution optimization; AgentPProf's product
artifact remains `.pb` or `.pb.gz`.

## Evaluation consequence

The complete full-pass trajectory remains a measured baseline named
**repeated full review**.  The amended method is evaluated separately as
**incremental invalidation**, starting from the latest outcome-blind state.
Its terminal condition, newly read contexts, calls, token use, and wall time
are reported explicitly.  The paper may conclude that full re-review is
non-convergent and prohibitively expensive on this population if the retained
measurements support that statement.  It may call the incremental mechanism
converged only if no invalidated item remains.

No success/failure side, pair identifier, reward, prior signed profile,
expected case answer, or human stage becomes visible during this amendment or
incremental run.
