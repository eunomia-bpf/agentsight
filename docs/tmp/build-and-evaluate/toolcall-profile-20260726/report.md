# Agent tool-call pattern 瓶颈与系统级优化机会

日期：2026-07-26  
分析脚本：[`analyze_toolcalls.py`](analyze_toolcalls.py)  
输入：`docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/events/*.json` 及事件回链的原生 Claude/Codex/Gemini JSONL

## 结论摘要

这批长期 agent 轨迹的瓶颈不是“工具都很慢”，而是三种不同机制叠加：

1. **大量轻量本地调用之间存在远大于工具执行时间的间隙，但 74.8% 不是“模型时间”。** 在 prompt episode 内，从第一个 tool start 到最后一个 tool end 的累计跨度中，工具 busy interval 的并集占 25.2%，相邻工具之间的原始空档占 74.8%。其中最大单条空档为 23.96 h，显然混有暂停/挂起；把每条 gap 截在 5 min 或 1 h 后，gap share 仍分别为 65.5% 和 69.6%。典型 read 的工具中位数只有 74 ms，而调用间 gap 中位数为 6.527 s；按“由下一操作归属”的口径，read 前 gap 中位数为 3.277 s，search 为 5.362 s，mutate 为 9.984 s。证据支持“交替边界很贵”，不支持把全部 gap 归因给 LLM。
2. **真正慢的“工具”主要是等待控制面。** `wait`、`write_stdin`、`wait_agent` 等占 19,920/180,764 = 11.02% 的调用，却占逐调用工具执行时间和的 64.0%；其 30.003 s 中位数主要是在等外部进程或子 agent，而不是做计算。
3. **观测到很多并发，但尚未利用的保守 read 并行机会小得多。** 172,346 条相邻边中，42,679（24.76%）已经在前一结果返回前启动，不能再次计为优化收益；1,801（1.05%）个 disjoint local reads 已在同一 batch；只剩 5,132（2.98%）条“顺序、不同精确路径、无 result-path 传递、未观测同 batch”的 local read 边。另有 37,466（21.74%）强依赖证据/代理和 85,268（49.47%）未知边。read/discovery burst 平均 4.67 calls、观测深度 1.49，但其 27,277 个逻辑并行边里已有 20,344 并发、1,801 同 batch，新增 cross-batch 候选只有 5,132。

逐项结论如下。

| 优化 | 本数据结论 | 可省的执行/往返上界 | 主要限制 |
|---|---|---:|---|
| 下一步 read prefetch | **通用 Markov prefetch 仍偏弱，target-conditioned 有局部信号** | pooled held-out 有 633 个 exact-path hits；只有 versioned full-file provider 能把它们转成执行 eligibility，fused 往返也至多 633；透明 prefetch 为 0 个模型往返 | 2,911 次预取中仅 21.75% path 命中；项目 recall 从 0% 到 45.16%；offset/limit 未预测 |
| 乱序/并行 | **应只对 versioned local-read batch 启用** | 42,679 条边已并发；1,801 已同 batch；剩余 cross-batch 候选 5,132（2.98% edges），最多才可能融合相同数量边界 | 49.47% 边语义未知；5,132 仍是无内容因果的宽松代理；edit/wait 链强依赖 |
| 测试推测执行 | **有延迟收益，但朴素 eager 策略浪费过大** | last-test predictor 可隐藏 1,564.5 s，最多融合 718 个往返 | 命令命中仅 26.2%；每次 edit 都测试会浪费 11,206/13,944 = 80.4% 的执行 |
| 增量 read/cache | **versioned snapshot/diff 有用；通用 result memoization 证据弱** | 2,172 次 exact-read 是有版本 provider 时的 eligibility；其中仅 94 次观测到相同输出；写后 diff 传输情景上界 30.8 MB | partial read/格式变化；外部写不可见；透明 cache 不自动消灭模型往返 |
| 事件驱动 wait | **保守收益存在，但远小于原始 burst 数** | 原始结构上界 8,354；核对同 tool、同 handle、被动、连续 no-progress 后为 **1,456** 次调用/往返（0.81% all calls） | 不缩短真实子进程运行时间；handle 缺失样本不计；仍需进度、取消、超时语义 |
| failure-aware guard/backoff | **结构化错误有用，轨迹不支持大规模“省重试”** | 2,899 个 same-op 后继中只有 126 个 exact-input 重试；95 个随后成功，是有 sound guard/retry 时的条件机会 | web 有 387 个 same-op 后继但 exact-input 为 0；同 operation 不能当同请求 |

这里的“调用”是语义 tool invocation；“往返”是模型→tool→模型边界。透明 prefetch/cache 可以避免外部执行或缩短执行时间，但模型仍然已经发出 tool call，因此默认**不**把它算成消失的模型往返。只有 scheduler 能在同一模型 turn 中预先注入或合并结果时，才使用“fused upper bound”。

## 1. 数据、覆盖与口径

### 1.1 语料

| project | 去重 tool calls | 占比 | native roots | prompt episodes |
|---|---:|---:|---:|---:|
| agentsight | 97,047 | 53.69% | 301 | 3,144 |
| ActPlane | 66,238 | 36.64% | 139 | 4,109 |
| eunomia.dev | 13,876 | 7.68% | 51 | 704 |
| bpf-developer-tutorial | 1,664 | 0.92% | 35 | 152 |
| agentskill-observability-paper | 991 | 0.55% | 8 | 174 |
| academic-writing-skills | 948 | 0.52% | 17 | 135 |
| **all** | **180,764** | **100%** | **551** | **8,418** |

六个 `.json.gz` 是相邻 `.json` 的压缩运输副本，分析只读未压缩文件，避免双计数。按 `(source_file, source_call_id)` 去重时另发现 539 个重复投影，全部来自同一原生调用的重复事件表示，脚本抑制这些重复并写入 `metadata.json`。

