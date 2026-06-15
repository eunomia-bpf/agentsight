# R131 Semantic-Axis Ablation

Date: 2026-06-15

Input: `.agentsight/agentflame/latest`

Integrity:

- System total preserved: True
- Token total preserved: True
- All variant totals match their full folded input: True
- AgentFlame report totals match folded inputs: True
- Generated folded projections exactly match existing folded files: True

Definition: mixed bucket weight counts the whole projected bucket when it
contains more than one full semantic key; residual mixed weight counts only the
non-dominant semantic variants inside those mixed buckets.

## Results

| Family | Variant | Axes | Total | Unique | Growth vs no-sem | Mixed bucket weight % | Residual mixed weight % | Reduction vs no-sem | Max reuse |
|--------|---------|------|-------|--------|------------------|-----------------------|-------------------------|---------------------|-----------|
| system | no-semantic | none | 167005 | 10641 | 0.000% | 90.219% | 44.639% | 0.000 pp | 12841 |
| system | session-only | session | 167005 | 13328 | 25.251% | 84.180% | 34.138% | 6.039 pp | 10130 |
| system | prompt-only | prompt | 167005 | 22341 | 109.952% | 37.687% | 7.526% | 52.532 pp | 6291 |
| system | full | session,prompt | 167005 | 24295 | 128.315% | 0.000% | 0.000% | 90.219 pp | 6004 |
| token | no-semantic | none | 28486605753818 | 32 | 0.000% | 100.000% | 34.344% | 0.000 pp | 27143078180575 |
| token | session-only | session | 28486605753818 | 248 | 675.000% | 100.000% | 31.501% | 0.000 pp | 25366042650265 |
| token | prompt-only | prompt | 28486605753818 | 1255 | 3821.875% | 99.639% | 5.300% | 0.361 pp | 18390759787982 |
| token | llm-call-only | llm-call | 28486605753818 | 2379 | 7334.375% | 99.998% | 31.407% | 0.002 pp | 25366042700314 |
| token | prompt+llm-call | prompt,llm-call | 28486605753818 | 6802 | 21156.250% | 95.765% | 0.027% | 4.235 pp | 17869111500310 |
| token | full | session,prompt,llm-call | 28486605753818 | 7902 | 24593.750% | 0.000% | 0.000% | 100.000 pp | 17869111395752 |

## Takeaways

- System-effect stacks have no LLM-call semantic axis by construction; LLM-call labels apply to token/LLM-call accounting, while tool effects inherit session and prompt tags.
- For system effects, no-semantic projection mixes 90.219% of full semantic weight; session-only leaves 84.180%, prompt-only leaves 37.687%, and full session+prompt semantics leaves 0.000% by construction.
- For token accounting, prompt+LLM-call projection reduces mixed full semantic weight from 100.000% to 95.765%; full session+prompt+LLM-call semantics leaves 0.000% by construction.

## Top System Example

`project:agentsight;agent:codex;call:tool/tool;effect:process;status:ok`

This projected bucket has weight 12841 and
133 full semantic variants.

## Top Token Example

`project:agentsight;agent:codex;model:codex;kind:estimate`

This projected bucket has weight 27143078180575 and
4100 full semantic variants.
