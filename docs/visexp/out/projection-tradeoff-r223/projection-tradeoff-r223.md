# R223 Projection Tradeoff

Status: `done/rq2-tradeoff-artifact`

This artifact answers RQ2 as a projection-selection problem over R170-derived generated evidence. Semantic-axis and display-policy rows share the same system-effect denominator; vocabulary rows report tag-display support. It does not read raw traces, call an LLM, or score human utility/adequacy.

## Semantic Axis Tradeoff

| Variant | Best for | Unique stacks | Compression | Mixed weight | Residual mixed | Max variants | Default? |
|---|---:|---:|---:|---:|---:|---:|---:|
| no-semantic | system-hotspot baseline | 11967 | 15.352 | 90.402% | 44.716% | 171 | no |
| session-only | coarse session cohorting | 15027 | 12.226 | 84.407% | 33.434% | 37 | no |
| prompt-only | default system-effect task profile candidate | 24703 | 7.437 | 36.722% | 7.485% | 9 | yes |
| full | drilldown and audit | 26829 | 6.848 | 0.0% | 0.0% | 1 | yes |

Interpretation: no-semantic is compact but mixes 90.402% of system-effect weight; prompt-only is the best single semantic axis for system effects; full session+prompt is the audit view. This supports a pluggable projection design rather than one universal stack.

## Display Policy Tradeoff

| Variant | Stack count | Reduction vs raw | Unreviewed active weight | Default safe | Human gate |
|---|---:|---:|---:|---:|---:|
| raw | 26829 | 0.0% | 0.0% | yes | no |
| alias_only | 26612 | 0.809% | 0.0% | yes | no |
| profile_guarded_candidate_applied | 26067 | 2.84% | 2.532% | no | yes |
| r209_conservative_display | 26612 | 0.809% | 0.0% | yes | no |

Interpretation: R209's conservative display policy matches alias-only: it reduces fragmentation without activating profile/regeneration candidates. The more aggressive profile-guarded variant is useful as an upper-bound ablation, not a default.

## Vocabulary And Drilldown

| Variant | Unique labels | Top-20 coverage | Review-required support | Raw drilldown | Default safe |
|---|---:|---:|---:|---:|---:|
| raw-tags | 1546 | 93.683% | 1.926% | yes | yes |
| canonical-display-overlay | 1364 | 95.186% | 1.926% | yes | yes |
| r209-active-map | n/a | - | 1.926% | yes | yes |

## Claim Boundary

- Supports: RQ2 mechanism/tradeoff claim for pluggable projection over R170-derived generated evidence.
- Does not support: C5 user utility, C6 semantic adequacy, merge quality, or promotion quality.
- Next gates: R142 participant responses and R124/R190/R203 human labels.
