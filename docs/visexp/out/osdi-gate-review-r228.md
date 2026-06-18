# R228 OSDI Gate Review After R220

Reviewer: read-only subagent `Sagan`

Status: not weak accept.

## Verdict

R220 is sufficient for a narrow C7 local clean-clone `agentpprof` smoke:
it exercises the real Rust CLI from a temporary clean clone, uses a public
synthetic Codex fixture, writes pprof/folded/JSON/SVG outputs, and verifies
`go tool pprof -top` readback. It does not support C5 user utility, C6 tag
adequacy, LLM-tag quality, external adoption, or community-ready status.

R219 correctly keeps `weak_accept_supported=false` because C5 still has no real
participant responses and C6 still has no independent human adequacy labels.

## Findings And Disposition

| Severity | Finding | Disposition |
|---|---|---|
| Blocker | C5/RQ4 still has no real developer outcome data. | Open. Requires returned R142 participant responses scored through R195. |
| Blocker | C6/RQ5 still has no independent human adequacy labels. | Open. Requires returned R124 labels and adjudication/scoring. |
| Major | R220 supports only local synthetic-fixture smoke, not external adoption or community-ready claims. | Wording already scoped in CLAIMS, R219, RESULTS_SUMMARY, and paper. |
| Major | Initial R220 oracle checked nonzero/totals/readback but not fixture-level projection correctness. | Fixed after review: R220 now checks exact expected tools/files/network stacks and reported token components. |
| Minor | Initial R220 provenance included parent worktree dirty paths. | Mitigated after review: R220 records dirty count only and states that the clean-clone oracle is the temporary clone status before fixture creation. |
| Minor | `no_real_agent_history_reads` is based on explicit session-file path control, not syscall read-set tracing. | Wording remains scoped to this smoke; no strong read-set privacy claim is made. |

## Current Gate

R220 strengthens C7 from local artifact hygiene toward local clean-clone
readback. It does not change the weak-accept gate. The next rows remain:

- P0: `R142-pilot-return` for C5/RQ4.
- P0: `R124-labels-return` for C6/RQ5.
- P1: `R190-R203-labels-return` for merge/promotion quality.
- P1: `R191-target-network-lineage` for C4 network breadth.
- P2: `R227-external-community` for external-machine/community artifact evidence.
