# AgentSight + AgentCgroup 学术定位讨论记录

记录一次关于 "如何把 AgentSight 与 AgentCgroup 讲成一个比'两个 eBPF tool'更大的故事" 的讨论。

> 这份文档是 thinking 过程的快照，不是结论。多个 framing 候选最后都被否掉了，保留它们是为了记下"为什么不行"，避免下次再绕回来。

---

## 1. 起点：当前的牌与短板

### 真正的强项
- **技术栈深度**：`memcg_bpf_ops` 在 upstream review 阶段已用上、`sched_ext` 集成、cgroup v2 分层 hierarchy。kernel-level chops 是大部分 ML/agent 研究者写不出的。
- **两个角度互补**：observation (AgentSight) + enforcement (AgentCgroup) 是同一论点的两面。
- **AgentCgroup characterization 的硬数字**：OS-level 占端到端延迟 56–74%；memory（不是 CPU）是瓶颈；峰值与均值比 15.4×。
- **niche 没拥挤**：serving-side（Cortex/Pie/Helium）已经是 Berkeley/Columbia/CMU 红海，agent OS primitive 这条线没人正面占。

### 真正的短板
- 机构权重：UCSC 不是 top-3 systems lab，OSDI/SOSP 主会的 PC bar 会更高。
- 两篇都还在 arxiv / workshop，没落顶会。
- "Yet another eBPF tool" 是真实的 framing 风险。
- abstraction story 比 implementation story 弱——技术走在叙事前面。

---

## 2. 学术界的现状（agent as a system）

简短判断：**领域处于 pre-paradigmatic 阶段**，结构上像 1975 年的分布式系统——还没有自己的 Lamport 1978 那种定义性 paper。

