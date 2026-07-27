# Compound shell/wrapper 路径边界对 RQ1--RQ4 的影响审计

日期：2026-07-26  
审计对象：`rq1-rq4-recompute-final/rq1-raw/events`  
结论：**MATERIAL（RQ1、RQ3）；RQ4 的组件/边界计数在 v2 所定义的同-worktree path-admission 边界内 immaterial。**

## 执行边界与产物

本审计只读取 held-out v2、final-HEAD RQ1--RQ4 事件与生成表。未修改
`docs/paper/`，未执行 Git 写操作，也未写入
`human-involvement-20260726/`、`invariance-mining-20260726/` 或
`rq7-heldout-20260726/`。所有新增文件均位于本目录：

- `audit_shell_boundary.py`：确定性扫描、ledger join 与敏感性上界；
- `compound_actions.csv`：逐 Tool call 的形态、路径容量与命令哈希；
- `exposure_summary.csv`：project/vendor 暴露面汇总；
- `heldout_failure_modes.csv`：v2 的 7 个差异 call；
- `rq1_sensitivity.csv`、`rq3_sensitivity.csv`、`rq4_sensitivity.csv`；
- `input_provenance.csv`：读取输入的 SHA-256。

复现命令（从仓库根目录运行）：

```bash
python3 docs/tmp/build-and-evaluate/shell-boundary-audit-20260726/audit_shell_boundary.py
```

## 1. v2 边界的精确定义

### 1.1 观察到的不是单向“漏解析”，而是 parser--oracle admission 分歧

v2 的完整 attempted-edge ledger 有 1,999 个 oracle edge、2,017 个
projection edge、1 个 missing 和 19 个 extra；20 个差异来自 7 个 native
Tool call。全部 1,865 个 edge-call status 与 70 个 session-order pair
一致。因此该边界精确定义为：

> 当一个 shell/custom-exec Tool call 需要理解多命令控制结构、shell
> 重定向/替换、wrapper 子命令或多操作数文件命令时，生产投影与冻结 v4
> oracle 对“哪些字符串应成为 strict artifact edge”发生差异；session
> identity、session order 和 call status 不受影响。

这一区分很重要。19 个 `extra` 不等于 19 个已证实的生产误报。逐 call
检查显示，多数 extra 是生产投影恢复了 oracle 没有进入的内层命令或
`git rm` 操作；唯一 missing call 中，冻结 oracle 自己把 `2>&1` 的末尾
`1` 当成路径并生成 `docs/1`。因此 v2 是有效的“相对于冻结 grammar 的
negative conformance”结果，但不是 20 条 filesystem ground-truth 错误的
证明。本审计按最保守方式把这些形态全部视为不可信。

### 1.2 七个 call、触发条件与具体路径操作数

| Project / call | 命令形态 | Oracle / projection 差异 | 被漏掉或错纳入的操作数 |
|---|---|---|---|
| bpf-benchmark / `toolu_014...` | `cp src1 src2 dir 2>&1`，多源复制加重定向 | 1 missing | production 因 segment 含重定向而丢弃整段；oracle 把 `>&`/`1` 当成最后两个 `cp` 操作数，最终形成伪路径 `docs/1`。真实 shell 操作数是两个 source 与一个 destination directory |
| ActPlane / `toolu_018...` | 三个 `cp` 链接到带跨行引号的 `git commit -m` | 3 extra | oracle 按行 `shlex`，未闭合跨行引号使首行整体跳过；projection 保留三个 `.claude/skills/*/SKILL.md` destination create |
| ActPlane / `call_j1...` | `git rm -r`，递归目录操作数 | 1 extra | oracle 不展开/不承认 `git rm` wrapper；projection 生成 scope delete `docs/corpus-rq1/smoke`，但不枚举递归 children |
| eunomia.dev / `call_s3...` | `rg ... && git rm -f p1 ... p11` | 11 extra | oracle 忽略 `git rm`；projection 为 11 个 PNG 操作数生成 delete |
| bpf-benchmark / `toolu_013...` | `diff <(sed ... main.tex) <(sed ... 2025/main.tex)` | 2 extra | oracle 把 process substitution 视为重定向边界并不进入；projection 将两个内层 `sed` 文件操作数投影为 read |
| bpf-developer-tutorial / `toolu_018...` | 首字符为反斜杠、换行/管道/重定向，call status=`fail` | 1 extra | oracle 跳过该 shell 形态；projection 保留失败 call 的 attempted read `src/52-fsession-latency/README.md` |
| eunomia.dev / `call_xa...` | `Promise.all([tools.exec_command(...), tools.exec_command(...)])` | 1 extra | oracle `unwrap_exec` 只解第一个静态 object；projection 解出第二个 command，并纳入中文 Markdown read |

