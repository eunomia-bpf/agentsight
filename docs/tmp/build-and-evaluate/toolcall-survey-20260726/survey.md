# LLM Agent 工具调用行为的 empirical 研究与系统级优化：文献 survey

检索截止日期：**2026-07-26**。

## 检索范围与判定口径

本 survey 先检查了本地 `docs/reference/` 与
`docs/background-related-work.md`，再用网络检索补充并核验原始来源。检索入口包括
arXiv、DBLP、ACM DL、USENIX、OpenReview/会议页面和 Google Scholar 链接，关键词组合包括
`agent tool-call trace/trajectory/workload characterization`、`coding agent
failure retry/repetition`、`agent tool prefetch/speculative/parallel/cache`、
`agent syscall/eBPF/I/O/resource profile` 等。文中只列能够在论文主页、正式会议页面或
DOI 页面核实的工作；尚未正式发表者标为 arXiv preprint。

这里的“empirical tool-call study”要求论文实际分析调用日志、轨迹或运行时测量，而不仅是
报告 benchmark 的最终成功率。SWE-bench、AgentBench、AgentBoard、BFCL、ToolBench、
τ-bench 等是重要的任务/能力评测基础设施，但若论文只报告正确率或 resolution rate，
不计作本问题中的“工具调用行为测量”先例。

先给结论：

- **已有**真实日常 coding-agent 工具分布与延迟研究，最直接的是 TraceLab；不能再声称
  “首次测量真实 coding-agent 工具调用”。
- **已有** benchmark 轨迹上的序列模式、重复/回退、失败率、重试环和失败恢复研究；这些
  角度本身也不是空白。
- **已有**投机工具执行、异步/并行调用、工具结果缓存、语义知识缓存和重复工作流编译系统；
  “agent 工具层从未被优化”不是成立的表述。
- **已有** CPU、内存、工具阶段延迟和 eBPF 可观测性研究；但在本次检索范围内，
  **未找到**对真实长期 agent 工作负载报告 syscall 类型分布、逐路径文件 I/O、
  网络/进程创建模式的系统性 workload study。
- 目前最可防守的空白是：在**真实、跨原生会话、持久工作区**中，把精确调用参数、状态变化、
  失败后的恢复序列、跨调用依赖/副作用和 OS 成本联合起来，并据此量化缓存、预取、并行和
  增量计算的安全上界。

# 1. LLM Agent 工具调用行为的 empirical / measurement 研究

## 1.1 覆盖情况总览

符号：✓ 表示论文直接、系统地测量；△ 表示只部分覆盖或仅有案例；— 表示未覆盖。

| 工作 | 自然日常轨迹 | 工具分布/延迟 | 序列/阶段 | 重复、失败或恢复 | OS 资源 | 跨原生会话的持久工作区 |
|---|---:|---:|---:|---:|---:|---:|
| TraceLab | ✓ | ✓ | △ | — | — | — |
| Agentic AI Workload Characteristics | — | ✓ | ✓ | ✓ | — | — |
| AgentCgroup | — | ✓ | ✓ | ✓ | ✓ | — |
| Bouzenia & Pradel | — | △ | ✓ | ✓ | — | — |
| Process-Centric Analysis / Graphectory | — | △ | ✓ | ✓ | — | — |
| Failure as a Process | — | — | ✓ | ✓ | — | — |
| Beyond Resolution Rates | — | △ | ✓ | △ | — | — |
| Coherence Collapse / TRAJEVAL | — | △ | ✓ | ✓ | — | — |
| AgentTrails | △（示例） | △ | ✓（依赖图） | △ | — | — |
| 本论文当前语料定位 | ✓ | 可测 | 可测 | 可测 | 可联合 | ✓ |

这里最重要的区分是：TraceLab 的“真实”是 43 名开发者日常使用 Claude Code/Codex 的
session trace；其余多数大规模行为研究仍是 SWE-bench、Terminal-Bench、ADE 等隔离
benchmark task 的重复运行。AgentTrails 使用真实/科学 agent 轨迹作演示，但并非大规模
自然工作负载 characterization。

## 1.2 直接测量系统工作负载与工具调用的论文

### TraceLab

