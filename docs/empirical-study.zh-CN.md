# 长期 Agent 工作过程实证研究设计

## 核心问题

**一个 Agent 自主运行几天、跨过多个 session 后，持久 workspace 中的产物究竟如何形成、被验证、被重访、迁移和重新组织？**

用户面对的不是“Git 少记录了什么”这一抽象问题，而是一个很具体的判断困难：给 Agent 一个目标和初始 idea，让它在同一个 workspace 里跨多个 session 自我迭代两三天；回来时看见几百次工具调用、几十个 commit 和大量文件，却不能判断项目是否正在收敛，Agent 先测试还是先实现，主要改了什么模块，在代码、论文和实验上分别投入多少，哪些尝试失败后被修正，以及 skill 或 harness 是否让工作陷入文档负担或测试空转。

本研究把长期 Agent 工作看成作用于持久 workspace 的有序过程。文件可以是代码、测试、配置、论文、研究笔记、数据、实验结果或文档；session 只是上下文容器，不是研究对象的边界。时间轴完全服从 Agent 的真实操作时间。Git 只提供最终状态、版本里程碑和部分存活证据，不定义轨迹时间，也不是论文主线。

## 研究贡献与案例发现分开

1. **实证贡献。** 在六个真实、持续演化的本地项目中，描述 artifact 如何保留、复用和复活，validation 如何响应 mutation，热点如何形成和迁移，source-session component 之间可以观察到什么连续性，以及 source-explicit skill/instruction 如何对应到 workspace 足迹。
2. **测量贡献候选。** 检验带有稳定 artifact identity、生命周期、层级、事件时间和 session lineage 的 workspace-centered action trajectory，能否正确表达 Final Diff、简单事件计数和 action-only procedure 无法编码的源可校验过程事实。当前实现未通过独立源数据一致性检验，因此这仍是被否定的实现假设，不是已经成立的论文贡献。
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

### RQ1：artifact 如何被巩固、搁置和重新激活？

长期轨迹中新引入或反复修改的 artifact 有多少最终仍存在、后来被重新读取或修改、跨 session 延续，或者在沉寂后再次被激活？mutation 是否集中在少数 identity，以及这些集中点是否随 action order 改变？这里研究的是 artifact fate 和 lineage，不再把“activity 不等于 progress”当成独立的新发现。

### RQ2：Agent 如何在 mutation 与 validation 之间切换？

Agent 是先探索、先修改还是先验证；成功和失败 validation 前后，mutation 范围、下一次修改和验证间隔如何改变？validation 是否紧跟实现，还是出现长的 mutation backlog？当前 adapter 覆盖不足时只报告 within-case 节律，不把未识别命令当成缺少验证。

### RQ3：workspace focus 如何形成、迁移、冷却和返回？

可解析到路径的 action 分别落在代码、测试、配置、论文/文档、数据和实验结果的什么位置？相邻 Tool call 是留在同一 artifact、同一 module，还是跨 module；热点何时换位、离开后经过多少 call 返回？这些是 action-order 的可观察 focus，不是内部注意力、时长、重要性、生产率、entropy 或 forgetting。

### RQ4：跨 source-session component 的工作如何续接？

把共享 native root session 的 parent/subagent stream 保持在同一个独立块内；对真正相邻且不重叠的 component，比较下一 component 首次 mutation 前的 re-grounding、前一 component artifact/module 的重访和新热点形成。coverage gate 不足时，不把它称为 memory、forgetting、comprehension 或 reset effect。

### RQ5：source-explicit skill 与 instruction 是否留下可重复的 workspace 足迹？

直接保留原生 `Skill` 名称/参数、`attributionSkill`、模型、root session、source stream 和 prompt index。Skill 足迹的主单位是 `(project, vendor, model, source role, native root session, attributionSkill)`；显式调用和 delegated execution 的同流连续连接只作保守覆盖审计，不虚构 per-invocation episode。`AGENTS.md`、`CLAUDE.md`、`SKILL.md` 的 read/mutation 单独作为 focal event。比较只问 source-attributed 组成是否重复，不推断 skill/harness 有用、无用或有因果效果。

### RQ6：哪些局部关系能跨出这六个选择性案例？

