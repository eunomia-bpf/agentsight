# RQ2 六案例跨案例 validation response 复审

## 结论

final-HEAD 将 recognized-success 项目覆盖从 3/6 提高到 6/6，因而解除
了上次的四项目 cross-case stop；但是六案例并没有呈现一致的
success/failure response 模式。

最稳定的共同描述只到 recognized-success cadence：在可形成完整
inter-success interval 的 5/6 项目中，interval 都有大量零 mutation
值，同时带有稀少但很长的 mutation burst。按项目汇总，零 mutation
比例为 47.6%--84.4%，五项目中的四个项目中位数为 0；按七条可形成
完整 interval 的 worktree lane，范围为 29.3%--86.1%。这支持“许多相邻
成功验证之间没有 confirmed mutation、但少数 interval 很长”的描述。
没有 count-model baseline，因此这里不使用统计含义更强的
`zero-inflated` 分布名称。

更具体的 event-distance response 则异质。success 后，在“下一 mutation
和下一 recognized validation 均观察到且不在同一事件”的可比事件中，
mutation 先发生的项目比例为 14.5%、24.8%、33.3%、52.4% 和 100%，
另一个项目只有一次 success、无法形成该比较。fail 后，相应比例为
0%、4.3%、7.2% 和 100%；另外两项目没有 recognized fail。前后相邻
validation interval 的 mutation rows 也没有统一增加或减少方向。因此，
本次 cross-case answer 是：**存在共同的高 zero mass cadence，但跨案例没有
一致的 outcome-conditioned response 模式。**

## 数据、口径与对账

输入只取自
`docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw/` 的
final-HEAD 权威复算。脚本固定并校验三个输入 SHA-256；具体 hash 在
`input-manifest.csv`，派生文件 hash 在 `output-manifest.csv`。

复算命令：

```bash
python3 docs/tmp/build-and-evaluate/rq2-crosscase-20260726/scripts/analyze_rq2_crosscase.py \
  --input-dir docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq2/raw \
  --output-dir docs/tmp/build-and-evaluate/rq2-crosscase-20260726
```

脚本核对了 180,180 条 worktree-lane trajectory rows、10 条 lane、
176,288 个 home-worktree-attributed actions 和
7,060 个 recognized validation events。六项目 recognized success 为
3,288、2,576、22、52、1、9，与 final-HEAD coverage CSV 完全一致。
完整 success-to-success interval 实际覆盖 5/6；recognized fail 覆盖
4/6，其中 eunomia.dev 和 agentskill-observability-paper 各只有 3 次
fail。`status=observed` 保留为 outcome unknown，不并入 success 或 fail。

本文使用三个互补的描述量：

1. **Cadence：** 每千 attributed actions 的 recognized attempt 数，以及
   同 outcome validation 之间严格位于两者之间的 lane-event 数。
2. **Mutation accumulation：** 相邻 recognized validation 之间的
   confirmed mutation rows，以及自前一 success 到当前 validation、当前
   validation 到下一 success 的 rows。为与任务用语对应，文中有时简称
   backlog，但这只是账本式 accumulation；success 处的重置是定义，
   不是该 success 覆盖、清除或证明了先前 mutation。
3. **Event-distance response：** 当前 validation 后到下一 mutation 和
   下一 validation 的严格中间 lane-event 数，以及两者哪个先出现。同一
   Tool event 同时含 mutation 和 validation 时单列为 co-observed，不
   发明 event 内顺序；观测端点未出现的后续事件保持 right-censored。

所有分位数采用 Hyndman--Fan type 7。结果按项目和 worktree 描述，不把
7,060 个事件当成 7,060 个独立项目，也不构造 progress score。
当前数据中 61 个 success events 共 co-observe 62 条 mutation rows
（agentsight 7/7、ActPlane 47/48、academic-writing-skills 7/7，
events/rows）；它们均从 success 前后的 accumulation 中排除并单列。
另有 9 个 lane-terminal success response 被 right-censor。每千 action
比率的分母是 home-worktree-attributed actions；30 个只有 action-target
worktree 的非 home events 进入相应 lane 的 event distance，但不进入该
rate 分母，而且它们都不是 recognized validation。

## 每项目 cadence

表中 `S/F/O` 是 `ok/fail/observed`；`S/F gap` 是同 outcome 之间严格
中间事件数的中位数；interval 分布只使用完整的 worktree-local
success-to-success interval。

