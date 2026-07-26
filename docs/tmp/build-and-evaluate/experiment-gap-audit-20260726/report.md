# 实验侧发现核销审计（当前 HEAD）

日期：2026-07-26

审计 HEAD：`0ff0dce0c43bab092a92efe13c90fc6767487f14`

范围：只审计实验、证据、数字消费链与复现状态；不修改论文；不执行新实验；不提交。

## 结论摘要

| 项 | 判定 | 核心结论 |
|---|---|---|
| a. RQ1--RQ4 final-HEAD 复算与论文一致性 | **部分关闭** | 修复后的 final-HEAD 复算真实存在，扩展分析也已对齐；但当前论文仍消费了旧的 RQ1--RQ4 图，正文/补充材料还保留数个旧分子分母和 `74.5%`。 |
| b. RQ2 `6/6` vs `3/6` | **部分关闭** | final 结果表和正文口径已明确为“修复前 3/6、修复后 6/6”；但当前补充材料嵌入的 RQ2 图仍写 `3/6 expose status=ok; cross-case stop`，且 `docs/evaluation.md` 仍把 cross-case re-review 记为 open。 |
| c. RQ4 总数与 stopped 状态 | **部分关闭** | final 数据的正确总数是 `121 components / 111 boundaries`，正文和 evaluation 已采用；但当前论文图仍是旧逐项 `120/110`。RQ4 的四项目 estimator gate **仍 stopped**。 |
| d. conformance 60/60 | **仍开放** | `60/60 B+C` 是对同一 72 文件、同一 120 问题集、修复后代码和修正后 v4 oracle 的 repair-corpus 复验；没有 held-out 问题/语料，也没有最终修复后的全量边级等价验证。 |
| e. Raw baseline | **仍开放** | 没有任何 scoreable Raw 结果，计划的 `360/360` 行实际为 `0/360`；只完成了一次 retrieval-engaged Terra preflight，随后被 harness boundary monitor 中止。 |
| f. RQ5 单一合格项目 | **仍开放** | 五个 exact-context Skill strata 合格，但只有一个项目能做 two-Skill comparison；`p=0.750` 只是该单一项目内的负结果，不能形成跨项目结论。 |
| g. Data availability 与复现包 | **部分关闭** | 论文已新增 Data Availability 段落，且仓库中已有不少脚本、派生表和 corrected oracle；但没有可定位的实际匿名包/URL/manifest，release-only clean-room 复算未做，当前被引用图仍旧，且重算 RQ2/RQ4 所需 final event/raw rows 默认被忽略。 |

因此，原评审中“RQ1--RQ4 没有在最终修复后复算”这一主问题已由真实复算关闭；但“论文当前数字与该复算一致”尚未关闭。原评审指出的 conformance 外推、Raw、RQ4 stop、RQ5 单项目和复现包缺口仍然成立。

## 审计依据与版本链

原评审的实验侧发现来自：

- `docs/tmp/review/codex-fullpaper-20260726/codex-stdout.log` 末尾；
- 当时结论包括：RQ1--RQ4 先于 event-workdir 最终修复、conformance 为同语料修复复验、RQ2 口径冲突、RQ4 总数冲突且 stopped、RQ5 单项目、Raw 未运行、Data Availability/replication package 缺失。

当前修复与复算链为：

1. `d3189ea68` 修改 `agent-session/src/parser.rs` 和 `agentvis/src/repository.rs`，加入 event-workdir 修复与回归测试；提交说明同时记录 session join、failed-call effect、shell path extraction 已修。
2. 从 `d3189ea68` 到当前 HEAD，这两个生产测量路径没有后续 diff；`git log` 的最后相关修改仍是 `d3189ea68`。
3. `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/commands.log:16-103` 记录 release build、相同 cutoff、六个根目录、RQ1 提取和 RQ2--RQ4 重算，产出 5,746 artifacts、13,906 mutations、121 components、111 boundaries。
4. `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/delta-report.md` 将该次 rerun 与较早的 `rq1-rq4-recompute-20260725/` 分开，明确 final 值。
5. `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/result.md:5-53` 使用 final RQ1 export 重算 dormancy/revival 与 turnover/cooling；`result-review.md:11-34` 独立复算为零差异。

需要注意：`commands.log` 自称“current workspace revision”，没有把测量代码 HEAD 写进命令记录；但提交时序、`d3189ea68..HEAD` 对生产测量文件的零 diff，以及 rerun 结果提交时间共同支持它确实位于最终修复之后。该 provenance 足以支持本次核销，但正式复现包仍应显式记录 commit SHA。

