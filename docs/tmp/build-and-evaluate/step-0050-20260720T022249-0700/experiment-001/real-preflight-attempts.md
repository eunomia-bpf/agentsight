# REAL PREFLIGHT Attempts Before Scoring

No attempt in this report opened the CodeTraceBench stage manifest or any score.

## Attempt 1 — Source Extraction And Exact-Length Output

- The first 188 trajectories reconstructed correctly.
- One released OpenHands variant represented chat content as a list of typed
  text blocks rather than a string. Task extraction stopped rather than falling
  back to a slug.
- After that parser repair, all 405 public archives reconstructed with complete
  operation coverage.
- On the longest selected trajectory, the exact-length assignment grammar
  allowed arbitrary whitespace and the 2,048-token response ended before the
  JSON array closed. Three shorter trajectories completed.
- Repair: preserve the same JSON integer array but disallow whitespace between
  array elements. The failed artifacts remain under external
  `preflight-attempt-1/`.

## Attempt 2 — Approved Full-Trajectory Assignment

- Complete source preparation: 405/405 trajectories and 20,866 operations.
- Actual inference: four complete trajectories, one per framework, totaling 340
  operations; maximum request 10,364 tokens; every operation assigned once.
- The goal planner produced concrete, readable workflow lists. Examples include
  eight responsibilities for constructing a benchmark task and six
  responsibilities for a SWE-agent code repair.
- Source-only behavior diagnostic: the candidate changed assignment on every
  operation in three of four trajectories; the plan-free arm did the same in
  all four. The outputs were deterministic counting/cycling patterns such as
  `0,1,2,0,1,2,...`, not evidence-conditioned segmentation.

## Attempt 3 — Causal Interface And Semantic-Label Validation

- The initial invocation stopped before source access because a local variable
  used for usage aggregation shadowed the HTTP module. Renaming that variable
  repaired only the implementation.
- Complete source preparation again covered 405/405 trajectories and 20,866
  operations without opening stages.
- Two selected trajectories completed causal inference. The next planner was
  correctly rejected because it copied system details and placeholders into
  responsibilities: `file /testbed/src/owlvit_for_object_detection.py`,
  `lines 1-100`, and `your_command_here`. A deterministic replay showed that a
  second selected task would have emitted `test with maze_1.txt`.
- Repair: retain the registered semantic-label rule but make its instruction
  operational: every responsibility begins with a task verb, rewrites paths,
  filenames, line ranges, commands, and placeholders as their task purpose,
  and checks every item before returning. The same rewrite instruction applies
  to plan-free switch labels. Algorithm/cache version advances to v3 so no
  partially completed v2 session is reused.
- Failed source-only artifacts remain under external
  `preflight-attempt-3-causal-label-failure/`.
- On the fresh v3 run, three trajectories completed. The remaining planner
  produced `explore maze`, `build maze map`, and `write maze map to file`.
  The last phrase was initially rejected because the validator had broadened
  the registered ban on a concrete path or file extension into a ban on the
  ordinary word `file`. The validator was corrected to accept that semantic
  responsibility while continuing to reject actual paths, extensions, line
  ranges, commands, tools, statuses, models, agents, and sessions. The three
  complete v3 caches remain valid and inference resumes without semantic retry.

## Attempts 4--5 — Unscored Label Semantics Versus Span Completion

- A plan-free `switch` at Terminus operation 29 copied
  `design_primers_final.py`. Rejecting that unscored label discarded a valid
  boundary decision. Revision 6 therefore retained plan-free labels and counted
  semantic violations without retry; independent Review 7 approved.
- A fresh v4 four-way run then showed that a planner can likewise copy a
  filename under parallel execution even when a separate replay of the same
  temperature-zero request returns a compliant plan. Selecting the compliant
  replay would cherry-pick the candidate.
- Revision 7 applies the same rule symmetrically: retain the first
  syntactically valid raw plan and plan-free labels, never retry or rewrite for
  semantics, and count both arms' system-label violations. CodeTraceBench's
  stage spans score only segmentation; violations explicitly prevent this
  experiment from authorizing generated-name accuracy. Independent Review 8
  approved. Algorithm/cache version advances to v5 and starts fresh.
- The incomplete v3 and v4 source-only artifacts remain under external
  `preflight-attempt-4-causal-baseline-label-validation/` and the next numbered
  `preflight-attempt-5-symmetric-plan-label-validation/`, respectively.

## Attempt 6 — Planner Cardinality Grammar

- v5 eliminated semantic-label aborts, and two selected trajectories completed.
  One planner nevertheless emitted 124 list items until its 2,048-token output
  truncated mid-string.
- The registered plan already limits the planner to at most the trajectory's
  operation count, but the GBNF implementation had encoded an unbounded list.
  The grammar now enforces the registered per-trajectory maximum directly.
  This is an output-language implementation repair, not a new plan-size tuning
  rule. Algorithm/cache version advances to v6 and starts fresh; failed v5
  artifacts remain under external
  `preflight-attempt-6-planner-cardinality-grammar/`.

## Attempt 7 — Exact-Duplicate Plan Normalization

- The bounded v6 planner produced an array within the registered operation-count
  maximum but repeated an exact responsibility string. Rejecting it would again
  require selective replay, while retaining multiple identical indices would
  manufacture index boundaries without a semantic change.
- The raw plan is now retained, then exact duplicate strings are removed in
  first-occurrence order before alignment. No operation, gold, or scorer is
  read and no label is rewritten. The duplicate count is reported.
  Independent Review 9 approved this implementation of the already registered
  unique inventory. Algorithm/cache version advances to v7 and starts fresh;
  failed v6 artifacts remain under external
  `preflight-attempt-7-exact-duplicate-normalization/`.

## Consequence Of Attempts 1--2

The full-trajectory array interface is executable but scientifically unfit for
this 3B model. Running it on all 405 trajectories would repeat the already known
one-operation fragmentation failure. Before any gold or score is opened,
revision 4 changes only the inference interface to the user's simpler causal
policy: process one operation at a time, keep the current state, and emit one
small stay/switch decision. The RQ, population, task planner, evidence fields,
baselines, standard metrics, and decision rule remain unchanged.
