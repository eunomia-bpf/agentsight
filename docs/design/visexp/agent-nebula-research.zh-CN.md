# Agent Nebula 研究计划：长期 Agent 的工作空间轨迹与自动监督

> **2026-07-23 当前科学合同。** 先让工具对真实长期 workspace 有用，再决定论文最终
> 形态。代码负责从 Claude、Codex、Gemini 原生记录计算可复查的跨 session 关系；Agent
> 读取紧凑简报、沿 source anchor 做语义解释，但不充当 gold。当前不主张“轨迹表示提高
> continuation 分数”，也不把人工 pathology 标注作为实验前提。首先回答一个更小的实证
> 问题：围绕持久 workspace 组织轨迹后，能观察到哪些单次 trace、最终 diff 和聚合计数
> 隐藏的过程连续性、动作策略与跨 root 精确路径访问？

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

> We organize native Agent histories around persistent workspaces, compute
> source-linked cross-session process relations locally, and expose them as an
> evidence index that another Agent can inspect rather than a verdict generator.

核心研究问题是：以 workspace 而非单次 trace 为单位后，能否重建 artifact 形成、反复
修改、验证关联、跨 session 交接与回访，量化 inspect–mutate–validate 的动作次序，并把
本地 lineage 与根在其他 workspace 的 Agent 精确路径访问区分开？这些关系能否让 Agent
先定位值得深读的原始证据，而不必重新估算日志中的计数和跨 session join？

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
5. **action–artifact provenance、跨 trace 对齐或让 Agent copilot 读图。** 2026 年
   AgentTrails 已经从原始轨迹恢复 action/entity provenance、构造多 trace joined graph、
   提取 pattern/skill，并让 LLM copilot 解释可审计图；Agentic Harness Engineering 也已
   把大量轨迹压缩为 evolving Agent 可消费的 evidence corpus。这些都不能作为本项目的
   一般性新意。

### 2.2 可辩护的研究空白

现有细粒度开发历史主要面向人类 IDE 操作；现有 Agent provenance/轨迹工具已经覆盖单次
与多次执行中的 action–artifact 依赖、比较和 Agent 辅助解释。Agent Nebula 因而只保留
一个更窄、必须由数据验证的交叉点：

- **持久 workspace 内部连续性：** 不把每个 native session 当独立 run，而是跟踪同一
  artifact 跨 session 的形成、反复修改、后续 worktree 验证关联、交接、回访和未闭合状态；
- **演化角色与 session root 分离：** `--global` 只接纳原生 Tool call 中精确引用该
  workspace 路径的外部 session；root-external session 可能是只读访问，也可能是受委托
  修改该仓库的 subagent。只读 root 不进入 mutation-driven evolution；产生 mutation 的
  root 仍是演化证据。该关系不再被命名为“独立消费者”；
- **证据索引而非自动定罪：** 本地代码计算关系、分母和两端 source anchor，Agent 再解释
  意图、失败、用户纠偏和可能干预点；高 mutation、低回读或长 validation 段都不是自动
  pathology；
- **不限于代码：** artifact 可以是源码、论文、实验结果、数据和 harness 文档；Git 只
  提供外层状态，不定义 action 时间轴。

因此，建议的中心表述是：

> Agent Nebula is a workspace-centered process-observability instrument that
> reconstructs persistent artifact evolution and action strategy, distinguishes
> root-external exact-path access, and exposes each relation as source-linked
> evidence for Agent inspection.

“星云”是这个模型的一种交互表示，不是全部贡献。

## 3. 论文主张层级

### 主张 C1：持久 workspace 是可测量的过程单位

原生 action 能被组织成跨 native session 的 artifact evolution、worktree validation
association、handoff 与 re-access 关系；这些关系都返回两端的原始 Tool evidence，而不是
由 Agent 从线性日志重新估算。

### 主张 C2：动作次序与跨 session 未闭合状态可被查询

系统能直接报告 inspect→mutate、mutate→validate、validate→mutate 等折叠状态转换，
以及成功识别的 validation 之前累积了多少 confirmed mutation event。它还能列出越过
producing session 的 mutation generation 及后续 supersession、worktree validation
association 或 open cutoff。它们是检索索引，不是质量分数。

### 次要观察：root-external 精确路径访问可以单独报告

根在其他 workspace 的 native session 可以被识别，但不能自动叫作独立 consumer：它可能
是被委派到该仓库的 subagent。报告必须分别给出 read action、native root session、source
file 和 observed mutation effect，且“读取”不等于遵守、因果影响或质量提升。

### 主张 C3：简报是 Agent 的检索索引，不是语义 gold

