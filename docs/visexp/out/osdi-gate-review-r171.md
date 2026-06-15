# R171 OSDI Gate Review

Last updated: 2026-06-15
Stage at update: audit / supplement
Source/command: read-only subagent review over `docs/visexp/STATE.md`, `RESEARCH_PLAN.md`, `EXPERIMENT_TRACKER.md`, `RESULTS_SUMMARY.md`, `CLAIM_VERDICT.md`, `EXPERIMENT_AUDIT.md`, `FOLLOWUP_PLAN.md`, `paper/main.tex`, and current `docs/visexp/out/*.json` gate artifacts
Completeness: complete

## Verdict

Not OSDI weak accept yet.

AgentFlame is a credible Level 3 mechanism/evaluation artifact, but not a
Level 4 systems narrative. The current evidence supports semantic attribution
and folded aggregation over local agent histories, plus a fixed-suite exact
lineage result. It does not yet support developer utility or semantic
correctness claims.

## Maturity

Current maturity: Level 3 conference-paper mechanism evidence.

- C1-C3 are fairly strong.
- C4 is strong only for the fixed 20-task Codex command-mode suite.
- C5 and C6 still block weak accept.

## Must-Fix Gaps

- C5 is unsupported: `docs/visexp/out/user-task-results.json` has zero real
  participant responses and `c5_supported=false`.
- C6 is partial only: `docs/visexp/out/tag-adequacy-results-r124.json` has 300
  candidate tags but zero final human labels and `adequacy_supported=false`.
- The current `event-count-proxy` is not a true span-duration flamegraph
  baseline. It must not be compared as span-duration tracing.
- C4 cannot be worded as broad/full-history exact provenance. R114 gives
  in-scope precision/recall evidence for a fixed command-mode suite only.
- The top-level research/paper artifacts live under `docs/visexp/`, including
  `docs/visexp/paper/main.tex`; root-level paper files are not the canonical
  research state.

## Recommended Next Artifact

Run R124-labels with real independent human labels, then join and score them.
This is the smallest next run that materially advances weak accept without
fabricated evidence because it directly tests whether the one-word tags are
adequate rather than merely syntactically valid.

Expected files:

- Input: `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`
- Frozen human sheets: two independent completed copies, not LLM/subagent labels
- Joined output: `docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv`
- Join manifest: `docs/visexp/out/tag-adequacy-label-join-r124.json`
- Scored outputs: `docs/visexp/out/tag-adequacy-results-r124.json`, `.csv`, `.md`
- Updated aggregate: `docs/visexp/out/evaluation.json`

Success gate: both labelers cover 300/300 rows, disagreements are adjudicated,
adequate >=80%, generic/noisy <=20%, misleading <=5%, and Cohen's kappa >=0.6
or the paper wording is narrowed.

## Claim Wording

Keep claims narrowed to: AgentFlame semantically labels
session/prompt/LLM-call control-plane context and joins it with
tool/process/effect provenance for local histories and a fixed command-mode
suite.

Do not claim proven developer utility, semantic correctness, broad exact
provenance, community readiness, or novelty as "agent flamegraphs."
