# Repository Nebula：统一设计

状态：**统一设计基线，待按本文重构实现**。

本文是 Repository Nebula 的单一事实来源。旧实现、README、测试或其他设计文档与本文冲突时，以本文为准。

## 1. 要回答的问题

Repository Nebula 只回答一个问题：

> Claude、Codex、Gemini 等 Agent 在多个 session 中，如何把注意力移动到不同文件，并让 repository 的文件空间逐步生长、修改、移动和消失？

它不是依赖图、进程图、网络图、LLM trace、Git 历史播放器或统一 dashboard。主画面的唯一实体是文件。

## 2. 用户看到的故事

播放开始时画布为空。第一条真实的 Agent 文件事件产生第一颗星；后续文件在已经形成的局部结构旁出生。读操作让文件短暂变亮，写操作产生暖色波纹，创建、删除和重命名改变星域的组成。文件之间持续通过引力和斥力寻找新的平衡，所以 repository 不是静态地图，而是随着 Agent 工作呼吸和重组的软件生命体。

用户第一眼应看见当前 Agent 正在触达哪里，第二眼看见哪些区域在生长或被反复修改，最后才通过悬停和时间轴查看文件路径、session 和真实时间。

## 3. 交付边界

一个命令只生成一个图文件：

```text
repository-nebula.html   自包含、可播放、无网络请求
repository-nebula.svg    指定 cursor 的静态矢量图
repository-nebula.png    指定 cursor 的静态截图
repository-nebula.gif    事件驱动的离散动画
repository-nebula.mp4    与 GIF 使用同一组事件帧
```

约束如下：

- 一个 HTML 只有 Repository Nebula 一张图。
- HTML 内嵌运行时代码和该图需要的数据，不依赖服务器、数据库或 API。
- HTML 只有播放/暂停、一个时间进度条、最小图例和当前动作说明。
- 不提供侧边栏、目录列表、cast list、dashboard 导航或多图联动。
- PNG、SVG、GIF 和 MP4 必须由同一个确定性渲染函数生成，不能各自实现一套语义。
- 生成物可以独立分享，也可以通过 `iframe`、图片或附件嵌入其他 Agent 生成的 report。

## 4. 数据和证据边界

### 4.1 唯一事件抽象

直接复用 `agent-session` 已有的 `SessionSummary` 和 `NormalizedEvent`。Repository Nebula 不建立第二套持久化事件 IR，不要求用户保存或理解中间 JSON。

视图只读取以下现有字段的紧凑投影：

```text
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
```

Git 只补充 repository 文件范围、file lifetime 和候选 durable change。它们不能覆盖 Agent 事件语义。

### 4.2 三类证据必须分开

1. **Agent recorded operation**：来自 Claude、Codex、Gemini 原生 session 的真实 Tool event。
2. **Durable Git evidence**：commit、status、rename 和 file lifetime。
3. **Frozen endpoint evidence**：当前 tree、blob size 等终点状态。

禁止进行以下升级：

- Agent 触达文件不等于 Agent 创建文件。
- Agent 写文件不等于 Git authorship。
- read-before-write 只是时间先后，不是因果关系。
- 从命令文本看到 `rm`、`mv`、重定向或 `cargo fmt`，不等于已经证明文件发生变化。
- Agent event 与 Git change 的匹配是候选关联，不能改写为确定 provenance。

### 4.3 Session 发现

默认模式自动发现所有支持的 Agent：

- Claude 使用项目路径编码匹配 repository 和 sibling worktree。
- Codex 使用 session `cwd`、worktree 和 Git remote 匹配。
- Gemini 使用项目路径或 project hash 匹配。
- 同一 Git repository 的多个 worktree 共享一个长期视图。

显式 `--global` 时扫描所有本地 Agent session，但只纳入真实 Tool event 中确实指向目标 repository 的操作。prompt、assistant 正文、搜索结果或普通文本中提到仓库名称，不算文件事件。

所有匹配 session 按真实 `ts_ms` 合并排序；新 session 继承此前形成的星域，不重新清空。

## 5. 哪些事件进入主图

主图只接收与 repository 文件直接相关的事件。

