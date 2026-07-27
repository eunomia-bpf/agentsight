# Agent 工具调用行为的全量描述统计

本报告对冻结事件导出的 **551 个 root session、1,918 个 source stream、181,303 次 Tool action** 做确定性描述统计。它回答“Agent 实际怎样调用工具”，而不是评判任务质量、生产率或因果上的 vendor 优劣。

## 1. 数据、schema 与统计口径

| 项目 | Tool action | root session | source stream | artifact-action coverage | observed status |
| --- | --- | --- | --- | --- | --- |
| ActPlane | 66,238 | 139 | 525 | 35.2% | 19.4% |
| academic-writing-skills | 948 | 17 | 25 | 48.8% | 0.7% |
| agentsight | 97,586 | 301 | 1,147 | 33.1% | 17.8% |
| agentskill-observability-paper | 991 | 8 | 36 | 46.8% | 0.0% |
| bpf-developer-tutorial | 1,664 | 35 | 48 | 49.4% | 5.3% |
| eunomia.dev | 13,876 | 51 | 137 | 21.6% | 27.1% |

每个事件均有工具名、命令/参数摘要、毫秒时间戳、`ok/fail/observed` 状态、root session、source stream 和稳定的 tool ordinal；文件证据只在 `actions` 或 `source_paths` 出现时可用。序列、重试和相邻依赖的主单位是 source stream，因此不会把并行 subagent 的 root-timeline 交错误当成一条顺序链。
同目录的 `.json` 与 `.json.gz` 是配对导出，本脚本每项目只选择一个逻辑输入，优先未压缩 `.json`；`input_manifest.csv` 记录投影输入的 SHA-256、文件大小和事件数，`native_source_coverage.csv` 也记录并行批次重建所读原生日志的哈希。
时间戳只有调用开始时间，没有统一的调用结束时间，所以本文的时间指标是“前一调用开始到下一调用开始”的间隔，不能直接解释为工具执行 latency。
所有项目/vendor 对比都是观察性分层；任务、模型、日期、harness 与项目组成同时变化，不能把比例差异解释为 vendor 固有能力；overall 是 action-weighted 池化值，也不是六项目等权平均。
`validation_checks.csv` 的 12 个独立分母/守恒检查全部通过，包括输入事件和、session 和、工具族和、Shell 主类和、stream 转移和、artifact/source-path read 和 native batch 覆盖。

## 2. 工具类型分布

| 工具族 | 调用数 | 份额 | fail/(ok+fail) | observed 份额 |
| --- | --- | --- | --- | --- |
| shell | 124,342 | 68.6% | 3.2% | 5.0% |
| edit | 17,800 | 9.8% | 4.4% | 53.0% |
| wait/control | 15,908 | 8.8% | 11.1% | 59.6% |
| read | 9,001 | 5.0% | 1.1% | 0.1% |
| coordination | 6,538 | 3.6% | 89.2% | 98.3% |
| search | 1,957 | 1.1% | 0.3% | 0.5% |
| task | 1,592 | 0.9% | 1.8% | 51.8% |
| plan/goal | 1,565 | 0.9% | 40.0% | 99.0% |
| fetch | 1,265 | 0.7% | 3.4% | 1.0% |
| write | 667 | 0.4% | 2.3% | 0.1% |
| tool discovery | 313 | 0.2% | 0.0% | 0.0% |
| multimodal | 148 | 0.1% | 8.1% | 75.0% |
| other | 108 | 0.1% | 24.2% | 12.0% |
| skill | 76 | 0.0% | 1.3% | 0.0% |
| network/other | 23 | 0.0% | 0.0% | 0.0% |

| vendor | shell | edit | wait/control | read | coordination | search | task | plan/goal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude | 38.8% | 22.7% | 0.0% | 24.4% | 0.0% | 5.3% | 2.1% | 0.0% |
| codex | 76.2% | 6.5% | 11.0% | N/A | 4.5% | N/A | 0.6% | 1.1% |
| gemini | 4.5% | N/A | N/A | 47.7% | N/A | 31.8% | N/A | N/A |

| 项目 | 前三个工具族 |
| --- | --- |
| ActPlane | shell 61.9%; edit 13.2%; wait/control 12.2% |
| academic-writing-skills | edit 41.2%; shell 31.6%; read 23.0% |
| agentsight | shell 75.7%; edit 7.3%; coordination 6.2% |
| agentskill-observability-paper | read 35.3%; edit 26.6%; shell 24.4% |
| bpf-developer-tutorial | shell 51.4%; read 24.5%; edit 14.9% |
| eunomia.dev | shell 58.5%; wait/control 21.5%; edit 7.4% |

| 工具族 | source category | projected effect | 调用数 | 份额 |
| --- | --- | --- | --- | --- |
| shell | shell | read | 69,546 | 38.4% |
| shell | shell | process | 37,397 | 20.6% |
| wait/control | tool | process | 15,901 | 8.8% |
| edit | edit | write | 9,451 | 5.2% |
| read | read | process | 8,921 | 4.9% |
| edit | edit | process | 8,321 | 4.6% |
| shell | shell | test | 7,246 | 4.0% |
| shell | shell | write | 5,750 | 3.2% |
| coordination | subagent | process | 5,491 | 3.0% |
| shell | shell | network | 2,485 | 1.4% |
| shell | shell | repo | 1,916 | 1.1% |
| search | network | process | 1,877 | 1.0% |

