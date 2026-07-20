# Full Run Attempt 2 — Compact JSON Without Cross-Field Non-Empty Grammar

**Stopped:** 2026-07-19T22:47:57-07:00  
**State:** Invalid/incomplete; not scored  
**Constraint:** direct-gbnf-single-frame-compact-json-v2.2

Attempt 2 retained 20,254 valid transitions across all 405 caches. At shutdown,
388 trajectories were complete and 17 were partial. The official stage
manifest and scores remained unopened.

The compact grammar eliminated all list-length and whitespace truncation
channels. It nevertheless encoded the two fields independently when the stack
was already non-empty, so it admitted the pair keep_depth zero plus new_frame
null. The model produced that pair once. The independent transition validator
rejected the empty resulting stack and stopped the run; the invalid response
was never cached.

The v2.3 grammar now encodes the existing non-empty contract directly:

- keep_depth zero requires one label;
- positive keep_depth permits null or one label;
- the initial empty stack also requires one label.

This is a strict subset of the v2.2 compact language. It changes no semantic
prompt, evidence, model, transition, label bound, RQ, metric, or interpretation.

All 20,254 retained responses already passed the independent non-empty
validator, so each is byte-for-byte admitted by v2.3. They can be reused only
after an explicit migration audit verifies canonical compact JSON, legal depth,
label syntax, non-empty replayed stacks, frame identity, cache order, and source
identity. The invalid uncached response cannot be migrated. A fresh v2.3
preflight is still required.
