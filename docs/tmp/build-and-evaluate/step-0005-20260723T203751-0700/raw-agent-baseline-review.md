# Raw-agent baseline review：academic-writing-skills

## 结论先行

这份基线只读取 Claude、Codex、Gemini 的原生 session 记录和目标 workspace 的 Git/文件状态；没有读取 `agentvis/output/*trajectory-brief*`、`agentvis/src/diagnose.rs`，也没有读取其他 Agent 写出的诊断结论。

从可核验的原始动作看，这个仓库的长期工作不是均匀推进，而是四个明显阶段：

1. 6 月中旬建立并审查 auto-research、OSS、project-bootstrap 等第一批 skill。
2. 6 月底到 7 月上旬扩展 paper writing、citation、rebuttal、experiment 等工作流。
3. 7 月 11–13 日集中重构 auto-research orchestration：大量工作反复落在 orchestrator、experiment design、state-machine/reference 上。
4. 7 月 14–16 日进入“压缩复杂度，同时避免丢失约束”的修正阶段；同一组热点跨 session 被重新打开、修改、检查。

最强的过程信号不是“文档写完后无人使用”，而是**核心规范被频繁重读和重写，且修改强度远高于行为验证强度**。例如 Claude 原生事件中，`auto-research-orchestrator/SKILL.md` 有 15 次显式 Read、74 次 Edit/Write，跨 7 个 session；`hierarchical-research-state-machine.md` 有 6 次 Read、69 次 Edit/Write，跨 3 个 session。它们不是 write-only artifact，但存在明显的 specification churn。

验证只形成了局部闭环：有 `py_compile`、一个 synthetic `check_progress.py` 调用、若干 stale-token sweep；大量收尾检查仍是 `grep`、`wc`、`git diff/status`。这些能证明语法或文本一致性，不能证明修改后的 skill 会让 Agent 在真实任务上表现更好。原始记录中没有找到与这些核心 skill 改动对应的 held-out 行为回放或修改前后对照。因此，最值得用户介入的时点是：同一规范跨 session 再次被大改时，先要求一个真实任务上的行为证据，再决定继续加规则、删规则或扩展 reference。

## 证据范围与检索成本

本次检索发生在 2026-07-23；原生日志目录是活的，因此下列字节数是本次检索时的快照，不等同于稳定数据集版本。

| 来源 | 初始清点 | 与目标仓库直接相关的集合 | 本次深读 |
|---|---:|---:|---:|
| Claude `~/.claude/projects` | 2,249 个 JSON/JSONL，791,942,225 bytes | 目标 project 目录内 21 个 JSONL，11,763,831 bytes | 全部 21 个文件、3,589 条 JSON 记录、658 个 `tool_use` |
| Codex `~/.codex/sessions` | 6,471 个文件，48,322,860,536 bytes | 2026-06/07 中有 51 个文件包含 Tool call 的精确目标 `workdir`，合计 1,882,984,589 bytes | 深读 5 个代表性原生 session，12,041,471 bytes；其余用于精确路径候选发现 |
| Gemini `~/.gemini/tmp` | 120 个文件，24,678,887 bytes | 未命中目标仓库绝对路径 | 无相关 session 可深读 |
| Workspace | 181 个 tracked files；当前 worktree clean | 2026-06 起 Git 历史及当前文件树 | `git log`、path touch 次数、tracked file 类别 |

Codex 的 51 个候选不是 51 项独立任务：读取每个文件首条 `session_meta` 后，得到 12 个 top-level session 和 39 个 child session；39 个 child 隶属于 5 个 parent thread。另一个重要边界是：没有 Codex `session_meta.cwd` 精确等于目标仓库，但 Tool call 内嵌的 `workdir` 精确匹配目标仓库。因此这里把它们作为“确实操作或读取过该仓库”的证据，不把它们自动等同于独立开发 session。

Claude 的 21 个文件包含 16 个顶层 JSONL 和 5 个 subagent JSONL。其合计 Tool 动作为：181 Read、250 Edit、10 Write、198 Bash、5 Agent，以及 14 个其他 Tool call。`84ce8ab7...jsonl` 含 NUL padding；去除 NUL 后能恢复 98 条合法 JSON 记录。报告保留这个源质量 caveat。

### 实际检索步骤