投影覆盖 1,094,090 个 source events 和 69,922 个 file actions。事件引用的 1,917 个原生 JSONL（总计 11.66 GB）全部存在；180,720/180,764 = 99.976% 的投影调用能回连到原生记录，180,665 = 99.945% 有 start/end 可计算时长。逐行扫描遇到 2,428 个不可解析 JSONL 行，但没有阻止上述调用匹配；该计数保留在 `metadata.json`。原生 tool results 总计 1,038,114,165 bytes。报告不输出 prompt、tool 参数正文或结果正文，只保存聚合计数、bytes、hash、状态和受限 path tokens。

两个最大项目贡献 90.33% 的调用。因此 pooled 数字是这两个长期 case 的加权描述，不是“六个项目平均 agent”的总体估计。每个 CSV 同时保留 per-project 行，便于检查异质性。

### 1.2 Episode、操作和时间

一个 episode 定义为：

```text
project × native_session × source lane × prompt_index
```

lane 分开 root/subagent 来源，避免把并发子流硬串成一条链。操作分类为 `navigate/search/read/mutate/validate/vcs/wait/web/delegate/control/shell/other`。直接工具按 tool name 分类；shell 用命令和已投影 read/write effects 分类。复合 shell 的词法分解只用于衡量 agent 是否已经主动 batching，不把 pipeline 错当成可乱序 DAG。

原生时间戳支持 tool start→result duration。所谓 `between-tool gap` 是当前已完成工具 frontier 到下一 tool start 的间隔，只在同一 prompt episode 内计算；它包含模型生成、服务队列、harness 调度和潜在暂停。原生记录没有独立的 inference-start、first-token、queue-start，因此不能把这段时间精确拆成“模型算力”与“模型 API 往返”。

### 1.3 依赖不是语义 gold

transcript 看不到模型内部“为什么选择下一调用”。最终脚本因此采用偏向 precision 的证据层级：

- **观测动态独立**：后一调用在前一结果返回前已经启动；它不可能读取该调用的动态结果。注意这只证明现有 trace 已并发，不是剩余收益。
- **已 batch 的 disjoint local reads**：精确路径不同、无 result-path 传递，且 native `batch_id` 相同；有执行层并行证据，但没有可再消灭的模型 turn。
- **剩余顺序 local-read 候选**：只接受 `read→read`、双方有显式路径、精确路径不相交、前一 read 内容中未发现下一路径，且未观测同 batch。search/navigate/web/vcs、缺 target 的调用全部留在 unknown。这仍然只是宽松代理：文件 A 的内容可能以非路径方式决定读取 B。
- **强依赖证据/代理**：已观测并发之外的 mutation→validation、exec→wait、失败反馈、result-path、同 artifact mutation state；read→edit 只有当 exact path 相同且 Edit old-string/patch context 的哈希行出现在先前 read 输出中，才记为 `observed_read_content_in_edit_context`。
- **same-artifact 但无内容证据**：精确路径相同的 read→edit 单列为 `same_exact_artifact_read_edit_proxy`，不再循环地拿“同路径”同时做 motif 选样和真实性证明。
- **未知**：跨文件语义、用户意图、隐含状态，以及不能满足上述高精度条件的边。

全量 172,346 条相邻边的最终拆分是：

| 类别 | edges | share | 如何使用 |
|---|---:|---:|---|
| 已观测并发 | 42,679 | 24.76% | 证明 workload 有 ILP；新增收益记 0 |
| 已同 batch 的 disjoint reads | 1,801 | 1.05% | 可能改进 executor，但不再省模型 turn |
| 剩余顺序 disjoint local-read 候选 | 5,132 | 2.98% | 新 batching/fusion 的宽松上界 |
| 强依赖证据/代理 | 37,466 | 21.74% | critical-path 代理 |
| unknown（含 3,086 same-path read→edit 代理） | 85,268 | 49.47% | 不自动乱序 |

`work/depth` 只保留强边、遗漏 unknown，因此仍是逻辑乐观上界；它还包含已经实现的并发，绝不能解释为“还可提速多少”。

## 2. 高频 pattern

### 2.1 高频相邻 n-gram

| pattern | occurrences | unique calls covered | 强依赖边 | 已并发 | 剩余顺序 local-read | 未知/其他 |
|---|---:|---:|---:|---:|---:|---:|
| read→read | 26,748 | 37,405（20.69%） | 7.57% | 49.48% | 19.19%（另 6.73% 已 batch） | 17.03% |
| edit→edit | 12,161 | 17,020（9.42%） | 57.47% | 0.90% | 0% | 41.62% |
| shell→shell | 11,006 | 16,732（9.26%） | 3.57% | 36.50% | 0% | 59.93% |
| explore→read | 8,397 | 16,794（9.29%） | 26.88% | 31.07% | 0% | 42.05% |
| wait→wait | 8,354 | 11,297（6.25%） | 96.41% | 3.59% | 0% | 0% |
| explore→explore | 7,392 | 11,662（6.45%） | 14.48% | 27.29% | 0% | 58.24% |
| read→explore | 7,307 | 14,614（8.08%） | 7.40% | 33.98% | 0% | 58.62% |
| shell→wait | 6,508 | 13,016（7.20%） | 99.23% | 0.77% | 0% | 0% |
| read→edit | 6,237 | 12,474（6.90%） | 19.05% | 0.71% | 0% | 80.25% |

这些 n-gram 是滑窗计数，覆盖率不可相加。`read→read` 是最高频 pattern；其中 49.48% 已经并发、6.73% 已同 batch，只有 19.19% 是剩余顺序候选。旧口径把 web/vcs/无 target 的 read-only 边也视为 independent，会明显高估机会，最终表已排除。`edit→edit` 则只有观测到的 0.90% 并发；`shell→wait` 与 `wait→wait` 本质上是 futures/polling 控制流，增加 worker 并行度不会消除依赖。

### 2.2 语义 motif

