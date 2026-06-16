# R201 Long-Tail Governance Sensitivity

Status: `long_tail_sensitivity_complete`

## Scope

- Reads generated R170 AgentFlame and R189 canonical-tag artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Tests whether R196 long-tail governance is robust to threshold and generic-vocabulary changes.
- Does not prove tag adequacy, merge quality, developer utility, or community adoption.

## Grid Rationale

- Tail thresholds: Sweep half/default/double support cutoffs: 50/100/200 for session and prompt tags, and 5/10/20 for LLM-call tags.
- Split thresholds: Sweep permissive and conservative multi-peak detection while holding the baseline tail thresholds fixed.
- Generic vocabulary: Perturb the noisy/generic-token list in both directions to test routing stability without mutating raw tags.

## Variant Summary

| variant | review tags | review support | long-tail tags | long-tail support | changed actions | head stability |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 323 | 1.926% | 1575 | 1.746% | 0 | 100.0% |
| `lower_tail_threshold` | 323 | 1.926% | 1449 | 0.921% | 89 | 100.0% |
| `higher_tail_threshold` | 323 | 1.926% | 1659 | 3.03% | 64 | 65.217% |
| `aggressive_split` | 323 | 1.926% | 1575 | 1.746% | 4 | 100.0% |
| `conservative_split` | 323 | 1.926% | 1575 | 1.746% | 1 | 100.0% |
| `narrow_generic_vocab` | 323 | 1.926% | 1575 | 1.746% | 0 | 100.0% |
| `expanded_generic_vocab` | 326 | 1.931% | 1575 | 1.746% | 3 | 100.0% |

## Interpretation

- Baseline review-required support is `1.926%` of total support.
- Worst variant review-required support is `1.931%` in `expanded_generic_vocab`.
- Lowest baseline-head stability is `65.217%` in `higher_tail_threshold`.
- These are policy-sensitivity measurements. Any regenerated or merged tag still needs R190/R124-style human review before a quality claim.

## Claim Boundary

R201 strengthens the design argument that R196 is an auditable governance layer rather than an opaque taxonomy. It does not support C5 user utility, C6 tag adequacy, canonicalization quality, or community adoption. It only reports how review-required row/support counts and display grouping change within this policy grid.
