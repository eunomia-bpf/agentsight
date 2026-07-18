# Repository Nebula：统一设计

状态：**v3 已实现；本文同时记录现行算法和验收边界**。

本文是 Repository Nebula 的单一事实来源。旧实现、README、测试或其他设计文档与本文冲突时，以本文为准。

## 1. 要回答的问题

Repository Nebula 只回答一个问题：

> Claude、Codex、Gemini 等 Agent 在多个 session 中，如何把注意力移动到不同文件，并让 repository 的文件空间逐步生长、修改、移动和消失？

它不是依赖图、进程图、网络图、LLM trace、Git 历史播放器或统一 dashboard。主画面的唯一实体是文件。

### 1.1 算法性质与科学边界

Repository Nebula 本质上是一个**带已知目录层级约束的动态图布局**，而不是任意的星云特效，也不是从像素中猜目录的无监督聚类。Git 路径提供层级先验，Agent 的真实文件操作序列提供状态时钟；算法把两者确定性地映射成每一步的文件状态和二维位置：

```text
Git 文件层级 + Agent 文件操作序列
            -> 每个事件步的文件集合、视觉状态和二维布局
```

表示法要同时满足四个可检验目标：

1. **层级保真**：同目录和长公共路径前缀的文件保持局部邻近，跨顶层目录的颜色混杂受控。
2. **时间连续**：相邻事件步保留人的心智地图，新增、删除和重要性变化只引发渐进重排。
3. **事件响应**：Read/Write/Create/Rename/Delete 立即产生对应视觉变化，且不会把热点文件弹成跨目录离群点。
4. **长期可读**：长期反复触达的文件与目录逐渐突出，久未访问者缩小、暗淡和压密，同时保留路径归属。

这些目标分别用目录混杂率、路径邻域保持率、相邻帧归一化位移、事件响应延迟、删除退出步数和确定性重放哈希评价。合成仓库可以验证单项不变量，真实多 session 仓库用于检查规模和组合行为。

当前参数是工程启发式，已经具备明确输入、状态方程、确定性输出和自动化不变量测试，但尚未经过用户研究或跨仓库定量标定。因此现阶段可称为“可复现、可证伪的可视化原型”，不能声称已经证明了文件的业务重要性、Agent 的因果推理或最优的软件聚类。

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

### 3.1 目标用户入口

用户不应该知道 `agent-session`、Python projector、ECharts、Playwright 或内部 view ID。v1 的用户入口是 AgentSight Rust CLI：

```bash
agentsight vis [PATH] [-o OUTPUT]... [--global]
```

`agentsight vis` 是 AgentSight 主二进制中的内嵌入口，直接调用 `agent-session` library。发行包内嵌生成 HTML 所需的 browser runtime，用户机器不需要安装 npm 或 Python。v1 不再维护第二个同功能 binary，避免复制 CLI、投影和渲染入口。

v1 只保留三个用户参数：

- `PATH`：可选 repository 路径，默认当前目录并向上寻找 Git root。
- `-o/--output`：可重复的输出路径，默认 `repository-nebula.html`；扩展名决定格式。同一命令中的所有格式共享一次事件投影和一次浏览器力模型。
- `--global`：可选，扫描所有本地 Agent session，但仍只保留实际命中 repository 的文件事件。

v1 不公开 `--view`、`--since`、`--until`、`--at`、`--frames`、`--fps`、`--width`、`--height` 或 `--format`。默认视图、完整 repository 时间、分享尺寸、帧率和播放时长都由固定算法决定，避免用户在理解图之前先配置渲染器。

默认行为是：

- repository 使用当前目录，并向上寻找 Git root。
- 时间范围从 repository root commit 到当前时间。
- 自动发现属于该 repository/worktree 的全部 Claude、Codex 和 Gemini session。
- 默认视图就是 Repository Nebula，不要求用户记住 `workspace-constellation`。
- 默认输出 `repository-nebula.html`。
- 默认分享画布为 `1200 × 675`；HTML 自动播放最长 30 秒，GIF/MP4 对每个布局快照输出一帧，不再二次抽帧，并以 8 fps 编码。
- 运行时持续把简短进度日志打印到 stderr。
- 不启动服务器，不自动上传，也不生成项目目录或中间数据文件。

常见用法：