| 项目 | attempts/1k actions | S/F/O | S/F gap | complete intervals | zero mutation | mutation rows median/p90/max |
|---|---:|---:|---:|---:|---:|---:|
| agentsight | 41.1 | 3288/373/202 | 5/41 | 3285 | 74.7% | 0/4/291 |
| ActPlane | 46.1 | 2576/277/159 | 3/35.5 | 2574 | 84.4% | 0/1/817 |
| bpf-developer-tutorial | 13.2 | 22/0/0 | 24/--- | 21 | 47.6% | 2/43/69 |
| eunomia.dev | 11.2 | 52/3/95 | 103/0 | 51 | 56.9% | 0/21/361 |
| agentskill-observability-paper | 4.0 | 1/3/0 | ---/76 | 0 | --- | --- |
| academic-writing-skills | 10.2 | 9/0/0 | 1/--- | 8 | 62.5% | 0/49/140 |

agentsight 的项目汇总会掩盖 lane 差异：其三条完整 lane 的零 mutation
比例为 29.3%、86.1% 和 66.7%，前两条 lane 的中位数分别为 2 和 0。
ActPlane 的第二条有 success 的 lane 只有一次 success，不能形成完整
interval。完整 lane 数字见 `lane-summary.csv`。

逐项目解释如下：

- **agentsight：** validation cadence 高，success 明显比 fail 密集。
  项目内 lane 异质性很大；一条 lane 通常在 success 间发生 mutation，
  另一条 lane 的 success interval 多数为零 mutation。
- **ActPlane：** cadence 与 agentsight 同为最高组，success interval 的
  零值比例更高，但仍出现最大 817 rows 的长尾 interval。
- **bpf-developer-tutorial：** 只有 success，cadence 较低；完整 interval
  的典型 accumulation 更高（中位数 2），但只有 21 个 interval。
- **eunomia.dev：** 150 次 attempt 中 95 次是 outcome unknown；success
  gap 较长，且只有 3 次 fail，不能把 unknown 当 fail 扩充分母。
- **agentskill-observability-paper：** 只有 4 次 attempt（1 success、
  3 fail），无法形成 success-to-success interval。
- **academic-writing-skills：** 9 次 attempt 全部 success；success gap
  中位数为 1，但 8 个完整 interval 中仍有最大 140 rows 的长尾。

## Validation 前后的 mutation accumulation

`pre -> post` 是当前 validation 与前/后相邻 recognized validation 之间
的 mutation-row 中位数。括号中的 `↑/= /↓` 是同时存在前后 interval 的
validation events 上，post 大于、等于、小于 pre 的事件数。它描述相邻
区间的负载变化，不表示 validation 使 backlog 消失。

| 项目 | success: pre -> post (`↑/= /↓`) | fail: pre -> post (`↑/= /↓`) |
|---|---:|---:|
| agentsight | 0 -> 0 (536/2222/524) | 0 -> 0 (12/343/18) |
| ActPlane | 0 -> 0 (254/2050/270) | 0 -> 0 (16/237/24) |
| bpf-developer-tutorial | 2 -> 2 (6/8/6) | --- |
| eunomia.dev | 0 -> 0 (10/24/16) | 0 -> 0 (0/3/0) |
| agentskill-observability-paper | 25 -> censored | 11 -> 16 (2/0/0) |
| academic-writing-skills | 0 -> 0 (2/3/2) | --- |

高支持项目中，大多数 validation event 两侧都是零 mutation，非零变化在
上升和下降间大致平衡或略偏下降；没有共同的 post-validation 增长或
下降方向。唯一全为上升的是 agentskill-observability-paper 的两次可配对
fail，但它来自总共 3 次 fail，且所有 fail 位于唯一 success 之前：
fail 后到下一 success 还增加的 mutation rows 中位数为 41。它是一个
稀疏案例模式，不能覆盖其他项目。

## Event-distance response

`next mutation / next validation` 是当前 outcome 后的中位严格中间事件
数。`mutation first` 的分母只包含两种后续事件都观察到、且不在同一
Tool event 的情况；因此它不把 right censor 或 co-observation 当作顺序。

