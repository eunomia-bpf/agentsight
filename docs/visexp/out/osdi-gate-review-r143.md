# R143 Independent OSDI/SOSP Gate Review

Last updated: 2026-06-15
Stage at update: audit / supplement
Source/command: read-only subagent review over `docs/visexp/EXPERIMENT_PLAN.md`, `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/EXPERIMENT_AUDIT.md`, `docs/visexp/paper/main.tex`, `docs/visexp/out/user-task-results.json`, and `docs/visexp/out/tag-adequacy-results-r124.json`
Completeness: complete for this review pass

## Verdict

Current maturity: Level 3. AgentFlame has credible mechanism evidence for a
conference-paper draft, but it is not yet a Level 4 systems narrative.

Weak accept: not yet. The main blocker is not novelty framing; C5 and C6 still
lack outcome evidence. `user-task-results.json` is `participant_results_empty`
and `tag-adequacy-results-r124.json` is `human_labels_empty`. The repository
correctly keeps C5 unsupported and C6 partial.

## Must-Fix Gaps

1. C5 user utility has no real participant result. The packet, answer key, and
   scorer exist, but they do not show that semantic effect flamegraphs help
   developers answer forensic questions faster or more accurately.

2. C6 tag adequacy has no human labels. The 3B syntax, latency, and stability
   evidence are useful, but they do not prove one-word tags are adequate.

3. Baseline naming is mostly corrected. Generated packets and paper text use
   `event-count-proxy` and do not present it as true span duration. The review
   found one residual matrix entry that said `span flamegraph`; this was fixed
   in `docs/visexp/EXPERIMENT_PLAN.md`.

4. C5 preregistration needed a frozen artifact. This pass added
   `docs/visexp/out/user-task-preregistration-r142.json` and
   `docs/visexp/out/user-task-preregistration-r142.md` so the pilot and paper
   run have a source-hash-locked analysis contract.

5. Privacy boundaries are plausible but not enough for a public release claim.
   Raw traces are not committed, and the R124 label sheet hides model/source
   metadata. Redacted preview artifacts remain research packets, not public
   sanitized release artifacts, unless a stronger release policy and scan are
   added.

## Minimal Next Artifact

Run the R142 pilot with real participants under the frozen preregistration and
produce `docs/visexp/out/user-task-pilot-r142/user-task-results.json`. This is
pilot evidence only. Paper-scale C5 still requires 12-20 participants or a
clearly scoped expert study that passes the preregistered scorer gate.

In parallel, collect two independent human labels over the R124 blinded sheet,
adjudicate disagreements, and rerun `score_tag_adequacy.py`.

## Claim Boundary

Until those two outcome artifacts exist, the paper should claim mechanism,
semantic partitioning, and fixed-suite exact lineage only. It should not claim
developer utility or semantic correctness of the tags.
