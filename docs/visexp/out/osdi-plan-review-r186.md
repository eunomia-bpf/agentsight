# R186 OSDI Plan Review

Date: 2026-06-15
Reviewer: Sagan subagent, read-only
Stage at update: supplement / experiment-design
Source/command: OSDI experiment-plan review over `docs/visexp/RESEARCH_PLAN.md`,
`docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/STATE.md`,
`docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/EXPERIMENT_AUDIT.md`,
`docs/visexp/out/weak-accept-gate-r184.json`,
`docs/visexp/out/osdi-gate-review-r185.md`, and
`docs/visexp/paper/main.tex`
Completeness: complete for plan review; not C5/C6 outcome evidence

## Verdict

Maturity: Level 3 conference-paper mechanism evidence. Not OSDI weak accept.

The mechanism story is credible: semantic folded stacks over real local
Codex/Claude histories, R131 semantic-axis ablation, R114 fixed-suite exact
lineage, R180 small-model syntax/stability, and R160/R170 artifact mechanism
checks are useful. R184 still blocks weak accept because C5 has no real
participant responses and C6 has no independent human labels.

## Highest-Risk Unsupported Claim

C5 developer utility is the highest-risk unsupported claim. The current
`user-task-results.json` remains `participant_results_empty` with
`c5_supported=false`; packets, preregistration, and scorer are protocol
evidence only.

C6 tag adequacy is the next blocker. R124 has 0 human labels, and R180
syntax/latency/stability cannot count as semantic adequacy.

## Priority Decision

Priority order after this cleanup:

1. Run a real R142 five-participant developer forensic pilot using the frozen
   preregistration and P01-P05 packets.
2. Collect R124 human tag-adequacy labels in parallel or immediately after the
   R142 pilot.
3. Run R151 only after R142 passes response-contract and pilot checks.
4. Defer target-specific C4 network hardening and R160/R200 artifact polish
   until the C5/C6 human-evidence gate is no longer empty.

Subagent review, LLM-filled labels, author mock responses, and placeholder rows
cannot count as C5/C6 evidence.

## Required Plan Cleanup

The review identified four plan-cleanup issues before human collection:

| Issue | Review finding | Current resolution |
|-------|----------------|--------------------|
| Next-action ordering | `STATE` already put R142 first, while earlier plan text put R124 first. | Revised `RESEARCH_PLAN` and `FOLLOWUP_PLAN` to use R186 review, then R142 pilot, then R124 labels, then R151. |
| Stale response warning | Older `FOLLOWUP_PLAN` text said not to collect responses with the current protocol. | Replaced with: R142 pilot collection may start after R186 cleanup; R151 paper-run responses are blocked until R142 passes. |
| RQ4 baseline wording | RQ4 still mentioned span-duration as a current compared baseline. | Reworded RQ4 to use `event-count-proxy` as the current baseline; true span-duration is optional only if timestamp-derived and preregistered separately. |
| Numbering / tracker handoff | Next-gate numbering and tracker handoff were not explicit enough. | Added claim-to-experiment map, system-under-test model, run order, tracker handoff, and R186 row. |

## Execution Gate

After the cleanup above, it is acceptable to start R142 pilot collection. This
does not upgrade C5: pilot evidence must remain labeled as pilot until the
existing scorer reports a valid result, and paper-scale C5 requires the R151
gate.

R184 remains authoritative for weak accept: until both C5 and C6 pass their
existing human-data scorers, the overall status stays `not_weak_accept`.