| motif | occurrences | unique-call coverage | calls/occ. mean | 观测串行深度 mean | 关键依赖/并行拆分 |
|---|---:|---:|---:|---:|---:|
| repeat read same target | 23,291 | 16.97% | 2.00 | 1.07 | 1,603 strong；3,759 已并发；17,929 unknown |
| exact-artifact read→edit | 16,849 | 13.92% | 2.00 | 1.29 | 4,176 有 read-content→edit-context 证据；11,970 仅 same-path proxy；18 已并发 |
| read/discovery burst | 13,592 | 35.09% | 4.67 | 1.49 | 20,344 已并发；1,801 已 batch；5,132 剩余顺序候选；16,673 unknown |
| edit burst | 4,859 | 9.42% | 3.50 | 2.29 | 6,989 strong；110 已并发；5,062 unknown |
| exploratory directory roam | 3,969 | 20.37% | 9.28 | 2.07 | 12,227 已并发；1,375 已 batch；4,134 剩余顺序候选；10,938 unknown |
| poll/wait burst | 2,943 | 6.25% | 3.84 | 3.72 | 96.41% / 3.59% / 0% |
| edit→validation cycle | 2,738 | 29.40% | 19.41 | 4.08 | 13,579 strong；9,885 已并发；757 剩余 local-read；25,156 unknown |
| validation retry、期间无 edit | 2,642 | 4.33% | 3.47 | 1.31 | 996 strong；2,011 已并发；66 剩余 local-read；3,460 unknown |
| bounded grep→read→edit→test | 1,065 | 7.14% | 12.12 | 4.00 | 2,742 strong；2,956 已并发；234 剩余 local-read；5,461 unknown |

定义：

- `read/discovery burst`：连续至少 2 个 navigate/search/read。
- `exploratory directory roam`：连续至少 4 个 discovery calls 且 target 涉及至少 3 个目录；这是“目录漫游”的结构代理，不是“无用探索”标签。
- `grep→read→edit→test`：同一 episode 内 search 后 6 calls 内有 read、随后 9 calls 内有 mutate、再随后 12 calls 内有 validate 的贪心 bounded subsequence。
- `edit→validation cycle`：两次 validation 之间存在至少一次 mutation；区间从该轮首个 edit 到 test。

四点值得注意：

1. **经典 grep→read→edit→test 存在，但不是主导形态。** 共有 1,065 次，覆盖 7.14% calls；其 11,843 条 occurrence edge slots 中有 2,742 strong（23.15%）、440 same-path proxy（3.72%）、5,461 unknown（46.11%），剩余逻辑并行边大多也已并发。它不是一条可整体预编译的固定四指令流水线。
2. **“裙带读”仍是最明确的批处理对象，但大部分 ILP 已经出现。** read/discovery burst 覆盖 35.09% calls；平均 4.67 calls、depth 1.49。其逻辑并行边 27,277 条中，20,344 已经并发、1,801 已同 batch，真正剩余的顺序 proxy 为 5,132。
3. **same-artifact 不能用循环定义证明“真依赖”。** 16,849 个 exact-path read→edit pairs 中，4,176（24.78%）有 edit context 行确实出现在 read 输出中的观测证据；11,970（71.04%）只有同路径代理；其余为其他强 path/control 证据或已并发。哈希行方法偏向 precision，会漏掉短行、语义改写和截断内容，因此 24.78% 是证据下界，不是“其余都独立”。
4. **edit burst 不能照搬 read 并行策略。** 6,989 条边有 mutation state/path 等强依赖，5,062 条未知；只有 110 条已观测并发，没有新的顺序 local-read 候选。
5. **validation 离 edit 常常很远。** edit→validation cycle 平均 19.41 calls，但观测 depth 为 4.08；中间存在可重叠工作，也存在大量未知依赖。它适合“最后一次 edit 后 debounce speculation”，不适合“每次 edit 都立即跑 test”。

## 3. 瓶颈归因

### 3.1 调用数、执行时间和结果字节不是同一个热点

| operation | calls / share | tool median / p95 | preceding gap median / p95 | tool-runtime sum | result bytes |
|---|---:|---:|---:|---:|---:|
| read | 51,656 / 28.58% | 74 ms / 759 ms | 3.277 s / 18.148 s | 31.97M ms | 408.9 MB |
| shell-other | 29,510 / 16.33% | 323 ms / 16.960 s | 5.481 s / 22.396 s | 117.06M ms | 331.0 MB |
| mutate | 26,886 / 14.87% | 51 ms / 1.481 s | 9.984 s / 58.764 s | 10.94M ms | 11.9 MB |
| wait | 19,920 / 11.02% | 30.003 s / 60.015 s | 4.002 s / 12.655 s | 536.08M ms | 29.1 MB |
| search | 21,218 / 11.74% | 87 ms / 1.366 s | 5.362 s / 28.414 s | 12.54M ms | 159.2 MB |
| vcs | 12,664 / 7.01% | 97 ms / 1.406 s | 0 / 20.071 s | 10.66M ms | 48.6 MB |
| validate | 5,754 / 3.18% | 1.283 s / 12.867 s | 4.251 s / 16.213 s | 21.73M ms | 20.1 MB |
| web | 3,132 / 1.73% | 6.756 s / 11.689 s | 0 / 7.256 s | 21.96M ms | 7.3 MB |

逐调用 tool runtime 和为 837.84M ms（232.7 h），但并发调用会重复计时。wait 一类单独为 536.08M ms（149.0 h），占 64.0%。除 wait 外，真正工具执行较慢的是任意 shell、delegate、web；read/search 的执行只占 tool-runtime sum 的 5.31%，却占全部 calls 的 40.31% 和结果 bytes 的 54.72%。

8,410 个有完整 timing 的 episode 累计跨度为 3,094.48M ms。tool-busy interval 并集为 778.79M ms（25.17%），between-tool gap 为 2,315.69M ms（74.83%）。这是 episode 累计量，多个 project/lane 并发时会重叠，不能当作真实历时相加。

