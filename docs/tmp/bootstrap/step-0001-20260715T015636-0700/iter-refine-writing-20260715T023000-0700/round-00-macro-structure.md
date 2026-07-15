# Round 00: Macro Structure

Skill: `check-paper-structure-flow`, Level 1, full-paper target
Reviewer mode: independent read-only subagent
Entry state: submission-shaped BOOTSTRAP contract; empirical values must remain placeholders

## Reviewer Findings

### Must-fix

1. The abstract and introduction did not separate background, root problem,
   closest approaches, central insight, system preview, and contributions.
2. `Evidence Model` and `Visualization Design` lacked a unified design opening
   with goals, architecture, and an end-to-end walkthrough.
3. Evaluation did not state all four RQs together, provide shared setup and
   baselines, close each RQ with an answer placeholder, or contain limitations.
4. The closest-work position did not address RECAP, Githru, trajectory work,
   and recent agent-code survival work.
5. The observed/committed/surviving triad was not traceable through the thesis,
   design, contributions, and RQs.

### Should-fix

1. Motivation mixed argumentative and neutral background roles and used
   question-form subsection titles.
2. The gallery catalogue dominated analytic function and did not separate core
   evaluated views from exploratory views.
3. Implementation did not mirror ingestion, joining, aggregation, layout, and
   interaction mechanisms.
4. Discussion consisted mainly of limitations.
5. Contributions overemphasized adapting seven visual traditions.
6. Future page growth should reserve more space for design, implementation,
   evaluation, and related work than for a visual catalogue.

### Consider

1. The original title suggested replacing commits with events.
2. The final architecture figure should expose all three evidence layers,
   uncertainty, mismatch outcomes, and coordinated selection.
3. RQ2 should connect behavior to durable outcomes and treat survival as an
   outcome dimension rather than a novelty claim.

## Root Decisions And Applied Fixes

- Accepted all Must-fix items. The introduction now has distinct problem,
  closest-approach, thesis, system-preview, and contribution paragraphs.
- Unified evidence and visualization under `System Design`, preceded by four
  goals, an expanded architecture placeholder, and an end-to-end walkthrough.
- Added the complete RQ contract, shared corpus/baseline protocol, explicit
  unanswered-result slots, and evaluation limitations.
- Grouped Related Work by replay, commit-centric visualization, trajectories,
  and survival. Exact citations remain for the citation round.
- Applied the three-layer vocabulary throughout and retained the explicit
  non-causality/non-authorship boundary.
- Accepted the Should-fix items by distinguishing core task-facing views from
  supporting gallery views and by expanding implementation/discussion roles.
- Accepted the title suggestion as `Process, Outcome, and Survival` because it
  states the complementarity thesis. The final title remains revisable after
  evidence exists.
- Kept RQ2 as one paper-level RQ but tied patterns to durable outcomes.

## Meaning And Evidence Check

No result value, causal claim, authorship claim, or implemented feature was
added. All empirical answers and final figures remain explicit placeholders.
The edits preserve the entry thesis while making its three evidence layers
structurally traceable.

## Verification

`make -C docs/paper` completed successfully and produced a four-page PDF. The
only layout diagnostics were three underfull boxes. The entry-snapshot diff is
nonempty, with 178 inserted and 87 deleted lines, and manual review confirmed
that deleted text was either reorganized or replaced by an equivalent,
more explicit evidence boundary.