六个作者相关项目不能估计总体发生率。RQ6 不把外部 task trace 与本地长期 workspace 混成一个总体，而是在 Open-SWE-Traces 的四个 harness/model strata 和 IdeaTrail scientific-process 轨迹中分别复核严格兼容的 path-target transition 与 module return。探索顺序、验证、路径集中和 staged revision 只作 harness-conditioned 或 analogous 描述，不冒充 artifact-lineage 复现。跨 session persistence、revival、re-grounding 和 Skill attribution 在不具备持续 workspace lineage/source attribution 的公开数据上明确记为 N/A。

### 单独的工具能力问题（不混入案例 RQ）

workspace-centered trajectory 是否比 Final workspace、Counts、ProcGrep 或 bounded Raw-log reader 多恢复 source-verifiable artifact-linked/cross-session 事实，是单独的 measurement-capability 实验。它不定义案例发现，也不能把自身输出当作真值。

当前结果是负面的实现校验：对 72 份冻结 native session、六个项目和 120 个独立源数据问题，四个确定性条件完成了 480 行比较。Trajectory 与 ProcGrep 的 30 个 action-only 答案完全一致，但只与实验中不同的 source-direct action grammar 一致 18 个；更关键的是，Trajectory 对 60 个 artifact-linked/cross-session 问题全部作答，却有 28 个答案错误。因此“增加可回答事实”不能转化为 capability claim。Raw-log model 因边界契约与 evidence 中原始绝对路径冲突，在有 11 次本地读取后停止，记为 N/A，不能形成 LLM 正确率、成本或优越性结论。

这项结果要求把当前本地案例数字理解为“在已声明投影规则下得到的测量”，而不是未经校验的 source truth。后续先区分 structured direct effect、较弱的 shell/scope inference、artifact identity 和 native-root session join，再决定是否重跑工具能力比较。RQ5 有独立的 2,063-stream checker，RQ6 使用独立公开数据重建；它们不依赖本次 B/C 关系表的正确性。RQ1、RQ3、RQ4 以及 RQ2 的 mutation-linkage 部分需要额外 source-level error taxonomy。

## 指标：不用一个任意总分吞掉结构

“Durable verified progress”不是一个手工加权的标量。研究报告三个正交维度及其交集：

1. **Introduced-artifact persistence：** 只统计 observation 内以 confirmed-success create 出生的 identity 是否在对应 worktree 的最终 tracked workspace 中仍存在；rename 永远继承 source identity 的出生状态，不能把新路径当成新 artifact。删除和临时 artifact 单列；worktree 已缺失或无法查询时，final state 记为 unknown 并从该维度排除，不能当成不存在。既有文件 write 的内容级存活是 unknown，只有原生 diff、snapshot 或 Git line evidence 可校验时才报告，不能从路径存在猜测。
2. **Reuse：** artifact 在创建或 mutation 后是否被后续 session 再读、再写、作为命令 scope 使用，及首次重访距离。
3. **Verification association：** mutation 到同一 artifact 下一次 mutation/delete 之前 recognized successful validation 的 event/time 距离；覆盖是 competing outcome，观察结束才是右删失。任意更晚 validation 只作 global association。

交集表示“持久、后来被使用、并与成功验证相邻”的 artifact progress。每个分量单独报告，不把不同含义压成一个分数。所有衰减和 horizon 画完整曲线或做预先声明的敏感性分析，不使用任意固定的 24 步。

### RQ 对应测量

| RQ | 主要测量 | 重要控制或限制 |
|---|---|---|
| RQ1 | introduced-artifact persistence；lineage reuse/revival；首次/repeat-observed mutation；identity concentration | 既有 write 的内容 durability 为 unknown；不把 repeat 自动称为 rework/thrashing/waste |
| RQ2 | validation cadence；mutation backlog；成功/失败 validation 前后的 event-distance response | 只使用 native effect/status；不声称某次 test 覆盖具体 mutation |
| RQ3 | artifact 类型分配；同 artifact/同 module/跨 module transition；hotspot rank turnover；return gap | `ok`/`observed` 分层；不使用力布局坐标作为统计量 |
| RQ4 | native-root/source-stream 结构；不重叠 component 边界；artifact/module overlap；pre-mutation re-grounding | root session 是重采样块；coverage 不足即停止，不推断 memory/forgetting |
| RQ5 | exact Skill invocation/attribution；root-session×Skill 组成和 JSD；instruction read/mutation 与 immediate next action | 参数不进入特征；至少 3 个 root session；观察性足迹不等于 causal effect |
| RQ6 | 公开数据中的兼容 within-attempt relation；不可兼容 longitudinal cell 的 N/A map | 不把 synthetic/task traces 与 natural multi-session cases 池化 |

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

