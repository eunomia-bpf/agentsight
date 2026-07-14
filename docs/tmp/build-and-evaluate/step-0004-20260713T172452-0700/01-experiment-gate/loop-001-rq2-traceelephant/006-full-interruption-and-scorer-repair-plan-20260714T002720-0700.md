# FULL Interruption And Scorer Repair Plan: TraceElephant RQ2

**Node:** 006
**Timestamp:** 2026-07-14T00:27:20-07:00
**Phase / step / gate / loop:** BUILD_AND_EVALUATE / 0004 / EXPERIMENT / 001
**Parent:** [real preflight and review](005-real-preflight-and-review-20260713T191114-0700.md)
**Status:** FULL execution interrupted at scorer entry; minimal scorer-only repair proposed; no scientific result

## Fixed Scientific Contract

The selected paper-level question remains verbatim:

> **RQ2: Does Profiler Output Correspond to Real Problems?**

The tested hypothesis, thesis, four RQs, primary AgentProf-versus-raw-action
comparison, workload, model, prompts, semantic fields, operation construction,
score, metrics, controls, positive criterion, and paper story are unchanged.
This repair may normalize malformed official scorer annotations. It may not
drop a trace, inspect a partial result, retune the mechanism, change a target
to favor either method, or revise the paper claim.

## Completed FULL Work Before The Interruption

The approved FULL command ran without protocol changes. Before scorer entry it
completed all target-blind and profile-producing work:

- 220 / 220 terminal official All-at-Once localizer records;
- 405 / 405 terminal semantic tag batches;
- 5,960 / 5,960 projected operations across all five official cells;
- the real `agentpprof 0.2.37` AgentProf and exact-raw primary paths;
- all declared non-oracle controls available before scorer entry;
- exact independent reconstruction for both primary real-binary paths; and
- 200 / 200 target-blind matched-semantic permutation profiles.

The materialized method index reports all 5,960 operation identifiers, 200
permutations, and `true` exact reconstruction for both primary conditions.
The compressed permutation index contains exactly 200 terminal records.

No point metric, permutation p-value, bootstrap interval, scientific verdict,
or paper result was produced or inspected. The failure occurred before those
quantities were computed.

## Terminal Failure

The FULL driver exited with status 1 when the isolated scorer loaded the first
malformed official target:

```text
magentic-runs-assistant-bench/
assistant_bench_task_26_gpt_4o_r6uatbdru2pa:
invalid mistake_step 'none'
```

The adapter correctly refused to guess. Its approved loader accepted only an
integer or an all-digit string. A complete audit of all 220 released
`trace_metadata.json` files found exactly two non-canonical step fields:

| Trace | Released `mistake_agent` | Released `mistake_step` | Other released annotation |
|---|---|---|---|
| Magentic-One / AssistantBench task 26 | `WebSurfer` | `none` | `mistake_reason` uniquely says `At Step 11, WebSurfer ...` |
| Magentic-One / AssistantBench task 28 | `Coder` | `Step 36` | no competing step number in `mistake_reason` |

For task 26, projected step 11 exists uniquely and its source component is
`WebSurfer`, matching the released agent. For task 28, projected step 36 exists
uniquely but its source component is `Orchestrator`, not the released `Coder`;
the complete released trace contains no `Coder` step. This is an official
annotation inconsistency rather than a missing operation or an adapter
off-by-one. The official TraceElephant evaluator converts both fields to
strings and scores agent and step independently with substring comparison; it
does not validate that the named agent emitted the named step.

## Minimal Repair Proposal

Do not edit the released dataset. Repair only the isolated scorer loader and
its audit output:

1. Accept the already approved integer and all-digit-string forms unchanged.
2. Accept a full-string, case-insensitive `Step <positive integer>` form and
   record normalization source `mistake_step_step_prefix`. This recovers task
   28 as released step 36 without using either method's output.
3. Only when `mistake_step` is the exact case-insensitive sentinel `none`,
   search the released `mistake_reason` for case-insensitive whole-token
   `Step <positive integer>` mentions. Require exactly one unique number and
   record normalization source `mistake_reason_unique_step`. This recovers
   task 26 as released reason step 11. Zero or multiple unique numbers remain
   an execution error.
4. Preserve the raw released step value, normalization source, and released
   reason in scorer-only `targets.jsonl` and `target-mapping.json` so the two
   deviations are independently auditable.
