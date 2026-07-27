# Independent Plan Review

## Round 1

### Blockers

1. The vendor-native human-message rule was not frozen precisely enough.
   Claude, Codex, and Gemini can retain duplicate or synthetic representations,
   and the projection contains root/user plus subagent streams. The plan must
   name the authoritative record, fallback, deduplication, wrapper exclusion,
   and root-stream restriction for every vendor. Project-attributed membership
   remains 551 rows; overall totals need a 550-unique-root sensitivity.
   `prompt_index` is only a per-source-stream reconciliation field.
2. Follow-up, explicit interruption, immediate redirection, and wall-clock
   quantities were too easy to over-name. Follow-up and source-native abort
   markers must be separate. Immediate action change must use adjacent actions
   from the same native root source/stream, with tool and path change reported
   separately and missing paths explicit. Without a turn-complete oracle,
   `last activity -> next prompt` is a post-activity inactive gap, not observed
   human attention or proven Agent waiting; `prompt -> last activity` is only
   an activity/work envelope.
3. The guidance-density formula and RQ1 outcome denominators were incomplete.
   Grouping on messages/actions mechanically relates the group to action
   volume, so the analysis must report actions, raw mutations, and mutations
   per action together. Zero-mutation sessions remain through a left join.
   Reuse and validation use non-delete eligible mutations and preserve
   observed, competing, and censored outcomes in the denominator.

### Non-Blocking Suggestions

- Freeze the conversational-turn definition and do not turn vendor-dependent
  assistant-message granularity into one autonomy score.
- Separate explicit approval request/response events, permission-policy
  configuration, and visible Agent question tools; report vendor coverage.
- Assert 551 project-attributed memberships, 181,303 event rows, 13,906
  mutation rows, and the full project × vendor grid. For strata with fewer
  than ten sessions, show individual observations and do not summarize a
  direction.

### Verdict

Revise before execution. The analysis is independently valuable supporting
evidence about mixed initiative and author-involvement confounding; it needs no
additional dataset or baseline.

## Resolution

The current plan and implementation adopt all three blocking repairs:

- Claude `type=user`, Codex `event_msg/user_message`, and Gemini
  `messages[].type=user` are authoritative; explicit fallbacks and synthetic
  exclusions are vendor-specific, subagent sources are excluded, and
  source-native prompt IDs plus timestamps deduplicate records.
- Follow-up and explicit abort counts are separate. Immediate action change is
  restricted to the same native root source file and stream. Time metrics are
  named activity envelope and post-activity inactive gap; actual human
  wall-clock attention remains unobservable.
- Guidance density is frozen as follow-up messages per 100 projected Agent
  actions. Action volume and mutation density accompany raw mutation counts;
  zero-mutation sessions remain; non-delete eligible reuse/validation rows
  retain observed, competing, and censored outcomes.

The main report will make no direction claim for a project × vendor stratum
with fewer than ten sessions.

## Follow-Up Verdict

**APPROVED.** The reviewer confirmed that the vendor-native record and
deduplication rules, follow-up/interruption/same-stream transition separation,
inactive-gap naming, frozen guidance-density formula, zero-mutation left join,
and RQ1 outcome denominators resolve the three blocking concerns. The execution
and completion rules are sufficient.
