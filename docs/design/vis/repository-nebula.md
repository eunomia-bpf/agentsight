# Repository Nebula：Agent 驱动的软件生长星云

状态：**Implemented candidate**。本文定义图的语义和视觉约束，并记录真实仓库产物的验证结果。

Repository Nebula 是一个单图、单文件的长期软件演化视图。它回答：

> 多个 Agent session 如何逐步发现、触达和修改一个 repository？

它不是依赖图、因果图、Git 历史回放或进程拓扑。主画面只有文件星点和无边界目录色云。

## 已实现的设计决定

1. **第一帧严格为空。** 播放从第一条真实 Agent 事件前 1 ms 开始；第一次文件动作发生前可以出现命令、进程或 domain-reference 脉冲，但没有文件星或目录云。
2. **默认发现所有支持的 Agent，但不默认扫描全局 transcript。** Claude、Codex、Gemini 使用 cwd/worktree/project hash/Git remote 的强身份证据归入 repository；显式 `--global` 才额外扫描其他本地 session，并只纳入真实 `tool_use/function_call` 中命中目标目录的 Tool 操作。prompt、assistant 正文和搜索结果中的普通提及不算。
3. **完整 repository 只作为低亮度上下文，不冒充 Agent 创建。** 第一次文件动作后，frozen endpoint 文件渐显为暗背景；真正触达的文件再按 Agent 时间点亮和运动。
4. **云上不放任何标签或边界。** 目录只由稳定颜色编码；路径仅在悬停文件星点时出现。
5. **最近注意力是瞬态。** read/write/command-associated file effect 按真实事件年龄衰减；累计访问只小幅改变常态亮度。
6. **Git 只提供软件边界和 durable reference。** 当前 tracked、Git lifetime 中出现过、或被 Agent 真实触达的 repository-relative 路径进入文件集合。Agent-observed untracked 路径保留但明确标记，不因缺少 Git lifetime 被丢弃。
7. **所有状态变化使用 Agent 时间。** Agent-associated Git add/delete/rename 可以改变生命周期效果，但发生在关联的 Agent event timestamp；commit timestamp 永远只闪最外层金色边框。

第三项用于同时满足两个需求：画面需要包含完整 repository，不能只有已触达文件；但初始空画布也不能把 endpoint 文件伪装成 Agent 当时创建的文件。

## 仓库已有研究与本图的相邻项目

仓库已经有完整的七类历史可视化、closest work、工具基线和来源核验，不在本文复制一遍。全量调查见 [Background And Related Work](../../background-related-work.md)，单文件交付约束见 [Single-artifact software evolution views](evolution-atlas.md)。本节只保留会直接改变 Repository Nebula 设计的比较。

