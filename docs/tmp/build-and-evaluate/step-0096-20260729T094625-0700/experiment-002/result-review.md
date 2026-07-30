# Independent Confirmation Result Review

## Verdict

PASS. The fixed confirmation supports the efficiency-with-noninferior-official-
similarity branch. It is decisive for this profiling-utility case and
supporting evidence for RQ2.

## Evidence checked

- All 69 pairs completed: 23 scenarios, three repetitions per scenario, and
  138 official ToolSandbox evaluations. Every cell is included.
- The eight pilot scenarios and 23 confirmation scenarios are disjoint; the
  preflight scenario is excluded. The run log contains exactly 138 unique
  successful confirmation records, without retries, replacements, or
  outcome-based selection.
- Both conditions use the same local model, sampling, scenario seed, empty
  policy, official ToolSandbox commit, and official evaluator. The repair
  changes only the mapping from an opaque protocol ID to an internal executable
  Python variable while retaining the original ID in assistant/tool history.
- BEFORE generated 28 raw-invalid IDs and incurred 28 Python syntax failures.
  CONVERTER-FIX generated 19 raw-invalid IDs and incurred zero syntax failures.
  Protocol-history mismatch is zero in both arms.
- The exact-state replay covers all 21 operations that formed the diagnosis
  profile. It removes 5/5 affected syntax failures, preserves all 21 protocol
  IDs, and leaves response and post-state unchanged for all 16 valid-ID
  controls.

## Independently reproduced confirmation

- Agent-side model tokens: 211,222 BEFORE versus 171,139 CONVERTER-FIX, a
  ratio of 0.8102 or 18.98% lower. The planned scenario-cluster bootstrap 95%
  interval is `[0.7336, 0.9212]`.
- Official similarity: 0.83105 versus 0.85721, a point delta of +0.02616. The
  scenario-cluster interval is `[-0.02221, 0.07629]`.
- Model calls: 255 versus 227.
- Tool calls: 159 versus 137.
- Turns: 457 versus 401.
- Exact successes: 8 versus 9; its interval crosses zero.

A separate 100,000-draw scenario-cluster bootstrap with another random seed
returned a token-ratio interval of `[0.7342, 0.9237]` and a similarity-delta
interval of `[-0.0232, 0.0754]`, leaving the decision unchanged.

## Strongest supported claim

Across 23 ToolSandbox scenarios isolated from the final repair's development
pilot, each repeated three times, a converter repair derived from an AgentProf
profile eliminated the observed opaque tool-call-ID syntax failures and
reduced agent-side model token volume by 19.0% (scenario-cluster 95% CI for
AFTER/BEFORE `[0.734, 0.921]`). Official task similarity was non-inferior under
the fixed −0.05 margin; its point estimate changed by +2.6 percentage points
with a 95% interval of −2.2 to +7.6 points.

## Required boundaries

- Do not claim a significant success-rate or official-similarity increase.
- Do not claim that AgentProf is faster than raw-log debugging or uniquely
  necessary to find this problem. No human developer time was measured.
- Agent-side model token volume is not dollar cost or wall-clock time.
- This is one compatibility-layer repair on one model and benchmark, not a
  general reasoning-policy result or a claim about all tool-call defects.
- The 23 scenarios are isolated from this final repair's pilot, not an
  untouched benchmark unknown to the broader project.
- The server's opaque-ID allocator is not controlled by the request seed, so
  the conditions are not strict common-randomness trajectory pairs. Complete
  intention-to-treat analysis, three repetitions, and scenario-cluster
  bootstrap address but do not remove this nuisance.
- Fault exposure differs between conditions (28 versus 19). The 19% result is
  the intention-to-treat effect over these randomized executions, not a fixed
  per-invalid-ID saving.
- The exact-state replay is mechanism evidence only; it does not establish the
  end-to-end token or task result by itself.
- Earlier policy and response-ID-normalization attempts remain development
  records and do not enter the confirmation evidence.
