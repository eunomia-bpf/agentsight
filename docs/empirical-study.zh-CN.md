# 长期 Agent 工作过程实证研究设计

## 核心问题

**一个 Agent 自主运行几天时，它究竟在持续取得经过验证的进展，还是只产生了大量看起来繁忙的活动？**

用户面对的不是“Git 少记录了什么”这一抽象问题，而是一个很具体的判断困难：给 Agent 一个目标和初始 idea，让它在同一个 workspace 里跨多个 session 自我迭代两三天；回来时看见几百次工具调用、几十个 commit 和大量文件，却不能判断项目是否正在收敛，Agent 先测试还是先实现，主要改了什么模块，在代码、论文和实验上分别投入多少，哪些尝试失败后被修正，以及 skill 或 harness 是否让工作陷入文档负担或测试空转。

本研究把长期 Agent 工作看成作用于持久 workspace 的有序过程。文件可以是代码、测试、配置、论文、研究笔记、数据、实验结果或文档；session 只是上下文容器，不是研究对象的边界。时间轴完全服从 Agent 的真实操作时间。Git 只提供最终状态、版本里程碑和部分存活证据，不定义轨迹时间，也不是论文主线。

## 研究贡献与案例发现分开

1. **实证贡献。** 在六个真实、持续演化的本地开源项目中，描述活动如何转化为 artifact 的持久、复用和验证，返工如何发生，session 边界后 Agent 如何重新建立工作连续性，以及注意力如何在 artifact 类型和模块间迁移。
2. **测量贡献。** 检验带有稳定 artifact identity、生命周期、层级、事件时间和 session lineage 的 workspace-centered action trajectory，能否表达 Final Diff、简单事件计数和 action-only procedure 无法编码的源可校验过程事实。
3. **工具产物。** `agent-session` 负责跨 Agent 的原始抽象；Agent Nebula 和研究查询只做薄投影。单图 HTML/PNG/SVG/GIF/MP4 是同一事实的可检查和可分享输出，不是独立科学 claim。

案例研究产生的是发现，不自动成为方法贡献。轨迹重建是 by design 的构造性质；只有来源覆盖、事实恢复准确性、额外事实覆盖和计算成本才是可检验的工具主张。

## 研究范围和不主张的内容

- 不要求工具改善 Agent，也不把干预效果作为当前主问题。
- 不使用人工标注、专家裁决或 LLM 生成的语义标签作为真值。
- 不从文件运动推断意图、失败原因、反思或“浪费”；只有 native session 明确记录这些语义时，后续分析才可引用原文证据。
- 不把“创建后未再读取”直接称为无用文档，也不把“反复测试”直接称为垃圾测试；它们是待解释的过程现象。
- 不从六个作者相关项目推断所有 Agent 的总体发生率，也不从观察性差异推断 skill、harness 或模型的因果效应。
- 不宣称首次研究 Agent trajectory、行为模式、验证缺失、过程指纹、持久 workspace 或确定性 trace 查询。
- Git 遗漏只作为传统结果视角的能力边界对照。

## 观测单位

- **Workspace：** 跨 session 持续存在的一组数字产物。
- **Action：** `agent-session` 解析出的有时间戳 Tool 事件；失败的调用保留为活动，但不能产生成功文件 effect。
- **Artifact：** workspace 相对路径指向的文件实体；原生 rename 保留 lineage，delete 后同路径 create 默认是新实体。
- **File effect：** read、write、create、rename 或 delete。目录参数只表示弱 scope 访问，不伪装为文件读写。
- **Mutation：** write、create、rename 或 delete。
- **Validation：** source-native effect 标识为 test/check/build/experiment 且有明确成功或失败状态的动作。成功命令只证明验证发生，不证明覆盖了某次具体修改。
- **Session boundary：** 独立 native session 的边界。并行子 Agent 不自动视为纵向重启。
- **Event time：** `(timestamp, stable source id)` 的确定性顺序，是所有动态分析的主时间轴。

## Research Questions

