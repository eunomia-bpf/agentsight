# R249 Paper-Scale C5 Collection Package

Status: `paper_scale_launch_ready_no_responses`

This package derives a twelve-participant paper-scale C5 launch package from
the frozen R142 task packets. It contains blinded participant packets, a blank
paper-scale response CSV, and assignments for scoring. It contains no answer
key and no participant responses.

Participants: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12

Coordinator steps:

1. Send each participant only their matching `participants/Pxx.md` or `participants/Pxx.json`.
2. Fill `responses/user-task-response-template-r249-paper.csv` only with real participant responses.
3. Score completed responses with:

```bash
python3 docs/visexp/score_user_task_results.py \
  --responses docs/visexp/out/user-task-paper-r249/responses/user-task-response-template-r249-paper.csv \
  --bundle docs/visexp/out/user-task-benchmark.json \
  --answer-key docs/visexp/out/user-task-answer-key.csv \
  --assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv \
  --out docs/visexp/out/user-task-paper-r249/scored
```

Claim boundary: R249 fixes the paper-scale launch logistics for C5, but records zero real participant responses. C5 remains unsupported until completed paper-scale responses are scored with the frozen answer key and nondefault R249 assignment file.
