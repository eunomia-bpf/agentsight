# Step 0005 Held-Out Preflight 独立结果审查

## Verdict

**INVALID。**

这不是 `strict-v1` 的 held-out 负结果。当前 preflight 暴露的是冻结
oracle/selector 对 Codex native root 的协议错误；因此 tested hypothesis
仍为 **inconclusive**，不能把 `status=fail`、session recall、10/10 B+C
或 exact edge 数字写成方法的正面或负面科学结果。

```text
run status: invalid
tested hypothesis: inconclusive
research value: dependency-only protocol finding
paper impact: no new RQ evidence; retain the prior projection-conditioned boundary
next paper decision: discard this held-out split and re-freeze a genuinely root-disjoint corpus
```

## 决定性证据

### 1. 冻结 oracle 把 source stream ID 当成了 native root

导致 missing session 的 Codex 文件为：

`rollout-2026-07-18T15-27-52-019f7757-d53e-77f0-8ce0-bf3b22bc76b8.jsonl`

其 `session_meta.payload` 同时给出：

```text
id               = 019f7757-d53e-77f0-8ce0-bf3b22bc76b8
session_id       = 019f4fd3-9535-7c11-9773-2e3b79e57a83
parent_thread_id = 019f4fd3-9535-7c11-9773-2e3b79e57a83
thread_source    = subagent
```

这里的 `id` 是子线程/source stream 自身的 rollout ID；`session_id` 和
`parent_thread_id` 指向其共享的 native root。这个解释也与 plan 的书面
合同一致：semantic session 是 native root，parent/subagent stream 只是
provenance，不能另算一个 session。

但 primary oracle/selector 的 `native_metadata()` 和 independent checker
的 `native_identity()` 都采用 `payload.id` 优先于 `payload.session_id`。
因此所谓“两套独立 oracle 一致”只说明它们共享了同一个 root-resolution
假设，并未独立验证这个假设。

对这个具体文件，production `agent-session` 先取
`payload.session_id`，因而正确地输出
`codex:019f4fd3-9535-7c11-9773-2e3b79e57a83`。冻结 oracle 却期待
`codex:019f7757-d53e-77f0-8ce0-bf3b22bc76b8`。公开 conformance JSON
中的唯一 session miss 正是这个协议分歧，而不是 production 丢失一个
native root。Production 还有专门的
`codex_session_meta_uses_native_root_id_for_root_and_subagent` 测试，明确
断言 root 与带 `payload.session_id` 的 subagent 共享同一 root ID；这不是
偶然的输出格式差异。

### 2. 当前 edge/B+C 通过不能挽救该 preflight

公开结果显示：

- attempted edges：111/111；
- confirmed-effect edges：108/108；
- edge-call statuses：108/108；
- B+C：10/10；
- session order：7/8，Codex 为 3/4。

这些数值并不构成“edge 正确、只有 session ordering 失败”的可用负结果。
该 Codex stream 有 Tool actions，但没有进入 strict file-edge gate 的
artifact action，所以错误的 root identity 没有改变 111 个 edge 的
multiset，也没有被本项目的 10 个 B+C 问题击中。它只在 session-order
gate 中显现。换言之，当前通过项没有检验发生协议错误的那一部分。

此外，scorer 的 `production_projection()` 会对不在 oracle
`expected_sessions` 中的 production session 直接 `continue`。因此它把
真实父 root 丢弃，只报告一个 expected session missing，而没有把真实父
root 同时报告为 unexpected/extra。后续 conformance 必须保留并惩罚未知
production root，不能先按 oracle identity 过滤。

### 3. 当前 corpus 不满足 held-out root-disjoint 条件

按正确 native root
`019f4fd3-9535-7c11-9773-2e3b79e57a83` 复核，该 root 已出现在 Step 0004
development freeze。当前 freeze 所称的 zero native-root overlap 是用错误
的子线程 `payload.id` 计算出来的。因此这个源文件并非 plan 所要求的
development-root-disjoint held-out source。

