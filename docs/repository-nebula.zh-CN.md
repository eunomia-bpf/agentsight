# Repository Nebula：算法与输出约定

Repository Nebula 回放 Agent session 中可证明的 Git 仓库文件动作时间，而不是 commit
时间。图中只有文件星点；目录只影响颜色和力场，不产生节点、边界或标签。commit
不会移动文件；某一动作帧覆盖到 commit 时，只让最外框闪烁。

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

## 观测边界

数据直接来自 `agent-session` 已有的 Claude、Codex 和 Gemini 解析器。每个 Tool
事件只增加一个很薄的路径事实：原始路径及 `read/write/create/delete/rename`
访问类型。可视化不会复制 prompt、代码正文、网络内容，也不构造额外的通用 IR。

路径按 session cwd 解析，并且必须落在目标 Git 仓库或同一仓库的 worktree 中。
Gemini session 用其 `projectHash = sha256(cwd)` 恢复 cwd；有明确失败结果的工具调用
不进入文件生命周期。
读操作只保留 Git 历史、索引或当前工作区认识的文件；写操作允许新文件在首次
commit 前出现。`.git`、`node_modules`、`target` 和 `.cache` 不进入星域。
`--global` 会搜索 Claude/Codex JSONL（含 Codex 归档）和 Gemini JSON；即使 session
原本属于其他项目，只要绝对路径指向目标仓库也会收录。若外部 session 只留下相对
路径且没有可恢复的 cwd，则无法证明其所属仓库，因而不会猜测或收录。

这里的 shell 动作是从 Agent 记录的高置信度命令参数推导，并不等价于 eBPF 或文件
系统审计：脚本内部自行产生的文件变化可能不可见。这一边界也是不把 Bash、网络和
LLM 伪装成文件节点的原因。

## 时间与帧

动作按 `(timestamp, session-id, event ordinal)` 排序。同一 Tool 事件中的多个
文件动作属于同一个动作步。短历史每个动作步产生一个布局快照；超长历史在布局前
按顺序合并为最多 360 个桶。导出器不会再对这些布局快照抽帧：360 个快照会得到
360 帧 MP4 和 360 帧 GIF。默认 8 FPS，因此最长回放为 45 秒。

仓库根 commit 只定义时间轴起点。没有 Agent 动作的区间不生成虚构活动。

为保持与基线逐帧一致，路径的最终排序沿用浏览器 `localeCompare()`；ASCII 路径在
固定 Chromium 环境中可复现，Unicode 路径的跨 ICU/locale 位序不作保证。未来若
更换为 code-point 排序，必须作为带 golden snapshots 的显式视觉迁移。

## 文件生命周期

- 第一次 read/write 会让文件从相近路径附近进入力场。
- create 使用绿色扩散环；write 使用橙色双波纹；read 使用白色注意力环。
- rename 在目标动作中显式保存来源路径；同一 Tool 事件的多组 rename 各自配对，
  并保留原节点的速度、访问次数和重要性，只切换路径与目录颜色。
- delete 使用红色退出环，经过 6 个动作步渐隐后从力场删除。
- 目录永远不是星点。

新文件依次寻找最近的可见对象：同一父目录、最长公共目录前缀、同一顶层目录，
都不存在时才从仓库中心附近出生。出生角度由路径哈希决定，不使用系统随机数。

## 颜色

顶层目录按排序后的目录名分配 OKLCH 色相，相邻目录以黄金角 `137.508°` 分离。
仓库名和冻结的 Git revision 共同决定初始色相。子目录沿用父目录色相，并随深度
提高亮度、降低色度；因此目录相近的文件颜色相近，但没有可见目录边界。

rename 或从父节点附近出生时，颜色在 6 个动作步内从旧颜色过渡到目标目录颜色。

## 长期重要性与短期注意力

长期重要性与短期注意力相互独立。

长期重要性在每次访问时增加：read `+1`、write `+2.5`、create/rename/delete
`+4`；首次被一个新 session 访问再加 `1.5`。其半衰期为：

```text
H_importance = clamp(round(total_event_steps × 0.08), 240, 2400)
importance(t) = importance(t0) × 2^(-(t-t0)/H_importance)
```

长期重要性控制静态大小、亮度、目录中心吸引力和目录整体位置。很久未访问的文件
逐渐变小、变暗、变密集，但不会因为单个重要文件而脱离其目录星域。

短期注意力只控制瞬时放大、发光和波纹。其半衰期按动作桶压缩率计算：

```text
H_attention = ceil(total_event_steps / layout_snapshots)
visible_window = 4 × H_attention
```

read、write、create、rename 的初始强度分别为 `0.35/0.75/1.0/0.8`，随后按动作步
指数衰减。它不按真实分钟衰减，因此长时间无动作不会让当前注意力凭空消失。

## 目录份额与节点大小

顶层目录的原始权重为：

```text
weight = (file_count + 8)^0.4 × (0.8 + 0.2 × mean_importance)
```

份额经过上限约束，单一大目录通常不能占据超过 42% 的画布；小目录有伪计数保护，
避免文件数差异直接造成面积悬殊。文件静态直径随总文件数缩放到 `0.85–6 px`，
再乘目录单元尺度和重要性；被访问时最多放大到 `10.5 px`。

## 力场

布局保持现有 `d3-force` 的 velocity-Verlet 模拟，所有随机扰动使用仓库、路径和
动作步的固定哈希种子。每个快照按以下顺序执行：

1. 应用 create/read/write/rename/delete 动作并更新重要性；
2. 按顶层目录计算受限面积份额，并按前两级目录建立隐形簇；
3. 同父目录文件组成不可见四叉树弹簧，同顶层目录的父目录代表再组成较弱弹簧；
4. 文件执行 Barnes–Hut 多体斥力和圆形碰撞；
5. 顶层目录簇互斥，子目录簇向所属顶层目录中心吸引；
6. 重要文件向簇中心施加更强吸引，目录整体随重要性向画布中心移动；
7. 速度使用 `0.38` 阻尼，并把节点约束在画布范围内。

目录弹簧和簇边全部不可见。节点数超过 `1000/500/200` 时，每个动作桶分别执行
`1/2/4` 个 tick，否则执行 8 个 tick，以限制长历史成本。

## 渲染和编码

交互 HTML 使用 ECharts Canvas renderer。SVG 使用同一份 ECharts option 按需
渲染，因此坐标、大小、颜色和内容相同；抗锯齿可能与 Canvas 有细微差别。
PNG 直接来自合成 Canvas。MP4 通过浏览器 WebCodecs 和 Mediabunny 从这批 Canvas
帧编码；GIF 由同一个 MP4 转换，不重新计算布局。

命令行必须打印 session 扫描、文件动作、帧进度、GIF 转换、输出大小和总耗时。
任何优化都不得改变动作排序、固定种子、目录颜色、力参数或快照数量；视觉回归以
旧自包含 HTML 为基线逐帧比较，媒体文件还必须用 `ffprobe` 证明帧数相同。
