# CodeTraceBench RQ2 Real Preflight

**Source-only check:** PARTIAL PASS — six selected official source variants across four frameworks align exactly and AgentProf counts match.
**REAL PREFLIGHT:** INCOMPLETE — this command does not yet exercise task-held-out reference construction, differential scoring, prediction writing, terminal label join, or the declared RQ2 metrics.

## Information Boundary

Selection used only framework, manifest outcome, archive availability, and trajectory ID order. The runner projected no `incorrect_stages`, stage, label, reason, or annotation path column. Every operation and stack was fixed before any hidden step label is eligible to load.

## Four-Framework, Six-Variant Result

| Framework / source variant | Trajectory | Source adapter | Steps | Action kinds | Semantic stacks | AgentProf |
|---|---|---|---:|---|---:|---|
| mini-SWE-agent / MiniSWE session log | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-54ac67f0` | `miniswe-message-trajectory` | 47 | communicate=2, edit=2, execute=1, inspect=27, install=6, search=4, version-control=5 | 10 | semantic/raw/phase exact |
| mini-SWE-agent / MiniSWE SWE raw | `miniswe-OpenAI__GPT-5-astropy__astropy-14598-416c95db` | `miniswe-message-trajectory` | 26 | communicate=2, edit=1, execute=3, inspect=14, search=6 | 7 | semantic/raw/phase exact |
| OpenHands / OpenHands event stream | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-7498555b` | `openhands-agent-actions` | 95 | edit=37, execute=19, inspect=31, search=2, test=6 | 8 | semantic/raw/phase exact |
| OpenHands / OpenHands SWE raw | `openhands-OpenAI__GPT-5-astropy__astropy-13398-3106f9b1` | `openhands-maximal-visible-action-context` | 48 | edit=5, execute=7, inspect=15, search=15, test=6 | 5 | semantic/raw/phase exact |
| Terminus2 / Terminus2 command stream | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-accelerate-maximal-square-eca249fc` | `terminus2-commands-txt-strings` | 22 | edit=8, execute=9, inspect=5 | 3 | semantic/raw/phase exact |
| SWE-agent / SWE-agent trajectory | `sweagent-OpenAI__GPT-5-Significant-Gravitas__AutoGPT-4652-b968024b` | `sweagent-trajectory-elements` | 32 | edit=2, execute=4, inspect=24, other=2 | 6 | semantic/raw/phase exact |

## Decision

This dependency check passes only the selected source-adapter and profiler-engagement boundary. It is not the approved REAL PREFLIGHT, is not evidence for RQ2, and is not a smoke-test substitute for the declared full run. The next step is to implement and review one shared end-to-end preflight/full scoring path before running all 3,291 published raw archives.
