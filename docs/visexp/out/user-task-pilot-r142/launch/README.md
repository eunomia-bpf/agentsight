# R187 R142 Pilot Launch Package

Status: `pilot_launch_ready_no_responses`

This directory is ready to send to real R142 pilot participants. It contains
per-participant blinded task packets, a blank response CSV, and a manifest. It
does not contain the R142 answer key or any participant responses.

Participant IDs: P01, P02, P03, P04, P05

Coordinator steps:

1. Send each participant only their matching `participants/Pxx.md` or `participants/Pxx.json`.
2. Collect exactly one completed response row for every assignment in `responses/user-task-response-template-r142-pilot.csv`.
3. Keep `docs/visexp/out/user-task-answer-key.csv` hidden from participants.
4. Score the completed CSV with `docs/visexp/score_user_task_results.py`.

Response fields:

- `response_json`: JSON object matching the task question.
- `task_time_seconds`: elapsed seconds for the task.
- `confidence`: integer 1..5.
- `notes`: optional participant notes.

Claim boundary:

R187 is launch material only. It records zero real responses and cannot support
C5. C5 remains unsupported until real participant responses are collected and
scored under the frozen R142 preregistration.