| 子方向 | 状态 | 代表工作 |
|---|---|---|
| Agent serving / inference systems | 已成熟，OSDI/SOSP 稳定出 paper | Cortex (SOSP'25), Pie (SOSP'25), Helium |
| AgentOps / failure / observability | 快速成形，但没进 systems 顶会 | MAST (NeurIPS'25 D&B Spotlight), TRAIL, AgentTrace, AgentSight |
| Agent OS / Agent Kernel | vision 很多，实现普遍偏弱 | AIOS 及一堆 follow-up |
| 真正像 systems 的早期信号 | 极少 | Conseca (HotOS'25), DAPLab fork-like primitives, Apple GAAT |

### 几个判断
1. serving-side 跑得快，是因为它能直接借数据库/分布式计算的成熟范式；"agent as a system" 缺这种现成对应物。
2. **工业界在好几个方向上跑在学术界前面**——MCP gateway 创业公司、E2B/Modal/Daytona、Temporal、Datadog/Langfuse 都已生产化；学术界还在写 vision paper。
3. 学术真正能领先工业的位置在 **基础抽象 + 形式化**——agent trajectory 形式语义、multi-agent termination 算法、agent capability calculus、agent fault model、agent observability completeness/soundness。
4. 发表生态错位：agent system 工作散落在 OSDI/HotOS/NeurIPS-D&B/AAAI/CCS/CHI/COLM——没有一个会议是它的"家"。

---

## 3. 战略选择：路 A vs 路 B

| | 路 A："eBPF for agent OS" 那个 group | 路 B："agent OS abstraction" 那个 group |
|---|---|---|
| 身份 | 技术 deep dive，每个新 kernel feature 出来就套到 agent | 定义新概念，被引用的是 framework 而非 implementation |
| 主要发表 | EuroSys / ATC / ASPLOS | HotOS + OSDI/SOSP |
| 五年累计引用估计 | 40–80 | 200+，且被新人当 baseline |
| 被工业吃的风险 | 高（kernel feature 5 年后是 commodity） | 低（abstraction 护城河随时间增加） |

**讨论中倾向于路 B**，理由：现有工作其实撑得起更大论点，浪费在路 A 上是低估自己。

但路 B 的硬要求：**必须把现有工作 reframe 成更大的论点**——这就是后面整个讨论的核心。

---

## 4. Agent infra 的六条 principle

OSDI 意义上的 principle 标准：跨多个具体系统都成立 / 能推出非平凡设计后果 / 能解释失败。

1. **Non-determinism is a first-class system property** — agent 是历史上第一类把"同一输入产生不同输出"作为正常运行状态的生产基础设施。
2. **The trust boundary is between intent and effect, not between processes** — agent 进程内部就有两个 trust domain（LLM untrusted + harness trusted），传统 process-based isolation 模型断裂。
3. **Observability must come from outside the system being observed** — 被观测实体能生成任意文本（包括"我没干那个"），自报 trace 不可信。Saltzer-Schroeder 1975 的 reference monitor tamperproof 原则在 agent 时代复活。
4. **The unit of correctness is the trajectory, not the call** — 单步对错没意义，trajectory-level 的 intent satisfaction 才是 well-defined correctness。
5. **State must be reconstructable, not just persistent** — debug/审计/回滚/replay/fork-and-explore 是常态而非异常路径。
6. **Coordination cost dominates compute cost in multi-agent systems** — multi-agent 失败率 41–87%，前三大失败都是 coordination 问题。

> **赌注**：Principle 4 + 5 合流（trajectory as unit of correctness + state as reconstructable event log）会先催生出"教科书必讲"的系统抽象。

---

## 5. Trajectory 抽象（principle 4 + 5 的具体化）

### 定义
一个 trajectory 是：一个 initial intent 在一个 environment 里展开成的 **因果闭包**——所有为了让这个 intent 成立或失败而发生的事件，连同它们的因果关系。

### 与已有抽象的关键区别
- **vs. workflow (Temporal/Cadence)**：workflow 是预定义 DAG，trajectory 是 emergent 的——拓扑在运行期才出现。
- **vs. session (Anthropic Managed Agents)**：session 是 trajectory 的存储侧实现（append-only event log），但没有把它抬成计算抽象。

### 推论（如果 trajectory 是计算单位）
- Scheduling、checkpointing、retry/recovery、resource accounting、SLO、debugging、testing 全部需要重做。
- 这是新的 OS-level abstraction，是 OSDI A 类候选。

---

## 6. 五个候选项目（按 OSDI 级别诚实重评）

| # | 项目 | 真实档次 |
|---|---|---|
| 1 | Capability Mediator | B 类，更适合 USENIX Security / CCS（不是 OSDI） |
| 2 | Trajectory Testing Framework | PLDI/POPL（不是 OSDI），除非加运行时 streaming evaluation 维度 |
| 3 | Deterministic Replay Boundary | **OSDI 边缘可投**——五个里最像 OSDI 的 |
| 4 | Open Trajectory Format | 不是 paper，是 RFC/standard |
| 5 | Termination Detection | PODC/short paper（不是 OSDI） |

### 真正 OSDI 级的方向（前面 5 个外）
- **A 类**：Trajectory as first-class scheduling unit
- **B 类**：Tamperproof trace + replay 的根本解决（AgentSight 的进化形态：reference monitor for AI agents）
- **B 类**：Capability-based OS for agents（kernel-level，不是 user-space proxy）
- **C 类**：Production agent measurement at scale（个人做不了，需要大厂规模数据）

---

## 7. Framing 的多次失败尝试

这是这次讨论最重要的部分——记录所有 **没立住的 framing**，避免下次再绕回来。

### 失败候选 A："Tool-call as a new OS primitive"
**为什么不行**：本质上还是描述"你做了什么"（在 tool call 边界做 cgroup 控制），换了个抽象包装。reviewer 会问"为什么粒度比正确性、安全性、可证性更值得发顶会"——答不上来。

### 失败候选 B："Semantic-system bridge"
**为什么不行**：从工作往上找伞（post-hoc rationalization），不是从问题往下推解法。"决策和执行劈开"是修辞不是论证；编译器/JIT/解释器都跨语义层，"劈开"本身不是新东西。

### 失败候选 C："Attribution"
**论点**：OS 的所有 access control / audit / resource accounting 本质都是 attribution；agent 引入 multi-source instructions + LLM attention mixing，traditional IFC/taint tracking 在 LLM 内部失效；attribution 必须迁移到 OS 层。

**为什么不行**：用户读完反应是"读起来非常混乱，非常模糊"——一段话堆太多大词（归因、语义错位、结构性破坏、latent function），每个词单独看像有意思，连起来没人能跟上。

### 失败候选 D：Cursor 故事 / "OS 看到的 ≠ 真正发生的"
**为什么不行**：用户一拳打回——**"这不就是 AgentSight 已经在说的 mismatch 吗？"** 是的。前面所有尝试（attribution / bridge / tool-call / Cursor 故事）都在 AgentSight 已有论点的同一个抽象层上换说法。

### 关键洞察
> 已经在用的论点（semantic gap），不够撑起一个比"两个 eBPF tool"更大的故事。这不是 framing 问题。framing 已经做完了。**问题是这个 framing 本身不够大**。

semantic gap 是 **describable** 的现象（"有个东西看不见"），不是 **forcing** 的论点。OSDI 接受 forcing 论点（"无论怎么努力，下面这件事必然发生"），不接受 describable 论点。

---

## 8. 最后一个尚未否定的方向：Fault-recovery model conflict

从 AgentCgroup 的具体数字（memory 是瓶颈、15.4× spike、不可序列化的 GPU memory state）反推得到的论点：

> Unix 的容错哲学是 crash-and-restart：进程死了重启、容器死了重建。这个哲学之所以成立，是因为传统软件的状态可以从外部重建（database 在 disk、session 在 cookie、business logic 在 code）。OS 杀进程是 cheap operation，因为重启代价有界、可预测。
>
> agent 不满足这个前提。agent 的工作状态不在 disk 上，在 LLM 的 context window 里——是几十轮对话累积出来的、隐性的、无法序列化的推理上下文。OS 一旦因为 OOM 杀掉这个进程，状态不是延迟恢复，是彻底消失。重启的 agent 不是 "resume from checkpoint"，是 "start a different task"。
>
> 这意味着 OS 现有的所有资源管理决策——OOM killer、cgroup memory limits、container restart policy、preemption——在 agent workload 上的语义全部错了。它们不是把"故障"恢复了，是把"工作"销毁了。这个错位无法在应用层修复：当 OS 决定杀你的时候，应用层已经没机会保存它需要保存的东西，因为它需要保存的东西活在不可序列化的 GPU memory region 里。

### 为什么这个方向有可能不是又一次绕圈
- 不是 "OS 看不见 agent"（gap），是 **"OS 的标准操作会主动伤害 agent"（conflict）**。
- gap 可以容忍，conflict 不能——这是 forcing 论点。
- 直接连到 AgentCgroup 的核心数据。
- 解释了为什么 graceful degradation（throttle/freeze）比 kill 重要。
- 对接经典 systems 工作（fault tolerance、checkpoint/restart、process migration）。
- 不是 LLM 特有——任何拥有不可序列化累积状态的 workload 都 share 这个问题。

### 仍未确认的事
- 这个论点是否真的覆盖工作的全部本质（也是从工作往上反推的，可能仍是 post-hoc 包装）。
- AgentSight 装得进这个 framing 吗？还是只覆盖 AgentCgroup 一半？
- 是不是又一个换皮的 mismatch？

**讨论停在这里**——再往前必须由本人确认方向，不是再写一段就能解决的事。

---

## 9. 行动 / 不行动清单（如果走路 B）

### 应该做
- 重写 AgentCgroup paper，把核心论点抬高（具体抬到哪个论点待定）。重投 EuroSys 2026 / ASPLOS 2027。
- 写 HotOS 2027 position paper 立 agenda——HotOS 是被低估的入口，单位努力的 visibility 回报最高。
- 开放 AgentResourceCorpus（144 个 SWE-rebench task 的 OS-level trace），做 systems 版本的 MAST-Data。
- 升级 AgentSight 走 enforce 方向（从 monitor 到 reference monitor + enforcer）。
- 利用 sched_ext / memcg_bpf_ops upstream 时机建立 kernel community presence。
- 主动和 Columbia DAPLab、Stanford systems-for-ML 这些组建立 cross-citation。

### 不应该做
- 又一个 MCP gateway / agent firewall / agent dashboard / agent eval harness / agent framework。
- 通用 sandbox runtime（E2B/Modal/Daytona 战场）。
- 追 OpenTelemetry semantic convention 节奏（SIG 太慢，会被大厂吞）。
- 让 paper 标题或 abstract 出现 eBPF——eBPF 是 mechanism 不是 contribution，应该是 implementation 段的注脚。

---

## 10. 留给未来的问题

读完第 8 节那段 fault-recovery model conflict，本人的直觉反应是：

- [ ] "对，我做的就是这个，但还差点什么"
- [ ] "这覆盖了 AgentCgroup 一半，但 AgentSight 装不进来"
- [ ] "这又是一个换皮的 mismatch"
- [ ] 别的什么 ____________

这个反应——不是分析、不是想法，是**直觉反应**——决定下一步往哪推。

---

## 11. 第二个 agent 的独立分析（不带前面 framing 包袱）

把整个材料（含本文档第 1–10 节 + AgentSight paper 文本）交给一个独立 agent 重做一遍。它的判断与第 1–10 节有几个**关键分歧**。

### 11.1 对 AgentSight paper 的 PC 视角评估
**判定：borderline reject，倾向 reject。** 不会 desk reject 但拿不到 champion。

致命弱项：
- **contribution 是 plumbing**：sslsniff (bcc 已有十年) + 进程 tracepoint + LLM 当 analyzer，三个组件都不新，串法（100–500ms 时间窗 + 字符串 argument matching）不是 non-trivial。
- **causal correlation 是 heuristic，没有 soundness/completeness 保证**——argument matching 在 base64/编码/缩写下立刻失效，没有 false positive/negative 分析。
- **case study 都是单 anecdote**，没有 ground truth dataset，没和 baseline (Falco + Langfuse 拼接) 对比。
- **§3.2 用 secondary LLM 做 "AI to watch AI"**：reviewer 会直接问"detection 是 non-deterministic 的，怎么 reproduce？"

### 11.2 对第 8 节 fault-recovery framing 的判定
**换皮 mismatch，不是 forcing 论点。**

一句话反驳就够：*"这就是 checkpointing 问题。CRIU、DMTCP、Singularity 解过了。GPU memory 不可序列化是 ML 系统的老问题（不是 agent 特有），Cortex/Pie 的 KV-cache management 已经在做了。"*

更狠的一击：第 8 节自己最后一句 "any workload with non-serializable accumulated state share this problem" —— 这句话**亲手承认**了它不是 agent-specific。一个非 agent-specific 的论点，没法解释为什么 AgentSight（一个 agent observability 工具）是它的必要 instance。**AgentSight 装不进去**——本人在第 10 节备选 □ 的第二项已经预感到了。

### 11.3 它的真实建议：选 (B)，不是 (A)

**核心诊断**（与第 1–10 节最大的认知差异）：

> 两篇现状的本质问题不是"framing 不够大"，而是 **两篇都在描述现象，没有一篇在 close loop**。

第 1–10 节假设 framing 是病；它说现象描述是病，framing 是症状。这是一个 hard reframe。

**缺的第三件事**：一个有 formal guarantee 的 trajectory-level resource controller。

- **输入**：一组并发运行的 agent trajectory（每个 = 一连串 tool call + 累积的 KV cache + memory footprint）
- **输出**：admission / throttle / freeze / migrate / kill 决策器
- **Guarantee**：在 well-defined cost model 下（如 sunk token cost、missed deadline 数），证明它比"OS 直接 kill"和"应用层 retry"严格更优，给出 worst-case bound

### 11.4 这个 reframe 的关键效果

- **AgentSight 降级为 sensor**——不再独立撑顶会，是 controller 的 input layer。**反而消解了所有当前对它的攻击**：heuristic correlation 不需要 sound，因为 controller 的 guarantee 不依赖它 sound。
- **AgentCgroup 降级为 actuator**——cgroup/sched_ext 是 mechanism 不是 contribution；contribution 是 controller 的 policy + 可证 property。
- **forcing 论点终于出现**：*"OS 的资源决策必须基于 trajectory-level 的 cost-of-loss，而不是 process-level 的 RSS；否则任何 admission/eviction 决策都是次优的，且这个次优有 lower bound。"* —— **这个论点能写成定理**。
- **15.4× spike 不再是 motivation 数字，而是定理的 corollary**——证明 spike 是缺乏 trajectory-level admission 的必然后果，本身就是 paper 的核心 contribution。

### 11.5 12–18 个月路径

| 阶段 | 月份 | 产出 |
|---|---|---|
| 定义 trajectory cost model | M0–M3 | sunk cost 公式（token + KV + 已执行 side effect）；progress signal 抽取（用 AgentSight）；开放 dataset：144 个 SWE-rebench task 的 trajectory cost trace |
| 实现 controller | M3–M9 | admission control + graceful preemption (freeze+swap not kill) + priority inheritance；AgentCgroup 是 enforcement layer |
| 证明 worst-case bound | M9–M14 | 大概率需要简化 cost model 到 competitive analysis 工具能处理的形式——**这是论文区别于"又一个 scheduler"的护城河** |
| 真实负载测量 | M14–M18 | Claude Code / Cursor / Devin-like 上跑；关键 metric：**sunk cost recovered per OOM event** + **P99 trajectory completion under memory pressure** —— 现有 systems literature 里没人报这两个，因为没人意识到要报 |

OSDI/SOSP 投稿时 AgentSight + AgentCgroup 在 related work 一笔带过（"in our prior work..."），主菜是 controller + bound + measurement。

### 11.6 它点出三个会让 (B) 路径塌掉的关键变量

1. **trajectory cost model 是否存在 well-defined formulation**——如果 token / KV / side-effect cost 没法 unify 到一个可优化的标量，整条路塌掉，回退到 (C)。
2. **15.4× spike 的真实成因**——KV cache 突发分配（admission 救得了）vs tool call 子进程峰值（不可预测，admission 救不了）。决定 controller policy 可不可行。
3. **本人对"AgentSight 不再独立投顶会"的接受度**——情感成本。如果 AgentSight 已经是 flagship，这条路情感上走不通。
4. （我加的第四个）**sched_ext 在 OSDI'27 时间窗内的 upstream 状态**——决定工程难度。

### 11.7 与第 1–10 节的对照

| | 第 1–10 节倾向 | 第 11 节判断 |
|---|---|---|
| 病灶 | framing 不够大 | 没 close loop |
| 解药 | 找更大的 framing 伞 | 做第三件 controller 工作 |
| AgentSight 角色 | 升级 framing 让它成为 flagship | 降级为 sensor，放弃 flagship 地位 |
| 第 8 节 fault-recovery | 未确认，可能是 forcing 候选 | 明确否决，是换皮 mismatch |
| OSDI/SOSP 可行性 | 取决于 framing 升级是否成功 | 取决于第三件工作能否做出来 + cost model 是否存在 |

**两个判断不是互斥的**——可能两个都对（病灶兼而有之），也可能某一方完全错。需要本人做出**情感和战略上的双重判断**：

- 是否接受 AgentSight 降级
- 是否相信 trajectory cost model 在 6 个月内可以证明存在 well-defined formulation