## 逐项核销

### a. RQ1--RQ4 是否确实 final-HEAD 复算，论文是否一致

**判定：部分关闭。**

#### 已关闭部分：复算本身真实且位于最终修复之后

`rq1-rq4-recompute-final` 的权威行记录为：

- 551 admitted native roots，181,303 Tool actions；
- 551/176,288 worktree-attributed roots/actions；
- 5,746 observed artifact identities；
- 13,906 confirmed mutation rows；
- later reuse `89.29--97.11%`，Spearman `rho=0.2000`；
- persistence、validation 均为 `6/6`；
- RQ3 mutation episodes 13,860；
- RQ4 为 121 components、111 boundaries。

文件级证据：

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/commands.log:22-103`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/rq1-summary.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw/rq2-coverage.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq3/raw/rq3-summary.csv`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq4/result.md`
- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/delta-report.md:171-184`

当前论文已经正确消费的大部分 headline 包括：

- `docs/paper/main.tex:46-62,114-122,245-248` 的 551、181,303、176,288、5,746、13,906、89.3--97.1、`rho=0.20`、60/60；
- `docs/paper/main.tex:327-339` 的 RQ4 `121/111` 和 stopped 限定；
- `docs/paper/supplement.tex:537-590,708-730` 及主文 `264-279,308-325` 的 final extension 数字；
- 扩展数字已由 `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/result-review.md` 独立核对。

#### 未关闭部分：当前论文仍含旧数字和旧图

文本中的已确认差异：

| 位置 | 当前论文 | final-HEAD 记录 |
|---|---:|---:|
| `main.tex:267-269`、`supplement.tex:498-501`，AgentSight persistence | `974/1043` | `973/1042` |
| 同上，ActPlane persistence | `28/245` | `28/239` |
| `main.tex:299-300`、`supplement.tex:499-501`，AgentSight validation-before-supersession | `2424/6111` | `2450/6112` |
| 同上，ActPlane validation-before-supersession | `1212/5604` | `1210/5604` |
| `main.tex:50,274`、`supplement.tex:54,625`，repeat-episode range 下界 | `74.5%` | `74.6%`（`4890/6556`） |

更严重的是，当前论文中的五个 RQ1--RQ4 图 PDF 都与较早的
`rq1-rq4-recompute-20260725` **字节相同**，而与 `rq1-rq4-recompute-final`
不同：

- `docs/paper/figures/rq1-activity-progress.pdf`
- `docs/paper/figures/rq1-progress-curves.pdf`
- `docs/paper/figures/rq2-validation-dynamics.pdf`
- `docs/paper/figures/rq3-rework-structure.pdf`
- `docs/paper/figures/rq4-component-continuity.pdf`

从当前 PDF 提取出的旧值包括：

- RQ1 persistence `974/1043`、`28/245`，reuse `5570/6111`、`5437/5604`，
  validation `2424/6111`、`1212/5604`；
- RQ2 AgentSight 某 lane `n=2565`，且图下注记仍是 `3/6`；
- RQ3 AgentSight `6555/6587`、repeat `74.5%`，而 final 为
  `6556/6588`、`74.6%`；
- RQ4 academic-writing-skills 仍为 `16/15` components/boundaries，而
  final 为 `17/16`。

所以“final-HEAD 已重算”已关闭；“论文数字与 final-HEAD 记录一致”仍开放。

### b. RQ2 的 6/6 与 3/6 口径

**判定：部分关闭。**

final 数据无歧义：

- `rq2/raw/rq2-coverage.csv` 六行的 `qualified_with_success` 均为 `True`；
- recognized success 分别为 3,288、2,576、22、52、1、9；
- `rq2/result.md:3` 明确写 `6/6 projects expose a recognized successful validation`；
- `delta-report.md:85-115` 明确 `3/6` 只属于 frozen pre-hardening run。

当前文本也大体正确区分了历史与当前：

- `main.tex:291-306` 写修复后 all six；
- `supplement.tex:594-617` 写修复前 3/6、修复后 6/6；
- `evaluation.md:22` 写 `6/6 ... (was 3/6)`。

但冲突仍存在于当前论文图：

- `docs/paper/figures/rq2-validation-dynamics.pdf` 与旧图 hash 相同；
- 图中仍写 `3/6 expose status=ok; cross-case stop`；
- final 图 `rq1-rq4-recompute-final/rq2/figures/rq2-validation-dynamics.pdf`
  才写 `6/6 expose status=ok; coverage gate passes`。

