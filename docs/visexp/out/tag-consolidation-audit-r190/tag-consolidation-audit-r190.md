# R190 Tag Consolidation Audit

Status: `tag_consolidation_audit_packet_ready`

## Scope

- Reads generated R170/R189-style artifacts only; raw traces are not read or mutated.
- Produces risk proxies and a blank audit packet; it is not human adequacy evidence.

## Ablation Summary

| variant | prompt-effect tags | llm-event tags | system stacks | token stacks |
|---|---:|---:|---:|---:|
| raw | 263 | 1423 | 26829 | 8569 |
| alias_only | 241 | 1392 | 26612 | 8190 |
| lexical_only | 200 | 868 | 25985 | 7169 |
| profile_guarded_current | 216 | 1254 | 26067 | 7661 |

## Risk Proxies

- Over-merge proxy rows exported: 80.
- Under-merge proxy rows exported: 80.
- Applied merges by reason: `{'llm': {'applied_merges': 171, 'review_suggestions': 104, 'applied_merges_by_reason': {'alias': 31, 'lexical+profile': 140}, 'applied_support_by_reason': {'alias': 645, 'lexical+profile': 727}, 'dictionary_alias_merges': 31, 'lexical_profile_merges': 140, 'profile_only_merges': 0, 'non_alias_profile_similarity': {'count': 140, 'min': 0.42, 'p50': 0.661, 'p90': 0.865, 'max': 1.0}}, 'prompt': {'applied_merges': 49, 'review_suggestions': 9, 'applied_merges_by_reason': {'alias': 24, 'lexical+profile': 25}, 'applied_support_by_reason': {'alias': 2185, 'lexical+profile': 3404}, 'dictionary_alias_merges': 24, 'lexical_profile_merges': 25, 'profile_only_merges': 0, 'non_alias_profile_similarity': {'count': 25, 'min': 0.456, 'p50': 0.64, 'p90': 0.736, 'max': 0.91}}, 'session': {'applied_merges': 11, 'review_suggestions': 1, 'applied_merges_by_reason': {'alias': 8, 'lexical+profile': 3}, 'applied_support_by_reason': {'alias': 117, 'lexical+profile': 1566}, 'dictionary_alias_merges': 8, 'lexical_profile_merges': 3, 'profile_only_merges': 0, 'non_alias_profile_similarity': {'count': 3, 'min': 0.538, 'p50': 0.668, 'p90': 0.668, 'max': 0.818}}}`.
- Scoring command after two independent labeler sheets: `python3 docs/visexp/r190_score_merge_audit.py --labeler-1 <sheet1> --labeler-2 <sheet2> --adjudication <adjudication.csv>`.

## Interpretation Boundary

R190 can say which consolidation rules account for tag-count reductions and which rows need human audit. It cannot say the merges are semantically correct until the audit labels are collected.
