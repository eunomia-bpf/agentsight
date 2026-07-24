# Real Preflight Report

**Status:** PASS — not a paper result

The approved command completed on retained real artifacts. Before reading any
target label, the implementation:

- joined all 27,346 operation IDs one to one across the three fixed path roots
  and benchmark projections;
- constructed candidate, information-matched raw, local-only, and
  AgentProf-only rank vectors;
- verified that both local-first variants preserve every strict local-score
  ordering;
- verified that equal rank keys remain tied; and
- accepted no target or correctness column in the rank constructor.

One target-bearing query per workload was then scored. AgentProf-only AP exactly
matched the corresponding Step 0071 per-query AP in all three workloads. The
preflight consumed all 1,756 trajectories for coverage validation but its three
query scores are not scientific results.

The preflight completed successfully in 1.3 seconds.

