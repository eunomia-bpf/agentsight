# Repository Nebula：目标设计与算法约定

Repository Nebula 回放 Agent session 中可证明的 Git 仓库文件动作时间，而不是 commit
时间。图中只有文件星点；目录只影响颜色和力场，不产生节点、边界或标签。commit
不会移动文件；某一动作帧覆盖到 commit 时，只让最外框闪烁。

本文只定义目标数据契约、算法和用户体验，不记录当前实现进度；实现状态在代码和测试
中维护，不能反向改变本文约定。

## 设计目标与核心场景

- 用全部 Agent session action 驱动时间轴，回放跨 session 的仓库长期演化。
- 文件是唯一节点；目录用稳定色系和群体力表达，位置随行动动态平衡。
- read/write/create/rename/delete 改变文件的短期视觉状态和长期结构状态。
- Agent 的有序文件动作形成可追踪的空间轨迹，而不是一组无顺序的热点。
- 同一份布局生成单 HTML、SVG、PNG、GIF 和 MP4，便于分享与嵌入 Agent report。
- 从已有结构化 action 识别 skill/harness 的候选低效模式，不依赖额外语义标签。

### 核心用户场景原话

> 我最近许多个软件开发和 auto research 的实验，都是开头设置好简单的目标和 idea，
> 让一个 Agent 在一个 repo 里面自我迭代 2–3 天时间，我再回来看一眼。我想要在 30s 内
> 理解 Agent 大致做了什么，迭代改进了什么文件，是怎么迭代改进的过程。比如说它是
> 根据什么样的做法去迭代代码，是先测试还是先写代码，主要改了什么模块，在论文还是
> 代码上面花的时间多，热点是什么。
>
> 我还在想具体怎么做。大概的思路是按 Agent 的真实读写时间回放仓库演化：文件是星点，
> 目录用稳定色系聚类，访问触发短暂亮起与放大，新建、重命名、删除改变星域结构，
> Git commit 作为外框闪烁的里程碑。它的价值是把长期运行 Agent 原本不可读的事件日志
> 压缩成可观察的软件生长过程，让人直观看到 Agent 的注意力如何移动、代码如何形成，
> 以及异常反复、遗忘区域和结构漂移发生在哪里。
>
> 现在 vibe coding 用得越来越多。很多代码由 AI 写完之后，人也不太管，不知道它中间
> 写了什么。除了结果的测试和功能验证，写的过程中是不是也应该记录以后可以回放的
> 编写轨迹：写这个代码的意图，尝试过什么，失败的原因是什么，当初踩过什么坑，后来
> 怎么避免，以及过程中有什么反思。
>
> 然后我也可以看到，是不是我的 skill 设计不合理，导致一些步骤过于复杂、不合理。
> 比如要求 Agent 记录了一堆文档，但实际上几乎不会回头看；或者 skill/harness 设计
> 不合理，导致 Agent 花了大量时间迭代无意义的垃圾测试用例，却不去写代码。

### 场景总结

这是一个“人离开、Agent 连续工作数日、人回来后快速恢复过程理解”的场景。用户不只
验收最终 diff 和测试结果，还需要理解四类过程事实：

1. **软件如何生长**：哪些文件和模块被创建、修改、迁移、删除，热点如何变化；
2. **Agent 如何行动**：注意力如何移动，探索、实现、测试和返工按什么顺序发生；
3. **资源投向哪里**：代码、测试、论文和文档分别占多少可观察 action 与活跃执行时间；
4. **工作方法是否合理**：是否出现文档低回读、垃圾测试空转、重复探索、验证滞后，
   以及这些现象是否与某个 skill/harness 边界相关。

文件行动轨迹先提供可由 session action 和真实读写直接证明的部分。意图、尝试、失败
原因、避坑和反思保留为后续语义层需求；加入时必须引用原 session 证据，不能从文件
移动模式自动猜测。