Shell 是主体（68.6%），但原生 read/edit/write 仍合计 15.2%；因此只按工具名统计 Bash/exec 会掩盖大量 shell 内部的读取、测试和仓库操作。
任务委派、协调和 wait/control 合计占 13.3%，说明“做工作”的调用和“管理并发/长任务”的调用在日志中形成可分离的控制平面。
vendor 表显示明显的接口语法差异（例如 Codex 的 apply_patch/wait、Claude 的 Read/Edit/Agent）；这些差异既是行为，也是产品工具面设计造成的测量差异。
Gemini 只有 3 个 session、44 个调用，所有 Gemini 百分比都只是极小样本描述，不与 Claude/Codex 作稳定差异判断。
`tool_family_distribution.csv` 给出所有 project、vendor 和 project×vendor 单元；`tool_name_distribution.csv` 保留未经合并的原始工具名。

## 3. Shell 命令内部构成

| Shell 主类 | 调用数 | Shell 内份额 |
| --- | --- | --- |
| search/text | 62,329 | 50.1% |
| git/repository | 19,925 | 16.0% |
| other | 13,092 | 10.5% |
| data/analysis/runtime | 8,399 | 6.8% |
| filesystem/navigation | 6,123 | 4.9% |
| test | 3,523 | 2.8% |
| process/system | 3,285 | 2.6% |
| container/orchestration | 2,313 | 1.9% |
| build/check | 2,212 | 1.8% |
| lint/format | 2,025 | 1.6% |
| network/remote | 1,044 | 0.8% |
| package/dependency | 72 | 0.1% |

| 提取的 command_name | 调用数 | Shell 内份额 |
| --- | --- | --- |
| sed | 21,372 | 17.2% |
| git | 15,098 | 12.1% |
| const | 14,267 | 11.5% |
| rg | 10,579 | 8.5% |
| python3 | 8,105 | 6.5% |
| nl | 7,455 | 6.0% |
| find | 5,190 | 4.2% |
| cargo | 4,736 | 3.8% |
| grep | 4,174 | 3.4% |
| gh | 3,050 | 2.5% |
| docker | 1,849 | 1.5% |
| wc | 1,746 | 1.4% |
| ls | 1,702 | 1.4% |
| tail | 1,646 | 1.3% |
| cd | 1,478 | 1.2% |

| 项目 | 前三个 Shell 主类 |
| --- | --- |
| ActPlane | search/text 49.8%; git/repository 12.6%; data/analysis/runtime 10.1% |
| academic-writing-skills | filesystem/navigation 47.3%; search/text 27.0%; git/repository 24.7% |
| agentsight | search/text 51.8%; git/repository 16.7%; other 12.2% |
| agentskill-observability-paper | search/text 78.9%; filesystem/navigation 14.5%; git/repository 2.5% |
| bpf-developer-tutorial | search/text 48.8%; git/repository 30.8%; other 11.0% |
| eunomia.dev | search/text 36.6%; git/repository 25.5%; other 19.1% |

分类以完整命令字符串的可复算正则为基础；exporter 能可靠提取首命令时，`command_name` 会优先于参数/引号内的误命中，其他情况按 lint/format→test→build/check→container→package→git 的固定优先级选主类。含多个阶段的复合命令另在同一 CSV 的 `multi_label_presence` 行保留所有命中，避免把 `git diff && cargo test` 简化成单一语义。
`command_name` 是 exporter 提取的首命令提示；Codex `exec` 中的 `const` 等值反映外层 JavaScript 包装，不应当成真实系统命令；这类无可靠提示的记录回退到完整命令文本分类。
search/text 与 filesystem/navigation 反映大量 shell 被当作通用读取接口；它们应与原生 Read/Grep 一起理解，而不应都算作“执行”。
lint/format、test 和 build/check 是命令语法识别，不等于检查覆盖了某次 edit，也不等于成功状态证明结果正确；这一口径比论文 RQ2 的 validation adapter 更宽，仅用于工具行为描述。
项目表说明 shell mix 具有明显案例依赖，因此跨项目池化份额只是 corpus 描述，不是六类项目总体发生率估计。

## 4. 调用序列、n-gram 与 Markov 转移

### 2-gram 前 8

| rank | 工具链 | 次数 | 全部窗口份额 |
| --- | --- | --- | --- |
| 1 | shell → shell | 99,647 | 57.7% |
| 2 | edit → edit | 9,081 | 5.3% |
| 3 | shell → wait/control | 9,003 | 5.2% |
| 4 | wait/control → shell | 8,545 | 4.9% |
| 5 | wait/control → wait/control | 6,714 | 3.9% |
| 6 | edit → shell | 5,832 | 3.4% |
| 7 | shell → edit | 4,957 | 2.9% |
| 8 | read → read | 3,974 | 2.3% |

### 3-gram 前 8

