# User questions：v2 完整重算结果

日期：2026-07-27

输入：`rq1-rq4-recompute-v2-20260727/rq1-raw`

## 结论

四项分析均已在修复后的 5,676 个 artifact identities、13,809 个
confirmed mutation rows 和 13,766 个 artifact-event mutation episodes
上完整重算。A/C/D 的精确值发生移动；B 的 source-test 顺序和 D 的配对
test-churn 结论保持不变。两次独立执行的 13 个 CSV 和
`run-summary.json` 逐字节一致。

## 配对契约修复

旧脚本要求同一 `(project, worktree, artifact identity, Tool event)` 的
所有 mutation rows 只能有一个 path。v2 中存在一个合法的 compound
rename：

```text
ActPlane / ActPlane:a00001076 / a7ef88e1ee014ecd
source action ordinals: 4 -> 7
docs/eval_scripts/prompts/judge_trajectory_system.md
  -> docs/tmp/rq1/judge_trajectory_steering_uptake_loose_system_20260606.md
```

修复后的契约仍将其计为一个 artifact-event episode，但允许多个 path：
按源事件的 `action_ordinal` 排序，以末次 mutation 的 path 决定 episode
的 artifact type、module anchor 和 validation outcome。输出同时保留
`paths`、`path_count`、`source_action_ordinals`、
`cross_path_compound` 和 `cross_type_compound`，因此该选择可审计。
本次只有 1 个 cross-path episode，且没有 cross-type episode。

## A. 创建后是否再访问

资格仍为 `birth_state=confirmed_create`。`NR` 是没有后续 confirmed
in-scope action 的比例，`RR` 是之后至少被 confirmed read 一次的比例。

| 类型 | 创建数 | 无后续 action（NR） | 后续 read（RR） |
|---|---:|---:|---:|
| Paper/docs | 1,093 | 332（30.4%） | 682（62.4%） |
| Code | 125 | 14（11.2%） | 97（77.6%） |
| Test | 14 | 2（14.3%） | 7（50.0%） |
| Other | 155 | 31（20.0%） | 105（67.7%） |

因此，对“新建文档后来是否会再读”的可识别答案仍是：全部新建
paper/docs 中 62.4% 后来被读，30.4% 没有后续 confirmed action。
投影仍不能识别哪些文档是用户明确要求创建的，因此不能把该比例解释为
“文档要求”的因果效果。

## B. Test-first 还是 code-first

| 合格配对 | Basename 配对 | 同 Tool-event module fallback | Test first | Code first | 同事件并列 |
|---:|---:|---:|---:|---:|---:|
| 28 | 13 | 15 | 0（0.0%） | 7（25.0%） | 21（75.0%） |

28 个配对仍全部来自 AgentSight。13 个严格 basename 配对中 7 个
code-first、6 个同事件并列；15 个 fallback 按定义只能是同事件并列。
其余五个项目没有合格配对，因此这仍是单案例描述，不能推广为六项目或
一般 agent 的开发策略。

## C. Read/write 的 artifact-type 分配

| Status view | Mode | 总 action | Paper/docs | Code |
|---|---|---:|---:|---:|
| `ok` | Read | 43,611 | 18,985（43.5%） | 18,764（43.0%） |
| `ok` | Write | 13,809 | 9,691（70.2%） | 2,239（16.2%） |
| `ok+observed` | Read | 43,657 | 19,006（43.5%） | 18,776（43.0%） |
| `ok+observed` | Write | 24,808 | 13,645（55.0%） | 7,960（32.1%） |

答案仍是：confirmed reads 在 paper/docs 与 code 之间接近持平，而
confirmed writes 明显偏向 paper/docs。加入 `observed` attempts 后，
write 差距缩小但方向不变。ActPlane 和 eunomia.dev 的 code reads
仍多于 document reads；六个案例在两个 status view 下都是 document
writes 多于 code writes。这里计数的是规范化 file actions，不是时间、
努力、重要性或进展。

## D. Test churn 与 code churn

`R` 是一个 identity 首次 mutation episode 之后的 episode 比例；`V`
是下一次该 identity mutation 前出现 recognized successful validation
的时间关联比例。

| 类型 | Mutated identities / episodes | R | V |
|---|---:|---:|---:|
| Test | 33 / 116 | 71.6% | 61.2% |
| Code | 289 / 2,235 | 87.1% | 48.1% |

任务匹配的 paired view 保持完全稳定：31 个 test-bearing
stream-prompt-module blocks 中有 16 个 repeat-test blocks，0/16 在
code episodes 为零时反复修改同一 test identity；只有 1/16 的 test
episodes 多于 code episodes，计数为 2 对 1。5 个 code-zero blocks
均没有 repeated test identity。配对块总计仍是 116 个 test episodes
和 493 个 code episodes。

因此，v2 仍没有观察到“反复改 test、source 完全不动”的指定模式。
全局 class totals 不能独立证明相对停滞；validation 也只是时间关联，
不证明测试覆盖、质量或正确性。

## 对账与判定

- 6 个项目、181,303 个 Tool events；
- 1,387 个 confirmed-created artifacts；
- 13,809 个 mutation rows → 13,766 个 artifact-event episodes；
- 1 个合法 cross-path compound episode，0 个 cross-type episode；
- 28 个 source-test 配对，31 个 test-bearing paired blocks；
- 两次重跑一致，详见 `consistency-check.md`；
- 旧值到新值的逐项对照见 `delta.md`。

```text
run status: valid
research value: supporting recomputation
paper impact: synchronize supplemental user-question numbers; no qualitative answer flips
next paper decision: use the v2 values and the repaired compound-mutation contract in final integration
```