上述快速理解时限只是场景举例，不映射为快照数量、播放时长或实验门槛。本文先定义
文件行动轨迹和可由现有 action 直接计算的诊断；意图、失败原因和反思等语义标签后续
作为独立可选层附加。

## 用户入口

```bash
agentsight vis [PATH] --global \
  -o output/repository-nebula.html \
  -o output/repository-nebula.svg \
  -o output/repository-nebula.png \
  -o output/repository-nebula.gif \
  -o output/repository-nebula.mp4
```

重复 `-o` 会共享一次 session 扫描和一次布局计算。HTML 是可离线分享的单文件，
内含播放按钮和进度条；SVG 是星图图层的矢量版本；PNG 是最终帧；GIF 和 MP4
包含相同数量、相同顺序的布局帧。

## 统一数据流

可视化复用 `agent-session` 已有的 `RepositoryEvent` 和 `FileAction` 投影，只给现有类型
补充布局所需的 Tool 元数据和可选证据字段，不再定义新的通用事件抽象：

```text
RepositoryTrace = {
  events: [RepositoryEvent],
  commits_ms,
  initial_files?: [{ path, file_identity? }],
  observation_completeness: {
    native_sessions: complete | partial,
    system_files: complete | partial | unavailable,
    unbound_system_observations,
    notes
  }
}

RepositoryEvent = {
  id, ts_ms, session_id, vendor,
  tool?, category?, command_name?, status?,
  start_ms?, end_ms?, skill_scope?,
  actions: [FileAction]
}

FileAction = {
  access, path, previous_path?, bytes?, evidence: [Evidence]
}

Evidence = {
  source: native_tool | system_observation | command_derivation,
  count?, first_ms?, last_ms?
}

Claude/Codex/Gemini sessions ─┐
                              ├─ agent-session RepositoryTrace
AgentSight optional file observations ─┘     │
                                             ▼
                                  JS 状态更新与动态布局
                                             │
                                             ▼
                                      layout snapshots
                                   ┌─────────┼─────────┐
                                   ▼         ▼         ▼
                                 HTML     SVG/PNG   GIF/MP4
```

`RepositoryTrace` 是 `agent-session` 已有的仓库外壳；`initial_files` 是观测开始时
保存的 manifest，`observation_completeness` 记录 action、路径和 system observation
的已知缺口。下文的 action 指一个与 Agent Tool 事件一一对应的 `RepositoryEvent`；即使
`actions=[]` 也保留该 event，以维持 session 操作与布局快照的一一对应。

Agent 原生文件工具、可证明路径的命令动作和 AgentSight 文件观察都合并进所属
`RepositoryEvent.actions`。系统观察通过 Tool 执行区间和进程子树绑定到 event；无法
绑定的观察不创建另一条时间轴。`evidence` 只保留来源，渲染层不维护“Agent 意图”和
“系统效应”两套节点、轨道或中间 IR。
无法绑定的系统观察只增加 `unbound_system_observations` 并写入 completeness notes，
不改变星域状态。

合并顺序固定为：先把同一 Tool 执行区间和进程子树内、同一文件身份、同一 operation
的全部成功系统调用聚合成一个 burst；再用 `(file identity/normalized path, operation,
previous_path)` 与原生 Tool 路径去重。重复项合并次数、字节和 evidence 来源集合，不能
重复增加访问次数、重要性、注意力、空间焦点或目录转移。无法恢复稳定文件身份时使用
规范化仓库相对路径；rename 同时比较旧路径和新路径。

布局输入通过内存直接传给 JS；HTML 内嵌动作和布局数据，其他格式消费同一批快照。
生成过程不落地临时 JSON/IR 文件。帧较多时同时流式写入 HTML 帧数据和媒体编码器，
以性能和增量编码处理长历史，而不是删除或合并 action。

## 观测边界

默认同时发现并读取所有可用 Claude、Codex 和 Gemini session，不要求用户逐个选择
Agent 或 session。数据直接来自 `agent-session` 已有的解析器。每个 Tool
事件只增加一个很薄的路径事实：原始路径及 `read/write/create/delete/rename`
访问类型。可视化不会复制 prompt、代码正文、网络内容，也不构造额外的通用 IR。

