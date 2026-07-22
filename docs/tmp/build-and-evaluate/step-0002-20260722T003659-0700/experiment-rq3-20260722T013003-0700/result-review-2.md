# RQ3 Independent Result Review — Round 2

**Verdict: PASS**

The repaired run closes all three blockers from the first result audit. The
frozen episode derivation remains unchanged, and the regenerated F6 now
implements the approved action-prefix and reporting definitions.

## Independent verification

- The current files match every SHA-256 recorded in `commands.log`.
- A clean rerun reproduced all three CSV hashes and both PNG hashes exactly.
  As noted in Round 1, PDF byte hashes include Matplotlib's creation timestamp;
  this does not change their rendered content.
- The denominators remain exactly 7,154 observed identities, 2,219 mutated
  identities, 13,150 mutation episodes, and 13,152 raw mutation rows. The
  previously audited source links, episode collapse, first/repeat labels,
  cross-session labels, birth-state coverage, and per-artifact loads are
  unchanged.
- Panel C now groups every artifact episode at a shared `event_index` before
  updating the cumulative numerator and denominator. It renders one
  post-action step per native Tool-action index, so the 829 multi-artifact Tool
  actions no longer expose an arbitrary within-action order or a linear trend
  across inactive action ranges. Each curve's final prefix exactly equals its
  independently recomputed project repeat fraction.
- F6 now prints episode/raw-row denominators, repeat fraction, cross-session
  share, repeat rename/delete composition, and elapsed mutation-span days.
  The displayed values independently recompute from `rq3-episodes.csv`.
- The top-10% shares now use the fractional boundary at exactly 10% of mutated
  identities. The recomputed shares are 68.5%, 75.9%, 42.0%, 41.9%, 86.7%,
  and 55.9%, matching `rq3-summary.csv` and `result.md` after rounding.
- The all-identity zero mass, conditional CCDF denominators, concentration
  curves, and birth-state sensitivity remain correct. All six projects exceed
  the preregistered 20-episode/10-mutated-identity eligibility gate.

## Figure and claim audit

Both PNGs were inspected at original resolution. Labels and the new table are
legible, no panel is clipped, and the figure distinguishes the unconditional
zero mass from the conditional CCDF. The figure continues to prohibit a
heavy-tail distribution claim, convergence claim, thrashing label,
defect-repair inference, and waste/failure interpretation. Cross-session
repetition is reported descriptively and is not called forgetting or reset
cost. The `days` field is the first-to-last observed mutation-episode span, not
the full repository age; this definition should remain explicit in prose.

## Result judgment

```text
run status: valid
tested hypothesis: supported for the preregistered mutation-concentration facet
research value: supporting
paper impact: additional RQ evidence
next paper decision: F6 and its descriptive numbers may be included with the current claim boundaries; keep convergence, validation-followed revision, and module-switching facets of RQ3 open
```

Across these six qualified cases, repeat-observed episodes account for
71.8%--91.8% of observed mutation episodes, while the exact top-10% identity
share varies from 41.9% to 86.7%. This supports a descriptive cross-case
finding that repeated mutation is common and differently concentrated; it is
not evidence of a particular tail family, convergence, or wasted work.
