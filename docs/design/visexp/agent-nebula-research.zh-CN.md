# Agent Nebula 研究计划：长期 Agent 的工作空间演化与行动轨迹

## 1. 研究对象

Agent Nebula 研究的不是“怎样把仓库画得更漂亮”，也不只研究 Coding Agent。软件开发、
auto research、论文写作和实验迭代都属于同一种长期 Agent 工作：Agent 跨多个 session
持续改变一个 workspace，最终形成代码、论文、实验结果、数据和文档等数字产物。

> 长期运行的 Agent 如何跨多个 session 持续改变一个 workspace，并最终形成代码、论文、
> 实验结果、数据和文档等数字产物？我们能否重建这些产物的形成过程，使后来者能够核对
> Agent 做了什么、如何做、在哪里失败和修正，并诊断 skill/harness 造成的低效？

这里的核心对象是 action-time workspace evolution：以 Agent action 的真实顺序为时间，
以具有生命周期的数字产物为实体，以 workspace 层级和相邻动作关系为空间约束，以
session、Tool action 和可选的系统文件观察为证据。Git repository 是一种常见 workspace，
Git commit 只作为可选里程碑，不定义时间轴，也不参与布局。

核心单位不是单次 session，因为一次长期工作会跨越许多上下文；不只是 Git repository，
因为研究过程还会形成仓库外或未提交的论文、数据和结果；也不是最终 patch，因为最终结果
会丢掉探索、失败、回退和验证过程。真正持续存在的研究对象是 workspace 及其中数字产物
的演化，Agent trajectory 是作用在这些产物上的时空路径。

### 1.1 核心用户场景

用户会给一个 Agent 设置简单目标和 idea，让它在一个 workspace 中自主迭代数小时或
2–3 天，之后才回来检查。用户希望快速理解 Agent 大致做了什么、改进了哪些产物以及
怎样完成迭代，例如：

- 是先测试还是先写代码，失败之后是否改变了做法；
- 主要修改了什么模块，注意力和热点怎样随时间移动；
- 在论文、代码、实验、数据和文档上分别投入了多少工作；
- 写代码的意图、尝试过的方法、失败原因、踩过的坑以及后来的反思是什么；
- skill 是否要求 Agent 记录大量几乎不再阅读的文档；
- harness 是否让 Agent 长时间迭代无意义的测试用例，而没有推进真正的实现或研究目标。

真实文件动作能够证明“发生了什么”；意图、失败原因和反思则必须来自 Agent session 中
可追溯的语义记录，不能从系统事件硬猜。语义解释是可附加的信息层，不改变底层 action
时间轴和 artifact 生命周期。

### 1.2 文件地图与 Agent 轨迹的分工

Agent Nebula 中的星点表示文件，但文件不只意味着源代码：它也可以是测试、配置、论文、
研究笔记、数据集、实验输入、日志、指标、图表、结果和临时产物。目录或其他 workspace
层级由稳定色系表达，不需要额外伪装成文件节点。

文件地图回答“什么产物发生了变化”，Agent trajectory 回答“Agent 如何让它发生变化”。
后者既包括 read/write/create/rename/delete 的先后次序，也包括与文件效应关联的搜索、
执行和验证动作。二者共同表现模块形成、热点迁移、反复返工、遗忘区域和结构漂移。

中心研究主张是：

> Long-horizon agents should be understood through the process by which they
> transform persistent workspaces, rather than only through final outputs or
> isolated session traces.

即：长期 Agent 的关键观测对象不是一次对话或最终结果，而是它跨 session 改造持久工作
空间、形成数字产物的完整过程。Coding 是第一批最容易严格评测的 workload，而不是系统
抽象的边界。

## 2. 新颖性边界

### 2.1 不能作为核心新意的主张

以下方向都有明确先例，不能单独作为论文贡献：

1. **操作级历史优于 commit 历史。** AZURITE、OperationReplayer、FeedBaG 等工作已经
   记录并重放人类开发者的细粒度 IDE 操作；“不用 commit、改用 event”本身并不新。
2. **可视化 Agent trajectory。** Agent Trajectory Explorer、AgentLens、SeaView、
   AgentDiagnose、TraceView 等已经提供轨迹浏览、时间轴、关系图、比较或诊断界面。
3. **保持动态图的 mental map。** 动态图可视化已有成熟的 temporal stability 研究；
   “相邻帧位置不要跳”是设计约束，不是天然的新算法贡献。
4. **做一张好看的仓库动画。** Gource、Githru 和软件城市等已经证明其传播价值，但视觉
   新奇性不能替代可测量的研究主张。