**Kan Zhu, Mathew Jacob, Chenxi Ma, Yi Pan, Stephanie Wang, Arvind Krishnamurthy,
Baris Kasikci. 2026. [TraceLab: Characterizing Coding Agent Workloads for LLM
Serving](https://arxiv.org/abs/2606.30560). arXiv preprint.**

**测了什么 / 没测什么：**测量 43 名开发者在 2025-09 至 2026-06 日常使用 Claude
Code 和 Codex 产生的 4,265 个 session、357,161 个 LLM step 和 432,510 次工具调用，
报告工具 popularity/latency 长尾、每 step 调用数和 prefix-KV cache 行为；但公开 trace
删除了原始用户消息及工具输入/输出文本，论文也没有分析调用成功状态、精确参数级重复、
失败后的恢复策略、artifact 依赖/副作用或 syscall/I/O。

可核实的重要数字包括：平均每个 request 有 10.8 次工具调用、每个 LLM step 1.2 次；
80 多种工具中 top-3 占比超过 80%；超过 1 分钟的调用仅占 4%，却占工具总时间的 85%；
全局 prefix-cache hit rate 为 95.7%。这篇论文已经覆盖“真实调用分布”和“工具与模型服务
时间结构”，是本论文最强的直接相邻工作。

### Agentic AI Workload Characteristics

**Yichao Yuan, Ankita Nayak, Souvik Kundu, Nishil Talati. 2026.
[Agentic AI Workload Characteristics](https://arxiv.org/abs/2605.26297).
arXiv preprint.**

**测了什么 / 没测什么：**在统一 Claude Code scaffold 中用 Gemma/Qwen 的 reasoning
与 non-reasoning 配置运行 ADE-Bench、DABStep、GAIA、SWE-bench Pro 和
Terminal-Bench 2.0，测工具类型、延迟、结果长度、失败率、失败重试导致的上下文增长以及
从 read/explore 到 execute/write 的阶段转移；但它是 benchmark workload，不测真实日常
会话、跨 session 工作区状态、精确同参重复距离、artifact lineage 或 OS syscall/I/O。

该文已经直接回答“有没有测失败和重试”：例如 Gemma Instant 在 ADE 上发出 2,757 次
Edit 调用，其中 95.4% 失败，形成最长 786 turns 的失败重试环。因此，“工具失败率/重试
从未被 empirical study 覆盖”是不成立的。

### AgentCgroup

**Yusheng Zheng, Jiakun Fan, Quanzhi Fu, Yiwei Yang, Wei Zhang, Andi Quinn. 2026.
[AgentCgroup: Understanding and Controlling OS Resources of AI
Agents](https://arxiv.org/abs/2602.09345). arXiv preprint, v3.**

**测了什么 / 没测什么：**在 Claude Code 上运行 144 个 SWE-rebench task、两种 LLM，
把工具语义/时间与每秒 CPU、内存采样对齐，并统计同一 test command 的连续重试组；
但只覆盖单一 agent/benchmark、CPU/内存而非 syscall 或逐文件 I/O，也没有自然长期或
跨 session 的持久工作区行为。

它报告 85%–97% 的 task 含有至少三个相同测试命令构成的 retry group，GLM 平均每 task
3.9 个 retry group、最长 56 次连续重试，并占 20.5% 执行时间。这是“重复测试/重试行为”
和 OS 资源后果的直接先例。

## 1.3 轨迹、序列模式、重复与失败研究

### Thought–Action–Result 轨迹

**Islem Bouzenia, Michael Pradel. 2025.
[Understanding Software Engineering Agents: A Study of Thought-Action-Result
Trajectories](https://arxiv.org/abs/2506.18824). ASE 2025.**

**测了什么 / 没测什么：**统一分析 RepairAgent、AutoCodeRover、OpenHands 的 120 条
程序修复轨迹和 2,822 次 LLM 交互，测 action 类别、常见 action sequence、重复/反模式、
token 与 thought-action-result coherence；但样本来自隔离修复任务，不测真实工具延迟、
OS 成本、精确参数/目标级重复或跨 session 工作区演化。

### Graphectory / process-centric analysis

**Shuyang Liu, Yang Chen, Rahul Krishna, Saurabh Sinha, Jatin Ganhotra,
Reyhaneh Jabbarvand. 2026.
[Process-Centric Analysis of Agentic Software
Systems](https://doi.org/10.1145/3798271). PACMPL 10(OOPSLA1), 2026.**

**测了什么 / 没测什么：**把 4,000 条 SWE-agent/OpenHands × 四种 LLM 的
SWE-bench Verified 轨迹编码为时序/语义图，量化探索、定位、修改、验证、重复、回退和
低效长轨迹，并用在线诊断/rollback 改善问题实例；但不测自然使用、精确工具 latency/
failure status、OS 资源、artifact producer-consumer lineage 或跨 session 持久状态。

### Failure as a Process

**Xiangxin Zhao, Han Li, Shuaiting Li, Tianyi Zhao, Earl T. Barr, Federica Sarro,
He Ye. 2026. [Failure as a Process: An Anatomy of CLI Coding Agent
Trajectories](https://arxiv.org/abs/2607.09510). arXiv preprint.**

**测了什么 / 没测什么：**从三个 CLI-agent scaffold、七种模型的 3,843 条
Terminal-Bench 轨迹中人工标注 1,794 条完整轨迹、63,000 多个 step，分析失败的出现、
根因、演化和恢复；但研究对象仍是 benchmark 失败过程，不报告工具调用延迟/资源、精确
同参重试、跨 session 状态或真实开发者使用。

这篇 2026-07 的新论文意味着“失败后的恢复是否发生、何时不可恢复”也已有系统研究；
本论文必须把区别落在真实长期工作区、工具级可观测字段和系统代价上。

### Beyond Resolution Rates

**Tural Mehtiyev, Wesley Assunção. 2026.
[Beyond Resolution Rates: Behavioral Drivers of Coding Agent Success and
Failure](https://arxiv.org/abs/2604.02547). arXiv preprint.**

**测了什么 / 没测什么：**分析 9,374 条轨迹、19 个 agent、8 个 framework、14 个 LLM
和 500 个任务，在控制 task difficulty 后比较 context-before-edit、validation 等行为与
成功/失败的关系；但不测工具执行层延迟、参数级重复/依赖、OS 行为或自然跨 session 使用。

### Coherence Collapse / TRAJEVAL

**Myeongsoo Kim, Dingmin Wang, Siwei Cui, Farima Farmahinifarahani,
Terry Yue Zhuo, Shweta Garg, Baishakhi Ray, Rajdeep Mukherjee, Varun Kumar.
2026. [Coherence Collapse: Diagnosing Why Code Agents Fail After Reaching the
Right Code](https://arxiv.org/abs/2603.24631). arXiv preprint.**

**测了什么 / 没测什么：**在三种架构、七种模型的 16,758 条轨迹中，把 search/read/edit
与 reference patch 对齐，发现覆盖、反复改写和“到达正确代码后又破坏”的 thrashing，并
验证 checkpoint 干预；但不测真实调用分布、工具 failure status/latency、系统资源或跨
session workspace evolution。

### APR traceability

**Ira Ceka, Hailie Mitchell, Saurabh Pujar, Luca Buratti, Shyam Ramji,
Junfeng Yang, Gail Kaiser, Baishakhi Ray. 2026.
[Understanding Automated Program Repair Agents Through the Lens of
Traceability: An Empirical Study](https://arxiv.org/abs/2506.08311).
ISSTA 2026.**

**测了什么 / 没测什么：**追踪五个 APR agent 在 500 个修复任务中从 issue 到 patch
validation 的完整决策过程，分析故障复现、测试生成/选择和 bash 等 primitive tools；
但不提供系统级工具分布/延迟/重试距离，也不覆盖自然长期或跨 session 工作区。

### Success/failure trajectory comparison

**Oorja Majgaonkar, Zhiwei Fei, Xiang Li, Federica Sarro, He Ye. 2025.
[Understanding Code Agent Behaviour: An Empirical Study of Success and Failure
Trajectories](https://arxiv.org/abs/2511.00197). arXiv preprint.**

**测了什么 / 没测什么：**比较 OpenHands、SWE-agent、Prometheus 在 SWE-bench 上的
成功/失败轨迹长度、方差、context gathering、defensive programming 和 fault
localization；但不测工具级失败重试、调用 latency/资源、artifact 依赖或跨 session 行为。

### Procedural fingerprinting

**Hamidah Oderinwale. 2026.
[Agent trajectories as programs: fingerprinting and programming coding-agent
behavior](https://arxiv.org/abs/2606.16988). arXiv preprint.**

**测了什么 / 没测什么：**用 ProcGrep 比较十个 coding agent 的 action vocabulary、
程序式序列、edit streak、熵和行为指纹，并以 85.7% 准确率识别 agent；但数据仍是
SWE-bench 轨迹，不测真实失败 status、系统成本、持久 artifact 或跨 session 变化。

### Agent provenance

**Eden Wu, Sonia Castelo, Yurong Liu, Cláudio T. Silva, Juliana Freire. 2026.
[AgentTrails: Towards Trust and Reuse for Agentic
Tasks](https://arxiv.org/abs/2607.18816). VLDB DASHSys Workshop 2026.**

**测了什么 / 没测什么：**从工具参数、响应、路径、URL 和中间 artifact 恢复
producer-consumer provenance graph，并对多条轨迹构造 joined graph 以显示重复调用、
依赖和 detour；但这是 4 页 prototype，当前只有 10 条手工标注 trace/234 条 gold edge
的初步依赖验证和两个 usage scenario，尚无大规模、长期、跨原生 session 的 workload
统计，也不测工具失败/OS 成本或优化收益。

AgentTrails 使“首次从工具轨迹恢复 artifact 依赖”这一主张不可用；仍可主张的是在真实
长期 corpus 上对这些依赖、重复和副作用做规模化 empirical characterization，并把它们
转化为优化可行性/安全性测量。

## 1.4 对问题 1 的直接回答

- **真实 agent 的工具调用分布：有。**TraceLab 是最直接且规模最大的公开先例。
- **序列模式与阶段变化：有。**Bouzenia–Pradel、Graphectory、ProcGrep、Agentic AI
  Workload Characteristics 都有覆盖。
- **重复率：部分有。**AgentCgroup 精确统计连续同一 test command 的 retry group；
  Graphectory/TRAJEVAL/ProcGrep 测反复、回退或 edit streak。**未找到**在真实日常 trace
  上按 canonicalized `(tool, target, arguments)` 报告重复率、reuse distance 和跨 session
  重现率的论文。
- **失败和重试：有。**Agentic AI Workload Characteristics 报工具失败率和 pathological
  retry loop；AgentCgroup 报测试重试；Failure as a Process 报失败发生与恢复。
  **未找到**真实日常长期 corpus 上同时对失败原因、精确重试、恢复动作、最终恢复效果和
  系统成本做联合测量的工作。

# 2. Agent 系统级性能优化：工具执行层而非纯 LLM inference

## 2.1 投机执行、预取和 LLM–tool overlap

### PASTE

**Yifan Sui, Han Zhao, Rui Ma, Zhiyuan He, Hao Wang, Jianxun Li, Kaiqiang Xu,
Kai Chen, Yuqing Yang. 2026.
[Parallelizing Tool Execution and LLM Generation for Low-Latency Agent
Serving](https://arxiv.org/abs/2603.18897). arXiv preprint.**

**做了什么 / 没做什么：**PASTE 从历史轨迹中的重复模式预测带具体参数的未来工具调用，
在 LLM 仍生成时投机执行并隔离结果，在 deep research、coding、scientific agent 上将
平均 task completion time 降低 43.5%；但其模式与效果来自 benchmark/离线历史，不测
自然长期 trace 中可预测调用的覆盖率、状态依赖、副作用冲突、跨 session 漂移或 OS 代价。

这说明“工具 prefetch/speculative execution 没有人做过”不成立。新的问题应是：
真实 coding-agent 调用中有多少能被**正确预测且安全执行**，预测收益是否被副作用、
workspace mutation 和错误恢复抵消。

### Sutradhara

**Anish Biswas, Kanishk Goel, Jayashree Mohan, Alind Khare, Anjaly Parayil,
Ramachandran Ramjee, Chetan Bansal. 2026.
[Sutradhara: An Intelligent Orchestrator-Engine Co-design for Tool-based
Agentic Inference](https://arxiv.org/abs/2601.12967). arXiv preprint.**

**做了什么 / 没做什么：**用 tool-aware prompt splitting、decode 中的 streaming tool
dispatch 和 orchestrator-aware KV cache 管理重叠 prefill、decode 与工具执行，在
production-scale synthetic requests 上将 median final-token-render latency 降低 15%、
E2E 降低 10%；但不分析自然 agent 的精确调用模式、失败重试、artifact 依赖或通用工具
结果缓存。

### Cortex

**Chaoyi Ruan, Chao Bi, Kaiwen Zheng, Ziji Shi, Xinyi Wan, Jialin Li. 2026.
[Cortex: Achieving Low-Latency, Cost-Efficient Remote Data Access For LLM via
Semantic-Aware Knowledge Caching](https://arxiv.org/abs/2509.17360).
NSDI 2026.**

**做了什么 / 没做什么：**为远程知识访问设计 semantic cache、staticity-aware
eviction 和一阶 Markov prefetch，在 search workload 上实现超过 85% hit rate/最高
3.6× throughput、coding workload 上提高 20%；但主要针对远程读侧知识/文件访问，不是
可任意修改本地 workspace 的通用工具，也未从真实长期 agent trace 验证可缓存/可预取
比例和失效规律。

## 2.2 并行和异步工具调用

### AsyncFC

**Guangyu Feng, Huanzhi Mao, Prabal Dutta, Joseph E. Gonzalez. 2026.
[Concurrency without Model Changes: Future-based Asynchronous Function Calling
for LLMs](https://arxiv.org/abs/2605.15077). arXiv preprint.**

**做了什么 / 没做什么：**AsyncFC 在纯 execution layer 用 future/placeholder 解耦
decoding 与函数执行，并在依赖允许时实现函数间并行，无需修改模型或工具实现，在 BFCL
和改造的 SWE-bench/HotpotQA 上降低 E2E 时间；但依赖由 annotation/保守 root lock
处理，没有测真实日常轨迹中的独立边比例、动态文件冲突、错误传播或 critical-path 上界。

### CPU-aware overlap

**Ritik Raj, Souvik Kundu, Ishita Vohra, Hong Wang, Tushar Krishna. 2025.
[Towards Understanding, Analyzing, and Optimizing Agentic AI Execution: A
CPU-Centric Perspective](https://arxiv.org/abs/2511.00739). arXiv preprint.**
（首次提交于 2025，本文核验的是 2026-04 的 v3。）

**做了什么 / 没做什么：**在 Haystack RAG、Toolformer、web-augmented LangChain、
Mini-SWE-Agent、ChemCrow 上 profile CPU/GPU 工具阶段，并用 COMB/MAS 重叠和调度
异构 agent workload，服务延迟最高改善 3.9×；但它做 component-level resource profile，
不分析自然工具序列、参数级依赖/重复、失败恢复或跨 session 状态。

TraceLab 的自然 trace 平均只有 1.2 个 tool call/LLM step，说明 agent 显式一次发出多个
工具调用并不普遍；但这并不等同于“没有潜在并行性”，因为跨相邻 step 的独立调用也可能
被调度器重叠。**未找到**用真实日常轨迹恢复依赖 DAG 后报告安全并行比例和关键路径缩短
上界的论文。

## 2.3 工具结果缓存、KV cache 和结果复用

### TVCACHE

**Abhishek Vijaya Kumar, Bhaskar Kataria, Byungsoo Oh, Emaad Manzoor,
Rachee Singh. 2026.
[TVCACHE: A Stateful Tool-Value Cache for Post-Training LLM
Agents](https://arxiv.org/abs/2602.10986). arXiv preprint.**

**做了什么 / 没做什么：**为 agent post-training 的并行 rollout 建立工具调用序列树，
只有完整历史前缀匹配时才复用结果，以保证 sandbox state 等价；在 terminal、SQL、video
任务上 hit rate 最高 70%、median tool latency 最高降低 6.9×且不降低 reward，但它不是
在线自然 agent serving，也不能在分叉、外部变化或长寿命 repo 中做通用 invalidation。

### Cortex

Cortex（上文）是语义知识/远程数据结果缓存和 prefetch 的直接先例；它覆盖读侧 semantic
reuse，但没有解决修改本地文件、运行测试、安装依赖、启动服务等有副作用工具的缓存正确性。

### TraceLab 与 KV cache

TraceLab 测的是 LLM prefix/KV cache 而非工具结果缓存：95.7% token-weighted hit rate
仍因 human-paced gap 产生昂贵 miss，并提出延长 retention、压缩或 prefetch。这已经覆盖
“真实 agent 的 KV cache 机会测量”，但没有实现新的 cache system，也没有把 exact tool
result reuse 与 KV reuse 联合。

### Agentix、AIOS：相邻但不应误称为工具结果缓存

**Michael Luo, Xiaoxiang Shi, Colin Cai, Tianjun Zhang, Justin Wong, Yichuan Wang,
Chi Wang, Yanping Huang, Zhifeng Chen, Joseph E. Gonzalez, Ion Stoica. 2026.
[Agentix: An Efficient Serving Engine for LLM Agents as General
Programs](https://www.usenix.org/conference/nsdi26/presentation/luo).
NSDI 2026.**

**做了什么 / 没做什么：**把 agent program 作为 LLM serving scheduler 的一等对象，
利用 program/call 依赖做优先级和抢占，在相同 latency 下将 program throughput 提高
4–15×；但优化对象是 LLM 请求排队/模型服务，不执行、缓存或预测外部工具。

**Kai Mei, Xi Zhu, Wujiang Xu, Wenyue Hua, Mingyu Jin, Zelong Li, Shuyuan Xu,
Ruosong Ye, Yingqiang Ge, Yongfeng Zhang. 2025.
[AIOS: LLM Agent Operating System](https://arxiv.org/abs/2403.16971).
COLM 2025.**

**做了什么 / 没做什么：**把 LLM、context、memory、storage、access 和 tools 管理抽象为
AIOS kernel services，并报告多 framework agent serving 最高 2.1× 加速；但它是 agent
runtime/OS abstraction，不是对真实工具行为的 workload study，也没有精确结果缓存或
文件状态增量计算。

## 2.4 重复工作流编译和“增量计算”

### Agent Workflow Optimization

**Sami Abuzakuk, Anne-Marie Kermarrec, Rishi Sharma, Rasmus Moorits Veski,
Martijn de Vos. 2026.
[Optimizing Agentic Workflows using Meta-tools](https://arxiv.org/abs/2601.22037).
arXiv preprint.**

**做了什么 / 没做什么：**AWO 从已有轨迹发现重复工具序列并编译为 deterministic
meta-tool，在两个 benchmark 上最多减少 11.9% LLM call、成功率提高 4.2 percentage
points；但不测自然长期 session 中模式稳定性、参数/状态依赖、失效条件和跨 repo 可迁移性。

### Production tool-making

**Kalle Kujanpää, Ning Liu, Shahnawaz Alam, Yeshwanth Reddy Sura, Tianyu Yang,
Kristina Klinkner, Shervin Malmasi. 2026.
[Tool-Making and Self-Evolving LLM Agents in Low-Latency
Systems](https://arxiv.org/abs/2607.08010). arXiv preprint.**

**做了什么 / 没做什么：**把 fulfillment-center alarm triage 中 44-node SOP 的重复代码
步骤预编译为经验证、版本化工具，生产 p50 latency 降低 42%，并在 1,500 个历史 alarm
上降低错误；但场景是固定 SOP/后端 schema，不是开放式 coding workspace，也没有从通用
agent trace 自动推导依赖感知增量 recomputation。

**本次检索未找到**类似 build system/dataflow engine 的通用工作：它能够在开放式 agent
session 中记录工具输入输出与读写集，在 workspace 发生部分修改后只重算受影响节点，并对
跨 session 的失效正确性和收益作 empirical evaluation。TVCACHE 是“完全相同历史前缀”
的安全复用，Cortex 是读侧 semantic cache，AWO/tool-making 是重复过程编译；三者都不是
上述意义的通用增量计算。

## 2.5 全工作流优化的边界工作

**Gohar Irfan Chaudhry, Esha Choukse, Haoran Qiu, Íñigo Goiri, Rodrigo Fonseca,
Adam Belay, Ricardo Bianchini. 2026.
[Murakkab: Resource-Efficient Agentic Workflow Orchestration in Cloud
Platforms](https://www.usenix.org/conference/osdi26/presentation/chaudhry).
OSDI 2026.**

**做了什么 / 没做什么：**用 declarative workflow、profile-guided optimizer 和 adaptive
runtime 联合选择模型/硬件/执行配置，最多降低 GPU 使用 2.8×、能耗 3.7×、成本 4.3×；
但它假定可暴露的结构化 workflow，重点是全栈配置与 SLO，不是从开放式 agent 的精确工具
历史学习重试、依赖、cacheability 或 speculation safety。

因此，系统优化文献可以分成三层，写 related work 时应避免混淆：

1. **LLM serving 层：**Agentix、TraceLab 的 KV 分析、AIOS 的 LLM/context scheduling。
2. **workflow/orchestration 层：**Murakkab、Sutradhara、CPU-aware scheduling。
3. **真正工具执行/结果层：**PASTE、AsyncFC、TVCACHE、Cortex、AWO、tool-making。

# 3. OS / 系统社区是否把 Agent 当作 workload profile

## 3.1 已找到的直接或相邻工作

### AgentCgroup：最直接的 OS workload characterization

AgentCgroup 属于 arXiv `cs.OS`，明确把 sandboxed coding agent 与 serverless、
microservice、batch workload 对比。它报告：

- container/agent 初始化与工具执行合计占 E2E latency 的 55%–60%；
- 约 185 MB 稳态框架内存上叠加工具驱动 burst，peak/average 最高 15.4×；
- burst 常只有 1–2 秒，测试、package install、Python snippet 的资源形态不同；
- retry loop 会累积未释放内存，最坏达到 502 MB。

**测了什么 / 没测什么：**它证明“agent 是新的 OS workload”这一视角已经存在，并提出
tool-call-aligned cgroup/eBPF controller；但只采样 CPU/内存和工具阶段，全文不报告 syscall
mix、block/file I/O、page cache、socket/network、process-spawn fan-out 或逐路径读写集。

### AgentSight：系统边界可观测性

**Yusheng Zheng, Yanpeng Hu, Tong Yu, Andi Quinn. 2025.
[AgentSight: System-Level Observability for AI Agents Using
eBPF](https://arxiv.org/abs/2508.02736). PACMI 2025.**

**测了什么 / 没测什么：**用 eBPF 在 TLS/进程/内核边界关联 agent 高层 intent 与低层
effect，低于 3% overhead，并用案例检测 prompt injection、reasoning loop 和 multi-agent
bottleneck；但论文目标是 observability framework 和案例，不是对大规模真实 agent corpus
报告 syscall/I/O workload distribution。

### CPU-centric agentic execution

Raj 等人的 CPU-centric paper（第 2 节）测五类代表性 agent workload 在两种硬件上的
latency/throughput/energy，发现部分 workload 的 CPU 工具阶段可占绝大部分时间，并提出
CPU-GPU overlap/scheduling。

**测了什么 / 没测什么：**它是系统 component profile 的先例；但 profiling 粒度是
workload/component 和 CPU/GPU，不是系统调用、文件路径、I/O 请求或真实长期 coding-agent
工作负载。

### AIOS 与 Murakkab

AIOS 使用“agent OS/kernel/service”抽象管理 agent 资源；Murakkab 是 OSDI 2026 的
agentic workflow 云端 orchestration system。

**测了什么 / 没测什么：**两者证明 OS/系统社区已经认真研究 agent runtime 与资源调度，
但都不是把不受控真实 agent 的 syscall/I/O trace 当作 workload 来做 longitudinal
characterization。

## 3.2 明确的“未找到”

截至检索日，在 arXiv、DBLP、ACM、USENIX 和 Google Scholar 的上述关键词范围内，
**未找到**以下论文：

- 对真实、长期运行的 coding agent 报告 syscall 类别频率与序列，例如
  `openat/read/write/execve/clone/connect` 的分布和 phase transition；
- 报告逐文件/目录的读写量、重复读取、metadata lookup、page-cache locality、临时文件和
  workspace 热点；
- 报告 agent 工具调用与实际 process tree、subprocess fan-out、network bytes/endpoints、
  block I/O 或文件 mutation 的一一对应；
- 比较不同 agent/model/framework 在同一真实 repo 上的 OS workload signature；
- 把这些 OS-level 事实与精确的失败重试、缓存/预取/并行安全性和跨 session artifact
  persistence 联合起来。

这是“本次检索未发现先例”的限定性结论，不应写成不加范围的“全世界第一”。最接近的
AgentCgroup 已覆盖 CPU/内存和重试，AgentSight 已提供 eBPF 观测机制；新工作必须在测量
对象、规模和指标上明确超出二者。

# 4. 与本论文最近的 5 篇工作及逐一空白

本论文当前本地定位是：551 个 native root sessions、181,303 次工具 action、六个选定
repository，并能观察跨原生 session 的 durable workspace evolution。下面的比较只陈述
当前语料**能够支持的潜在位置**；只有在正文真正实现相应指标、报告方法和效应量后，才能
作为论文贡献。

| 最近工作 | 它测了什么 | 它没测什么 | 本论文相对空白 |
|---|---|---|---|
| [TraceLab, Zhu et al., 2026](https://arxiv.org/abs/2606.30560) | 真实日常 Claude Code/Codex 的 4,265 sessions、432,510 tool calls；工具分布/延迟、step 密度、context 与 KV cache | 原始 tool args/results 被删除；无 status/recovery、精确重复、artifact 依赖、OS trace、repo 内跨 session 演化 | 用保留语义的 native session 数据测 canonicalized invocation、同目标重复/距离、失败恢复、跨 session artifact persistence，并将其与工作区状态变化关联 |
| [Agentic AI Workload Characteristics, Yuan et al., 2026](https://arxiv.org/abs/2605.26297) | 五个 benchmark 上的工具类型、延迟、result length、failure rate、retry loop、read→write 阶段变化和 KV reuse | benchmark/统一 scaffold；无真实用户会话、跨 session repo state、精确依赖与 OS effect | 验证这些失败/阶段规律在真实长期开发中是否成立，并区分“有进展的重试”和“无效重复”，报告其持久成本 |
| [AgentCgroup, Zheng et al., 2026](https://arxiv.org/abs/2602.09345) | 144 个 task 的 CPU/内存 burst、工具时间、相同测试命令 retry group，并提出 tool-call-aligned resource control | 单 agent/benchmark；无 syscall/I/O/path trace、自然 session、artifact lineage | 将工具语义/失败/状态变化与真实 OS effect 对齐；若本论文不新增 kernel/resource trace，则只能以行为维度互补，不能声称 OS profiling 首例 |
| [Process-Centric Analysis, Liu et al., 2026](https://doi.org/10.1145/3798271) | 4,000 benchmark 轨迹的时序/语义图，定位-修改-验证、重复/回退、低效过程及在线干预 | 无自然使用、精确 latency/status/resource、artifact producer-consumer 和跨 session 状态 | 从抽象 action graph 下沉到 exact tool target/result/workspace mutation，并研究模式在同一 repo 的多个原生 session 中如何持续或改变 |
| [AgentTrails, Wu et al., 2026](https://arxiv.org/abs/2607.18816) | 从参数/结果恢复 artifact provenance，joined graph 对齐多条执行并显示重复和 detour | 4 页 prototype；10 条标注 trace/234 gold edges，两个 scenario；无规模化 longitudinal statistics、失败/OS cost 或优化评估 | 在 181k action 规模上验证 dependency extraction，量化跨 session lineage、冗余、可安全并行/缓存/增量重算比例；不能再把 provenance graph 本身作为首创 |

### 新颖性风险与推荐定位

不能使用的宽泛 claim：

- “first real-world coding-agent workload trace”——TraceLab 已覆盖；
- “first empirical study of agent tool distributions/sequences/retries”——多篇行为研究已覆盖；
- “first OS-level profile of coding agents”——AgentCgroup 已覆盖 CPU/内存；
- “first provenance/dependency graph for agent tools”——AgentTrails 已覆盖；
- “first tool speculation/parallelism/cache”——PASTE、AsyncFC、TVCACHE、Cortex 已覆盖。

更可防守的中心 claim 是：

> 现有工作分别测量真实 serving trace、benchmark 行为、OS 资源或 provenance prototype，
> 但尚未在长期真实 repo 中联合刻画精确工具调用语义、失败恢复、artifact/状态依赖和跨
> 原生 session 的持久影响，也没有用这种联合证据量化工具层优化的安全机会与上界。

如果论文要主张系统优化意义，至少应从 trace 中输出以下量化结果，而不仅是定性建议：

1. exact/canonicalized 重复率、reuse distance、同目标与同参数比例；
2. 失败调用后的下一步动作、恢复长度、恢复成功率和额外 latency/action cost；
3. read/write/execute 的 producer-consumer DAG、可交换/有冲突边和 critical path；
4. 只读/幂等/有副作用工具的经验比例及可安全 speculation 上界；
5. 结果 cache 在 exact、state-aware、semantic 三种策略下的 hit 上界和 invalidation 原因；
6. 跨 session artifact reuse、重复探索/测试和 workspace mutation 的持久性；
7. 若可取得系统 trace，按工具类别对齐 CPU、内存、syscall、I/O 与 subprocess 成本。

# 确认的 empirical 空白

以下结论经过本地文献与截至 2026-07-26 的网络检索交叉检查；“未找到”均按上述数据库、
关键词和公开论文范围理解。

1. **真实长期语料上的精确重复与恢复联合测量：未找到。**已有工作测总体工具分布、
   benchmark failure rate、test retry group 或抽象反复行为，但未找到对日常原生 session
   按 canonicalized `(tool, target, arguments, workspace state)` 同时报告重复率、reuse
   distance、失败原因、恢复序列、恢复结果和代价的研究。

2. **持久 repo 中的跨 session 工具行为：未找到。**TraceLab 研究 session/serving，
   benchmark 研究 isolated task，AgentTrails 比较多条 trace；未找到把同一 repo 的多个
   原生 session 串成 durable artifact/workspace evolution 并测重复探索、复用和技术债的
   empirical study。

3. **真实轨迹上的并行可行性和安全上界：未找到。**PASTE 和 AsyncFC 已实现 speculation/
   concurrency，但未找到从自然日常 trace 恢复读写/副作用依赖后，报告可安全并行比例、
   冲突率和 critical-path speedup upper bound 的研究。

4. **可变 coding workspace 的通用工具结果缓存：未找到。**TVCACHE 依靠完整历史前缀等价，
   Cortex 处理读侧语义知识；未找到支持文件、进程、依赖安装和测试等有状态工具，且用真实
   跨 session trace 评估 invalidation 正确性与收益的通用 cache。

5. **开放式 agent 工具图的增量计算：未找到。**AWO/meta-tools 和 production
   tool-making 编译重复流程，AgentTrails 恢复 provenance；未找到像 build system 一样
   维护工具读写集/依赖图、workspace 局部变化后只重算受影响节点，并在开放式 agent 上做
   empirical evaluation 的系统。

6. **真实 agent 的 syscall/I/O workload signature：未找到。**AgentCgroup 测 CPU/内存，
   AgentSight 提供 eBPF observability；未找到大规模报告 syscall mix、逐路径文件 I/O、
   process fan-out、network/block I/O 及其阶段/失败相关性的论文。

7. **语义行为、持久状态与系统成本的三方联合：未找到。**现有论文通常只覆盖其中一到两层：
   轨迹语义、LLM/tool serving、或 CPU/内存。未找到在同一真实 corpus 上把“agent 为什么
   调用—工具改变了什么—OS 付出多少—后续 session 是否复用/重做”完整关联的研究。

同样需要明确：下列角度**不是空白**——工具调用总体分布、工具 latency 长尾、read→write
阶段变化、重复/回退、工具失败率、测试重试、失败发生与恢复、CPU/内存 burst、工具投机/
并行执行、stateful tool cache、semantic knowledge cache、agent provenance graph。论文的
novelty 必须建立在上面七项更窄且可测的联合空白，而不是重复这些已有结论。
