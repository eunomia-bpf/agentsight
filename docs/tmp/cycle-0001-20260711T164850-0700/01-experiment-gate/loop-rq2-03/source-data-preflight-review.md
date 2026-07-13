# Independent Source/Data Preflight Review

**Initial verdict:** REVISE  
**Final status:** factual corrections applied; experiment remains not approved

The independent reviewer reproduced the repository revision, four file hashes,
inventory, success/call counts, matched task/trial-index matrices, call/result
adjacency, ID reuse, additive-measure availability, and official reward code.
It agreed that tau-bench has no independent operation-linked failure oracle and
must not support the proposed first-fault inspection experiment.

Three corrections were required and applied to `source-data-preflight.md`:

1. Fourteen episodes reach the 30-step limit without termination; ten remain in
   the trials-0--3 model comparison. Observed prefixes pass, universally
   complete terminated episodes do not.
2. Output requirements are usually combined with mutation actions. Final reward
   is the database-state and output-check conjunction, while the output branch
   overwrites diagnostic `info`; it is still task-level, not call-level.
3. Shared `(task_id, trial ordinal)` cells are a matched index matrix, not proof
   of identical user transcripts or common random numbers.

Final source suitability is partial. The full step-inspection experiment is not
approved because of missing operation-linked decision evidence, not because RQ2
is too broad. No files, skills, or Git state were changed by the reviewer.
