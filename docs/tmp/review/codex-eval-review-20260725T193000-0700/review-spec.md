# Review spec: reviewer-style audit of the Evaluation section (codex)

You are an independent reviewer auditing the Evaluation section of
`docs/paper/main.tex` in this repository. READ-ONLY except writing your
review file. Never run any git command that modifies state (`git diff`,
`git log`, `git status` allowed). Never write outside the repository.
Never touch `docs/agentpprof-paper/` (submodule).

## What to audit

1. **Number provenance**: for each table and each headline number in the
   four RQ subsections and both case studies, locate its source record
   under `docs/tmp/build-and-evaluate/` (steps 0072, 0075, 0076, 0077,
   0078, 0079, 0080, 0081 hold the recent ones) and confirm the paper
   states it exactly (documented rounding acceptable). Flag any number you
   cannot trace.
2. **Claim-evidence fit**: as a skeptical AAAI reviewer, list every place
   where the stated claim is stronger than the cited evidence, every
   missing baseline a reviewer would demand, and every scope disclosure
   that is load-bearing. Rank the top 5 attack points with the exact
   sentence they target.
3. **Internal consistency**: numbers repeated in abstract/intro/body must
   agree; table values must match prose; appendix references must resolve.
4. **Title fit**: the title is "AgentProf: Semantic Profiler for Long
   Horizon AI Agents"; assess how well the current evaluation mix supports
   the "Long Horizon" scoping and what would strengthen it.

## Deliverable

Write `eval-review.md` in THIS directory: verdict (accept-risk level),
traceability table (number -> source file -> match), top-5 attack points
with quoted sentences, consistency findings, and title-fit assessment.
Be specific; no generic advice.
