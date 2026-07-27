# Independent result review

## Verdict

**PASS；0 blocking issue。**

审阅为只读独立复算，覆盖自包含 estimator/baseline 快照、v2 输入、
本地格子 CSV、分类门槛、RQ6 复用边界和第二次输出。

## 核对结果

- 本地数据确由 v2 events、RQ2/RQ4 rows 和 revival rows 生成；
  270 行等于 6 projects × 3 vendors × 15 metrics。
- RQ6 没有重读 public raw，只使用自包含且哈希固定的 external summary；
  baseline 和复用输出逐字节一致，SHA-256 为
  `9ef2e175504aebcac7fe6142f8c3ba5a4c8bf9592e8ad0fca06680ddb8cf335a`。
- Path locality：8 个合格格子，mean=0.8811366495，
  CV=0.08842567577，8/8 contrast 为正，direction consistency=1.0，
  leave-one-cell-out=1.0，external=`replicated_direction`；保留
  `invariant-candidate` 正确。
- 分类计数为 1 invariant / 8 vendor-shaped / 6 idiosyncratic。
- 唯一 label flip 为 `artifact_reuse_access_share`：
  vendor SS `0.617572 → 0.547520`，vendor direction 保持 1.0，但
  leave-one-project-out shape stability `2/3 → 1/3`，低于 2/3 门槛，
  所以 `vendor-shaped → idiosyncratic` 正确。
- 其余 14 个 label 稳定。第二次输出的显式 5 个生成 CSV、JSON 和 2 个
  PNG 与本目录逐字节一致。

## Decision

结果可进入最终集成，但必须同步 artifact reuse 的分类翻转和新的
`1/8/6` 分类计数。未发现对 `docs/paper/` 或
`docs/evaluation.md` 的改动。
