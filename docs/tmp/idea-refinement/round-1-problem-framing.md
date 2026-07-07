# Round 1 — Problem Framing

**Date:** 2026-07-07
**Paper:** docs/agentpprof-paper/main.tex (English ACM sigconf)

## What was checked

Problem framing against idea-quality-checklist.md Section 1:
- Concrete painful consequence
- Root cause vs. symptoms
- Multi-dimensionality
- Problem felt before solution
- Common problems (single-dimension, straw-man, scope creep)

## Findings (from subagent)

1. **Single-dimension framing (Important):** Intro ¶1 frames problem around cost/budget attribution ("which categories of work consume the most tokens", "aggregate cost distribution") but RQ2 evaluates failure, safety, quality, redundancy. Failure/safety barely mentioned in problem setup.

2. **Straw-man risk (Important):** ¶4 dismisses Datadog/Laminar in two sentences without explaining the structural reason they can't do resource attribution. Reviewers familiar with these tools may feel their capabilities are undersold.

3. **Abstract front-loads solution (Minor):** Only 2.5 sentences of problem before jumping to "two abstractions" and implementation details. Problem doesn't breathe.

4. **Requirements gap (Minor):** R1-R3 map to heterogeneity and aggregation but don't cover the failure/safety/quality dimension that RQ2 evaluates. Gap between requirements and evaluation.

5. **Absolute scope claim (Minor):** "no existing observability tool folds events across sessions" is too absolute given related work acknowledges Datadog/Laminar take steps.

## What was changed (before → after, with line numbers)

### 1. Intro ¶1 (lines 57-60): Add failure/safety dimensions
- Before: "which categories of work consume the most tokens, where failures concentrate, and how cost distributes across semantic task families."
- After: "which categories of work consume the most tokens, where failures concentrate, which task families trigger safety violations or redundant effort, and how cost distributes across semantic categories."

### 2. Intro ¶2 (lines 63-71): Hedge absolute claim + add failure dimension
- Before: "no existing observability tool folds events across sessions into an aggregate cost distribution"
- After: "no existing observability tool provides full cross-session resource attribution by semantic category"
- Added: ", nor identify which intent categories concentrate the failures" at end of example.

### 3. Intro ¶4 (lines 89-91): Add structural reasoning for Datadog/Laminar gap
- Added: "The gap is architectural: clustering operates at the request level and does not propagate labels to downstream system effects, so failures and costs triggered by a category remain unattributed."

### 4. Abstract (lines 27-30): Add pain sentence before solution
- Added: "The consequence is that failures, safety violations, and wasted effort remain unattributable to the task categories that cause them."

### 5. R2 requirement (line 212): Note that R2 subsumes diagnostic views
- Added: "This subsumes diagnostic views: failure, safety, and quality labels are fields that participate in the same aggregation."

## Remaining concerns

- The abstract is getting long. May need tightening in later rounds.
- No concrete failure scenario in Section 1 (only the cargo-test cost example). Could add a failure-localization scenario but may exceed space.
