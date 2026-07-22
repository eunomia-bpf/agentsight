# Agent Nebula 研究计划：长期 Agent 的工作空间轨迹与自动监督

> **2026-07-21 当前科学合同。** 本研究不再使用人工 pathology 标注，也不让另一个 Agent
> 充当 gold。核心实验在真实 benchmark 的 session 边界冻结 workspace，为不同监督条件
> 创建完全相同的分叉，真正执行后续 Agent session，再由官方可执行 grader 判断干预是否
> 改善结果。下文的表示、算法、用户场景和长期目标保持不变；实验与主张以这个闭环结果为准。

## 1. 研究对象

Agent Nebula 研究的不是“怎样把仓库画得更漂亮”，也不只研究 Coding Agent。软件开发、
auto research、论文写作和实验迭代都属于同一种长期 Agent 工作：Agent 跨多个 session
持续改变一个 workspace，最终形成代码、论文、实验结果、数据和文档等数字产物。

> 长期运行的 Agent 如何跨多个 session 持续改变一个 workspace，并最终形成代码、论文、
> 实验结果、数据和文档等数字产物？我们能否重建这些产物的形成过程，使自动诊断器或
> 监督 Agent 能够核对执行证据，判断工作是否取得进展、陷入空转或偏离目标，并诊断
> skill/harness 造成的低效？

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

本研究不把“人直接看图回答问题”作为主要机制或实验对象。人的需求由自动诊断器或另一个
监督 Agent 承接：它读取 workspace trajectory，输出进展判断、异常区间、可能原因、是否
需要干预以及对应的原始 action 证据。人仍然是最终受益者，但不需要亲自浏览完整日志或
承担论文中的主要诊断任务。

真实文件动作能够证明“发生了什么”；意图、失败原因和反思则必须来自 Agent session 中
可追溯的语义记录，不能从系统事件硬猜。语义解释是可附加的信息层，不改变底层 action
时间轴和 artifact 生命周期。

### 1.2 文件地图、轨迹与诊断工具的分工

Agent Nebula 中的星点表示文件，但文件不只意味着源代码：它也可以是测试、配置、论文、
研究笔记、数据集、实验输入、日志、指标、图表、结果和临时产物。目录或其他 workspace
层级由稳定色系表达，不需要额外伪装成文件节点。

文件地图回答“什么产物发生了变化”，Agent trajectory 回答“Agent 如何让它发生变化”。
后者既包括 read/write/create/rename/delete 的先后次序，也包括与文件效应关联的搜索、
执行和验证动作。二者共同表现模块形成、热点迁移、反复返工、遗忘区域和结构漂移。

自动诊断器不需要从动画像素反推这些结构。实现上应直接从现有 agent-session 抽象计算
可查询的轨迹投影，使监督 Agent 能够询问活跃产物、目录转移、验证滞后、返工区间、失败
恢复和证据位置。HTML/GIF/MP4 是同一轨迹的可检查与传播视图，不是诊断 Agent 的输入
协议，也不要求额外建立一套重复的事件 IR。

中心研究主张是：

> Long-horizon agents should be understood through the process by which they
> transform persistent workspaces, rather than only through final outputs or
> isolated session traces.

即：长期 Agent 的关键观测对象不是一次对话或最终结果，而是它跨 session 改造持久工作
空间、形成数字产物的完整过程。Coding 是第一批最容易严格评测的 workload，而不是系统
抽象的边界。

面向当前研究范围，更具体的贡献定位是：

> We develop process-level scalable oversight for long-horizon agents by
> reconstructing workspace-centered action trajectories that automatic
> supervisors can query before intervening in a real continuation, whose effect
> is measured by an executable task outcome.

核心研究问题是：在 supervisor 与后续 worker 的预算固定时，workspace-centered action
trajectory 能否比完整、等预算的 Raw Retrieval 更好地支持一次真实干预，使后续 session
获得更高的官方任务分数，同时不增加伤害？“空转、偏航、验证缺失”仍是 supervisor 可以
推理的过程现象，但不再要求人工先把它们标成 gold。

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
- **过程恢复而非结果展示：** 评价目标是自动诊断器或监督 Agent 能否准确判断“先测试还是
  先写、热点怎样迁移、在哪里反复、哪些产物低回读”，并返回可核验的原始证据；
- **harness 诊断：** 从可观察的动作序列研究文档负担、test-only churn、验证滞后、重复
  探索等候选低效是否与 skill/harness 设计相关，而不是只比较任务是否最终通过。

因此，建议的中心表述是：