| rank | 工具链 | 次数 | 全部窗口份额 |
| --- | --- | --- | --- |
| 1 | shell → shell → shell | 83,062 | 50.0% |
| 2 | shell → wait/control → shell | 6,747 | 4.1% |
| 3 | edit → edit → edit | 5,946 | 3.6% |
| 4 | shell → shell → wait/control | 5,270 | 3.2% |
| 5 | wait/control → shell → shell | 5,020 | 3.0% |
| 6 | wait/control → wait/control → wait/control | 4,772 | 2.9% |
| 7 | edit → shell → shell | 4,191 | 2.5% |
| 8 | shell → shell → edit | 3,811 | 2.3% |

### 4-gram 前 8

| rank | 工具链 | 次数 | 全部窗口份额 |
| --- | --- | --- | --- |
| 1 | shell → shell → shell → shell | 71,075 | 44.3% |
| 2 | edit → edit → edit → edit | 4,290 | 2.7% |
| 3 | wait/control → wait/control → wait/control → wait/control | 3,864 | 2.4% |
| 4 | shell → shell → wait/control → shell | 3,823 | 2.4% |
| 5 | shell → wait/control → shell → shell | 3,820 | 2.4% |
| 6 | edit → shell → shell → shell | 3,162 | 2.0% |
| 7 | shell → shell → shell → wait/control | 3,110 | 1.9% |
| 8 | shell → shell → shell → edit | 3,052 | 1.9% |

### 高频 Markov 转移

| from | to | 次数 | P(to|from) | 全部转移份额 |
| --- | --- | --- | --- | --- |
| shell | shell | 99,647 | 83.2% | 57.7% |
| edit | edit | 9,081 | 55.8% | 5.3% |
| shell | wait/control | 9,003 | 7.5% | 5.2% |
| wait/control | shell | 8,545 | 54.2% | 4.9% |
| wait/control | wait/control | 6,714 | 42.5% | 3.9% |
| edit | shell | 5,832 | 35.8% | 3.4% |
| shell | edit | 4,957 | 4.1% | 2.9% |
| read | read | 3,974 | 51.2% | 2.3% |
| coordination | coordination | 3,787 | 59.4% | 2.2% |
| coordination | shell | 2,345 | 36.8% | 1.4% |
| shell | coordination | 2,335 | 1.9% | 1.4% |
| read | edit | 2,114 | 27.2% | 1.2% |
| shell | read | 1,931 | 1.6% | 1.1% |
| read | shell | 1,446 | 18.6% | 0.8% |
| search | search | 1,431 | 76.6% | 0.8% |

### Shell 展开后的 hybrid 工具链

| n | rank | 工具链 | 次数 | 份额 |
| --- | --- | --- | --- | --- |
| 2 | 1 | shell:search/text → shell:search/text | 39,920 | 23.1% |
| 2 | 2 | shell:git/repository → shell:git/repository | 10,558 | 6.1% |
| 2 | 3 | edit → edit | 9,081 | 5.3% |
| 2 | 4 | wait/control → wait/control | 6,714 | 3.9% |
| 2 | 5 | read → read | 3,974 | 2.3% |
| 2 | 6 | coordination → coordination | 3,787 | 2.2% |
| 2 | 7 | shell:other → wait/control | 3,783 | 2.2% |
| 2 | 8 | shell:other → shell:other | 3,729 | 2.2% |
| 2 | 9 | shell:git/repository → shell:search/text | 3,626 | 2.1% |
| 2 | 10 | shell:search/text → edit | 3,565 | 2.1% |
| 3 | 1 | shell:search/text → shell:search/text → shell:search/text | 28,938 | 17.4% |
| 3 | 2 | shell:git/repository → shell:git/repository → shell:git/repository | 6,683 | 4.0% |
| 3 | 3 | edit → edit → edit | 5,946 | 3.6% |
| 3 | 4 | wait/control → wait/control → wait/control | 4,772 | 2.9% |
| 3 | 5 | coordination → coordination → coordination | 2,597 | 1.6% |
| 3 | 6 | read → read → read | 2,345 | 1.4% |
| 3 | 7 | shell:search/text → shell:search/text → edit | 2,285 | 1.4% |
| 3 | 8 | wait/control → shell:other → wait/control | 2,201 | 1.3% |
| 3 | 9 | shell:other → wait/control → shell:other | 2,109 | 1.3% |
| 3 | 10 | shell:git/repository → shell:search/text → shell:search/text | 2,039 | 1.2% |

### 项目与 vendor 的首位模式

| 层 | top bigram | 份额 | top trigram | 份额 |
| --- | --- | --- | --- | --- |
| ActPlane | shell → shell | 50.3% | shell → shell → shell | 41.1% |
| academic-writing-skills | edit → edit | 38.1% | edit → edit → edit | 34.5% |
| agentsight | shell → shell | 64.9% | shell → shell → shell | 57.8% |
| agentskill-observability-paper | shell → shell | 16.2% | shell → shell → shell | 13.3% |
| bpf-developer-tutorial | shell → shell | 45.5% | shell → shell → shell | 41.3% |
| eunomia.dev | shell → shell | 46.4% | shell → shell → shell | 39.9% |
| claude | shell → shell | 30.0% | shell → shell → shell | 24.9% |
| codex | shell → shell | 63.8% | shell → shell → shell | 55.0% |
| gemini | read → read | 25.6% | search → search → search | 14.3% |