raw share 对 idle 敏感，最终 CSV 因此给出 sensitivity：

| gap 口径 | gap sum | gap share（相对 busy + 该口径 gap） |
|---|---:|---:|
| 原始 | 2,315.69M ms | 74.83% |
| 每条最多计 1 h | 1,780.28M ms | 69.57% |
| 每条最多计 5 min | 1,480.89M ms | 65.54% |

共有 129,475 条正 gap，中位 6.527 s、p95 33.550 s、p99 88.834 s；276 条超过 5 min，47 条超过 1 h，最大 86,242,128 ms（23.96 h，单条占 raw gap 3.72%）。即便截断长 idle，gap 仍占多数，支持“轻量 tool-call loop 的模型/API/harness 边界是热点”；但任何把 74.83% 直接换算成可节省 LLM latency 的结论都是错误的。

因此：

- 对 read/search，主要收益来自**减少模型/tool 交替和结果传输**，不是加速 `read(2)` 或 `rg` 本身。
- 对 wait，主要收益来自**改变控制协议**，不是并行执行同一条依赖链。
- 对 test/web/长 shell，执行时间足够长，满足命中率时才值得 prefetch/speculate。
- 在没有模型服务端 TTFT、decode 和 KV-cache telemetry 时，不能从本数据声称“模型计算占 74.8%”；这里只能说 tool-free gap 占 74.8%。

### 3.2 结果传输

原生 tool results 经 `to_text()` 规范化后总计 1.038 GB。read 408.9 MB、shell-other 331.0 MB、search 159.2 MB，三者合计 86.60%。这是 UTF-8 payload-byte proxy，不是 wire bytes、token 数或 prefill 时间。这说明把每次调用都优化几十毫秒，可能不如减少重复全文、限制 search fanout、把 poll progress 改成 delta，以及让模型消费结构化摘要。

## 4. Prefetch

### 4.1 实验

按 project 内 native session 起始时间做 80/20 chronological split。模型只用训练段的转移矩阵：

- `op` context：当前 operation；
- `op_target` context：当前 operation + 当前 primary target；
- 目标：下一调用是否为 read，以及 exact next path。

`in_sample_ceiling` 是使用全语料计数后对同一语料的 Bayes top-k 上界，明确包含训练泄漏，只回答“这个 context 最多能解释多少重复”；`chronological_80_20_conditional` 假设 oracle 已知下一步一定是 read；`actionable` 还必须自行判断要不要预取。

### 4.2 数字

| policy | next-read hit/recall | prefetch precision | issued | hits | 可隐藏的 read runtime |
|---|---:|---:|---:|---:|---:|
| in-sample `op`, top-1 | 4.12% | N/A | N/A | 1,955/47,424 | N/A |
| in-sample `op_target`, top-1 | 51.46% | N/A | N/A | 24,405/47,424 | N/A |
| held-out conditional `op_target`, top-1 | 31.63% overall；seen-context 内 45.72% | 45.72% | 1,601 | 732 | 174.186 s |
| held-out conditional `op_target`, top-3 | 37.51% | 20.09% | 4,321 | 868 | 224.424 s |
| held-out actionable `op_target`, threshold 0.25 | 27.36% | 21.75% | 2,911 | 633 | 141.035 s |
| held-out actionable `op_target`, threshold 0.50 | 16.29% | 21.65% | 1,741 | 377 | 90.614 s |

pooled held-out 有 13,240 transitions、2,314 个 next reads。`op_target` 的 in-sample top-1 可解释 51.46% 历史 read，held-out conditional 降到 31.63%；713/2,314 个 next reads 的 context 在 pooled train 中未见。generalization gap 仍然明显：**重复路径能解释历史，但不能稳定预测所有新 session 的 exact next file**。

actionable threshold 0.25 下，2,911 次预取命中 633 次，2,278 次浪费，浪费率 **78.26%**；命中仅占 held-out transitions 的 4.78%。read 中位执行只有 74 ms，累计可隐藏的实际 read runtime 上界为 141.035 s。

pooled 模型会让项目间相同 `op|target` context 共享路径先验，这对真正的跨仓通用 predictor 可能有用，也可能是乐观泄漏。逐项目独立训练后，同一 threshold 的加总为 2,506 issued、525 hits、20.95% precision、22.69% next-read recall、112.584 s hidden；各项目 recall 从 0%（academic-writing-skills）到 45.16%（agentskill-observability-paper），两个大项目为 ActPlane 31.02%、agentsight 25.43%。因此部署应以 project-local 或 repository-family held-out 为准，不能只看 pooled 633 hits。

### 4.3 省什么、为什么常常没用

- **透明 prefetch/cache**：pooled 有 633 次 held-out exact-path hits（project-local 加总 525）。若预取的是 versioned full-file snapshot，后续任意 range 可从内存服务，才可把它视为最多 633 次外部 read execution eligibility；模型往返减少 **0**。
- **主动结果注入或 fused turn**：633 只是 path-level ceiling，脚本没有预测 offset/limit/格式参数。只有 scheduler 还能满足最终完整 read args 并安全注入结果时，才可能最多减少 633 个 held-out tool roundtrips；实际上界更低。
- **有效场景**：稳定 manifest、README、固定配置、同一 target 的局部反复检查，且 workspace 有 version id。
- **无效机理**：下一 path 高熵、新文件和新目录 context unseen；read 很快；top-k 增加 recall 同时迅速增加无用 I/O；partial read 的 offset/limit 也会变化。
- **反例**：一次 grep 输出决定读取哪个错误日志或测试文件时，下一 path 对结果有真依赖；提前读最常见文件既浪费，也可能把 stale content 注入模型。

结论：不要做“按 operation 转移矩阵盲预取下一个文件”。更合理的是 versioned workspace snapshot + 低成本 metadata warmup，或只对长期稳定、side-effect-free、低 fanout context 启用。

