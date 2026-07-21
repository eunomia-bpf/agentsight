# Result-Grounded Task Stack — Real Preflight

## Registered Purpose

Preflight checked only real endpoint wiring, causal field separation, state
application, durable resume, output parsing, and scorer construction. Weak
semantic behavior was recorded and did not stop the complete run or trigger a
prompt/model sweep.

## Public ToolSandbox Preflight

The complete eight-turn
`mistral_nemo/nonexpert/trial-7/turn_on_wifi_low_battery_mode` trajectory ran
through the real Qwen2.5-3B endpoint. Under the authoritative r7 projection:

- all eight assistant-only outcomes were withheld from OPEN;
- the one tool-call request remained prefix-visible;
- one child was opened;
- two model CLOSE calls both returned `complete`;
- six later CLOSE steps were synthetic root-latch keeps;
- maximum depth was root plus one child; and
- no commandish, phase-like, copied-tool, or literal-`done_when` child appeared.

The same preflight then replayed from cache in about 0.1 seconds with identical
state and request hashes. The completion key, progress curve, subgoals,
model/persona, and future turns remained unavailable.

## CodeTrace Preflight

One complete session from each of five source adapters ran through the same
endpoint: five sessions, 84 source-native turns, and 100 operations. The r7
run produced:

- 51 starts and 33 continues;
- 59 real model CLOSE decisions, all `complete`;
- 25 synthetic root-latch keeps;
- depth one or two including the root;
- 13 phase-like and 14 commandish proposed child labels; and
- zero internal-frame or complete-sequence-ID leakage in 59/59 real CLOSE
  prompts.

These diagnostics already suggested semantic collapse, but the full registered
population proceeded unchanged.

## Preflight Verdict

The authoritative r7 preflights were mechanically valid and scientifically
weak. That is the intended distinction: preflight authorized full execution,
not the hypothesis or constructor.
