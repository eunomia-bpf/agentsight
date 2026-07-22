# Case-study protocol 1: AgentCap review profiles

Timestamp: 2026-07-22T00:38:00-07:00
Status: fixed before focused pprof queries and paper interpretation

## Scope

This many-session collection uses four complete real AgentCap Codex review sessions already selected
in Step 0064: R024 evaluator-backed replay, R025 checker ablation, R035 gateway
mismatch analysis, and R081 top-conference evidence. They contain 326 source
operations. The current root Agent read every indexed operation summary and
assigned sparse stable-ID marks; no regex or source-field transition selected a
semantic boundary. The operation-name pool is shared across the four sessions.

No individual review session is treated as a case study by itself. This
protocol was written after the implementation smoke query established that
the pprof was readable and conserved all 326 operations, but before focused
queries, selection of case findings, or paper prose. It is therefore a fixed
case-analysis protocol, not a blind preregistration.

## Fixed user questions

1. **Effort allocation.** Within each review task, which semantic operations
   consume the most recorded operations?
2. **Review-to-fix evolution.** After an initial review reports a problem, how
   much work moves into fix verification, and which verification operations
   repeat across tasks?
3. **Conclusion path.** Which paths culminate in a blocking or accepting review
   conclusion, and can the profile distinguish expensive evidence gathering
   from the small conclusion-bearing operation?
4. **Cross-task recurrence and exceptions.** Which review operations aggregate
   across all four tasks, and which deep paths expose task-specific exceptions
   that would disappear in a flat tool/action profile?

## Evidence and interpretation rules

- Use only the generated standard pprof and stock `go tool pprof` queries.
- Report operation counts, not time or token cost; this input does not authorize
  a latency or token claim.
- A shared display name denotes deliberate Agent canonicalization through one
  operation-name pool. It is product evidence that aggregation works, not an
  independent accuracy score for semantic identity.
- The case may demonstrate answerability and expose concrete paths. It cannot
  validate nested-boundary accuracy, user utility, or the automatic backend.
- Retain all four sessions and all 326 operations. Do not select a favorable
  prefix or drop an inconvenient path.

## Planned queries

1. Whole-profile `top` and `tree`.
2. Per-task focus for R024, R025, R035, and R081.
3. Focus on `verify_requested_fixes`, `identify_blocking_finding`, and
   `report_review_conclusion`.
4. Focus on task-specific exception paths: evaluator deviations, stale
   documentation, test-environment diagnosis, and reference-corpus validation.
