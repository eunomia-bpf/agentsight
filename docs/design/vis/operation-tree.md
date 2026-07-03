# Operation Stack：语义 profiler 的递归模型

状态：设计提案（2026-07）。当前 `agentpprof` 已实现本模型的第一步：
`--stack` 可任意选择 operation stack，`--stack-rule` 可把线性轨迹递归
折叠成 task/subtask/phase 等多层；本文描述完整目标模型和后续演进路径。
视觉设计见
[intent-to-effect-flame-graph.md](intent-to-effect-flame-graph.md)，
实验证据与 claim 边界见
[../visexp/paper/evaluation-claims-setup.zh-CN.md](../visexp/paper/evaluation-claims-setup.zh-CN.md)。

## 动机

Flamegraph 的本质能力是同类事物的递归嵌套：每一帧在更细的粒度上回答
「为了什么在做这件事」，深度不限。CPU 栈因为代码天然递归而白拿这个结构。
早期 agentpprof 的语义轴只有一层：prompt 打完标签，下面直接跳到机制帧
（call/tool/path）。一个「写代码」intent 底下的 explore → edit → test → fix
子结构会被压平，flamegraph 只有一层语义可钻。当前实现已经把 stack
构造改成可配置 operation stack：用户可以保留 prompt，也可以去掉 prompt，用
`task,subtask,phase` 把多个 prompt 或单个 prompt 内事件折成
任意深度的语义层。

真实的 agent 工作是递归的：一个 intent 分解为多个 subtask，subtask（例如
subagent）内部还有自己的计划。模型应该表达这个结构。

## 模型

**定义 1（operation，操作）。** 操作是执行历史中任意粒度的一次可计量
活动：一个 intent、一个 subtask、一次 LLM 调用、一次 tool call、一个
process、一次 syscall 级的文件/网络效果，都是操作。每个操作携带属性
元组和可加度量（token 数、持续时间、CPU 时间、次数）。观测到的最细
粒度操作构成按时间排序的序列 O = [o₁, …, oₙ]；粗粒度操作包含细粒度
操作。

**定义 2（operation stack，操作栈）。** 操作栈是把一个 operation 投影成
有序 frame 序列的函数 σ(o) = [f₁; f₂; …; f_k]。frame 可以直接来自
operation 字段，也可以由 `--stack-rule FRAME:LABEL=REGEX` 从 operation
字段中计算出来。prompt、session、tool call、process、path、domain 都不是
独立抽象，只是 operation 或 operation stack frame 的一种取值。

因此完整求值只有一个形式：

```text
eval(φ, σ, w, O) = { (σ(o), w(o)) | o ∈ O, φ(o) }
```

`--view` 选择 φ 和 w，即采样哪些 operation、用什么权重；`--stack` 和
`--stack-rule` 选择 σ，即 operation stack 怎么递归折叠。切段、标注、
血缘拼接、process 展开都只是产生 operation 字段或 stack frame 的机制，
不是额外的核心抽象。
`operations` view 是最通用的 operation-count 查询，适合本地 trace 和
第三方 normalized operation JSONL；`tokens`、`files`、`network`、`time`
只是更具体的 φ/w 预设。

## 两个对称的难问题

工具的管线里只有两个非平凡问题，且互为对偶：

- **切段（segmentation）**：哪里到哪里是一个单元？→ 产出树结构
- **标注（labeling / 意图识别）**：这个单元在做什么？→ 产出节点标签

两者都是从非结构化 trace 到结构的映射，都需要同一组后端谱系：

| 后端类型 | 标注侧（已有） | 切段侧（提案） |
| --- | --- | --- |
| 确定性规则 | regex `--tag-rule` | operation stack rule `--stack-rule` |
| 模型推断 | 本地 LLM 标签器 | LLM 判段边界（研究方向） |
| 无监督 | TF-IDF + K-Means 聚类 | 变化点检测 / 序列聚类 |

递归 = 在每一层交替执行切段和标注：切出 span → 给 span 打标签 → 在
span 内部继续切。

**推断切段是必需后端，不是可选项。** 理由与 LLM 标签器对称：很多 trace
没有显式标记（非主流 agent、裸 API 循环）；即使有标记，有趣的结构也常常
比任何标记更细（一个 prompt 内的多个阶段）；推断结果可以像 LLM 标签
蒸馏成 regex 规则一样，蒸馏成可复现的 span 规则。

## Stack Frame 证据来源（按强度排序）

`--stack-rule` 和未来推断后端可用的证据，从强到弱：

1. **Subagent 调用**：Claude Code 的 subagent 写独立 session 文件且有派生
   关系（R170 中 77 个），是数据里已有的真 subtask，无需推断。当前实现仍把
   它们当平级 session；下一步应把它们作为 operation 字段或 stack frame。
2. **Agent 自己声明的计划**：TodoWrite / update_plan 的 item 内容加
   pending → in_progress → completed 状态转换，是 agent 亲口声明的 subtask
   边界。当前 parser 仅归类为 `category:"plan"`，内容被丢弃。
3. **用户 prompt**：parser 的 `current_prompt_index` 游标提供时间跨度证据，
   但 prompt 只是 operation 字段，不是固定边界。
4. **LLM call / tool 标签升级为 phase**：同一 prompt 内按 LLM 标签、
   tool effect/category 的变化检测 phase，零新数据。当前实现已把
   这一步泛化成 operation stack frame：phase 只是默认 frame，用户可定义 task、
   subtask、intent 等任意递归层。
5. **推断切段**：对事件序列做变化点检测或聚类（特征：工具类别、触碰
   路径、call 标签、时间间隔）。

用户 `--stack-rule` 可以覆盖或补充以上任何一层。

## 实现现状与差距

| 模型组件 | 现状 | 需要的改动 |
| --- | --- | --- |
| Operation | `agent-session` 已产出 prompt、LLM call、tool/effect 等 operation 字段；`--operation-file` 可直接读取第三方 normalized operation JSONL | 继续补齐 plan、subagent、process/syscall 字段和更多第三方转换器 |
| Operation stack | `agentpprof` 用 `--stack` 和 `--stack-rule` 从 operation 字段生成任意深度栈，本地 session 和外部 operation JSONL 共用同一求值路径 | 增加更多内置证据后端和推断式 rule 生成 |

演进顺序建议：subagent 嵌套（证据最硬、改动最小）→ todo/plan span →
更强的 `--stack-rule` 预设 → 推断式 stack rule 生成。

## 评估影响

- 语义轴加深会降低栈合并率（同一 intent 下各 session 的 subtask 序列不同），
  是经典的宽度换深度权衡；R224 类 mixed-weight 消融需按深度分层重跑。
- 切段质量成为独立于标签质量的新 claim：边界 adequacy 需要自己的 oracle
  （类比 C6 的标签 adequacy），推断切段的边界尤其需要人工或标记对照评估。
- todo/plan 文本仍是自由文本，复用意图识别层打标签。
- 时间包含近似在 subtask 层误差更大（todo 状态转换与工具调用不严格对齐），
  与 live-capture 精确血缘（R114 一系）的关系需要明确：血缘可用时应优先于
  时间包含。
