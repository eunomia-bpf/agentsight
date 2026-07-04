# R297 Operation Boundary Backend

This run is an expansion probe over existing OSWorld-Human operations. It trains a held-out adjacent-boundary backend from non-oracle operation fields, writes predicted `learned_group` fields back to test operations, and leaves recursive folding to the Rust profiler.

## Result

- Learned backend: precision 0.74, recall 0.8102, F1 0.7735 over 1036 held-out adjacent pairs.
- Baselines: phase-change F1 0.2919, action-change F1 0.5142, group-pattern reference F1 0.581, always-boundary F1 0.709.
- Scope: this is supervised label-derived boundary prediction, not unsupervised intent discovery.

## Generated Operation Fields

- `learned_group`: predicted session-local group id for the held-out operations.
- `learned_group_pattern`: cross-session action pattern derived inside each predicted group.
- `learned_group_position`: start/middle/end/single inside the predicted group.
- `learned_boundary_prev`: whether the current operation starts a predicted boundary.

## Files

- `augmented_operations`: `docs/visexp/out/operation-boundary-backend-r297/osworld-learned-boundary-test-operations.jsonl`
- `profile_spec`: `docs/visexp/out/operation-boundary-backend-r297/learned-boundary-profile-spec.json`
- `json`: `docs/visexp/out/operation-boundary-backend-r297/boundary-backend-report.json`
- `markdown`: `docs/visexp/out/operation-boundary-backend-r297/boundary-backend-report.md`
- `html`: `docs/visexp/out/operation-boundary-backend-r297/boundary-backend-report.html`
