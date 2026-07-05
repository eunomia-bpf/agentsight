# R339 Sequence Adequacy

This run reuses existing tracked labeled operation JSONL. It does not fetch, sync, create, or relabel datasets.
It scores ranked profile groups after visible ranking, using hidden labels only for offline evaluation.

## Headline

Overall status: `pass`. The default visible policy is `operation_stack:query_aware`.
At top-5 groups, it inspects median 0.0937 operation work and covers median 0.2629 positive-session recall, versus fixed-session recall 0.0160 and flat operation work 1.0000.
At a 30% operation budget, it reaches median 0.3900 positive-operation recall and 0.4669 positive-session recall while touching median 0.3467 sessions.
Fixed-session reaches median 0.3230 positive-session recall at 0.3227 session work. Raw action reaches 0.5147 positive-session recall but touches 0.9103 sessions.

## Claim Boundary

Operation-stack query-aware ranking gives a sequence-scope triage tradeoff: it covers more positive sessions than fixed-session under a 30% operation budget while touching far fewer sessions than raw action stacks, and it inspects much less work than flat summaries.

Must not claim:
- does not prove human or agent analyst productivity
- does not prove automatic discovery of all intent boundaries
- does not dominate fixed-session on first-positive work
- does not make raw action stacks obsolete for high session recall

## Artifacts

- `sequence-adequacy-report.json`
- `task-sequence-adequacy.csv`
- `policy-sequence-summary.csv`
- `default-sequence-comparisons.csv`
- `task-sequence-cards.csv`
