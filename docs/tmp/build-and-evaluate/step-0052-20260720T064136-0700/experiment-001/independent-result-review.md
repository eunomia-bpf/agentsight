# Independent Result Review — Step0052

- reviewer: independent read-only subagent
- skill explicitly used: `research-experiment-design`
- final run status: **VALID / COMPLETE**
- tested hypothesis: **CONTRADICTED / NOT ADOPTED**
- scorer bug: none found
- rerun required: no
- reporting must-fix: one, resolved below

## Independent Raw Reconstruction

The reviewer independently rebuilt all 405 session caches:

- 20,866 operations and 20,461 adjacent pairs;
- 405 initialization decisions;
- 3,954 learned changes;
- 16,359 learned continues and 148 structurally forced continues;
- 4,359 predicted temporal instances (`405 + 3,954`);
- 20,313 continuation calls and 4,359 label calls, totaling 24,672;
- five one-item sessions with 153 operations: five initializations plus 148
  forced continuations;
- 1,011/2,568 responsibility types used/available, summed per trajectory.

All source-cache hashes, operation-evidence hashes, transition progression,
prediction coverage, and candidate instances matched with zero errors.

## Independently Recomputed Standard Metrics

| Method | Exact span F1 | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| Candidate | 0.02080197 | 0.62238459 | 0.15360936 |
| Step0051 joint interface | 0.00820057 | 0.26437093 | 0.22174048 |
| Current recurrence | 0.06805485 | 0.64917310 | 0.28710570 |
| Multi-resolution recurrence | 0.05643542 | 0.66274031 | 0.26557136 |

Candidate sufficient statistics match the scorer: exact-span precision
`0.017435`, recall `0.025780`, 76 true spans and 4,359 predicted spans;
B-cubed precision `0.557246`, recall `0.704768`; and boundary TP 499, FP 3,455,
FN 2,044, TN 14,463.

## Bootstrap Reconstruction

The reviewer independently reran all 10,000 paired task-cluster resamples with
251 clusters and seed 20260720. Every delta matched the stored JSONL:

- candidate minus current: mean `-0.047430`, 95% interval
  `[-0.059199,-0.036636]`, positive fraction `0.0000`;
- candidate minus multires: mean `-0.035802`, interval
  `[-0.045914,-0.026248]`, positive fraction `0.0000`;
- candidate minus joint: mean `+0.012603`, interval
  `[+0.007819,+0.017686]`, positive fraction `1.0000`.

The mutually exclusive `contradicted-not-adopted` verdict is correct. The
candidate significantly improves the failed joint interface but significantly
loses to both adoption comparators.

## Scorer And Isolation Audit

Candidate temporal instances, Step0051 joint instances, numeric contiguous
runs, and all 20,461 `(step,step+1)` pair mappings have zero mismatches. Every
session has consecutive one-based steps. No scorer correction or rerun is
needed.

Inference has no manifest parameter. The manifest is opened only by the score
subcommand after all predictions exist. Source caches contain no official gold;
their only `stage` field is the candidate's own maintained instance.

## Reporting Must-Fix And Resolution

The initial summary called the boundary input completely free of alternative
labels. The reviewer confirmed that no candidate inventory was injected, but
the complete continuation user prompt contained another retained label as a
substring in 1,211/20,313 calls. Of those, 73 were only shorter-label overlap
inside the active-responsibility text. The unchanged public task and causal
evidence itself naturally contained another retained label in 1,138/20,313
calls (`5.60%`).

This does not invalidate the complete interface comparison. It forbids a
single-factor causal claim about label visibility. The implementation now
materializes zero continuation prompts with the injected inventory marker and
the 1,138 source-evidence mentions separately. The plan/full report preserve
the distinction. Cached model outputs were unchanged.

The first cache-only summary refresh overwrote inference wall time with summary
reconstruction time. The evaluator now preserves `inference_wall_seconds` and
separately records `summary_regeneration_wall_seconds`. Raw summaries again
retain the observed preflight `21.169971` seconds and full `1433.672988`
seconds; regeneration takes about one and two seconds respectively. No model
output, metric, bootstrap row, or verdict changed.

## Completed Diagnostics

The original operation-triplet `A -> B -> A` count was 1,605; this means the
middle responsibility occupies exactly one operation. Collapsing operations to
temporal stages gives 2,808 responsibility-sequence `A -> B -> A` returns.

The plan's non-adjacent-return diagnostic is now explicit:

- 3,348/3,954 changes return to a responsibility seen earlier in the same
  trajectory;
- 606 changes first enter a previously unused responsibility.

These definitions and counts are now materialized in the raw summary and
reports. They do not change metrics or verdict.

## Scientific Boundary And Verdict

The only positive mechanism statement is that the complete same-operation
two-stage interface removes the joint grammar's near-all-switch behavior and
improves flat-stage partition fidelity over Step0051. It cannot prove causal
independence, absence of all alternative-label text, label accuracy, or general
LLM task decomposition ability.

The experiment does not validate:

```text
concrete task -> nested subtask -> phase/strategy
              -> semantic action -> operation object -> result
```

It is flat-stage development evidence only. Reject the candidate, keep the
recurrence mechanism, preserve thesis/RQs/story, and do not put this negative
mechanism result in the positive paper.
