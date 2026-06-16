# R211 Stack Examples And Tag Distribution

Status: `stack_examples_ready_no_outcome_claims`

## Scope

- Reads generated R170/R189 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM; R170 is the upstream real llama.cpp annotation run.
- Supports RQ2 figure construction and case-study selection, not C5/C6 outcome claims.

## Summary

- Sessions: 325.
- System observations: 183714.
- Semantic system stacks: 26829.
- Nonsemantic mixed weight: 90.402%.
- Flat mixed weight: 90.918%.
- Tag dimensions summarized: 6.
- Baseline collapse examples: 14.

## Top Label Shares

| dimension | top tag | share | top-5 coverage | unique tags |
|---|---|---:|---:|---:|
| session_tag_by_sessions | `review` | 25.231% | 59.385% | 60 |
| session_tag_by_system_effect_weight | `refactor` | 48.942% | 91.902% | 53 |
| prompt_tag_by_prompt_rows | `refactor` | 31.445% | 62.749% | 328 |
| prompt_tag_by_system_effect_weight | `refactor` | 39.824% | 77.078% | 263 |
| llm_tag_by_llm_events | `refactor` | 35.932% | 75.022% | 1423 |
| llm_tag_by_estimated_tokens | `refactor` | 83.575% | 99.322% | 1423 |

## Process Split Examples

| process | weight | prompt tags | top split | ambiguous share |
|---|---:|---:|---|---:|
| `rg` | 33959 | 176 | refactor=14677; review=7176; design=3077; analyze=1068; test=975; benchmark=829; research=716; docs=585; designcodex=376; debug=354; trace=274; explain=218 | 56.78% |
| `sed` | 30810 | 180 | refactor=13638; review=5012; design=2942; test=1225; analyze=1154; benchmark=1008; research=937; docs=496; debug=295; trace=286; commitlog=265; ignored=254 | 55.735% |
| `tool:tool` | 22996 | 102 | refactor=11579; design=2572; review=2176; analyze=1683; test=1189; benchmark=994; debug=314; research=246; docs=228; ignored=206; validate=137; compare=121 | 49.648% |
| `git` | 18592 | 147 | refactor=5966; review=4067; design=999; test=892; analyze=834; research=703; docs=432; explain=373; commit=280; testcodex=248; trace=207; ignored=202 | 67.911% |
| `find` | 7818 | 131 | refactor=2863; review=1347; design=794; analyze=636; test=361; research=209; benchmark=159; designcodex=118; docs=99; build=60; explore=48; explain=44 | 63.379% |
| `nl` | 7439 | 75 | review=2959; refactor=2517; design=326; docs=208; test=138; research=120; benchmark=112; reviewbu=110; designfix=98; analyze=78; codex=78; debug=49 | 60.223% |
| `python3` | 6419 | 88 | refactor=2564; analyze=1175; review=554; test=310; research=252; design=248; docs=138; ignored=109; commitlog=94; debug=80; eval=60; benchmark=53 | 60.056% |
| `cargo` | 5297 | 68 | refactor=1818; review=860; research=366; design=306; commitlog=258; test=198; analyze=194; explain=188; designcodex=162; benchmark=105; trace=68; commit=44 | 65.679% |

## Baseline Collapse Examples

| system key | weight | prompt tags | top split | ambiguous share |
|---|---:|---:|---|---:|
| `process:tool:tool;effect:process;status:ok` | 13136 | 93 | refactor=6316; review=1817; design=1443; analyze=797; test=597; benchmark=251; ignored=206; debug=185; research=167; validate=134 | 51.918% |
| `process:git;effect:read;status:ok` | 5345 | 116 | review=1335; refactor=1239; design=389; research=321; analyze=316; test=242; explain=185; docs=122; commitlog=109; commit=91 | 75.023% |
| `process:tool:tool;effect:process;status:observed` | 7969 | 57 | refactor=4236; design=908; analyze=782; benchmark=600; test=517; review=220; debug=122; docs=96; research=51; report=43 | 46.844% |
| `process:cargo;effect:test;status:ok` | 2000 | 48 | refactor=639; review=345; research=213; commitlog=146; explain=124; test=79; design=55; docs=37; trace=35; meta=25 | 68.05% |
| `process:python3;effect:process;status:ok` | 1829 | 70 | refactor=718; review=220; analyze=205; test=138; research=102; ignored=41; design=37; benchmark=31; docs=27; compare=27 | 60.744% |
| `process:sed;effect:read;status:ok;path:native-sim/libnativeloader` | 1917 | 8 | refactor=926; design=427; benchmark=332; review=161; test=48; analyze=18; compare=3; validate=2 | 51.695% |
| `process:rg;effect:read;status:ok;path:collector/src` | 1458 | 55 | review=535; refactor=436; designcodex=99; design=82; test=46; designfix=35; analyze=29; trace=18; docs=13; codex=13 | 63.306% |
| `process:ps;effect:process;status:ok` | 952 | 43 | refactor=220; analyze=217; review=129; design=120; test=98; trace=17; debug=15; serve=12; testcodexrun=12; benchmark=11 | 76.891% |

## Top Semantic Stacks

| rank | weight | session | prompt | process/effect | short stack |
|---:|---:|---|---|---|---|
| 1 | 6004 | `refactor` | `refactor` | `tool:tool/process` | `agent:codex;session:refactor;prompt:refactor;call:tool/tool;effect:process;status:ok` |
| 2 | 4115 | `refactor` | `refactor` | `tool:tool/process` | `agent:codex;session:refactor;prompt:refactor;call:tool/tool;effect:process;status:observed` |
| 3 | 1648 | `refactor` | `refactor` | `sed/read` | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:module/x86;status:ok` |
| 4 | 1349 | `refactor` | `design` | `tool:tool/process` | `agent:codex;session:refactor;prompt:design;call:tool/tool;effect:process;status:ok` |
| 5 | 1349 | `refactor` | `review` | `tool:tool/process` | `agent:codex;session:refactor;prompt:review;call:tool/tool;effect:process;status:ok` |
| 6 | 1212 | `analyze` | `analyze` | `docker/process` | `agent:codex;session:analyze;prompt:analyze;call:tool/shell;process:docker;effect:process;status:ok` |
| 7 | 1042 | `refactor` | `refactor` | `rg/read` | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:rg;effect:read;path:micro/programs;status:ok` |
| 8 | 926 | `refactor` | `refactor` | `sed/read` | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:native-sim/libnativeloader;status:ok` |

## Claim Boundary

R211 supports figure selection and reviewer-auditable examples for RQ2. It does not prove tag adequacy, developer utility, or exact lineage breadth; those remain governed by the existing C5/C6/C4 gates.