> Agent Nebula is a workspace-centered process-observability and oversight
> instrument for diagnosing how long-running agents create and revise digital
> artifacts across sessions.

“星云”是这个模型的一种交互表示，不是全部贡献。

## 3. 论文主张层级

### 主张 C1：可查询的过程恢复

action-time、生命周期感知、workspace 中心的表示，相比原始 session 日志、普通 Tool 时间轴、
session summary 和最终产物，能够保留诊断长期 Agent 所需的跨 session 顺序、产物生命周期、
空间转移与原始证据，并允许诊断器按区间和产物查询。

### 主张 C2：过程结构提高真实干预效用

在 supervisor、后续 worker、提示和预算相同的条件下，为监督 Agent 提供可查询的
workspace trajectory，相比完整、同源、等预算的 Full Raw Retrieval，能够生成更有用的
干预；从同一 workspace checkpoint 执行后，官方可执行 grader 给出更高结果。

### 主张 C3：自动监督的收益不是额外推理造成的

Workspace Trajectory 的收益必须同时超过“不给干预”和“只查看当前 workspace 的通用反思/
搜索”控制，并报告伤害率、弃权、token、工具调用和延迟。若只与弱 summary 或 final state
比较，不能支持 C2。

### 主张 C4：跨 Agent 与跨任务泛化

上述收益不是某一个 Agent、workspace 规模、语言或任务类型造成的。结论需要按 workspace、task、
Agent 和 harness 分组验证，不能随机打散 event 后做有泄漏的评估。

## 4. 研究问题

- **RQ1（客观干预效用）：** 在 supervisor 与 continuation 预算固定时，Workspace
  Trajectory Retrieval 产生的干预，是否比 Full Raw Retrieval 在相同 checkpoint 的真实
  后续运行中获得更高的官方可执行结果？
- **RQ2（信息贡献）：** 在 RQ1 出现非零收益后，prior-session 历史、action 顺序、artifact
  生命周期和 workspace transition 分别贡献多少真实 continuation gain？
- **RQ3（安全与泛化）：** 收益与伤害率、弃权和成本在不同 Agent、harness、workspace/
  task family、任务类型和运行时长上是否稳定？
- **RQ4（harness 诊断，后续）：** 多个任务上的真实干预效应能否进一步定位 skill/harness
  的系统性失效，而不依赖人工 pathology 标签？这一问题不进入第一个 RQ1 pilot。

## 5. 表示与算法作为可检验模型

### 5.1 论文算法：中性的 workspace 过程投影

论文中的主算法不是星云的力导向布局，也不是一组手写的异常分数。对冻结区间中的全部
Agent action，构造器按真实 action 顺序做一次确定性投影：保留包括零文件效应在内的全部
action；只把 native/system 证据明确支持的 read、write、create、rename、delete、execute
和 validate 关联到产物；只根据这些效应或精确静止边界更新产物的存在、路径和内容状态；
再加入显式的 action 顺序、session 所属、goal 所属与相继、路径层级、rename identity 和
action-to-artifact 关系。每个输出事实都必须带有 Full Raw 能逐字节取回的底层 ID。

核心投影不使用阈值、固定事件窗口、重要性权重、从命令文本猜测的文件效应、pathology
标签、生成的意图或由最终结果选择的特征。证据无法建立的关系保持缺失或 `unknown`。因此
算法本身不预先诊断“空转”“偏航”或“验证缺失”；这些是使用同一模型与预算的监督 Agent
需要输出的判断。

验证候选关系和跨 goal recurrence matcher 降为可删除的派生索引。它们必须引用两侧的
原始 action，并在查看标签前冻结规则；实验中单独消融。若收益依赖这些索引，只能主张该
索引有用，不能把收益泛化成整个 workspace trajectory 都有用。

### 5.2 展示算法：Agent Nebula 动态布局

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
活动会降低局部稳定约束，使真实变化仍可见。这组权重只决定 HTML/GIF/MP4 的展示效果，
不进入监督 Agent 的输入，不按 pathology 标签或诊断结果调参，也不是当前论文的算法贡献。

Agent 的“轨迹”不是永久连线。每个 action 的目标位置是当次文件集合的加权质心；连续
action 构成瞬时路径，视觉上只保留短尾迹或移动光环。用于分析时则保留完整的目录转移
矩阵与文件相邻动作图，使“频繁来回”“跨模块跳转”“局部深挖”可以量化。

## 6. 实验设计

### E1：checkpoint-fork 闭环干预实验