116 道题中的 4 个错误只由最后两类中的两个 call 引起：

- bpf-developer-tutorial 的额外 failed read 使 P0 的 attempted calls/reads
  从 29/9 变成 30/10，造成 B1/B2 错误；
- eunomia.dev 的第二个 wrapped read 使 P0 从 44/21 变成 45/22，造成
  B1/B2 错误。

其余 18 条 edge 差异没有命中本次 B/C/D 题目的选中 identity，但仍使完整
ledger 失败。

### 1.3 本审计的两个扫描范围

为避免把“出现 `&&`”直接等同于“已知错误”，报告保留两层范围：

1. **Broad compound/wrapper**：多 shell segment/换行/管道、`bash|sh -c`、
   直接脚本解释器或 wrapper script、process substitution、以及 Codex
   JavaScript `exec` envelope 的并集。
2. **Held-out-trigger scope**：v2 七个 call 所暴露的可执行语法类并集：
   multi-source `cp|mv`、recursive/multi-operand `git rm`、process
   substitution、leading backslash、文件命令与重定向混合、跨行引号复合
   命令、multi-static-exec envelope。

“含路径操作数”采用
`max(projected distinct (access,path), independent lexical operands)`；
词法恢复仅进入已知 file commands、script invocation 与静态 nested
shell command。它是暴露/容量上界，不宣称每个候选字符串都是实际文件效果。

## 2. final-HEAD 暴露面

### 2.1 总量

final-HEAD 共 181,303 个 Tool call，其中 124,340 个被投影为 shell：

| 范围 | 形态 Tool calls | 占全部 | 其中含路径 | 占全部 | 形态内含路径比例 | 路径容量 |
|---|---:|---:|---:|---:|---:|---:|
| Broad compound/wrapper | 75,680 | 41.74% | 51,792 | 28.57% | 68.44% | 89,869 |
| Held-out trigger | 9,703 | 5.35% | 8,465 | 4.67% | 87.24% | 21,211 |

形态不是互斥标签。全语料中主要标签计数为：compound control 72,170、
`exec` envelope 14,538、redirection+file command 5,416、wrapper script
4,706、跨行引号复合命令 2,586、process substitution 1,249、multi-exec
envelope 864、`bash|sh -c` 48、multi-source `cp|mv` 36、recursive/multi
`git rm` 17、leading backslash 6。

### 2.2 Project 分布

| Project | All Tool calls | Broad | Broad+path | Held-out-trigger+path |
|---|---:|---:|---:|---:|
| agentsight | 97,586 | 48,185 | 33,089 | 4,335 |
| ActPlane | 66,238 | 21,097 | 15,501 | 3,493 |
| eunomia.dev | 13,876 | 5,593 | 2,688 | 481 |
| bpf-developer-tutorial | 1,664 | 377 | 209 | 66 |
| academic-writing-skills | 948 | 262 | 192 | 58 |
| agentskill-observability-paper | 991 | 166 | 113 | 32 |

绝对暴露集中在 agentsight 与 ActPlane；但每个项目都有 held-out-trigger
且含路径的 call，所以不能把风险局限到一个 workload。

### 2.3 Vendor 分布

| Vendor | All Tool calls | Broad | Broad+path | Held-out-trigger+path |
|---|---:|---:|---:|---:|
| Codex | 144,433 | 65,979 | 45,474 | 6,463 |
| Claude | 36,826 | 9,701 | 6,318 | 2,002 |
| Gemini | 44 | 0 | 0 | 0 |

