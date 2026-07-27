# 独立结果审查

## 结论

**最终判定：PASS。** 当前全量 run 完整、可复算，报告中的主要数字、分层分布、图和真实案例均有源数据或派生明细支持；未发现会使四组结论失效的实质方法错误。

```text
run status: valid
tested hypothesis: contradicted（强合取版本）；其中晚期重读上升和失败链稀少得到支持，但“启动税随 gap 增长”和“簿记文件总体更少回读”被数据反驳
research value: supporting
paper impact: additional RQ evidence，并给出 mechanism/workload boundary
next paper decision: 可写入稳健的晚期重读、启动长尾、约 6.5% harness-shaped footprint 和严格失败链稀少等分层事实；不要写成普遍 context degradation、gap 导致重建税、因果 harness overhead 或“文档几乎从不回读”
```

本次审查独立读取六个未压缩 source export，未导入 `analysis.py` 的计算函数；对关键指标另写一次性只读计算，随后才与 `manifest.json` 和 `raw/` 对照。输入的六个 SHA-256 与 manifest 全部一致。

## 完成性与复现路径

- 计划规定的六个项目均进入全量分析；主命令记录为 `python analysis.py`。
- 四个方向在 `report.md` 中均有独立的“方法、数字表、PNG、3–5 句解读、异常/真实案例”，最后有排序后的论文/后续发现。
- 产物含 8 张可解码 PNG，尺寸为 2520–3600 px；人工查看了 progress、startup、bookkeeping revisit 和 failure-cascade 图，标题、坐标、分层和稀疏点可读。
- `raw/section_eligibility_full_6x3_grid.csv` 明确物化完整 6×3 网格；空 cell 为 0/N/A，报告只对有足够样本的 cell 作趋势判断。
- `report.md` 的 30 个本地链接全部存在；`analysis.py` 通过 `py_compile`。
- 范围审计时，`git status --short` 对 `docs/paper/`、用户列出的其他 20260726 并行目录和本目录查询，只显示本实验目录为未跟踪项；脚本的写路径也仅为本目录的 `raw/`、`figures/`、`manifest.json` 和 `preflight.json`。

## 独立复算

### 1. Corpus 与会话漂移

直接逐个读取 `*.json`（不重复读取同内容的 `.json.gz`）得到：

| 指标 | 独立复算 | 报告 |
|---|---:|---:|
| project-root memberships | 551 | 551 |
| 全局唯一 `session_id` | 550 | 550 |
| 重复 membership root | `claude:0ee9082c-0794-444d-8dba-022dcfb5f370`，跨 2 项目 | 同 |
| project event rows | 181,303 | 181,303 |
| unique event IDs | 180,764 | 180,764 |
| 重复 project rows | 539 | 539 |
| worktree file actions | 69,922 | 69,922 |
| Claude / Codex / Gemini rows | 36,826 / 144,433 / 44 | 同 |

我另行按冻结的 root 排序、三等分、resolved action history 和 10-call re-edit 规则复算了所有 `L>=30` roots。233 个长 roots 及报告表中的全部 paired median 均一致。例如：

- AgentSight Claude/Codex 的 late−early reread 为 +17.16/+23.13 pp；
- ActPlane Claude/Codex 为 +16.67/+22.18 pp；
- eunomia Codex 为 +28.88 pp；
- 对应失败中位差、re-edit 中位差和 edit-calls/path 中位差也逐 cell 相符。

这支持“晚期 resolved reread 上升”，但失败和编辑碎片化的方向不一致，因而报告对强 context-aging 叙事的否定是由结果而非缺失分析造成的。

### 2. 启动税

我独立重建同项目、唯一 worktree、严格非重叠的最近前驱，并对每个完整前 10-call prefix 重算 instruction、root README、`git status/log`、前驱 artifact overlap 和 mutation overlap：

| 指标 | 独立复算 | 报告 |
|---|---:|---:|
| 完整 N=10 roots | 362 | 362 |
| 有严格前驱 | 348 | 348 |
| narrow q25 / median / q75 / p90 | 0% / 10% / 10% / 20% | 同 |
| extended q25 / median / q75 / p90 | 10% / 20% / 30% / 60% | 同 |
| instruction 为零的 roots | 98.62% | 98.6% |
| root README 为零的 roots | 91.44% | 91.4% |
| predecessor reread 为零的 roots | 52.76% | 52.8% |
| predecessor-mutation reread 为零的 roots | 81.22% | 81.2% |

各 `n>=10` stratum 的 Spearman 也一致：AgentSight Claude/Codex 为 -0.292/-0.058，ActPlane Claude/Codex 为 -0.022/+0.056，bpf Claude 为 -0.020，eunomia Claude/Codex 为 -0.760/-0.212，academic-writing-skills Claude 为 -0.599。没有正向 gap 趋势的结论成立。

审查期间发现的两处启动分析实现问题已经关闭：

1. 初版 startup distribution 图曾混入 `L<10` roots；当前 `save_startup_plots()` 明确过滤 `complete_prefix`，图与主表的 362-root denominator 一致。
2. 初版 strict git regex 漏掉 `git -C <path> status/log`；当前 regex 同时支持 `-C`、`--git-dir` 和 `--work-tree`，全量表和图已重跑。对当前 `startup_details_n10` 独立重匹配，280 个 strict-git tags 无一处不一致；案例 `claude:304fbd2c-976a-4791-894f-2fa166306a4d` 现在正确为 9/10、extended=90%。修复将总体 extended p90 从插值的 59% 更新为 60%，不改变主解释。