## 5. 乱序与并行执行

### 5.1 ILP 上界

在只保留强依赖代理、忽略未知语义边时：

- logical work / critical-depth aggregate = **6.93×**；
- episode logical parallelism 中位数 **2.52×**，p95 **15.33×**；
- 49,612/172,346 = **28.79%** 边属于逻辑并行集合；
- 其中 **42,679 已经并发**，**1,801 已同 batch**，剩余顺序 local-read proxy 只有 **5,132**；
- 37,466/172,346 = **21.74%** 有强依赖证据/代理；
- 49.47% unknown。

这是类似 instruction-level parallelism 的**逻辑乐观**上界，不是预测 speedup，也不是“仍可获得 6.93×”。它按调用数而非耗时加权、忽略 unknown，且把 42,679 条已经实现的并发也体现在较短 critical path 中。read 的 10-way fanout 可能只省几百毫秒工具时间，长 test 的 2-way overlap 反而更值钱。

### 5.2 最合适的窗口

read/discovery burst 有 13,592 次、63,436 unique calls。其边分成 20,344 已并发、1,801 已同 batch、5,132 剩余顺序 disjoint local-read proxy、16,673 unknown；只有最后的 5,132 是新增 cross-batch/fusion 的宽松边界上限。directory roam 内相应为 12,227 已并发、1,375 已 batch、4,134 剩余、10,938 unknown。

这个策略对局部 read 比全局 DAG 更可靠：

```text
snapshot_version = V
batch [
  read(file_a, V),
  read(file_b, V),
  grep(pattern, subtree_c, V)
]
```

同一 snapshot 使无写入的 read 集合可重排；batch result 保留 per-call status、bytes 和 provenance。

### 5.3 为什么不是所有调用都能并行

- exact-artifact read→edit 的 16,849 pairs 中，仅 4,176 有 read 内容行进入 edit context 的直接证据；11,970 只是同路径代理。不能把代理全称为真依赖，也不能把没有命中哈希的部分当独立。
- edit burst 有 6,989 strong edges、5,062 unknown；不同文件 edit 也可能共享接口、符号或生成物。
- poll/wait burst 的 96.4% 是控制依赖；并行更多 wait 没有意义。
- grep→read→edit→test motif 的强依赖和未知合计 68.0%，不能整体乱序。
- 现有 agents 已在 shell 层主动 batching：124,009 个 shell calls 中 51,064（41.18%）含多个 `&&/||/;` 或换行片段，词法估计 507,918 个 shell primitives，平均 4.10 primitives/call、p95 14。剩余 call-level ILP 不能假装这些 primitive 都是尚未利用的机会。

### 5.4 省什么

- 外部工具调用数：**0**，只是并行发出。
- 对**已并发的 42,679 edges**：新增外部工具调用和模型往返收益都为 0；它们只证明执行框架已经利用部分 ILP。
- 对**已同 batch 的 1,801 disjoint reads**：模型往返收益为 0；若 executor 仍串行，可能有工具 wall-time 收益，但 trace 不足以重放。
- 对**剩余 5,132 顺序 local-read edges**：外部调用数仍为 0；只有模型把多个 future reads 一次规划/发出时，才可能最多融合 5,132 个边界。`batch_id` 对部分供应商不是可靠的 turn id，因此 5,132 仍是宽松上界。
- 实际 wall-time 低于逻辑 6.93×，因为 unknown edges、资源竞争、结果序列化和既有 shell batching；本数据没有 scheduler replay，不能给因果 speedup。
- 反例：连续对同一文件的小 Edit 必须观察上一 patch 的新文本；把它们并发可能导致 patch mismatch 或 lost update。

结论：实现 typed read-batch + workspace version/effect sets，优先于一个对所有工具做自动乱序的通用 scheduler。

## 6. 推测执行

### 6.1 Test speculation

5,754 个 validate calls 中，2,738 个属于 mutation→validation cycle。cycle test failure rate 为 11.69%；全部 validate failure rate 为 10.24%。失败率本身不意味着应该更早跑：推测执行是否有价值取决于测试命令可预测、测试是否作用于同一 workspace version，以及可隐藏的 runtime 是否大于浪费成本。

若 oracle 完全知道最后一次 edit 后将运行的 test 命令：

- 2,730/2,738 cycles 有正 overlap window；
- 可隐藏 6,875.855 s / 8,795.370 s = **78.18%** 的这些 test runtime。

但简单的“同 lane 上一次 test command”预测器只命中 718/2,738 = **26.22%**，加权可隐藏 1,564.511 s = 17.79%。这 718 个命中具有正 overlap window，因此 fused upper 最多消灭 718 个 roundtrips；透明 speculation 仍消灭 0 个模型/tool 边界，只让结果更早 ready。

### 6.2 Eager-after-every-edit 为什么没用

这些 cycles 中共有 13,944 次 edits。若每次 edit 都按最终 test runtime 推测一次：

- 只有每轮最后一个 version 的 2,738 次可能被正式 test 消费；
- 11,206 次是 stale-version execution；
- 浪费率 **80.36%**；
- 用每轮最终 test runtime 乘前面 stale edit 数的情景估算为 27,227.345 s，是正式 cycle test runtime 的 **3.10×**。这不是实际运行过的中间版本 test 时长，若增量测试更短会高估、若中间版本更慢会低估。

这比预测器能隐藏的 1,564.511 s 大得多。更糟的是 build/test 争抢 CPU、I/O 和锁，可能反过来拖慢 agent。

### 6.3 有效条件、反例和策略

有效：

- test command 长期稳定；
- test 只读或运行在 copy-on-write snapshot；
- 最后一次 edit 后有数秒模型思考窗口；
- test runtime 长，且资源余量充足。

无效：

- edit burst 仍在进行，前面每个 snapshot 很快 stale；
- test command 由错误内容、变更模块或 grep 结果动态决定；
- test 有外部副作用、写数据库、占端口或修改 build cache；
- 测试很短，调度成本大于隐藏时间。

