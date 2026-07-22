# RQ5 Result Review — Final

**Reviewer:** independent result reviewer  
**Date:** 2026-07-22  
**Verdict:** **PASS**

## Review judgment

```text
run status: valid
tested hypothesis: supported, descriptively and within the six observed cases
research value: supporting
paper impact: additional RQ evidence with an explicit construct/coverage boundary
next paper decision: admit F8a/F8b only as path-resolved workspace-activity evidence;
  align the paper's RQ5 wording before integration and do not claim internal
  attention, duration, importance, entropy, cooling, forgetting, or causality
```

The repaired run executes the final Round-3 plan on the frozen six-project
corpus. It supports a bounded descriptive finding: artifact allocation,
worktree-module activity, adjacent source-path transitions, and module-return
gaps are heterogeneous across the six observed projects. This is evidence
about merged, path-resolved workspace activity, not an estimate of an Agent
population or a reconstruction of internal attention.

## Frozen inputs and reproducibility

- The RQ1 input hashes are verified by the analysis command before any result
  is derived. The reviewed RQ4 access input is exactly
  `26466eb3a343ee6eb9a459a6c4690b8ae072b0317a775f6636093f0d3eb344cf`.
- Every hash recorded in `commands.log` matches the current file, including
  eight CSVs, F8a/F8b PDF and PNG outputs, `result.md`, and
  `agentvis/research/plot_rq5.py`.
- I reran the authoritative command into a fresh `/tmp` output directory. All
  eight CSVs, both PNGs, and `result.md` were byte-identical to the reviewed
  artifacts. The independent run took 5.72 s wall time and 717,732 KiB maximum
  RSS. PDFs embed CID TrueType fonts; their creation metadata is not used as a
  byte-reproducibility anchor.
- An initial independent rerun exposed nondeterministic ordering in the module
  return CSV. The implementation was repaired to sort all set/state iteration,
  rerun twice by the author, and then rerun once more independently. The final
  module-return hash is stable at
  `e921cc58d56e6235344b5dbd11d4ede25611aae63b8deb23765b1b63a07e3882`.

## Independent metric audit

### Source coverage, status, and primary units

I recomputed the coverage table directly from the frozen RQ1 JSON, separately
for every project and vendor. All 17 rows match, including status counts,
source action rows, scope rows, scope-only calls, calls without resolved paths,
failed calls without path evidence, and home-or-target worktree attribution.
For example, AgentSight contains 126,476 Tool events, of which 96,982 have a
home or target worktree; 3,877 are scope-only and 3,400 failed without a
non-scope resolved path.

The current RQ4 access table contains 95,112 eligible non-scope read/mutation
rows. Applying the frozen primary key
`(project, worktree, event, lineage, operation)` produces exactly 95,111 unique
primary units: 83,800 `ok` and 11,311 `observed`. The one collapse is a real
two-step rename of the same lineage and operation in one Tool event. Every
retained unit now has a reviewed RQ4 artifact identity; unresolved identity is
zero in all projects.

An independently written implementation of `artifact-path-v1` agrees with all
95,111 exported classifications, including first-match precedence, exhaustive
manifest/basename rules, root-module naming, and case folding. Destination
paths are used for rename allocation. Of 82 retained rename units, 81 expose a
source path and one source RQ1 action does not; the destination allocation is
valid, but that single source/destination rename pair is unavailable and must
not be described as complete rename-pair coverage.

### Fractional Tool-call sensitivity

For each `(project, worktree, event, read-or-mutation)` stratum, I independently
summed the per-lineage weights. All 71,361 eligible call-strata sum to exactly
one. `rq5-summary.csv` reconciles its action denominators, fractional
denominators, and seven artifact classes for both all path-resolved and
`ok`-only scopes.

The status sensitivity is material rather than cosmetic. In mutation rows,
the total-variation shift between all path-resolved and `ok`-only allocation is
11.4% for AgentSight, 13.4% for ActPlane, 10.0% for the BPF tutorial, and 49.7%
for eunomia.dev. F8a exposes this sensitivity directly and the result text
correctly treats `observed` as unknown outcome, not confirmed effect.

### Worktree-lane transitions and module returns

I rebuilt each `(project, worktree)` call sequence from `rq5-calls.csv` and
reapplied the set precedence independently. All 71,238 transitions match row
for row: 31,883 same-artifact, 30,551 same-module, and 8,804 cross-module.
No cross-worktree adjacency is formed, and the singleton-only summary matches
the raw transition flags.

I also rebuilt the module return-risk state machine independently. A risk
interval opens only after the first call omitting a previously present module,
closes on the next containing call, and remains right-censored only if still
open at the lane end. All 11,080 exported episodes match row for row: 10,959
observed returns and 121 right-censored gaps. The five-project return gate is
applied correctly. AgentSkill's three observed returns are shown as
`N/A (n=3<20)` in F8b rather than as a return-distance estimate.

The 133 worktree-module summary rows independently reconcile action, read,
mutation, resolved-call, native-session, first/last event, and first/last time
fields. All 50 cumulative leader-change rows also match an independent prefix
reconstruction.

## Figure audit

F8 is appropriately split into two paper-width result figures instead of one
overloaded canvas:

- **F8a** compares all path-resolved and `ok`-only read/mutation allocation.
  Totals, class colors, and the unknown-outcome warning match the CSV/result
  text.
- **F8b** uses the frozen top-eight `(worktree, module)` rule, lexical display
  order, 60 equal-count action-order bins, one count per displayed module per
  call, a unique-call `remainder`, and row-maximum color normalization. The
  transition and return panels match the reviewed rows and gates.

Both PDFs are 7.05 inches wide, use embedded TrueType fonts, and keep plotted
text at or above 7 pt. Fresh PNG and PDF inspection found no label/data
overlap; the previously reported legend/title collisions and undersized fonts
are gone. Exact counts remain in CSV/result text where the heatmap uses
display-only row normalization.

## Evidence and writing boundary

The run does not require an external baseline: it is a descriptive multi-case
measurement, not a superiority comparison. Likewise, error bars would be
misleading because the plotted quantities exhaust the frozen observed corpus
rather than represent repeated random trials.

Before F8 enters the paper, the current RQ5 prose must be aligned with the
approved construct. Any remaining wording about internal “attention,”
transition entropy, hotspot cooling, persistent cold regions, memory, or
forgetting is not supported by this run. The valid claim is narrower:
path-resolved artifact allocation and source-path activity migration differ
among these six observed persistent workspaces, and native status materially
changes several allocation summaries.

