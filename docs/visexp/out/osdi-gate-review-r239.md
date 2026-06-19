# R239 OSDI Gate Review After R238/R170 Integration

Last updated: 2026-06-19
Stage at update: read-only subagent review plus author revision
Completeness: review artifact; no new human labels or participant responses

## Review Inputs

- Paper/research reviewer inspected the R170/R224/R238-integrated paper and
  claim documents under the OSDI rubric.
- Code/artifact reviewer inspected the R238 code path, official artifact,
  direct-only local outputs, and process-tracer readiness changes.

## Findings

The reviewers agreed on the high-level state: the work remains a strong
mechanism artifact but is not OSDI weak accept yet. C5 still has 0 participant
responses, and C6 still has 0 final human adequacy labels.

The paper/research review found four wording/evidence issues:

- `CLAIM_VERDICT.md` still used older dates and R131-era C3 numbers in the
  main C3 row.
- C4 evidence needed to include R191/R229/R232/R234/R238 in the main claim row,
  with a scoped-workload verdict rather than an R182-only summary.
- `FOLLOWUP_PLAN.md` B6x still described the old 205-session workload instead
  of the R224-on-R170 current denominator.
- The paper and tracker used wording that made the R234/R238 boundary look
  broader than the evidence supports.

The code/artifact review found five implementation/evidence caveats:

- The committed official R238 artifact supported the 4-task full-run result,
  but the 5/5 direct-only repetitions were only local `/tmp` artifacts before
  this revision.
- `command_root_pid_self_time_window` is plausible for the direct root process
  connect row, but without committed per-event rows it should not be overclaimed
  as a broad false-positive proof.
- R238 gate names blurred witness-port observation with witness-port joined
  rows, and `positive_controls_gate` really meant Codex witness-port observation.
- The readiness barrier proves process-tracer readiness, not SSL/stdout/system
  runner readiness.
- BPF PID propagation changes are plausible but still need direct runtime
  coverage for fork/exec propagation and BPF-only aggregate flushing.

## Revisions Applied

- Added `direct-only-repetition-summary-r238.{json,md}` as a compact committed
  summary of the five local direct-only repetitions. It records 10/10 direct
  tasks captured/joined and 35/35 target network rows joined, while explicitly
  stating that those repetitions had no negative controls.
- Updated `CLAIM_VERDICT.md` to the 2026-06-19 evidence boundary, including
  R224/R170 C3 numbers and a scoped C4 row covering R114/R191/R229/R232/R234/R238.
- Updated `FOLLOWUP_PLAN.md` B6x to use the R170 denominator and R224 result
  paths.
- Updated `EXPERIMENT_TRACKER.md` to mark R219's next-row list as historical
  and to distinguish the official R238 full run from the direct-only readiness
  supplement.
- Updated `RESULTS_SUMMARY.md`, `EXPERIMENT_AUDIT.md`, and `paper/main.tex`
  to call R238 a process-tracer readiness and boundary-localization result, not
  broad Claude-launched or arbitrary network coverage.
- Updated `r237_agent_execution_witness_network_capture.py` to emit clearer
  future gates: witness-port observed vs joined, Codex witness observed, and
  direct orphan resolved. Legacy gate names remain for backward compatibility
  with existing artifacts.

## Current Verdict

The R238 integration strengthens C4 in a narrow way: direct `record --` target
network capture is no longer blocked by the process-tracer readiness race, and
the official full run preserves negative-control precision. It also makes the
remaining boundary sharper: Codex/Claude-launched target-network rows still
have three orphan or missing-action cases.

This does not change the weak-accept gate. The next non-substitutable evidence
remains:

- C5: real R142/R151 participant responses.
- C6: real R124/R190/R203 human labels.
- C4: follow-up for Codex/Claude-launched target-network process-time matching
  and Claude/Bun thread/process attribution.
- C7: external fresh-clone/community feedback beyond local smoke tests.