1. 用 `find ... -type f -printf '%s'` 清点三种 Agent 的原生记录文件数与字节数。
2. 对 Claude 读取目标 project 目录中的全部 JSONL；对每条原始消息直接提取 `tool_use.id`、Tool 名、路径、时间戳和对应 `tool_result`。
3. 对 Codex 的 2026-06/07 原生 session 先搜索 Tool call 序列化文本中的精确模式：

   ```text
   \"workdir\":\"/home/yunwei37/workspace/my-paper-work/academic-writing-skills\"
   ```

   仅在候选集内读取 `session_meta`，再深读 5 个代表性 session 的原生 `custom_tool_call` / `custom_tool_call_output`。仅仅在 prompt 或文档正文中提到目标路径不计为行为证据。
4. 对 Gemini 原生记录做目标绝对路径搜索；无命中。
5. 在 workspace 中用 `git status`、`git log --name-only`、`git ls-files` 检查最终状态和 path touch 次数。Git 只作为 workspace 演化的外层佐证，不用于替代 Agent 动作时间。

## 主要工作阶段

### 阶段 A：第一批 research/OSS skill 建立与审查（6 月 13–17 日）

Claude session [`0dc25b6c...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/0dc25b6c-b2a5-43fe-bd7c-21d9372355bd.jsonl) 从 README、operating model、orchestrator 和 experiment skill 开始读取，随后修改相同文件：

- `toolu_01NjWMr1Bt4kRXrd2Ei4RmF8`：Read `auto-research-orchestrator/SKILL.md`。
- `toolu_01LHakg9o7kHiBqns9nLP7ot` 等 4 个 Tool call：Edit 同一 orchestrator。
- `toolu_013iJKfzfRbpTU2o4QGoiJvE`：Edit `docs/auto-research-operating-model.md`。
- `toolu_01AvGHDLyVSbKy4YaHBbRNyg`：Edit `README.md`。
- `toolu_01XrBXnvAoiMkgBdXTipty14`：最后用 grep 对十类 artifact 名称做跨文件一致性检查。

同一时期另外几个 Claude session 分别审查或修改 OSS workflow 和 project bootstrap。这里能确认的是“先读现有规范、再局部修改、最后做文本一致性检查”；不能从这些动作推断 skill 的真实下游效果。

### 阶段 B：工作流扩展（6 月底至 7 月 10 日）

最终 Git 历史显示这一阶段持续加入/修改 research startup、paper structure、iterative writing、citation verification、rebuttal 和 figure skills。Codex 原生 session [`019f3e80...jsonl`](/home/yunwei37/.codex/sessions/2026/07/07/rollout-2026-07-07T14-34-17-019f3e80-d0b0-7ad2-a0bb-ecffe1a1be43.jsonl) 提供了一个可直接核验的扩展示例：

- `call_Lrlt20ndBkRCa981YwlNn7MU`：对 `skills/rebuttal/SKILL.md` 应用补丁。
- `call_078VEtJUNleXYgIxXtyvMndx`：继续修改 rebuttal 的 sources reference。

这说明仓库热点并非只有 coding/auto-research orchestration，还包含论文写作与学术工作流；但这一 session 只能证明 rebuttal skill 被写入，不能证明它被成功用于真实 rebuttal。

### 阶段 C：orchestration 集中重构（7 月 11–13 日）

Claude session [`bd8b9dc5...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/bd8b9dc5-3915-48ea-b578-a3984e71ccd7.jsonl) 持续约 17 小时 45 分，含 222 个 Tool call：28 Read、113 Edit、6 Write、63 Bash、1 Agent，以及其他 Tool call。其动作集中在 orchestrator、hierarchical state machine、research-experiment-design 和 plan template：

- `toolu_01Lom7ZaCLmFWixGf9Ytrg5a`：Read orchestrator。
- `toolu_01HjmazN7UPB9jHXhy6kK68A` 与 `toolu_01QpsF66hDbabjxn6fWCUbJn`：Write hierarchical state machine。
- `toolu_01FDDqsjeZEUJ1uSyhfDiEWs`：Edit orchestrator。
- `toolu_01CYir5oa7qxVdQJUyU2q3Us`、`toolu_018N4eRKkfzcNadPQkLS96Jy`：Edit/Write experiment skill。

用户在同一原始 session 中多次改变或收紧约束，例如：

- message `61307618-bfcb-4029-86bf-8c81bbc2a8d2`：要求删除 state-machine reference 并去重重组。
- message `2e903d0c-5365-4aff-8a50-c074f424852f`：追问是否丢失关键正/负约束。
- message `0daf5f50-ff30-4f2c-ad03-d6a5228c1a7e`：质疑 Agent 擅自加入升级规则。

这是“探索—改写—用户纠偏—再次改写”的直接证据。把它称为失败需要额外判断；更保守的结论是：规范的决策边界尚未稳定，Agent 在没有用户明确授权时容易把建议升级成强制流程。