同理，`48 files from 48 distinct native roots` 也没有被当前 freeze
证明：它实际证明的是 48 个由错误 resolver 生成的 ID。把全部文件按正确
root 重新分组后，数量仍有可能恰好是 48，但在重算之前不能作此声明；而
zero development-root overlap 已经由这个反例直接否定。

这意味着不能只修改 oracle、在相同 48 个文件上重跑并把结果继续称为
held-out。preflight 结果已经打开，而且正确分组后 split 本身违反了冻结
条件；该 corpus 必须作废。

### 4. Production 也需要补齐完整的 Codex root resolver

这一次 production 因为文件含有 `payload.session_id` 而得到正确 root。
但当前 parser 的 fallback 是
`payload.session_id -> payload.thread_id -> payload.id`，没有读取
`payload.parent_thread_id`。冻结记录中存在只带
`parent_thread_id` 的旧式 Codex subagent metadata；对这种记录，
production 仍可能把 child `id` 错当 root。

所以结论不是“production 已经全面正确，只改 oracle 即可”，而是必须先
冻结一个覆盖 Codex schema 版本的共同 root-resolution 合同，再由三条实现
各自实现并通过同一公开 fixture。

## 最小合法重新验证条件

1. **先冻结 native-root 规范。** 对 Codex 明确规定并测试：
   `payload.session_id` 优先，其次 `payload.parent_thread_id`，最后才是
   root record 自身的 `payload.id`。若还支持 `thread_id`，必须在书面规范
   中给出其语义和优先级。source-stream identity 继续由 source 自身
   ID/path stem 表示，不能与 semantic native root 复用。
2. **三方独立实现同一合同。** Selector/primary oracle、independent
   checker 和 `agent-session` 必须分别实现该 resolver。公开 fixture 至少
   覆盖：旧式 root、带 `session_id=id` 的新式 root、只有
   `parent_thread_id` 的旧式 subagent、同时带
   `session_id/parent_thread_id` 的新式 subagent。fixture 的 expected
   root 必须手工声明，不能由任一被测 resolver 生成。
3. **修复 scorer 的未知-root 过滤。** Production 中不属于 oracle
   expected roots 的 session 必须作为 `extra` 进入 session、call 和 edge
   conformance；不得静默跳过。root/stream join 也必须在过滤前检查。
4. **重新建立完整 split。** 用修正后的 resolver 对所有候选和 development
   source 重新分组。新的 held-out 必须与 Step 0004 以及本次已打开的
   Step 0005 corpus 在 file hash、semantic native root 和 native call 上
   全部不重叠；同一 root 的 parent/subagent streams 必须作为一个不可拆分
   group。
5. **使用全新 held-out，而非替换单个失败文件。** 在查看任何新问题或
   score 前，预先固定 project eligibility、每项目 root 数、cutoff、
   source cap、selection rule、全新 seed、question spec、oracle/checker
   hash、current-v0 revision 和全部 gates。新 seed 只运行一次，不能因
   root 数、问题分布或分数不理想而重试。
6. **重新 seal baseline 与 code。** 在新 corpus 上先密封
   `current-v0`；随后完成 public fixtures、parser/projection tests 和
   independent code-freeze review，再打开一个预先指定项目的真实
   preflight。preflight 只有在 session/root、ordered calls、attempted
   edges、effect edges、status 和 B+C 全部按合同完成时才允许进入六项目
   full run。

若新的 spec、selector、oracle 或 scorer 在 preflight 后再次发生语义修改，
受影响的 held-out split 必须再次作废，不能把修订后的同一数据继续当作
未见测试集。

## 论文处置

当前 Step 0005 只能作为 artifact engineering 记录：一次真实 preflight
发现并阻止了 native-session identity 合同错误。它没有独立科学贡献，也
不支持 `strict-v1` 成功或失败。

在新的合法 held-out run 完成前：

- 不报告 Step 0005 的 10/10 B+C、111/111 edge 或 7/8 session recall 作为
  paper result；
- 不把这次 fail 描述成 native records 无法支持 exact lineage；
- 不用它替换 Step 0004 的负面 implementation finding；
- RQ1--RQ4 继续保持 projection-conditioned，而不是被本次 preflight
  “修复”或进一步否定。