| 事件 | 是否进入 | 视觉含义 |
|---|---:|---|
| Read/Search/Glob 且能解析到 repository 文件 | 是 | Agent 注意力到达文件 |
| Edit/Write 且能解析到 repository 文件 | 是 | 文件被直接修改 |
| 明确或有候选 durable evidence 的 create | 是 | 新文件出生；候选状态必须注明不确定性 |
| 明确或有候选 durable evidence 的 delete | 是 | 文件衰减并退出力场 |
| 明确或有候选 durable evidence 的 rename/move | 是 | 同一文件从旧路径状态过渡到新路径状态 |
| Bash 且有可靠的 repository 文件路径和文件 effect | 是 | 投影到对应文件，不产生命令节点 |
| 只有命令文本路径、无法判断文件 effect 的 Bash | 否 | 不猜测文件变化 |
| 无文件路径 Bash | 否 | 完全忽略 |
| Network/domain | 否 | 完全忽略 |
| Process | 否 | 完全忽略 |
| LLM response / heartbeat | 否 | 完全忽略 |

Read 虽然不改变磁盘文件，但改变了 Agent 对文件的注意力状态，所以保留。Network、LLM、process 和无路径命令既不画成节点，也不改变外框颜色。

## 6. Git 的职责

Git 只做三件事：

1. 给 repository-relative 文件去噪，排除 `.git/`、dependency cache、build output、coverage 和临时日志。
2. 提供 tracked/lifetime/rename 等 durable reference。
3. 在 commit timestamp 让整个 artifact 的最外层边框短暂闪金色。

Git 不得：

- 让文件出生、消失、移动、变大或变色。
- 成为动画的第二套时钟。
- 把当前 endpoint 文件提前放进历史画面。
- 把 Git author 改写成 Agent author。

未被任何 Agent 文件事件触达的 endpoint 文件不进入 Nebula。完整 endpoint repository 的静态拓扑应由独立图展示，不能作为暗背景淹没 Agent 过程。

Agent 真实触达的 repository-relative untracked 文件可以保留，但 tooltip 必须标记为 `observed untracked`，不能写成 `created`。

## 7. 时间语义

### 7.1 Agent 事件是唯一状态时钟

```text
t0 - 1 ms   空画布
t0          第一条 Agent 文件事件，第一颗星出现
t1...tn     后续真实 Agent 文件事件
tn          最后一条文件事件后的平衡状态
```

进度条保留真实 timestamp。自动播放可以压缩没有事件的长时间空档，但不得插入虚构动作。

### 7.2 注意力按事件步衰减

历史可能跨越数月，而分享动画只有数秒。不能再用“五分钟半衰期、三十分钟消失”驱动压缩动画，否则一次高亮可能不到一帧。

默认使用最近 24 个 Agent 文件事件作为注意力窗口：

```text
attention(i, k) = action_gain * 2^(-(k - last_event_i) / 6)
```

- `k` 是当前 Agent 文件事件序号，不是 wall-clock 分钟。
- 6 个事件步为一个视觉半衰期。
- 超过 24 个事件步后瞬态注意力消失，累计文件状态保留。
- 同一个 Tool event 触达多个文件时，这些文件在同一个事件步更新。
- tooltip 和时间轴仍显示真实时间，事件步只用于可观看的视觉衰减。

Read 的 `action_gain` 小于 Write/Edit。Create/Delete/Rename 使用独立生命周期动画，不复用普通 read/write pulse。

### 7.3 播放节奏

- 每个显著文件事件至少保留两个视觉帧。
- 新文件出生、写波纹、删除和重命名必须各自有可见的过渡帧。
- 长空档压缩，密集 burst 可以减速，但事件顺序不能改变。
- session 边界不清空画面；当前动作说明显示 vendor、session、action、path 和真实 timestamp。
- 拖动进度条时，从最近的确定性 checkpoint 或起点重放到目标 cursor。

## 8. 动态引力布局

### 8.1 核心原则

文件没有预设的最终稳定坐标。稳定的是目录颜色和确定性计算，不是位置。

每个文件拥有动态状态：

```text
position
velocity
mass
directory/path features
recent attention
lifecycle state
```

每个 Agent 文件事件后，当前可见文件运行固定次数的确定性力模拟：

```text
F_i =
    path_attraction_i
  + directory_attraction_i
  + attention_gravity_i
  + weak_centering_i
  - repulsion_i
  - collision_i
  - damping_i
```

