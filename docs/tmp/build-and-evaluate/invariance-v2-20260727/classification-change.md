# 不变量分类变化对照

## 汇总

| 类别 | 旧数量 | v2 数量 | 变化 |
|---|---:|---:|---:|
| `invariant-candidate` | 1 | 1 | 0 |
| `vendor-shaped` | 9 | 8 | −1 |
| `project-shaped` | 0 | 0 | 0 |
| `idiosyncratic` | 5 | 6 | +1 |

唯一的 label flip 是：

| 度量 | 旧分类 | v2 分类 | 触发原因 |
|---|---|---|---|
| `artifact_reuse_access_share` | `vendor-shaped` | `idiosyncratic` | Leave-one-project-out shape stability 从 2/3 降至 1/3，低于 2/3 门槛 |

路径局部性保持 `invariant-candidate`：CV
`0.088424 → 0.088426`，方向一致性 `1.00 → 1.00`，逐格 LOO
`1.00 → 1.00`，RQ6 gate 仍为 `replicated_direction`。

其余 13 个非路径局部性度量也没有 label 变化。所有 15 个度量的 CV、
方向一致性、vendor SS 与旧/新分类在 `classification-delta.csv` 中。