在官方多轮 benchmark 的下一次独立 session 之前冻结完整 workspace、已完成的原生 session、
runtime state 和下一轮官方 prompt。为同一个 checkpoint 创建四个字节一致、名称不泄漏条件
的分叉：

1. 不给任何干预；
2. 让同一个 supervisor 只查看当前 workspace，做通用反思/搜索；
3. 让 supervisor 使用完整、同源、等预算的 Full Raw Retrieval；
4. 让 supervisor 使用相同 Raw 工具，再增加确定性的 artifact history、session diff 和
   source-linked effect 查询。

后三种条件都输出一条有长度上限的 advice 或 `ABSTAIN`，以相同中性 wrapper 附加到未修改的
下一轮官方 prompt。随后使用相同 worker 模型、reasoning effort、超时和剩余轮数执行每个
分叉，最后调用未修改的官方 executable oracle。

主要 estimand 是：

```text
Δ_workspace = E[Y(WorkspaceTrajectory) - Y(FullRaw)]
Gain(c)      = E[Y(c) - Y(NoIntervention)]
Δ_structure = Gain(WorkspaceTrajectory) - Gain(GenericMatched)
```

其中 `Y` 是同一 checkpoint 后真实 continuation 的官方分数，不是人或 LLM judge 的标签。
同时报告每种干预相对 no-op 的伤害率、弃权效用、supervisor/worker token、工具调用、返回字节、
延迟和总运行时间。Full Raw 打平或获胜即否定更强的表示主张；只降低成本则只能主张效率。

### E2：轨迹信息消融

只有 E1 在官方结果上优于 Full Raw 和 Generic 控制之后，才在同一闭环任务上依次去掉：

- 跨 session 连续性；
- action 的先后顺序；
- create/rename/delete 生命周期；
- 目录和相邻 action 的空间转移；
- 修改与后续验证的关联；
- 可返回原始 action 的证据索引。

该实验判断真实干预收益究竟来自哪类过程结构，而不是仅仅看到更多文本。所有条件必须对齐
source membership 与预算并报告实际 token/byte/call 差异。动态布局继续用于 HTML/GIF/MP4
检查与 demo，但不作为当前自动监督论文的独立主张。

### E3：行为与 harness 诊断（后续、无语义 gold）

只有多个任务上的客观干预结果存在后，才分析哪些可观测过程量与正收益、伤害或弃权相关。
候选描述性指标包括：

- artifact action share 与 active-duration share；
- documentation readback；
- test-only churn actions/loops；
- unverified edit span；
- recovery cost；
- no-file-action share；
- 目录转移熵、短期折返率和重复访问但无写入的探索段。

这些指标只用于预注册描述性分析或后续机制消融，不作为主轨迹构造器的手写 pathology
特征，也不产生“人工确认的低效区间”。harness 责任必须由实际替换/移除对应 skill、hook、
instruction 后的 outcome change 或其他可执行反事实来验证；单纯相关性不能叫根因。

### E4：跨来源证据消融

比较仅使用 Agent 原生 Tool action，与加入已绑定系统文件观察后的结果。该实验回答系统级
证据究竟修正了多少漏报、路径误判和“命令声称访问但没有文件效应”的情况。系统观察是
同一 action 的附加 evidence，不引入第二条产品时间线。

## 7. 数据集与防泄漏原则

数据集应包含不同 Agent、harness、workspace 类型、语言、规模、任务类型和运行时长，并
保留失败 run，不能只收集成功案例。软件仓库可以作为第一阶段受控 workload；auto
research、论文与实验 workspace 用于检验表示是否真的超越 coding。最小可发表单元不是
event 数，而是能够在冻结 checkpoint 上复现、分叉并由官方 grader 判定结果的
task/session group。

训练或调参、阈值选择、诊断评估必须按 workspace 或 task group 划分。相同 issue、fork、
模板 workspace 或同一长运行的切片不能跨训练与测试集合。发布数据时可用路径哈希或受控
重放，但论文中的 primary truth 是未修改的官方 executable outcome；轨迹中的每个派生事实
仍须回到原始 action 或 checkpoint 字节核验。

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
- **主动记忆与 harness 优化：** Remember When It Matters 已经让独立 memory Agent 注入
  trajectory-grounded reminder；RHO 已经用历史 rollout 无监督优化 harness；SWE Context
  Bench 已比较 full trajectory 与 summary 的经验复用；REFLECT 已用 intervention replay
  检验 attribution。因此当前新意只能是严格匹配 Raw 与额外推理预算后，跨 session
  workspace evolution 是否提高真实 continuation utility。