推荐的是 **debounced, versioned speculation**：在 mutation quiet window 后预测一次；只对历史命中率、预计 runtime、资源成本的期望收益为正的命令执行；新 edit 到来立即取消或丢弃旧 snapshot 结果。失败结果只有在 workspace version 完全匹配时才能提交。

## 7. 增量执行与缓存

### 7.1 Read reuse

- same-target repeat-read motif：23,291 次。
- 两次同 target read 之间未观测到该 target mutation：22,895 次，占全部 read calls 的 44.32%；若 harness 维护完整、versioned file snapshot，这是“可从 snapshot 服务”的 eligibility 上界，涉及 161.119 MB result bytes，不是 result-cache hit。
- 上述 22,895 中只有 **308** 次原生结果 hash 完全相同，这是观测到 exact-result reuse 的下界（1.35%）。主要原因是相同文件不代表相同 offset/limit、输出格式或外部状态。
- 使用完整原生参数 hash 后，同一 lane、同一 invocation、无观测 workspace mutation 的 read 有 **2,172 次**，涉及 3.770 MB；其中只有 **94** 次结果 hash 相同（4.33%）。因此 94 是最保守的观测复用下界，2,172 只有在 canonical/versioned provider 保证 freshness 与参数语义时才是执行 eligibility，占 read calls 的 4.20%。

因此，应用层格式化 result memoization 的可观测稳定 hit 很低；更有用的是 filesystem server 持有 `file@workspace_version`，按新的 range 请求从同一 snapshot 服务，而不是盲返上一段 tool result。

### 7.2 写后 reread 的 diff

8,523 次 same-target reread 之间观测到 mutation，完整 reread results 为 57.883 MB。用 native Edit/patch 新内容 payload 作为 changed-byte proxy，逐次上界可省 30.801 MB，即 53.21%。

这个数是传输上界，不是已验证压缩率：

- patch payload 可能含 old/new 双份文本或重复 patch；
- 多次 edit 可能改同一区域；
- 格式化行号和上下文会改变；
- shell 写入和外部进程写入的真实 delta 可能不完整。

可实现接口应返回 `(base_version, new_version, hunks)`，模型/harness 验证 base version 后应用；版本不匹配时回退全文。

### 7.3 重复命令

完整原生 invocation 相同且未观测 workspace mutation的上界：

| operation | opportunities | bytes upper | 可否直接复用 |
|---|---:|---:|---|
| shell-other | 4,967 | 2.230 MB | 通常不可；可能依赖时间、网络、进程、环境 |
| read | 2,172 eligibility；94 observed-identical | 3.770 MB 条件上界 | 仅对 canonical/versioned file 安全 |
| vcs | 449 | 0.225 MB | 需锁定 index/refs/worktree version |
| search | 420 | 0.297 MB | 对 versioned subtree 较安全 |
| validate | 81 | 0.620 MB | 通常不可；测试可能 nondeterministic 或依赖外部状态 |
| navigate | 42 | 0.023 MB | 需锁定目录 snapshot |

大多数相同 validate invocation（1,888 次）发生在观测 mutation 之后，不能缓存；无 mutation 的只有 81 次。由此可见“缓存 test 结果”不是主要机会，增量 test selection 或 build graph cache 才可能有价值，但本轨迹没有 test-level dependency graph，不能估算其命中率。

### 7.4 省什么

- 透明 snapshot/cache：省外部执行和 bytes，但模型 roundtrip 默认仍为 **0**。
- fused snapshot provider：观测相同结果下界只有 94；strict exact-invocation eligibility 为 2,172；若允许新 range 从完整 file snapshot 服务，same-target eligibility 是 22,895。后两者都是带 version/freshness 假设的上界，不能称实测 cache hits。
- diff：最多省 30.801 MB，不一定省调用；push invalidation/delta 才可能合并 roundtrip。
- 反例：subagent、watcher 或用户在 trace 外改文件；同 path 版本已经变化，此时无版本号 cache 会向模型提供 stale code。

## 8. 数据中额外暴露的优化点

### 8.1 从 polling 改为 event-driven futures

这是数据中最明显的控制面异味，但按 handle 复核后，直接可省上界显著小于仅按“连续 wait-family”计算的数字。

- wait-family calls：19,920，占 11.02%。
- tool runtime sum：536.079M ms，占所有逐调用 runtime 的 64.0%。
- no-progress results：4,291，占 wait calls 的 21.54%。
- `wait_agent`：4,012 calls，其中 3,058 = 76.22% 返回 no-progress。
- 原始连续 wait-family bursts：2,943；burst 中 11,297 calls；中位长度 2，p95 10。若不看 tool、handle、是否带输入、是否有进展，结构算式给出 8,354，但这**不是可执行优化数**。
- 最终保守规则要求：同一 tool、同一 `cell/session/thread/job/target/agent` handle、被动调用（排除带输入的 `write_stdin/send_input`）、结果为 no-progress，并且连续。得到 **863 bursts、2,319 empty polls**，保留每 burst 一次 await 后可省 **1,456 calls/roundtrips**，占 all calls 0.81%；burst 中位 2、p95 4。

实现上应让 long-running exec/subagent 返回 future，harness 负责在 completion、progress threshold、deadline 或 error 时唤醒模型。`wait(timeout)` 仍作为显式 deadline/cancel primitive，而不是让模型每 10–60 s 再问一次。

这不会缩短子进程真实 runtime，也不会把依赖链并行化；它最多省 1,456 次已验证同 handle 的模型唤醒、tool envelope 和空结果处理。handle 缺失或 no-progress 文本未被正则识别的样本未计，故它也是 precision-oriented 上界/coverage 下界的混合口径。反例是交互程序需要模型看到流式输出后及时输入；此时应按结构化 progress event 唤醒，而不是完全等到结束。

