# Agent Nebula 是否需要重新设计：2026-07-22 评审

## 结论

视觉上只需要局部重新设计，不应推翻星点、目录色系和动态力场；实现顺序上必须先修正并校验数据投影，再增加动作余辉。

- **保留空间层：** 文件是星点；目录由稳定色系和不可见簇力表达；文件位置随路径结构、
  目录整体、重要性、斥力、碰撞和 temporal stability 动态变化。
- **重做动作轨迹层：** 当前动作、最近动作次序和 native root-session 边界必须比长期
  importance 更容易看见。
- **先校验测量输入：** transition、return gap、artifact fate 和 session continuity
  只能从通过 source-level conformance 的 action/path/lineage rows 计算；任何力布局
  坐标都不是科研统计量。

这不是“换一种更炫的图”，而是修复视觉主语：Agent Nebula 的主语应当是 Agent 如何
沿 workspace 移动并改变 artifact，背景星域只是它作用的空间。

## 判定依据

### 1. 实证结果支持空间轨迹，而不是静态热点

六个自然案例的 path-compatible anchor 中，跨顶层 module 的相邻动作占
2.1%--20.2%，合格案例在两次 module 访问之间严格介入的调用数中位数为 2--4。
独立公开样本包含四个 Open-SWE strata 各 64 个 task instance（256 条分层选择，跨
strata 为 255 个唯一任务 ID）和 64 个 IdeaTrail topic；跨 module 比例为
18.0%--30.0%，相同 return 距离中位数为 2--3。

因此 Agent 动作既不是完全随机跳转，也不是永远停留在一个热点：它通常局部工作，
会跨模块移动，并在很短的 action 次序内返回。目录聚类仍然有意义，但只显示累计亮度
不足以表达这种“离开—移动—返回”。

### 2. 现有媒体的空间层可读，动作次序不够可读

对 30 秒 ACTplane GIF 的六个等距时刻做视觉检查后：目录色团和仓库整体生长可见；
当前动作卡也能说明 Tool 和路径。但在数百到数千文件时，当前文件环相对背景太小，
只看星域无法恢复最近两三个动作去了哪里。终态 PNG 更只能表达累计结构，不能表达轨迹。

### 3. 当前实现与既定语义存在两个明确差距

1. 图形运行时只保存一个平滑后的 `state.focus`；新动作覆盖旧焦点，因此它表达“当前
   焦点”，没有表达“最近动作的空间次序”。
2. 短期焦点目前按 source `session_id` 重置，而事件已经具有 `native_session_id`。
   parent/subagent stream 共享 native root 时不应被画成一次失忆；只有新的 native root
   session 才应重置短期轨迹。

这两个问题可以在不改力场、不增加节点类型和不引入永久边的情况下修复。

### 4. 2026-07-23 的源数据校验改变了实现优先级

独立 source-direct checker 在同一批 72 份冻结 native session 上重建了 1,721 条
artifact edge。当前 trajectory 在 60 个 artifact-linked/cross-session 问题上得到
32 个正确答案和 28 个错误答案；六个项目的正确率差异也很大。这个结果没有否定星点、
目录色和动态聚类的视觉语法，但否定了“现有投影已经足够忠实，可以直接作为科研测量”
这一实现假设。

因此重新设计分成严格的先后关系：

1. 先区分 native Tool 参数直接证明的 file effect 与 Bash/path scope 推导出的弱 effect；
2. 校验 worktree-relative path、rename/delete/create identity 和 native-root session join；
3. 只有通过校验的 effect 才进入论文 estimand，较弱 effect 可以进入回放，但必须在
   动态图例和导出元数据中标明 evidence strength；
4. 数据契约通过后，再实现本页的最近焦点余辉和 session tick。

这不是把 Agent Nebula 改成另一种图，而是防止它把错误的 artifact 关系可视化得更有
说服力。

## 最小重新设计

### A. 最近焦点余辉，不画连线

每个有文件作用的 action 产生一个加权空间焦点。运行时保留仍高于可见阈值的焦点历史，
用逐步变小、变暗的空心光环表达先后次序；不连接成折线，也不固定保留 24 步或固定
N 个点。

```text
trail_strength(i,t) = evidence_i × 2^(-(t-i)/H_trail)
visible iff trail_strength >= epsilon_trail
H_trail = H_attention
```

当前 action 的环最大、最亮；越早的环越小、越暗。一次 action 同时作用多个文件时仍只
用一个焦点摘要位置，但各文件继续显示自己的 read/write/create/rename/delete 效果。

### B. native root-session 才是短期轨迹边界

- parent/subagent source stream 共享 `native_session_id`：轨迹连续。
- `native_session_id` 改变：清除短期余辉，从新 session 第一个文件 action 重新出现。
- repository state、文件 identity、长期 importance 和目录布局跨 root session 保留。
- 进度条只加一个细 session tick，不增加节点、边或大块提示。

### C. 当前动作必须压过背景重要性

文件很多时，静态星点继续随总文件数缩小；当前直接文件 Tool 的 halo 保持屏幕空间最小
可见直径，shell 推导和目录 scope 按既有 evidence scale 更弱。长期 importance 只控制
背景大小、明暗和目录整体质量，不能把当前动作淹没。

### D. 目录仍整体移动，活跃文件不能成为离群点

重要性增加作用于所属目录簇的整体质量和中心吸引，而不是给单文件一个把它拉出目录的
强中心力。路径弹簧、目录簇力、碰撞和 temporal stability 继续约束内部结构。Agent 的
短期移动由 halo/余辉表达，不靠把当前文件从目录中拖走来表达。

## 明确不做

- 不画永久 trajectory edge、read→write edge 或目录边界。
- 不把 Bash、Network、LLM、Skill 变成星点。
- 不让 Skill/语义标签控制颜色、质量、位置或目录引力。
- 不换成新的 3D、Sankey、process graph 或统一大前端。
- 不从星点坐标计算 transition、return、重要性或生产率。

## 验收方式

1. 合成 `A→B→C` 文件动作序列：同一 native root 内同时看到按强度递减的三个焦点位置，
   且没有 `lines` series；保留数量只由半衰期和 epsilon 决定。
2. parent/subagent stream 切换但 `native_session_id` 相同：余辉不重置；新的 native root：
   余辉重置，长期仓库状态不重置。
3. 1,000+ 文件时，当前直接 read/write halo 在 GIF 尺寸下仍可见；shell 和目录 scope
   明显更弱。
4. 新建、rename、delete 后，目录纯度、节点重叠和无关区域位移不比现有 golden case
   退化；活跃文件不会独自成为远离目录的离群点。
5. HTML、PNG、GIF、MP4 继续消费同一动作顺序和布局状态；compact 只选择输出帧，不能
   跳过中间状态推进。

## 科研位置

该改动首先是观测仪器的可读性修复，不单独构成“算法优越”的论文 claim。论文中的
过程关系必须由独立源数据校验后的 action/path/lineage estimand 支持；Agent Nebula
用来回放、导航和形成可核对案例。现阶段不应重做视觉骨架，也不应继续添加语义层；
优先级是 projection conformance。若未来要声称布局本身更好，必须另做跨帧追踪、目录
纯度、节点重叠和空间记忆评测，不能用当前实证结果替布局背书。
