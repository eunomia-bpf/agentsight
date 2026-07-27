# 不变量 v2：两次重跑一致性

## 结果

**PASS。** 使用最终 `analysis.py` 做两次完整独立执行；两次都从 v2
events 重新派生 tool-behavior 与 session-dynamics，再重算本地格子。
5 个 CSV、`run-summary.json` 和 2 个 PNG 全部逐字节一致。

Run 1 是本目录；Run 2 位于
`/tmp/agentsight-invariance-v2-selfcontained-rerun.IA46XY`。命令为：

```bash
python docs/tmp/build-and-evaluate/invariance-v2-20260727/analysis.py
python docs/tmp/build-and-evaluate/invariance-v2-20260727/analysis.py \
  --output-dir /tmp/agentsight-invariance-v2-selfcontained-rerun.IA46XY
```

对 5 个生成 CSV、`run-summary.json` 和 2 个 PNG 按相同相对文件名
执行 `sha256sum ... | sha256sum`，两次均为：

```text
33b7a66abcc49f3f12a55af6dc144279d21868ee431f6b4fbca37ec5b32b0ca4
```

两次均得到 270 个本地格子行、15 个度量、1/8/6 的
invariant/vendor-shaped/idiosyncratic 分类，以及唯一的
`artifact_reuse_access_share` label flip。路径局部性两次均为
CV=0.08842567576616599、方向一致性 1.0、逐格 LOO 1.0。

运行中的 pandas/bottleneck 版本提示和 constant-input Spearman 提示
均为 warning；两次退出码为 0，且没有造成输出差异。