### RQ1：活动如何转化为持久且验证相关的 artifact progress？

长期轨迹中的 mutation 有多少形成了最终仍存在、后来被重新使用、并在后续成功 validation 前没有被立即覆盖或删除的 artifact 变化？活动量、mutation 量、存活、复用和验证之间是否一致，还是大量活动没有进入这些交集？

### RQ2：验证以什么节律跟随实现和研究产物变化？

Agent 是先验证再修改、边修改边验证，还是累积大量变更后才验证？成功和失败 validation 前后，mutation burst、artifact 范围和下一次修改如何变化？代码、测试、论文、数据和结果产物的节律是否不同？

### RQ3：返工和不收敛如何表现？

哪些 artifact 被反复读写、验证后再次修改、删除后替代，或在多个模块间来回切换？返工是短期修正、失败驱动的恢复，还是跨 session 的重复探索？这些模式与最终 artifact 存活和验证关联有何关系？

### RQ4：session 边界如何影响工作连续性？

新 session 在第一次 mutation 前需要多少读取、搜索和命令动作？它是否回到上一个 session 的活跃 artifact 和模块，还是重新探索或迁移注意力？跨 session 的重新定位、旧热点重访和返工构成怎样的可观察 `session reset tax`？该术语只描述观测成本，不推断模型内部记忆。

### RQ5：Agent 的注意力如何在 workspace 中迁移？

时间分别花在代码、测试、配置、论文/文档、数据和实验结果的什么位置？热点如何形成、迁移和冷却？主要模块之间的转移、并行推进和长期遗忘区域如何随 action time 演化？

### RQ6：skill、harness、模型和任务配置与过程模式有什么关联？

显式 skill 调用或可观察配置之后，artifact 类型、validation cadence、返工、session 重新定位和最终存活是否呈现稳定差异？某些配置是否与大量生成但很少重访的文档、长时间无验证的 mutation 或测试空转同时出现？这是时间关联和跨案例异质性分析，不是因果归因。

### RQ7（工具）：workspace-centered trajectory 增加了哪些可验证的测量能力？

在相同源记录范围内，稳定 artifact identity、生命周期、层级、event time 和 session lineage，能否比 Final Diff、Counts、ProcGrep 的标准 action-only procedure 和固定预算 Raw-log LLM 分析覆盖更多源可校验的过程事实？其准确率、覆盖率、证据定位、token、延迟和输出字节成本是多少？

## 指标：不用一个任意总分吞掉结构

“Durable verified progress”不是一个手工加权的标量。研究报告三个正交维度及其交集：

1. **Durability：** create 后 artifact 在最终 tracked workspace 中仍存在；mutation 后是否在后续 action/session horizon 内保持稳定；删除和临时 artifact 的比例。内容级存活只有在原生 diff、snapshot 或 Git line evidence 可校验时才报告，不能从路径事件猜测。
2. **Reuse：** artifact 在创建或 mutation 后是否被后续 session 再读、再写、作为命令 scope 使用，及首次重访距离。
3. **Verification association：** mutation 到下一次成功 validation 的 event/time 距离、未验证 mutation backlog、session 结束时 backlog，以及 validation 后再次 mutation 的频率。

交集表示“持久、后来被使用、并与成功验证相邻”的 artifact progress。每个分量单独报告，不把不同含义压成一个分数。所有衰减和 horizon 画完整曲线或做预先声明的敏感性分析，不使用任意固定的 24 步。

### RQ 对应测量

