# 不变量格子：v2 本地复核结果

日期：2026-07-27

本地输入：修复后的 v2 events、RQ2/RQ4 rows 与 v2 revival rows

公开输入：复用冻结的 RQ6 external-status summary

## 结论

路径局部性仍是唯一的 `invariant-candidate`。15 个度量的新分类为
1 个 `invariant-candidate`、8 个 `vendor-shaped`、6 个
`idiosyncratic`、0 个 `project-shaped`。与旧分类相比有且仅有一个
翻转：stable-identity access reuse 从 `vendor-shaped` 变为
`idiosyncratic`。

## 路径局部性

| 指标 | 旧值 | v2 新值 | 判定 |
|---|---:|---:|---|
| 合格格子 | 8 | 8 | 稳定 |
| CV | 0.088424 | 0.088426 | 稳定且远低于 0.30 |
| 方向一致性 | 1.00 | 1.00 | 8/8 同向 |
| 逐格 leave-one-out | 1.00 | 1.00 | 稳定 |
| RQ6 external status | `replicated_direction` | `replicated_direction`（复用） | 稳定 |
| 分类 | `invariant-candidate` | `invariant-candidate` | 稳定 |

v2 的合格格子均值为 0.881137；“same path + same-module-only −
cross-module” contrast 在所有合格格子中仍为正。因此 shell-boundary
修复不推翻路径局部性候选。

## 分类翻转

`artifact_reuse_access_share` 的跨格子幅度仍然很稳定，但配对子格的
shape robustness 不再达到旧契约：

| 判据 | 旧值 | v2 新值 |
|---|---:|---:|
| CV | 0.075073 | 0.075933 |
| Claude/Codex vendor direction consistency | 1.00 | 1.00 |
| Vendor SS share | 0.617572 | 0.547520 |
| Project SS share | 0.252081 | 0.306113 |
| Interaction SS share | 0.130347 | 0.146367 |
| Leave-one-project-out shape stability | 2/3 | 1/3 |
| 分类 | `vendor-shaped` | `idiosyncratic` |

vendor SS 仍略高于 0.50，三个配对项目中的 Codex−Claude 仍同号，
但 leave-one-project-out 稳定率从门槛上的 2/3 降到 1/3，所以必须
如实撤回 `vendor-shaped` 标签。这里的 `idiosyncratic` 只表示未通过
invariant/vendor/project 三类门槛，不表示可因果归因于个人偏好。

其余 14 个度量分类全部稳定；逐项旧值→新值见
`classification-delta.csv` 和 `classification-change.md`。

## RQ6 复用边界

本次只重算本地 6×3×15 = 270 个显式格子。projection 修复不触及
RQ6 的 320 条公开轨迹，因此未重新读取公开 raw rows；只复用旧
`external_replication_summary.csv` 中的分类 gate，其 SHA-256 为：

```text
9ef2e175504aebcac7fe6142f8c3ba5a4c8bf9592e8ad0fca06680ddb8cf335a
```

复用内容原样保存在 `rq6-reused-external-summary.csv`，输入角色与哈希
记录在 `input-manifest.csv`。旧分类和 RQ6 gate 的输入快照、以及本地
格子所需的冻结 estimator 代码也保存在本目录，因此提交不依赖未跟踪的
旧实验目录。本地 tool-behavior 和 session-dynamics 输入从 v2 events
重新派生；RQ2/RQ4 与 revival estimator 使用 v2 rows。

## 对账与判定

- 本地格子：270 行，15 个度量；
- corpus：181,303 Tool events、551 sessions；
- 分类：1 invariant / 8 vendor-shaped / 6 idiosyncratic；
- 分类变化：仅 `artifact_reuse_access_share`；
- 两次最终脚本重跑的 5 个 CSV、1 个 JSON 和 2 个 PNG 逐字节一致，
  详见 `consistency-check.md`。

```text
run status: valid
tested question: path locality remains invariant-candidate; one vendor-shaped label is contradicted
research value: supporting recomputation
paper impact: preserve the locality candidate; update stable-identity reuse to idiosyncratic
next paper decision: integrate only after synchronizing the 8/6 vendor/idiosyncratic counts and the reuse label
```
