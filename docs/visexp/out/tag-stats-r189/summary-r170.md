# R189 Tag And Stack Statistics

Source: `.agentsight/agentflame/r170-full-current/agentflame.json` and `semantic-system.folded.txt`. This is a derived aggregate; it does not include raw prompt text.

## Scale
- Sessions: 325 ({'claude': 50, 'claude-subagent': 77, 'codex': 198})
- Raw tool events: 142,468
- Raw LLM events: 114,837
- System observations: 183,714
- Semantic system stacks: 26,829
- Semantic compression: 6.848x

## Session tags by sessions
| rank | tag | count | share |
|---:|---|---:|---:|
| 1 | `review` | 82 | 25.231% |
| 2 | `refactor` | 56 | 17.231% |
| 3 | `docs` | 24 | 7.385% |
| 4 | `design` | 16 | 4.923% |
| 5 | `analyze` | 15 | 4.615% |
| 6 | `countlines` | 11 | 3.385% |
| 7 | `test` | 9 | 2.769% |
| 8 | `research` | 8 | 2.462% |
| 9 | `agentsightsm` | 8 | 2.462% |
| 10 | `coda` | 7 | 2.154% |
| 11 | `rootpidrefsc` | 5 | 1.538% |
| 12 | `docsupdate` | 5 | 1.538% |
| 13 | `jsonokno` | 5 | 1.538% |
| 14 | `paperagentfl` | 5 | 1.538% |
| 15 | `benchmarks` | 5 | 1.538% |
| 16 | `rmarkdown` | 5 | 1.538% |
| 17 | `verify` | 4 | 1.231% |
| 18 | `bash` | 4 | 1.231% |
| 19 | `build` | 3 | 0.923% |
| 20 | `debug` | 3 | 0.923% |

## Prompt tags by prompt rows
| rank | tag | count | share |
|---:|---|---:|---:|
| 1 | `refactor` | 899 | 31.445% |
| 2 | `review` | 448 | 15.670% |
| 3 | `analyze` | 200 | 6.995% |
| 4 | `design` | 124 | 4.337% |
| 5 | `docs` | 123 | 4.302% |
| 6 | `test` | 122 | 4.267% |
| 7 | `research` | 82 | 2.868% |
| 8 | `trace` | 53 | 1.854% |
| 9 | `testcodex` | 28 | 0.979% |
| 10 | `evaluate` | 26 | 0.909% |
| 11 | `validate` | 22 | 0.769% |
| 12 | `docsupdate` | 21 | 0.735% |
| 13 | `compare` | 21 | 0.735% |
| 14 | `debug` | 20 | 0.700% |
| 15 | `tag` | 18 | 0.630% |
| 16 | `build` | 15 | 0.525% |
| 17 | `cleanup` | 15 | 0.525% |
| 18 | `check` | 14 | 0.490% |
| 19 | `optimize` | 12 | 0.420% |
| 20 | `explain` | 12 | 0.420% |

## LLM-call tags by events
| rank | tag | count | share |
|---:|---|---:|---:|
| 1 | `refactor` | 41,263 | 35.932% |
| 2 | `analyze` | 18,712 | 16.294% |
| 3 | `design` | 9,592 | 8.353% |
| 4 | `test` | 9,184 | 7.997% |
| 5 | `tokenize` | 7,402 | 6.446% |
| 6 | `report` | 6,494 | 5.655% |
| 7 | `review` | 5,248 | 4.570% |
| 8 | `docs` | 3,335 | 2.904% |
| 9 | `debug` | 1,816 | 1.581% |
| 10 | `build` | 1,432 | 1.247% |
| 11 | `research` | 1,068 | 0.930% |
| 12 | `trace` | 566 | 0.493% |
| 13 | `validate` | 508 | 0.442% |
| 14 | `audit` | 386 | 0.336% |
| 15 | `uxdesign` | 357 | 0.311% |
| 16 | `verify` | 303 | 0.264% |
| 17 | `check` | 294 | 0.256% |
| 18 | `cleanup` | 266 | 0.232% |
| 19 | `benchmark` | 175 | 0.152% |
| 20 | `evaluate` | 173 | 0.151% |

## Prompt tags by system-effect weight
| rank | tag | count | share |
|---:|---|---:|---:|
| 1 | `refactor` | 73,162 | 39.824% |
| 2 | `review` | 33,267 | 18.108% |
| 3 | `design` | 15,705 | 8.549% |
| 4 | `analyze` | 11,457 | 6.236% |
| 5 | `test` | 8,012 | 4.361% |
| 6 | `research` | 4,736 | 2.578% |
| 7 | `benchmark` | 4,033 | 2.195% |
| 8 | `docs` | 3,477 | 1.893% |
| 9 | `debug` | 1,587 | 0.864% |
| 10 | `explain` | 1,463 | 0.796% |
| 11 | `trace` | 1,401 | 0.763% |
| 12 | `commitlog` | 1,361 | 0.741% |
| 13 | `ignored` | 1,221 | 0.665% |
| 14 | `designcodex` | 1,074 | 0.585% |
| 15 | `testcodex` | 982 | 0.535% |
| 16 | `commit` | 739 | 0.402% |
| 17 | `build` | 724 | 0.394% |
| 18 | `validate` | 658 | 0.358% |
| 19 | `feedback` | 567 | 0.309% |
| 20 | `compare` | 535 | 0.291% |

