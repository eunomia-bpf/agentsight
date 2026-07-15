# BOOTSTRAP Step 0001

Started: 2026-07-15T01:56:36-07:00
Phase: BOOTSTRAP
Current gate: REVIEW_GATE (complete)

## EXPERIMENT_GATE

### Gate entry

The root read `docs/user-instruction.md` and
`docs/questions-for-author.md`. The user requests a new worktree, many
interactive software-evolution visualizations grounded in real multi-day data,
reuse of existing visualization tools, experimental evaluation, and a paper.
This gate therefore begins with mandatory literature/tool grounding and
artifact feasibility, not a toy rendering or a commit-only proxy.

### Node B1: repository and data feasibility baseline

**Context.** 2026-07-15T01:36:00-07:00, BOOTSTRAP experiment gate, complete.

**Question and entry.** Determine whether the repository and local environment
contain enough structured agent and Git history to support the requested study.

**Inputs and method.** Inspected `origin/master`, repository instructions,
`agent-session` types/parsers, existing frontend and visualization designs,
worktrees, and local Claude/Codex session-file dates and byte counts. Created a
clean worktree at `/home/yunwei37/workspace/agentsight-evolution-gallery` on
`codex/vis-gallery` from `origin/master` commit `a007540cc`.

**Results and raw evidence.** `agent-session` already exposes prompts, tool
events, path groups, status, tokens, cwd, and timestamps across Claude, Codex,
and Gemini. AgentSight-specific Claude records cover 20 dates between June 1
and July 15, 2026; local Codex records cover the period at much higher volume.
Existing views are run-centric and do not implement the requested longitudinal
families. The original checkout contained unrelated user artifacts and was not
modified.

**Scientific impact and decision.** Real multi-day feasibility is supported,
but coverage counts do not answer an RQ. The project will join agent events,
Git changes, and current survival rather than equating a tool event with a
committed or surviving change.

**Review, state updates, and next action.** Initialized the scientific
contract, canonical documents, and submission-shaped paper. Next, mandatory
primary-source literature grounding must establish closest work, baselines,
protocols, and reusable official tools before empirical plan review.

### Node B2: literature, novelty, and reusable-tool grounding

**Context.** 2026-07-15T02:10:00-07:00, BOOTSTRAP experiment gate, complete.

**Question and entry.** Test whether the proposed representation, views, and
evaluation remain differentiated after searching historical software-
evolution visualization, current coding-agent observability, trajectory
analysis, replay, and code-survival work. Verify reusable tools and mandatory
baselines before implementation.

**Inputs and method.** Ran the `research-literature-novelty` workflow against
primary papers, official proceedings and project pages, official npm metadata,
and the local toolchain. The detailed search, contradiction review, and
baseline handoff are recorded under `literature-20260715T021000-0700/`.

**Results and raw evidence.** RECAP is the closest same-mechanism work because
it already joins Copilot chat with fine-grained edit history for replay. Recent
trajectory studies already classify coding-agent behavior, and recent survival
work already compares agent- and human-associated code. Githru supplies the
closest Git visual-analytics baseline. The primary sources for all seven
historical visualization families were verified. ECharts, D3, Cytoscape.js,
uPlot, Perfetto Trace Event, Gource custom logs, and Hercules cover most of the
mechanical visualization and baseline work.

**Scientific impact and decision.** A replay-only, gallery-only, or first-
survival framing is rejected. The project keeps its central thesis but sharpens
the empirical object to disagreement among observed agent events, committed
changes, and currently surviving code. The ambitious claim requires measured
review utility against Git-only and event-table baselines. RQ1 join quality is
the first post-BOOTSTRAP experiment.

**Review, state updates, and next action.** The literature gate is complete.
The paper may enter the BOOTSTRAP write gate, where the submission-shaped
skeleton receives the mandatory twelve-round `iter-refine-writing` pass before
the scientific contract is frozen.

### Skipped components

Final RQ experiments are skipped in BOOTSTRAP: the scientific contract is not
yet literature-grounded or frozen, and the artifact is not implemented.

## WRITE_GATE

Entered 2026-07-15 after Nodes B1 and B2 completed and completed the same day.
The submission-shaped paper retains explicit result and figure placeholders;
no empirical claim replaced a placeholder.

The mandatory `iter-refine-writing` workflow completed all twelve serial
rounds: macro structure, microstructure, section conventions, logic flow,
abstract/introduction reconstruction, cross-document consistency, sentence
structure, word choice, terminology/claim tone, whole-paper flow, full citation
verification, and entry-snapshot meaning preservation. Independent read-only
reviewers were used at the required review rounds, with root-only application of
accepted fixes. The citation gate verified 20/20 active entries with zero
mechanical errors or warnings and corrected several overbroad source claims.
The final meaning audit restored the user's explicit file-birth/death-history
requirement and found the other artifact/research obligations preserved.

The paper compiles to seven pages. Canonical design, implementation, evaluation,
related-work, and idea-history documents now match the frozen evidence model:
recorded process, zero/one/many candidate actual-Git associations, separate Git
lineage, and current-tree endpoint survival.

## REVIEW_GATE

Entered after all twelve writing rounds completed and completed on 2026-07-15.
The independent outer audit returned a conditional pass with three blocking
contract fixes: exact RQ1 truth/denominators/window semantics, preregistered
confidence-stratum gates, and continuous rename-aware file lifetimes that break
on deletion/recreation. All three were applied and synchronized across the
canonical documents and paper. The corrected contract passes to an RQ1
preflight; no implementation result is claimed.

## Ranked open objections

1. RQ1 candidate association and line-lineage quality may be too weak for RQ2
   or RQ3 event-to-outcome claims.
2. A broad gallery may produce visual interest without measurable review
   utility beyond a strong Git-only interface or a full joined table.
3. A controlled participant study may be impractical within the available
   population; an informal demo cannot substitute for it.
4. Stable spatial layouts and overview aggregation may not preserve accurate
   navigation at full local-history volume.
5. Cross-vendor schemas may not expose enough exact edit payload to support
   line-level overlays outside narrow confidence strata.

## Current transition

BOOTSTRAP step 0001 is scientifically complete and frozen. Commit and push this
single completed step, then enter the RQ1 implementation/experiment loop. The
next experiment is the controlled exporter/join preflight recorded in the
outer audit; the full gallery must not be used to bypass join validation.
