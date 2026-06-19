# R241 OSDI Gate Review After R240 Regression Guards

Last updated: 2026-06-19
Stage at update: read-only subagent review plus author response
Completeness: review artifact; no new human labels or participant responses

## Review Inputs

- Read-only subagent reviewed the repository at commit `77e6b71` on branch
  `research/semantic-flamegraph-artifacts`.
- Inputs included `docs/visexp/paper/main.tex`,
  `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/EXPERIMENT_TRACKER.md`,
  `docs/visexp/RESULTS_SUMMARY.md`, `docs/visexp/EXPERIMENT_AUDIT.md`,
  `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/out/lineage-guard-r240/`,
  `bpf/tests/test_process_runtime.py`, and `collector/src/cmd_exec.rs`.
- The review used the OSDI/SOSP claim-evidence rubric and did not edit files or
  rerun tests.

## Verdict

The project remains Level 3 conference-paper mechanism evidence, not Level 4
systems narrative. Weak accept is not supported.

The review agrees that C1-C3 are credible mechanism/characterization claims, C4
is supported only for fixed and controlled scoped workloads, C7 is partial
artifact usability, and C5/C6 remain the blocking gates.

## Findings

### Blockers

- C5 still has no outcome data. The existing task packet, preregistration,
  response contract, and launch bundle are protocol evidence only; no real
  participant responses have been scored.
- C6 still has no human adequacy labels. Syntax/stability, LLM outputs,
  synthetic labels, and subagent review do not count.
- User-utility baselines/outcomes remain missing. The current paper correctly
  names `event-count-proxy` and prompt wall-clock duration as limited baselines,
  not true span-duration evidence.

### Major Issues

- R240 does not change the weak-accept gate. It is correctly scoped as C4
  regression evidence and does not prove broad Claude-launched/raw-socket
  coverage or affect C5/C6.
- R240 provenance needed cleanup: the committed artifact before this response
  recorded `commit: 34c651b` and `working_tree_dirty: true`, while the review
  target was `77e6b71`.
- R240's machine-readable artifact recorded only the synthetic lineage guard,
  while the tracker also cited BPF and Rust regression tests.
- `CLAIM_VERDICT.md` omitted R220 from the C7 evidence row even though tracker,
  results, and paper already discussed the `agentpprof` clean-clone smoke.

### Minor Issues

- The BPF target-child network test should port-match the target child
  `NET_BIND` row instead of only checking type presence.
- The paper's C4 table verdict `controlled-suite only` was too narrow given
  R229/R232/R234; it should say fixed and controlled scoped workloads are
  supported while broad coverage remains partial.

## Author Response

- Regenerate R240 from a clean worktree at `77e6b71` before this revision, so
  the artifact records clean provenance for the reviewed state.
- Extend the R240 artifact schema to record external regression commands:
  `make -C bpf test` and
  `cd collector && cargo test wait_for_process_runner_start`.
- Strengthen the BPF target-child network runtime test to port-match the target
  child `NET_BIND` and `NET_CONNECT` summaries. `NET_LISTEN` remains a type
  assertion because the current summary may expose fd-level detail instead of a
  port.
- Add R220 to the C7 claim-verdict evidence as local clean-clone
  `agentpprof`/pprof-readback evidence only.
- Update the paper table's C4 verdict to
  `supported for fixed and controlled scoped workloads; partial broadly`.

## Current Gate

The smallest next non-substitutable artifact remains a real R142
five-participant pilot scored through the existing response contract, followed
by R124/R190/R203 human labels for C6 and canonicalization/promotion quality.
Subagent review, synthetic fixtures, LLM labels, and mock responses do not
close those gates.
