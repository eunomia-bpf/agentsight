# R142 User-Task Pilot

R142 launch materials are already frozen by R187. Use the participant packets under:

- `docs/visexp/out/user-task-pilot-r142/launch/participants`

Collect completed response rows in a copy of:

- `docs/visexp/out/user-task-pilot-r142/launch/responses/user-task-response-template-r142-pilot.csv`

Then score the completed CSV with:

```bash
python3 docs/visexp/score_user_task_results.py \
  --responses <completed-pilot-response.csv> \
  --bundle docs/visexp/out/user-task-benchmark.json \
  --answer-key docs/visexp/out/user-task-answer-key.csv \
  --assignments docs/visexp/out/user-task-assignments.csv \
  --out docs/visexp/out/user-task-pilot-r142
```

Do not distribute answer keys or scoring artifacts to participants.