5. Continue to require exactly one projected operation at every normalized
   step. An absent, duplicate, non-positive, or out-of-range target remains
   `INVALID` before any metric.
6. Treat source-component equality with released `mistake_agent` as a reported
   annotation-consistency diagnostic rather than a validity condition for the
   step-localization metric. Report the exact mismatch count and rows. The
   official task defines agent and step labels independently, and the primary
   metric evaluates the released decisive step, not agent classification.
7. Keep official responsible-agent accuracy as a separate descriptive metric.
   Do not rewrite the task-28 agent, infer a substitute component, or use the
   mismatch to change any operation, group, score, or target step.

This repair retains all 220 real failures and their released step evidence. It
is stricter than the official substring scorer about integer normalization and
unique operation mapping, while avoiding the scientifically unrelated claim
that the released agent string must equal the actor at the independently
released target step.

## Repair Validation Before Resuming FULL

After implementation, rerun only the isolated scorer until target loading and
mapping finish. Before accepting metrics, independently verify:

- exactly 220 targets and 220 unique target mappings;
- exactly 218 direct numeric normalizations, one `Step 36` normalization, and
  one unique-reason `Step 11` normalization;
- every normalized target is in range and maps to exactly one operation;
- task 26 maps step 11 to `WebSurfer`;
- task 28 maps step 36 to `Orchestrator` while retaining released agent
  `Coder` as the sole reported component mismatch;
- no scorer annotation appears in operations, profiles, or permutation input;
- the existing 5,960-operation method index and all 200 permutation records
  remain byte-for-byte reusable; and
- no model call or target-blind profile is rerun.

A fresh independent reviewer must review this proposal and the implementation
against `research-experiment-design`, the approved plan, raw released records,
official evaluator, and existing artifacts. Any `MUST-FIX` concern is repaired
and re-reviewed before the scientific result is interpreted.

## Independent Proposal Review

A fresh read-only Codex reviewer independently read the complete
`research-experiment-design` skill, user instructions, approved plan,
preflight report, this proposal, official evaluator, both anomalous raw
records, the adapter, and the materialized target-blind artifacts. The normal
collaboration subagent interface had exhausted its thread quota, so the review
used an ephemeral local Codex process with a read-only sandbox. It made no
repository edit, model call, or scientific-metric query.

The reviewer returned **PASS** with zero must-fix findings. It independently
confirmed that:

- the 220-label population contains exactly 218 digit strings, one `Step 36`,
  and one `none` sentinel;
- task 26 has one unambiguous reason-derived step 11 whose actor matches;
- task 28 directly releases step 36, that step exists uniquely, and its content
  manifests the released sorting error even though its source actor is
  `Orchestrator` and the independent released agent label is `Coder`;
- the official evaluator treats responsible agent and decisive step as
  separate outcomes;
- both methods receive the same operation, component, target step, and scorer
  treatment, so retaining step 36 gives neither method a special advantage;
- all 5,960 target-blind operations, both exact primary profiles, and all 200
  matched permutations are complete and reusable; and
- no scorer key appears in target-blind artifacts and no FULL scientific
  metric or verdict exists.

The reviewer requested one implementation safeguard already consistent with
this proposal: add a target-validation-only early exit so the 218/1/1
normalization distribution, 220 unique mappings, and sole component mismatch
can be checked before any point metric, permutation p-value, bootstrap, or
verdict is computed.

## Resume Decision

The scorer repair was implemented exactly as proposed, including the requested
`--validate-targets-only` early exit. Validation completed with 220/220 valid
unique mappings, normalization counts 218/1/1, one reported component mismatch,
no metric or bootstrap output, and unchanged hashes for all target-blind FULL
inputs.

A second fresh read-only Codex reviewer then audited the implementation, raw
anomalies, official evaluator, target artifacts, control chronology, scorer-key
isolation, and validation-only control flow. It returned **PASS** with zero
must-fix findings. It confirmed that no anomalous trace is hard-coded, both
methods share the same normalized target, task 26 maps to step 11, task 28 maps
to step 36 while preserving the independent `Coder` annotation as a diagnostic,
and the validation-only path returns before downstream analysis. The reviewer
made no edit, model call, or scientific-result query.

The FULL experiment remains `INCOMPLETE`, not scientifically negative, only
until the approved isolated scorer runs over the complete target-blind
artifacts and finishes the 10,000 paired bootstrap replicates. No paper edit is
authorized by this node.