位置是当前文件集合、路径关系和注意力共同形成的暂时平衡。新增、删除、重命名和近期访问都会改变局部乃至整体布局。

### 8.2 路径和目录引力

文件间引力按以下顺序增强：

1. 同一 parent directory。
2. 最长公共目录前缀较长。
3. 同一 top-level directory。
4. 同一 extension 只能作为很弱的同分因素，不能主导布局。

目录没有固定锚点、边界或文字标签。同色文件通过相互吸引自然形成可移动色云；目录云的质心由当前文件位置计算，也会随时间改变。

### 8.3 斥力、碰撞和阻尼

- 所有可见文件之间存在多体斥力，避免全部塌缩到一点。
- 近距离使用 collision force，保证星点和活动光环不会重叠。
- 使用速度阻尼抑制永久振荡。
- 使用很弱的全局 centering 防止整个系统漂出画布，但不能把目录固定到预设扇区。
- 删除文件的质量和透明度逐步降为零，随后退出力场；其消失会触发周围文件重新平衡。

### 8.4 注意力改变局部平衡

最近触达的文件临时增加视觉亮度和有效引力质量：

```text
Read       小幅、短暂增加
Edit/Write 更强、持续更久
Create     新质量进入系统
Delete     质量逐渐退出系统
```

注意力力必须弱于结构引力和碰撞力。它应使局部星域轻微聚拢和呼吸，不能让一次 Read 把整张图剧烈拉动。

### 8.5 新文件出生

新文件从当前已经可见、路径最相近的文件旁边出生：

```text
同一 parent directory
→ 最长公共目录前缀
→ 同一 top-level directory
→ 当前同色目录云质心
→ 画布中心
```

出生点只是动画初态，不表示 provenance、依赖或创建者。新文件出现后立即参与引力、斥力和碰撞，不沿固定轨迹飞向预设终点。

### 8.6 确定性和库复用

优先复用 tree-shaken `d3-force` 模块：

- `forceSimulation`
- `forceManyBody`
- `forceCollide`
- `forceCenter`
- 自定义很薄的 path/directory attraction force

固定初始 seed、事件顺序、参数和每事件 tick 数。同一输入和 cursor 必须得到相同坐标，确保 HTML、SVG、PNG、GIF 和 MP4 一致。

禁止继续使用当前的“目录扇区 + golden-angle 半径 + 预设终点”算法。

## 9. 连续色云

颜色是目录结构的唯一空间编码：

```text
色相             = top-level directory
饱和度/明度微调  = subdirectory
云的密度与范围   = 当前文件位置和活动状态
```

目录色云随文件移动，不设多边形边界，不显示目录标签，不把每个文件包进一个清晰的大圆。

理想密度定义为：

```text
density(x, y) = Σ Gaussian(file_position, bandwidth, activity_weight)
```

实现可复用 KDE，或使用少量径向渐变近似，但不能形成现在的大面积均匀紫雾。云必须服从当前动态文件位置，而不是 frozen endpoint 文件集合。

## 10. 文件视觉语义

| 视觉通道 | 含义 |
|---|---|
| 星点色相 | top-level directory |
| 同色系微调 | subdirectory |
| 常态明度 | 路径深度和累计 Agent 访问次数的弱提示 |
| 常态大小 | 累计 observed activity 的 `log1p` 尺度 |
| 白色短闪/细环 | 最近 Read/Search |
| 暖色核心和扩散环 | 最近 Edit/Write |
| 绿色出生动画 | 明确或候选 create |
| 红色衰减 | 明确或候选 delete |
| 青色连续移动 | rename/move |
| 白色细边框 | observed untracked |
| 金色 artifact 外框 | commit reference，仅闪外框 |

最近动作的视觉增量必须明显强于累计访问和路径深度的基线差异。主画面不得出现：

- Bash 菱形。
- domain 三角形。
- process 方块。
- LLM heartbeat。
- 文件间连线、轨迹线、read→write 边或因果边。
- 目录文字、territory 边界或永久文件标签。

图外允许一个最小当前动作说明：

```text
Codex · Edit · collector/src/main.rs · session 42/200 · 2026-07-16 10:24:03
```

