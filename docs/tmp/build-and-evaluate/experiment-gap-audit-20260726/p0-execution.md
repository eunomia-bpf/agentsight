# P0 clean-room 数字、图与复现包门禁执行报告

日期：2026-07-26

输入审计 HEAD：`0ff0dce0c43bab092a92efe13c90fc6767487f14`

权威数据：

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/`

结论：**P0 全部门禁通过。** 论文消费端现在与 final-HEAD 数字一致；
RQ2 图显示修复后的 `6/6`，RQ4 图六项目逐项合计为 `121/111` 并保留
stopped 限定。正文和补充材料只替换数字，没有改 RQ 含义、限定语或结论
方向。

## 1. final-HEAD 全链重算

以下入口均成功执行：

```bash
python3 scripts/plot_rq1.py --input rq1-raw --output rq1-figures
python3 scripts/plot_rq2.py --rq1-root rq1-raw --output rq2
python3 scripts/plot_rq3.py --rq1-root rq1-raw --output rq3
python3 scripts/plot_rq4.py --rq1-root rq1-raw --output rq4
python3 scripts/headline_rq1.py
python3 ../rq-extensions-20260726/analyze_rq_extensions.py \
  --rq1-root rq1-raw --output ../rq-extensions-final-20260726
```

全链输出：

- RQ1：551 sessions，181,303 actions，551/176,288 attributed，
  5,746 artifacts，13,906 mutations，reuse `89.29--97.11%`，
  Spearman `rho=0.2000`；
- RQ2：recognized-success coverage `6/6`；
- RQ3：13,860 episodes / 13,906 source rows，repeat
  `74.6--90.8%`；
- RQ4：121 components / 111 boundaries。

## 2. 重生成并同步的图

| 图 | final 输出 | 论文引用文件 | 门禁结果 |
|---|---|---|---|
| RQ1 activity/progress | `rq1-figures/rq1-activity-progress.pdf` | `docs/paper/figures/rq1-activity-progress.pdf` | `973/1042`、`28/239`、`2450/6112`、`1210/5604`；同步 hash 相同 |
| RQ1 cumulative progress | `rq1-figures/rq1-progress-curves.pdf` | `docs/paper/figures/rq1-progress-curves.pdf` | final denominators 6112/5604/282/694/196/247；同步 hash 相同 |
| RQ2 validation | `rq2/figures/rq2-validation-dynamics.pdf` | `docs/paper/figures/rq2-validation-dynamics.pdf` | `n=2623`；`6/6 expose status=ok; coverage gate passes`；同步 hash 相同 |
| RQ3 repeated mutation | `rq3/figures/rq3-rework-structure.pdf` | `docs/paper/figures/rq3-rework-structure.pdf` | `6556/6588`、`74.6%`；同步 hash 相同 |
| RQ4 continuity | `rq4/figures/rq4-component-continuity.pdf` | `docs/paper/figures/rq4-component-continuity.pdf` | 31/28、24/22、29/28、18/16、2/1、17/16，合计 121/111；stopped 注记保留；同步 hash 相同 |

`pdftotext -layout` 对五张论文图的旧数字扫描为空。CSV-only clean-room
重画到临时目录后，五张 PDF 的提取文本与论文引用 PDF 逐字相同。

图像检查还发现 RQ1 activity 图的旧标签布局互相遮挡；只调整了标签偏移，
并把 validation exact fractions 放入图例。数据、坐标、标题和结论均未变。

## 3. 论文数字替换及出处

下表中的“论文位置”是替换后的文件行号；“出处”是 final-HEAD 记录行。

| 论文位置 | 替换 | final-HEAD 出处 |
|---|---|---|
| `docs/paper/main.tex:50` | repeat 下界 `74.5% -> 74.6%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv:2`（4890/6556） |
| `docs/paper/main.tex:269` | AgentSight persistence `974/1043 -> 973/1042`；ActPlane `28/245 -> 28/239` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv:2-3` |
| `docs/paper/main.tex:274` | repeat 下界 `74.5% -> 74.6%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv:2` |
| `docs/paper/main.tex:297` | RQ2 零突变上界 `86.8% -> 86.1%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/result.md:19`（2259/2623，由 `rq2-cycles.csv` 复算） |
| `docs/paper/main.tex:299-300` | AgentSight validation `2424/6111 -> 2450/6112`；ActPlane `1212/5604 -> 1210/5604` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv:2-3` |
| `docs/paper/supplement.tex:54` | repeat 下界 `74.5% -> 74.6%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv:2` |
| `docs/paper/supplement.tex:499` | AgentSight persistence `974/1043 -> 973/1042`；ActPlane `28/245 -> 28/239` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv:2-3` |
| `docs/paper/supplement.tex:500` | AgentSight validation `2424/6111 -> 2450/6112`；ActPlane `1212/5604 -> 1210/5604` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv:2-3` |
| `docs/paper/supplement.tex:604` | RQ2 零突变上界 `86.8% -> 86.1%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/result.md:19`（2259/2623） |
| `docs/paper/supplement.tex:625` | repeat 下界 `74.5% -> 74.6%` | `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv:2` |

审计点名的旧分子/分母和 `74.5%` 均已清零；同时清出了审计表未单列、
但仍来自旧 RQ2 lane 的 `86.8%`。

## 4. 复现包门禁

普通文件/命令清单：

- `docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/p0-reproduction-manifest.md`

数字复算入口：

- `docs/tmp/build-and-evaluate/experiment-gap-audit-20260726/reproduce_p0_numbers.py`

门禁结果：

- 清单解析得到 31 个仓库路径，全部真实存在并已跟踪或暂存；
- final RQ2 trajectory/cycles/coverage、RQ3
  artifact-load/episodes/summary、RQ4 components/boundaries 已加入复现包；
- RQ2--RQ4 原脚本新增 `--input-raw`，可仅从发布 CSV 重画论文图，不读取
  live HOME 或私有 native sessions；
- `headline_rq1.py` 改为从脚本位置解析仓库根目录，不再依赖本机绝对路径；
- `reproduce_p0_numbers.py` 从发布 CSV/JSON 重算 P0 论文数字，并对
  RQ2 `6/6`、RQ2 `86.1%` 和 RQ4 `121/111` 执行硬检查；
- full local event derivation 与 released-row figure rendering 两条命令链
  均已执行成功；
- 按用户要求未增加 hash manifest 或冻结仪式。

数据/图/复现入口提交：
`773d0ea75c12a1254ea3746aa8035858a175c7b0`
（`research: publish final RQ figure inputs`）。

## 5. LaTeX、页数、引用与 diff 门禁

执行：

```bash
cd docs/paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
```

结果：

- `main.pdf`：7 页总计；第 1--6 页为内容，第 7 页仅参考文献；
- `supplement.pdf`：17 页；
- 两个目标均无 LaTeX error；
- `main.log` 与 `supplement.log` 均无 undefined reference/citation；
- `\cite` 数量：main `12 -> 12`，supplement `16 -> 16`，合计
  `28 -> 28`；
- `git diff` 显示 main/supplement 只改数字；未删除引用，未改限定语；
- 旧值 `974/1043`、`28/245`、`2424/6111`、`1212/5604`、
  `74.5%`、`86.8%`、旧图 RQ1/RQ3/RQ4 数字及 final RQ2
  `3/6 expose status=ok` 在论文文本和五张新图中均不存在。

## 6. 最终判断

```text
run status: valid
tested hypothesis: supported（论文消费端与 final-HEAD 发布行一致）
research value: dependency-only
paper impact: 不改变 RQ、科学结论或限定；关闭 a/b/c 的消费端冲突并补齐 g 的本地复现入口
next paper decision: 可继续使用 final-HEAD 数字和新图；RQ4 estimator gate 仍 stopped
```

论文数字、编译 PDF 与本报告将在第二个提交
`research: align paper with final RQ results` 中提交；该提交即本报告所在
commit，最终 hash 由提交后命令输出记录。
