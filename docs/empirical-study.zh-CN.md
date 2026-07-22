# 长期 Agent 工作过程实证研究设计

## 核心问题

**一个 Agent 自主运行几天时，它究竟在持续取得经过验证的进展，还是只产生了大量看起来繁忙的活动？**

用户面对的不是“Git 少记录了什么”这一抽象问题，而是一个很具体的判断困难：给 Agent 一个目标和初始 idea，让它在同一个 workspace 里跨多个 session 自我迭代两三天；回来时看见几百次工具调用、几十个 commit 和大量文件，却不能判断项目是否正在收敛，Agent 先测试还是先实现，主要改了什么模块，在代码、论文和实验上分别投入多少，哪些尝试失败后被修正，以及 skill 或 harness 是否让工作陷入文档负担或测试空转。

本研究把长期 Agent 工作看成作用于持久 workspace 的有序过程。文件可以是代码、测试、配置、论文、研究笔记、数据、实验结果或文档；session 只是上下文容器，不是研究对象的边界。时间轴完全服从 Agent 的真实操作时间。Git 只提供最终状态、版本里程碑和部分存活证据，不定义轨迹时间，也不是论文主线。

## 研究贡献与案例发现分开

1. **实证贡献。** 在六个真实、持续演化的本地开源项目中，描述活动如何转化为 artifact 的持久、复用和验证，重复 mutation 如何分布，source-session component 之间可以观察到什么连续性，以及 path-resolved workspace activity 如何在 artifact 类型和模块间迁移。
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
- **Artifact：** `(worktree id, workspace 相对路径)` 指向的文件实体；原生 rename 只在同一 worktree 内保留 lineage，delete 后同路径 create 默认是新实体。
- **File effect：** read、write、create、rename 或 delete。目录参数只表示弱 scope 访问，不伪装为文件读写。
- **Mutation：** write、create、rename 或 delete。
- **Validation：** 当前 adapter 从有限命令族识别出的 test/check/build 动作；只有 `status == ok` 是 recognized successful validation。未识别命令和 `observed` 状态属于 coverage unknown。成功命令只证明验证发生，不证明覆盖了某次具体修改。
- **Session boundary：** 独立 native session 的边界。并行子 Agent 不自动视为纵向重启。
- **Event time：** `(timestamp, stable source id)` 的确定性顺序，是所有动态分析的主时间轴。

## Research Questions

### RQ1：活动如何转化为持久且验证相关的 artifact progress？

长期轨迹中新引入的 artifact 有多少最终仍存在？mutation episode 有多少后来重新使用，多少在下一次 mutation/delete 覆盖之前出现 adapter 识别的成功 validation？活动量、mutation 量、引入物存活、复用和验证之间是否一致，还是大量活动没有进入这些交集？

### RQ2：验证以什么节律跟随实现和研究产物变化？

Agent 是先验证再修改、边修改边验证，还是累积大量变更后才验证？成功和失败 validation 前后，mutation burst、artifact 范围和下一次修改如何变化？代码、测试、论文、数据和结果产物的节律是否不同？

### RQ3：重复 mutation 的结构如何表现？

artifact 的首次 mutation 与 repeat-observed mutation episode 分别有多少？重复 mutation 在 artifact identity 之间如何集中，并怎样随 Agent action order 累积？当前证据只回答这一描述性切面；它不自动等于返工、不收敛、thrashing、缺陷修复或浪费，validation-followed revision 和 module switching 仍是开放问题。

### RQ4：source-session component 之间能观察到什么连续性？

native records 不提供跨 Agent 可移植的 parent/child session role，而且 session 会重叠。当前分析在每个 worktree lane 内构造 transitive concurrency components，只比较相邻且不重叠的 component：下一 component 首次 mutation 前发生了什么、是否重访前一 component 的 artifact/module。若 coverage gate 不足，就只报告 within-case/source-coverage，不把它称为 reset、resume、memory、forgetting 或 comprehension。

### RQ5：path-resolved workspace activity 如何分配和迁移？

可解析到路径的 action 分别落在代码、测试、配置、论文/文档、数据和实验结果的什么位置？相邻 Tool call 是留在同一 artifact、同一 module，还是跨 module；离开后经过多少 call 返回？这些是 action-order activity，不是时长、内部 attention、重要性、生产率、entropy、cooling 或 forgetting。

### RQ6：skill 和 instruction 的 source coverage 足够做关联分析吗？

