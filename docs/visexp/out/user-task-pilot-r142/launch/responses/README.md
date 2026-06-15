# R142 Pilot Responses

The CSV template in this directory is intentionally blank. Complete it only with
real participant responses from P01-P05.

Do not commit filled response rows unless the participants have approved the
research data handling plan. After collection, score a copy with:

```sh
python3 docs/visexp/score_user_task_results.py \
  --responses <completed-pilot-response.csv> \
  --bundle docs/visexp/out/user-task-benchmark.json \
  --answer-key docs/visexp/out/user-task-answer-key.csv \
  --assignments docs/visexp/out/user-task-assignments.csv \
  --out docs/visexp/out/user-task-pilot-r142
```