路径按 session cwd 解析，并且必须落在目标 Git 仓库或同一仓库的 worktree 中。
Gemini session 用其 `projectHash = sha256(cwd)` 恢复 cwd；有明确失败结果的工具调用
仍保留为 action。缺少系统证据时，仅由失败 Tool 参数推导的路径不改变文件生命周期；
system observation 已证明成功的 read/write/create/rename/delete 仍必须保留，因为命令
可能先产生文件副作用，再以失败状态结束。具体投影规则是：失败 Tool 的参数推导路径
不写入 `RepositoryEvent.actions`，event 可以保持 `actions=[]`；同一 event 中系统已证明
成功的 `FileAction` 正常驱动生命周期、重要性、注意力、焦点和波纹。
存在起点 manifest 时，读操作只保留该 manifest 或此前 action 已创建/重命名的文件；
缺少 manifest 时，native Tool 或 system observation 明确证明的仓库内 read 可以创建
first-observed 节点，只有命令文本推测而没有明确路径证据的 read 不进入星域。任务结束
时的 worktree 不能用于起点 allowlist。写操作允许新文件在首次 commit 前出现。
`.git`、`node_modules`、`target` 和 `.cache` 不进入星域。
`--global` 会搜索 Claude/Codex JSONL（含 Codex 归档）和 Gemini JSON；即使 session
原本属于其他项目，只要绝对路径指向目标仓库也会收录。若外部 session 只留下相对
路径且没有可恢复的 cwd，则无法证明其所属仓库，因而不会猜测或收录。

仅由原生 session 得到的 shell 动作来自高置信度命令参数推导，并不等价于文件系统
观察：脚本内部自行产生的文件变化可能不可见。存在 AgentSight 文件观察时，它只补充
同一个 `FileAction` 的路径和 evidence。Bash、网络和 LLM 本身都不伪装成文件节点。

## 时间与帧

动作按 `(ts_ms, session-id, event ordinal)` 排序。同一 Tool 事件中的多个
文件动作属于同一个动作步。每个 Agent action 产生一个布局快照；没有仓库文件动作的
action 也保留一个状态不变的快照，使进度条与 session 操作一一对应。HTML、GIF 和
MP4 使用全部快照，不合并、不抽帧、不设置快照总数上限。播放速度只改变观看速度，
不改变动作与帧的对应关系。

时间轴从第一个 Agent action 开始，到最后一个 Agent action 结束。进度条按动作序号
推进；墙钟时间只在详情中显示，不把 session 间长时间空档扩成空白帧。跨 session
保留仓库状态和长期重要性，但短期注意力与轨迹在新 session 开始时重新建立。session
边界只在进度条上显示一个细刻度，不增加星点、连线或大块提示。

commit 不定义时间轴起点、终点、布局或文件状态。对位于观测 action 时间范围内的
commit，在第一个满足 `action.ts_ms >= commit_ms` 的快照让最外框闪烁；因此落在两个
action 之间时属于后一个 action，时间戳相等时属于该 action。范围之外的 commit 不进入
回放。

事件 ID 和动作路径的最终比较沿用浏览器 `localeCompare()`；目录色板和路径树内部使用
JavaScript 默认字符串排序。ASCII 路径在固定 Chromium 环境中可复现，Unicode 路径的
跨 ICU/locale 位序不作保证。未来若统一更换为 code-point 排序，必须作为带 golden
snapshots 的显式视觉迁移。

## 文件生命周期

- 第一次 read/write 会让文件从相近路径附近进入力场。
- create 使用绿色扩散环；write 使用橙色双波纹；read 使用白色注意力环。
- rename 在目标动作中显式保存来源路径；同一 Tool 事件的多组 rename 各自配对，
  并保留原节点的速度、访问次数和重要性，只切换路径与目录颜色。