紧凑简报应帮助 Agent 选择热点、跨 session handoff 和少量 source anchor；原始记录仍负责
意图、失败原因、用户纠偏和语义阶段。当前只主张可检索性与案例效用，不主张简报必然比
Full Raw 得出更正确的语义诊断。

### 非主张：可视化与自动干预收益

星云布局服务回放、检查和传播；不作为统计测量。trajectory advice 是否提高 continuation
官方分数是未来可选实验，当前没有证据，不能写入主 claim。

## 4. 研究问题

- **RQ1（内部过程连续性）：** 一个持久 workspace 跨 independent native session 呈现
  哪些 artifact 形成、重复 mutation、验证关联、handoff、回访、修改前 inspection 与模块迁移
  结构？这些关系在代码、论文、教程、研究和 harness workspace 中有何差异？
- **RQ2（动作策略）：** 跨 native session 的 inspect、mutate、validate 状态怎样转换？
  哪些 mutation burst 长时间未被成功识别的 validation 闭合，哪些 session 先验证再修改、
  只在修改后验证或没有可识别验证？
- **RQ3（Agent 使用价值）：** 当同一个 Agent 需要接管或审计长期工作时，source-linked
  brief 与直接 Raw Retrieval 分别能够发现什么、漏掉什么，并消耗多少检索、字节、Tool
  call 与 source verification？
- **RQ4（边界与泛化）：** 这些关系对 parser/admission 规则、generated/scratch、目录 scope、
  worktree、外部别名和 live-log cutoff 有多敏感？在独立用户与公开/前瞻 workspace 上是否
  仍成立？

## 5. 表示与算法作为可检验模型

### 5.1 论文算法：中性的 workspace 过程投影

论文中的主算法不是星云的力导向布局，也不是一组手写的异常分数。对具有固定 observation
cutoff 的全部 Agent action，构造器按真实 action 顺序做一次确定性投影：保留包括零文件效应在内的全部
action；只把 native/system 证据明确支持的 read、write、create、rename、delete、execute
和 validate 关联到产物；只根据这些效应或精确静止边界更新产物的存在、路径和内容状态；
再加入显式的 action 顺序、session 所属、goal 所属与相继、路径层级、rename identity 和
action-to-artifact 关系。每个输出事实都必须带有 Full Raw 能逐字节取回的底层 ID。

核心投影不使用固定事件窗口、重要性加权总分、pathology 标签、生成的意图或由最终结果
选择的特征。文件效应来自 `agent-session` 的 structured Tool 字段或保守的 shell grammar；
目录只在 action-time 路径证据支持时标成 scope；动态 cwd 无法解析时相对路径保持缺失，
失败与未知 mutation 分开
报告。validator 分类允许仓库自有的 `test/check/verify/validate/lint/smoke` 脚本，但后续
成功 worktree check 只叫 temporal association，不叫逐文件 coverage。算法本身不预先
诊断“空转”“偏航”或“浪费”；Agent 必须从 prompt、command、result 与 source anchor
解释这些语义。

物理 transcript 文件不是 session 分母。Codex continuation、archive 或复制文件可能包含
同一个 native root 的同一个 Tool call；投影先用
`(vendor, native_root, source_call_id/source_event_id)` 去重。没有原生 ID 时，才用
`timestamp + tool + command + structured paths` 的严格相等指纹去除逐字复制，不合并普通
的重复命令。Coverage 同时报告去重前解析的 Tool/LLM 记录数和去重后保留的 Tool call 数，
使物理日志冗余不会伪装成 Agent 行为。

验证候选关系和跨 goal recurrence matcher 降为可删除的派生索引。它们必须引用两侧的
原始 action，并在查看标签前冻结规则；实验中单独消融。若收益依赖这些索引，只能主张该
索引有用，不能把收益泛化成整个 workspace trajectory 都有用。

动作策略投影只使用三个可核验状态。对每个 native root session，把 file-active Tool event
按 action time 映射为：

```text
validate  if effect == recognized validation
mutate    else if it has a confirmed file mutation
inspect   else if it has a successful file read
other     otherwise
```

相邻相同状态先折叠，再统计有向转换；这避免一次 inventory 展开出的许多 file effect
支配策略计数。另从每个 confirmed mutation event 开始累积 mutation burst，直到同一
worktree 出现 successful recognized validation；session 或 observation cutoff 时仍未闭合
的 burst 单独报告。该算法没有任意 `24` 步窗口，也不把长 burst、无 validation 或
validate→mutate 自动命名为失败。

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

### E1：自然长期 workspace 的过程连续性研究

