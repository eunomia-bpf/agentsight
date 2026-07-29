# Plan review

## Fresh review

Verdict: **APPROVE**

No blocking scientific or executability defects.

The experiment directly tests the fixed RQ3 mechanism hypothesis and is
nonredundant: the same-model flat arm isolates hierarchy depth on the complete
population, and either positive or negative results change the permitted
mechanism claim.

Reusing Step 0087 as the direct-hierarchy arm is justified. Its frozen prompt
requests complete variable-depth paths in one pass, explicitly excludes
STOP/SPLIT and recursive binary refinement, and its harness makes one isolated
complete-trajectory request, followed only by validation, deterministic
assembly/root repair, canonicalization, and scoring. The complete
405-trajectory artifacts and 20,866 operation/20,461 pair rows exist. No
distinct recursive/refined arm exists, so omitting that comparison is correct.

The planned budgets are fair: exact packets, model, CLI release, ignored user
configuration, defaults, isolation, workers, timeout, retry policy, downstream
pipeline, oracle, and scoring are matched; only the depth contract changes.
Ordinary B-cubed and exact-boundary metrics answer the declared question, and
10,000 paired task-cluster bootstrap resamples over the same 251 tasks with a
fixed seed are valid.

The completion rule, resumable artifacts, cost accounting, preflight, and
full-run commands are sufficiently specified for implementation and execution.

Optional, nonblocking suggestions:

- hard-code the installed `codex-cli 0.145.0` path and record `--version`;
- preserve an exact prompt diff showing that only hierarchy-depth clauses
  changed;
- state how an otherwise-valid session-ID mismatch after the ordinary retry
  receives parity with Step 0087's documented format-only exception;
- name the defining protocol for exact boundary F1 alongside B-cubed.

## Root disposition

Accept the review. No scientific repair or second review is needed.

The implementation will invoke the exact installed 0.145.0 binary and record
its version. It will save a unified prompt diff. The ordinary policy remains
one initial call plus one format retry. If and only if the second response is
otherwise valid and differs solely in the top-level session string, the
harness may replace that string with the packet's exact value, record the
repair, and leave every mark byte-for-value unchanged. This is the same
format-only fallback that Step 0087 predeclared for ordinal 53; it is not a
semantic retry. Any other terminal error leaves the full arm incomplete and
forbids partial scoring.

Exact boundary precision/recall/F1 follows the released CodeTraceBench stage
transition protocol already frozen in the Step 0087 RQ3 scorer. No metric is
added or changed.

Post-review implementation inspection found that Step 0087 freezes separate
seeds in its unchanged helpers: `20260720` for B-cubed and `20260722` for
boundary F1. The plan now records both exact seeds. This corrects
reproducibility wording only; it does not change the hypothesis, metric,
population, or expected answer and does not require a follow-up review.