- delete 使用红色退出环，经过 6 个动作步渐隐后从力场删除。
- 目录永远不是星点。

新文件依次寻找最近的可见对象：同一父目录、最长公共目录前缀、同一顶层目录，
都不存在时才从仓库中心附近出生。出生角度由路径哈希决定，不使用系统随机数。

只有完整观测确实从空 worktree 建立前开始时，动画才从零文件逐个生长。仓库早于观测
窗口时，只能使用观测开始时保存的 `initial_files` manifest，把其中的文件作为低亮度
pre-existing stars 一次性载入；任务结束时的 worktree 不能倒灌为起点，否则会让未来
文件提前出现。缺少起点 manifest 时，文件只在首次观察到 read/write/create 时出现，
并标记为 first observed，不宣称是真实出生。初始状态不从 commit 历史合成，也不改变
action 时间轴。

## 颜色

顶层目录按排序后的目录名分配 OKLCH 色相，相邻目录以黄金角 `137.508°` 分离。
稳定仓库身份和目录路径共同决定初始色相，不使用 Git revision。子目录在父目录色相
附近做稳定的小幅变化，并随深度提高亮度、降低色度；因此目录相近的文件颜色相近，
但没有可见目录边界。

rename 或从父节点附近出生时，颜色在 6 个动作步内从旧颜色过渡到目标目录颜色。

## 长期重要性与短期注意力

长期重要性与短期注意力相互独立。

长期重要性在每次访问时增加：read `+1`、write `+2.5`、create/rename/delete
`+4`；首次被一个新 session 访问再加 `1.5`。其半衰期为：

```text
H_importance = clamp(round(total_action_steps × 0.08), 240, 2400)
I_raw(f,t) = I_raw(f,t_prev) × 2^(-(t-t_prev)/H_importance)
             + gain(operation_t) + session_novelty(f,t)
```

所有 action step（包括没有文件动作的 step）都推进 importance 和 attention 的 age；
只有文件动作增加 gain。显示前再用当前可见文件的 P95 做稳健归一化。先对全部
`I_raw` 升序排序，使用 nearest-rank `ceil(0.95 × visible_file_count)` 对应的值，并把
尺度下限设为 1：

```text
P95_scale = max(1, nearest_rank_P95(I_raw(*,t)))
importance(f,t) = clamp(log1p(I_raw(f,t)) / log1p(P95_scale), 0, 1)
```

没有可见文件时跳过归一化和渲染。

长期重要性控制静态大小、亮度、目录中心吸引力和目录整体位置。很久未访问的文件
逐渐变小、变暗、变密集，但不会因为单个重要文件而脱离其目录星域。

短期注意力只控制瞬时放大、发光和波纹。先把每个有文件动作的 action 映射到权重最高
的前两级目录，再统计同一 session 内“连续停留在同一目录”的 action run 长度集合
`R`；`R` 是保留重复值的完整列表，不是去重后的 set。没有文件动作的 action 结束当前目录 run；多个目录操作权重并列时按稳定目录路径
排序选择。半衰期使用这些 run 的中位数，与 Agent 在该次工作中的实际局部停留节律
对齐：

```text
H_attention = max(1, median(R))
attention(age) = A_operation × 2^(-age/H_attention)
cutoff_age = floor(H_attention × log2(1/epsilon_attention))
```

read、write、create、rename 的初始强度分别为 `0.35/0.75/1.0/0.8`，随后按动作步
指数衰减。默认 `epsilon_attention = 1/16`；低于该可见阈值后停止绘制。没有可用 run
时令 `H_attention=1`。它不按真实分钟衰减，因此长时间无动作不会让当前注意力凭空
消失，也不使用固定的“最近 24 步”窗口。delete 不使用 `A_operation`，只使用退出环；
进入 delete 渐隐期的节点不施加 shape anchor。

## 目录份额与节点大小

顶层目录的原始权重为：

