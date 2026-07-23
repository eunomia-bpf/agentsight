# Outcome-blind annotation audit — `other-00`..`other-03`

## Verdict: REVISE

This audit read only `backend-instruction.md` and the four assigned batches'
`trace.jsonl`, `annotation.json`, and `backend-report.md`.  It did not read
outcome-side artifacts or modify an annotation.

The data is structurally sound and the annotation is largely outcome-blind,
but the three source-node boundary/name issues below must be corrected.  The
reported `unique stacks` values also need to be reconciled before the reports
can be treated as an auditable materialization record.

## Structural, coverage, and report checks

| Batch | sessions / prompts | annotations | trace nodes / LLM samples | max depth | coarse leaves (>=8 LLM steps) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `other-00` | 28 / 28 | 188 | 1006 / 475 | 4 | 13 |
| `other-01` | 28 / 28 | 164 | 1430 / 687 | 4 | 29 |
| `other-02` | 28 / 28 | 169 | 1636 / 790 | 4 | 36 |
| `other-03` | 28 / 28 | 146 | 1132 / 538 | 4 | 20 |

- PASS: all mandatory session and prompt operations are present (112 each);
  every annotation has exactly `tag`, `parent`, and `next`; all referenced
  IDs exist; `next` is forward; and all child ranges are nested and sibling
  ranges disjoint.  No cycles or dangling non-root parents were found.
- PASS: the maximum depth is 4 in every batch, exactly as reported.  Excluding
  the seeded session-to-prompt edge, there are no unary internal operations;
  no prompt has a flat semantic fan-out.  Counting long leaf spans at the
  validator's apparent threshold (eight LLM samples) reproduces the reports'
  coarse-warning counts exactly: 13 / 29 / 36 / 20.
- PASS: annotation totals and `nodes / samples` in every backend report match
  the assigned files.
- REVISE (report metadata): if `unique stacks` means unique materialized
  `path` arrays, the trace instead contains 52 / 43 / 42 / 28 distinct LLM
  paths (54 / 45 / 44 / 30 across all node kinds), not the reported
  425 / 558 / 575 / 379.  Either recompute this field or document the other
  stack identity used to obtain those values.  The current three permitted
  artifacts do not expose such an identity.

## Outcome-blind and naming review

No added tag directly copies a tool verb (`click`, `fill`, `press`, etc.) or
names benchmark reward, pair side, success/failure, model, or status.  The
shared `recover from failed or repeated interaction` is used on source-visible
errors/repetition in the sampled long traces (for example AssistantBench
Qwen-0's error/CAPTCHA loop and AssistantBench Llama-30's timeout loop), not
as an inferred outcome label.  Terminal source reports use the prescribed
`verify or report task completion` name where appropriate.

The remaining naming concern is responsibility conflation: two catalog-order
spans use `configure and submit the catalog order`, while comparable sessions
correctly use separate `configure the catalog order` and `submit the catalog
order` operations.  This is the same responsibility being segmented/named
inconsistently, and source actions establish a clean boundary.

## Must-fix annotation nodes

1. `llm:workarena__workarena.servicenow.filter-trivial-expenses-and-select-investments-medium-l2__GenericAgent-gpt-4o-2024-11-20:step-0003` (`other-02`)

   It is tagged `verify or report task completion` from steps 3--15, but the
   span opens the filter, constructs the condition, inspects and compares
   expenses, and only then sends the user report at step 15.  Split it into
   source-supported filtering/selection responsibilities and make the report
   a separate terminal leaf.  A completion/report label may not absorb the
   preceding substantive work.

2. `llm:workarena__workarena.servicenow.infeasible-navigate-and-order-development-laptop-p-c-with-reason-l2__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0004` (`other-03`)

   `configure and submit the catalog order` spans item selection/configuration
   at steps 4--5 and the submission click at step 6.  Split at step 6 and use
   the shared existing names `configure the catalog order` and `submit the
   catalog order`.

