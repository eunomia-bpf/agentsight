# R189 Tag Consolidation

Status: `tag_consolidation_completed`

## Scope

- Input: `.agentsight/agentflame/r170-full-current`.
- Raw agent traces are not read directly or modified.
- Raw one-word tags are preserved; canonical tags are a display/aggregation layer.

## Headline Metrics

### session_effect

- Unique tags: 53 -> 45 (15.094% reduction).
- Top-20 coverage: 99.465% -> 99.714%.
- Long-tail weight: 0.39% -> 0.334%.
- Auto-merged tags: 11; review suggestions: 1.

### prompt_effect

- Unique tags: 263 -> 216 (17.871% reduction).
- Top-20 coverage: 90.445% -> 92.72%.
- Long-tail weight: 2.933% -> 2.275%.
- Auto-merged tags: 49; review suggestions: 9.

### prompt_rows

- Unique tags: 328 -> 279 (14.939% reduction).
- Top-20 coverage: 79.573% -> 83.666%.
- Long-tail weight: 10.038% -> 8.674%.
- Auto-merged tags: 49; review suggestions: 9.

### llm_events

- Unique tags: 1423 -> 1254 (11.876% reduction).
- Top-20 coverage: 94.546% -> 95.337%.
- Long-tail weight: 1.903% -> 1.689%.
- Auto-merged tags: 171; review suggestions: 104.

### llm_tokens

- Unique tags: 1423 -> 1254 (11.876% reduction).
- Top-20 coverage: 99.999% -> 100.0%.
- Long-tail weight: 0.0% -> 0.0%.
- Auto-merged tags: 171; review suggestions: 104.

## Stack Aggregation

- System stacks: 26829 -> 26067 (2.84% reduction), total preserved: True.
- Token stacks: 8569 -> 7661 (10.596% reduction), total preserved: True.

## Merge Mechanism

| dimension | dictionary aliases | lexical+profile | profile-only | review suggestions | non-alias profile sim p50/p90 |
|---|---:|---:|---:|---:|---:|
| llm | 31 | 140 | 0 | 104 | 0.661/0.865 |
| prompt | 24 | 25 | 0 | 9 | 0.64/0.736 |
| session | 8 | 3 | 0 | 1 | 0.668/0.668 |

## High-Confidence Example Merges

| dimension | raw | canonical | reason | confidence | support |
|---|---|---|---|---:|---:|
| session | `uxdesign` | `design` | lexical+profile | 0.859 | 1148 |
| prompt | `designcodex` | `design` | lexical+profile | 0.775 | 1074 |
| prompt | `testcodex` | `test` | lexical+profile | 0.807 | 982 |
| prompt | `docupdate` | `docs` | alias | 0.96 | 446 |
| prompt | `designfix` | `design` | alias | 0.96 | 404 |
| llm | `uxdesign` | `design` | lexical+profile | 0.79 | 357 |
| prompt | `eval` | `evaluate` | alias | 0.96 | 273 |
| prompt | `reviewbu` | `review` | lexical+profile | 0.797 | 254 |
| session | `reviewbu` | `review` | lexical+profile | 0.807 | 254 |
| prompt | `testcodexrun` | `test` | lexical+profile | 0.789 | 198 |
| prompt | `analyzesess` | `analyze` | lexical+profile | 0.852 | 179 |
| prompt | `docwrite` | `docs` | alias | 0.96 | 174 |
| prompt | `doc` | `docs` | alias | 0.96 | 171 |
| session | `visdesign` | `design` | lexical+profile | 0.761 | 164 |
| llm | `fix` | `debug` | alias | 0.96 | 128 |
| prompt | `docsfix` | `docs` | alias | 0.96 | 118 |
| prompt | `cleanups` | `cleanup` | lexical+profile | 0.845 | 106 |
| llm | `updateplan` | `plan` | alias | 0.96 | 101 |
| prompt | `perfstrace` | `trace` | lexical+profile | 0.75 | 97 |
| prompt | `docsanalyze` | `docs` | alias | 0.96 | 90 |
| session | `docwrite` | `docs` | alias | 0.96 | 90 |
| prompt | `docrewrite` | `docs` | alias | 0.96 | 82 |
| prompt | `testcase` | `test` | alias | 0.96 | 81 |
| llm | `eval` | `evaluate` | alias | 0.96 | 80 |
| prompt | `testrewrite` | `test` | lexical+profile | 0.777 | 78 |
| prompt | `docsupdate` | `docs` | alias | 0.96 | 68 |
| prompt | `docszh` | `docs` | alias | 0.96 | 68 |
| prompt | `refactorrepo` | `refactor` | lexical+profile | 0.764 | 67 |
| prompt | `docsreview` | `docs` | alias | 0.96 | 66 |
| prompt | `visdesign` | `design` | lexical+profile | 0.729 | 64 |

## Review Boundary

R189 is not human tag adequacy evidence. It shows whether noisy raw tags can be consolidated into a more stable profiling vocabulary while keeping raw tags auditable. Human C6 labels are still required before claiming semantic correctness.