PNG/SVG/GIF 没有 hover，因此最小图例和当前动作说明必须随 artifact 一起导出，不能把全部语义藏在 tooltip 中。

## 11. 数据传递架构

### 11.1 当前实现

当前实际调用链是：

```text
Claude/Codex/Gemini native sessions
        +
Git history / endpoint
        |
        v
agent-session Rust parser
        |
        v
LongitudinalArtifact JSON stdout
        |
        v
Python project.py 再聚合
        |
        v
Node projectForView 再裁剪
        |
        v
JSON + browser runtime 内嵌进单 HTML
        |
        v
ECharts -> HTML / SVG / PNG / GIF / MP4
```

这条链没有服务器或运行时网络请求，但对 Nebula 而言存在重复解释：Rust 事件模型、Python Gallery 模型、Node view 模型和 ECharts series 模型。虽然 Python 输出没有保存为用户中间文件，它事实上仍是一层额外投影。

### 11.2 目标实现

Repository Nebula 应收敛为：

```text
agent-session JSON stdout
        |
        v
薄 JS view projection
        |
        v
d3-force state + ECharts renderer
        |
        v
单 HTML / SVG / PNG / GIF / MP4
```

原则是：

- `agent-session` 是唯一事件语义来源。
- JS 只筛选字段、维护动态力状态和生成 ECharts option。
- Nebula 不再经过完整 `project.py`。
- Git lifetime 和候选 durable change 由 `agent-session` 直接输出。
- 不写 canonical evidence artifact，不要求用户管理中间 IR。
- 其他确实需要复杂 Git 聚合的静态图可以继续使用独立聚合逻辑，不能反向增加 Nebula 的复杂度。

### 11.3 每一步的数据形态和落盘规则

目标路径中的数据通过 stdout 和进程内对象传递，不生成 `.json`、`.jsonl`、SQLite 或所谓 canonical artifact 临时文件。

| 步骤 | 产生的数据 | 存放位置 | 是否落盘 |
|---|---|---|---:|
| `agent-session-export` | 一个 `LongitudinalArtifact` JSON 文档，包含 session、normalized events、Git lifetime 和候选 durable change | Rust stdout；Node 读取后成为字符串 | 否 |
| Node `JSON.parse` | `LongitudinalArtifact` JavaScript object | Node 内存 | 否 |
| 薄 JS projection | 只含 `meta`、文件相关 events、必要 lifetime/commit reference 的普通 JavaScript object | Node 内存 | 否 |
| 动态力计算 | `Map<path, FileState>`，其中包含 `x/y/vx/vy/mass/visits/lastEventStep` | Node 或浏览器内存 | 否 |
| HTML 组装 | CSS、浏览器 runtime、紧凑 JSON payload 和初始化调用组成的 HTML 字符串 | Node 内存 | 否 |
| HTML 输出 | 完整自包含 HTML | 用户指定输出路径 | **最终文件** |

薄投影的概念形态如下，它不是新的公共 schema，也不单独写成文件：

```text
{
  meta: {
    repository,
    revision,
    window,
    session_scope
  },
  events: [
    {
      ts_ms,
      session_id,
      vendor,
      action,
      paths,
      write_paths,
      durable_changes
    }
  ],
  commits: [committed_at_ms]
}
```

文件节点不需要作为第二份输入重复保存；它们可以从首次出现的文件事件增量建立。Git lifetime 只在 rename/delete/create 候选需要时随对应事件保留最小字段。

浏览器 runtime bundle，例如 `dist/runtime.iife.js`，是项目构建时产生并复用的代码资产，不是每次生成 Nebula 时产生的数据临时文件。生成 HTML 时它的文本被读入内存并内嵌到最终 HTML。

不同输出格式的磁盘行为如下：

- **HTML**：无临时文件，直接写最终 `.html`。
- **SVG**：HTML 字符串仅存在内存；Playwright 用 `page.setContent()` 打开，取出 `<svg>` 字符串后直接写最终 `.svg`，无临时 HTML。
- **PNG**：HTML 字符串仅存在内存；Playwright 直接截图到最终 `.png`，无临时 HTML。
- **GIF/MP4**：在 `/tmp/agentsight-vis-frames-*` 创建短生命周期目录，逐 cursor 写 `frame-0000.png` 等帧文件；`ffmpeg` 编码最终 `.gif` 或 `.mp4` 后递归删除整个目录。