```bash
# 当前 repository，生成默认 HTML
agentsight vis

# 指定 repository
agentsight vis /path/to/repo -o repo.html

# 扫描所有本地 Agent session，只保留实际命中该 repository 的文件事件
agentsight vis /path/to/repo --global -o repo-global.html

# 生成适合社交媒体或 report 的动画
agentsight vis /path/to/repo --global -o repo.gif

# 生成完整历史结束状态的静态快照
agentsight vis /path/to/repo -o repo.png
agentsight vis /path/to/repo -o repo.svg

# 一次扫描、一次布局模型，同时生成全部分享格式
agentsight vis /path/to/repo --global \
  -o repo.html -o repo.svg -o repo.png -o repo.gif -o repo.mp4
```

输出格式完全由扩展名决定，不再要求额外 `--format`：

```text
.html  可交互、可播放、可悬停
.svg   指定 cursor 的矢量快照
.png   指定 cursor 的完整 artifact 截图
.gif   离散事件动画，适合直接分享
.mp4   与 GIF 相同语义的高效视频
```

### 3.2 打开、分享和复用

- HTML 可以直接双击打开；不需要 `localhost` 或后台进程。
- Markdown/report 可以链接 HTML，并使用生成的 PNG/GIF 作为预览图。
- 支持本地资产的报告系统可以使用 `<iframe src="repository-nebula.html">` 嵌入交互版本。
- 社交媒体直接上传 PNG、GIF 或 MP4。
- SVG 可以内联进技术报告或网页，保留矢量质量。
- 同一命令可以重复 `-o` 生成不同扩展名；它们必须复用同一个数据对象和同一个确定性力模型。

HTML 中用户只操作：

1. Play/Pause。
2. 一个真实时间进度条。
3. 悬停文件星查看路径、最近动作、累计访问和 session。

图上方或下方始终显示最小当前动作说明，避免用户必须悬停才能知道动画正在做什么。

不额外显示 session 分割线、切场动画、边框闪烁或 session 节点。多个 session 是同一个 repository 演化过程；vendor 和 session 只出现在当前动作文字与 tooltip 中，session 改变时自然更新文字即可。

### 3.3 默认运行日志

日志默认写入 stderr，最终文件写入用户路径。日志保持固定的五步结构：

```text
[agentsight-vis 1/5] repository  /path/to/repo
[agentsight-vis 2/5] sessions    claude=8 codex=21 gemini=3
[agentsight-vis 3/5] file events read=842 write=391 create=44 rename=8 delete=17
[agentsight-vis 4/5] simulation  events=1302 visual-steps=360 duration=30s
[agentsight-vis 5/5] output      repository-nebula.html  4.8 MiB
```

发现和解析时间较长时，每处理一批 session 更新进度或定期打印累计数，不能长时间无输出。单个坏 session 以 warning 记录并继续；repository 无可用文件事件时明确报错，不生成看似成功的空图。

### 3.4 开发期兼容入口

`vis-gallery` 仍保留原有 31 张图的开发/回归入口，便于继续生成其他软件工程图。它不是 Repository Nebula 的普通用户路径：

```bash
cd vis-gallery
npm ci
npx playwright install chromium
npm run build

npm run render -- \
  --repo /path/to/repository \
  --since repo \
  --view workspace-constellation \
  --output repository-nebula.html
```

Repository Nebula 的普通入口已经是前述 `agentsight vis`；Node/Python 链仅服务其他 Gallery 图和兼容测试。

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
read_paths
write_paths
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
- Bash 可以推导文件动作，但必须保留 `inferred_from_bash` 来源，不能伪装成直接文件系统证据。
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
| Tool 导致且能解析到 repository 文件的 Read | 是 | Agent 注意力到达文件 |
| Tool 导致且能解析到 repository 文件的 Write/Edit | 是 | 文件被直接修改 |
| 明确或有候选 durable evidence 的 create | 是 | 新文件出生；候选状态必须注明不确定性 |
| 明确或有候选 durable evidence 的 delete | 是 | 文件衰减并退出力场 |
| 明确或有候选 durable evidence 的 rename/move | 是 | 同一文件从旧路径状态过渡到新路径状态 |
| Bash 可可靠推导出 repository 文件动作 | 是 | 转换成 read/write/create/rename/delete，不产生命令节点 |
| Bash 含动态变量、未展开 glob 或无法解析的文件 effect | 否 | 跳过不可靠部分 |
| 无文件路径 Bash | 否 | 完全忽略 |
| Network/domain | 否 | 完全忽略 |
| Process | 否 | 完全忽略 |
| LLM response / heartbeat | 否 | 完全忽略 |