| RQ | 主要测量 | 重要控制或限制 |
|---|---|---|
| RQ1 | action/mutation 数；artifact 生存曲线；create 后重访；mutation→成功 validation 距离；三者交集 | 分项目报告；区分文件级和内容级证据；不把 activity 当分母之外的进展证据 |
| RQ2 | validation cadence；mutation burst；成功/失败 validation 前后事件窗；未验证 backlog | 只使用 native status；按任务/项目/Agent 分层，不声称测试覆盖具体修改 |
| RQ3 | 每 artifact mutation 分布；read–write–validate 序列；验证后返工；模块切换；delete/replace | 报告分布和多阈值敏感性，不定义单一 thrash cutoff |
| RQ4 | 新 session 首次 mutation 前动作；此前热点重访率；artifact/module overlap；跨 session 返工 | 只描述可观察重新定位，不推断内部遗忘；短 session 单列 |
| RQ5 | artifact 类型投入；模块 transition matrix/entropy；热点中心迁移；冷区持续时间 | 目录颜色/分类稳定，空间布局不是统计证据 |
| RQ6 | skill/config 事件后的动作和 artifact mix；validation、返工、存活的组内差异 | 只做时间关联；报告 source coverage 和混杂，不做因果语言 |
| RQ7 | fact accuracy、coverage、evidence precision、abstention、token/byte/latency | 问题按 action-only、artifact-linked、cross-session、final-state 分层 |

模型派生的 motif、embedding、聚类或 LLM 摘要可以作为二级探索性指标，但必须回到 source ID 和确定性指标解释；它们不定义 primary truth，也不能替代上述事实测量。

## 首批六案例

| 项目 | 工作类型 | 入选理由 |
|---|---|---|
| AgentSight | 系统软件、可观测性、研究 | 长期、多 Agent、大规模代码和文档演化 |
| ActPlane | 系统软件、研究 | 大型长期实现与实验迭代 |
| bpf-developer-tutorial | 教程、代码、文档 | 文档与代码共同演化的对照 |
| eunomia.dev | 站点、博客、文档、代码 | 内容生产与软件维护混合 |
| agentskill-observability-paper | 论文、实验、代码 | auto-research 工作空间 |
| academic-writing-skills | skill、prompt、测试、文档 | skill/harness 开发案例 |

主分析只纳入 repository identity 可直接确认的 Claude、Codex 和 Gemini session，并保留 session 中没有文件路径的 Bash、validation 和其他 Tool action。`--global` 路径命中只补充外部 session 的文件 effect；因为它缺少周围 no-file action，不能进入 validation cadence 和 session-reset 主分析，只做覆盖率敏感性检查。

## RQ7 的对照和事实集

1. **Final Diff / final workspace：** 代表只看最终结果。
2. **Counts：** 每类 action、文件和 session 的聚合计数，代表 activity telemetry。
3. **ProcGrep `2e8277003d...`：** 最强 action-only procedure 对照；直接使用官方 Claude/Codex adapters 和 canonical action spine，不用自制 n-gram 替代。
4. **Bounded Raw-log LLM：** 同源范围、固定检索/context/output 预算，要求给出 source citation 或 abstain；不是 ground truth。
5. **Artifact-linked trajectory：** 本方法，只增加稳定 artifact identity、effect、hierarchy、event time 和 session lineage。

事实问题预先分层：

- **action-only：** 先读还是先写、测试是否出现在 edit 后、动作序列模式；ProcGrep 应当持平或获胜。
- **artifact-linked：** 哪个 artifact 在验证后又被修改、哪个新文件后来被重访、rename 前后是否为同一 lineage。
- **cross-session：** 新 session 是否回到上一 session 热点、首次 mutation 前重新读取了哪些既有 artifact。
- **final-state：** 哪些 artifact 最终存在；Final Diff 应当足够。

真值由与被测输出独立的 native record、workspace state 和 Git/source snapshot 校验程序生成。工具输出必须给出 source ID；没有足够源证据时正确行为是 abstain。这样不需要人工语义 gold，也避免用另一个 LLM 的意见给本方法打分。

## 分析与报告规则

