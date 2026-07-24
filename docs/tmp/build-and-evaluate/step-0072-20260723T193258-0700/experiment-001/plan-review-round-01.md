# Independent Plan Review — Round 1

**Verdict:** NEEDS REVISION

## Must-fix issues

1. The raw-action comparison was not information-matched. The candidate
   included semantic frames plus source-kind/tool/outcome suffixes, while the
   proposed raw-action baseline did not. The revised plan must give both sides
   identical source-evidence suffixes and aggregation.
2. The method provenance and adaptivity were overstated. These RQ2 paths do not
   establish an online general LLM backend, and the local-first rule was already
   developed on these populations in Step 0037.
3. The plan lacked exact commands, authoritative roots, operation-ID join
   rules, and full-run completion counts.
4. The AP/MAP citation and established workload-specific resampling structures
   were missing. Zero-positive trajectories must count toward coverage but not
   enter AP/MAP.
5. AgentProf-only is a component ablation, not a third main baseline.

## Disposition

All five issues were adopted in the revised experiment plan. No new
reproducibility contract, non-Markdown gate, or extra benchmark was added.