v1 的动作集合严格收口为 `read`、`write`、`create`、`rename`、`delete`。Read 虽然不改变磁盘文件，但改变了 Agent 对文件的注意力状态，所以保留。Network、LLM、process 和无路径命令既不画成节点，也不改变外框颜色。

### 5.1 Bash 文件动作推导

Bash 不是图中实体，只是文件动作的另一种来源。Rust 侧直接复用 `agent-session` 已有的保守 operand、redirection、pipeline 和嵌套 shell 解析，不建立第二套 Bash parser，也不声称解释完整命令语言。

只处理成功完成、cwd 可解析且目标路径能够归一化到 repository 内部的命令。基础规则为：

| Bash 结构 | 推导动作 |
|---|---|
| `cat/head/tail/less` 等明确读取文件参数 | `read` |
| `sed -i`、`perl -pi`、明确写入已有文件的重定向 | `write` |
| `touch`、`cp SOURCE NEW`、向新路径重定向 | `create`；无法判断目标此前是否存在时降级为 `write` |
| `mv OLD NEW` 且两端路径可解析 | `rename` |
| `rm/unlink FILE` | `delete` |
| pipeline | 分别解析每个 command 和重定向，最后按规范化路径合并 |
| `mkdir/rmdir` | 不生成 star；目录不是图中实体 |
| `cargo fmt`、生成器或脚本但没有明确输出路径 | 不推导具体文件动作 |

变量、command substitution、未展开 glob、动态 `find -exec`、脚本内部副作用或 repository 外路径默认跳过。若同一 Tool event 已经包含直接 Edit/Write 记录，直接记录优先，Bash 推导只补充未覆盖路径并去重。

每个推导动作复用已有字段保留来源和访问角色：

```text
category = shell
path_ref.access = read | write
```

Nebula 不再增加单独的 confidence/IR 字段；无法保守确定的 effect 直接跳过。图上仍然只显示对应文件的五种动作。

## 6. Git 的职责

Git 只做三件事：

1. 给 repository-relative 文件提供 worktree 边界。
2. 提供 tracked/lifetime/rename 等 durable reference 和事件关联候选。
3. 在 commit timestamp 让整个 artifact 的最外层边框短暂闪金色。

