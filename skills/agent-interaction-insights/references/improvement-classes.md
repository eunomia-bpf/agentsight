# Interaction Improvement Classes

Start from the user's improvement decision, then use evidence to justify changes.

## 1. Reduce User Corrections

Questions:

- Where did the user need to restate scope, privacy, validation, or output expectations?
- Which instructions should move into AGENTS.md, CLAUDE.md, a checklist, or a workflow gate?

Outputs: correction heatmap, instruction backlog, stop-and-ask conditions.

## 2. Improve Summary Trust

Questions:

- Did final summaries distinguish done, checked, unrun, failed, and inferred?
- Did validation claims include exact command, scope, status, and timestamp?
- Did the agent expose sensitive details or unsupported claims in summaries?

Outputs: validation funnel, claim-evidence matrix, summary template changes.

## 3. Reduce Loop And Retry Waste

Questions:

- Which retries repeated the same failed hypothesis?
- Which tool attempts should have stopped earlier or narrowed scope?

Outputs: retry matrix, retry budget, before-rerun checklist.

## 4. Improve Instructions And Workflow Design

Questions:

- Which repeated behavior should become an instruction, deterministic tool path, eval, or policy?
- Which instructions were too vague or too easy to ignore?

Outputs: workflow backlog, candidate evals, policy changes, task framing changes.

## 5. Compare Agent Fit

Questions:

- Which tasks are safe for autonomy, which need checkpoints, and which should use deterministic tools?
- How do agents, models, prompts, or tool policies differ by correction rate, validation trust, and retry waste?
- Which model variants or agent configurations produce the best trust/cost tradeoff for each task class?

Outputs: task-fit matrix, before/after comparison, adoption recommendation.