Codex 的绝对数更高，主要因为 14,538 个 JavaScript `exec` envelope；Claude
也有 2,002 个 held-out-trigger+path call，因此这不是单一 vendor 边界。

## 3. 敏感性分析

### 3.1 上界模型与 materiality 标准

报告同时给两个层次：

- **Current-projection ablation**：删除当前已投影且来自风险 call 的
  mutation/introduction rows；若风险 call 当前是某个既有 mutation 的
  reuse/validation endpoint，则把该 endpoint outcome 置为不确定。它不
  假设任何新漏边，是更窄、更可解释的敏感性。
- **All-missed/wrong upper bound**：在上面的删除之外，每个独立候选路径
  最多新增一个 path outcome、翻转一个前驱 outcome，并按命令 effect
  上界新增 create/non-delete mutation denominator。这是用户指定假设的
  adversarial bound；它不是替代解析器的点估计。

判定标准为：任一论文比例的最坏变化达到 1 percentage point、任一资格
denominator 可消失、或 headline exact count/gate 可改变，即为 material。

### 3.2 RQ1：persistence、reuse、validation

下面先报告更窄的 held-out-trigger scope。Pooled baseline 与论文六个
project numerator/denominator 的合计一致。

| Metric | Baseline | 当前投影消融区间 | 最大变化 | All-missed/wrong numerator | denominator | 率上界区间 |
|---|---:|---:|---:|---:|---:|---:|
| Persistence | 1046/1348 = 77.60% | 1002--1019 / 1285 = 77.98--79.30% | **1.70 pp** | 0--6795 | 1285--6795 | 0--100% |
| Reuse | 12331/13135 = 93.88% | 11806--12063 / 12815 = 92.13--94.13% | **1.75 pp** | 271--18866 | 12815--18866 | 1.44--100% |
| Validation before supersession | 3890/13135 = 29.62% | 3671--3757 / 12815 = 28.65--29.32% | 0.97 pp | 0--18625 | 12815--18866 | 0--98.72% |

只看当前 projection 消融，persistence 与 reuse 已超过 materiality
阈值；不需要依赖 0--100% 的极端新增边上界来作结论。

与论文 project-level headline 的直接关系：

- 论文 later-reuse 范围是 89.29--97.11%。held-out-trigger 消融允许
  agentsight 的 91.18% 降至 87.99%，并允许 ActPlane 到 97.36%，所以
  headline range 与六项目排序都不稳健；相应的 Spearman
  \(\rho=0.20\) 也需要在修复后重算。
- 六个 persistence denominator 在 held-out-trigger 消融后仍均大于
  0，故 6/6 coverage 本身不被该窄消融推翻；但各项目比例可改变。
- Broad 消融更大：pooled persistence 为 30.00--35.52%、reuse
  94.89--97.17%、validation 12.30--16.65%；academic-writing-skills 的
  persistence denominator 可从 1 降到 0，使 6/6 persistence coverage
  变为至多 5/6。

完整逐项目 numerator、denominator、endpoint-sensitive rows 和容量在
`rq1_sensitivity.csv`。

### 3.3 RQ3：path locality

本审计直接从 final-HEAD event JSON 重建：

- 只保留 `ok|observed`、非-scope、具有 worktree/path 的 action；
- 每个 `(project, worktree, event)` 是一个 path-resolved call；
- 相邻 call 共享 exact path 或 top-level module 即为 local。

首先出现一个与 shell 边界独立的 provenance 问题：final-HEAD 重建范围为
**76.90--100.00%**，而 main paper 报告的 79.8--97.9% 来自 RQ6 的旧
local anchor，supplement 的 79.2--99.1% 又来自另一旧 RQ3 生成。当前
`rq1-rq4-recompute-final` 并未重跑 `plot_rq5.py`/RQ6 local anchor。因此
论文当前 RQ3 headline 不是 final-HEAD event 输入的同口径产物。

Held-out-trigger call 的“只重标当前已存在 path call、不新增漏 call”区间：