Git lifecycle candidate 只能把同一 Agent 文件事件的表现细化为 create/delete/rename；星出现和状态变化仍发生在该 Agent event 的 `ts_ms`，不能挪到 commit 时间。

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
repository root commit ... t0 前   空画布
t0          第一条 Agent 文件事件，第一颗星出现
t1...tn     后续真实 Agent 文件事件
tn          最后一条文件事件后的平衡状态
```

进度条保留真实 timestamp。自动播放可以压缩没有事件的长时间空档，但不得插入虚构动作。

### 7.2 注意力按事件步衰减

历史可能跨越数月，而分享动画只有数秒。不能再用“五分钟半衰期、三十分钟消失”驱动压缩动画，否则一次高亮可能不到一帧。

注意力窗口随历史压缩比例自适应。令 `E` 为 Agent 文件事件步数，`S=min(E,360)` 为布局快照数：

```text
B = max(1, ceil(E / S))
attention(i, k) = action_gain * 2^(-(k - last_event_i) / B)
window = 4B
```

- `k` 是当前 Agent 文件事件序号，不是 wall-clock 分钟。
- 一个布局快照平均覆盖的事件数 `B` 构成一个视觉半衰期。
- 超过四个半衰期后瞬态注意力消失，因此高亮大约跨四个连续布局/GIF 帧衰减。
- 同一个 Tool event 触达多个文件时，这些文件在同一个事件步更新。
- tooltip 和时间轴仍显示真实时间，事件步只用于可观看的视觉衰减。

Read 的 `action_gain` 小于 Write/Edit。Create/Delete/Rename 使用独立生命周期动画，不复用普通 read/write pulse。

### 7.3 长期重要性按事件步衰减

瞬态注意力只回答“Agent 刚刚看了哪里”，不能承担“长期哪些文件重要”。每个文件另有一个按 Agent 文件事件步衰减的长期状态：

```text
importance_raw(i, k) = previous * 2^(-(k - previous_step) / H) + action_gain + session_bonus
H = clamp(round(total_event_steps * 0.08), 240, 2400)
importance(i) = clamp(log1p(importance_raw) / log1p(P95(importance_raw)), 0, 1)
```

动作增量为 `Read=1`、`Write=2.5`、`Create/Rename/Delete=4`；一个此前未触达该文件的 session 首次访问时再加 `1.5`。同一个 session 中的重复动作仍被如实计数，但跨 session 反复使用会获得额外权重，两者不再完全等价。

长期重要性影响常态大小、常态亮度、中心引力和多体质量；它不产生 read/write 光环。四个自适应视觉半衰期结束后，长期重要性仍可保留，但会随新的 repository 文件动作逐渐衰减。这里的“重要”严格指 Agent 行为历史中的持续触达，不声称业务重要性、代码质量或 Git authorship。

### 7.4 播放节奏

- HTML 自动播放按最多 12 个视觉状态/秒准备 cursor；GIF/MP4 由 `agentsight vis` 对浏览器模型生成的每个布局快照各输出一帧、以 8 fps 编码，禁止在布局快照之上再次抽样。
- 文件动作数为 `E` 时，默认完整播放时长为 `D = clamp(8 + 0.04 × E, 8, 30)` 秒。
- 少于 550 个文件动作时，播放时长随动作数从 8 秒增长到最多 30 秒。
- 超长历史的 HTML 自动播放固定最多 30 秒；GIF/MP4 时长由 `S / 8 fps` 决定，360 个布局快照对应约 45 秒，不要求用户选择时长。
- 浏览器模型的总视觉步数为 `S = min(E, 360)`；播放 cursor 再按时长最多抽取 360 个。
- 当 `E <= S` 时，一个文件动作对应一个或多个过渡帧；当 `E > S` 时，按事件序号把连续动作放入视觉桶，每个动作仍更新累计状态，但同一桶只渲染一次平衡过程。
- 同一个 Tool event 触达的所有文件必须保留在同一视觉步；超长历史只合并相邻 Tool event，不能拆散一次操作。
- 长空档压缩，密集 burst 合并，但事件顺序不能改变。
- session 边界不产生额外视觉动作；当前动作说明显示 vendor、action、path 和真实 timestamp，session id 放在 tooltip 中。
- 一个视觉桶包含多个动作时，当前动作说明显示聚合摘要，例如 `Codex · 17 actions · 12 read / 4 write / 1 create`。
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
decayed long-term importance
lifecycle state
```

每个 Agent 文件事件后，当前可见文件运行固定次数的确定性力模拟：

```text
F_i =
    path_attraction_i
  + directory_attraction_i
  + local_importance_core_i
  + directory_envelope_i
  - repulsion_i
  - collision_i
  - damping_i
```

目录整体还受到目录层的二维力：

```text
F_directory =
    importance_centering
  - directory_repulsion
  - soft_envelope_collision
  - damping
```

位置是当前文件集合、路径关系和缓慢变化的长期重要性共同形成的暂时平衡。新增、删除、重命名和长期重要性变化会改变局部乃至整体布局；短期 attention 不参与位置计算。

### 8.2 路径和目录引力

文件间引力按以下顺序增强：

1. 同一 parent directory。
2. 最长公共目录前缀较长。
3. 同一 top-level directory。
4. 同一 extension 只能作为很弱的同分因素，不能主导布局。

目录不是节点，不拥有独立的 star。每次力计算只从当前成员位置即时求出目录质心、重要性和软包络，再把目录层的平移力等量施加给所有成员；这些计算态不进入输出数据，也不渲染为点、边界或固定 territory。同色文件因此形成可整体移动的星群，而不是由隐藏锚点固定。

为了避免 O(F²)，实现只建立局部不可见结构邻接：

1. 同 parent directory 的文件按稳定顺序组成低度数四叉吸引树，避免超大目录形成无法装入画布的长链。
2. 每个 parent 选一个代表；同 top-level directory 的代表再组成低度数四叉吸引树。
3. parent 内连接比 top-level 代表连接更短、更强。
4. 不因为 extension 相同单独建立引力关系。