```text
weight = (file_count + 8)^0.4 × (0.8 + 0.2 × mean_importance)
```

顶层目录数 `D>0` 时，份额上限为 `min(1, max(0.42, 1/D + 0.08))`；`D=0` 时不计算
份额。小目录有伪计数保护，避免文件数差异直接造成面积悬殊。文件静态直径随总文件数
缩放到 `0.85–6 px`，
再乘目录单元尺度和重要性；被访问时最多放大到 `10.5 px`。

## 力场

布局使用 `d3-force` 的 velocity-Verlet 模拟，所有随机扰动使用仓库、路径和
动作步的固定哈希种子。每个快照按以下顺序执行：

1. 应用 create/read/write/rename/delete 动作并更新重要性；
2. 按顶层目录计算受限面积份额，并按前两级目录建立隐形簇；
3. 同父目录文件按稳定路径顺序组成不可见的 4 叉路径树弹簧，同顶层目录的父目录代表
   再组成较弱的 4 叉路径树；这里的路径树不是 Barnes–Hut 的空间四叉树；
4. 文件执行 Barnes–Hut 多体斥力和圆形碰撞；
5. 顶层目录簇互斥，子目录簇向所属顶层目录中心吸引；
6. 相邻 action 经常连续触达的目录中心产生饱和的弱引力；
7. 重要文件提高所属目录簇的整体质量，目录整体随重要性向画布中心移动；
8. 使用上一快照的目录中心和内部相对位置约束无关跳动；
9. 速度使用 `0.38` 阻尼，并把节点约束在画布范围内。

目录弹簧和簇边全部不可见。节点数超过 `1000/500/200` 时，每个 action 快照分别执行
`1/2/4` 个 tick，否则执行 8 个 tick，以限制长历史成本。

### Agent 轨迹与目录行为关联

动作 `i` 的空间焦点是该 action 所有文件操作在当前布局中的加权质心：

```text
q_i = sum_f(w_operation(f) × position_i(f)) / sum_f(w_operation(f))
w_read/write/create/rename/delete = 1 / 2 / 2.5 / 2.5 / 2
```

焦点使用细环或局部光晕，从 `q_{i-1}` 平滑移动到 `q_i`，不画永久连线。最近焦点的
余辉使用和注意力相同的指数形式；默认 `H_trail=H_attention`，但状态独立，后续可按
跨帧轨迹追踪实验单独标定 `H_trail/epsilon_trail`。新 session 从第一个有文件动作的位置
重新出现。一个 action 同时触达许多文件时，每个文件分别产生操作效果，焦点只摘要
影响中心，并同时计算这些文件相对焦点的影响半径。没有文件动作的 action 保持上一个
焦点位置，不产生文件波纹。

同一 session 中前后相继的有文件 action 的目录分布形成时序邻近；中间没有文件动作的
action 保留在时间轴上，但不制造虚假目录：

```text
p_i(a) = action i 在目录 a 的操作权重 / action i 的全部目录操作权重
T_ab += p_i(a) × p_(i+1)(b)
degree_a = sum_b(T_ab + T_ba)
S_ab = (T_ab + T_ba) / sqrt(degree_a × degree_b)  # 两个 degree 都大于 0 时
A_ab = 1 - exp(-S_ab)
```

`A_ab` 只产生目录中心之间的弱力，所有目录分量都保留；文件不会被转移力单独拉出所属
目录。任一 degree 为 0 时定义 `S_ab=0`。路径引力表达静态结构邻近，`A_ab` 表达 Agent
行动的长期时序邻近。

### Temporal stability

每个文件跨快照保留 `(x,y,vx,vy)`。除此之外，显式限制目录内部形状和目录整体中心
在相邻快照间没有 action 依据的变化：

```text
r_prev(v) = x_prev(v) - C_prev(directory(v))
F_shape(v) = k_shape(v) × (C_current + r_prev(v) - x_current(v))
F_center(d) = k_center(d) × (C_prev(d) - C_current(d))

k_shape(v) = k_shape_base × (1 - attention(v))
activity(d) = clamp(max_{v in d}(attention(v)), 0, 1)
k_center(d) = k_center_base × (1 - activity(d))
```

