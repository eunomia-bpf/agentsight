# Aggregate semantic-responsibility summary

This is an experiment summary, not paper text. It uses the complete frozen
42-session population and the final one-pass automatic annotation. Paths below
contain only coarse semantic tags; source content, absolute paths, and raw
session identifiers are omitted.

## Population and measures

| Item | Value |
| --- | ---: |
| Sessions | 42 |
| Trace nodes | 10,423 |
| Session / prompt / LLM / tool nodes | 42 / 1,252 / 5,620 / 3,509 |
| Semantic annotations | 1,737 |
| Tool-operation mass | 3,509 |
| Bounded LLM token mass | 1,380,863,014 |
| Unique token stacks | 5,620 |
| Unique operation stacks | 3,236 |

Token width is the sum of the same bounded `agent-session` token components
used by AgentPProf's local-session token view. Tool-operation width assigns one
unit to each parsed tool node. Prompts and LLM nodes do not receive operation
units, and tools do not receive token units.

## Top responsibilities by token mass

| Rank | Full semantic path | Tokens | Share |
| ---: | --- | ---: | ---: |
| 1 | `refine paper > align evaluation` | 23,959,384 | 1.735% |
| 2 | `refine paper > refine algorithms` | 22,362,281 | 1.619% |
| 3 | `refine paper > polish prose` | 21,325,512 | 1.544% |
| 4 | `refine paper > reduce jargon` | 20,751,211 | 1.503% |
| 5 | `refine paper > standardize terms` | 16,575,974 | 1.200% |
| 6 | `refine paper > continue refinement` | 16,089,815 | 1.165% |
| 7 | `refine paper > add citations` | 15,735,958 | 1.140% |
| 8 | `develop manuscript > fix section consistency` | 14,932,321 | 1.081% |
| 9 | `refine paper > audit academic terms` | 14,807,641 | 1.072% |
| 10 | `refine paper > build checker` | 14,391,929 | 1.042% |

The largest token responsibilities are distributed rather than dominated by
one path: the top path contains 1.735% of complete token mass.

## Top responsibilities by operation count

| Rank | Full semantic path | Tool operations | Share |
| ---: | --- | ---: | ---: |
| 1 | `refine paper > translate paper` | 48 | 1.368% |
| 2 | `refine paper > refine prose > revise sentences` | 43 | 1.225% |
| 3 | `revise paper > audit terminology` | 36 | 1.026% |
| 4 | `refine paper > standardize terms > standardize terms` | 36 | 1.026% |
| 5 | `refine paper > align evaluation` | 35 | 0.997% |
| 6 | `refine paper > polish prose` | 33 | 0.940% |
| 7 | `refine paper > refine algorithms` | 28 | 0.798% |
| 8 | `refine paper > reduce jargon` | 27 | 0.769% |
| 9 | `refine paper > revise terminology` | 27 | 0.769% |
| 10 | `refine paper > continue refinement` | 26 | 0.741% |

The repeated frame in rank 4 is retained exactly as produced by the fixed
one-pass backend; there was no aggregate-aware cleanup pass.

## Semantic-depth distribution

Depth includes the mandatory session-level and prompt-level semantic
operations. The backend introduced optional recursive operations only where it
found a responsibility change.

| Semantic depth | Token mass | Token share | Tool operations | Operation share |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 971,614,231 | 70.363% | 1,970 | 56.141% |
| 3 | 400,396,091 | 28.996% | 1,460 | 41.607% |
| 4 | 8,852,692 | 0.641% | 79 | 2.251% |
| **Total** | **1,380,863,014** | **100%** | **3,509** | **100%** |

The final profile therefore has variable depth 2--4. It is not forced to a
target depth.

## Cross-session name reuse

Mandatory session/prompt tags are excluded from this calculation. The 443
optional annotation occurrences use 353 distinct tag strings. Eighteen tag
strings occur in at least two workspace session records, so the unique-name
cross-record reuse rate used for the requested cross-session summary is
**18 / 353 = 5.099%**. The remaining 335 names are single-record tags. The 42
workspace records contain 31 distinct native `source_session` strings, so this
is record-level rather than independent-run reuse.

This low reuse was observed under the fixed independent per-record first-pass
protocol; the experiment does not establish that batching caused it.
AgentPProf reports it as an advisory fragmentation diagnostic, and the task
explicitly prohibited an aggregate-aware revision loop.

## Three deepest paths

All three have semantic depth four. They are selected by token mass among the
deepest distinct paths.

| Rank | Full semantic path | Tokens | Tool operations |
| ---: | --- | ---: | ---: |
| 1 | `audit evidence > audit evaluations > inspect results > inspect ablations` | 1,605,586 | 8 |
| 2 | `audit evidence > audit evaluations > inspect results > inspect tag alignment` | 1,054,595 | 5 |
| 3 | `audit evidence > audit evaluations > inspect results > inspect profiling cost` | 1,026,241 | 5 |

## Agent split

| Agent | Token mass | Token share | Tool operations | Operation share |
| --- | ---: | ---: | ---: | ---: |
| Claude | 1,371,000,658 | 99.286% | 3,279 | 93.445% |
| Codex | 9,862,356 | 0.714% | 230 | 6.555% |
| **Total** | **1,380,863,014** | **100%** | **3,509** | **100%** |

The population is therefore strongly Claude-weighted, especially under token
width. Cross-agent comparisons should not treat the two agent totals as a
balanced benchmark.

## Longest-horizon sessions

The three sessions are selected by the frozen inventory's observed timestamp
span. Labels L1--L3 avoid exposing raw session identifiers.

| Session | Agent | Horizon | Dominant token responsibility | Token share within session | Dominant count responsibility | Count share within session |
| --- | --- | ---: | --- | ---: | --- | ---: |
| L1 | Claude | 33.891 h | `refine paper > align evaluation` | 3.635% | `refine paper > translate paper` | 3.721% |
| L2 | Claude | 21.947 h | `develop research paper > address review > inspect evidence` | 2.812% | `develop research paper > schedule research > schedule work` | 3.676% |
| L3 | Claude | 13.246 h | `maintain paper assets > merge incoming changes > resolve merge conflict` | 10.578% | `maintain paper assets > verify prior merge > compare branch history` | 11.111% |

The dominant responsibility differs across all three long-horizon sessions:
evaluation alignment, evidence inspection, and merge/conflict work. The low
largest-path shares in L1 and L2 also show that these sessions span many
responsibilities rather than one repeated operation.

## Mechanical diagnostics

The final token validation reports 72 nonblocking warnings and 70 structured
issue intervals. They consist of coarse spans, flat fan-out, one unary
refinement, cross-session singleton fragmentation, and near-name candidates.
Coverage, nesting, and conservation remain valid. These diagnostics are
retained as one-pass quality boundaries and were not used for revision.