力布局还把路径的前两段作为局部子星群，例如 `docs/design` 与 `docs/blog`。子星群之间具有软排斥，并被拉回所属 top-level directory 的即时质心；因此同一大目录可以呈现多个不规则路径岛屿，而不是一个均匀圆盘，也不会与其他 top-level directory 任意穿插。

邻接只参与力计算，永远不画成 edge。默认目标距离和强度为：

```text
same parent tree      distance=14..32 px  strength=0.14
same top-level tree   distance=34..68 px  strength=0.04
```

目录的视觉份额不与文件数线性对应。每个 top-level directory 先计算凹权重：

```text
directory_weight = (visible_file_count + 8)^0.4 * (0.8 + 0.2 * mean_importance)
```

归一化后使用 water-filling 把多目录场景中的单目录份额限制在 `max(0.42, 1 / directory_count + 0.08)`，再把剩余份额分给其他目录。这个份额只调整局部距离、静止星点密度和 top-level 吸引树的目标尺度，不生成目录节点、边界或固定 territory。大目录仍包含更多星，但其面积增长是次线性的；小目录不会被压成不可见的一点。

### 8.3 斥力、碰撞和阻尼

- 所有可见文件之间存在多体斥力，避免全部塌缩到一点。
- 近距离使用 collision force，保证星点和活动光环不会重叠。
- 不同 top-level directory 的软包络相互排斥；目录质心距离小于两个包络半径之和时，整个目录的成员获得同方向平移速度，避免颜色星域穿插。
- 使用速度阻尼抑制永久振荡。
- 目录长期重要性由 `0.7 × mean_importance + 0.3 × peak_importance` 得到；它控制整个目录质心的中心力，单个热点只能提高目录整体中心性，不能脱离目录独自飞向全局中心。
- 越过画布边界时反转并衰减速度，不能只截断坐标；只截断会让向外速度累积并把节点粘成矩形边框。
- 删除文件的质量和透明度逐步降为零，随后退出力场；其消失会触发周围文件重新平衡。

v3 默认参数使用 `1200 × 675` 逻辑画布：

```text
global_resting    = clamp(6 * sqrt(480 / max(480, visible_files)), 0.85, 6) px
directory_scale   = clamp(sqrt(directory_share * visible_files / directory_files), 0.52, 1.8)
resting_diameter  = clamp(global_resting * directory_scale * (0.62 + 0.38 * sqrt(importance)), 0.85, 6) px
focused_diameter  = resting + (10.5 - resting) * attention
many-body charge  = (-1.3 - 0.65 * radius) * importance_mass * directory_scale * density_scale
collision radius  = radius + 0.8 px
collision iterations = 2 (<=1000 files), 1 (>1000)
velocityDecay     = 0.38
directory radius = clamp(0.34 * sqrt(directory_share * canvas_area / π), 24, 140) px
directory center = alpha * (0.008 + 0.016 * directory_importance)
local core pull  = alpha * (0.0015 + 0.03 * file_importance)
ticks per visual step = 8 (<=200 files), 4 (<=500), 2 (<=1000), 1 (>1000)
```

高重要性文件受到指向本目录质心的局部核心力；低重要性文件在斥力和路径引力下形成更密集的目录外围。目录的重要性再决定整个星群离全局中心的距离。两层力与碰撞、包络和阻尼共同求平衡，不形成固定同心圆，也不给目录或文件预设最终坐标。

每个视觉步应用一个事件桶后重新加热模拟：read 使用 `alpha=0.10`，write 使用 `0.18`，create/rename/delete 使用 `0.35`；一个桶包含多种动作时取最大 alpha。tick 数按可见文件规模分档，输入、分档、seed 和事件顺序固定，因此不同输出格式可复现。

### 8.4 短期注意力不改变布局

最近触达的文件只临时增加视觉亮度和显示大小：

```text
Read       小幅、短暂增加
Edit/Write 更强、持续更久
Create     新质量进入系统
Delete     质量逐渐退出系统
```

短期 attention 不修改结构连接、目录质心、斥力或碰撞质量。一次 Read/Write 不得让星群抖动；只有它累积进长期 importance 后，才会缓慢改变文件在目录内的位置和目录整体中心性。

