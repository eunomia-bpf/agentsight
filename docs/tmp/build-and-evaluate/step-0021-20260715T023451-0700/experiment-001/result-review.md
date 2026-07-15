# Independent Result Review — Reused CodeTraceBench Stage Fidelity

**Verdict:** PASS
**Scientific answer under the approved plan:** MIXED
**Reviewer role:** fresh read-only result reviewer using
`research-experiment-design`; no plan, implementation, or execution role

## Recomputed Evidence

The reviewer independently reconstructed the declared populations, recurrence
statistics and decisions, official-stage assignments, every pooled metric, and
the framework breakdown from the raw artifacts.

- Reference: 2,229 target-disjoint sessions / 87,703 operations.
- Target: 405 sessions / 20,866 operations / 20,461 adjacent pairs.
- Ground truth: 2,948 gap-free official stages.
- Coverage: each operation and pair appears once; all 20,866 units are
  conserved.
- Leakage: none. Rust receives only unit weight and `{session, action}`;
  official stages are loaded after Rust predictions; recurrence reference and
  target session IDs do not overlap.

The independently recomputed recurrence results are boundary F1
`0.2685055633` and B-cubed F1 `0.4750077514`. The boundary delta over direct
action-change is `+0.0009811917`; the partition delta against external
phase-change is `-0.1794376523`. Recurrence therefore wins exactly one primary
metric and the approved verdict is `MIXED`.

## Mechanism Diagnosis

The reviewer also compared every recurrence and action-change decision:

| Framework | Identical decisions | Total decisions |
|---|---:|---:|
| OpenHands | 9,817 | 9,817 |
| SWE-agent | 1,432 | 1,432 |
| mini-SWE-agent | 2,104 | 2,104 |
| Terminus2 | 7,038 | 7,108 |
| **Total** | **20,391** | **20,461** |

All 70 differences merge an action-change boundary. This means 99.6579% of
the complete recurrence decisions equal direct action-change and strongly
supports the root's diagnosis that the current cutoff calibration mostly
degenerates to action identity on this family.

## Paper And Next-Experiment Decision

This is valid decisive mechanism-selection evidence, not positive independent
cross-family confirmation. It does not authorize narrowing RQ3, changing its
positive hypothesis, changing the fixed thesis, or rewriting the paper story.
Because the reader-facing paper should present the strongest honest supported
case rather than the laboratory history, this mixed post-hoc mechanism result
does not enter the paper as a headline result.

The reviewer agrees that reusing the captured trajectories to improve the same
recurrence mechanism is appropriate. Any later CodeTraceBench result used to
select that repair must be labeled mechanism-development evidence rather than
fresh independent confirmation. No optional finding affects validity.
