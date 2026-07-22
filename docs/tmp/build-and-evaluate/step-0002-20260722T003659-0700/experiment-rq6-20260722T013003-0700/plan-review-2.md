# RQ6/F9 Plan Review — Round 2

**Reviewed:** 2026-07-22  
**Scope:** follow-up review of the revised coverage-only plan; no implementation
or result review  
**Verdict:** **PASS**

## Decision

The revised plan resolves the Round-1 validity blockers.  It no longer treats
the three visible signals as one exposure, no longer labels absence of a signal
as unexposed, and no longer estimates artifact, validation, rework, survival,
or harness effects from source-incomparable sessions.  It uses only fields
recoverable from the frozen RQ1 export, explicitly records the missing Skill
name/model/config/external-instruction fields, and makes the absence of the
forest plot the preregistered stop rather than an implementation failure.

This is executable and scientifically honest as a **source-coverage audit and
RQ6 stop decision**.  It is not evidence that a skill or harness is helpful,
harmful, used, or unused.  No external baseline, human label, LLM judge, causal
adjustment, or bootstrap is needed for the admitted question.

## Round-1 closure

| Round-1 blocker | Revised-plan disposition | Judgment |
|---|---|---|
| Skill name/model/config unavailable from frozen input | Declared unavailable; no re-export or inference | Closed |
| Heterogeneous events pooled as binary exposure | Three non-equivalent source kinds retained separately | Closed |
| `no event` mislabeled as unexposed | Renamed `no_observed_source_event` with explicit limitation | Closed |
| Incomparable anchors, horizons, and censoring | No outcome or temporal-effect comparison is attempted | Closed |
| Parallel sessions and confounded session bootstrap | No outcome attribution, effect, or bootstrap is attempted | Closed |
| Unfrozen artifact/validation/rework estimands | Removed from this experiment | Closed |
| Forest plot implies a comparable treatment effect | Replaced by coverage proportions, counts, and occurrence heatmaps | Closed |
| Missing command, outputs, checks, and decision | Frozen command, ordinary outputs, reconciliation, and unconditional stop | Closed |

## Required implementation interpretations

These points follow directly from the approved definitions and should be
checked in result review; they do not require another plan round.

1. **Rename endpoints.** For `instruction_mutation`, apply the exact basename
   rule to both the rename destination `path` and `previous_path`.  A rename
   away from `SKILL.md`, `AGENTS.md`, or `CLAUDE.md` is still an instruction-file
   mutation.  Emit one signal row per source event/file lineage rather than
   double-counting when both endpoints qualify.
2. **Action-order semantics.** The 60 equal-count bins describe position in a
   project's merged native action order.  They are not equal wall-clock bins,
   do not measure duration, and by themselves do not diagnose calendar-time
   separation.  First/last timestamps may report calendar span separately.
3. **Session denominator.** Derive the denominator from the unique session IDs
   in each frozen project's admitted event timeline and reconcile it to the
   frozen `session_count`.  Do not silently substitute candidate or parsed
   session counts.
4. **Source identity.** Verify every signal against the frozen
   `RepositoryEvent.id`; report native `source_call_id` availability and use it
   when present.  A missing optional native call ID is coverage unknown, not a
   reason to invent an ID or discard the event.
5. **Status and zeros.** Keep status on `skill_tool` events exactly as exported.
   Instruction-file actions exist only where the projection retained a file
   effect.  A zero cell in the count/heatmap is an observed absence under the
   exact frozen rule; missing fields and unavailable outcome families remain
   visibly N/A rather than zero.
6. **Non-exclusive accounting.** Session proportions for the three source
   kinds may sum above 100%.  Reconcile raw signal rows, unique sessions, and
   project/vendor/status tables so every plotted numerator can be regenerated
   from `rq6-observed-events.csv`.
7. **Figure language.** Title and caption F9 as source-signal coverage, not
   configuration association or harness exposure.  Preserve the printed
   `association analysis stopped` notice and the unavailable-field list in
   both PDF and PNG.

## Completion and paper decision

A full run is complete when frozen input hashes match, every admitted event and
session reconciles, all signal rows pass the exact Tool/path rules, the CSVs
regenerate F9, and an independent result review verifies the counts and stop
language.  Any observed density or heterogeneity remains a coverage fact.

The paper-facing decision is already fixed: RQ6 has insufficient native-field
coverage in this frozen corpus for a valid skill/harness association analysis.
F9 may document that negative measurement boundary.  Future work may enrich
the source export and then preregister a separate association or controlled
experiment, but this run must not turn its coverage counts into process-quality
claims.