此外，解释状态尚未完全闭环：

- `docs/evaluation.md:22` 仍写 “cross-case stop is lifted and its re-review is open”；
- `rq1-rq4-recompute-final/rq2/result.md:26` 仍写
  “this experiment does not close canonical RQ2”；
- 论文正文已经给出 cross-case description。

因此，数据口径是 6/6，但当前论文资产和结果审阅状态仍未统一。

### c. RQ4 总数矛盾与 stopped 状态

**判定：部分关闭；总数产物已修，论文图未同步；RQ4 仍 stopped。**

正确 final 值为：

| Project | Components | Boundaries |
|---|---:|---:|
| agentsight | 31 | 28 |
| ActPlane | 24 | 22 |
| bpf-developer-tutorial | 29 | 28 |
| eunomia.dev | 18 | 16 |
| agentskill-observability-paper | 2 | 1 |
| academic-writing-skills | 17 | 16 |
| **Total** | **121** | **111** |

证据：

- `rq4/result.md:5-12`；
- `delta-report.md:137-169`；
- `rq4-components.csv` 和 `rq4-boundaries.csv` 分别为 121 和 111 个数据行；
- `main.tex:327-339`、`supplement.tex:643-657`、`evaluation.md:24` 已采用
  `121/111`。

原来的 `121/108` 已从论文文本中消失，但当前
`docs/paper/figures/rq4-component-continuity.pdf` 仍是旧图：

- academic-writing-skills 仍显示 `16 components / 15 boundaries`；
- 六项目逐项仍合计 `120/110`；
- 该 PDF 与较早 `rq1-rq4-recompute-20260725` 图 hash 完全相同。

RQ4 的 stopped 状态没有改变，而且是正确保留：

- 仅按总 boundary 数，3/6 项目达到 20：28、22、28、16、1、16；
- estimator-specific final 覆盖进一步受限，例如 mutation-observed 为
  17、14、21、8、1、7，artifact-overlap-defined 为
  15、14、19、7、1、5；
- 因而没有四个项目对相应 estimator 达到 `n>=20`；
- final `plot_rq4.py:605-608` 仍生成
  `All four-project gates stopped`；
- 当前正文明确把结果限制为 data-limited within-case/coverage evidence。

### d. conformance：同语料修复复验、held-out 与边级验证

**判定：仍开放。**

狭义结果是真实的：

- 修复后的 projection 在 corrected v4 oracle 上为
  A `12/30`、B `30/30`、C `30/30`、D `30/30`；
- `docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/workdir-fix/result.md:50-107`
  记录了最后 workdir fix 后的全 120 行 question-level 比较；
- 当前论文把它限定为 `repair-corpus conformance`，没有再声称一般能力。

但它仍是同语料、同问题集的修复后验证：

- `docs/evaluation.md:129-135` 明确 Step 0004 和后续复验复用同一 72 个
  archived native files；
- `codex-oracle-task.md:21` 要求在 `SAME frozen data` 上重导全部 120
  expected answers；
- v4 改了 24/120 个 expected answers，但没有生成新的 held-out
  question set；
- workdir 修复后仍在这 120 个问题上重放，只改变目标两行。

没有 held-out 证据，也没有最终修复后的全量边级验证：

- `corrected-oracle/result-review.md:5-6,29-46` 明确批准范围只是
  same-question reassessment，**不是 edge-level equivalence**；
- 该 review 要求未来 version-consistent freeze、full edge-ledger
  comparison 和 adversarial fixtures；
- workdir-fix 结果完成的是 120 个 question rows，不是所有 source event
  到 projected edge 的 precision/recall 对账。

所以 `60/60` 可作为窄范围 regression/conformance gate，不能关闭
held-out 泛化或 edge correctness 缺口。

### e. Raw baseline 是否实际运行，补跑可行性与成本

**判定：仍开放；未实际完成，补跑技术上中等偏高可行，但必须作为新实验。**

实际状态：

- 计划矩阵需要 6 projects × 20 questions × 3 repetitions =
  **360 Raw rows**；
- `result.md:48-53` 和 `result-review.md:43-49` 明确 none of 360 ran；
- `raw/raw-preflight-attempts.json` 记录四次尝试均为 0 scoreable answers：
  两次 transport/monitor 缺陷、一次 900 秒 timeout、一次 Terra
  boundary stop；
- Terra 尝试确实 engaged retrieval：11 tool calls、117,184 returned
  bytes、99.74 秒，但没有最终答案；