| Project | Final-HEAD baseline | 当前 call relabel 区间 | 最大变化 |
|---|---:|---:|---:|
| ActPlane | 88.96% | 81.62--90.53% | **7.34 pp** |
| agentsight | 87.21% | 78.62--88.76% | **8.59 pp** |
| eunomia.dev | 76.90% | 72.72--78.40% | **4.18 pp** |
| bpf-developer-tutorial | 93.61% | 91.43--93.99% | **2.17 pp** |
| academic-writing-skills | 92.65% | 91.54--92.87% | **1.11 pp** |
| agentskill-observability-paper | 100.00% | 100.00% | 0 pp |

若再允许当前 pathless 风险 call 被正确 admission，六项目完整上界区间分别
为 71.39--92.06%、70.59--90.63%、63.07--82.93%、84.51--95.08%、
81.10--94.72%、89.74--100%。因此 RQ3 是明确 material；“predominantly
path-local”这个定性方向在大多数上界端仍成立，但论文中的精确 range 与
跨语料 magnitude comparison 不能在修复前继续当作 final-HEAD 数字。

### 3.4 RQ4：components / boundaries

RQ4 component 与 boundary 由 `(project, worktree, native session)` 的
时间区间和 overlap 连通分量决定，而不是由 path label、artifact ID 或
module label 决定。v2 七个 call 的差异均是已归属 worktree 内的 path
admission 差异。

审计按 RQ4 原脚本重放 source-session intervals，并删除每个风险 call 的
所有 action-derived target worktree（保留 event 自身的 home worktree）。
Broad 与 held-out-trigger 两层在六个项目上均得到：

- component shift：0；
- boundary shift：0；
- 总数保持 **121 components / 111 boundaries**；
- ≥20-boundary gate 保持 agentsight、ActPlane、bpf-developer-tutorial
  三个项目，即 **3/6**，四项目 estimator gate 仍停止。

所以在 v2 精确定义的 scope-preserving path-admission 边界内，RQ4 的
**计数上界偏移为 0，immaterial**。有少量 final-HEAD 风险 call 当前包含
non-home worktree action；如果修复改变 worktree attribution，而不只是同
worktree 的 path admission，这属于另一个边界，本审计没有把它伪装成可
识别的数值上界。修复后仍应重跑 RQ4，以验证计数 0 偏移并更新 path/module
overlap panels。

## 4. Materiality 判定

### 判定

**总体 MATERIAL。**

- RQ1：held-out-trigger 的当前投影消融已使 pooled persistence/reuse
  最多移动 1.70/1.75 pp，并可改变论文 reuse range 与项目排序；
- RQ3：五个项目仅重标当前风险 call 就可移动 1.11--8.59 pp；而且论文
  RQ3 headline 另有 final-HEAD input provenance 不一致；
- RQ4 exact component/boundary count：同-worktree 边界下上界 0，
  immaterial，但 overlap/prefix 等 path-derived panel 仍需重算；
- All-missed/wrong adversarial upper bound 远大于上述消融，不能把该边界
  降格成一句 threat 后继续使用现有 exact projection-sensitive 数字。

## 5. 修复建议

### 5.1 Parser / projection 改动点

1. **用 clause AST 取代丢失结构的 token list。**  
   `agent-session/src/parser.rs::shell_segments` 应输出 command clause、
   pipeline、group/process-substitution 与 redirection node，而不是把
   `()|;&<>` 都压成无归属 segment。可使用经过 fixture 固定的 Bash AST
   parser，或扩展现有 lexer，但必须保留 operator ownership。

2. **重定向只剥离 redirection operand，不丢弃整个 file-command。**  
   当前 `shell_segment_actions` 一见任何 redirection token 就返回空。
   应把 `2>&1`、`> file`、`< file` 附着到对应 clause；`cp`/`sed` 的正常
   operands 继续解析，重定向目标按 read/write 单独处理。绝不能把 fd
   `1`/`2` 当文件路径。

3. **正确建模 multi-source `cp|mv|install`。**  
   `shell_segment_actions` 当前只取最后两个 operands。应把最后一个解释为
   destination，其余为 sources；当 destination 是目录时，source read
   可以精确，destination child identity 只有在 basename mapping 或 cutoff
   workspace manifest 可确定时才精确，否则输出 scope/abstain，不合成假
   exact path。