| 项目 | 已验证的承重机制 | 本图借用 | 本图明确不借用 |
|---|---|---|---|
| [mindwalk](https://github.com/cosmtrek/mindwalk) | 将 coding-agent session 规范化为 file-touch trace，并在确定性 repository citymap 上回放；读、写和编辑以不同 glow 表达 | Agent 事件作为播放主时钟；同一 repository 跨 session 保持稳定空间；最近触达衰减；本地生成 | 3D 摄像机、单 session 重置、永久 deepest-touch 染色、HUD/评价面板、目录文字和关系线。Nebula 要表现的是多 session 累积生长与移动中的注意力，不是 session viewer |
| [Gource](https://gource.io/) / [code_swarm](https://doi.org/10.1109/TVCG.2009.123) | 用发光、运动、衰减和压缩时间把版本历史变成可观看的视频 | 短暂高亮后回落、事件间空档压缩、GIF/MP4 作为一等输出、新对象从既有局部结构附近进入 | commit 作为主时钟、开发者节点、文件到人的吸引线、随机自由漂移。它们的“活”要保留，但主体改成 Agent 的真实文件动作 |
| [GitHub Next Repo Visualizer](https://githubnext.com/projects/repo-visualization/) | 把完整 repository 层级压成可辨认的视觉指纹，并生成可直接嵌入 README 的 SVG | Git-tracked 全文件上下文、稳定的 repository 指纹、单 SVG/PNG 易分享和嵌入 | circle packing 的硬边界、永久文件标签、以 endpoint 文件大小冒充演化。Nebula 的目录是连续色云，不是装箱图 |
| [CodeCity](https://doi.org/10.1145/1370175.1370188) | 用稳定位置建立 locality 和 repository 心智地图 | 文件位置必须可记忆、跨格式和跨 session 可比较；视觉通道必须有明确语义 | 建筑、街道、3D 高度和导航。它们增加展示成本，却没有帮助看 Agent 注意力移动 |
| [EvoStreets](https://doi.org/10.1145/1879211.1879239) / [Software Cartography](https://doi.org/10.1002/smr.414) | 演化图必须维持 mental map；新增元素应在既有结构上增量布局，而不是每帧洗牌 | 新星从路径相近的旧星附近派生；旧星位置具有高稳定权重；目录层级决定局部邻域 | 让 commit 版本重排城市、把创建年份编码成街道、用语义降维覆盖目录结构。第一版以路径邻近为可解释的“相近” |
| [RECAP](https://arxiv.org/abs/2605.01104) | 聊天、编辑过程和持久结果需要联合观察，单看 Git 无法恢复过程 | 保留 recorded process 与 durable Git 的证据边界；不把“触达”升级成“创建/作者” | 编辑器专用 replay UI 和 shadow history。Nebula 仍是一张文件空间图，不扩张成完整会话审查器 |

### 可直接复用的实现机制

- 继续复用现有 tree-shaken ECharts SVG renderer：scatter、渐变、tooltip、单一 slider、SVG/PNG 截图和逐 cursor 重绘已经覆盖交付需求。
- 确定性碰撞和增量位置可用 [d3-force](https://d3js.org/d3-force) 的 `forceX/forceY`、`forceCollide` 和固定 tick 数实现；只有在产物体积与代码量实测小于自写迭代器时才加入该模块，不引入完整 D3。
- [d3-contour density](https://d3js.org/d3-contour/density) 可以计算二维核密度，但直接输出的是 contour polygon，会重新引入用户已否决的云边界。因此第一版仍用有限 radial-gradient lobes 近似连续密度场；若视觉检查显示明显“一个文件一个圆”，再只复用其 KDE 计算而不画 contour 边。

这组比较给出一个清楚的差异：Repository Nebula 不是“二维版 mindwalk”或“Agent 版 Gource”。它保留两者可观看的事件回放，但把空间固定在 Git 管理的 repository、把时间改成跨 session 的 Agent 真实动作、把分享单位缩成一个图文件，并严格区分注意力、文件存在和 Git 结果。

## 非目标

Repository Nebula 明确不做：

- 不画文件之间的连线。
- 不画 session 轨迹折线、依赖边、read→write 边或因果边。
- 不把进程、命令、domain 或模型画成参与文件布局的节点；无路径事件只能产生短暂 ambient marker。
- 不让 commit 创建、删除、移动或缩放文件。
- 不把首次看到文件直接写成“创建文件”；只有 Agent-associated durable `A` 才显示候选 create 环。
- 不根据 endpoint 文件大小伪造历史文件大小。
- 不从 shell 动词猜测 create/delete/rename，也不把命令路径称为“命令生成文件”。生命周期只来自 Git status 与 Agent event 的候选关联。
- 不引入第二套可视化事件 IR。
- 不依赖统一 dashboard 或服务器。

依赖、因果、session 路径等关系继续由独立单图承担，不能塞回 Nebula。

## 数据输入

直接复用 `agent-session` 的现有抽象：

```text
SessionSummary
NormalizedEvent {
  ts_ms
  session_id
  vendor
  kind
  action
  category
  effect
  paths
  write_paths
  process_chain
  domains
}
```

Repository 只补充 frozen endpoint、Git lifetime 和稳定布局种子：

```text
EndpointFile {
  path
  top_level_directory
  subdirectory
  stable_seed
  git_scope             // tracked now or tracked in selected history
}

Agent-associated Git status 只作为 event 上的紧凑 `durable_changes` 字段进入视图，不建立第二套事件 IR。
```

这只是所选视图的紧凑字段投影，不是新的事件模型，也不写成用户需要管理的中间文件。

## 时间语义

### 全局时钟

当前 scope 中的 session、sidechain 和工具动作按真实 `ts_ms` 合并排序。默认 scope 是 repository identity；`--global` 再加入其他 session 对目标目录的真实 Tool 操作：

```text
t0 - 1 ms     空画布
t0            第一条 Agent 事件（可能没有文件路径）
tf            第一条 Agent 文件事件，第一颗星从画布中心出生
t1...tn        后续所有真实 Agent 事件
tn             最后一条 Agent 文件事件
```

后续 session 继承此前已经形成的文件宇宙，不重新清空。

进度条保存真实时间戳。自动播放可以压缩没有事件的长时间空档，但不生成虚构动作，时间标签仍显示真实时间。

### Commit

Commit 不参与文件布局和文件状态：

```text
commit timestamp -> artifact 外框短暂金色闪烁
```

commit 不会让星点出生、消失、移动、变大或改变颜色。若动画为了显示外框而采样一个纯 commit cursor，图内状态冻结在此前最近的 Agent-derived visual cursor；只有 commit 与真实 Agent event 恰好同一时刻时，图内状态才会同时前进。

此约束也适用于 gallery 中所有可播放视图：动画状态只在真实 Agent 操作时间上变化。Git-only 图可以作为指定 cursor 的静态结果图，但如果进入播放模式，commit 只能作为最外层 artifact flash，不能暗中成为第二套动画时钟。

## Git 文件范围

文件范围按以下优先级收口：

1. `git ls-files` 中当前 tracked 的文件。
2. 所选历史窗口内由 Git lifetime 证明曾 tracked、且被 Agent 事件真实触达的文件；这保留后来删除或改名的开发文件。
3. Agent 真实触达的 repository-relative 路径，即使最终没有 Git lifetime 也保留，并标为 observed untracked；tooltip 只能写 `first observed`，不能写 `created`。

以下文件默认排除：

- `git check-ignore` 命中的文件。
- `.git/`、dependency cache、build output、coverage、临时日志。
- 只在 prompt/assistant 正文中出现、没有真实 Tool 操作的路径。

这不是用 Git 驱动画面，而是用 Git 给完整软件边界去噪。Agent-observed untracked 文件不能因为 endpoint 或 lifetime 缺失而被静默丢掉。

### 第一帧

第一帧必须满足：

```text
files = 0
clouds = 0
labels = 0
edges = 0
```

不能把播放起点裁到第一条事件，否则第一帧已经出现文件。

## 两层文件语义

### Repository context layer

完整 frozen endpoint 文件集合用于建立空间背景。它在第一条 Agent 事件之后以很低透明度渐显：

- 表示“当前 repository 中存在、可被 Agent 访问的上下文”。
- 不表示文件在该时间点被创建。
- 不参与读写波纹。
- 默认不显示 tooltip 之外的文字。
- 被 Agent 首次触达后，原位置上的暗星升级为 observed star。

如果某个事件路径不在 frozen endpoint 中，例如临时文件或最终已删除文件，则它没有背景暗星，只在事件发生时进入 observed layer。

### Agent-observed layer

文件第一次出现在 Agent 事件中时进入 observed layer：

- 首次 `Read`：语义是 **discovered**。
- 首次 `Edit` 或其他 write effect：语义是 **first observed write**。
- 首次 `Write`：仍只写成 **first observed via Write**；只有同一 Agent event 关联到 Git `A` 候选时才增加 candidate create 环，仍不声称确定 authorship。
- 后续访问累计亮度和活动尺度。

当前版本使用 Agent event 与 Git lifetime/change 的候选关联显示 create/delete/rename 环；状态发生在 Agent event 时间，commit 仍只闪外框。它是 durable candidate，不是 OS 级文件系统证明，也不升级为 authorship。

## 目录颜色

颜色是目录的唯一显式编码。云上没有文字标签。

规则：

```text
色相 hue          = top-level directory
明度/饱和度微调   = subdirectory
透明度/密度       = 当前可见文件数量和 Agent 触达强度
```

例如 `docs/paper`、`docs/tmp` 和 `docs/figures` 必须属于同一色系，而不是三个无关颜色。

颜色必须由目录路径稳定决定：同一个 repository、同一个目录在不同 session、不同输出格式和不同播放时间中保持同色。

## 布局

### 目录层级布局

顶层目录先获得稳定的 cluster anchor。子目录在父 anchor 周围形成同色系子云。

布局不使用随机洗牌，也不直接把文件路径哈希成最终二维坐标。稳定 seed 只能用于同一 cluster 内的初始角度和微小扰动。

### 连续运动

浏览器保留上一帧位置，并以其作为下一事件帧的初态。每个事件步执行固定次数的确定性布局迭代：

```text
directory attraction  文件靠近所属目录云心
collision             文件星点不重叠
stability             已存在文件尽量保持上一帧位置
birth force           新文件从出生点缓慢进入目标位置
```

PNG/SVG/GIF/MP4 在指定 cursor 上从第一事件确定性重放到目标时间，因此同一数据、同一 cursor 得到相同布局。

### 新星出生点

新星必须从已经可见、路径最相近的旧星旁边派生，而不是从随机屏幕边缘飞入。候选只来自当前 cursor 前已经 observed 的文件，按以下信息排序：

1. 相同 parent directory。
2. 最长公共目录前缀。
3. 相同 extension/file kind。
4. 同一 session 最近触达，作为同分时的 tie-breaker。

若没有候选，出生点才回退到所属子目录云心，再回退到顶层目录云心。出生位置是父星当前位置加一个由新路径稳定 hash 决定的小偏移；随后通过 `birth force` 缓慢进入自己的稳定位置。旧星不会因为新星出现而大幅重排。

这只是视觉出生点，不升级为 provenance 或 create 结论。tooltip 必须使用 `first observed`。

## 连续色云

色云不是给每颗星套一个半透明圆，也不是 Voronoi、多边形或 territory 边界。

每个目录云由文件位置上的平滑核叠加形成密度场：

```text
density(x, y) = Σ Gaussian(file_position, bandwidth)
```

实现可以使用有限数量的径向渐变 lobe 近似密度场，但必须满足：

- 同目录的重叠光场看起来是一片连续云。
- 子目录继承顶层目录色相。
- 文件增加时云自然扩张、变浓。
- 文件位置移动时云跟随移动。
- 不出现每颗文件一个清晰可辨的大圆边界。
- 不出现任何文字标签。

## 文件视觉通道

| 视觉通道 | 语义 |
|---|---|
| 星点色相 | 顶层目录 |
| 星点常态明度 | 目录深度与累计 Agent 访问次数；二者都只允许小幅改变基线 |
| 星点大小 | 累计 observed activity 的对数尺度 |
| 极低透明度暗星 | frozen endpoint context，尚未被 Agent 触达 |
| 白色核心 + 细环 | 最近直接读取；按真实事件年龄衰减 |
| 暖色核心 + 向外扩散环 | 最近直接 Edit/Write；按真实事件年龄衰减 |
| 菱形核心 + 紫色波纹 | `agent-session` 记录的 command-associated path effect；明确不等同于 OS 级创建证据 |
| 金色 artifact 外框 | commit timestamp |

当前事件数据没有历史文件大小快照，因此不能把 endpoint bytes 当成过去每一帧的文件大小。未来若 `agent-session` 提供每次写入后的 size/diff bytes，再把星点面积切换为历史大小。

“目录深度”在这里是弱结构提示：更深的文件常态略暗，但不能被解释为更不重要。“累计访问”使用 `log1p` 并按 P95 截断，只让长期热点比从未再访的星略亮。最近动作的瞬态增量必须远大于两项基线差异：

```text
baseline  = context + 0.15 * depth_factor + 0.20 * log_visit_factor
pulse(t)  = action_gain * 2^(-event_age / 5 min)
brightness(t) = clamp(baseline + pulse(t), 0, 1)
```

这样累计访问仍能留下微弱的长期结构，但一颗星每次被 Agent 访问时会明显点亮，然后在 30 分钟内回到正常亮度。连续播放时，亮区在文件之间迁移，直接表现 Agent 的浏览、聚焦、修改和离开，而不是把整个已探索疆域永久照亮。

## 注意力衰减

读取和写入效果使用真实事件年龄：

```text
0--5 min     高亮
5--30 min    指数衰减
>30 min      注意力效果消失，文件星本身保留
```

read、direct write 和 command-associated path effect 使用不同 `action_gain`、核心形状和波纹颜色，但共享同一衰减函数。紫色菱形只表达“记录到的命令与该路径关联”，不声称命令创建了文件。纯命令不制造假文件星，只在中心产生短暂 ambient pulse；进程、模型响应和 domain reference 同样只作为不参与布局的外围/中心瞬态标记。

写入波纹需要显式渲染为若干同心环的年龄状态，不能只依赖浏览器 CSS/ECharts 的实时动画。这样 GIF 和 MP4 的离散帧也能捕捉到传播波。

主图不保留彗尾或任何形式的点到点连线。若以后重新讨论局部残影，也必须是单个星点周围的短暂局部效果，不能连接两个文件。

## 交互

默认交互保持最少：

- Play/Pause。
- 单一真实时间进度条。
- 悬停文件查看 `path`、目录、累计访问、最近动作、首次 observed 动作。
- 不提供侧栏、目录列表、cast list 或 dashboard 导航。

进度条拖动到任意时间时，图必须重建该时间点的累计状态。

## 输出

一个命令生成一个图文件：

```text
repository-nebula.html   自包含、可播放、无网络请求
repository-nebula.svg    指定 cursor 的静态矢量图
repository-nebula.png    指定 cursor 的静态截图
repository-nebula.gif    多个真实事件 cursor 的离散动画
repository-nebula.mp4    与 GIF 相同的事件驱动帧
```

HTML 只嵌入该图需要的紧凑字段。所有 endpoint 文件可以保留，但不能携带与本图无关的 blame、authors、daily、association 等完整统计。

## GIF/MP4 取帧

取帧必须包含：

1. 第一事件前的空白帧。
2. 第一条事件。
3. 早期若干逐文件生长帧。
4. read 事件及其衰减帧。
5. write 事件及 30 s、90 s、3 min 波纹帧。
6. 中期多 session 累积状态。
7. 最后一条事件。

早期帧使用更密集的采样，避免第二帧直接跳到几十个文件。长时间无事件的区间可以压缩。

## 性能约束

- 事件按时间排序后单次扫描。
- Endpoint context 只保留 `path/group/stable_seed` 等紧凑字段。
- 背景星空使用一个 scatter series；不为每个目录或文件创建 DOM 组件。
- 目录色云使用有限数量密度 lobe，不随文件数量线性创建大型阴影节点。
- 目标是约 20k 文件、1k 事件仍可生成可播放单 HTML。
- 不为这张图引入统一前端或额外服务器。

## 验收标准

### 自动测试

- 第一 playback cursor 小于第一条事件，且文件、云均为空。
- 第一条事件后恰好出现第一个 observed 文件。
- 所有 endpoint 文件都存在于低亮度 context layer。
- context 文件和 observed 文件使用不同透明度与 tooltip 语义。
- 主图不存在 `line`、`graph`、edge、link 或 directory label series。
- 同一顶层目录的所有子目录属于同一 hue family。
- 新星优先出生在路径最相近的已观察文件旁边；无候选时才从目录云心出生。
- 最近访问的瞬态亮度显著高于累计访问基线，并在 30 分钟后回归基线。
- ignored/build output 若从未被 Agent 真实触达则不进入主图；真实触达的 untracked repository-relative 路径保留并明确标记。
- read ring 在 30 分钟后消失。
- write ripple 在 GIF 静态帧中存在，并在 3 分钟后消失。
- command-associated 视觉只表达已有 session path effect，不升级成 create/delete/rename 结论。
- commit 只改变 artifact 外框 class，不改变 ECharts 文件 series 数据。
- 多 session 事件累计，不在 session 边界清空。

### 真实视觉检查

必须分别用 AgentCap 和 AgentSkill 生成 HTML、PNG、SVG、GIF 和 MP4，并至少检查：

```text
frame 0       完全空
frame 1       第一个文件与背景上下文开始显现
frames 2--7   早期逐步生长
25%           多目录色云形成，无文字、无连线
50%           多 session 累积，读写效果可辨
75%           色云仍连续，不出现散点蜘蛛网
100%          完整上下文可见，触达文件明显亮于背景
```

检查时要打开真实 HTML 点击播放，并检查浏览器 console/page errors。不能只依赖单元测试或最终 PNG。

## 实现与验证

实现直接复用 `agent-session` 的 session/event 抽象，不创建第二套 IR。Nebula 的 lean 构建路径解析 identity-matched session，按需用 `--global` 提取跨 session 的目标目录 Tool 行，再用 `git ls-tree` 和 first-parent lifetime/status 提供 frozen endpoint 与 durable candidate。它跳过 hunk、numstat、blame、ownership、co-change 和 survival 等本图不使用的数据。

已完成的自动验证包括：空白首帧、完整 Git context、首次 observed、路径邻近出生、读写与命令关联脉冲、30 分钟衰减、无 line/graph/label、Git 噪声过滤，以及纯 commit cursor 冻结图内 visual cursor、只切换 artifact 外框 class。浏览器端还逐个打开所有单图产物，检查 console error、布局溢出和 commit flash。

2026-07-16 使用两个真实长期 repository 验证。默认与 `--global` 使用同一时间窗口和 Git endpoint；global 的额外 session 只贡献命中目标目录的 Tool 操作，不贡献无关 LLM 正文：

| Repository / scope | Sessions | Agent events | Tool events | LLM responses | Commits |
|---|---:|---:|---:|---:|---:|
| AgentCap / default | 8 | 943 | 337 | 606 | 416 |
| AgentCap / `--global` | 153 | 2,525 | 1,919 | 606 | 416 |
| AgentSkill / default | 36 | 2,849 | 991 | 1,858 | 246 |
| AgentSkill / `--global` | 200 | 10,964 | 9,106 | 1,858 | 246 |

两组 `--global` 产物均逐帧检查了空帧、早期 discovery、目录色云形成、read 白环、direct-write 暖色波纹、command-associated 紫色菱形、30 分钟回落和 commit 金色外框。图内文件状态没有随 commit 改变。产物 footer 与 SVG metadata 会分别写明 `repository_identity` 或 `global_tool_operations`，分享后仍可判断采样范围。