### 2.2 可辩护的研究空白

现有细粒度开发历史主要面向人类 IDE 操作；现有 Agent 轨迹工具主要以一次任务的
Thought–Action–Result、线性时间轴或抽象行为图为中心。Agent Nebula 聚焦两者之间尚未
充分解决、且不限于代码的交叉点：

- **长期与跨 session：** 观察一个 workspace 在多个 Agent、多个 session、数日运行中的连续
  演化，而不把每次 run 隔离成单独故事；
- **工作空间状态与行动轨迹合一：** 同一模型同时表达文件的 create/read/write/rename/delete
  生命周期，以及 Agent 注意力在目录和文件之间移动的顺序；
- **声明与文件效应可关联：** Agent 原生 Tool action 表达调用意图，系统文件观察在可用时
  表达真实效应；二者绑定到同一 action，而不是建立两套互不相干的时间线；
- **过程恢复而非结果展示：** 评价目标是用户能否准确回答“先测试还是先写、热点怎样迁移、
  在哪里反复、哪些产物低回读”，并快速返回原始证据核对；
- **harness 诊断：** 从可观察的动作序列研究文档负担、test-only churn、验证滞后、重复
  探索等候选低效是否与 skill/harness 设计相关，而不是只比较任务是否最终通过。

因此，建议的中心表述是：

> Agent Nebula is a workspace-centered visual instrument for reconstructing and
> diagnosing how long-running agents create and revise digital artifacts.

“星云”是这个模型的一种交互表示，不是全部贡献。

## 3. 论文主张层级

### 主张 C1：过程恢复

action-time、生命周期感知、workspace 中心的表示，相比原始 session 日志、普通 Tool 时间轴、
静态热点图和 commit 历史，能让用户更快、更准确地恢复长期 Agent 工作过程，并定位支持
答案的原始证据。

### 主张 C2：时空布局

一个联合约束目录层级、动作相邻性、长期重要性和 temporal stability 的动态布局，能在
“看清当前结构”和“保留跨帧空间记忆”之间取得可测量的平衡；Agent 的连续路径可读性
高于固定最终布局或逐帧独立布局。

### 主张 C3：可观察的 harness 诊断

不依赖生成式语义摘要，仅从有证据的文件动作和 Tool 顺序计算的指标，能够定位一部分
人工确认的低效区间，例如文档低回读、测试空转、验证滞后、删除后重建和重复探索。

### 主张 C4：跨 Agent 与跨任务泛化

上述收益不是某一个 Agent、仓库规模、语言或任务类型造成的。结论需要按 repo、task、
Agent 和 harness 分组验证，不能随机打散 event 后做有泄漏的评估。

## 4. 研究问题

- **RQ1（理解）：** 不同表示怎样影响长期 Agent 过程问题的回答正确率、完成时间、证据
  定位时间和信心校准？
- **RQ2（布局）：** hierarchy、sequence adjacency 与 temporal stability 分别怎样影响
  文件追踪、目录纯度、节点重叠、跨帧位移和真实结构变化的可见性？
- **RQ3（诊断）：** 哪些纯动作指标能够识别人工确认的低效区间，在哪些 workload 上会
  产生误报？
- **RQ4（泛化）：** 结果在不同 Agent、harness、仓库规模、任务类型和运行时长上是否
  稳定？

## 5. 表示与算法作为可检验模型

设第 `i` 个 Agent action 为 `a_i`，它在时间 `t_i` 对零个或多个文件产生带证据的动作。
可视状态 `S_i` 由 `S_{i-1}` 和 `a_i` 更新；不存在以 commit 为单位的隐藏状态跳跃。

每个可见文件 `f` 具有：

- 生命周期状态 `L_i(f) ∈ {absent, visible, removed}`；
- 短期注意力 `A_i(f)`，由最近的 read/write/create/rename/delete 及其证据强度更新；
- 长期重要性 `I_i(f)`，由累计动作、重访、session 新颖性和衰减更新；
- 位置 `x_i(f) ∈ R²`，由目录层级、文件斥力、碰撞、相邻动作和时间稳定性共同决定。

布局可写成一个随 action 更新的能量目标：

```text
E_i = λ_h E_hierarchy
    + λ_s E_sequence
    + λ_r E_repulsion
    + λ_c E_collision
    + λ_t E_temporal
    + λ_a E_attention
```

