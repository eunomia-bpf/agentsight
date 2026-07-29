Read-only independent result review. Do not edit any file.

Review this completed experiment against:
- plan.md
- plan-review.md
- execution-log.md
- raw-results.json
- results.md
- format-repairs.jsonl
- flat_annotation/annotate.py
- flat_annotation/postprocess.py
- score/operation-score-rows.jsonl
- score/pair-score-rows.jsonl
- bootstrap-bcubed-f1.json
- bootstrap-boundary-f1.json

Recompute or directly check the key metrics and intervals. Pay particular
attention to the author-approved mechanical normalization of ordinal 118:
two marks with a complete path identical to the preceding mark were deleted,
and the implementation requires the expanded path for every operation to
remain identical. Determine whether this affects semantic assignments or
boundary scores, whether all 405 trajectories are included, whether the
hierarchy and flat populations are matched, and whether the conclusion
"positive point estimates but statistically inconclusive on both registered
metrics" follows.

Return concise Markdown with:
1. run status: valid / invalid / incomplete
2. tested hypothesis: supported / contradicted / inconclusive
3. recomputed key numbers
4. any blocking issue
5. paper-safe interpretation