7 月 11 日的另一个 Claude parent session [`09103580...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/09103580-a390-4294-a6dc-3dcf933bfef0.jsonl) 通过 4 个 `Agent` Tool call 并行分析不同 third-party auto-research/research-skill 项目（`toolu_01HRmbj...`、`toolu_01SDcz...`、`toolu_0144Wv...`、`toolu_011t7...`）。这 4 个 subagent 是一项比较任务的分工，不能计成 4 项独立复现实验。

### 阶段 D：复杂度压缩与语义保全（7 月 14–16 日）

至少三个不同的 Claude parent session 回到同一组文件：

- [`e8db6d0d...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/e8db6d0d-4863-4c4e-837c-3a792bdc5987.jsonl)：65 个 Tool call；用户反复要求压缩、限制 baseline 数量、复用旧实验、减少报告文件和重复规则。
- [`48255634...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/48255634-a49f-48b5-ae0c-882112407193.jsonl)：102 个 Tool call，其中 69 Edit；用户追问“有没有丢掉原意”“是否浪费 token 做无意义 artifact 基础设施”“不要过分流程要求”。
- [`84ce8ab7...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/84ce8ab7-c3d6-4d6d-9e0e-52cfb62c97b1.jsonl)：继续压缩 `iter-refine-writing` 与 `iter-review-critique`，最后主要以 grep/status 检查。

这构成明确的跨 session 恢复：Agent 不是只在一个 session 内反复编辑，而是在后续日期重新读取并继续修同一组规范。`48255634...` 中 `toolu_018kRdwnXmA7T6Ku4wbyBHBD` 和 `toolu_01M1mzxEZ9auVUp71hYoF6xm` 重新读取两个核心 skill，之后产生多轮 Edit。Codex child session [`019f52ca...jsonl`](/home/yunwei37/.codex/sessions/2026/07/11/rollout-2026-07-11T13-07-03-019f52ca-64cf-7592-9007-06970a4a099c.jsonl) 也在 `call_xq2afTI10FuS1vOmLV5MTfuq` 中读取这些 skill/docs 的完整 diff；这证明它们后来被复审，但该 child 不能算独立开发任务。

## 热点与复用

### 显式 Agent 文件动作

下表只统计 Claude 原生日志中的显式 `Read`、`Edit`、`Write`，不把 Bash 内的 `sed`、`grep`、重定向或脚本副作用伪装成普通 Read/Write。

| 文件 | 动作总数 | 涉及 session | Read | Edit/Write |
|---|---:|---:|---:|---:|
| `skills/auto-research-orchestrator/SKILL.md` | 89 | 7 | 15 | 74 |
| `.../hierarchical-research-state-machine.md` | 75 | 3 | 6 | 69 |
| `skills/research-experiment-design/SKILL.md` | 38 | 5 | 11 | 27 |
| `.../bootstrap-research-project.md` | 20 | 3 | 4 | 16 |
| `skills/iter-refine-ideas/SKILL.md` | 20 | 1 | 6 | 14 |
| `skills/iter-refine-writing/SKILL.md` | 18 | 2 | 2 | 16 |
| `skills/evolve-agent-skills/SKILL.md` | 10 | 2 | 3 | 7 |
| `README.md` | 9 | 7 | 7 | 2 |
| `docs/auto-research-operating-model.md` | 7 | 4 | 6 | 1 |

因此，“核心 skill/文档大量写入但很少再看”只对部分 hotspot 的**读写比例**成立，不适合作为整个仓库的事实：

- orchestrator/state-machine 的确呈现高 mutation-to-read ratio；
- 但它们跨多个 session 被重新读取和再编辑，不是生成后遗忘；
- README 和 operating model 反而以 Read 为主，显示文档被后续任务复用；
- Bash 内隐式读取没有进入上表，所以不能用上表精确计算真实复用率。

更准确的诊断是：**规范热点发生高频再解释和再编码**。这可能来自需求仍在演化，也可能来自 skill/harness 容易诱导过度流程化；仅凭动作计数无法区分二者。

### Git 外层佐证

2026-06 起 path-level commit touch 次数最高的是：

| 文件 | Git commit touch |
|---|---:|
| `auto-research-orchestrator/SKILL.md` | 52 |
| `research-experiment-design/SKILL.md` | 33 |
| `README.md` | 27 |
| `docs/auto-research-operating-model.md` | 24 |
| `iter-refine-writing/SKILL.md` | 23 |
| `hierarchical-research-state-machine.md` | 23 |
| `research-state-machine.md` | 20 |

