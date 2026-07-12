# Operation Tree：语义 flamegraph 的递归模型

状态：设计提案（2026-07）。当前 `agentpprof` 实现的是本模型的深度-1 特例；
本文描述目标模型和演进路径。视觉设计见
[intent-to-effect-flame-graph.md](intent-to-effect-flame-graph.md)，
实验证据与 claim 边界见
[../visexp/paper/evaluation-claims-setup.zh-CN.md](../visexp/paper/evaluation-claims-setup.zh-CN.md)。

## 动机

Flamegraph 的本质能力是同类事物的递归嵌套：每一帧在更细的粒度上回答
「为了什么在做这件事」，深度不限。CPU 栈因为代码天然递归而白拿这个结构。
当前 agentpprof 的语义轴只有一层：prompt 打完标签，下面直接跳到机制帧
（call/tool/path）。一个「写代码」intent 底下的 explore → edit → test → fix
子结构被完全压平，flamegraph 只有一层语义可钻。

真实的 agent 工作是递归的：一个 intent 分解为多个 subtask，subtask（例如
subagent）内部还有自己的计划。模型应该表达这个结构。

## 模型

**定义 1（operation，操作）。** 操作是执行历史中任意粒度的一次可计量
活动：一个 intent、一个 subtask、一次 LLM 调用、一次 tool call、一个
process、一次 syscall 级的文件/网络效果，都是操作。每个操作携带属性
元组和可加度量（token 数、持续时间、CPU 时间、次数）。观测到的最细
粒度操作构成按时间排序的序列 O = [o₁, …, oₙ]；粗粒度操作包含细粒度
操作。

**定义 2（operation tree，操作树）。** 操作树 T 是有根树，**每个节点都
是一个操作**，父子边表示包含。树是同构的：intent 包含 subtask，subtask
包含 tool call，tool call 包含 process，process 包含子 process 和效果，
可以无限递归。区别只在**边的来源**：

- **切段边**（不确定，需推断或规则）：intent → subtask 等语义分组；
- **调用边**（事实，日志记录）：prompt → LLM 调用 → tool call；
- **血缘边**（事实，系统观测）：tool call → shell → 子进程 →
  文件/网络效果（eBPF 进程树或时间跨度包含）。

操作栈由树派生：σ(o) = root 到 o 的路径。不再有独立的「机制帧」概念，
process 链、路径、域名本来就是路径上的操作节点。栈不是第一性抽象，
树才是。

**定义 3（segmenter，切段器）。** 切段器负责生成树中所有**切段边**：
seg: O → T 的语义分组部分。调用边和血缘边是观测事实，不需要切段器。
切段器可插拔：边界**不**与 session/prompt/tool 等任何特定事件类型强
绑定，那些只是某种切段器的证据来源。

**定义 4（view，视图）。** 与现有模型相同：V = (φ, σ, w)，φ 选择操作，
σ 读出树路径，w 给权重；求值产出 folded stacks。视图层不感知树是怎么
建出来的。由于内部节点也是操作，w 可以取「自身度量」（process 自己的
CPU 时间）或「聚合子树」，对应 flamegraph 的 self/total 语义。

这个模型把两个工具统一成一棵树：agentpprof 从日志恢复上半棵
（intent → subtask → tool call），AgentSight live capture 用 eBPF 观测
下半棵（process → 效果），两者在 tool call 节点拼接（血缘边，R114 一系
实验验证的正是这个拼接）。当前已发布的 agentpprof = 「以 prompt 标记做
深度-1 切段，process 链作为帧内联」这一特例。

## 两个对称的难问题

工具的管线里只有两个非平凡问题，且互为对偶：

- **切段（segmentation）**：哪里到哪里是一个单元？→ 产出树结构
- **标注（labeling / 意图识别）**：这个单元在做什么？→ 产出节点标签

两者都是从非结构化 trace 到结构的映射，都需要同一组后端谱系：

| 后端类型 | 标注侧（已有） | 切段侧（提案） |
| --- | --- | --- |
| 确定性规则 | regex `--tag-rule` | 标记切段 + 用户 `--span-rule` |
| 模型推断 | 本地 LLM 标签器 | LLM 判段边界（研究方向） |
| 无监督 | TF-IDF + K-Means 聚类 | 变化点检测 / 序列聚类 |

递归 = 在每一层交替执行切段和标注：切出 span → 给 span 打标签 → 在
span 内部继续切。

**推断切段是必需后端，不是可选项。** 理由与 LLM 标签器对称：很多 trace
没有显式标记（非主流 agent、裸 API 循环）；即使有标记，有趣的结构也常常
比任何标记更细（一个 prompt 内的多个阶段）；推断结果可以像 LLM 标签
蒸馏成 regex 规则一样，蒸馏成可复现的 span 规则。

## 切段证据来源（按强度排序）

确定性标记切段器可用的证据，从强到弱：

1. **Subagent 调用**：Claude Code 的 subagent 写独立 session 文件且有派生
   关系（R170 中 77 个），是数据里已有的真 subtask，无需推断。当前实现把
   它们当平级 session；第一步就是嵌套回父 prompt 的 span 内。
2. **Agent 自己声明的计划**：TodoWrite / update_plan 的 item 内容加
   pending → in_progress → completed 状态转换，是 agent 亲口声明的 subtask
   边界。当前 parser 仅归类为 `category:"plan"`，内容被丢弃。
3. **用户 prompt**：当前唯一使用的边界（parser 的 `current_prompt_index`
   游标，时间跨度包含语义）。
4. **LLM call 标签升级为 phase**：连续同标签的 LLM 调用合并成一个 phase
   span，零新数据。
5. **推断切段**：对事件序列做变化点检测或聚类（特征：工具类别、触碰
   路径、call 标签、时间间隔）。

用户 `--span-rule` 可以覆盖或补充以上任何一层。

## 实现现状与差距

| 模型组件 | 现状 | 需要的改动 |
| --- | --- | --- |
| 操作序列 | `agent-session` 已产出 | 无 |
| 切段器 | 硬编码在 parser（prompt 游标） | 提出 `Segmenter` 接口；标记/规则/推断三实现 |
| 操作树 | 不存在（`prompt_index` + `process_chain` 扁平内联为帧） | `SessionRecord` 增加 span 层；subagent 挂回父 span；process 链成为节点 |
| 标注 | 标签器只标 prompt/LLM call | 推广为标注任意 span 节点（接口不变） |
| σ | 各视图硬编码帧序列 | 改为读树路径 |
| 视图 | `ProfileView` 四个内置 | 不变 |

演进顺序建议：subagent 嵌套（证据最硬、改动最小）→ todo/plan span →
`Segmenter` 接口 + `--span-rule` → 推断切段。

## 评估影响

- 语义轴加深会降低栈合并率（同一 intent 下各 session 的 subtask 序列不同），
  是经典的宽度换深度权衡；R224 类 mixed-weight 消融需按深度分层重跑。
- 切段质量成为独立于标签质量的新 claim：边界 adequacy 需要自己的 oracle
  （类比 C6 的标签 adequacy），推断切段的边界尤其需要人工或标记对照评估。
- todo/plan 文本仍是自由文本，复用意图识别层打标签。
- 时间包含近似在 subtask 层误差更大（todo 状态转换与工具调用不严格对齐），
  与 live-capture 精确血缘（R114 一系）的关系需要明确：血缘可用时应优先于
  时间包含。