主 n-gram 在每个 source stream 的同一 `prompt_index` 连续段内滑窗，不跨 prompt/root session，也不把多个 subagent stream 拼接；因此 `read→edit→shell` 表示单次用户 prompt 下可观察的局部调用语法。
Markov 表给出一阶条件概率而非因果依赖；高 self-loop 既可能是批量独立读取，也可能是反复尝试，需要与文件重读和失败重试表联合解释。
`hybrid_shell` 只把 Shell token 展开为命令主类，其他原生工具族保持不变，用于显露 family-level `shell→shell` 下面的搜索、Git、测试与构建链条。
同工具族 run 的长尾以 `shell` 最明显：p90=12.0、max=203；这补充了 n-gram 的局部模式，显示某些行为以长 burst 出现。
完整 2–4 阶每层前 30 模式、所有 project/vendor 分层以及完整长格式转移矩阵分别在 `tool_ngrams.csv`、`markov_transitions.csv` 和 `same_family_runs.csv`；三表同时保留 `full_stream` 敏感性口径。

## 5. 会话调用节奏、异质性与集中度

| 层 | session | calls p50/p90 | active span p50(h) | capped-active calls/h p50 | switch p50 | Gini | top 10% share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ActPlane | 139 | 53.0 / 1066.8 | 0.19 | 611.7 | 19.7% | 0.83 | 74.7% |
| academic-writing-skills | 17 | 21.0 / 160.8 | 0.03 | 769.8 | 18.7% | 0.65 | 54.3% |
| agentsight | 301 | 10.0 / 339.0 | 0.01 | 532.3 | 15.9% | 0.94 | 92.0% |
| agentskill-observability-paper | 8 | 24.5 / 390.7 | 0.39 | 353.1 | 51.9% | 0.65 | 45.7% |
| bpf-developer-tutorial | 35 | 19.0 / 117.2 | 0.06 | 511.6 | 16.3% | 0.63 | 49.7% |
| eunomia.dev | 51 | 42.0 / 981.0 | 0.10 | 538.8 | 20.7% | 0.75 | 63.3% |
| claude | 265 | 22.0 / 360.6 | 0.07 | 565.0 | 25.0% | 0.78 | 66.3% |
| codex | 283 | 19.0 / 837.6 | 0.04 | 543.4 | 10.2% | 0.92 | 88.3% |
| gemini | 3 | 14.0 / 16.4 | 0.04 | 453.6 | 46.2% | 0.06 | 38.6% |

每 session 的调用量高度右偏：中位数 20.0、p90 527.0、p99 4975.5；top 10% session 承担 84.5% 的调用。
active span 是首末调用墙钟跨度，会包含用户离开；`capped-active calls/h` 把每个 source-stream 的同 prompt 相邻间隔最多计 5 分钟。其分子仍是 session 全部调用，所以单调用 prompt 只增加分子、不增加 active-time 分母，会使该启发式 burst 速率机械上偏；并行 stream 还会重复计算重叠墙钟，因此它不是 token、root-session 墙钟或人工时间效率。
same-prompt stream-local switch rate 衡量工具族切换，不受 subagent 交错或新用户 prompt 边界影响；高切换可表示紧密 read/edit/test 循环，也可表示频繁上下文切换，不能单独赋予好坏。
`session_metrics.csv` 保留 551 个 session 的原始指标，便于识别极端会话；`session_pace_summary.csv` 给出项目、vendor 和交叉分层。

## 6. 重复与潜在冗余

### 同 prompt、source-stream 内的重复 read