### 3. Bookkeeping / harness footprint

按报告列明的 path classifier、plan/Skill union 和 `status != fail` access 规则独立重算：

| 指标 | 独立复算 | 报告 |
|---|---:|---:|
| strict file bookkeeping calls | 10,147 (5.5967%) | 10,147 (5.60%) |
| strict gross calls | 11,743 (6.4770%) | 11,743 (6.48%) |
| strict exclusive calls | 10,733 (5.9199%) | 10,733 (5.92%) |
| broad gross calls | 12,756 (7.0357%) | 12,756 (7.04%) |
| adjusted strict gross | 11,349 (6.2597%) | 6.26% |
| unique-event strict gross | 11,743 / 180,764 = 6.4963% | 6.50% |
| bookkeeping reads / writes / W÷R | 9,079 / 3,467 / 0.3819 | 同 |
| ordinary project reads / writes / W÷R | 40,613 / 23,401 / 0.5762 | 同 |
| bookkeeping read≤50 | 1,627 / 3,221 = 50.51% | 50.5% |
| ordinary read≤50 | 11,911 / 22,779 = 52.29% | 52.3% |

每文件零读对照也重现为 bookkeeping 186/598=31.10%、ordinary 1,352/3,432=39.39%。因此“簿记文件总体写后几乎不读”的强怀疑确实不受支持；更窄的多数 stratum 回读较慢/较少仍可作为后续假设。

非阻断边界：当前 `exclusive` 的 ordinary-target veto 使用 resolved in-worktree `actions`。若把相对 `source_paths` 也一律视为项目内普通 target，会另将 53 calls 判作 mixed，使 exclusive 从 5.920% 变为 5.891%；但 `source_paths` 包含 shell 变量和未解析外部路径，不能可靠充当 resolved target。该 0.029 pp 敏感性不改变结论，论文措辞宜保留“exclusive proxy / resolved target”。

### 4. 失败链

我独立在每个 `(project, session_id, source_stream_id)` 内按 source ordinal 排序，重新构造 exact key、连续 fail run 和 full-stream mechanical outcome：

| 指标 | 独立复算 | 报告 |
|---|---:|---:|
| strict chains / member calls | 16 / 58 | 16 / 58 |
| project-row call share | 0.0319906% | 0.0320% |
| unique-event call share | 0.0320860% | 0.0321% |
| length q25 / median / q75 / p90 / max | 3 / 3 / 4 / 5 / 7 | IQR 3–4、p90 5、max 7 |
| patterns | edit 12、polling 3、remote 1 | 同 |
| full outcomes | exact recovered 13、observed unresolved 2、modified route 1 | 同 |

项目 × vendor 的 6 个非零 cell 及 local burden 也一致；其余 12 个完整网格 cell 为零。39 个 interleaved clusters 被正确保持为 sensitivity，没有混入 16-chain 主数。

## 源案例核验

至少以下案例可在原始事件中逐调用重现：

1. `agentsight / claude:5ba07bb3-7f75-40aa-a808-47abdf92aacc / stream 04df6fd07086c51e`：source tool ordinals 262–268 是对 `references.bib` 的 7 次连续 `Edit fail`；随后一次 Bash、一次 Read，再在 ordinal 271 `Edit ok`，即报告所述 3 calls 后 exact recovery。
2. `agentsight / claude:304fbd2c-976a-4791-894f-2fa166306a4d`：原始前 10 calls 中 9 calls 含 strict `git log/status`，第 10 call 使用 `git -C ... log`；当前 classifier 和报告均计 9/10。独立前驱重建给出约 0.02 h gap。
3. `ActPlane / codex:019e80ef-6c47-7023-9a42-dc9dc4db3a04 / stream a5ed645f7faec1be`：同 `session_id=28219` 的三次 `write_stdin fail` 后，下一次 exact target 为 `ok`。

这些不是仅由摘要表推断的轶事；session、stream、source ordinal、命令和状态都能回到 source export。

## 有效性边界与最终判断

- 这些是 source-verifiable proxies，不是对“遗忘”“浪费”“因果 harness overhead”或任务成功的真值标注；报告已持续使用限定语。
- 一个 root 可能包含并发 subagent 或跨时恢复；报告给了 per-stream failure ordering 和 >8h composite sensitivity。
- Claude/Codex 的 edit payload coverage 不对称；报告没有把 patch-line 指标当跨 vendor 主结论。
- Gemini 只有 3 个 roots；图表保留描述点，但没有由此作趋势判断。
- Bookkeeping 分类在 Skill 自身作为产品的项目上有明显构念混淆；adjusted sensitivity 已把 `academic-writing-skills` 的 gross 从 61.6% 降到 20.0%，报告没有把未调整值当浪费。
- Strict failure burden 只表示连续失败 member calls，不包括无法因果归属的所有后续诊断工作；报告同时给出 recovery distance 和 interleaved sensitivity，未把 0.032% 扩大解释成全部 failure cost。

综上，当前结果可作为一组 **supporting、边界清楚的 RQ 证据** 返回写作流程。最有论文价值的结论是跨多个足量 strata 的晚期 resolved reread 上升及其与失败/碎编辑不共变；最重要的负结果是 gap 未预测更高启动 proxy、簿记文件也没有更高的“写后零读”率。下一步若继续实验，应受控区分 continuation 与新任务、必要 re-grounding 与 context degradation，并接入原始 tool-result error text 研究 interleaved retry clusters。
