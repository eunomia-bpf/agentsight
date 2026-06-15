# R122 Tag Adequacy Label Packet

Date: 2026-06-15T05:44:32+00:00

This artifact samples real local Codex/Claude session, prompt, and LLM-call
fragments for human tag adequacy labeling. Raw traces are parsed read-only. The
committed CSV contains redacted previews and blank label columns; the local
fragment file used by automated stability runs is not committed.

| Kind | Count |
|------|------:|
| session | 100 |
| prompt | 100 |
| llm | 100 |

Outputs:

- Label packet: `docs/visexp/out/tag-adequacy-label-packet-r122.csv`
- Local fragment file: `.agentsight/agentflame/r122-real-fragments.txt`

Claim impact: this prepares R122 but does not by itself support human adequacy.
The CSV still needs independent labels and agreement/adjudication.
