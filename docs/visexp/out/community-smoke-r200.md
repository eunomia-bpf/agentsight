# R200 Community Smoke

Status: `community_smoke_passed`

## Claim Boundary

R200 verifies a public-safe generated-fixture AgentFlame run, output completeness, prompt redaction, and fixed-input cache behavior. It is C7 artifact-hygiene evidence only; it does not support C5 developer utility, C6 tag adequacy, full-history exact lineage, or community adoption.

## Run Summary

- Clean run return code: `0`.
- Cached run return code: `0`.
- Clean llama.cpp calls: `5`.
- Cached llama.cpp calls: `0`.
- Cached cache hits: `5`.
- System observations: `6`.

## Privacy

- Reads real `.codex`/`.claude` traces: `False`.
- Fixture contains private prompts: `False`.
- Non-redacted prompt previews in committed report: `0`.

## Gate

- C7 artifact smoke passed: `True`.
- Community adoption supported: `False`.
- C5/C6 supported: `False`.

## Boundary

R200 is a public-safe artifact smoke over a generated fixture. It does not replace full-history traces, C5 participant evidence, or C6 human tag labels.
