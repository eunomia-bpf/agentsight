# User questions：旧值到 v2 新值

旧值来自 `user-questions-20260726`，新值来自本目录。百分比按论文显示
精度四舍五入。

## A. 创建后访问

| 指标 | 旧值 | v2 新值 | 变化 |
|---|---:|---:|---:|
| Created paper/docs | 1,066 | 1,093 | +27 |
| Paper/docs 无后续 action | 318（29.8%） | 332（30.4%） | +14；+0.6 pp |
| Paper/docs 后续 read | 665（62.4%） | 682（62.4%） | +17；显示比例不变 |
| Created code | 124 | 125 | +1 |
| Code 无后续 action | 14（11.3%） | 14（11.2%） | 0；−0.1 pp |
| Code 后续 read | 97（78.2%） | 97（77.6%） | 0；−0.6 pp |

## B. Source-test 顺序

完全稳定：28 个合格配对、13 个 basename pairs、15 个同事件
fallbacks；test-first/code-first/tied 仍为 `0/7/21`
（`0.0%/25.0%/75.0%`）。

## C. 类型分配

| View / mode | 旧值 | v2 新值 | 变化 |
|---|---:|---:|---:|
| Confirmed reads 总数 | 43,322 | 43,611 | +289 |
| Confirmed reads docs/code | 18,828 / 18,727（43.5% / 43.2%） | 18,985 / 18,764（43.5% / 43.0%） | +157 / +37；0.0 / −0.2 pp |
| Confirmed writes 总数 | 13,906 | 13,809 | −97 |
| Confirmed writes docs/code | 9,701 / 2,261（69.8% / 16.3%） | 9,691 / 2,239（70.2% / 16.2%） | −10 / −22；+0.4 / −0.1 pp |
| `ok+observed` reads 总数 | 43,363 | 43,657 | +294 |
| `ok+observed` reads docs/code | 18,849 / 18,739（43.5% / 43.2%） | 19,006 / 18,776（43.5% / 43.0%） | +157 / +37；0.0 / −0.2 pp |
| `ok+observed` writes 总数 | 24,902 | 24,808 | −94 |
| `ok+observed` writes docs/code | 13,653 / 7,982（54.8% / 32.1%） | 13,645 / 7,960（55.0% / 32.1%） | −8 / −22；+0.2 / 0.0 pp |

近乎持平的 read 结论和 document-heavy write 结论均不翻转。

## D. Test/code churn

| 指标 | 旧值 | v2 新值 | 变化 |
|---|---:|---:|---:|
| Test identities / episodes | 33 / 116 | 33 / 116 | 不变 |
| Test repeat / validation | 71.6% / 61.2% | 71.6% / 61.2% | 不变 |
| Code identities / episodes | 316 / 2,257 | 289 / 2,235 | −27 / −22 |
| Code repeat / validation | 86.0% / 48.7% | 87.1% / 48.1% | +1.1 / −0.6 pp |
| Test-bearing blocks | 31 | 31 | 不变 |
| Repeat-test blocks / repeat+code-zero | 16 / 0 | 16 / 0 | 不变 |
| Test/code episodes in paired blocks | 116 / 493 | 116 / 493 | 不变 |

旧 collapse 会在一个 ActPlane compound rename 上终止。v2 契约修复后，
该跨路径 mutation 仍作为一个 identity-event episode，按 action ordinal
排序并以终点 path 分类。它是 paper/docs，不进入 B 或 D 的 test/code
配对；完整重算确认 B 和 paired-D 的稳定不是由跳过失败行得到的。
