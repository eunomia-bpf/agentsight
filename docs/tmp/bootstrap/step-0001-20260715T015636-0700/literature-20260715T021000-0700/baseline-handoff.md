# Baseline And Experiment Handoff

Timestamp: 2026-07-15T02:22:00-07:00
Owner target: `research-experiment-design`

## Fixed paper questions

This handoff does not alter RQ1--RQ4. The first candidate empirical loop is RQ1
because join fidelity can invalidate the artifact's central mechanism and is a
prerequisite for every later view.

## Competing positions

1. **Event-plus-Git position:** process events and durable outcomes provide
   complementary, necessary evidence.
2. **Git-sufficiency position:** commits, blame, and existing evolution metrics
   answer the practical questions; event detail is mostly decorative replay.
3. **Event-table position:** fine-grained logs contain the needed evidence and
   visualization/joining adds presentation rather than new capability.

## Required baselines

### Git-only

- Artifact: system Git used through stable plumbing commands.
- Visible information: commit DAG, timestamps, paths, additions/deletions,
  authors, current blame and survival.
- Tuning: rename detection, first-parent versus all commits, time window.
- Protocol: same repository and time interval; no native-event fields.
- Consequence: if it answers the process questions at matched accuracy/time,
  the central event necessity claim is unsupported.

### Native event table

- Artifact: `agent-session` normalized events rendered as a sortable/filterable
  table or JSON inspector.
- Visible information: the full event fields used by the gallery, excluding
  Git joins and coordinated encodings.
- Tuning: same filters and time range.
- Consequence: if it matches task outcomes, the visualization utility claim is
  unsupported even if the join remains useful.

### External formats and tools

- Perfetto Trace Event export for an industrial timeline baseline.
- Gource custom log for animation/poster comparison.
- Hercules or direct Git metric oracle for burndown, ownership, and coupling
  cross-check; citation-only if the stale artifact cannot run fairly.
- RECAP and Githru as closest position/evaluation precedents; do not fabricate
  a runtime comparison when artifacts are unavailable.

## Official external assets

- Local AgentSight Claude/Codex histories spanning multiple dates.
- AgentSight Git repository and its exact commit/rename/blame history.
- SWE-bench public experiment trajectories for later RQ2 generalization.
- Will It Survive? replication package and CLSA Zenodo package for survival
  protocol comparison, subject to license and size preflight.
- Perfetto browser UI and Trace Event JSON.
- Gource 0.56 and Hercules v10.7.2 official artifacts.

## RQ1 candidate preflight

1. Extend the event IR with repository-relative exact paths and edit-size fields
   while retaining coarse `path_groups` for privacy-preserving summaries.
2. Export all AgentSight sessions in a declared multi-day interval.
3. Parse rename-aware Git changes over the same interval.
4. Classify each file event as exact/interval/ambiguous/unmatched and each Git
   change as observed/unobserved; separately mark current path/line survival.
5. Manually audit a stratified sample of matches and mismatches from raw
   session and Git evidence.
6. Run Git-only and event-only answerability checks for a predefined set of
   questions before building every view.

Preflight success requires contact with real session files and Git history,
non-empty matched and mismatched categories, reconstructable sample evidence,
and no private text in committed outputs. It cannot answer RQ1 until the full
planned interval and audit complete.

## Required measurements

- Discovery and parse coverage by agent/session/date.
- Exact path extraction and canonicalization yield.
- Event-to-Git match rate, ambiguity, and mismatch taxonomy.
- Git change coverage by observed events.
- Current survival for matched changes.
- Sensitivity to match windows and rename thresholds.
- Export runtime and size as early RQ4 evidence only after protocol review.

## Failure and repair rules

- If exact paths are unavailable, do not infer file-level attribution from
  `path_groups`; repair the parser or report the limitation.
- If timestamp matching is ambiguous, retain candidate sets/confidence and do
  not select a single author/commit silently.
- If privacy-safe evidence cannot be committed, keep raw results local and
  publish only aggregate/sanitized artifacts with reconstruction commands.
- If Git-only wins, preserve the result and reduce view-specific implementation
  only after the scientific contract is explicitly reconsidered in BOOTSTRAP.
