# Task spec: recompute and durably record every Case Study 2 quantity

You are an autonomous engineering agent in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Deterministic recomputation only — no LLM calls, no re-annotation. Never
modify existing files; never run git commands. All deliverables go in THIS
directory. Use /home/yunwei37/workspace/.venv/bin/python3.

## Quantities to recompute from the frozen artifact

From the frozen recursive workspace
(`docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/` with
`trace.jsonl`, `annotation.json`, `stacks.folded`) and the same pair
manifest and expert labels that `script/agentreward_diff_pprof_eval.py`
reads (inspect it READ-ONLY to locate them):

1. Pair-occurrence-weighted totals: bad-side and good-side operation
   occurrences over the 338 pairs (paper: 7,366 / 3,780).
2. Occurrences under the shared recovery responsibility per side
   (paper: 3,286 / 455 under `recover interaction`) and under the
   completion responsibility (paper: 135 / 191). Document the exact path
   prefix used for each.
3. Recovery share of each side (paper: 44.6% / 12.0%) and completion share
   (paper: 1.8% / 5.1%).
4. Recovery-exposure AP against the 435 consensus expert looping labels
   (paper: .634; prevalence .398), the 10,000-draw task-cluster bootstrap
   interval for AP-minus-prevalence (paper: [.181,.293]), the registered
   fixed-chain projection AP (paper: .656), and the recursive-minus-fixed
   interval (paper: [-.107,.061]). Reuse the exact scoring/bootstrap code
   paths of the existing harness where possible; document seeds.

## Deliverables

- `recompute_cs2.py` — complete deterministic script.
- `primary-record.json` — every quantity with value, definition, input
  file paths and sha256 checksums, seed, and the paper's currently
  displayed value alongside.
- `results.md` — a table: quantity | paper value | recomputed value |
  match/mismatch. For any mismatch, state the recomputed value as the
  authoritative one. Include the exact frozen-artifact identity (paths +
  checksums) so the case study is version-pinned.
- `execution-log.md` — commands and wall time.

If a required input (e.g., the pair manifest or looping labels) cannot be
located, STOP and write results.md describing exactly what is missing.