## 单独的 measurement-capability gate 与后续对照设计

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

上述 capability comparison 已完成确定性部分。真值由与被测输出独立的 native record、workspace state 和 Git/source snapshot 校验程序生成；工具输出必须给出 source ID，没有足够源证据时正确行为是 abstain。Step 0004 冻结 72 份 native session 和 cutoff state，独立重建 1,721 条 edge 与 120 个答案，并执行 480 行确定性矩阵。冻结实现的 Trajectory B+C 为 32/60 正确、28/60 错误（2026-07-23），当时的 capability claim 被否定。随后的错误分类把 28 个错误分成 14 个刻意放宽的 shell/scope 证据与 14 个真实缺陷（native-root session join、failed-call effect 丢失、shell 路径抽取），修复这些缺陷加一个 event workdir 缺陷并把 oracle 修正到 v4 后，当前修订在修正基准上达到 60/60 B+C（仅本语料的修复后一致性，不构成一般性 exact-fact capability claim）。Raw branch 在有真实本地检索的 preflight 中因边界契约停止，记为 N/A；840 行 integrated comparison 未完成，不比较 Raw 或确定性方法成本。

## 分析与报告规则

- 六个项目先分别作为完整案例报告，再给出跨案例共同模式；不把 session 当作独立项目样本夸大显著性。
- 主要结果是效应大小、分布、生存/累积曲线和不确定性，不以 `p < 0.05` 代替解释。
- bootstrap 或置换只在交换单位合理时按 project/session block 进行；连续 action 不独立重采样。
- 报告 Claude/Codex/Gemini、项目、artifact 类型和时间段覆盖；缺失 Tool status、effect 或 session cwd 的事件保留在 coverage 表，不静默丢弃。
- 观察到的 skill/harness 差异只用于形成后续受控假设。若多个项目的任务、模型和 harness 同时不同，不做跨项目因果比较。
- 首批本地案例是 supporting、hypothesis-generating evidence。面向 AAAI 的广泛经验主张最终需要独立公开或前瞻采集的外部 corpus；选择依据由本轮 source-coverage 结果决定。

## 预期产物

- 每项目一个 source-coverage JSON/CSV 和一个过程指标 JSON/CSV；
- 跨项目 RQ1–RQ5 汇总表、source checker 与可复算脚本；
- RQ6 的分 corpus external-relation coverage/N/A 表，不把异质数据合并成总体；
- 单独工具实验的 120 个分层事实、480 行确定性方法输出、source-conformance 结果和 Raw N/A 记录；不把共享 loop timing 当方法成本；
- RQ1 的 artifact survival、reuse、revival 和 mutation-concentration 图；
- RQ2 的 mutation/validation response 图；
- RQ3 的 artifact/module focus 分配、迁移和 return 图；
- RQ4 的 session-boundary 对齐图；
- RQ5 的 Skill attribution footprint 与 instruction focal-event 图；
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
| F6 RQ1 artifact consolidation 补充 | 展示 unconditional zero mass、conditional CCDF、identity concentration 和 action-atomic repeat prefix | Python CCDF + concentration + post-action step curve，不定义 thrash cutoff | 六项目真实数据已独立复算通过 |
| F7 RQ4 component continuity | 展示相邻不重叠 component 的 first mutation、prefix composition、artifact/module overlap 和 coverage | Python component-boundary 图；重叠 session 不被强行串行化 | 真实数据已独立复算通过；gate 失败，停在 coverage/within-case |
| F8a/F8b RQ3 focus allocation/migration | 展示 artifact 类型分配、module activity、source-path transition 和 return gap | Python stacked bars + action-order heatmap；不使用力布局坐标作统计 | 真实数据已独立复算通过；低支持 return 显示 N/A |
| F9a/F9b RQ5 Skill/instruction footprints | 展示 native root-session source coverage、合格 Skill 足迹距离、instruction focal event 和 immediate next action | Python root-block bars/有限点集 + 分项目归一化 focal-event heatmap；不构造 exposure 或因果标签 | 新鲜六项目投影和 2,063 个 native stream 复核通过；唯一合格双 Skill 比较不支持可重复分离（精确 p=0.750） |
| F10 工具 source-conformance | 对比 Final State、Counts、ProcGrep 和 artifact trajectory 在 action/artifact/cross-session/final-state 四类源可校验事实上的 correct/wrong/abstain；Raw 单列 N/A | Python 120-question common-denominator stacked bars；不绘制不可比较的 cost | 480 行确定性矩阵完成；Trajectory B+C 32 正确/28 错误，capability claim 否定；Raw preflight 后 N/A |
| F11 RQ6 external boundary | 显示 local path-target transition/module return 在 public coding/scientific trace 上的 recurrence、幅度差异和 N/A 边界 | 分 corpus 的 transition/return 图与 evidence-boundary matrix；不池化异质总体 | 五个 strata 各 64 个独立单位已运行（Open-SWE 共 256 条选择、跨 strata 255 个唯一任务 ID）；独立 checker 对 31,249 个 Tool call 和 22,113 个 transition 零差异复算通过 |