- **评测混淆：** Rethinking Harness Evolution 说明额外 feedback/search 和同 benchmark
  调参可以伪造 harness 改进。因此必须加入 Generic matched control、held-out task family
  和实际资源账单。

## 9. 投稿路线

扩大到 workspace 后，会议选择应由最终证据最强的贡献决定，而不是预先把项目限定为
软件工程工具：

1. **AAAI AI Alignment：首选完整故事。** 以 process-level scalable oversight 为中心，
   证明监督 Agent 能够利用 workspace trajectory 在真实 continuation 中提高官方结果并
   控制伤害；动态图是可解释、可复核的 artifact，而不是论文唯一贡献。
2. **AAAI Demonstration：系统展示路线。** 用真实长期 workspace 现场展示轨迹查询和
   Agent Nebula 回放，适合验证传播力和收集反馈，但两页 demo 不能替代完整科学评价。
3. **IAAI：部署后的应用路线。** 当诊断工具已经被真实 Agent workflow 使用，并能报告
   可测量的可靠性、生产率或维护收益时，Tools and Methodologies 路线高度匹配。
4. **MSR：行为数据与测量路线。** 如果主贡献变成跨 Agent、harness 和 workspace 的长期
   trajectory 数据集、过程指标与实证发现，MSR 比单纯可视化会议更合适。可视化在这条
   路线上是分析仪器，不是主要新意。
5. **ICSE/FSE/ASE：软件工程子集路线。** 如果实验主要落在代码仓库，贡献集中于开发过程
   恢复、软件理解或自动化开发诊断，可以投稿；但需要明确把 auto research 作为泛化场景，
   不能一边声称通用 workspace、一边只评测 coding。
6. **CHI/IEEE VIS/IUI：不作为当前主路线。** 它们适合未来研究人类理解、交互或布局本身；
   当前既然只研究自动诊断或 Agent 使用工具，就不以用户实验和可视化可用性作为主要证据。

当前建议以 **AAAI AI Alignment 作为完整研究故事的第一目标**，AAAI Demonstration 作为
独立的系统展示入口，MSR 可承接数据/测量论文。若未来把 AgentSight 的跨层系统捕获、
声明—效应差异、低开销长期采集和生产规模做成核心，才适合讨论系统会议；仅有可视化
不足以支撑 OSDI/SOSP 式系统主张。

## 10. Go/No-Go 门槛

在扩大实现之前按顺序完成三个 gate：

1. **真实机制 preflight：** 在 Harness Bench 多轮任务的 session 边界成功 pause/fork/
   inject，四个分叉字节一致、无 oracle/future leakage，所有后续 session 和官方 grader
   可重复运行；
2. **客观效用 pilot：** Workspace Trajectory 相对 Full Raw 与 Generic matched control
   是否提高 task-balanced official outcome，且不增加相对 no-op 的伤害率；
3. **泛化 pilot：** 通过独立计划把同一协议扩展到未见过的 coding workspace family 和
   scientific-work benchmark，不能把同一任务的多次 continuation 当成多个 task family。

若 Workspace Trajectory 没有超过强 Raw 和额外推理控制，即使动画更吸引人，也不能继续
包装成自动监督研究贡献；最多保留经成本证实的压缩效率或产品展示价值。

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
- Harness Bench. *Measuring Harness Effects in Realistic Agent Workflows*.
  <https://www.harness-bench.ai/>
- Wu et al. *Remember When It Matters: Proactive Memory Agent for Long-Horizon
  Agents*. <https://arxiv.org/abs/2607.08716>
- Pan et al. *Retrospective Harness Optimization: Improving LLM Agents via
  Self-Preference over Trajectory Rollouts*. <https://arxiv.org/abs/2606.05922>
- Wang et al. *Rethinking the Evaluation of Harness Evolution for Agents*.
  <https://arxiv.org/abs/2607.12227>
- Zhu et al. *SWE Context Bench: A Benchmark for Context Learning in Coding*.
  <https://arxiv.org/abs/2602.08316>
- METR. *RE-Bench: Evaluating frontier AI R&D capabilities of language model
  agents against human experts*.
  <https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/>
- Siegel et al. *CORE-Bench*. <https://github.com/siegelz/core-bench>
- Archambault, Purchase, and Pinaud. *Animation, Small Multiples, and the Effect
  of Mental Map Preservation in Dynamic Graphs*.
  <https://inria.hal.science/inria-00472423v1>
- Beck et al. *The State of the Art in Visualizing Dynamic Graphs*.
  <https://www.visus.uni-stuttgart.de/documentcenter/forschung/visualisierung_und_visual_analytics/eurovis14-star.pdf>