这个排序与原生 Agent 动作热点一致，增强了“orchestration 规范是主要返工区域”的可信度。它不说明每次 commit 是谁写的，也不说明每个改动好坏。

## 验证是否闭环

### 已确认的局部闭环

- `48255634...#toolu_01HUTy6z26kA1hx6YpA3WKGJ` 执行 `python3 -m py_compile skills/auto-research-orchestrator/scripts/check_progress.py`，结果含 `py OK`；同一调用清扫旧目录 token。
- `48255634...#toolu_01RfCyxZEJA9x75CbkNHgLBN` 清扫 “11 rounds” 等旧文本，结果无命中。
- `0dc25b6c...#toolu_01XrBXnvAoiMkgBdXTipty14` 对 artifact 名称做跨文件一致性检查。
- `bd8b9dc5...#toolu_01VufMqBadvx4HbjiXhhRHdd` 检查旧结构 token、文件行数和 Git 状态。

### 未闭环或含混之处

- `bd8b9dc5...#toolu_01GmuQoHwpqBXnBPxzsypP5u` 对 synthetic fixture 运行 `check_progress.py`，原始结果为 `exit=1`，但 Tool result 标记 `is_error=false`。没有足够上下文证明这个非零退出是预期告警还是失败，所以不能把它计为通过。
- `e8db6d0d...#toolu_01SVMd4mASJ4Re24uaC4DAca` 以 word/line count 验证“压缩”，结果显示 `research-experiment-design/SKILL.md` 从 2,179 words/274 lines 增至 2,229 words/281 lines。该 session 的部分文件变短，但“整体压缩成功”并不由这个结果支持。
- 当前 repo 只有 3 个 tracked Python 文件和 1 个 test 文件；核心工作主要是 Markdown skill。完整深读的 Claude 记录和 5 个 Codex 样本中，没有发现这些 skill 改动在 held-out 长期任务上的前后对照、下游成功率或行为回放。

所以可以说：**文本一致性与脚本语法有局部验证；skill 的行为效果没有在本样本中闭环。** 这是“未观察到”，不是证明系统中绝不存在其他实验。

## 值得用户介入的过程

1. **规范被再次大改之前。** 同一文件跨 session 返回且 mutation/read 比例很高时，应先展示：本轮要解决的具体行为失败、要保留的正/负约束、预计删除的规则。原始记录里用户多次在修改后才追问“有没有丢掉原意”，说明介入发生得偏晚。
2. **Agent 把建议升级为强制流程时。** `bd8b9dc5...` 中用户明确质疑未经授权的升级规则；`48255634...` 又指出 open RQ、strongest reject argument、review→experiment routing 可能把理想证据膨胀成强制实验。这是高价值的干预点：要求 Agent 区分“事实缺口、建议、硬约束”。
3. **继续增加 artifact/reference 之前。** 用户在 `e8db6d0d...` 和 `48255634...` 多次指出报告仪式、重复规则和无意义 artifact 基础设施。动作与 Git 热点也表明 state-machine/reference 是高 churn 区。新的规范文件应先回答“哪个已观察行为需要它”，而不是只凭完整性增加。
4. **文本检查通过、但准备把 skill 视为有效之前。** `grep`、`wc`、`py_compile` 只覆盖已知文本或语法错误。至少需要一个真实任务轨迹，比较修改前后是否减少空转、过量实验、报告文件或用户纠偏次数。
5. **删除或压缩关键约束时。** 三个后期 session 都出现“压缩”与“不要丢失含义”的张力。适合由用户只审语义 contract diff，而不是再次阅读整份 skill；原生轨迹已经能定位哪些条款在后续 session 中被反复恢复。

## 可以可靠回答与不能回答的边界

可以可靠回答：

- Agent 在哪些文件和模块上反复工作；
- 哪些工作跨 session 恢复；
- 显式 Read/Edit/Write 的顺序和 Tool call；
- 哪些检查确实运行、其原始退出或输出是什么；
- 用户在哪些时间点明确纠偏。

目前不能可靠回答：

- 某个规则是否在真实任务中提升了最终研究质量；
- 所有 Bash 命令隐含访问了哪些文件；
- 文档“被读”是否等于被 Agent 正确遵循；
- 高 churn 是需求自然演化、Agent 执行错误还是 skill/harness 根因；
- 未命中的 Gemini/Codex session 是否通过别名路径、容器路径或复制 workspace 操作过相同内容。

## 原始证据索引

Claude：

