# R196 Long-Tail Tag Governance

Status: `long_tail_governance_candidates_ready_with_regeneration_smoke`

## Scope

- Input AgentFlame artifact: `.agentsight/agentflame/r170-full-current`.
- R189 mapping: `docs/visexp/out/tag-consolidation-r189/canonical-tag-map-r189.csv`.
- Raw agent traces are not read or modified.
- Raw one-word tags are preserved; R196 only emits governance candidates.

## Action Counts

| action | tags |
|---|---:|
| `auto_canonicalize_existing` | 231 |
| `review_merge` | 114 |
| `contextual_split_candidate` | 2 |
| `regenerate_candidate` | 39 |
| `keep_rare_distinct` | 1241 |
| `keep_head` | 184 |

## Dimension Summary

| dimension | tags | long-tail tags | long-tail support | review tags | review support |
|---|---:|---:|---:|---:|---:|
| llm | 1423 | 1284 | 1.903% | 259 | 1.376% |
| prompt | 328 | 253 | 2.996% | 56 | 3.258% |
| session | 60 | 38 | 0.397% | 8 | 0.938% |

Review packet rows: 323; accepted review labels: 0.

## Highest-Support Review Candidates

| dimension | raw tag | action | support | reason | top profile |
|---|---|---|---:|---|---|
| prompt | `ignored` | `contextual_split_candidate` | 1221 | multi_peak_processes;multi_peak_paths;generic_or_noisy_tag | sed=254; tool/tool=206; git=202; rg=149; python3=109; llvm-objdump=37 |
| session | `uxdesign` | `auto_canonicalize_existing` | 1148 | r189_lexical+profile | rg=324; sed=258; wc=180; git=164; cargo=112; nl=78 |
| prompt | `designcodex` | `auto_canonicalize_existing` | 1074 | r189_lexical+profile | rg=376; sed=186; cargo=162; find=118; git=96; wc=34 |
| prompt | `testcodex` | `auto_canonicalize_existing` | 982 | r189_lexical+profile | git=248; sed=183; rg=149; tool/tool=51; find=44; actplane=43 |
| prompt | `codex` | `contextual_split_candidate` | 402 | multi_peak_processes;generic_or_noisy_tag | git=126; nl=78; rg=50; rustfmt=48; sed=44; cargo=22 |
| llm | `uxdesign` | `auto_canonicalize_existing` | 357 | r189_lexical+profile | review=1152922522; docx=769754031; codexcheck=474901594; codexinteg=401430163; refactor=383636057; uxdesigncodx=302513465 |
| llm | `check` | `regenerate_candidate` | 294 | generic_or_noisy_tag | refactor=2709619; review=1050982; merge=479675; metrics=159701; test=116453; docs=84193 |
| prompt | `reviewbu` | `auto_canonicalize_existing` | 254 | r189_lexical+profile | nl=110; rg=96; git=30; find=18 |
| session | `reviewbu` | `auto_canonicalize_existing` | 254 | r189_lexical+profile | nl=110; rg=96; git=30; find=18 |
| prompt | `testcodexrun` | `auto_canonicalize_existing` | 198 | r189_lexical+profile | find=42; python3=32; tool/tool=30; sed=28; git=16; llama-server=12 |
| prompt | `analyzesess` | `auto_canonicalize_existing` | 179 | r189_lexical+profile | rg=38; python3=29; sed=27; git=21; find=13; tool/tool=10 |
| prompt | `codexcheck` | `regenerate_candidate` | 176 | generic_or_noisy_tag | wc=54; rg=46; git=28; cargo=26; sed=18; nl=4 |
| llm | `update` | `regenerate_candidate` | 168 | generic_or_noisy_tag | review=242415819; refactor=825135; metrics=161249; test=117141; build=88845; design=1146 |
| session | `visdesign` | `auto_canonicalize_existing` | 164 | r189_lexical+profile | sed=36; cargo=16; python3=16; find=14; jq=14; nl=14 |
| session | `bpfanalyze` | `review_merge` | 126 | r189_review_suggestion_not_applied | find=48; tool/read=40; grep=32; wc=4; ls=2 |
| prompt | `checkpoint` | `regenerate_candidate` | 126 | generic_or_noisy_tag | rg=42; sed=22; git=18; nl=14; tool/tool=10; tool/plan=8 |
| prompt | `cleanups` | `auto_canonicalize_existing` | 106 | r189_lexical+profile | tool/tool=40; du=38; docker=20; df=6; journalctl=2 |
| prompt | `codexinteg` | `regenerate_candidate` | 100 | generic_or_noisy_tag | wc=36; rg=30; sed=26; cargo=6; nl=2 |
| prompt | `perfstrace` | `auto_canonicalize_existing` | 97 | r189_lexical+profile | git=21; tmp_mktemp=14; opencode=10; agentsight=7; rg=7; claude=4 |
| prompt | `update` | `regenerate_candidate` | 95 | generic_or_noisy_tag;long_tail | rg=28; sed=20; tool/tool=19; git=16; tool/plan=3; find=3 |
| prompt | `testrewrite` | `auto_canonicalize_existing` | 78 | r189_lexical+profile | sed=40; rg=10; git=9; tool/plan=4; cargo=4; tool/tool=4 |
| prompt | `costanalysis` | `regenerate_candidate` | 71 | generic_or_noisy_tag;long_tail | tool/subagent=38; python3=11; git=7; sed=6; rg=3; tool/plan=2 |
| prompt | `refactorrepo` | `auto_canonicalize_existing` | 67 | r189_lexical+profile | tool/subagent=38; python3=11; git=5; sed=5; rg=3; tool/plan=2 |
| prompt | `visdesign` | `auto_canonicalize_existing` | 64 | r189_lexical+profile | sed=34; rg=10; nl=8; find=6; jq=4; git=2 |
| prompt | `loganalyze` | `review_merge` | 61 | r189_review_suggestion_not_applied | rg=28; sed=14; perl=10; tool/plan=4; find=3; cargo=1 |
| llm | `testcodex` | `auto_canonicalize_existing` | 56 | r189_lexical+profile | test=83254480; examples=657; compare=415; refactor=400; setup=342; testcodex=282 |
| llm | `visdesign` | `review_merge` | 48 | r189_review_suggestion_not_applied | docgen=27573635; visdesign=1102193 |
| prompt | `docscheck` | `auto_canonicalize_existing` | 46 | r189_lexical+profile | nl=24; rg=14; tool/plan=6; git=2 |
| prompt | `auditrewrite` | `regenerate_candidate` | 42 | generic_or_noisy_tag;long_tail | rg=22; sed=10; git=6; tool/plan=2; find=2 |
| prompt | `designdoc` | `auto_canonicalize_existing` | 41 | r189_lexical+profile | rg=19; sed=9; nl=6; git=4; tool/plan=3 |

## Claim Boundary

R196 supports a governance mechanism for long-tail tags: existing R189 merges stay auditable, risky review rows are surfaced, generic/noisy tags can be sent to regeneration, and high-support multi-peak tags can be split contextually. It does not prove semantic adequacy or merge quality. Optional LLM regeneration proposes candidate tags only; it does not count as C5 developer-utility evidence, C6 human adequacy evidence, or R190 merge-quality evidence. R124 human labels and R190 merge-risk labels are still required.