### 8.2 Failure-aware local guard、negative cache 与 retry backoff

共有 5,466 个可观测失败，占 3.02% calls；2,899 = 53.04% 在后两次调用内出现同 operation，其中 2,017 后继成功。这个宽松规则只能描述“失败后仍在做同类工作”，不能称真正 retry。

最终脚本另算三种更窄的口径：

| retry 口径 | within 2 calls | 后继成功 | 能否作为可省上界 |
|---|---:|---:|---|
| same operation | 2,899 | 2,017 | 否；query/path/对象可能完全不同 |
| same exact native input + same tool | **126** | **95** | 仅在 sound preflight、幂等自动 retry 或 negative cache 存在时 |
| exact target overlap | 1,877 | 1,487 | 仍可能是对同文件的不同修复，不等于重复请求 |

126 个 exact-input repeats 中只有 13 个是“再次失败且 error signature 相同”，表明简单 negative cache 的直接证据很小。分 operation 看，mutate 为 64 个 exact-input retries（53 成功），validate 30（20 成功），shell 17（12 成功），read 5（3 成功），search/vcs/web 都是 0。可以本地检查路径存在、Edit old-string 唯一性、workdir、regex/arg schema并返回结构化 error；但本轨迹只支持 **126-call 条件上界**，不支持旧的 1,184-call preflight 说法。

web 是重要反例：443 failures 中 387 个在两 calls 内出现另一个 web operation，但 exact-input retry 为 **0**，same-target 只有 65 且仅 3 个成功。它更像搜索/query 改写、不同 URL 或恢复流程，不能据此推出固定 backoff 会省 387 次。只有工具返回明确 rate-limit/timeout code 时，harness 才应实施 backoff/circuit breaker；本数据未结构化 error taxonomy，无法量化该子集。

反例：validate failure 是 agent 需要消费的语义证据，不能被 guard“优化掉”；mutation 后也不能 negative-cache 旧的失败。

### 8.3 Typed batch/DAG API，而不是继续让 agent 拼 shell

41.18% 的 shell calls 已包含多个词法 command fragments，平均约 4.10 fragments/call、p95 14。这个现象说明 agent 已经主动绕过逐 tool loop；它也说明单纯统计 shell tool calls 会低估实际 OS operations。

更好的系统接口不是鼓励更长的 shell 字符串，而是提供：

- typed batch 中每个 node 的 read/write resource set；
- 显式依赖 edge；
- per-node timeout/status/bytes；
- snapshot version 与 commit barrier；
- 失败时只重跑受影响 node；
- 一个聚合 result envelope。

这样可以把 read burst 的并行机会显式化，并给 cache/speculation 安全条件；同时避免 shell quoting、长输出混合、无法取消单节点等问题。词法 fragment 数可能因引号内分号而高估，pipeline 也本来就有数据依赖，因此 507,918 primitives 不能被解释为同量可并行工作。

### 8.4 结果 delta 和服务端上下文保持

1.038 GB tool results 与大量短 read/search 表明另一个热点是结果进入模型上下文，而非文件系统 I/O。可以：

- search 只返回 path/line index，按需取 excerpt；
- poll 只返回新增 bytes 和 terminal state；
- repeated read 返回 version+diff；
- batch results 去重同一 path/context；
- 对长 test 先返回 structured summary，再按 handle 获取 full log。

