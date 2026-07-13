# Independent Preflight Review — RQ2 Cross-Family Problem Localization

## Verdict

**PASS.** The real preflight engages the approved execution paths and may advance
to full execution. This verdict admits executability only; no preflight metric or
single-case output is paper evidence.

## Scope Reviewed

- approved RQ2 experiment plan and four-round plan review;
- `script/operation_family_heldout_eval.py`;
- the complete preflight report and raw output tree;
- every per-trajectory Rust input/profile pair;
- materialized risk scores and every development grouping output;
- official AgentRx, TELBench, bare, and DRIFT source and runtime paths.

## Independent Reconstruction

1. All 29 development trajectories invoke the maintained Rust release binary
   separately. AgentRx and TELBench also invoke it on one real unlabeled
   trajectory each. The reconstructed semantic path intentionally omits the
   trajectory identifier so identical paths can aggregate across trajectories;
   4 of the 46 development paths do so, with one path covering 12 trajectories.
2. Induced and matched-null outputs each cover all 729 unique operations exactly
   once and each contain 46 global groups. Recomputed group-size multisets match
   globally, within every trajectory, and for every trajectory-by-semantic-path
   contribution. The null therefore changes membership while preserving the
   proposed view's cardinality and aggregation shape.
3. The raw-action view groups by tool, action, and event-native tool status. The
   three SQL prefix views are real SQLite queries and their memberships match an
   independent reconstruction from source fields.
4. Risk-tag thresholds recompute exactly from the 25th, 50th, and 75th
   percentiles of 4,285 separate SATRaj training scores. They are not selected on
   the AgentReward preflight target.
5. The only labels passed to the scorer are development AgentReward labels.
   AgentRx conversion reads official IR instruction, role, and content; TELBench
   is rewritten to `id`, `source_id`, `question`, and ordered raw spans before
   profiler or model execution. Neither confirmatory family is scored.
6. Microsoft AgentRx and NJU-LINK DRIFT revisions match the report. The decrypted
   TELBench file passes the official checksum and contains 1,000 cases. Official
   `bare` and `drift` commands produced real prompts, predictions, token usage,
   and per-case logs through the declared local Qwen2.5-3B llama.cpp endpoint.

## Required Disclosures Carried Forward

- SQLite does not expose a native `ROLLUP` operator here. The implementation
  executes each rollup prefix as a separate `GROUP BY` query and scores it
  separately, which is scientifically equivalent to the approved comparison and
  must be described accurately.
- Full execution must record the llama-server binary, model path, endpoint, and
  launch command in ordinary raw output and the Markdown result report.

## Transition

Proceed to every development-selection cell, all aligned public AgentRx
trajectories, all 1,000 TELBench cases, 100 matched controls, all three seeds and
ablations, and complete official bare/DRIFT runs. A partial prefix remains
incomplete and cannot return to WRITE.