4. **显式处理 `git rm|mv` wrapper 与递归 scope。**  
   `git rm -r dir` 不应把目录字符串自动当成一个 exact artifact delete。
   strict ledger 要么基于 sealed workspace manifest 展开 descendants，
   要么只保留 scope action 并从 exact artifact estimand 排除；multi-path
   `git rm` 则逐 operand 处理。

5. **process substitution 作为嵌套 shell clause。**  
   `<(sed ... p)`/`>(cmd ...)` 中的命令可形成 attempted effects，但不能把
   `(`、`)` 或 redirection token 当普通操作数；外层 call status 继续独立
   保留。

6. **按每个 nested exec 保留独立 workdir。**  
   `tool_event_from_input`/`extract_tool_paths` 应遍历全部静态
   `tools.exec_command` 与 `tools.shell_command` object，而不是用
   “exactly one nested input”作为 effective input。支持 JSON/JS
   double/single/template static string 与静态变量；遇到动态 expression
   明确 abstain。每个 nested command 的 cwd/workdir 必须随 edge 保留。

7. **失败 call 的 attempted semantics 与 shell parse validity 分开。**  
   `status=fail` 不应自动删除 attempted edge，但 lexer 必须先判断哪些
   clause 实际可达/被 shell 接受。leading backslash、line continuation、
   comment 与 `set -e`/control operator 需要 fixture，而不是靠字符串前缀。

8. **把 cwd 放到 action/segment 层。**  
   `agentvis/src/repository.rs::inline_shell_cwd` 当前只能给整条命令一个
   resolved/dynamic 结论。应由 parser 为每个 clause/action 附带解析时
   cwd，使 `cd a && read x; cd b && write y` 不再共享一个模糊 cwd。

### 5.2 必须新增的回归 fixture

至少覆盖 v2 七个原始 call，并增加：

- `cp a b dir 2>&1`、`cp -- a dir`、`cp -t dir a b`；
- `git rm -r dir` 与 `git rm -- p1 p2`；
- 两个及三个静态 nested exec、不同 nested workdir、一个动态 nested
  expression（应 abstain）；
- `<(sed ... p)`、重定向与 pipeline 组合；
- 跨行 quoted commit message 前的 file command；
- leading backslash/comment、failed status 但前置 clause 已执行；
- `bash -c`、wrapper script 与 wrapper 内部不可见 effect 的明确边界。

生产 parser 与独立 oracle 不应复制同一实现；fixture 应同时断言 attempted
edge、confirmed edge、status、cwd、scope/exactness 与 artifact generation。

## 6. 修复后的最小重算集合

不需要重新采集 native transcript；从已冻结/已保存 source records 重新
投影即可。最小集合为：

1. parser unit tests 与 strict action fixture；
2. 新建 held-out conformance run（不要覆盖 v2），重跑完整 B/C/D 与
   attempted/confirmed/status/session ledgers；
3. final-HEAD 六项目 `research-rq1`，重新生成 events、
   `rq1-artifacts.csv`、`rq1-mutations.csv`、`rq1-summary.csv`；
4. RQ1 figures/headline，包括 project range、Spearman rho、persistence 与
   validation coverage；
5. RQ2 validation dynamics，因为 mutation/supersession intervals 来自同一
   路径投影；
6. RQ3 既要重跑 mutation episodes，也要以 final-HEAD events 重跑
   `plot_rq5.py` 的 allocation/migration，以及 RQ6 local anchor；这一步
   同时关闭本审计发现的旧-anchor provenance 不一致；
7. RQ4 accesses、components、boundaries、prefix/overlap panels；预期 count
   仍为 121/111，但必须由修复后的 projection 验证；
8. 只有上述生成值稳定后，才同步论文 exact counts、ranges、figures 与
   held-out limitation。

## 最终建议

**先修 parser/oracle 的 compound-shell 与 wrapper clause semantics，再重算
RQ1--RQ4；当前不要仅增加 threats 句子后保留所有 projection-sensitive exact
值。** RQ4 的 121/111 count 可暂视为对该特定同-worktree path-admission
边界稳定，但 RQ1 的 numerator/denominator、RQ3 path-locality range 和相关
跨项目比较均已达到 material 阈值。