- 因此论文中 Raw=N/A 是正确处理，不应算 wrong/abstain，更不能支持
  trajectory superiority。

当前补跑资产：

- 224 MiB 的 frozen private corpus 仍在本地；
- 72 个 archived source files、workspace cutoff blobs、freeze/question
  metadata 都在；
- `agentvis/research/rq7_measurement.py` 的 sandbox、model call、scorer、
  360-row full-run 路径仍在；
- `/usr/bin/bwrap` 和 Codex CLI `0.145.0` 可用。

当前阻塞：

1. 旧 experiment 已按预注册规则关闭，不能把修 harness 后的执行伪装成
   原实验续跑；
2. `rq7_measurement.py:2610-2634` 的 command-string monitor 仍会把证据中
   出现的原始绝对路径当作访问行为，原 Terra failure 可复现；
3. 新 run 必须使用 corrected v4 answers，并重新冻结 model/version、
   prompt、预算、retry policy；
4. 需要可用的固定模型与认证；这是主要现金成本和可用性风险。

按原预算，完整补跑为 18 个模型调用，每个最多 15 分钟、64 retrieval
calls、1 MiB returned tool bytes、64 KiB output。串行最坏 wall time 为
270 分钟（4.5 小时）；累计上限为 1,152 retrieval calls 和 18 MiB
returned bytes，另加 18 次模型推理费用。预期产出是 360 Raw result rows、
18 个 Raw cost rows，以及与 trajectory B+C accuracy/cost 的 matched
comparison。

### f. RQ5 单一合格项目限制

**判定：仍开放。**

当前证据：

- 六项目共有 67 explicit Skill invocations 和 1,675 attributed actions；
- independent checker 对 2,063/2,063 streams、7,304 signal rows 和
  205,836 adjacent boundaries 对账无误；
- 五个 exact-context Skill strata 达到至少三个 native roots；
- 但只有 `agentskill-observability-paper` 在同一
  project/vendor/model/source-role stratum 内有两个合格 Skill；
- 该项目内 same/different median JSD 为 `0.116/0.123`，9/10 pairs，
  exact root-block `p=0.750`；
- leave-one-project-out 为 N/A。

文件级证据：

- `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq5-skill-footprints/result.md`
- 同目录 `full-six-projects/figures/result.md:18-32`
- `docs/paper/main.tex:341-360`
- `docs/paper/supplement.tex:732-757`
- `docs/evaluation.md:25`

这是一个诚实的单项目负结果，不是跨项目“Skill 无 fingerprint”的充分
证据；论文目前用 “only eligible comparison” 限定，表述边界基本正确，
但实验缺口未关闭。

### g. Data availability 声明与复现包

**判定：部分关闭。**

已关闭部分：

- `docs/paper/main.tex:498-503` 已新增 Data Availability；
- 声明说明 raw native sessions 含 private prompts/paths、不可分发；
- 当前仓库已跟踪 final RQ1 artifact/mutation/summary rows、扩展分析十个
  CSV/JSON、final 分析脚本、corrected v4 answers/oracle artifacts，以及
  Step 0004 的公开 result rows。

未关闭部分：

1. 声明仍写 `repository (link on OpenReview)`，仓库中没有可核验的实际
   URL、release archive、manifest 或 package README；
2. 没有从仅含拟发布文件的 clean clone/container 执行一键复算；
3. `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/commands.log`
   被根 `.gitignore` 的 `*.log` 忽略；
4. final `rq1-raw/events/` 被目录 `.gitignore` 忽略；
5. final RQ2/RQ3/RQ4 的 `raw/` CSV 被根 `.gitignore` 的
   `docs/tmp/**/raw/` 忽略；
6. 因缺少 final event ledger，仅凭当前 tracked RQ1 artifact/mutation
   rows不能从头重算 RQ2 cadence 或 RQ4 component/boundary；
7. tracked `rq1-raw/projects.json` 含本机绝对路径
   `/home/yunwei37/...`，与“anonymized repository”不一致；
8. 当前 paper figures 仍消费旧复算，说明尚无 release-number gate。

所以“声明存在”已关闭；“声明与可发布、匿名、独立可复算的包相符”仍未
关闭。

## 按论文价值排序的可执行方案

下面把科学实验与依赖性完整性工作分开。P0 不增加研究价值，但必须先做，
否则任何新实验数字仍可能在论文消费端漂移。

### P0（立即，dependency）：final-HEAD clean-room 数字与复现包门禁

