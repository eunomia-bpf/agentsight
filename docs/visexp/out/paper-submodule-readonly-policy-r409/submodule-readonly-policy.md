# R409 English Submodule Read-Only Policy Gate

Status: `pass`
Checks: 12/12
Push safety: `unsafe_due_to_ahead_submodule_gitlink`

The current outer-repo workflow can continue Chinese-paper and evidence work while treating docs/agentpprof-paper as read-only. English-paper sync gaps are recorded by R405/R397/R398/R399, not repaired by editing the submodule. A direct push remains unsafe when the ahead history contains a submodule gitlink update.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| root_matches_requested_worktree | True | ROOT=/home/yunwei37/workspace/agentsight-research-semantic-flamegraph expected=/home/yunwei37/workspace/agentsight-research-semantic-flamegraph |
| branch_is_research_v2 | True | branch=research/semantic-flamegraph-artifacts-v2 |
| agents_policy_forbids_submodule_edits | True | AGENTS/CLAUDE contain the read-only submodule policy and Chinese-paper separation rule. |
| submodule_not_staged | True | No staged parent-index change for docs/agentpprof-paper. |
| submodule_dirty_state_recorded_not_cleaned | True | Submodule dirty status is recorded and intentionally left alone: ['M main.pdf', ' M references.bib', '?? scripts/verify_bib.py'] |
| r405_gap_audit_passes | True | R405 records read-only English submodule scope and the current 3+1 sync gap. |
| r397_uses_gap_aware_policy | True | R397 passes with English synced or R405-recorded read-only gap. |
| r398_uses_gap_aware_policy | True | R398 treats Chinese as writable authority and English as synced or R405-recorded gap. |
| r399_uses_gap_aware_policy | True | R399 checks Chinese PDF freshness and routes English drift through R405. |
| canonical_docs_record_readonly_policy | True | Canonical docs describe R405 English read-only gap handling and avoid submodule edits. |
| direct_push_safety_explicit | True | push_safety=unsafe_due_to_ahead_submodule_gitlink; upstream=origin/research/semantic-flamegraph-artifacts-v2 |
| source_status_tracked_or_dirty_allowed | True | All R409 sources are tracked or intentionally dirty while the gate is generated. |

## Submodule

```json
{
  "ahead_history_changes_submodule": true,
  "cached_dirty": false,
  "parent_index": "b6672cbf3e2316af67b5312ca3f1d1dee32b9ab4",
  "push_safety": "unsafe_due_to_ahead_submodule_gitlink",
  "submodule_head": "138b7a3ad3b6ae794ebf6c86ea94e8feaf8da86e",
  "summary": "submodule_head=138b7a3ad3b6ae794ebf6c86ea94e8feaf8da86e;parent_index=b6672cbf3e2316af67b5312ca3f1d1dee32b9ab4",
  "unstaged_dirty": true,
  "upstream": "origin/research/semantic-flamegraph-artifacts-v2",
  "worktree_status": [
    "M main.pdf",
    " M references.bib",
    "?? scripts/verify_bib.py"
  ]
}
```