当前活跃文件和目录降低锚定强度，允许 create、rename、delete、重要性和行为邻近推动
真实演化；未触达区域保持较强稳定。求解器把路径/目录引力、行为关联、碰撞、相对
形状稳定和目录中心稳定作为加权力混合逐 tick 迭代，不声称求得全局能量最优。稳定权重
需要同时用跨帧追踪正确率、单帧目录纯度、节点重叠和总位移选择。

create 的首帧没有上一位置，不施加 shape anchor；跨目录 rename 保留文件坐标和速度，
但从该帧起相对目标目录中心建立锚点；delete 渐隐期间继续参与碰撞，退出后同时删除
位置、速度和锚点状态。

## Skill / harness 过程诊断

这部分只使用 session 中可用的结构化 skill 边界、Tool action、命令结果和文件路径，
不增加意图、失败原因或反思等语义标签。路径先按仓库可覆盖规则分为 production code、
test、paper、docs、config 和 unknown；一个多文件 action 可以按操作权重分配给多个类别。
`category/command_name/status` 用于识别 test/build/lint，`start_ms/end_ms` 用于活跃时长，
`skill_scope` 只在原生 session 有结构化 skill 边界时填写。缺失字段对应的指标输出
unknown，而不是用模型猜测或用事件时间差补齐。

```text
artifact_action_share(kind) = kind 的文件操作权重 / 全部已分类文件操作权重
active_duration_share(kind) = kind 的 Tool 执行区间 / 全部已观测 Tool 执行区间
documentation_readback      = 后续再次 read 的已生成文档数 / 已生成文档数
test_only_churn_loops       = 只含失败验证、测试修改和再次验证的最大连续区间数
test_only_churn_actions     = 这些区间包含的 action 数
unverified_edit_span        = 最近成功 test/build/lint 后的 production write 数
recovery_cost(session)      = 新 session 首次 write 前对既有文件的重复 read 数
no_file_action_share(skill) = skill 边界内 files 为空的 action 数 / 该 skill 的 action 数
```

Tool 没有可靠 start/end 时只报告 action share，不用相邻事件的墙钟差冒充“花费时间”。
低文档回读和 test-only churn 是供人检查的候选摩擦，不自动等价于无价值：文档可能是
最终产物，测试迭代也可能发现真实缺陷。回放把这些区间映射回对应 action 和星域位置，
让用户直接核对是哪一个 skill、目录和循环造成的。

test-only churn 区间从一次失败的 test/build/lint 开始；后续只允许测试文件修改和再次
验证。成功验证、production code 动作或 session 结束时关闭区间。单次失败且没有测试
修改不计为 churn loop。

## 复杂度与确定性

设 action 数为 `N`，快照 `i` 的可见文件数为 `V_i`，目录簇数为 `D_i`，该 action
触达的目录数为 `m_i`：

- action 排序为 `O(N log N)`；
- 目录时序邻近累计为 `O(sum_i(m_i^2))`，不丢弃 action 或目录分量；
- 每个 force tick 的文件多体力约为 `O(V_i log V_i)`；
- 目录簇成对斥力为 `O(D_i^2)`，目录很多时使用空间索引优化；
- 全部快照的输出数据量为 `O(sum_i V_i)`；生成器流式编码时常驻布局内存为
  `O(max_i V_i)` 加编码缓冲。

快照数始终等于 action 数，不设总数上限。相同输入使用稳定的事件、路径和目录排序，
以及仓库、路径和动作步的固定哈希种子。优化前后必须比较快照数、文件生命周期、目录
颜色、坐标容差和媒体帧数，而不是只比较最终 PNG。

## 渲染和编码