其中 `E_temporal` 惩罚没有结构证据支持的跨帧位移，但注意力上升、新建、重命名和目录
活动会降低局部稳定约束，使真实变化仍可见。研究中不把某组权重写成常数真理，而是通过
消融和任务表现寻找 Pareto 区域。

Agent 的“轨迹”不是永久连线。每个 action 的目标位置是当次文件集合的加权质心；连续
action 构成瞬时路径，视觉上只保留短尾迹或移动光环。用于分析时则保留完整的目录转移
矩阵与文件相邻动作图，使“频繁来回”“跨模块跳转”“局部深挖”可以量化。

## 6. 实验设计

### E1：过程理解对照实验

从同一份证据生成四种条件，避免数据量不同造成偏差：

1. 原始 session/Tool 日志；
2. 可缩放的线性 Tool 时间轴；
3. 静态文件热点图或最终 treemap；
4. Agent Nebula 动态工作空间轨迹。

任务不问审美偏好，而问有客观答案的问题：主要修改模块或产物类别、首次测试与首次实现
的顺序、论文/代码/实验投入、热点迁移、重复探索、删除后重建、文档回读、测试空转，以及
支持判断的 action 证据。
指标包括正确率、完成时间、证据定位时间、漏报/误报、信心校准和 NASA-TLX 等主观负荷。

### E2：布局消融与压力测试

在同一轨迹上比较：

- 无 temporal stability；
- 固定最终布局；
- 无目录层级力；
- 无相邻动作力；
- 完整模型。

客观指标包括节点身份追踪率、目录混杂度、节点重叠、归一化位移、轨迹折返可辨识度和
对真实 create/rename/delete 的检测率。仓库规模和 action 数应分层，不用小仓库结论替代
大仓库压力结果。

### E3：行为与 harness 诊断

先由多名标注者仅根据原始证据标记低效区间和类型，再冻结标签定义。候选指标至少包括：

- artifact action share 与 active-duration share；
- documentation readback；
- test-only churn actions/loops；
- unverified edit span；
- recovery cost；
- no-file-action share；
- 目录转移熵、短期折返率和重复访问但无写入的探索段。

评估按 repo/task/Agent 分组交叉验证，报告 precision、recall、AUROC/PR-AUC 与误报案例。
如果指标只能区分任务类型，不能定位低效过程，则 C3 不成立。

### E4：跨来源证据消融

比较仅使用 Agent 原生 Tool action，与加入已绑定系统文件观察后的结果。该实验回答系统级
证据究竟修正了多少漏报、路径误判和“命令声称访问但没有文件效应”的情况。系统观察是
同一 action 的附加 evidence，不引入第二条产品时间线。

## 7. 数据集与防泄漏原则

数据集应包含不同 Agent、harness、workspace 类型、语言、规模、任务类型和运行时长，并
保留失败 run，不能只收集成功案例。软件仓库可以作为第一阶段受控 workload；auto
research、论文与实验 workspace 用于检验表示是否真的超越 coding。最小可发表单元不是
event 数，而是具有完整任务上下文、可复核证据和结果判定的 run/session group。

训练或调参、阈值选择、诊断评估必须按 workspace 或 task group 划分。相同 issue、fork、
模板 workspace 或同一长运行的切片不能跨训练与测试集合。发布数据时可用路径哈希或受控
重放，但论文内部的 ground truth 必须能回到原始 action 核验。

## 8. 最近工作与直接威胁

- **细粒度开发历史：** AZURITE、OperationReplayer、FeedBaG 和 IDE 交互可视化证明
  operation-level history 早已存在；本工作的差异必须放在 autonomous Agent、跨 session、
  仓库状态与执行证据联合建模上。
- **Agent 轨迹工具：** Agent Trajectory Explorer、AgentLens、SeaView、AgentDiagnose、
  ReTrace 与 TraceView 已覆盖通用轨迹浏览、分层摘要、时间轴、比较和关系图。TraceView
  尤其接近，因此实验必须比较“轨迹图”类基线，而不能只比较 raw log。
- **Coding Agent 行为研究：** SWE-Agent trajectory 分析、traceability taxonomy、
  SWE-Explore 和 trajectory fingerprinting 表明探索路径与行为模式已经成为评测对象。
  Agent Nebula 应提供新的可操作测量，而不是重复描述“不同 Agent 行为不同”。
- **动态图：** temporal stability 与 mental-map preservation 已有完整研究脉络；新意需要
  来自面向文件生命周期和 Agent 路径的联合目标及其任务实证，而非直接复用术语。

## 9. 投稿路线

扩大到 workspace 后，会议选择应由最终证据最强的贡献决定，而不是预先把项目限定为
软件工程工具：

