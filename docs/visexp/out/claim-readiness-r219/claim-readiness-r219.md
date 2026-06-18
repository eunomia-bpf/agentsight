# R219 Claim Readiness Gap Gate

Status: `osdi_weak_accept_not_supported`

R219 is a reviewer-facing claim-readiness audit over generated artifacts.
It does not read raw agent traces, does not call an LLM, and does not count synthetic or subagent evidence as C5/C6 support.

## Summary

- R170 full-history sessions: 325.
- R170 system observations: 183714.
- R180 valid outputs: 2700/2700.
- R114 command-mode precision/recall: 100.0%/100.0%.
- R191 target network joined: 4/4.
- R229 controlled replication: 5 tasks, 394 in-scope effects, 0/306 negative joins, raw join 394/1080 = 36.481%.
- R230 full-history projection: 183714 folded weight, missing frame weight 0, tool prompt-index coverage 100.0%, duplicate prompt-index rows 12, prompt-tag drift 346 weight (0.188%), LLM drift 93 events (0.081%).
- R231 drift root cause: display projection exact true, R230 reproduced true, field drift localized true, unique-index field drift 0 tool weight/0 LLM events, external cross-repo supported false.
- R217 production display buckets/support: 1748/482398.
- R218 preview accepted/rejected rows: 2/4.
- C5 participant responses: 0.
- C6 final adequacy labels: 0.

## Verdict

- Weak accept supported: `False`.
- Human evidence supported: `False`.
- Blockers: ['C5/RQ4 has no supported real participant outcome', 'C6/RQ5 has no supported independent human adequacy labels'].
- Open scope gaps: ['C4 strict prompt-row/full-history lineage remains open', 'C4 external cross-repo live exact-lineage replication remains open', 'C7 external-machine/community evidence remains open'].

## Claim Rows

- C1 semantic folded stacks over real histories: `supported`. Next: rerun only after parser/tagger changes
- C2 local one-word tagging feasibility: `supported_for_syntax_latency`. Next: collect R124 labels before claiming adequacy
- C3 semantic partitioning and display mechanics: `supported_as_mechanism`. Next: C5 participant study and R190/R203 human review labels
- C4 exact semantic-effect lineage: `supported_for_fixed_command_mode_suite`. Next: normalize/fix Claude duplicate prompt-index semantics and run external cross-repo live exact-lineage replication
- C5 developer utility: `unsupported`. Next: collect and score R142 pilot responses through R195
- C6 tag adequacy and merge/promotion quality: `partial_syntax_stability_only`. Next: collect R124/R190/R203 paired labels and score through R195
- C7 community/open-source usefulness: `partial`. Next: external-machine fresh clone plus real-report sanitization and developer-feedback audit

## RQ Rows

- RQ1 feasibility/cost: `supported`. Next: rerun after implementation changes only
- RQ2 semantic partitioning: `supported_as_mechanism`. Next: R142 C5 outcomes
- RQ3 exact lineage: `supported_for_fixed_command_mode_suite`. Next: normalize/fix Claude duplicate prompt-index semantics and run external cross-repo live exact-lineage replication
- RQ4 developer utility: `unsupported`. Next: collect real R142 responses
- RQ5 tag adequacy: `partial`. Next: collect paired R124/R190/R203 labels
- RQ6 artifact/community: `partial`. Next: external-machine smoke and public real-report audit

## Next Experiments

- P0 R142-pilot-return: Score real developer responses for the frozen semantic-vs-baseline forensic tasks.
- P0 R124-labels-return: Score independent human adequacy labels for one-word session/prompt/LLM-call tags.
- P1 R190-R203-labels-return: Score merge-risk and regenerated-label promotion quality before any display-map promotion claim.
- P1 R232-external-crossrepo-lineage: Replicate live exact-lineage on an external cross-repo controlled workload.
- P1 R233-prompt-row-lineage-normalization: Normalize or fix Claude duplicate prompt-index semantics so generated reports can support strict prompt-row lineage.
- P2 R227-external-community: Run agentpprof on an external machine or container with a real sanitized report audit and developer-feedback checklist.

## Disallowed Evidence

- subagent review
- LLM-filled labels
- synthetic review fixtures
- empty launch packets
- syntax-only tag validity
