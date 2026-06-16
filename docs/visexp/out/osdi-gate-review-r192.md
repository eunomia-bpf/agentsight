# R192 OSDI Gate Review After R190-Score

Last updated: 2026-06-15
Stage at update: gate / supplement
Source/command: read-only subagent review over `STATE`, `RESEARCH_PLAN`,
`EXPERIMENT_PLAN`, `EXPERIMENT_TRACKER`, `RESULTS_SUMMARY`,
`CLAIM_VERDICT`, `EXPERIMENT_AUDIT`, `FOLLOWUP_PLAN`, `paper/main.tex`,
and `docs/visexp/out/tag-consolidation-audit-r190`
Completeness: complete as read-only review

## Verdict

Current maturity is Level 3, not OSDI weak accept.

The mechanism story is credible, but the outcome gates remain empty. C5 still
has no participant responses and C6 still has no human adequacy labels. R190-
score strengthens the evidence boundary by preventing blank merge-audit rows
from becoming fake evidence, but it does not make canonicalization correct and
does not support tag adequacy or developer utility.

## Findings

1. **Not OSDI weak accept.** C5 has `participant_count=0`,
   `response_count=0`, and `c5_supported=false`; C6 has
   `human_labels_empty`, `final_label_count=0`, and
   `adequacy_supported=false`. This is a promising mechanism/prototype paper,
   not yet a Level 4 systems narrative.

2. **R190-score strengthens the gate, not the science claim.** It is useful
   because it reports `canonicalization_quality_supported=false`, 0 final
   labels, 0.0% paired coverage, and no over-/under-merge rates for the blank
   packet. It supports only the claim that AgentFlame has an auditable
   merge-risk scoring protocol.

3. **Highest-risk unsupported claims remain C5 and C6.** C5 requires real
   R142/R151 user data. C6 requires two independent R124 human label sheets,
   adjudication, and a scored adequacy result. R190 merge labels are separate
   and are needed only for a canonicalization-quality claim.

4. **No major R190-score overclaim was found.** Current docs and paper wording
   mostly keep the boundary correct. The mild risk is wording such as
   "noise-control" or "vocabulary-hygiene" being read as quality evidence, so
   it should stay paired with "candidate", "proxy", or "audit protocol".

5. **C4 and C7 remain scoped.** C4 is strong for the fixed command-mode R114
   suite but not arbitrary full-history exact provenance or target-specific
   network capture. C7 is a bounded local artifact smoke, not community
   readiness.

## Required Next Evidence

- `R142`: collect five real pilot participants and score into
  `docs/visexp/out/user-task-pilot-r142/user-task-results.json`.
- `R151`: collect 12-20 participants or a deliberately scoped expert study
  before making a paper-scale utility claim.
- `R124`: collect two independent completed sheets from
  `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`, join,
  adjudicate, and rerun `score_tag_adequacy.py`.
- `R190-score`: label
  `docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-packet-r190.csv`
  and rerun `r190_score_merge_audit.py` only if the paper wants to claim
  canonicalization quality.

## Recommendation

Do not add more visualization polish next. Run R142 with real participants and
collect R124 human adequacy labels. Collect R190 merge-risk labels only if the
paper wants to report canonicalization quality.