正文只保留支持主要 claim 的图；精确数值和完整项目表放附录/结果文件，避免同一数据同时以冗余表格和图重复。

## 当前证据状态

本地 RQ1–RQ5 分别由确定性脚本和 source ID 支持。RQ1 的 reuse 与 repeated-mutation structure 覆盖六案例，confirmed-create persistence 仍只有 3/6；RQ2 因 recognized successful validation 只有 3/6 而停止跨案例估计；RQ3 的 allocation/transition 覆盖六案例但一个 return-gap case 为低支持 N/A；RQ4 的 boundary estimator 未满足四项目 gate；RQ5 已修复旧导出器假阴性，67 次显式 Skill 调用和 1,675 条原生归因被保留；独立检查器对投影纳入的 2,063 个 source stream 逐一复核，共核对 7,304 条 Skill/instruction 信号和 205,836 个相邻 Tool 边界，差异为零。任意脚本或未展开 shell glob 的 instruction 访问不宣称完整；主要 instruction 图只使用 2,822 条独立重算的高置信直接/简单 shell 访问。五个 exact project/vendor/model/source-role/Skill strata 满足三 root gate，但只有 agentskill-observability-paper 的 root role 同时具备两种合格 Skill；same/different JSD 中位数为 0.116/0.123（9/10 对），root-block 随机化的差值为 -0.007，在 12 个可容许赋值（4 个不同统计值）上的单侧精确 p=0.750，因此结果是不支持稳定或可重复的 Skill fingerprint，而不是“弱指纹”。RQ6 在四个 Open-SWE strata 各取 64 个独立 task instance（256 条分层选择，跨 strata 为 255 个唯一 task ID），并取 64 个独立 IdeaTrail topic；所有 strata 均有 64 个可解析 path/transition 单位，独立 checker 对 320 行、31,249 个 Tool call 和 22,113 个 transition 零差异复算通过。五层的跨模块比例为 18.0%–30.0%，本地 path-compatible anchor 为 2.1%–20.2%；公开轨迹在 module return 前严格位于两次访问之间的调用数中位数为 2–3，本地合格案例为 2–4。因此外部证据支持“Agent 行动形成局部且会返回的有序路径轨迹”，但不支持把本地幅度当总体发生率，也不能回答 persistent artifact lineage、跨 session re-grounding 或 Skill attribution。工具 capability comparison 与上述案例 RQ 分离。确定性矩阵已经完成并否定当前实现的 exact-fact capability；Raw 因 preflight 边界停止为 N/A，没有 LLM、成本或 baseline 优越性结论。该结果要求先对 RQ1–RQ4 共用的本地投影做 source/projection error taxonomy；RQ5 的独立 native checker 与 RQ6 的独立公开数据重建受影响较小。
