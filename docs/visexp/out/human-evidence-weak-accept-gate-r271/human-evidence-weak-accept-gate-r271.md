# R271 Human Evidence Weak-Accept Gate

Status: `awaiting_private_c5_and_c6_returns`

## Component Status

- C5/R268: `awaiting_private_c5_returns`; supported=`False`.
- C6/R270: `awaiting_private_c6_labels`; supported=`False`.

## Commands

```bash
python3 docs/visexp/r268_c5_real_return_scoring_pipeline.py
python3 docs/visexp/r270_c6_real_label_scoring_pipeline.py
```

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Human evidence ready for OSDI review: `False`.
- Weak accept supported: `False`.
- Requires independent OSDI review: `False`.

## Boundary

R271 only joins public-safe aggregate gates from R268 and R270. It does not read or export raw private rows, create participant responses, create human labels, or replace the final independent OSDI review. Global weak-accept support remains false until real C5/C6 evidence is present and reviewed.

## Next Action

Collect private C5 responses and private C6 labels, run this script, resolve any C6 adjudication reported by R270, then run an independent OSDI review before updating public paper claims.
