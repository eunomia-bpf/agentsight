# Independent result review

## Verdict

**PASS；无阻塞性修正。**

审阅为只读复算；未修改分析产物，未访问
`rq7-heldout-20260726/`。

## 独立复算

- 15 类别完全复现：1 `invariant-candidate`、9 `vendor-shaped`、
  5 `idiosyncratic`、0 `project-shaped`。
- 路径局部性：8 个合格格子、5 个项目、3 个 Claude/Codex 对；
  CV=0.088424；contrast 8/8 为正；逐格 LOO=1.00。RQ6 五分层 CI
  下界均大于 0（0.332–0.597）。
- 晚期重读：5 个格子、3 个项目、2 个完整 vendor 对；CV=0.231095，
  5/5 为正且 LOO=1.00；RQ6 五个 CI 也全为正。因未达到
  6 格子/4 项目的覆盖门槛，`undercovered` 正确。
- 9 个 `vendor-shaped` 均满足 vendor SS=0.543–0.938、
  vendor sign=1.00、LOO≥2/3；7 个 LOO=1.00，复用率和重复读取率
  为 2/3。全部标为 `limited` 且未作 vendor 因果解释。
- 34 个有效分布 fit 中，本地 20 个全部不可区分；公开 14 个中
  2 个偏 lognormal、12 个不可区分、0 个偏 power law。BH q 值、
  cluster-bootstrap CI 和六组
  `shape_stable_parameter_drifting=false` 一致。
- RQ6 为 320 条、5 分层、每层 64；manifest 中 320 个 RQ6 原始文件，
  351 个输入哈希均一致。
- 对账复现 181,303 次本地 Tool calls 和 11,271 次
  `action_gap_gt_100` 复活；manifest 无 RQ7 路径。

## 边界审计

报告正确区分 stable identity 与 exact path、IdeaTrail 与 Open-SWE
两个 corpus family、harness-shaped shell、相对分布比较与绝对
goodness-of-fit。

唯一可选措辞建议是把“证据反对普遍 power law”改成“证据不支持普遍
power-law claim”；主报告已采纳。

## Paper decision

只提升路径局部性为当前 general-claim candidate；晚期重读保留为
高优先级待复制候选，其余作为 vendor/harness 形状或外部效度边界。