3. `llm:workarena__workarena.servicenow.infeasible-navigate-and-order-development-laptop-p-c-with-reason-l2__GenericAgent-anthropic_claude-3.7-sonnet:step-0002` (`other-03`)

   The same conflated tag covers item/configuration actions at steps 2--4 and
   the order submission at step 5.  Apply the same split and shared names as
   above.

## Source-level sample (12 multi-step sessions)

The following sessions were inspected against contiguous source reasoning and
tool actions, not benchmark outcomes:

| Batch | session (agent) | source-supported finding |
| --- | --- | --- |
| `other-00` | AssistantBench validation.0 (Qwen) | search -> repeated unexpected-error retry -> provider change -> CAPTCHA loop; recovery hierarchy is supported. |
| `other-00` | AssistantBench validation.30 (Llama) | dataset inspection, timeout recovery, index browsing, and final obstruction report have distinct boundaries. |
| `other-00` | AssistantBench validation.20 (Claude) | search, official-price inspection, one timeout recovery, comparison, then a user answer are correctly separated. |
| `other-01` | create-hardware-asset (Qwen) | field population and scrolling-to-locate fields are coherent coarse spans; no outcome inference used. |
| `other-01` | create-problem (Claude) | failed field interaction, lookup navigation, obstruction reports, and dismissal attempt follow the source actions. |
| `other-01` | filter-requested-items-and-order-Apple (Claude) | requested-item filtering, catalog navigation, configuration, and submission are source-distinct. |
| `other-02` | trivial-expenses/select-investments (GPT-4o) | identified must-fix 1: a 13-step filter/analysis span was incorrectly labelled solely as completion/reporting. |
| `other-02` | warranty-expiration lookup (Claude) | filter inspection, interim direct search, and final user answer are distinct; the terminal final report is source-visible. |
| `other-02` | infeasible-create-user (Claude) | user population, save/retry, duplicate reporting, and attempted update are distinguishable without judging feasibility. |
| `other-03` | infeasible-order-laptop (Qwen) | identified must-fix 2: configuration and submit click are separate responsibilities. |
| `other-03` | sort-change-request-list (GPT-4o) | navigation, sorting attempts, repeated user reports, and retries are visible; no external result was used. |
| `other-03` | create-problem (Claude) | module navigation, new-record opening, population, and save each have source-action support. |

## Required recheck after revision

Re-run the annotation validator/materialization after applying the three node
fixes, then update each affected backend report with the validator's exact
`unique stacks` definition and value.  Preserve the outcome-blind rule: use
only source-visible reasoning, action, and visible errors when resegmenting.

## Follow-up re-audit — PASS

This follow-up was limited to the three must-fix nodes above, their affected
annotation/profile schema, and the four reports' unique-stack explanation. It
does not reopen the wider audit.

- PASS: the `other-02` GPT-4o expense span now starts with `filter the expense
  lines` at step 3, changes to `select investments within the budget` at step
  4, and places `verify or report task completion` only at step 15. The
  resulting `next` chain continues legally to the recovery span at step 16.
- PASS: the `other-03` Qwen catalog span now uses `configure the catalog
  order` for steps 4--5 and `submit the catalog order` at step 6 before the
  completion report at step 7.
- PASS: the `other-03` Claude catalog span now uses `configure the catalog
  order` for steps 2--4 and `submit the catalog order` at step 5 before the
  completion-report span at step 6.
- PASS: every affected annotation object has exactly `tag`, `parent`, and
  `next`; all parent/next IDs resolve to trace nodes, all `next` references
  move forward, and the materialized trace leaf agrees with the revised tag.
  The affected report totals are also updated to 171 annotations for
  `other-02` and 148 for `other-03`.
- PASS: all four `operations.pb.gz` files pass gzip validation and are parsed
  successfully by Go pprof. Their unique folded-stack counts are exactly
  425 / 558 / 575 / 376, matching `other-00` through `other-03`
  respectively. Each report now correctly explains that this is AgentPProf's
  identity over the materialized semantic path plus the LLM/tool leaf, not a
  count of unique semantic paths. The latest `other-03` value is 376, as
  expected after the shared-name merge.

The original three must-fix findings and unique-stack reporting concern are
closed under this limited follow-up.