对每个完整可访问的 workspace lineage，按原生 action time 重建内部 evolution session，
分别报告 artifact kind、module transition、修改前 inspection、重复 mutation、validation
association、跨 session handoff 与 re-access。项目是 case，不把六个同一作者相关仓库
伪装成总体样本；每个结果都保留 source file、Tool call、event 与解释边界。

首批五个工具验证案例是 AgentSight、ActPlane、eunomia.dev、bpf-developer-tutorial 和
academic-writing-skills。它们先用于发现算法缺陷和有用问题，再由独立用户或前瞻项目验证。

### E2：动作策略与 root-external exact-path access

默认只分析 cwd/project/remote 属于目标 worktree 的 session；`--global` 额外扫描原生 Tool
call 中对目标 root 的精确路径引用。只读 external root 不参与 mutation-driven
修改前 inspection、module transition 和 exploration span；产生 mutation 的 external root
仍作为 workspace evolution evidence。主要结果包括：

- artifact 第一次 observed mutation 之后的 workspace reread 与 external reread；
- inspect–mutate–validate 转换、mutation burst 和 open burst；
- external read-only、external mutating 与无精确 file read 的 native-root 分母；
- 最常被外部读取的 artifact、read action、native root、source file 数和 source anchors；
- 对 symlink、worktree、copied workspace、动态 cwd 与诊断器自引用的敏感性。

该实验回答动作策略和跨 root 访问足迹是否可稳定测量；它不把 read 当成独立消费、遵守、
效果或因果。

### E3：Agent 读取简报与 Raw Retrieval

固定同一 Agent、源集合、任务和检索预算，比较：

1. 最终 workspace/Git；
2. 原生 session summary 或 aggregate counts；
3. Full Raw Retrieval；
4. source-linked workspace brief 加可回到 Raw 的 anchor。

Agent 输出不是 gold。事实类问题使用 exact source predicate、构造条件或 executable outcome；
开放诊断只比较检索覆盖、引用正确性、source verification、Tool call、返回字节、token 与
可行动 next step，不用另一位 Agent 的偏好分数冒充真值。开发期允许独立 Agent review 暴露
误归因和误导标题，但论文结论需要预先固定 protocol。

### E4：source conformance 与前瞻效用

parser/admission/identity 先用共享 fixture、negative path cases、rename/delete/recreate、
worktree、动态 cwd、目录 scope 和 validator semantics 做 source conformance。旧的 exact-fact
benchmark 只保留为回归套件，不再驱动 paper story。

工具稳定后，在新的长期项目结束或 session handoff 时，让接管 Agent 先读 brief、列出待核验
handoff 与 source anchors，再执行真实任务。可执行结果和是否实际使用 handoff queue 作为
前瞻证据。只有该实验成功，未来才能讨论 intervention utility；当前论文不预设成功。

## 7. 数据集与防泄漏原则

数据应包含不同 Agent、harness、workspace 类型、语言、规模、任务类型和运行时长，并保留
失败、放弃和纯读取 session，不能只收集成功案例。软件仓库是第一批成熟载体；auto research、
论文、教程、实验数据和 harness workspace 用来检验抽象是否真的超越 coding。

当前五个本地项目是自然案例和工具调试证据，不估计总体比例。独立验证必须按用户和 workspace
group 划分；相同 issue、fork、模板 workspace、共享 Skill repo 或同一长运行切片不能跨
development/test。live native logs 每次运行都会变化，所以研究结果必须记录 cutoff、source
membership、revision 与 admission counts。每个派生关系仍须回到原始 action 核验。

## 8. 最近工作与直接威胁

- **细粒度开发历史：** AZURITE、OperationReplayer、FeedBaG 和 IDE 交互可视化证明
  operation-level history 早已存在；本工作的差异必须放在 autonomous Agent、跨 session、
  仓库状态与执行证据联合建模上。
- **Agent 轨迹工具：** Agent Trajectory Explorer、AgentLens、SeaView、AgentDiagnose、
  ReTrace 与 TraceView 已覆盖通用轨迹浏览、分层摘要、时间轴、比较和关系图。TraceView
  尤其接近，因此实验必须比较“轨迹图”类基线，而不能只比较 raw log。
- **Agent provenance 与 reuse：** AgentTrails 已从原始 trace 恢复 action–artifact
  provenance、对多 trace 做 joined graph、提取 pattern/skill，并提供 LLM copilot；它是
  当前最接近的系统工作。项目只能检验 persistent workspace 内跨 native-session continuity、
  action strategy 与 cross-root exact-path access 这一更窄边界。
- **Coding Agent 行为研究：** SWE-Agent trajectory 分析、traceability taxonomy、
  SWE-Explore 和 trajectory fingerprinting 表明探索路径与行为模式已经成为评测对象。
  Agent Nebula 应提供新的可操作测量，而不是重复描述“不同 Agent 行为不同”。