Read 的显式白环还要做视觉限流：每个布局快照只为当前 `strength` 最高的四个文件画紧凑细环，环直径固定为星点直径加 6 px，不随 `age` 向外扩张。其余同桶 Read 仍更新文件光晕、长期状态和顶部动作计数，但不各自生成扩散圆。这样保留“注意力到了哪里”的瞬时提示，同时避免长历史压缩后上百个白环遮住目录颜色和文件分布。

视觉增量为：

```text
attention_gain(read)   = 0.35
attention_gain(write)  = 0.75
attention_gain(create) = 1.00
attention_gain(rename) = 0.80

```

Create 在 6 个视觉步内把 opacity 和质量从 0 提升到 1。Delete 在 6 个视觉步内把 opacity 和质量降到 0，然后删除节点和邻接。Rename 保留同一个节点的坐标和速度，更新路径邻接，并在 6 个视觉步内完成位置再平衡和目录颜色过渡。

### 8.5 新文件出生

新文件从当前已经可见、路径最相近的文件旁边出生：

```text
同一 parent directory
→ 最长公共目录前缀
→ 同一 top-level directory
→ 当前同色文件位置的平均值
→ 画布中心
```

出生点只是动画初态，不表示 provenance、依赖或创建者。新文件出现后立即参与引力、斥力和碰撞，不沿固定轨迹飞向预设终点。

### 8.6 确定性和库复用

优先复用 tree-shaken `d3-force` 模块：

- `forceSimulation`
- `forceManyBody`
- `forceCollide`
- 自定义很薄的 path/directory attraction force

固定初始 seed、事件顺序、参数和每事件 tick 数。同一输入和 cursor 必须得到相同坐标，确保 HTML、SVG、PNG、GIF 和 MP4 一致。

禁止继续使用当前的“目录扇区 + golden-angle 半径 + 预设终点”算法。

## 9. 目录颜色继承

图上的实体只有文件 star。目录本身没有 star、标签、边界、polygon、KDE、radial lobe 或独立背景云。目录只影响两件事：文件颜色和路径引力权重。

每颗文件 star 可以带很小的同色柔光；同色 star 靠近后，光晕自然叠加成星域观感。这不是单独计算和渲染的目录云，因此不会再出现大面积均匀紫雾。

颜色使用感知较均匀的 OKLCH 空间。顶层目录获得稳定基色，子目录继承父目录色系并逐层变浅：

```text
H_top(rank) = (repository_seed + 137.508° × rank) mod 360°
L(depth)    = min(0.84, 0.58 + 0.055 × depth)
C(depth)    = max(0.08, 0.17 - 0.015 × depth)
H_child     = H_top + signed_hash(directory_path) × 8°
```

- `rank` 来自 repository 顶层目录名的字典序；完整 Git 文件边界可以参与颜色表分配，但未触达文件仍不进入画面。
- `repository_seed` 由 repository identity 稳定产生。
- `signed_hash` 的范围是 `[-1, 1]`，只让 sibling directory 有轻微区别，不改变父目录色系。
- 同一 repository、目录和 scope 中颜色稳定；新增文件不会让已经分配的目录重新换色。
- 例如父目录是红色，子目录是浅红色，下一层继续提高明度并略降色度，不突然跳成蓝色。
- 根目录文件使用同一稳定色表中的 `(root)` 色系，不创建特殊中心节点。

颜色过渡也由事件步驱动：

- 新文件从出生参考文件的颜色，在 6 个视觉步内过渡到自己的目录颜色。
- rename 到同一目录时颜色不变。
- rename 到另一目录时，沿 OKLCH 最短色相路径在 6 个视觉步内过渡到新目录色系。
- Read/Write 不替换文件的目录色；白色 read 光环和暖色 write 波纹只叠加在外部。

## 10. 文件视觉语义

| 视觉通道 | 含义 |
|---|---|
| 星点色相 | top-level directory |
| 同色系微调 | subdirectory |
| 常态明度 | 按事件步衰减的长期重要性；路径深度只提供很弱的修正 |
| 常态大小 | 全局文件密度、次线性目录份额和长期重要性的组合 |
| 瞬态大小 | 仅最近 Read/Write/Create/Rename 使星点短暂放大，随后按事件步回到基线 |
| 白色短闪/细环 | 最近 Read/Search |
| 暖色核心和扩散环 | 最近 Edit/Write |
| 绿色出生动画 | 明确或候选 create |
| 红色衰减 | 明确或候选 delete |
| 青色连续移动 | rename/move |
| 白色细边框 | observed untracked |
| 金色 artifact 外框 | commit reference，仅闪外框 |