- 六个项目先分别作为完整案例报告，再给出跨案例共同模式；不把 session 当作独立项目样本夸大显著性。
- 主要结果是效应大小、分布、生存/累积曲线和不确定性，不以 `p < 0.05` 代替解释。
- bootstrap 或置换只在交换单位合理时按 project/session block 进行；连续 action 不独立重采样。
- 报告 Claude/Codex/Gemini、项目、artifact 类型和时间段覆盖；缺失 Tool status、effect 或 session cwd 的事件保留在 coverage 表，不静默丢弃。
- 观察到的 skill/harness 差异只用于形成后续受控假设。若多个项目的任务、模型和 harness 同时不同，不做跨项目因果比较。
- 首批本地案例是 supporting、hypothesis-generating evidence。面向 AAAI 的广泛经验主张最终需要独立公开或前瞻采集的外部 corpus；选择依据由本轮 source-coverage 结果决定。

## 预期产物

- 每项目一个 source-coverage JSON/CSV 和一个过程指标 JSON/CSV；
- 跨项目 RQ1–RQ6 汇总表与可复算脚本；
- RQ7 的分层事实集、各方法输出和成本表；
- RQ1 的 artifact survival、reuse 和 validation-association 图；
- RQ2/RQ3 的 mutation/validation/rework 时间图；
- RQ4 的 session-boundary 对齐图；
- RQ5 的 artifact/module 注意力迁移图；
- 每项目可分享的 Agent Nebula 单图 HTML 和媒体文件，作为案例证据导航而非统计真值。

### 论文图表计划

所有数值结果图必须由 Python/matplotlib 直接读取冻结的 CSV/JSON 生成矢量 PDF；不在 TikZ 中手填结果，不用示意数字冒充实验结果。每个图只回答一个主要问题：

| 图 | 作用 | 数据和形式 | 状态 |
|---|---|---|---|
| F1 过程测量定义图 | 说明 artifact durability、reuse、validation distance 和 session re-grounding | TikZ action-time 示意图，明确不是实验数据 | 已画入论文 |
| F2 数据流图 | 说明 native session 如何经 `agent-session` 进入测量和 Agent Nebula | TikZ 设计图 | 已画入论文 |
| F3 RQ1 progress 曲线 | 展示各项目 mutation 的 durability、reuse、validation association 随 event/session horizon 的累积曲线 | Python 生成多曲线/CDF，项目分面并给 block uncertainty | 等 RQ1 数据 |
| F4 RQ1 activity–progress 对照 | 检验 action/mutation volume 是否对应三个进展维度 | Python scatter/interval plot，项目是主要点，session 只作组内分布 | 等 RQ1 数据 |
| F5 RQ2 validation 节律 | 展示 mutation backlog 和成功/失败 validation 的时间关系 | Python event-aligned line/heatmap | 等 RQ2 数据 |
| F6 RQ3 rework 分布 | 展示 artifact mutation、验证后返工和 delete/replace 的长尾 | Python CCDF/分组 interval plot | 等 RQ3 数据 |
| F7 RQ4 session reset | 展示 session 边界前后重新读取、首次 mutation 和此前热点重访 | Python boundary-aligned curve | 等 RQ4 数据 |
| F8 RQ5 attention migration | 展示 artifact 类型投入和 module transition | Python stacked area + transition heatmap；不使用力布局坐标作统计 | 等 RQ5 数据 |
| F9 RQ6 configuration association | 展示 skill/harness 可观察事件后的组内过程差异及不确定性 | Python forest plot；只写 association | 等 RQ6 数据 |
| F10 RQ7 measurement coverage | 对比 Final State、Counts、ProcGrep、Raw-log LLM 和 artifact trajectory | Python accuracy/coverage/cost 多面板；action-only 和 artifact-linked 分层 | 等 RQ7 数据 |

正文只保留支持主要 claim 的图；精确数值和完整项目表放附录/结果文件，避免同一数据同时以冗余表格和图重复。

## 当前第一项实验

第一项完整实验只回答 RQ1：在六个项目的全部合格 native sessions 中，activity、artifact durability、reuse 和 validation association 的关系是什么？一次统一 extraction 可以保留后续 RQ 所需字段，但本轮只对 RQ1 做预先声明的解释和结论。RQ2–RQ7 在后续 research step 分别进入独立实验设计和复审，避免用一个巨大脚本同时“证明”多个不同关系。