- **动态图：** temporal stability 与 mental-map preservation 已有完整研究脉络；新意需要
  来自面向文件生命周期和 Agent 路径的联合目标及其任务实证，而非直接复用术语。
- **主动记忆与 harness 优化：** Agentic Harness Engineering 已把大量经验压缩成 evolving
  Agent 可消费的 evidence corpus；RHO 用历史 rollout 无监督优化 harness；SWE Context
  Bench 比较 full trajectory 与 summary；REFLECT 用 intervention replay 检验 attribution。
  因此“让 Agent 读历史”“优化 harness”都不是当前新意。当前只研究可观察的动作策略、
  artifact 连续性和 cross-root access，并把 causal harness claim 留给真实替换或 outcome
  实验。
- **评测混淆：** Rethinking Harness Evolution 说明额外 feedback/search 和同 benchmark
  调参可以伪造 harness 改进。因此必须加入 Generic matched control、held-out task family
  和实际资源账单。

## 9. 投稿路线

扩大到 workspace 后，会议选择应由最终证据最强的贡献决定，而不是预先把项目限定为
软件工程工具：

1. **MSR：当前最匹配的完整论文路线。** 如果贡献是跨 Agent/harness/workspace 的长期
   process dataset、source-valid measurement 与 action-strategy / workspace-continuity 实证，
   MSR 比泛化的“自动监督”主张更准确。
2. **AAAI Demonstration：系统展示路线。** 用真实长期 workspace 现场展示轨迹查询和
   Agent Nebula 回放，适合验证传播力和收集反馈，但两页 demo 不能替代完整科学评价。
3. **IAAI：部署后的应用路线。** 当诊断工具已经被真实 Agent workflow 使用，并能报告
   可测量的可靠性、生产率或维护收益时，Tools and Methodologies 路线高度匹配。
4. **AAAI/NeurIPS/ICLR 完整论文：有条件路线。** 只有独立、前瞻实验证明 brief 或
   handoff queue 改善 Agent continuation、harness evolution 或可执行 outcome，才能回到
   scalable oversight/learning story；当前五个观察案例不够。
5. **ICSE/FSE/ASE：软件工程子集路线。** 如果独立实验主要落在代码仓库，贡献集中于开发过程
   恢复、软件理解或自动化开发诊断，可以投稿；但需要明确把 auto research 作为泛化场景，
   不能一边声称通用 workspace、一边只评测 coding。
6. **CHI/IEEE VIS/IUI：不作为当前主路线。** 它们适合未来研究人类理解、交互或布局本身；
   当前既然只研究自动诊断或 Agent 使用工具，就不以用户实验和可视化可用性作为主要证据。

当前建议以 **MSR/实证测量故事作为第一完整论文目标**，AAAI Demonstration 作为
独立的系统展示入口；若前瞻 utility 出现，再升级为 AAAI 等 Agent 论文。若未来把 AgentSight 的跨层系统捕获、
声明—效应差异、低开销长期采集和生产规模做成核心，才适合讨论系统会议；仅有可视化
不足以支撑 OSDI/SOSP 式系统主张。

## 10. Go/No-Go 门槛

按顺序完成三个 gate：

1. **产品与 source-conformance gate：** 一个命令在真实 workspace 生成 Agent 可读简报；
   cwd/worktree/scope/rename/delete/recreate/status/validator/global admission 有测试与
   source audit；signal 保持中性并能直接回到原始 Tool call。
2. **独立实证 gate：** 在不同用户或前瞻 workspace 上复现至少一种非平凡的内部 continuity
   与 cross-root exact-path access 发现，并排除诊断器自引用、共享 Skill 安装路径和
   alias/copy 混淆。
3. **Agent utility gate：** 固定 source/budget 的 Agent-reader protocol 证明 brief
   至少降低检索成本或提高 exact source coverage；若要主张监督收益，还必须真实执行
   continuation 并用可执行 outcome 验证。

若只有漂亮动画和本地五案例，本项目保留为有价值的 OSS/demo，不能包装成一般性 Agent
science。若 cross-root access 不能在独立数据中复现，则把它降级为案例发现；
若 brief 不优于 Raw，则只主张本地索引与可视化，不主张诊断能力提升。

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
- Wu et al. *AgentTrails: Towards Trust and Reuse for Agentic Tasks*.
  <https://arxiv.org/abs/2607.18816>
- Lin et al. *Agentic Harness Engineering: Observability-Driven Automatic
  Evolution of Coding-Agent Harnesses*. <https://arxiv.org/abs/2604.25850>
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