1. **CHI：首选完整故事。** 如果核心是人如何理解、接管和监督数日运行的 Agent，需要
   formative study、真实长期任务、对照界面和严格用户实验。CHI 能容纳 coding、auto
   research、论文与实验等多种 workspace，也是“从最终结果转向过程理解”最自然的社区。
2. **IEEE VIS：首选可视分析故事。** 如果核心产出是新的动态 workspace 表示、时空布局、
   mental-map 权衡和分析任务模型，应以表示/交互、analytics/decisions 或 empirical VIS
   的标准评价，而不把论文写成 Agent 产品介绍。
3. **IUI：近期且高度匹配的 AI×HCI 路线。** 如果贡献同时包含可计算的行为指标和供人
   检查 Agent 的智能界面，IUI 要求的 computational 与 human-centric 两面正好匹配；
   仍需用户研究或计算实验支撑主张。
4. **MSR：行为数据与测量路线。** 如果主贡献变成跨 Agent、harness 和 workspace 的长期
   trajectory 数据集、过程指标与实证发现，MSR 比单纯可视化会议更合适。可视化在这条
   路线上是分析仪器，不是主要新意。
5. **ICSE/FSE/ASE：软件工程子集路线。** 如果实验主要落在代码仓库，贡献集中于开发过程
   恢复、软件理解或自动化开发诊断，可以投稿；但需要明确把 auto research 作为泛化场景，
   不能一边声称通用 workspace、一边只评测 coding。
6. **UIST：有条件候选。** 只有在交互技术本身足够新、可复用且经过强交互实验时才优先；
   单纯一张动态星云或一个回放页面不够。

当前建议以 **CHI 作为完整研究故事的第一目标，IEEE VIS 作为算法与可视分析强时的并列
目标，IUI 作为更聚焦且近期的落点**。MSR 可承接独立的数据/测量论文。若未来把 AgentSight
的跨层系统捕获、声明—效应差异、低开销长期采集和生产规模做成核心，才适合讨论系统
会议；仅有可视化不足以支撑 OSDI/SOSP 式系统主张。

## 10. Go/No-Go 门槛

在扩大实现之前先完成三个 pilot：

1. **可回答性 pilot：** 盲测参与者能否从现有图中正确回答至少一组过程问题，并比 Tool
   时间轴更快定位证据；
2. **稳定性 pilot：** 大仓库与长历史中，完整布局相对消融版是否减少无意义跳动，同时
   不隐藏真实重命名、创建和热点迁移；
3. **诊断 pilot：** 预注册的动作指标能否在未见过的 run 上命中人工确认的低效区间。

若只观察到“动画更吸引人”，但正确率、证据定位或诊断能力没有提高，应将 Agent Nebula
定位为产品展示功能，而不是继续包装成研究贡献。

## 参考入口

- Yoon and Myers. *Supporting Selective Undo in a Code Editor with a History of
  Fine-grained Changes* / AZURITE visualization.
  <https://research.yyoon.net/papers/vlhcc13-yyoon-AzuriteViz.pdf>
- Hattori et al. *OperationReplayer: A Tool for Chronological Replay of Operations
  in Software Development*. <https://www.jstage.jst.go.jp/article/jssst/28/4/28_4_4_371/_article/-char/en>
- Wang et al. *AgentLens: Visual Analysis for Agent Behaviors in LLM-based
  Autonomous Systems*. <https://arxiv.org/abs/2402.08995>
- Gao et al. *SeaView: Interactive Visualization for Multi-Agent Coding Systems*.
  <https://arxiv.org/abs/2504.08696>
- Sajadi et al. *TraceView: Interactive Visualization of Agentic Program Repair
  Trajectories*. <https://arxiv.org/abs/2606.22110>
- Zhang et al. *SWE-Explore: Benchmarking How Coding Agents Explore Repositories*.
  <https://arxiv.org/abs/2606.07297>
- Oderinwale. *Agent trajectories as programs: fingerprinting and programming
  coding-agent behavior*. <https://arxiv.org/abs/2606.16988>
- Archambault, Purchase, and Pinaud. *Animation, Small Multiples, and the Effect
  of Mental Map Preservation in Dynamic Graphs*.
  <https://inria.hal.science/inria-00472423v1>
- Beck et al. *The State of the Art in Visualizing Dynamic Graphs*.
  <https://www.visus.uni-stuttgart.de/documentcenter/forschung/visualisierung_und_visual_analytics/eurovis14-star.pdf>