**对应缺口：a、b、c 的消费端不一致，以及 g。**

- **输入数据：**
  `rq1-rq4-recompute-final/rq1-raw/` 的 final export、RQ2--RQ4 final raw
  CSV、`rq-extensions-final-20260726/`、corrected v4 oracle；对 native
  event export 生成最小可发布的去敏 ledger，保留 project pseudonym、
  native-root block、event order/time、effect/status、relative artifact
  identity、validation 和 session-component 字段，删除 prompt/code、
  username、绝对路径和 secrets。
- **脚本：**
  `headline_rq1.py`、`plot_rq1.py`、`plot_rq2.py`、`plot_rq3.py`、
  `plot_rq4.py`、`rq-extensions-20260726/analyze_rq_extensions.py`，外加
  一个普通 shell/Make target 在 clean container 中顺序运行并比较
  `paper-number-ledger.csv`。这只是复现入口，不是新的实验控制系统。
- **执行：**
  从只含发布包的 clean checkout 运行；不得访问 live HOME 或原 raw
  sessions；重新生成全部表和五个 RQ1--RQ4 图；独立审阅 final RQ2
  interpretation；对论文中所有显式数字做 exact/rounded ledger 比较。
- **预计产出：**
  `README`、一条运行命令、环境/commit/cutoff 记录、SHA-256 manifest、
  去敏 source-linked rows、全部派生 CSV、regenerated figures、数字
  ledger 和 clean-room result review。
- **影响数字/结论：**
  不改变科学结论；会把 persistence 修为 `973/1042`、`28/239`，
  validation 修为 `2450/6112`、`1210/5604`，repeat range 修为
  `74.6--90.8%`，将 RQ2 图改为 6/6，并让 RQ4 图显示 121/111。
  只有该门禁通过后，Data Availability 的“every statistic is
  recomputable”才有本地证据。

### P1（最高科学价值，decisive）：held-out question + full edge-ledger conformance

**对应缺口：d。**

- **假设：** 冻结后的 projection 不仅在 repair corpus 的 selected
  questions 上正确，也能在未参与修复的数据上保持 artifact/session
  fact correctness 和 edge-level precision/recall。
- **输入数据：**
  优先选择作者无关项目；最低可接受方案是在六项目中取完全不属于原 72
  文件、且未用于 bug taxonomy 的 72 个 disjoint native root files。
  在看到 projection 输出前，按相同四 family 固定模板生成新 120 问题。
- **脚本：**
  复用 `agentvis/research/rq7_measurement.py`、
  `rq7_source_oracle_check.py` 和 v4 oracle grammar；新增的独立 checker
  只负责对 held-out bytes 生成 question answers 和全量
  attempted/confirmed edge ledger，不能导入 projection。
- **执行与正确性：**
  先固定 code commit、source manifest、question templates 和 exclusions；
  对所有 held-out Tool calls 比较 session order、attempted edges、
  confirmed-effect edges、status 和 workdir resolution；adversarial
  changing-cwd、failed-call、inline-cd、wrapped-patch fixtures 只作
  correctness controls。
- **预计产出：**
  新 120-question held-out matrix；B/C/D exact scores；按 vendor/project
  的 edge precision、recall、F1 和 error taxonomy；完整 edge-diff CSV；
  independent result review。
- **影响数字/结论：**
  若通过，可在论文中新增 held-out B+C 和 edge-level conformance，
  将当前 `repair-corpus 60/60` 从 regression evidence 升为独立支持；
  若失败，必须继续保留 repair-corpus 限定，并检查失败 edge 是否影响
  RQ1--RQ4 数字。

### P2（decisive baseline）：重新注册并完成 bounded Raw reader 全矩阵

**对应缺口：e。**

- **假设：** stable artifact/session representation 在同源问题上提供
  Raw on-demand reconstruction 不能以相近 accuracy/cost 替代的能力。
- **输入数据：**
  复用现存 224 MiB frozen corpus、同一 72 files、同一问题文本和
  corrected v4 expected answers；Raw 看不到 expected answers、normalized
  rows、ProcGrep atoms 或 trajectory index。
- **脚本与 harness 修复：**
  从 `rq7_measurement.py` 分支一个新实验计划。保留 Bubblewrap read-only
  mount、tool/byte/output/time caps 和 network command deny-list；删除或
  改写对 command string 中绝对路径字面量的误判。文件系统越界由实际
  mount 可见性控制，并加入“证据中出现绝对路径不应中止”和“真实 outside
  read 必须失败”两个 preflight controls。