## Session tags by system-effect weight
| rank | tag | count | share |
|---:|---|---:|---:|
| 1 | `refactor` | 89,914 | 48.942% |
| 2 | `review` | 29,164 | 15.875% |
| 3 | `design` | 25,434 | 13.844% |
| 4 | `analyze` | 12,433 | 6.768% |
| 5 | `research` | 11,891 | 6.473% |
| 6 | `test` | 5,190 | 2.825% |
| 7 | `docs` | 3,292 | 1.792% |
| 8 | `uxdesign` | 1,148 | 0.625% |
| 9 | `branding` | 955 | 0.520% |
| 10 | `cleanup` | 604 | 0.329% |
| 11 | `cleanlocal` | 414 | 0.225% |
| 12 | `audit` | 317 | 0.173% |
| 13 | `report` | 290 | 0.158% |
| 14 | `refactorchk` | 288 | 0.157% |
| 15 | `debug` | 280 | 0.152% |
| 16 | `build` | 274 | 0.149% |
| 17 | `reviewbu` | 254 | 0.138% |
| 18 | `backup` | 230 | 0.125% |
| 19 | `license` | 196 | 0.107% |
| 20 | `visdesign` | 164 | 0.089% |

## Top semantic stacks
| rank | weight | share | stack |
|---:|---:|---:|---|
| 1 | 6,004 | 3.268% | `agent:codex;session:refactor;prompt:refactor;call:tool/tool;effect:process;status:ok` |
| 2 | 4,115 | 2.240% | `agent:codex;session:refactor;prompt:refactor;call:tool/tool;effect:process;status:observed` |
| 3 | 1,648 | 0.897% | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:module/x86;status:ok` |
| 4 | 1,349 | 0.734% | `agent:codex;session:refactor;prompt:design;call:tool/tool;effect:process;status:ok` |
| 5 | 1,349 | 0.734% | `agent:codex;session:refactor;prompt:review;call:tool/tool;effect:process;status:ok` |
| 6 | 1,212 | 0.660% | `agent:codex;session:analyze;prompt:analyze;call:tool/shell;process:docker;effect:process;status:ok` |
| 7 | 1,042 | 0.567% | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:rg;effect:read;path:micro/programs;status:ok` |
| 8 | 926 | 0.504% | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:native-sim/libnativeloader;status:ok` |
| 9 | 907 | 0.494% | `agent:codex;session:refactor;prompt:refactor;call:tool/tool;effect:process;status:fail` |
| 10 | 896 | 0.488% | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:micro/programs;status:ok` |
| 11 | 860 | 0.468% | `agent:codex;session:refactor;prompt:design;call:tool/tool;effect:process;status:observed` |
| 12 | 814 | 0.443% | `agent:codex;session:refactor;prompt:refactor;call:tool/shell;process:sed;effect:read;path:vendor/linux-framework;status:ok` |

## Same process split by prompt tags
| process | total | distinct prompt tags | top splits |
|---|---:|---:|---|
| `rg` | 33,959 | 176 | `refactor`=14,677; `review`=7,176; `design`=3,077; `analyze`=1,068; `test`=975; `benchmark`=829; `research`=716; `docs`=585 |
| `sed` | 30,810 | 180 | `refactor`=13,638; `review`=5,012; `design`=2,942; `test`=1,225; `analyze`=1,154; `benchmark`=1,008; `research`=937; `docs`=496 |
| `tool:tool` | 22,996 | 102 | `refactor`=11,579; `design`=2,572; `review`=2,176; `analyze`=1,683; `test`=1,189; `benchmark`=994; `debug`=314; `research`=246 |
| `git` | 18,592 | 147 | `refactor`=5,966; `review`=4,067; `design`=999; `test`=892; `analyze`=834; `research`=703; `docs`=432; `explain`=373 |
| `find` | 7,818 | 131 | `refactor`=2,863; `review`=1,347; `design`=794; `analyze`=636; `test`=361; `research`=209; `benchmark`=159; `designcodex`=118 |
| `nl` | 7,439 | 75 | `review`=2,959; `refactor`=2,517; `design`=326; `docs`=208; `test`=138; `research`=120; `benchmark`=112; `reviewbu`=110 |
| `python3` | 6,419 | 88 | `refactor`=2,564; `analyze`=1,175; `review`=554; `test`=310; `research`=252; `design`=248; `docs`=138; `ignored`=109 |
| `cargo` | 5,297 | 68 | `refactor`=1,818; `review`=860; `research`=366; `design`=306; `commitlog`=258; `test`=198; `analyze`=194; `explain`=188 |
| `tool:plan` | 3,779 | 77 | `refactor`=1,698; `review`=606; `design`=322; `research`=166; `analyze`=146; `test`=124; `benchmark`=95; `explain`=82 |
| `tool:read` | 3,208 | 30 | `refactor`=1,726; `review`=579; `test`=207; `design`=124; `docs`=106; `listfiles`=52; `workspace`=48; `build`=43 |
| `make` | 2,714 | 32 | `refactor`=1,007; `review`=881; `design`=432; `benchmark`=93; `test`=47; `research`=41; `ignored`=29; `debug`=28 |
| `grep` | 2,411 | 30 | `refactor`=1,474; `review`=477; `test`=104; `docs`=62; `design`=46; `workspace`=33; `explore`=32; `verify`=30 |
| `wc` | 2,352 | 54 | `refactor`=1,096; `review`=596; `design`=70; `docx`=64; `test`=56; `codexcheck`=54; `research`=48; `docs`=42 |
| `tail` | 2,298 | 32 | `analyze`=997; `refactor`=414; `design`=348; `test`=213; `docs`=78; `review`=76; `benchmark`=58; `compare`=30 |
| `ls` | 2,057 | 95 | `refactor`=805; `review`=267; `design`=213; `test`=128; `analyze`=108; `docs`=74; `benchmark`=57; `research`=43 |
