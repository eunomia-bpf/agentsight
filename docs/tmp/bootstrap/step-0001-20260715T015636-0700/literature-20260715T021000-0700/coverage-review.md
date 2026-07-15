# Literature Coverage And Contradiction Review

Timestamp: 2026-07-15T02:18:00-07:00
Status: complete with recorded residual uncertainty

## Coverage review

The search covered each declared threat category with primary evidence:

- **Same problem:** RECAP, Githru, AgentSeer.
- **Same mechanism:** RECAP's chat/edit join; stable layouts from Software
  Cartography and EvoStreets; Git survival from Hercules and recent studies.
- **Same evaluation:** Githru's controlled tasks, Merino et al.'s systematic
  evaluation review, RECAP's multi-week deployment.
- **Same setting:** code-agent trajectories, AI-assisted course projects,
  agent-labelled open-source PR histories, and real Git repositories.
- **Contradictory evidence:** software maps can confuse users; many software
  visualizations lack strong evaluation; RECAP already achieves fine-grained
  replay; recent work already analyzes behavioral signatures and survival.
- **External tools:** chart/layout libraries, Perfetto, Gource, Hercules, and
  Git plumbing were checked against official sources.

No additional keyword variant found a system that simultaneously provides
cross-vendor native-agent ingestion, multi-session repository evolution,
explicit observed/committed/surviving mismatch, seven coordinated evolution
views, and controlled review-task evaluation. Absence is not proof; this is the
residual novelty uncertainty.

## Material contradictions

1. **RECAP weakens the original mechanism claim.** It already argues that chat
   and Git alone are insufficient and joins chat with shadow edits. The project
   must evaluate actual Git outcomes and cross-session evolution, not claim a
   first replay or unified timeline.
2. **Agent survival is not novel.** Will It Survive? directly studies
   agent-authored code survival at scale. Survival views are a projection and
   validation instrument, not the central contribution.
3. **Trajectory patterns are crowded.** ICSE and 2026 trajectory work already
   identify success/failure patterns and behavioral signatures. New pattern
   names without predefinition and outcome linkage would be post-hoc branding.
4. **Stable maps are not automatically intuitive.** Prior cartography studies
   report surprising/confusing layouts. The initial artifact should use a
   deterministic hierarchy-first layout, with semantic layout as an optional
   experiment.
5. **Visual appeal is weak evidence.** The evaluation literature finds that a
   majority of software-visualization work lacks strong evaluation. Screenshots
   and social engagement cannot substitute for task outcomes.

## Root-facing alternatives

- **Adopted evidence direction:** keep the strong event-plus-durable-outcome
  claim and make mismatch categories first-class.
- **Rejected narrowing:** present a gallery as an experimental frontend only.
  This would satisfy implementation but abandon the requested paper-level
  scientific value.
- **Serious competing explanation:** most review utility may come from Git
  outcomes and task-specific metrics; event detail may add only replay appeal.
  The Git-only and event-table baselines must be capable of winning.

## Search-tree updates

- Opened a high-priority branch for process/outcome mismatch and join quality.
- Demoted first-survival and first-trajectory-pattern claims.
- Added HCI/CS-education deployment and VIS evaluation as adjacent branches.
- Added a reproducibility branch for Hercules/CLI metric cross-checks.

## Remaining uncertainty and reopen conditions

- RECAP describes itself as open source, but no public source repository was
  identified in its full text. Reopen artifact search if code becomes public.
- Agent-authorship inference from local sessions may remain ambiguous. If RQ1
  preflight cannot establish useful match confidence, preserve mismatch views
  and remove authorship comparisons rather than invent provenance.
- A defensible RQ3 human study needs participants or an externally reviewable
  benchmark task set. Record and pursue a default expert-task protocol without
  pausing, but do not report simulated participants as human evidence.
