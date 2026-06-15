# R122 Tag Adequacy Label Packet

Date: 2026-06-15T07:42:10+00:00

This artifact samples real local Codex/Claude session, prompt, and LLM-call
fragments for human tag adequacy labeling. Raw traces are parsed read-only. The
committed CSV contains redacted previews, the candidate one-word tag produced
by the local llama.cpp benchmark when available, and blank label columns. The
local fragment file used by automated stability runs is not committed.

| Kind | Count |
|------|------:|
| session | 100 |
| prompt | 100 |
| llm | 100 |

Outputs:

- Label packet: `docs/visexp/out/tag-adequacy-label-packet-r122.csv`
- Local fragment file: `.agentsight/agentflame/r122-real-fragments.txt`
- Candidate tag source: `.agentsight/agentflame/model-benchmarks-r123.json`
- Candidate tags matched: 300 / 300

Claim impact: this prepares R122 but does not by itself support human adequacy.
The CSV still needs independent labels and agreement/adjudication. Labelers
judge whether `candidate_tag` preserves the main intent of the redacted preview;
they should not invent replacement tags in the label columns.

Privacy boundary: redacted previews intentionally keep enough prompt wording for
human judgment, including ordinary exact-output directives. They must not contain
home paths, secret-token patterns, email addresses, URL paths, or long raw ids.
