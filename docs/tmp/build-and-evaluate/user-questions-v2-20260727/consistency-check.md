# User questions v2：两次重跑一致性

## 结果

**PASS。** 使用最终 `analyze_user_questions.py` 对同一 v2 输入做两次
独立执行，13 个 CSV 和 `run-summary.json` 全部逐字节一致。

Run 1 是本目录中的输出；Run 2 位于
`/tmp/agentsight-user-questions-v2-rerun.y1Y6HW`。两次执行命令分别为：

```bash
python docs/tmp/build-and-evaluate/user-questions-v2-20260727/analyze_user_questions.py
python docs/tmp/build-and-evaluate/user-questions-v2-20260727/analyze_user_questions.py \
  --output /tmp/agentsight-user-questions-v2-rerun.y1Y6HW
```

对相同相对文件名执行 `sha256sum *.csv run-summary.json | sha256sum`，
两次均为：

```text
b006554cfff27161731e49bf72819df29d59aea13a2ef20cab147e631132bce8
```

两次均对账为 5,676 artifacts、1,387 confirmed-created artifacts、
13,809 mutation rows、13,766 mutation episodes、1 个 cross-path
compound episode、0 个 cross-type compound episodes、28 个 source-test
pairs 和 31 个 test-bearing blocks。