- **执行：**
  固定一个当前可用模型、版本、reasoning、prompt、预算和 no-retry
  policy；先跑最小真实 preflight，再跑 6 projects × 3 repetitions。
- **成本：**
  18 模型调用；串行最坏 4.5 小时；最多 1,152 retrieval calls、18 MiB
  returned tool bytes，另加模型费用。
- **预计产出：**
  360 Raw rows、18 Raw cost rows、每 family correct/wrong/abstain、
  B+C project-block uncertainty，以及在 accuracy parity 条件下的
  wall/token/cost 对比。
- **影响数字/结论：**
  Raw 从 N/A 变成实测；若 matched/wins，削弱或取消 representation
  necessity/superiority；若显著落后且协议公平，才支持增量 capability
  claim。

### P3（decisive for RQ4）：前瞻扩充 eligible continuity boundaries

**对应缺口：c 中仍 stopped 的 RQ4。**

- **假设：** 在足够的独立、非重叠 native-root components 下，
  re-grounding prefix 和 prior artifact/module continuity 可形成至少四
  项目的 cross-case estimator，而不是只剩 coverage 描述。
- **输入数据：**
  冻结当前 RQ4 derivation 后，前瞻收集 AgentSight、ActPlane、BPF
  tutorial、eunomia.dev 的新 native roots。按 final coverage，四项目对
  mutation-observed/overlap/resolved-prefix 达到 20 的最小完全合格
  boundary 缺口约为 5、6、1、13，即至少 25 个新增 qualifying
  boundaries；实际需采集更多 raw roots，因为并非每个 boundary 都有
  mutation 和 resolved overlap。
- **停止规则：**
  只看 coverage denominator，不看 effect direction；当四项目各 estimator
  `n>=20` 时停止，或到预注册上限（例如 8 周或 200 个新 roots）后保留
  stopped 结论。
- **脚本：**
  `agentvis research-rq1` 与 final `plot_rq4.py`，保持 component
  construction、overlap 和 first-mutation 定义不变；运行独立
  root/component reconciliation。
- **预计产出：**
  新 `rq4-components.csv`、`rq4-boundaries.csv`、
  `rq4-prefix-actions.csv`、per-project coverage/effect tables，以及
  project/root-block uncertainty。
- **影响数字/结论：**
  若 gate 通过，RQ4 可从 within-case/coverage 升为 cross-case
  continuity estimate；否则 stopped 保留，并给出实际扩充后的上界。

### P4（supporting/decisive for RQ5）：多项目 exact-context Skill repeatability

**对应缺口：f。**

- **假设：** named-Skill attributed action composition 的 within-Skill
  repeatability 在多个项目中是否稳定优于 matched different-Skill
  activity。
- **输入数据：**
  保留当前唯一合格项目，并新增至少三个作者无关、自然使用 named Skills
  的项目。每个项目需在同一 vendor/model/source-role stratum 内至少两个
  Skill，每个 Skill 至少覆盖三个独立 native roots；建议每项目至少六个
  roots，并冻结所有 pre-invocation matching fields。
- **脚本：**
  `agentvis research-rq1`、`agentvis/research/check_rq5_sources.py`、
  `agentvis/research/plot_rq5_skill_footprints.py`；保持 source-native
  `attributionSkill`、root blocking 和现有 JSD features，不发明
  per-invocation delegated boundaries。
- **预计产出：**
  每项目 same/different JSD、exact root-block permutation、四项目
  aggregated effect、leave-one-project-out、coverage and source-check
  manifests。
- **影响数字/结论：**
  当前 `one eligible project, p=0.750` 将被跨项目估计替代或补充；
  positive 结果只支持 repeatable composition，negative 结果支持更强的
  “no supported separation”边界；两者都不能自动变成 causal Skill
  effectiveness claim。

## 最终核销意见

当前 HEAD 的最大进展是：最终 projection 修复后的 RQ1--RQ4 主复算和
RQ1/RQ3 扩展复算已经真实完成，核心 headline 也大多进入论文。当前最大
即时风险不是“没有跑”，而是**论文仍引用旧图并保留局部旧数字**，导致
RQ2、RQ4 的已修口径在成稿中再次冲突。

在新增昂贵实验前，应先执行 P0。科学上最值得投入的是 P1
held-out + edge ledger，其次是完成 Raw baseline；RQ4 和 RQ5 的缺口需要
真实新增数据，不能靠同一 final export 的再次分析关闭。
