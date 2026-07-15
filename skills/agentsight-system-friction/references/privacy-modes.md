# Privacy Modes

Use the least revealing mode that answers the system question. Name the mode in the output.

## private-debug

Exact local identifiers, command snippets, and hosts may be used when they are necessary to solve the local problem and the user requested private debugging.

## team-share

Summarize commands and path patterns. Prefer statuses, counts, durations, resource magnitudes, source types, and host/path/process/session categories.

## public-share

Use aggregate evidence only. Prefer anonymous categories, coarse time windows, counts, and operating outcomes.

## Sensitive Findings

Report sensitive access as a class and path pattern, not a value:

- good: `read cloud credential file under ~/.aws/...`
- bad: printing key material, token contents, or auth headers