最近动作的视觉增量必须明显强于长期重要性和路径深度的基线差异。主画面不得出现：

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

### 11.1 已实现的普通用户路径

当前 `agentsight vis` 实际调用链是：

```text
Claude/Codex/Gemini native sessions
        +
Git history / endpoint
        |
        v
agent-session Rust library
        |
        v
薄 Rust Nebula projection
        |
        v
JSON + browser runtime 内嵌进单 HTML
        |
        v
ECharts -> HTML / SVG / PNG / GIF / MP4
```

HTML 路径没有服务器、运行时网络请求、Python、Node 子进程或用户可见中间数据。`vis-gallery` 的旧链只为其他 31 张图和开发回归保留。

### 11.2 组件边界

Repository Nebula 应收敛为：

```text
agentsight vis (Rust)
        |
        v
agent-session Rust library
        |
        v
薄 Rust view projection
        |
        v
内嵌 browser runtime：d3-force state + ECharts renderer
        |
        v
单 HTML / SVG / PNG / GIF / MP4
```

原则是：

- `agent-session` 是唯一事件语义来源，并由 Rust 直接调用，不经过子进程 JSON 管道。
- 薄 Rust projection 只筛选五种文件动作和最小 Git reference，然后序列化进最终 HTML。
- 内嵌 JS 只维护动态力状态、交互播放和 ECharts option，不重新解释命令或事件语义。
- Nebula 不再经过完整 `project.py`。
- Git lifetime 和候选 durable change 由 `agent-session` 直接输出。
- 不写 canonical evidence artifact，不要求用户管理中间 IR。
- npm/Vite 只允许作为开发时构建 browser runtime 的工具；发布的 Rust binary 使用 `include_str!` 内嵌构建产物，用户机器不需要 Node 或 Python。
- HTML 输出不依赖外部程序；需要媒体格式时，Rust 只启动一个 headless Chromium、打开一个页面并构建一次原始 D3/ECharts 模型。SVG/PNG 从该页面导出；GIF/MP4 再调用 FFmpeg。缺少可选渲染依赖时打印明确安装提示，不影响 HTML 输出。
- 其他确实需要复杂 Git 聚合的静态图可以继续使用独立聚合逻辑，不能反向增加 Nebula 的复杂度。

### 11.3 每一步的数据形态和落盘规则

目标路径中的数据通过同一 Rust 进程内对象传递，不生成 `.json`、`.jsonl`、SQLite 或所谓 canonical artifact 临时文件。`agent-session-export` 的 stdout JSON 继续作为调试/兼容接口存在，但不在普通用户生成 Nebula 的路径上。

