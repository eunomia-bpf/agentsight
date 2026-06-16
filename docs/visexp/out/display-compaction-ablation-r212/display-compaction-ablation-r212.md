# R212 Display-Compaction Ablation

Status: `display_compaction_ablation_ready_no_quality_claims`

## Boundary

- Reads generated R170/R196/R209 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM.
- Applies display compaction only to session/prompt tags in semantic-system stacks; LLM/token display compaction is out of scope for this run.
- Reports display-policy mechanics only; false-merge and missed-merge rates remain `n/a` until human labels exist.

## Variant Summary

| variant | stacks | session tags | prompt tags | affected weight pct | unreviewed profile weight pct |
|---|---:|---:|---:|---:|---:|
| `raw` | 26829 | 53 | 263 | 0.0 | 0.0 |
| `alias_only` | 26612 | 48 | 241 | 1.188 | 0.0 |
| `profile_guarded_candidate_applied` | 26067 | 45 | 216 | 3.72 | 2.532 |
| `r209_conservative_display` | 26612 | 48 | 241 | 1.188 | 0.0 |

## Selected Behavior Ambiguity

| behavior | variant | distinct prompts | ambiguous share pct | top prompt splits |
|---|---|---:|---:|---|
| `process:git;effect:read;status:ok` | `raw` | 146 | 66.966 | refactor=5625; review=3879; design=868; test=781; analyze=685; research=571; docs=365; explain=291 |
| `process:git;effect:read;status:ok` | `alias_only` | 133 | 66.966 | refactor=5625; review=3879; design=884; test=805; analyze=685; research=571; docs=567; explain=291 |
| `process:git;effect:read;status:ok` | `profile_guarded_candidate_applied` | 116 | 66.937 | refactor=5630; review=3911; test=1074; design=984; analyze=702; research=571; docs=569; explain=291 |
| `process:git;effect:read;status:ok` | `r209_conservative_display` | 133 | 66.966 | refactor=5625; review=3879; design=884; test=805; analyze=685; research=571; docs=567; explain=291 |
| `process:cargo;effect:test;status:ok` | `raw` | 62 | 63.778 | refactor=1346; review=644; research=250; design=188; commitlog=174; designcodex=141; explain=131; analyze=124 |
| `process:cargo;effect:test;status:ok` | `alias_only` | 57 | 63.778 | refactor=1346; review=644; research=250; design=213; commitlog=174; designcodex=141; test=137; explain=131 |
| `process:cargo;effect:test;status:ok` | `profile_guarded_candidate_applied` | 52 | 63.778 | refactor=1346; review=644; design=354; research=250; commitlog=174; test=149; explain=131; analyze=124 |
| `process:cargo;effect:test;status:ok` | `r209_conservative_display` | 57 | 63.778 | refactor=1346; review=644; research=250; design=213; commitlog=174; designcodex=141; test=137; explain=131 |
| `process:rg;effect:read;status:ok` | `raw` | 175 | 56.707 | refactor=13890; review=6811; design=2922; analyze=981; test=911; benchmark=783; research=674; docs=530 |
| `process:rg;effect:read;status:ok` | `alias_only` | 161 | 56.707 | refactor=13890; review=6811; design=3100; analyze=981; test=916; benchmark=783; docs=741; research=674 |
| `process:rg;effect:read;status:ok` | `profile_guarded_candidate_applied` | 142 | 56.654 | refactor=13907; review=6919; design=3492; test=1064; analyze=1013; benchmark=783; docs=755; research=678 |
| `process:rg;effect:read;status:ok` | `r209_conservative_display` | 161 | 56.707 | refactor=13890; review=6811; design=3100; analyze=981; test=916; benchmark=783; docs=741; research=674 |
| `process:sed;effect:read;status:ok` | `raw` | 180 | 55.845 | refactor=13514; review=5006; design=2918; test=1213; analyze=1153; benchmark=1001; research=930; docs=494 |
| `process:sed;effect:read;status:ok` | `alias_only` | 165 | 55.845 | refactor=13514; review=5006; design=2920; test=1218; analyze=1153; benchmark=1005; research=930; docs=727 |
| `process:sed;effect:read;status:ok` | `profile_guarded_candidate_applied` | 146 | 55.803 | refactor=13527; review=5018; design=3151; test=1472; analyze=1180; benchmark=1005; research=932; docs=727 |
| `process:sed;effect:read;status:ok` | `r209_conservative_display` | 165 | 55.845 | refactor=13514; review=5006; design=2920; test=1218; analyze=1153; benchmark=1005; research=930; docs=727 |

## Claim Boundary

R212 conserves total system-effect weight across all variants: `True`. The conservative R209 display policy is alias-only equivalent: `True`. The profile-guarded variant is reported as a hypothetical candidate-applied view, not a reviewed default. R212 cannot support semantic adequacy, merge quality, developer utility, or community adoption.