用户仍然关心：skill/harness 是否制造文档负担、无效测试迭代或其他流程空转。但在比较结果前，必须先确认 source records 能否定义 exposure 和 non-exposure。当前只审计 exact `Skill` Tool call，以及 `AGENTS.md`、`CLAUDE.md`、`SKILL.md` 的 read/mutation；若缺少 Skill 名称/参数、模型/配置字段、repo 外 instruction 和真实未暴露证明，就停止 association analysis，而不是把缺失当作未使用。

### RQ7（工具）：冻结 corpus 是否具备公平 matched comparison 的证据合同？

在生成任何问题、模型调用或性能数值之前，冻结 corpus 是否同时保存了 normalized action spine、source linkage、immutable native admitted prefixes、per-worktree cutoff revision/untracked state，以及可执行的 pinned baseline 和独立 oracle 合同？缺一项就将相应方法/问题族记为 N/A，并停止比较。workspace-centered trajectory 是否优于 Final Diff、Counts、ProcGrep 或 Raw-log LLM 是后续 capability 问题，不由当前 RQ7 回答。

## 指标：不用一个任意总分吞掉结构

“Durable verified progress”不是一个手工加权的标量。研究报告三个正交维度及其交集：

1. **Introduced-artifact persistence：** 只统计 observation 内以 confirmed-success create 出生的 identity 是否在对应 worktree 的最终 tracked workspace 中仍存在；rename 永远继承 source identity 的出生状态，不能把新路径当成新 artifact。删除和临时 artifact 单列；worktree 已缺失或无法查询时，final state 记为 unknown 并从该维度排除，不能当成不存在。既有文件 write 的内容级存活是 unknown，只有原生 diff、snapshot 或 Git line evidence 可校验时才报告，不能从路径存在猜测。
2. **Reuse：** artifact 在创建或 mutation 后是否被后续 session 再读、再写、作为命令 scope 使用，及首次重访距离。
3. **Verification association：** mutation 到同一 artifact 下一次 mutation/delete 之前 recognized successful validation 的 event/time 距离；覆盖是 competing outcome，观察结束才是右删失。任意更晚 validation 只作 global association。

交集表示“持久、后来被使用、并与成功验证相邻”的 artifact progress。每个分量单独报告，不把不同含义压成一个分数。所有衰减和 horizon 画完整曲线或做预先声明的敏感性分析，不使用任意固定的 24 步。

### RQ 对应测量

| RQ | 主要测量 | 重要控制或限制 |
|---|---|---|
| RQ1 | action/mutation 数；introduced-artifact persistence；mutation 后重访；validation-before-supersession competing-risk 曲线；合格 introduction episode 的三者交集 | 分项目报告；既有 write 的内容 durability 为 unknown；不把 activity 当分母之外的进展证据 |
| RQ2 | validation cadence；mutation burst；成功/失败 validation 前后事件窗；未验证 backlog | 只使用 native status；按任务/项目/Agent 分层，不声称测试覆盖具体修改 |
| RQ3 | 首次/repeat-observed mutation episode；每 identity load；exact top-10% concentration；action-atomic prefix curve | 只描述已观察 mutation 结构，不推断 convergence、thrashing、waste 或 failure |
| RQ4 | concurrency component 边界；mutation-observed prefix；artifact/module overlap；first-mutation state | 只比较相邻不重叠 component；coverage 不足即停止，不推断 reset/resume/memory/forgetting |
| RQ5 | artifact 类型的 path-resolved action/call allocation；同 artifact/同 module/跨 module transition；return gap | `ok`/`observed` 分层；不使用力布局坐标，不解释为 attention/time/importance/entropy/cooling |
| RQ6 | exact Skill Tool；instruction read/mutation；session/vendor/status/source-call coverage；action-order bins | 当前 exposure 字段不足，association/effect 全部 N/A |
| RQ7 | source-contract present/partial/N/A；method/template readiness；comparison stop | 不生成 accuracy、advantage、evidence、token、latency 或 cost 数值；N/A 不等于零性能 |

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

## RQ7 readiness gate 与后续对照设计

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

上述是后续 capability comparison 的条件设计。真值必须由与被测输出独立的 native record、workspace state 和 Git/source snapshot 校验程序生成；工具输出必须给出 source ID，没有足够源证据时正确行为是 abstain。当前冻结 corpus 缺少 immutable native prefixes 和 cutoff worktree/untracked state，因此 F10 只审计 readiness，不生成事实问题或方法分数。

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
- RQ7 的 source-contract、method/template readiness 表；后续 corpus 合同齐备后再生成分层事实集、方法输出和成本表；
- RQ1 的 artifact survival、reuse 和 validation-association 图；
- RQ2/RQ3 的 mutation/validation/rework 时间图；
- RQ4 的 session-boundary 对齐图；
- RQ5 的 artifact/module path-resolved activity 分配和迁移图；
- 每项目可分享的 Agent Nebula 单图 HTML 和媒体文件，作为案例证据导航而非统计真值。