本数据没有 tokenization、provider KV-cache、prefill 或 GPU residency telemetry，不能把 bytes 直接换算为 token/latency。类似 [INFERCEPT](https://arxiv.org/abs/2402.01869) 的模型服务端 interception/KV 保持可能与这里的高频 tool interruption 互补，但这份轨迹无法估计该层收益。

## 9. 与相关系统机制的关系

- [LLMCompiler](https://arxiv.org/abs/2312.04511) 用 planner、task fetcher 和 executor 构造 parallel function-call DAG。本数据支持其“存在 ILP”的前提，但 42,679 条边已经并发，保守的新增顺序 local-read proxy 只有 5,132；49.47% unknown 要求 runtime effect/version 检查。
- [ReWOO](https://arxiv.org/abs/2305.18323) 将 reasoning plan 与 tool observations 解耦，以减少交替调用。目录漫游和 read burst 表明提前形成 read plan 可能减少 roundtrip；但 exact-artifact read→edit 中至少 4,176 次有内容流证据，grep/search 结果也会决定下一路径，coding workflow 不能完全脱离 observations。
- [PASTE](https://arxiv.org/abs/2603.18897) 基于控制流/dataflow pattern 推测 tool execution。本分析复现了“pattern 存在”，但 exact-path 的 chronological generalization 明显低于 in-sample ceiling；因此部署必须报告 held-out precision、waste、版本一致性，而不能只报告历史 pattern frequency。
- [Speculative Actions](https://arxiv.org/abs/2510.04371) 通过 tentative action 与 commit verification 追求 lossless acceleration。本数据中的 80.4% eager-test waste 和 mutation invalidation 说明 copy-on-write snapshot/commit barrier 是 coding speculation 的必要条件。
- [ToolCaching](https://arxiv.org/abs/2601.15335) 强调 cacheability 与 freshness 的异质性。本数据同样显示 same target 很常见，但 exact native invocation 很少；cache key 必须包含 workspace version、range/args 和 effect class。
- [INFERCEPT](https://arxiv.org/abs/2402.01869) 优化 tool interception 时的模型 serving/KV state。这是本报告未测量但可能重要的另一层：即使 tool execution 被 cache，频繁恢复模型上下文仍可能有成本。

本报告没有复现这些系统的 published speedup；它只用本地长期轨迹判断各机制的适用机会、上界和失败模式。

## 10. 推荐系统设计顺序

优先级按“数据机会 × 安全性 × 实现确定性”排序：

1. **event-driven futures**：先消除同 handle 的连续被动 no-progress polls，保留 progress/deadline/cancel；保守上界 1,456 calls，原始 8,354 只作结构诊断。
2. **versioned read snapshot + typed batch**：模型一次声明多个 local-read nodes，scheduler 依据精确 resource sets 并发；先覆盖 5,132 条尚未观测 batch/并发的 read edges，不重复计算 42,679 条既有并发。
3. **result delta/handles**：全文 read、search、test、poll 都用 versioned delta 和 lazy full-log handle，减少 1.038 GB result traffic。
4. **deterministic preflight + structured error**：path、workdir、Edit match、regex/arg schema 在本地快速判定；先用 126 个 exact-input retry 做错误 taxonomy。web 只有在结构化 rate-limit/timeout 证据下才 backoff，不能按 same-op 频率推断。
5. **debounced speculation**：仅对长、稳定、side-effect-free 的 test/read 启用；使用 workspace version，按命中率×可隐藏 runtime−资源浪费做 admission。
6. **最后才是通用 Markov prefetch**：exact next path 的 held-out precision 不足，应在前五项有 telemetry 后再做小范围自适应。

一个安全 scheduler 至少需要以下运行时字段：

```text
call_id, operation, exact_args_hash
read_set, write_set, side_effect_class
workspace_version_in, workspace_version_out
future_id, batch_id, dependency_ids
start, first_byte, end, input_bytes, output_bytes
cache_hit, speculation_hit, cancelled, stale_version
```

当前原生 session 已有 call start/end/result bytes，但缺 workspace version、显式 dependency、first-byte、cache/speculation outcome 和模型 serving 时间；这些缺口正是本报告只能给上界、不能直接回放 scheduler speedup 的原因。

## 11. 局限与反证边界

1. 这是 post-hoc observational profile，不是把优化实现后做 A/B replay；所有“省多少”均标注为 execution、bytes 或 fused-roundtrip 上界。
2. 49.47% adjacent edges 语义未知。强依赖代理和 5,132 条顺序 local-read 候选都有漏报/误报；没有声称恢复模型内部真实因果图。
3. `between-tool gap` 不是纯 LLM latency，可能包含服务队列、harness、用户或调度暂停；累计 episode 时间也会跨并发 lane 重叠。
4. agentsight + ActPlane 占 90.33% calls；小项目不能支撑稳定的独立总体估计。所有 pooled 结论应结合 per-project CSV。
5. shell 分类和 primitive 数是词法代理；quoted semicolon 可能高估，pipeline/data transform 本来有依赖。
6. no-observed-mutation 不等于文件一定没变。trace 外用户、watcher、编译器和 subagent 写入都需要 workspace version/invalidation 才能安全 cache。
7. mutation diff 使用 Edit/patch payload bytes，不是 filesystem block delta；30.801 MB 是情景传输上界。
8. read→edit 内容证据只对规范化后长度至少 8 的行做 64-bit hash、每个输出最多 6,000 个唯一行；它偏向 precision，会漏掉短行、语义改写、截断和多行重组。64-bit 碰撞概率很低但非零。
9. `batch_id` 在 Claude message 中更接近同 turn 标识，在部分 Codex function-call 记录中可能退化为 call id；因此“未同 batch”的 5,132 不能等价为“必经独立模型往返”。
10. failure 从 native error/exit code 与投影 status 推导，工具没有标准 status 时可能漏报；error signature 是规范化文本 hash，不是语义 error taxonomy。
11. 结果只描述 2026-01-11 至 2026-07-21 的这组六项目长期轨迹，不自动推广到浏览器、数据库事务、支付、机器人或其他 side-effect-heavy agents。

## 12. 可复现产物

| 文件 | 内容 |
|---|---|
| `corpus_summary.csv` | 六项目调用数、session、原生覆盖、bytes |
| `operation_profile.csv` | operation/project/vendor 的 calls、runtime、gap、bytes、failure |
| `timeline_profile.csv` | episode 内 tool busy union、raw gap、5min/1h capped sensitivity |
| `transition_patterns.csv` | top-25 bigram/trigram/4-gram，拆分已并发/已 batch/剩余顺序 read |
| `named_patterns.csv` | 九类 motif 的次数、覆盖、深度、内容证据与并行拆分 |
| `dependency_profile.csv` / `dependency_summary.csv` | 相邻操作对与细粒度依赖标签/汇总 |
| `ilp_profile.csv` | logical work/depth 上界及已实现/剩余机会拆分 |
| `prefetch.csv` | in-sample ceiling、chronological held-out conditional/actionable 策略 |
| `speculation.csv` | mutation→test、命令预测、隐藏时间、eager waste |
| `incremental.csv` | reread、exact invocation、snapshot/diff/cache 上界 |
| `polling.csv` | raw wait-family burst 与同 handle 被动 empty-poll 保守上界 |
| `failure_recovery.csv` | same-op、exact-input、same-target retry 分层 |
| `shell_batching.csv` | 现有复合 shell batching 的词法统计 |
| `metadata.json` | 输入、定义、去重、原生回连、脚本/input/CSV SHA-256 与 native manifest digest |
| `validate_artifacts.py` | 校验 script/input/CSV hash、核心算术与报告数字锚点 |
| `artifact-manifest.json` | 最终报告、脚本、CSV、metadata 的冻结 SHA-256 |

一条命令重算：

```bash
python3 docs/tmp/build-and-evaluate/toolcall-profile-20260726/analyze_toolcalls.py
python3 docs/tmp/build-and-evaluate/toolcall-profile-20260726/validate_artifacts.py
```

CSV 先写同目录 `.tmp` 再用 `os.replace` 原子替换；`metadata.json` 记录本次脚本 SHA-256、六个输入 JSON 的 SHA-256/size/mtime、1,917 个 native 文件 path+size+mtime manifest digest，以及每个 CSV 的 SHA-256。报告是解释性手写产物，最终交付前另做了 CSV 数字锚点检查；未来若把该 profile 纳入持续流水线，应该让报告表格由 CSV 模板自动生成。
