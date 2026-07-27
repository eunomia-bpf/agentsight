# Independent result review

## Verdict

**PASS；0 blocking issue。**

审阅为只读核对，覆盖 v2 输入血缘、源事件、脚本、全部 CSV、报告和第二次
重跑输出。

## 核对结果

- 9 个 provenance 输入的 bytes/SHA-256 均与 v2 文件一致。
- 唯一 cross-path compound mutation 是 ActPlane identity
  `ActPlane:a00001076` 在事件 `a7ef88e1ee014ecd` 中 action ordinal
  `4 → 7` 的 chained rename。按 identity-event 合并、按 ordinal 排序并
  使用 terminal path/type/module/validation 的契约与源事件最终状态一致。
- A：paper/docs `1,093 / 332 NR / 682 RR`，code
  `125 / 14 NR / 97 RR`；百分比及旧→新 delta 正确。
- B：28 个配对 = 13 basename + 15 fallback，test/code/tied =
  `0/7/21`，且全部来自 AgentSight。
- C：`ok` read/write totals 为 `43,611/13,809`，
  `ok+observed` 为 `43,657/24,808`；paper/docs 与 code 的计数、比例和
  delta 均与 CSV 一致。
- D：test 为 `33 identities / 116 episodes / 71.6% R / 61.2% V`；
  code 为 `289 / 2,235 / 87.1% / 48.1%`。31 个 paired blocks、16 个
  repeat-test blocks、0 个 repeat+code-zero blocks 和 116/493
  test/code episodes 均正确。
- 第二次输出的 13 个 CSV 和 JSON 与本目录逐字节一致。

## Decision

四项数值和结论可进入最终集成；需使用 v2 精确值和修复后的 compound
mutation 契约。未发现对 `docs/paper/` 或 `docs/evaluation.md` 的改动。
