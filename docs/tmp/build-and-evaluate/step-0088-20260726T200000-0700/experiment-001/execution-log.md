# Execution log

- Frozen source: `docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl`.
- Backend: `codex exec --model gpt-5.6-sol`; one isolated call per session and at most one format retry.
- Instruction: loaded verbatim from Step 0087 at execution time; only the source packet format changes.
- Model-visible operation fields: `action`, `phase`, `target`, `repeat_state`, `repeat_signal`, `app`, `environment`, `status`, `tool`.
- Gold/scorer-only fields excluded from every packet: `human_group`, `group_index`, `group_position`, `group_size`, `group_pattern`, `group_alignment`.
- No Git command is part of this experiment.

## Events

- 2026-07-26T21:43:17-07:00 — `prepare`: operations=3978, pairs=3691, pilot_sessions=40, sessions=287
- 2026-07-26T21:43:26-07:00 — `pilot-backend-start`: cached=0, pending=40, selected=40, timeout_seconds=1200, workers=4
- 2026-07-26T21:45:16-07:00 — `pilot-backend-finish`: complete=40, failures=0, selected=40
- 2026-07-26T21:45:40-07:00 — `pilot-score`: direct_bcubed_f1=0.6568026158959439, direct_boundary_f1=0.20994475138121543, gate_passed=true, recurrence_bcubed_f1=0.7032664969792927, valid=true
- 2026-07-26T21:45:57-07:00 — `full-backend-start`: cached=40, pending=247, selected=287, timeout_seconds=1200, workers=4
- 2026-07-26T21:56:15-07:00 — `full-backend-finish`: complete=287, failures=0, selected=287
- 2026-07-26T21:56:52-07:00 — `full-score`: direct_bcubed_f1=0.448069247675728, direct_boundary_f1=0.14923907707412862, gate_passed=null, recurrence_bcubed_f1=0.7861695437481887, valid=true