| 项目 | success: next mutation / validation | success mutation first | fail: next mutation / validation | fail mutation first |
|---|---:|---:|---:|---:|
| agentsight | 74 / 4 | 24.8% (814/3285) | 318 / 1 | 4.3% (16/373) |
| ActPlane | 418.5 / 2 | 14.5% (374/2571) | 907 / 1 | 7.2% (20/277) |
| bpf-developer-tutorial | 23.5 / 24 | 52.4% (11/21) | --- | --- |
| eunomia.dev | 211.5 / 40 | 33.3% (17/51) | 424 / 0 | 0.0% (0/3) |
| agentskill-observability-paper | 1 / censored | incomparable | 1 / 69 | 100% (3/3) |
| academic-writing-skills | 0 / 1 | 100% (3/3) | --- | --- |

academic-writing-skills 另有 5 次 success，其下一 mutation 与下一
validation co-observed 于同一 Tool event；这些行没有被强排为 mutation
first。agentskill-observability-paper 的唯一 success 后没有下一
validation，故 success 顺序不可比。

在同时有 success 和 fail 的三个较高事件量案例（agentsight、ActPlane、
eunomia.dev）中，fail 后下一 validation 比下一 mutation更近，且 fail
的 mutation-first 比例低于同项目 success；这不支持“recognized fail
通常立即触发 mutation”这一统一描述。稀疏的
agentskill-observability-paper 恰好相反，3/3 fail 后 mutation 先出现。
因此，差异不是同一方向上的幅度变化，而是可观察顺序模式本身不同。

## 跨案例分层比较

可观察分层只显示同现关系，不能隔离 vendor 或项目类型效应：

- 两个 `systems/research` 项目均为 Codex-dominant 的混合 vendor 案例，
  attempt cadence 最高（41.1 和 46.1/1k actions），success 约占 85%，
  fail 后多数先再次 validation 而非 mutation。两者相似，但项目类型、
  vendor mix、项目规模和 adapter 使用同时共变，不能判为其中任何一个
  因素的效应。
- eunomia.dev 也为 Codex-dominant，却只有 11.2 attempts/1k actions，
  且 63.3% attempts 为 outcome unknown。这直接表明
  `Codex-dominant` 本身不足以预测 systems 两案例的 cadence/outcome
  composition。
- 两个 pure-Claude 案例也不一致：
  agentskill-observability-paper 是 fail-heavy 的稀疏序列，academic-writing-skills
  则是 success-only，且常在下一 validation 前或同一事件观察到 mutation。
  因而 pure-Claude 也没有对应单一 response 模式。
- bpf-developer-tutorial 是 Claude-dominant 的混合案例，但 success-only、
  mutation-first 与 validation-first 近似平衡；它与 pure-Claude 两案例
  均不同。
- 在两个 systems 项目内，Codex action strata 的 recognized-attempt rate
  均高于 Claude（agentsight 42.0 vs 35.2；ActPlane 52.7 vs 27.9 per
  1k vendor actions），但 bpf-developer-tutorial 反向（Claude 20.0 vs
  Codex 1.7）。这些是项目内 vendor exposure 的原始比率，不是匹配后的
  vendor 比较。

只有 `systems/research` 类型有两个案例；其他项目类型各只有一个案例。
vendor 又嵌套于项目、任务和 adapter outcome coverage 内。因此本数据
可以报告“systems 两案例相似、其他类型各异”的同现，不能形成 vendor
或项目类型的总体解释。

## 对 RQ2 论文段落的建议

1. 保留并强化已有的窄结论：修复后 6/6 有 recognized success；在 5/6
   可形成完整 interval 的项目中，success cadence 有高 zero mass 并带
   长尾 mutation burst。把论文当前的 `strongly zero-inflated` 改为精确
   zero fraction/long-tail 描述，因为本分析没有检验 count-model
   baseline。
2. 不要把它扩写成六案例一致的 validation response。增加一句明确结果：
   outcome-conditioned event response 跨案例不一致；较高事件量的三个
   success+fail 案例中 fail 后更常先再次 validation，但一个 3-fail
   稀疏案例相反。
3. 在 RQ2 分母中同时报告 `success 6/6`、`complete inter-success
   interval 5/6` 和 `fail 4/6`。6/6 success coverage 解除旧 gate，
   不等于每个 outcome 的六项目覆盖。
4. vendor/project-type 只作为可观察共变与限制；不要写 vendor effect、
   项目类型效应或 population-level replication。

## 结果处置

```text
run status: valid
tested question: high zero mass in success cadence observed; a single six-case outcome-conditioned response pattern is not supported
research value: supporting
paper impact: additional RQ2 evidence plus an outcome-coverage and heterogeneity boundary
next paper decision: retain the cadence/long-tail claim, add the no-consistent-response result and exact 6/6, 5/6, 4/6 denominators
```