| estimand | 层 | read instance | 重复份额 | 无中间 mutation/重复 | 重复 identity-unit | call gap p50/p90 | time gap p50/p90(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artifact identity | overall | 43,878 | 46.7% | 76.2% | 29.2% | 3.0 / 88.0 | 24.2 / 1231.2 |
| artifact identity | claude | 8,972 | 29.1% | 68.5% | 20.1% | 2.0 / 11.0 | 8.8 / 75.7 |
| artifact identity | codex | 34,885 | 51.2% | 77.3% | 32.7% | 4.0 / 103.0 | 37.3 / 1452.5 |
| artifact identity | gemini | 21 | 0.0% | N/A | 0.0% | N/A / N/A | 0.0 / 0.0 |
| artifact identity | ActPlane | 14,806 | 47.7% | 77.4% | 27.0% | 3.0 / 46.0 | 18.8 / 555.6 |
| artifact identity | academic-writing-skills | 212 | 5.7% | 58.3% | 6.0% | 6.0 / 22.8 | 111.3 / 173.3 |
| artifact identity | agentsight | 25,909 | 48.6% | 75.8% | 32.3% | 4.0 / 115.0 | 30.2 / 1608.0 |
| artifact identity | agentskill-observability-paper | 242 | 53.7% | 49.2% | 30.4% | 2.0 / 6.0 | 10.2 / 86.1 |
| artifact identity | bpf-developer-tutorial | 520 | 14.2% | 67.6% | 11.7% | 13.0 / 57.0 | 103.4 / 360.9 |
| artifact identity | eunomia.dev | 2,189 | 28.2% | 78.4% | 22.5% | 4.0 / 38.0 | 29.5 / 677.9 |
| exact source path | overall | 53,006 | 44.2% | 87.3% | 27.5% | 4.0 / 95.0 | 29.1 / 1356.5 |
| exact source path | claude | 10,184 | 28.7% | 71.0% | 19.2% | 2.0 / 10.0 | 8.0 / 71.4 |
| exact source path | codex | 42,801 | 48.0% | 89.6% | 30.2% | 4.0 / 111.0 | 43.5 / 1578.0 |
| exact source path | gemini | 21 | 0.0% | N/A | 0.0% | N/A / N/A | 0.0 / 0.0 |
| exact source path | ActPlane | 16,476 | 47.7% | 82.2% | 27.1% | 3.0 / 45.0 | 22.5 / 536.3 |
| exact source path | academic-writing-skills | 262 | 6.9% | 66.7% | 6.6% | 1.0 / 21.6 | 9.2 / 164.0 |
| exact source path | agentsight | 32,529 | 45.1% | 90.7% | 29.5% | 4.0 / 123.0 | 36.1 / 1778.9 |
| exact source path | agentskill-observability-paper | 367 | 37.3% | 48.9% | 17.8% | 2.0 / 6.0 | 9.9 / 93.7 |
| exact source path | bpf-developer-tutorial | 591 | 14.4% | 76.5% | 11.7% | 8.0 / 57.6 | 71.6 / 429.5 |
| exact source path | eunomia.dev | 2,781 | 24.7% | 81.7% | 19.4% | 4.0 / 38.0 | 29.5 / 677.9 |

### 同 prompt、source-stream 内的 Shell 原样重跑

| 层 | Shell call | exact rerun | immediate exact | 失败后立即原样重跑 | 该重跑成功率 |
| --- | --- | --- | --- | --- | --- |
| overall | 124,342 | 15.4% | 0.6% | 26 | 34.6% |
| claude | 14,303 | 5.3% | 3.3% | 9 | 33.3% |
| codex | 110,037 | 16.7% | 0.3% | 17 | 35.3% |
| gemini | 2 | 0.0% | 0.0% | 0 | N/A |
| ActPlane | 40,994 | 21.1% | 0.3% | 7 | 28.6% |
| academic-writing-skills | 300 | 2.3% | 1.0% | 3 | 0.0% |
| agentsight | 73,834 | 12.9% | 0.6% | 12 | 58.3% |
| agentskill-observability-paper | 242 | 5.4% | 1.7% | 0 | N/A |
| bpf-developer-tutorial | 855 | 7.7% | 0.0% | 0 | N/A |
| eunomia.dev | 8,117 | 11.7% | 3.1% | 4 | 0.0% |

`actions` 给出 43,878 个 artifact-identity read，其中 46.7% 在同 prompt 内重复；`source_paths` 给出 53,006 个 exact-path read，对应重复率 44.2%。
artifact identity 可跨 rename 延续，exact path 则把 rename 前后视为不同路径；两者回答不同问题，不能把前者表述成纯“同路径”比例。
两种 estimand 的重复读中，分别有 76.2% 和 87.3% 未观察到中间同 identity/path mutation；这只是潜在重复线索，不能排除外部修改、输出截断或合理的记忆刷新。
Shell 的原样重跑率为 15.4%，立即相邻原样重跑率为 0.6%；这里的 exact 指原始 command 字符串完全相等（不要求 vendor 原始工具名相同），前者包括合理的周期性 `git status`/测试，不能全部视为浪费。
`full_stream` 与 root-session 口径也保留在 CSV；前者允许跨用户 prompt 的 re-grounding，后者还会合并不同 subagent，因此都不作为主要冗余估计。

## 7. 并行批次与顺序关系线索

| 层 | native coverage | batch | multi-call batch | batched-call share | batch max | disjoint/shared/unknown multi-batch |
| --- | --- | --- | --- | --- | --- | --- |
| overall | 100.0% | 140,590 | 19,510 (13.9%) | 33.2% | 9 | 1,602 / 1,975 / 15,933 |
| ActPlane | 100.0% | 48,811 | 8,893 (18.2%) | 39.7% | 9 | 506 / 827 / 7,560 |
| academic-writing-skills | 100.0% | 948 | 0 (0.0%) | 0.0% | 1 | 0 / 0 / 0 |
| agentsight | 100.0% | 76,427 | 9,618 (12.6%) | 31.5% | 9 | 960 / 1,096 / 7,562 |
| agentskill-observability-paper | 100.0% | 991 | 0 (0.0%) | 0.0% | 1 | 0 / 0 / 0 |
| bpf-developer-tutorial | 100.0% | 1,425 | 111 (7.8%) | 21.0% | 6 | 22 / 7 / 82 |
| eunomia.dev | 100.0% | 11,988 | 888 (7.4%) | 20.0% | 9 | 114 / 45 / 729 |
| claude | 100.0% | 36,826 | 0 (0.0%) | 0.0% | 1 | 0 / 0 / 0 |
| codex | 100.0% | 103,732 | 19,503 (18.8%) | 41.7% | 9 | 1,599 / 1,975 / 15,929 |
| gemini | 100.0% | 32 | 7 (21.9%) | 43.2% | 6 | 3 / 0 / 4 |

| 相邻调用分类 | pairs | 份额 |
| --- | --- | --- |
| unknown | 115,302 | 66.7% |
| observed_disjoint | 23,484 | 13.6% |
| observed_overlap | 20,728 | 12.0% |
| dependency_cue | 13,314 | 7.7% |

| 层 | dependency cue | observed overlap | observed disjoint | unknown |
| --- | --- | --- | --- | --- |
| ActPlane | 8.3% | 13.7% | 11.8% | 66.2% |
| academic-writing-skills | 1.5% | 27.8% | 34.8% | 35.9% |
| agentsight | 7.3% | 11.2% | 14.6% | 66.8% |
| agentskill-observability-paper | 1.1% | 41.1% | 11.5% | 46.3% |
| bpf-developer-tutorial | 4.7% | 12.0% | 33.3% | 50.0% |
| eunomia.dev | 8.9% | 6.7% | 11.1% | 73.3% |
| claude | 1.0% | 26.4% | 14.5% | 58.2% |
| codex | 9.2% | 8.8% | 13.4% | 68.6% |
| gemini | 0.0% | 0.0% | 33.3% | 66.7% |

native batch 重建覆盖 100.0% 的调用；其中 33.2% 位于同一 assistant message/response batch 的多调用批次。这证明“发出多个调用”的原生并行机会，但无统一结束时间，不能证明这些调用在墙钟上实际重叠。
池化比例几乎全部来自 Codex（41.7% 的 covered call）和极小的 Gemini 子样本；Claude 的 36,826 个调用中没有同一 assistant event 的多 tool_use，所以不能把 33.2% 当成跨 vendor 的一般发生率。
Claude 用同一 assistant JSONL 事件中的多个 `tool_use`，Codex 用首个 call output 前连续的 `*_call`，Gemini 用同一 message 的 `toolCalls` 数组重建；`native_batch_coverage.json` 记录可读源文件与映射覆盖，`parallel_batches.csv` 保留 source file、call ID 和 event ID 供逐批审计。
同 prompt 相邻调用只把失败原样重试、edit/write→test/build/lint 和 shell/task→wait/control 或 coordination 记为 `dependency_cue`；共享 artifact/path 仅记 `observed_overlap`，不自动当成顺序依赖。
双方 path 非空且不相交只记 `observed_disjoint`，并不证明独立；unknown 往往来自 shell/网络/控制工具缺少 path 证据。因此这里能给出依赖线索的下界，不能给出可信的“独立调用率”；CSV 按具体证据原因拆分。

## 8. 失败率与失败后的行为

| 工具族 | calls | decisive calls | fail | fail/(ok+fail) | observed |
| --- | --- | --- | --- | --- | --- |
| shell | 124,342 | 118,106 | 3,798 | 3.2% | 5.0% |
| edit | 17,800 | 8,363 | 366 | 4.4% | 53.0% |
| wait/control | 15,908 | 6,432 | 711 | 11.1% | 59.6% |
| read | 9,001 | 8,994 | 102 | 1.1% | 0.1% |
| coordination | 6,538 | 111 | 99 | 89.2% | 98.3% |
| search | 1,957 | 1,948 | 5 | 0.3% | 0.5% |
| task | 1,592 | 768 | 14 | 1.8% | 51.8% |
| plan/goal | 1,565 | 15 | 6 | 40.0% | 99.0% |
| fetch | 1,265 | 1,252 | 42 | 3.4% | 1.0% |
| write | 667 | 666 | 15 | 2.3% | 0.1% |
| tool discovery | 313 | 313 | 0 | 0.0% | 0.0% |
| multimodal | 148 | 37 | 3 | 8.1% | 75.0% |
| other | 108 | 95 | 23 | 24.2% | 12.0% |
| skill | 76 | 76 | 1 | 1.3% | 0.0% |
| network/other | 23 | 23 | 0 | 0.0% | 0.0% |

| 层 | calls | fail/(ok+fail) | observed 份额 |
| --- | --- | --- | --- |
| ActPlane | 66,238 | 3.9% | 19.4% |
| academic-writing-skills | 948 | 4.6% | 0.7% |
| agentsight | 97,586 | 3.2% | 17.8% |
| agentskill-observability-paper | 991 | 4.3% | 0.0% |
| bpf-developer-tutorial | 1,664 | 5.2% | 5.3% |
| eunomia.dev | 13,876 | 3.5% | 27.1% |
| claude | 36,826 | 2.8% | 0.1% |
| codex | 144,433 | 3.7% | 23.6% |
| gemini | 44 | 4.5% | 0.0% |

| 失败后的下一 Tool 行为 | 次数 | 份额 |
| --- | --- | --- |
| generic_shell_changed_command_same_class | 1,643 | 31.7% |
| generic_shell_changed_command_different_class | 1,618 | 31.2% |
| switch_to:shell | 552 | 10.6% |
| switch_to:edit | 246 | 4.7% |
| switch_to:read | 244 | 4.7% |
| exact_retry_not_success | 217 | 4.2% |
| same_raw_tool_changed_arguments | 162 | 3.1% |
| end_of_prompt | 135 | 2.6% |
| switch_to:wait/control | 133 | 2.6% |
| exact_retry_success | 60 | 1.2% |
| same_family_changed_tool_or_arguments | 45 | 0.9% |
| switch_to:plan/goal | 31 | 0.6% |
| end_of_stream | 28 | 0.5% |
| switch_to:coordination | 23 | 0.4% |
| switch_to:task | 20 | 0.4% |
| switch_to:search | 15 | 0.3% |
| switch_to:tool discovery | 7 | 0.1% |
| switch_to:write | 4 | 0.1% |
| switch_to:fetch | 1 | 0.0% |
| switch_to:multimodal | 1 | 0.0% |

全量共有 5,185 个 fail；在有明确 ok/fail 的调用中失败率为 3.5%。另有 34,104 个 observed 状态，它们是结果未知/仅观测，不能放进成功率分母当作成功。
失败后的第一步只在同一 prompt 连续段内按 exact retry、非 Shell 原始工具改参数、通用 Shell 更换命令（同/不同命令类）、同工具族换工具、切换工具族和 stream 结束拆分；`end_of_prompt` 单列为保守的放弃/转入下一用户指示代理量，`within_3_calls` 也不会跨 prompt。
失败率同时受工具接口的 status 语义影响，尤其 observed 比例在 vendor 间差异大；因此 vendor 失败率只在各自 decisive 子集内描述，不作能力排名。
原始工具名层面的长尾（例如具体 MCP/API 工具）在 `failure_rates.csv` 中完整保留，可用于定位家族汇总掩盖的高失败工具。

## 9. 时间结构与长尾等待

| 前一工具族 | gap | p50(s) | p90(s) | p99(s) | >60s | 占全部 >60s gap |
| --- | --- | --- | --- | --- | --- | --- |
| other | 49 | 11.28 | 58.44 | 444.55 | 10.2% | 0.1% |
| task | 1,328 | 8.60 | 26.28 | 345.71 | 5.6% | 1.6% |
| coordination | 6,373 | 30.84 | 65.02 | 327.24 | 13.5% | 18.8% |
| wait/control | 15,780 | 30.61 | 42.00 | 187.56 | 6.5% | 22.3% |
| write | 516 | 6.55 | 48.36 | 147.68 | 7.9% | 0.9% |
| plan/goal | 1,400 | 8.26 | 29.07 | 145.83 | 3.3% | 1.0% |
| read | 7,769 | 3.84 | 14.64 | 117.09 | 2.1% | 3.5% |
| shell | 119,803 | 5.26 | 21.98 | 82.31 | 1.9% | 48.3% |
| multimodal | 100 | 8.48 | 21.91 | 68.70 | 4.0% | 0.1% |
| edit | 16,271 | 6.39 | 17.89 | 57.98 | 0.9% | 3.1% |
| fetch | 1,203 | 1.57 | 14.91 | 41.23 | 0.4% | 0.1% |
| tool discovery | 301 | 4.20 | 8.17 | 38.76 | 0.0% | 0.0% |
| skill | 67 | 5.49 | 11.02 | 38.60 | 1.5% | 0.0% |
| search | 1,868 | 0.94 | 14.99 | 36.80 | 0.2% | 0.1% |

### 项目与 vendor 的同 prompt gap

| 层 | gap | p50(s) | p90(s) | p99(s) | >60s |
| --- | --- | --- | --- | --- | --- |
| ActPlane | 62,129 | 5.28 | 34.97 | 98.57 | 2.4% |
| academic-writing-skills | 813 | 3.86 | 18.17 | 67.90 | 1.7% |
| agentsight | 94,385 | 6.75 | 30.48 | 106.48 | 2.9% |
| agentskill-observability-paper | 817 | 5.38 | 19.50 | 132.19 | 2.9% |
| bpf-developer-tutorial | 1,512 | 3.98 | 19.18 | 133.82 | 3.2% |
| eunomia.dev | 13,172 | 7.51 | 24.42 | 94.64 | 2.0% |
| claude | 31,527 | 4.23 | 14.14 | 86.46 | 1.6% |
| codex | 141,262 | 7.13 | 34.16 | 107.30 | 2.9% |
| gemini | 39 | 6.18 | 20.09 | 65.87 | 2.6% |

同一 prompt 内的相邻 source-stream 调用，p50=6.30s、p90=33.35s、p99=104.10s；2.7% 超过 60 秒。
`shell` 对全部 >60s gap 的计数贡献最大（48.3%），但这只是“长间隔前一个可见工具”的归属，间隔还包含模型推理、工具执行、调度和潜在用户等待。
same-prompt 口径排除了显式新 prompt 边界的大部分用户离线时间；`all_adjacent` 口径仍保留在 CSV，可用于完整墙钟轨迹。
没有 end timestamp 时，不能回答真实 runtime 或工具内部等待；要做 latency 研究需回到原生 tool_result/runner duration 字段，不能从本表反推。

## 10. 数据记录重复与稳健性提醒

| 层 | calls | 重复 source-call ID 组 | 跨 stream / core 完全一致 | 首条之外记录 | 份额 |
| --- | --- | --- | --- | --- | --- |
| overall | 181,303 | 312 | 312 / 312 | 316 | 0.2% |
| ActPlane | 66,238 | 0 | 0 / 0 | 0 | 0.0% |
| academic-writing-skills | 948 | 0 | 0 / 0 | 0 | 0.0% |
| agentsight | 97,586 | 291 | 291 / 291 | 291 | 0.3% |
| agentskill-observability-paper | 991 | 0 | 0 / 0 | 0 | 0.0% |
| bpf-developer-tutorial | 1,664 | 0 | 0 / 0 | 0 | 0.0% |
| eunomia.dev | 13,876 | 21 | 21 / 21 | 25 | 0.2% |
| claude | 36,826 | 312 | 312 / 312 | 316 | 0.9% |
| codex | 144,433 | 0 | 0 / 0 | 0 | 0.0% |
| gemini | 44 | 0 | 0 / 0 | 0 | 0.0% |

冻结投影中有 316 条记录与同项目/vendor 的既有 `source_call_id` 重复，约占 0.2%。
312 个重复组全部跨 source stream、跨 source file，且 tool/command/status/timestamp 核心字段完全一致；这符合 resumed/copied native stream 的同一源调用再次进入投影的特征。
本报告保持注册的 181,303 action 分母，不擅自去重，但把该比例单列。
stream-local 重读、重跑和 n-gram 可能受这种复制轻微影响；按 source-call ID 去重会改变“记录行为”与“Agent 实际执行行为”的 estimand，需另行预注册。
项目/vendor 分层可以定位重复集中位置，后续若把这些统计写入论文，建议同时给出保留全部记录与 source-call 去重的敏感性版本。

## 11. 可能之前 empirical study 没覆盖的发现

下面是相对于当前 RQ1（artifact fate/reuse）、RQ2（mutation-validation）、RQ3（workspace focus）、RQ4（component continuity）和 RQ5（skill footprint）最可能新增的观察角度；它们是候选发现，不自动升级为论文 claim。

- **工具语法而非 artifact 语法：** 最常见 bigram 是 `shell → shell`（57.7%）；2–4 阶链和 Markov self-loop/switch 描述了 Agent 的局部操作 grammar，现有 RQ 没有系统比较这种 grammar。
- **控制平面开销：** task、coordination、wait/control 合计 13.3% 的调用，可单独研究“产出动作”和“管理并发/等待”的比例、burst 与失败面。
- **原生多调用批次很少/很常用到什么程度：** 可映射调用中 33.2% 位于 multi-call batch；此前 component 分析区分并行 subagent，但没有量化同一 assistant turn 的 batched tool use。
- **无可见状态变化的重读：** 同 prompt 重复 read 中，artifact identity 口径有 76.2%、exact-path 口径有 87.3% 未观察到中间 mutation；两种 estimand 的差异本身就是需要报告的测量边界。
- **命令级重试与周期性复查：** exact shell rerun 占 15.4%；把失败后的原样重跑、改参数、换工具和成功后的周期性复查分开，可以形成更细的 recovery taxonomy。
- **调用量集中在少数超长 session：** top 10% session 占 84.5% 的调用，说明以“平均 session”为中心会漏掉 corpus 的主要行为质量；应报告 session-level分布或按 root block 加权。
- **长尾是 next-call lag，不只是 test/build 等待：** 同 prompt gap 的 p99 达 104.1s，且长尾贡献按前一工具族高度不均；需要带 end timestamp 的后续研究拆分模型思考、工具 runtime和调度等待。
- **状态语义本身是 vendor 测量偏差：** observed 状态共有 34,104 次；若把它默认当成功，会系统性改变失败率和恢复路径。
- **source stream 复制是行为统计的隐藏敏感性：** 0.2% 的记录是同项目/vendor 下重复 source-call ID；长期轨迹研究需要明确“记录实例”还是“唯一执行调用”作为 estimand。
- **可观察依赖的覆盖缺口：** retry/validation/control handoff 只能提供保守 dependency cue，path overlap/disjoint 都不能分别证明依赖/独立；大量 pair仍是 unknown，说明只靠 file effects 无法恢复完整工具依赖 DAG。

## 12. 复算与产物索引

复算命令：

```bash
python3 docs/tmp/build-and-evaluate/toolcall-behavior-20260726/analyze_toolcalls.py \
  --events-dir docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/events \
  --output-dir docs/tmp/build-and-evaluate/toolcall-behavior-20260726
```

主要 CSV：

- `corpus_coverage.csv`, `schema_coverage.csv`, `input_manifest.csv`, `native_source_coverage.csv`
- `tool_family_distribution.csv`, `tool_name_distribution.csv`, `tool_effect_distribution.csv`
- `shell_command_distribution.csv`, `shell_command_name_distribution.csv`
- `tool_ngrams.csv`, `markov_transitions.csv`, `same_family_runs.csv`
- `session_metrics.csv`, `session_pace_summary.csv`, `intercall_timing.csv`
- `repeated_reads.csv`, `shell_repetition.csv`
- `failure_rates.csv`, `failure_followups.csv`
- `parallel_usage.csv`, `parallel_batches.csv`, `dependency_estimates.csv`
- `source_duplication.csv`, `native_batch_coverage.json`
- `validation_checks.csv`

输入目录：`/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/events`。本次分析未修改 `docs/paper/`，没有执行 git 写操作。
