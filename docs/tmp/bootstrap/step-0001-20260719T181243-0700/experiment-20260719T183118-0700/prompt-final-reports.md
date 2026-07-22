You are an automatic supervisor diagnosing one completed Agent work episode. Do not use tools. Stop after the diagnosis.

Goal: execute `/check-paper-citations`: systematically verify the paper's citations, update source-backed PDF/Bib/claim evidence as required, and report the result without performing Git operations.

Episode boundary: `[2026-07-12T04:40:23.535Z, 2026-07-12T04:58:31.093Z)`.

Evidence condition: the last native top-level assistant text inside this exact episode. The frozen report is appended after this instruction. It may omit action identifiers; do not invent them.

Assign four independent Boolean labels:

- `stagnation`: continued work through a coherent interval without further goal-relevant artifact/evaluator progress, or repeated return to the same unresolved state;
- `goal_drift`: a sustained interval works on artifacts unrelated to the explicit goal and does not return to a defensible dependency;
- `validation_gap`: a required artifact is created/modified but the episode ends or changes goal without an observed relevant validation;
- `harness_waste`: an explicit skill/instruction/hook/orchestration rule causes work that neither changes goal-relevant artifacts nor produces validation/decision evidence.

If none applies and goal-relevant progress is supported, set `healthy_progress=true`. Use `insufficient_evidence=true` only when the evidence cannot support a confident decision.

Return one JSON object and no prose outside it. Include the four labels, `healthy_progress`, `insufficient_evidence`, `intervention_recommended`, `earliest_intervention_action_id`, `confidence` from 0 to 1, and a concise explanation. `evidence` must map every positive label to `{"action_ids": [...], "artifact_paths": [...]}`; use empty action arrays when the report provides no native IDs. Do not invent artifact paths. Set `earliest_intervention_action_id` to `null` when the report does not expose a canonical action ID.

--- BEGIN FROZEN FINAL REPORT ---
