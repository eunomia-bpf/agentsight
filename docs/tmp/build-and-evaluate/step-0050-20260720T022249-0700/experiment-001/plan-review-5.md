# Experiment 001 Plan Review 5

- reviewed: 2026-07-20T03:15:10-07:00
- reviewer: independent subagent after rereading `research-experiment-design`
- verdict: **REVISE**

## Judgment

The Round 4 causal-interface repairs are implemented correctly: exact
per-operation JSON/GBNF, state persistence, semantic-label restrictions,
separate planner and causal output limits, algorithm/cache v2, source-only
preflight, byte-identical current evidence, and rejection of old array caches.

## Blocking Repairs

1. Add the required `--target-operations` argument to the registered score
   command.
2. Make `promising-not-adopted` follow the registered rule: the candidate beats
   both main comparators in point estimate but at least one interval crosses
   zero. Descriptive controls do not participate in that classification.
3. Describe preflight selection honestly as the largest source-evidence
   character estimate per framework, not the population's exact largest causal
   token request, and replace the stale full-trajectory-array module text.

No other full-population validity defect was found.
