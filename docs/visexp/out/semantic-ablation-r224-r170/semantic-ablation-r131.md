# R131 Semantic-Axis Ablation

Date: 2026-06-18

Input: `.agentsight/agentflame/r170-full-current`

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
| system | no-semantic | none | 183714 | 11967 | 0.000% | 90.402% | 44.716% | 0.000 pp | 13127 |
| system | session-only | session | 183714 | 15027 | 25.570% | 84.407% | 33.434% | 5.995 pp | 10130 |
| system | prompt-only | prompt | 183714 | 24703 | 106.426% | 36.722% | 7.485% | 53.680 pp | 6310 |
| system | full | session,prompt | 183714 | 26829 | 124.192% | 0.000% | 0.000% | 90.402 pp | 6004 |
| token | no-semantic | none | 31805830937143 | 33 | 0.000% | 100.000% | 41.196% | 0.000 pp | 30462289581575 |
| token | session-only | session | 31805830937143 | 283 | 757.576% | 100.000% | 31.544% | 0.000 pp | 25366043212259 |
| token | prompt-only | prompt | 31805830937143 | 1309 | 3866.667% | 99.676% | 6.358% | 0.324 pp | 18492506870498 |
| token | llm-call-only | llm-call | 31805830937143 | 2568 | 7681.818% | 99.998% | 31.477% | 0.002 pp | 25366043637938 |
| token | prompt+llm-call | prompt,llm-call | 31805830937143 | 7382 | 22269.697% | 92.978% | 0.041% | 7.022 pp | 17869111504384 |
| token | full | session,prompt,llm-call | 31805830937143 | 8569 | 25866.667% | 0.000% | 0.000% | 100.000 pp | 17869111395752 |

## Takeaways

- System-effect stacks have no LLM-call semantic axis by construction; LLM-call labels apply to token/LLM-call accounting, while tool effects inherit session and prompt tags.
- For system effects, no-semantic projection mixes 90.402% of full semantic weight; session-only leaves 84.407%, prompt-only leaves 36.722%, and full session+prompt semantics leaves 0.000% by construction.
- For token accounting, prompt+LLM-call projection reduces mixed full semantic weight from 100.000% to 92.978%; full session+prompt+LLM-call semantics leaves 0.000% by construction.

## Top System Example

`project:agentsight;agent:codex;call:tool/tool;effect:process;status:ok`

This projected bucket has weight 13127 and
143 full semantic variants.

## Top Token Example

`project:agentsight;agent:codex;model:codex;kind:estimate`

This projected bucket has weight 30462289581575 and
4718 full semantic variants.
