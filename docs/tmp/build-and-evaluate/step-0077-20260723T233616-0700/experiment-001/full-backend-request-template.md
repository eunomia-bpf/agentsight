# Complete automatic-backend request: {{CASE}}

Read:

- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/automatic-backend-instruction.md`
- `{{WORKSPACE}}/trace.jsonl`
- `{{WORKSPACE}}/annotation.json`

The outcome-blind profiling question is:

> {{QUESTION}}

Create a complete first-pass semantic annotation from the empty annotation
file. Create and name every mandatory session/prompt operation and add useful
variable-depth refinements from source-visible responsibility changes. You may
read enough assigned source context to make the decisions; you do not need to
read every field or force a boundary.

Do not run AgentPProf, inspect aggregate diagnostics, read retained
annotations, search for expected answers, read paper/case figures or
narratives, or read outcome/reward/pair/human-stage data.

Edit only `{{WORKSPACE}}/annotation.json`. Return a concise summary in the task
response; do not write another workspace file and do not use Git.