### 论文图表计划

所有数值结果图必须由 Python/matplotlib 直接读取冻结的 CSV/JSON 生成矢量 PDF；不在 TikZ 中手填结果，不用示意数字冒充实验结果。每个图只回答一个主要问题：

| 图 | 作用 | 数据和形式 | 状态 |
|---|---|---|---|
| F1 过程测量定义图 | 说明 introduced-artifact persistence、reuse、validation-before-supersession 和 session re-grounding | TikZ action-time 示意图，明确不是实验数据 | 已画入论文 |
| F2 数据流图 | 说明 native session 如何经 `agent-session` 进入测量和 Agent Nebula | TikZ 设计图 | 已画入论文 |
| F3 RQ1 progress 曲线 | 展示 introduced-artifact persistence、reuse 和 validation-before-supersession | Python 生成 persistence panel 与 Aalen–Johansen competing-risk 曲线，显示 denominator/risk count | 六项目真实数据已独立复算通过并入文 |
| F4 RQ1 activity–progress 对照 | 检验可归属 worktree 的 action/mutation volume 是否对应三个进展维度 | Python scatter/interval plot；无法定位 worktree 的 admitted action 单列为 coverage，不混入横轴 | 六项目真实数据已独立复算通过并入文 |
| F5 RQ2 validation 节律 | 展示 cumulative mutation trajectory、recognized validation outcome 和完整 cycle backlog | Python 原生 action-order 轨迹 + complete-cycle 分布；无成功 validation 的项目只显示 coverage | 真实数据已独立复算通过；3/6 source coverage，结论停在 within-case |
| F6 RQ3 repeated-mutation 结构 | 展示 unconditional zero mass、conditional CCDF、identity concentration 和 action-atomic repeat prefix | Python CCDF + concentration + post-action step curve，不定义 thrash cutoff | 六项目真实数据已独立复算通过并入文 |
| F7 RQ4 component continuity | 展示相邻不重叠 component 的 first mutation、prefix composition、artifact/module overlap 和 coverage | Python component-boundary 图；重叠 session 不被强行串行化 | 真实数据已独立复算通过；gate 失败，停在 coverage/within-case |
| F8a/F8b RQ5 activity allocation/migration | 展示 artifact 类型分配、module activity、source-path transition 和 return gap | Python stacked bars + action-order heatmap；不使用力布局坐标作统计 | 真实数据已独立复算通过并入文；低支持 return 显示 N/A |
| F9 RQ6 source-signal coverage | 展示 exact Skill/instruction 信号的 session、vendor、status 和 action-order coverage | Python nonexclusive shares + N/A-masked count heatmap + equal-action bins；不画效应 | 两轮独立结果复核通过；association analysis 明确停止 |
| F10 RQ7 matched-comparison readiness | 审计 Final State、Counts、ProcGrep、Raw-log LLM 和 artifact trajectory 是否具备公平比较所需的同源证据合同 | Python source-contract/method/template readiness 矩阵；N/A 不编码为零性能 | 两轮独立结果复核通过；12 present、0 partial、24 N/A，matched comparison 明确停止 |

正文只保留支持主要 claim 的图；精确数值和完整项目表放附录/结果文件，避免同一数据同时以冗余表格和图重复。

## 当前证据状态

RQ1–RQ7 均在同一冻结 corpus 上分别设计、运行和独立复核，没有用一个巨大脚本同时“证明”不同关系。RQ1 的 reuse 具备六项目覆盖，persistence/validation 只覆盖 3/6；RQ2 同样因 recognized-success 只覆盖 3/6 而停止跨案例回答；RQ3 的 repeated-mutation structure 覆盖六项目；RQ4 的 boundary estimator 未满足四项目 gate；RQ5 的 path-resolved activity allocation/transition 覆盖六项目但 return gap 有一个低支持 N/A；RQ6 因 exposure-defining 字段缺失，停在 source-coverage。RQ7 完成的是 matched-comparison readiness audit：normalized Counts 仅满足描述性 prerequisite，Artifact Trajectory 仅为 coverage-only，Final State、ProcGrep 和 Raw-log LLM 因缺少 native-prefix/cutoff-workspace 合同保持 N/A；它不构成任何 baseline 优越性证据。
