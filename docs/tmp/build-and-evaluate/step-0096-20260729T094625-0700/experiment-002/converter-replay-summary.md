# Strict converter mechanism replay

The replay included all 21 agent tool operations from the eight
`episodes-compatible/no-policy` trajectories used to build
`before-profile.pb.gz`: 5 operations with non-Python-identifier opaque IDs and
16 operations with valid IDs. No operation was filtered.

For each operation, `replay_converter_mechanism.py` reconstructed the versioned
ToolSandbox databases at the recorded `sandbox_message_index`, initialized the
recorded official execution console, and forked two executions through
ToolSandbox's official `ExecutionEnvironment`. BEFORE used the original opaque
ID in `openai_tool_call_to_python_code`; AFTER used the current converter rule
to derive only a safe internal Python variable while retaining the original
protocol ID. Recorded UUIDs and timestamps were supplied identically to both
arms so nondeterminism could not masquerade as a converter effect.

The reconstruction check passed: BEFORE reproduced the original response and
post-state for 21/21 operations. AFTER reduced `SyntaxError: invalid decimal
literal` failures from 5/5 affected operations to 0/5, while retaining the
original protocol ID for 21/21 operations. For all 16 valid-ID controls, BEFORE
and AFTER had identical execution responses (16/16) and identical post-states
(16/16). One repaired invalid-ID call correctly exposed the underlying
`ConnectionError: Wifi is not enabled`; the converter removed the syntax fault
without changing the ToolSandbox domain semantics.

This is mechanism evidence only. It makes no claim about model tokens, complete
scenario outcomes, or end-to-end utility. The auditable per-operation inputs,
pre-state snapshots, generated code, responses, state hashes, and checks are in
`converter-replay-results.json`; the machine-readable aggregate is in
`converter-replay-summary.json`.
