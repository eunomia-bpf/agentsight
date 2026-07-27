# Final v2 integration report

Date: 2026-07-27

## Scope and outcome

The repaired-v2 RQ1--RQ4 projection, downstream user-question and invariance
recomputations, second conformance-repair cycle, human-involvement profile, and
RQ7 read-count update are synchronized into both paper entry points and
`docs/evaluation.md`. Seven affected publication figures were regenerated from
the repaired-v2 CSVs. The paper keeps the second repaired corpus explicitly as
`repair-corpus-v2`; it is repair evidence rather than an independent
generalization test.

## Integrated changes

- RQ1 now uses 5,676 observed identities, 2,318 mutated identities, 13,809
  mutation rows, 13,766 episodes, 89.29--96.94% reuse, Spearman rho 0.0286,
  the BPF/AgentSight adjacent rank reversal, and repaired-v2 persistence,
  validation, dormancy, revival, and concentration quantities.
- RQ2 now reports 29.3--86.5% zero-mutation intervals while preserving the
  1--817 maximum range and the heterogeneous-response boundary.
- RQ3 now reports Case D paper/docs mutation allocation of 60.7% for all
  resolved statuses and 86.8% for `ok`, repaired transition ranges, five
  return-qualified cases, and repaired-v2 turnover/cooling values.
- RQ4 explicitly records that the repaired-v2 recheck preserves 121
  components, 111 boundaries, and the stopped 3/6 gate; conditional support is
  65 first-mutation boundaries and 59 defined-overlap boundaries.
- RQ6 uses the repaired 76.8--100.0% local-anchor range. Path locality is the
  sole cross-project, cross-vendor, public-corpus invariant candidate
  (CV 0.088, leave-one-out 1.0, all five public confidence intervals positive).
  The paper records eight vendor-shaped versus zero project-shaped behavior
  shapes and rejects a universal power-law claim.
- RQ7's supplement denominator is 43,889 artifact-identity reads.
- The supplement's user-originated questions use all repaired-v2 values,
  including the single legal cross-path compound episode and the unchanged
  source--test order result.
- The conformance narrative now presents the complete second field cycle:
  material audit, six compound-shell shape families, 18 action fixtures,
  preserved 60/60 regression, repair-corpus-v2 B+C 58/58 and D 29/29, exact
  attempted/confirmed/status ledgers, third-corpus generality boundary, and
  the ensuing full recomputation.
- A new supplement subsection reports 7,804 human messages, one message per
  23.2 Agent actions, 63.3% startup-only human-bearing sessions, approximately
  50% immediate action redirection after explicit interruptions, the 73.8%
  inactive-gap boundary, and the Codex subagent user-role attribution trap.
  The main corpus description now calls the cases author-associated
  mixed-initiative traces.
- `docs/evaluation.md` records repaired-v2 status and refreshed next actions
  for RQ1--RQ7, both conformance cycles, invariance, and human involvement.

## Regenerated publication figures

The following PDFs were rendered from the repaired-v2 CSVs and visually
checked after replacement:

- `rq1-activity-progress.pdf`
- `rq1-progress-curves.pdf`
- `rq2-validation-dynamics.pdf`
- `rq3-rework-structure.pdf`
- `rq4-component-continuity.pdf`
- `rq5-artifact-allocation.pdf`
- `rq5-activity-migration.pdf`

## Evidence and consistency gates

- A source-level assertion pass recomputed or checked every material
  paper-facing replacement against the repaired-v2 CSV/JSON outputs and the
  specified conformance, invariance, user-question, and human-involvement
  reports. It also scanned both TeX entries for superseded headline values.
- Human interruption values use the report's deduplication key
  `(session_id, followup_ordinal)`: 577 comparable interrupted follow-ups, 291
  exact-tool changes, and 286 tool-family changes. The extra raw CSV rows are
  duplicate cross-project memberships and are not separate follow-ups.
- Both LaTeX entry points compile with `latexmk -pdf -interaction=nonstopmode
  -halt-on-error`.
- Final logs contain no errors, undefined citations/references, or overfull
  boxes.
- Main PDF: 7 pages total; page 7 begins `References`, so main content occupies
  6 pages and satisfies the at-most-7-content-page gate.
- Supplement PDF: 21 pages.
- Citation-command count across both entry points: 28, unchanged.
- Citation-key and `\label` set comparison found no removals. The only removed
  headings are explicit renames of the former held-out section to the second
  repair-cycle section; the invariance and human-involvement headings are
  additions.
- `git diff --check` passes for the integrated figure, paper, and evaluation
  commits. The reviewed diff shows no unrelated technical section, citation
  key, cross-reference label, or previously stated limitation silently
  disappearing.

## Commits

Evidence-producing commits already at the integration baseline:

- Compound-shell repair:
  `51f7cece251888a0bf559044b62188d499222e9a`
- RQ1--RQ4 repaired-v2 recomputation:
  `98d409225f7512c6f8ae33c3fa2a5ed2e255b1cd`
- Repaired-v2 user-question and invariance outputs:
  `c65cba729cb1358d5ef669b61201abde220a8f0e`

Final integration commits:

- Publication figures:
  `2edfd1363289c292fc0a165023672d8dd0fc21d0`
- Main paper, supplement, and compiled PDFs:
  `5e52282a38046a80ce9f8df04ed1df5f30a5624d`
- Evaluation frontier:
  `10420a92c97080c69ddfb5cbd8d9592cd7c41dbc`

The immutable hash of the commit containing this report cannot be embedded in
that same commit without changing the hash. It is recorded in the post-commit
handoff and can be obtained from `git rev-parse HEAD`.

## Workspace note

The three specified pre-existing evidence-input directories
`human-involvement-20260726/`, `invariance-mining-20260726/`, and
`shell-boundary-audit-20260726/`, plus the unrelated
`iter-refine-writing-20260726T063131Z/` directory, remain untracked and
untouched. They were not silently folded into the paper/evaluation commits.
