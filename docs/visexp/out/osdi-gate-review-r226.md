# R226 OSDI Gate Review After R225

Status: `reviewed_not_weak_accept`

Reviewer: read-only subagent using senior OSDI reviewer criteria.

## Verdict

Not weak accept. R225 materially improves the previous missing-duration-baseline
gap by adding a concrete prompt wall-clock duration baseline, but it does not
provide true workflow span-duration, active runtime, or tool/LLM start-end spans.
R219 correctly keeps `weak_accept_supported=false` because C5 still has 0
participant responses and C6 still has 0 final adequacy labels.

## Findings

| Severity | Finding | Disposition |
|---|---|---|
| Blocker | C5/C6 remain missing: no real participant outcomes and no independent human adequacy labels. | Still open; cannot be fixed without real returned R142/R124/R190/R203 evidence. |
| Major | R225 is only a prompt wall-clock baseline, not a full span-duration workflow baseline. | Accepted; paper, artifact, tracker, and summary explicitly say wall-clock interval, possible idle/user-wait time, no active runtime, no true tool/LLM spans. |
| Major | Initial R225 comparison appeared to compare duration from 226/325 sessions with full R170 effect folded profile. | Fixed after review: R225 now uses a stronger session identity, reconstructs covered prompt-index system-effect weights from the same R170 `agentflame.json`, and checks expanded effect totals against `semantic-system.folded.txt`. Current artifact reports 324/325 sessions with prompt spans and 183,714/183,714 covered effects. |
| Minor | Generic design wording could imply duration is supported before the R225 boundary appears. | Partially accepted; R225/RQ4 wording is now explicit, but broad design prose should still be tightened in a future writing pass. |

## Current Gate

R225 strengthens the mechanism/evaluation package but does not change the
acceptance gate:

- C3/RQ2: stronger mechanism evidence with projection tradeoff and prompt
  wall-clock duration baseline.
- C5/RQ4: unsupported until real developer responses are collected and scored.
- C6/RQ5: partial syntax/stability only until human adequacy and merge/promotion
  labels are collected and scored.
