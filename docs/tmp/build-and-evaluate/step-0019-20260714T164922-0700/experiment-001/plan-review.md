# Plan Review

## Verdict: REVISE

## Scientific validity and admission

The experiment is admitted and paper-relevant: it tests one downstream RQ2 decision that the existing concentration and inspection curves do not settle, reuses the complete six-task R315 population, and gives positive, mixed, contradictory, and invalid outcomes different paper consequences. Its scope is appropriately limited to this fixed reader and these already ranker-selected R315 packets. No additional model, dataset, or external baseline is required for approval.

## Main-baseline fairness

The fixed-session comparison is the strongest runnable matched baseline. Both non-flat views expose five groups and use the same reader, prompt, field categories, decoding, and three-group selection budget; recall and precision account for the deliberately different group sizes. The plan also correctly bounds any positive result to the truncated R315 packet construction rather than claiming superiority over raw action or universal view dominance. This criterion passes.

## Flat and order controls

Flat is correctly labeled a non-selective completeness control rather than a granularity-matched baseline, and the deduplicated R316 top-three result is a useful existing-ranker control. However, R316 does not control the new reader's position bias: it evaluates visible query-aware rank order, whereas the main run uses one arbitrary ID-derived order. It therefore cannot distinguish content-based selection from a reader preference for early aliases.

## Hidden-key, order, and identifier separation

This is blocking. Sorting each packet lexicographically by its original group IDs and then assigning `G01`--`G05` hides the literal IDs but makes alias position a deterministic encoding of ID order. Because the two views have unrelated IDs and the cited prior work establishes position bias, one presentation per packet leaves view effect confounded with unmatched arbitrary position; six task pairs cannot average that away. Revise the protocol to use a predeclared hidden-key-blind, view-symmetric balanced presentation scheme (for example, all five cyclic rotations of a base order, so every group occupies every position), assign fresh aliases only after each presentation is ordered, and aggregate the repeated presentations within task before the six paired task comparisons. The persisted raw request must be constructed from an explicit allowlist and must exclude `packet_id`, `view`, `ranker`, `response_prompt`, `rank`, original `group_id`, and hidden-key fields; keep the alias-to-original-ID map only in the collection record used later by scoring. This is an order/identity repair, not a request for another baseline.

## Metrics and outcome partition

Recall and precision at three groups are claim-matched primary metrics, work fraction and lift are appropriately secondary, and reporting all six paired deltas without a population-level p-value is suitable. The verdict rule is nevertheless blocking because it is not mutually exclusive: if both medians are positive but each metric wins on exactly three tasks, the plan classifies the result as both `Mixed` (positive medians but fewer than four wins) and `Contradicted` (both improve on at most three tasks). Replace this with one exhaustive, disjoint rule, defined after the order-balanced within-task aggregation; for example, supported only when both metrics meet both conditions, contradicted only when neither metric meets its full condition, and mixed otherwise.

## Executability

The artifact paths and packet ID exist, the visible and hidden files each contain the expected 18 task-view cases, the R316 CSV is present, and `/v1/models` exposes `qwen3.6-27b`; the three command shapes are otherwise executable once the adapter is implemented. Revise the preflight command/prose from three attempts to at most two real attempts, as required by the experiment protocol; full-run transport/schema retries may remain explicitly non-observational. Update the planned call count, completion rule, and scoring inputs to reflect the balanced presentations, while retaining all cells and recomputing the complete score from locked responses.

After these order-confounding, verdict-partition, and preflight-limit repairs, the plan should be approved without expanding its model, dataset, or baseline scope.

## Follow-up Review — 2026-07-14

### Verdict: APPROVE

The revision resolves every blocking finding. Each non-flat packet now uses five hidden-key-blind cyclic presentations, assigns aliases only after ordering, places every group once in every position, and averages rotation metrics within task/view before the six paired task comparisons; the explicit request allowlist and persisted scorer-only alias map provide the required rank, identifier, and hidden-key separation. The metric-pass rule makes supported, mixed, and contradicted exhaustive and disjoint. The preflight is explicitly limited to two real command attempts and uses `--attempts 2`, while the complete 66-presentation full-run and score commands, completion rule, checkpoint path, and task-level analysis are internally consistent. The fixed-session baseline remains fair and claim-matched, and flat and R316 retain distinct non-headline control roles. No scientific or executability defect remains that would invalidate the planned result; no extra model, dataset, or baseline is required.
