# Privacy Modes

Use the least revealing mode that answers the question. Name the mode in the output.

## private-debug

Use for local troubleshooting. Exact local identifiers and command snippets may be used when they are necessary to solve the local problem and the user requested private debugging.

## team-share

Use for internal reports. Summarize prompts, responses, and command output. Prefer counts, statuses, durations, short task/claim summaries, and reader-safe categories.

## public-share

Use aggregate evidence only. Prefer anonymous categories, coarse time windows, counts, and outcome summaries.

## Sensitive Findings

Report secret access as a class and path pattern, not a value:

- good: `read cloud credential file under ~/.aws/...`
- bad: printing key material or token contents

## Missing Evidence

Do not write "the agent did not do X" when the source cannot observe X. Write "this source did not provide evidence of X" instead.
