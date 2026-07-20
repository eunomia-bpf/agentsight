# Experiment 003 — Real Preflight v2.3

**Timestamp:** 2026-07-19T22:19:00-0700  
**Status:** PASS; full execution may continue  
**Tested component:** constrained single-frame transition policy only  
**Official stage labels opened:** no

## Executed configuration

- Model: local Qwen2.5-3B-Instruct Q4_K_M through llama.cpp.
- Model SHA-256: `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.
- Seed: `20260719`; temperature: `0`.
- Output contract: `direct-gbnf-single-frame-nonempty-v2.3`.
- Input: one complete public trajectory from each of the four CodeTraceBench frameworks.
- Population: 4 trajectories and 196 operations.
- Visible evidence: de-slugged public task identity, current stack labels, preceding observation, and current action.
- Hidden throughout inference: official manifest, official stages, and all current scoring results.

## Result

All 196 operations produced legal, non-empty stack transitions. The resulting
depth ranged from 1 to 4 (mean 2.2041). Re-executing the command from the four
completed per-session caches produced a byte-identical predictions file with
SHA-256 `db17fff7fa0bf12cf73b7ba9e1588911f9cbb7e481879128127c3c86d4601f5d`.

The transition distribution was 28 pushes and 168 sibling replacements. Every
operation still introduced a new frame (`new_frame_rate = 1.0`). This is a
source-only diagnostic, not a stage-fidelity score. It confirms that the legal
variable-depth state machine runs correctly but that raw Qwen leaves are too
fine-grained to serve directly as semantic operations.

## Decision

Continue the approved Experiment 004 plan: preserve the uncapped raw stack,
add an immutable task root, and contract generated frame instances that do not
span at least two operations. This changes neither the model outputs nor the
research question; it defines which generated frames have enough temporal
support to count as operations. Materialize the contracted partition before
opening official stages, then perform the registered complete-population score.