| 步骤 | 产生的数据 | 存放位置 | 是否落盘 |
|---|---|---|---:|
| `agent-session` library | Rust `LongitudinalArtifact`，包含 session、normalized events、Git lifetime 和候选 durable change | Rust 内存 | 否 |
| 薄 Rust projection | 只含 `meta`、五种文件动作和必要 commit reference 的内部 view struct | Rust 内存 | 否 |
| JSON serialization | 内嵌 HTML 所需的紧凑 payload 字符串 | Rust 内存 | 否 |
| 动态力计算 | `Map<path, FileState>`，其中包含 `x/y/vx/vy/visits/lastEventStep` | 浏览器内存 | 否 |
| HTML 组装 | CSS、内嵌 runtime、紧凑 JSON payload 和初始化调用组成的 HTML 字符串 | Rust 内存 | 否 |
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
      durable_change
    }
  ],
  commits: [committed_at_ms]
}
```

文件节点不需要作为第二份输入重复保存；它们可以从首次出现的文件事件增量建立。Git lifetime 只在 rename/delete/create 候选需要时随对应事件保留最小字段。

浏览器 runtime bundle 是项目构建时产生并通过 `include_str!` 嵌入 Rust binary 的代码资产，不是每次生成 Nebula 时产生的数据临时文件。生成 HTML 时 Rust 直接把它写入最终 HTML。

不同输出格式的磁盘行为如下：

- **HTML**：无临时文件，直接写最终 `.html`。
- **SVG/PNG**：Rust 在受 RAII 管理的临时目录写一个短生命周期 HTML，一个 headless Chromium 页面读取后直接导出最终文件，函数返回时自动删除临时目录。
- **GIF/MP4**：同一页面按布局序号渲染每个原始 snapshot，即使多个 snapshot 拥有同一毫秒时间戳也不会合并。每一帧只截图一次，PNG 字节不落盘并同时写入 GIF/MP4 的 FFmpeg stdin；导出不插入或替换 commit 帧，也不在最多 360 个布局 snapshot 上再次抽帧。

媒体导出只维护一个 Chromium、一个页面和一个 D3/ECharts 模型。页面按布局序号顺序渲染，GIF 与 MP4 编码器消费同一帧流，因此浏览器数量、输出格式数量和动画语义相互独立。

这里的浏览器截图只是内存中的编码帧，不是新的事件 IR、数据交换格式或用户产物。普通路径不会生成 `frame-NNNN.png` 目录。

交互式 HTML 首次打开时确定性预计算最多 360 个轻量 snapshot，并在页面内存中缓存。拖动时间轴通过二分查找选择最近 snapshot；snapshot 不嵌入 HTML、不写磁盘，也不成为用户需要理解的格式。

## 12. 实现和性能约束

- Agent 文件事件预先按时间排序，播放时增量处理。
- 路径吸引边只保留目录内或最长公共前缀的局部邻居，不能构造完整 O(F²) 边集。
- 多体斥力使用 quadtree/Barnes-Hut 实现，优先复用 `d3-force`。
- 每个视觉桶运行按文件规模分档的固定 ticks，并保存最多 360 个内存 snapshot；拖动时间轴不必从零重算。
- 背景、文件、活动核心和生命周期效果使用少量共享 series，不为每个文件创建 DOM 节点。
- 不引入 Cytoscape、uPlot、统一前端、生产 sourcemap 或额外服务器。
- 当前自动化覆盖 1,200 个 observed 文件；10k Agent 文件动作会先压缩到最多 360 个视觉步。更大文件规模需要单独做内存基准后再承诺。

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
- 图中只有文件 star；目录没有节点、star、标签、边界或独立云层。
- 不同 top-level directory 形成不穿插的软星群；包络只参与力计算，不可见。
- 高重要文件留在本目录核心；它提高整个目录的中心性，不成为跨目录离群点。
- 新文件出现会推动邻近文件重新平衡。
- 删除文件会退出力场并使局部重新平衡。
- 最近注意力只造成受控的局部扰动。
- 同一视觉桶包含大量 Read 时，显式白环不超过四个且不会随年龄扩张成主视觉。
- 持续跨 session 被触达的文件在没有瞬态光环时仍更亮、更大、更靠近核心。
- 久未访问文件逐渐缩小、变暗并在外围形成更密集的历史层。
- 大目录的视觉份额次线性增长；极端文件数差异不会按原始比例吞掉小目录。
- 同一输入、cursor 和参数得到确定性相同的布局。
- 图中没有可见 edge、directory label 或 territory boundary。

### 视觉和交付

- 用户无需 hover 即可从最小图例和当前动作说明区分 Read、Write、Create、Delete、Rename 和 Commit。
- 一次只生成一个图；HTML 只有一个 chart 和一个进度条。
- HTML 无网络请求；SVG、PNG、GIF、MP4 与 HTML 使用同一语义和坐标。
- 产物可以直接打开，也可以嵌入其他 Agent 生成的 report。

## 15. 实现顺序

1. 在 Rust collector 中实现简化 `agentsight vis` 入口及五步 stderr 日志。
2. 让 Nebula 直接消费 `agent-session` Rust 类型，移除 Python projection 依赖。
3. 复用 `agent-session` 已有的保守 Bash 文件 operand/redirection 推导，并补充 Read 路径投影。
4. 删除 endpoint context、目录节点/云和所有非文件 ambient marker。
5. 用确定性 `d3-force` 状态替换极坐标固定目标布局。
6. 实现目录 OKLCH 色系继承和 create/rename 六步颜色过渡。
7. 将注意力从真实分钟改为事件步衰减，并实现最多 30 秒、360 视觉步的自动播放算法。
8. 加入当前动作说明和完整最小图例。
9. 重新生成真实多 session HTML、PNG、SVG 和 GIF，逐帧视觉检查。
10. 更新 README、测试和示例，使它们只引用本文语义。