交互 HTML 使用 ECharts Canvas renderer。SVG 使用同一份 ECharts option 按需
渲染，因此坐标、大小、颜色和内容相同；抗锯齿可能与 Canvas 有细微差别。
PNG 直接来自合成 Canvas。MP4 通过浏览器 WebCodecs 和 Mediabunny 从这批 Canvas
帧编码；GIF 由同一个 MP4 转换，不重新计算布局。

长历史仍逐 action 输出全部帧。生成器边计算边编码并持续打印进度，不在内存中保存
全部位图；用户只请求 HTML 时不会启动媒体编码。输出体积和耗时随 action 数增长，
不能通过静默合并或删除快照来优化。

命令行必须打印 session 扫描、文件动作、帧进度、GIF 转换、输出大小和总耗时。
任何优化都不得改变动作排序、固定种子、目录颜色、力参数或快照数量；视觉回归保存
golden scene 并逐帧比较，媒体文件还必须用 `ffprobe` 证明帧数相同。

## 科研脉络与验证

### 软件演化可视化

Evolution Matrix、Githru 等工作展示了如何通过稳定空间表示软件历史，
但主要以版本或 commit 为时间单位。Repository Nebula 把最小时间单位改为 Agent
action：commit 之前的 read/write/create/rename/delete 顺序、注意力移动和跨 session
演化都成为可观察对象。

### 动态图与 temporal stability

动态图研究中的 mental-map preservation 关心相邻快照保持位置是否帮助用户追踪节点。
Archambault、Purchase 和 Pinaud 的实验发现 small multiples 总体更快，animation 在
识别新增节点/边时错误更少，而位置稳定性的总体影响有限。Beck 等人的综述也指出现有
证据依赖任务，并非“节点越固定越好”。因此本设计把 `k_shape/k_center` 作为实验变量，
同时衡量跨帧追踪正确率和单帧布局质量。

- [本地论文：Animation, Small Multiples, and the Effect of Mental Map Preservation in Dynamic Graphs](reference/2011-archambault-animation-small-multiples.pdf)
- [本地综述：The State of the Art in Visualizing Dynamic Graphs](reference/2014-beck-visualizing-dynamic-graphs.pdf)

### 可检验问题

1. 相比静态最终图和普通 Tool 时间轴，空间轨迹是否让用户更快、更准确地识别主要模块、
   热点迁移、反复探索和遗忘后重访？
2. `k_shape/k_center` 的什么取值能在跨帧追踪、目录纯度、节点重叠和真实结构变化之间
   取得较好的任务相关平衡？
3. 文档回读率、test-only churn、验证滞后和 recovery cost 能否准确定位人工确认的
   skill/harness 低效区间，而不是只反映任务类型？

验证应按仓库、任务和 Agent 分组，避免路径与 workload 泄漏。若图只能提高主观的
“看起来懂了”，却不能提高问题回答准确率或原始证据定位速度，则设计主张不成立。

## 参考资料

- Daniel Archambault, Helen Purchase, Bruno Pinaud. *Animation, Small Multiples,
  and the Effect of Mental Map Preservation in Dynamic Graphs*. IEEE TVCG, 2011.
  [HAL](https://inria.hal.science/inria-00472423v1)
- Fabian Beck, Michael Burch, Stephan Diehl, Daniel Weiskopf. *The State of the
  Art in Visualizing Dynamic Graphs*. EuroVis STAR, 2014.
  [VISUS](https://www.visus.uni-stuttgart.de/documentcenter/forschung/visualisierung_und_visual_analytics/eurovis14-star.pdf)
- Michele Lanza. *The Evolution Matrix: Recovering Software Evolution using
  Software Visualization Techniques*. IWPSE, 2001.
  [PDF](https://www.inf.usi.ch/lanza/PUBS/P/Lanz2001c.pdf)
- Youngtaek Kim et al. *Githru: Visual Analytics for Understanding Software
  Development History Through Git Metadata Analysis*. IEEE TVCG, 2021.
  [arXiv](https://arxiv.org/abs/2009.03115)
