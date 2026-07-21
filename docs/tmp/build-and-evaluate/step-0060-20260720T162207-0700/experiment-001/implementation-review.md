# Result-Grounded Task Stack — Implementation Review

## Scope

The implementation review covered
`script/rq3_result_grounded_task_stack_eval.py`, the complete public
ToolSandbox source materialization, both real preflights, cache recovery, the
Step 0059 comparison, recurrence mapping, all standard scorers, and the
scenario/task-cluster bootstraps. Reviewers explicitly applied
`research-experiment-design` and did not edit the implementation.

## Initial Review Rounds

The first independent pass found and corrected the following must-fix defects
before the initial full run:

1. planned command lines did not match the CLI;
2. assistant-only natural-language outcomes were incorrectly visible to
   ToolSandbox OPEN;
3. candidate and baseline completion prompts treated abandonment as a positive
   completion although the public TED target records only positive progress;
4. the Step 0059 baseline incorrectly displayed an invented `done_when`;
5. cache resume did not bind current inputs or replay request/state hashes;
6. CodeTrace scorer expected the wrong Step 0059 field name; and
7. a proposed lexical phase filter contradicted the registered simple
   algorithm and was removed in favor of descriptive diagnostics.

The repaired r6 implementation regenerated the complete visible source,
withheld assistant-only outcomes from OPEN, used success-only completion for
both candidate and baseline, replayed every cached transition from input and
request hashes, and passed two real preflight/resume runs. The reviewer returned
**APPROVE — zero must-fix**.

## Invalid r6 Full Run And Leakage Discovery

The first 3,551-trajectory r6 ToolSandbox full run completed and its metrics
were exactly reproducible, but independent raw-result review found a blocking
leak: `close_prompt()` projected the active stack semantically but serialized
the raw active child leaf. That raw object contained `instance`, whose value
included the complete model/persona/trial/scenario sequence ID. The defect
affected 1,137 child-active CLOSE requests across 869 trajectories and made the
r6 candidate run invalid. Its inference summary's assertion that model/persona
was hidden was therefore false.

The in-progress r6 CodeTrace full run was stopped. A first Ctrl-C stopped the
foreground wait but left PID `2776171` and its executor threads running. The
reviewer detected that process through `/proc`; it was then terminated and
verified absent before any repaired full run began. Existing r6 candidate
caches remain isolated as invalid history.

## Minimal r7 Repair And Review

The r7 correction changes one causal projection only:

```text
raw child frame {instance, label, done_when}
    -> CLOSE-visible {label, done_when}
```

OPEN, the state machine, model, decoding, workload, metrics, and baselines are
unchanged. Candidate and baseline cache revisions and filenames were split:

- candidate: `semantic-close-projection-r7`;
- Step 0059 baseline: `fresh-causal-source-r6`.

This allowed the repaired ToolSandbox candidate to reuse all 3,551 independently
validated r6 baseline caches and their 9,485 turns without repeating baseline
inference. Repaired runs used distinct `toolsandbox-full-r7` and
`codetrace-full-r7` directories.

Independent review verified that ToolSandbox's 8/8 preflight OPEN requests and
2/2 real CLOSE requests, and CodeTrace's 84/84 OPEN requests and 59/59 real
CLOSE requests, contained neither an internal `instance` key nor the complete
sequence ID. Cache replay, mixed r7-candidate/r6-baseline reuse, CLI execution,
and scorer smoke checks passed. The reviewer returned **APPROVE — zero
must-fix** for repaired full execution.

## Malformed-I/O Repair

At 395/405 completed CodeTrace sessions, one OPEN response exhausted the fixed
128-token output allowance and ended as truncated JSON. This was treated as
malformed I/O, not a semantic transition. The same prompt and grammar received
one 256-token retry; the discarded response hash, parse error, and original
token allowance are stored in the call record. No completed session was rerun,
and the final inference summary records exactly one malformed-I/O repair.

## Final Implementation Verdict

The authoritative implementation is r7. The r6 candidate result is invalid and
must never enter scoring or paper evidence. The r6 Step 0059 baseline caches are
valid, input-bound, request-bound, state-replayed, and intentionally reused by
r7. Step 0060 changed no shared skill, production Rust component, paper file,
branch, or paper story; concurrent changes outside this research repository are
not attributed to this step and were not touched.