- [`0dc25b6c...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/0dc25b6c-b2a5-43fe-bd7c-21d9372355bd.jsonl)
- [`09103580...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/09103580-a390-4294-a6dc-3dcf933bfef0.jsonl) 及其 4 个 `subagents/*.jsonl`
- [`bd8b9dc5...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/bd8b9dc5-3915-48ea-b578-a3984e71ccd7.jsonl) 及其 1 个 `subagents/*.jsonl`
- [`e8db6d0d...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/e8db6d0d-4863-4c4e-837c-3a792bdc5987.jsonl)
- [`48255634...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/48255634-a49f-48b5-ae0c-882112407193.jsonl)
- [`84ce8ab7...jsonl`](/home/yunwei37/.claude/projects/-home-yunwei37-workspace-my-paper-work-academic-writing-skills/84ce8ab7-c3d6-4d6d-9e0e-52cfb62c97b1.jsonl)

Codex 深读样本：

- [`019f52ca...jsonl`](/home/yunwei37/.codex/sessions/2026/07/11/rollout-2026-07-11T13-07-03-019f52ca-64cf-7592-9007-06970a4a099c.jsonl)
- [`019f55a0...jsonl`](/home/yunwei37/.codex/sessions/2026/07/12/rollout-2026-07-12T02-20-08-019f55a0-7b27-7ef0-94b6-0fc3243ab246.jsonl)
- [`019f3e80...jsonl`](/home/yunwei37/.codex/sessions/2026/07/07/rollout-2026-07-07T14-34-17-019f3e80-d0b0-7ad2-a0bb-ecffe1a1be43.jsonl)
- [`019f53aa...jsonl`](/home/yunwei37/.codex/sessions/2026/07/11/rollout-2026-07-11T17-12-21-019f53aa-f8a8-7191-8378-346fb8a6db58.jsonl)
- [`019f8dea...jsonl`](/home/yunwei37/.codex/sessions/2026/07/23/rollout-2026-07-23T00-40-09-019f8dea-e4ad-7f03-9365-a47c66535f3d.jsonl)

没有按 `evolve-agent-skills` 的默认约定向目标仓库 `analysis/` 写 retrospective，因为本任务明确限制只能创建本报告、不能修改其他文件。

## 2026-07-24：与最新版 trajectory brief 的短对照

本节是在 raw-log baseline 完成后，才读取最新版
[`academic-writing-skills-trajectory-brief.md`](/home/yunwei37/workspace/agentsight-agent-nebula-research/agentvis/output/academic-writing-skills-trajectory-brief.md)
和
[`tool-first-natural-case-report.md`](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/tool-first-natural-case-report.md)
所得；它不改变前述 blind baseline。

| Raw baseline 结论 | 新版 brief 能否快速支持 | 仍需保留的边界 |
|---|---|---|
| orchestrator/state-machine 是持久热点 | **强支持。** brief 直接找出 10 个跨 session 重复修改的 artifact，并把 hierarchical state machine 排为 3 个 session、68 次 mutation 的首位。 | mutation 是定位信号，不证明缺陷、返工或浪费。 |
| 后期工作跨 session 恢复并覆盖前序修改 | **强支持。** `artifact-reaccess-after-session-gap`、`cross-session-validation-carryover` 和 handoff queue 直接给出 revival、supersession、later-validation association 与 open-at-cutoff 的端点。 | “later worktree validation”只是时间关联；不能证明该命令覆盖了每个 pending 文件。 |
| 核心文档不是写完即废弃 | **支持，而且比 raw baseline 更完整。** brief 给出 21 个 touched documents、4 个未观察到 reread、66 个 workspace later reads。 | Read 仍不等于理解、遵守或改善下游行为。 |
| 修改强度高于行为验证强度 | **部分支持。** brief 统计 250 个 confirmed mutations、9 个 recognized successful validations，并显示 204 个 mutation 在观察到 worktree validation 前已被后续修改 supersede。 | 这些数不能区分文本检查、脚本测试和真实 skill 行为实验；raw baseline 对 `grep`、`wc`、`py_compile` 与缺少 held-out 行为对照的判断仍需读原始命令。 |
| 工作经历建立、扩展、集中重构、复杂度压缩四阶段 | **只能提供骨架。** module transitions 和 session 时间序列能快速指出 `skills → third_party → skills` 以及后期持续聚焦 skills。 | 四个阶段的名字、目标和“压缩但保留语义”来自 prompt、Git 内容与深读，不是 JSD 或 module label 自动推出的。 |
| Agent 曾把建议升级为强制流程，用户反复纠正丢约束与 artifact ceremony | **不能自动支持。** brief 的 prompt preview 能把读者带到相关事件，但没有生成这个语义判断。 | 是否越权、为何失败、用户意图和规则含义必须回到原始对话；mutation count 不能代替。 |
| skill/harness 可能导致流程复杂化 | **仍不能归因。** 当前 `skill-footprint` 只观察到 1 个显式 Skill、1 个 session、0 个 mutation/validation。 | 现有数据不足以把复杂度归因给某个 skill，也不足以比较修改前后行为。 |

### External producer/consumer angle 的真实增量

这个角度有明确附加价值，而且是 raw baseline 的精确 `workdir` 检索没有覆盖的部分。Raw baseline 的 Codex 发现规则要求 Tool call 的 `workdir` 等于目标仓库；新版 `--global` 则找到 1,361 个 rooted elsewhere、但 Tool call 精确访问仓库路径的 session，其中 1,360 个有 read 且无 confirmed mutation。它还把内部 authoring reread（66）与外部 later reads（5,197）分开，并显示 `auto-research-orchestrator/SKILL.md` 有 1,275 次外部 later read。

对 skill/harness 仓库而言，这个区分是实质性的：artifact 的主要生命周期可能不是“作者 session 后来是否重读”，而是“其他 workspace 中的 Agent 是否访问它”。因此它能纠正把内部低 reread 误判成“无人使用”，也避免把外部消费者混入仓库自身的 module migration。就当前证据而言，最稳妥的新增结论是：

> Agent Nebula 可以分别重建持久 workspace 的内部生产轨迹和跨 workspace 的精确路径访问轨迹。

这比单纯热点图更有分析价值，但还不是“这些 skill 有效”或“外部 Agent 因此做得更好”。

### 当前 evidence 可能过度解释的地方

1. **“1,275 次读取”不是 1,275 个独立消费者。** 它是 read effect/call 数；同一 session、child session、parent task 或同一 Agent 可重复读取。论文层面还需要按 parent thread、外部 workspace 和 artifact generation 去重。
2. **“external consumption”最好暂称 external access footprint。** 精确 `sed`/`cat`/Read 证明访问了路径，但不证明内容进入了决策，更不证明 downstream outcome 改变。“actively consumed control artifact”比当前证据略强。
3. **after-first-mutation 不是 producer-generation attribution。** 文件会继续被修改；一次后续 read 不能自动归因到某次具体写入，也不能说明消费者读到的是哪一代语义。若要研究 producer→consumer，应记录 read 时可见的 Git/worktree generation。
4. **session rooted elsewhere 不等于独立任务或独立用户。** Raw baseline 已发现大量 child session 共享少数 parent thread。新版 brief 正确分离了 workspace/external origin，但还没有证明外部样本彼此独立或具有代表性。
5. **handoff queue 的“actionable”仍是产品假设。** 它确实给出比 aggregate count 更好的检查入口；但尚未前瞻性证明 takeover Agent 会使用队列、缩短恢复时间或减少错误。
6. **五个本地 workspace 只能构成自然案例。** producer/consumer 关系在 `academic-writing-skills` 上尤其明显，但不能据此估计一般长期 Agent workspace 的发生率，也不能单凭 closest-work 搜索提升为 novelty claim。
7. **两个结果文件不是完全相同的计数快照。** 最新 brief 报告 5,197 个 external reads after first mutation，tool-first report 写 5,196。差 1 很可能来自 live history 或生成时点，但在文件中没有共同 run/snapshot ID 可直接证明；论文表格合并这些数之前应固定输入清单和 revision。

综合判断：新版 brief **能显著缩短 raw investigation 的候选发现和跨 session join 阶段**，尤其能快速支持热点、恢复、交接状态和内外部访问分离；raw logs 仍负责阶段命名、用户意图、失败原因、越权判断和行为有效性。当前最可信的产品形态正是 tool-first report 所说的“source-linked evidence index for an Agent reader”，而不是自动 verdict generator。

## 2026-07-24：真实接管 Agent 复核（source snapshot `6e4e8df8800df84e`）

这次把最新版 brief 当作接管入口，重点查看 `action-strategy`、handoff、Skill footprint 和 root-external concentration，并严格限制为 10 个原始 Tool-call anchor。最新版已从前一节的 snapshot 更新为 126 个 included native sessions（17 workspace、109 root-external），因此本节数值取代前一节的旧 snapshot 数值；不同 snapshot 的计数不能直接拼接。

### 1. 对接管最有行动价值的三个 pattern

1. **Cross-session handoff queue：价值最高，但它是检查队列而不是未完成任务清单。** 它能把接管注意力立即缩到 76 个跨 producing-session 边界的 mutation generations，并列出 open、later-validation association 或 supersession。对接管者最直接的操作是先核对 open-at-cutoff 的高影响 skill、当前 Git 状态、后续提交和真实验证，再开始新修改。它比“这个仓库最近改了很多”有用得多。
2. **Action strategy：快速识别验证偏斜。** 24 个 mutating sessions 中，18 个没有 recognized validation；只有 5 个在首次 mutation 后观察到成功验证；14 个 mutation bursts 被成功验证关闭，24 个在 session/snapshot 末尾仍为 open burst。它足以把接管调查优先级放到“长 mutation burst、没有后续 validation marker”的 session，但不能把这些 session 自动判成错误。
3. **Root-external exact-path concentration：揭示分散在其他 workspace 的真实生产者。** 109 个 root-external sessions 中，24 个有 observed mutation effects，84 个有 reads 且没有 mutation effect。顶层 artifact 的 845 次外部 read actions 只分布在 14 个 root-external sessions、29 个 native source files 中，单 session 最多 257 次、中位数 27 次。这能提醒接管者：skill repo 的作者轨迹并不只在以该 repo 为 cwd 的 session 中，必须回到外部 parent task 才能理解修改原因。

`skill-footprint` 没进入前三：它只观察到 1 个显式 Skill、1 个 session、1 个 confirmed mutation、0 个 documentation mutation、0 个 validation，无法承担接管诊断。

### 2. 相比 raw-only review 的新发现

- **Raw-only review 严重低估了跨 root 的写入。** 当时只深读 5 个 Codex 样本并主要用精确 `workdir` 找候选；最新版 exact effects 找到 1,016 个 confirmed mutations 和 24 个 root-external mutating sessions。Skill repo 的长期演化实际包含来自 `geoperf`、`agentsight` 和 workspace-rooted parent session 的维护动作。
- **“外部”不是消费者的同义词。** Anchor `call_6EmBKmLdETcoXl8eeZ7PWkKF` 来自 cwd 为 AgentSight 的长期 parent，却直接修改 orchestrator 和对应 retrospective；`call_iYnPHSV4SpGZbAS65sJLvumK` 也从 AgentSight parent 一次删除 custom runner，并联动修改 5 个 skill/doc 文件。producer/consumer 应按 mutation effect 再分层，不能只按 root cwd 分。
- **规范修正延续到 raw review 未完整覆盖的后期。** `call_O0Q3sHetEZh9KbMKej1alQBA` 在 7 月 22 日同时修改 `oss-change-workflow/SKILL.md` 并创建 content-review-drift retrospective；用户上下文仍在纠正“不必要的审查”。这说明“复杂度压缩与授权边界修正”不是 7 月 14–16 日结束的阶段，而是持续维护主题。
- **行动顺序现在有了分母。** Raw review 只能人工判断若干 session 以 grep/diff 收尾；brief 能系统显示 inspection↔mutation 很常见，而 mutation→validation 只有 6 个 collapsed transitions。这个量化适合定位样本，但语义仍需 source follow-up。
- **外部访问高度集中，而非广泛独立采用。** 845 次 top-artifact reads 看似巨大，实际只来自 14 个 root-external sessions。Raw review 对“核心规范被复用”的方向判断成立，但最新版更清楚地表明复用集中在少数长期任务。

### 3. 仍会误导的标题和数值

- **“Non-overlapping native-session restarts require uneven repository re-grounding”不适合当前最大案例。** `action_time_to_first_mutation_ms=1,041,761,689`（约 12.1 天）和 1,052 个 read Tool calls 来自同一个以 `geoperf` 为 cwd 的 Codex parent session `019f1b45...`。`call_QPDgc5...` 在 7 月 1 日读取 orchestrator，`call_pFjGiQ...` 到 7 月 13 日才向 skill repo 写 candidate patch；中间时间包含长期 geoperf 工作，不是一次 restart 的恢复成本。这里应称“target-workspace read span before first observed mutation”，不能称 grounding cost。
- **“The action sequence exposes ... strategy”把观测序列说得过于有意图。** 167 个 inspection→mutation、153 个 mutation→inspection 是聚合 state transitions，不证明 Agent 采用了某种策略。更准确的标题是 “Observed inspect–mutate–validation sequencing”。
- **“mutation events”容易被理解成独立编辑调用。** `call_iYn...` 一个 patch Tool call 同时影响 6 个文件；handoff 会为这些 artifact 分别建立 generation。最大 142 mutations/cycle 和 76 pending generations 都不是 142/76 次独立决策。
- **“Unresolved workspace changes”比实际语义强。** open-at-cutoff 只表示未观察到 later recognized validation 或 supersession，不等于 Git 未提交、内容错误或用户尚未完成。队列甚至包含同一 patch 产生的多个 `__pycache__`/generated-scratch 行；真实接管应先降权这些条目。
- **`external-workspace-reuse` 仍容易被读成独立消费。** `call_Gp2ajn...` 的 cwd 是 `/home/yunwei37/workspace`，用户任务本身就是 review 并修改 skill；它并不是无关项目采用。`call_hmecn...` 与 `call_Dwr...` 在同一 AgentSight-rooted session 中相隔约 100 分钟反复读相同 state-machine，证明的是集中访问，不是两个消费者。
- **“successful validation”不是行为正确。** recognized marker 只能说明命令成功；Markdown skill 的文本/语义效果、真实下游行为和文件级覆盖都没有由 22 个 successful validations 自动证明。

### 4. 能否发现 skill/harness 导致的重复重读、文档负担或验证偏斜

**重复重读：可以发现候选，不能归因。** 顶层 artifact 有 845 次 root-external read actions，单 session 最多 257 次；两个核验 anchor `call_hmecn...`、`call_Dwr...` 确认同一 session 确实反复读取 state-machine。这与 harness 反复 re-grounding 一致，但也与“长期任务主动咨询持续变化的控制规范”一致。需要按 parent task、skill version、artifact generation 和 user turn 对齐，比较每次 reread 后是否出现新决策，才能称为无效重复。

**文档负担：可以看到 activity imbalance 和候选 clutter，不能把文档本身判为负担。** 最新 brief 有 958 个 confirmed document mutations、117 个 touched documents、33 个 never-reread documents；但这是一个以 skill/docs 为产品的仓库。`call_O0Q...` 一次同时修改 skill 并按 workflow 创建 retrospective，`call_iYn...` 则在用户“别加 py 脚本，太复杂了”的上下文中删除 runner并同步多个规范文件。这些是 `skill_bloat` / workflow ceremony 的调查入口，不是总体浪费率。要证明负担，还需任务级时间/调用成本、artifact 是否改变后续决策，以及删减后的对照结果。

**验证偏斜：证据最强，但仍是关联。** 18/24 mutating sessions 没有 recognized validation、24 个 open mutation bursts、mutation→validation transitions 仅 6，说明轨迹明显偏向 inspect/mutate 而非显式验证。另一方面，多数 artifact 是 Markdown，适合的验证可能是语义 review、用户 acceptance 或真实 downstream task，而不是 test command。当前可以诊断“缺少可观察的验证闭环”，不能诊断“这些修改没有被验证”。

**Skill/harness 因果：当前 verdict 为 `observe`。** 唯一显式 Skill anchor `toolu_01XJxH7XNcDbFjYU8gzCEXso` 只是启动 `agent-friction-analysis`；同 session 被归属的唯一 mutation 是后续 `toolu_01YYFf2m131wKC6oTUHJRG8N` 清理 empty dirs/`__pycache__`，与该 Skill 的行为效果没有可识别机制联系。大多数 auto-research skill 使用是通过读取规范、系统注入或隐式调用发生，缺少稳定的 Skill identity/version 和 invocation→decision→outcome 链。因此现有 footprint 只能证明 source-fidelity/attribution 覆盖不足，不能证明某个 skill 造成重复读取、文档负担或验证偏斜。

### 本次 10 个 source anchors

1. `019f1b45...#call_QPDgc5SQszITJeItwF9waoDy`
2. `019f1b45...#call_pFjGiQYqFztiQUMQcFCEyHSS`
3. `019f8765...#call_O0Q3sHetEZh9KbMKej1alQBA`
4. `019f4e0a...#call_6EmBKmLdETcoXl8eeZ7PWkKF`
5. `019f64a4...#call_iYnPHSV4SpGZbAS65sJLvumK`
6. `019ec966...#call_Gp2ajnTywAdC8V6Z9Vlpaodz`
7. `019ec23a...#call_hmecnUBzIFm5nFr8q6ehl47o`
8. `019ec23a...#call_DwrPLjBCXrjJ7hKGF9sM18PJ`
9. `9bd74ea0...#toolu_01XJxH7XNcDbFjYU8gzCEXso`
10. `9bd74ea0...#toolu_01YYFf2m131wKC6oTUHJRG8N`

接管判断：brief 已足以把数十 GB 原始日志缩成一个有用的调查队列；handoff 与 cross-root authoring 是真实产品价值。Action-strategy 和 Skill footprint 目前更适合作为 `observe` 级候选信号，不能直接生成 harness 归因或 skill 修改建议。
