# Experiment 003 Plan Review 2

Act as a different, read-only senior research reviewer with expertise in
hierarchical task models, LLM agents, and rigorous AI evaluation. Read the full
paper under `docs/paper/`, complete `docs/idea-story.md`, Experiment 002's
full-run failure report, Experiment 003's complete plan, and plan review 1.

Independently attack the causal and operational sufficiency of the V2 rule:
`prefix(current stack, keep_depth) + zero-or-one fresh frame`. Verify that
depth is truly variable and uncapped, that the local Qwen input can decide all
four transitions online, that V1 score feedback did not leak into V2, and that
the registered B-cubed comparison answers the stated mechanism hypothesis.
Do not edit files, invent a new RQ/story, or turn optional ablations into gates.
Return `APPROVE` or `REVISE` and only necessary must-fix items.