GIF/MP4 的临时 PNG 是渲染编码缓存，不是数据交换格式。未来可以改成把帧通过 pipe 直接送入 `ffmpeg`，但当前临时目录方案更简单、失败时更容易诊断，且正常退出和异常退出都必须清理。

交互式 HTML 中的力状态在浏览器内存里增量维护。向后拖动时间轴时可以从头确定性重放，并在本次页面生命周期内建立内存 checkpoint cache；checkpoint 默认不嵌入 HTML、不写磁盘，也不成为用户需要理解的格式。

## 12. 实现和性能约束

- Agent 文件事件预先按时间排序，播放时增量处理。
- 路径吸引边只保留目录内或最长公共前缀的局部邻居，不能构造完整 O(F²) 边集。
- 多体斥力使用 quadtree/Barnes-Hut 实现，优先复用 `d3-force`。
- 每个事件运行固定数量 ticks，并周期性保存 checkpoint；拖动时间轴不必每次从零重算。
- 背景、文件、活动核心和生命周期效果使用少量共享 series，不为每个文件创建 DOM 节点。
- 不引入 Cytoscape、uPlot、统一前端、生产 sourcemap 或额外服务器。
- 目标规模：约 20k repository 文件范围、10k Agent 文件事件仍可生成；实际画面只包含截至 cursor 已 observed 的文件。

## 13. 明确删除的旧设计

以下旧行为必须从实现、测试和 README 中删除：

1. 第一次事件后渐显全部 frozen endpoint 文件。
2. 固定目录扇区和 golden-angle 最终坐标。
3. 文件位置保持不变的 mental-map 假设。
4. 真实五分钟半衰期和三十分钟注意力窗口。
5. 中心 Bash 菱形、domain 三角、process 方块和 LLM heartbeat。
6. Bash/Network/LLM 改变外框颜色。
7. 依据同 extension 强行选择视觉父文件。
8. 大面积低语义 radial-gradient 雾层。
9. 把全部解释放在 tooltip 中。
10. Nebula 对完整 Python Gallery projection 的依赖。

## 14. 验收标准

### 数据

- 默认同时发现 Claude、Codex、Gemini 的 repository session。
- `--global` 只增加真实命中 repository 的 Tool event。
- prompt、assistant 正文和普通搜索提及不会制造文件事件。
- Network、process、LLM 和无路径 Bash 不进入最终 payload。
- Agent-observed untracked 文件保留且语义明确。

### 时间

- 第一 cursor 位于第一条 Agent 文件事件之前，画面严格为空。
- 图内状态只在 Agent 文件事件步变化。
- commit-only cursor 冻结图内状态，只闪 artifact 外框。
- 注意力在事件步上可见衰减，不会因跨月历史压缩而只存在一帧。
- 多 session 连续播放且不重置。

### 布局

- 图中没有预设最终坐标和固定目录扇区。
- 新文件出现会推动邻近文件重新平衡。
- 删除文件会退出力场并使局部重新平衡。
- 最近注意力只造成受控的局部扰动。
- 同一输入、cursor 和参数得到确定性相同的布局。
- 图中没有可见 edge、directory label 或 territory boundary。

### 视觉和交付

- 用户无需 hover 即可从最小图例和当前动作说明区分 Read、Write、Create、Delete、Rename 和 Commit。
- 一次只生成一个图；HTML 只有一个 chart 和一个进度条。
- HTML 无网络请求；SVG、PNG、GIF、MP4 与 HTML 使用同一语义和坐标。
- 产物可以直接打开，也可以嵌入其他 Agent 生成的 report。

## 15. 实现顺序

1. 删除 endpoint context 和所有非文件 ambient marker。
2. 让 Nebula 直接消费 `agent-session` 输出，移除 Python projection 依赖。
3. 用确定性 `d3-force` 状态替换极坐标固定目标布局。
4. 将注意力从真实分钟改为事件步衰减。
5. 加入当前动作说明和完整最小图例。
6. 重新生成真实多 session HTML、PNG、SVG 和 GIF，逐帧视觉检查。
7. 更新 README、测试和示例，使它们只引用本文语义。
