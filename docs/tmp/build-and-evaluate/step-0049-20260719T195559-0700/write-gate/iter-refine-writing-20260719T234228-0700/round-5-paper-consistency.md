# Round 5 — Paper Consistency

**Started:** 2026-07-20T00:12:53-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `check-terminology-infoflow`  
**Scope:** paper consistency  
**Completed:** 2026-07-20T00:25:25-07:00  
**Status:** complete

## Contract and anchors

- Exact thesis and exactly four RQs are immutable.
- Design and Implementation are authoritative for model/mechanism.
- Evaluation tables and admitted result summaries are authoritative for numbers.
- Abstract, Introduction, captions, RQ answers, Scope, and Conclusion must agree
  with those anchors.
- The Qwen trial is negative research history and cannot enter the positive
  paper.

## Method

A fresh reviewer reads the complete paper and cross-checks component names,
interfaces, data flow, construction modes, metrics, numerical claims, table and
figure captions, and paper-to-artifact anchors. Findings are classified as
blocker, major, or minor. Only verified local consistency repairs are eligible;
style normalization and scientific rewriting are out of scope.

## 1. Inconsistencies found

- **Blocker:** the RQ1 prose attributed top-10 overlap 7/10, Spearman 0.623,
  and the network 8th/93rd ranks to time versus tokens. The authoritative R225
  artifact measures prompt-span duration versus system-effect count.
- **Major:** the Design overview assigned system-effect joining to
  source-specific ingestion inside `\sys`, while Figure 1 and Implementation
  assign the scoped join to AgentSight and its adapter.
- **Major:** `docs/design.md`, `docs/implementation.md`, and
  `docs/evaluation.md` still described coarse recurrence and 0.649 as the
  current mechanism despite Step 0049's multi-resolution 0.663 result.
- **Minor:** RQ2's target-blind sentence failed to distinguish validation labels
  used for HINTBench field-order selection from unseen test targets.
- **Minor:** sessions and spans were called “not hierarchy levels” rather than
  “not fixed hierarchy levels.”
- **Minor:** the approximate 9.8K Rust LOC claim lacked a stable counting
  boundary.

## 2. Why each mattered

The first conflict assigned real numbers to an unmeasured comparison. The
second moved ownership across the system boundary. The stale sibling documents
could cause future agents to restore the superseded coarse mechanism. The
minor issues obscured test-label isolation, selectable hierarchy semantics, and
an unstable artifact-size fact.

## 3. Fixes

- Restored R225's actual comparison: prompt-span duration versus system-effect
  count, with the same 7/10, 0.623, and 8th/93rd values and the idle/user-wait
  qualification.
- Stated that source capture and adapters preserve AgentSight's link, while
  operations carry inherited fields into AgentProf projection and folding.
- Scoped the RQ2 isolation statement to test targets and explicitly retained
  the separate validation-snapshot selection.
- Changed sessions/spans to optional, not fixed, hierarchy levels.
- Removed the unstable LOC count without removing any implementation content.
- Updated only current-state passages in `docs/design.md`,
  `docs/implementation.md`, and `docs/evaluation.md` to the Step 0049
  mechanism and 0.662740 result. Coarse 0.649173 remains explicitly identified
  as predecessor/history and comparator.

## 4. Verified passes

- Exact thesis and exactly four RQs are stable.
- Step 0049 mechanism agrees across paper, implementation, and result report:
  detail continuity can remove but not add a coarse boundary; incomplete detail
  falls back to coarse.
- CodeTrace 0.782/0.575/0.663, coarse 0.649, raw 0.541, +0.014,
  interval [0.009,0.018], and four-framework direction agree.
- OSWorld exact fallback and 0.680 boundary / 0.786 ordinary B-cubed F1 agree.
- RQ1 capture/join, RQ2 MAP, RQ3 tag/backend, and RQ4 time/RSS values agree with
  inspected authoritative records.
- No Qwen negative evidence entered the paper.
- Official build: 9 pages; complete Conclusion on page 7; references only on
  pages 8--9; no undefined citation/reference or overfull box; citation-command
  count 62.
- No writing/review Git operation was performed.
