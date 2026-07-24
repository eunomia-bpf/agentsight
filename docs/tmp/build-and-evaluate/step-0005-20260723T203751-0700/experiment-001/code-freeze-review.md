# Strict-v1 解封前实现审计

## 结论

**BLOCK：当前不能解封 held-out evaluation。**

本次只读审计覆盖 `plan.md`、`freeze-record.md`、`agent-session/src/parser.rs`、`agentvis/src/repository.rs`、`agentvis/src/rq1.rs`，以及 `rq7_measurement.py`、`rq7_source_oracle_check.py` 的 v2 路径。没有运行 held-out 评测，没有读取 private oracle answers 或 baseline results，也没有修改实现代码。

当前 exact edge/status/effect gate 和 B+C 覆盖门槛本身可以执行；但 oracle、production 和 scorer 仍不是同一个可执行规范。更严重的是，scorer 从 oracle 注入 session 顺序，并复用 oracle 的 `ArtifactTracker` 重建 production lineage，因此现有满分不能证明 production 真正实现了 session ordering 和 artifact identity。

## 阻塞项

### B1. Oracle 与 production 的路径/动作语法不一致

同一个原始 Tool call 可能在三条路径中产生不同 edge，违反冻结规范要求的“同源、同语法、同排序”。

1. **结构化路径键不一致。** 两个 Python oracle 的 `PATH_KEYS` 接受 `absolute_path` 和 `target_file`，而 `agent-session/src/parser.rs::collect_path_fields` 只接受 `path`、`file_path`、`filepath`、`notebook_path`、`old_path`、`new_path`。production 会漏掉 oracle 认可的 edge。
2. **shell operand 语法不一致。** production 的 `plausible_path_token` 要求 `/` 或有限扩展名，因而会拒绝 `README`、`Makefile`、`LICENSE` 等无扩展名仓库文件；Python oracle 对冻结命令的非选项、非通配符、可归一化仓库内 operand 没有这一扩展名白名单。
3. **shell 状态机不一致。** production 额外处理 `cd`、wrapper、嵌套 `bash -c` 和嵌入的 `tools.exec_command` JSON；两个 oracle 没有相同实现。这不只是“更强解析”，而是会改变相对路径基准、edge 数量及顺序。
4. **patch move 语义不一致。** production 将 `*** Update File` + `*** Move to` 转为 `rename_from` + `rename`，并删除原来的 write；两个 oracle 会保留 Update/write，再追加 rename pair，形成不同 edge multiset。

上述差异都能在不打开 held-out 的情况下由静态实现确认。必须先形成唯一的 frozen action grammar，并让 source checker、primary oracle 和 production 对相同公开 fixture 逐 call 输出完全相同的有序 action list。

### B2. Scorer 没有独立验证 production 的 session order 与 lineage

`rq7_measurement.py::production_projection` 直接使用冻结 oracle `project["sessions"]` 建立 `session_order`，随后把这些 oracle session ordinals 写入 production edge。这样即使 production 的 native-root/session 排序错误，conformance 仍可能通过。

同一函数还把 production action 喂给 primary oracle 使用的 Python `ArtifactTracker`，由 scorer 重新计算 B/C。也就是说，B+C 不是读取 Rust `agentvis/src/rq1.rs` 的真实 lineage/query 结果，而是由与 oracle 相同的实现生成。该路径会掩盖 production 的 artifact identity、rename、delete/recreate 和跨 session continuity 缺陷。

此外，`edge_key` 不含 `session_ordinal`、`event_ordinal`、action ordinal 或 `artifact_id`。因此 exact attempted edge、status、confirmed-effect 三个 1.0 gate 即使通过，也不能证明 total order 或 artifact identity 正确。

解封前至少需要：

- 从 production 独立产生 session ordering，并与 oracle ordering 比较；
- 对有序 action 序列或包含 action ordinal 的键做 conformance，而不只是 edge multiset；
- 用真实 production lineage/RQ1 输出计算 B+C，或提供与 primary oracle 独立实现的 candidate query path；
- 显式检查 artifact identity、rename continuity、delete/recreate 和跨 session continuity。

### B3. Production 丢失 call 内动作顺序，rename 不能保证原子执行

`agent-session` 的 `ToolEvent.paths` 经 `BTreeMap` 组织，`agentvis/src/repository.rs` 又通过 `BTreeSet` 生成 action，因此同一 Tool call 中的语义顺序会被词典序重排。对 rename 来说，目标路径可能先于源路径执行。

`agentvis/src/rq1.rs` 顺序消费 actions，只对 `rename` 有特殊处理；`rename_from` 会先按普通 mutation 路径处理。若目标路径词典序早于源路径，tracker 可能先创建/迁移目标 identity，再为源路径制造额外 identity。当前 edge multiset gate 不含 action ordinal 或 artifact ID，因此这种错误仍可能取得 exact edge 1.0。

rename 必须成为带明确 source/target 顺序的原子动作，或者冻结 action ordinal 并让 oracle、production、scorer 都验证该顺序。

### B4. 无时间戳 Tool call 的处理不一致

`agentvis/src/repository.rs::append_session` 对 `tool.ts_ms == None` 直接 `continue`，production 因此完全丢掉这些动作；两个 oracle 会保留它们，并在全局排序时使用 session-first timestamp fallback。书面规范要求完整读取 native session 行及其动作，没有授权 production 丢弃无时间戳 call。

需要冻结一个统一策略：保留并使用相同 fallback，或由三条实现共同排除；不能只有 production 排除。

### B5. Positive claim 的 v1-over-v0 条件没有进入完成 gate

`plan.md` 的 Positive clause 要求 strict-v1 相对 sealed current-v0 改善；但 `rq7_measurement.py::full` 的可见 pass 条件只有 exact conformance 和 B+C 覆盖，没有加载并比较 sealed v0。当前 `status: pass` 因而最多代表 v1 自洽门槛，不能代表 Positive claim 成立。

若 v0 比较有意留到 result review，则必须把它记录为独立、不可跳过的最终 decision gate，并禁止把 `full: pass` 表述为实验 claim 通过；更稳妥的做法是让 completion scorer 显式读取 sealed v0 projection 后给出 improvement decision。

## 已确认可执行或未发现问题的部分

- `exact_conformance` 确实对 attempted edges、confirmed-effect edges、edge call statuses 执行 overall 和 per-vendor 的严格 1.0 gate。
- preflight/full 确实把 exact conformance 与 B+C 的 10/10、60/60 覆盖要求组合起来。
- repository 保留 failed/observed actions；`agentvis/src/rq1.rs` 在 lifecycle/reuse/mutation 前过滤 `status != "ok"`，attempt 与 confirmed effect 的高层分离已经存在。
- `source_stream_id` 的 vendor/native-id/file-stem 哈希公式在 production 与 oracle 间一致。
- 对具有时间戳的 Tool call，production 的 `(ts, stream, tool ordinal, id)` 与 oracle 的全序设计基本一致；当前主要差异是无时间戳 call 以及 scorer 注入 oracle order。
- 静态搜索未发现 production 中嵌入 private answer、held-out hash 或项目级答案常量。审计过程中没有查看 private answers/baseline results。`freeze-record.md` 也记录了首次 oracle 身份 bug 在查看 held-out answer/score 之前作废并重建；没有发现答案泄漏证据。

## 解封条件

1. 用一个冻结、可测试的 action grammar 消除 B1 的全部 parser 差异。
2. production 独立输出并接受 session/order/lineage conformance，消除 B2 的 oracle 注入与共享 tracker 循环。
3. 原子化 rename 或冻结并验证 call 内 action order。
4. 统一无时间戳 call 策略。
5. 将 v1-over-v0 设为明确且不可跳过的 Positive decision gate。
6. 只在公开 development fixtures 上重新做 source-oracle、production-oracle 和 query-level preflight；上述五项全部通过后，再进行一次新的只读解封审计。

在这些条件满足前，不应运行或打开 held-out 评测结果。

---

## 第二次审查

### 结论

**BLOCK：B3--B5 的主要缺陷已经修复；B1 仍有可执行的
production/oracle grammar 分歧，B2 仍有三条实现共享的 stale-attempt
lineage bug，不能解封 held-out evaluation。**

本轮只读检查了当前 diff、最终 `plan.md`、`freeze-record.md`、公开
`development-action-fixtures.json` 和指定的 Rust/Python 实现。没有读取或
运行 private held-out answers、baseline results 或 strict-v1 results。

公开检查结果：

- `check-action-fixtures`：4/4 通过；
- `agent-session` library tests：18/18 通过；
- `agentvis` library tests：38/38 通过；
- 两个 Python 文件通过 `py_compile`；
- `git diff --check` 通过；
- Final Strict-v1 Code Seal 中五个实现文件的 SHA-256 均与当前文件一致。

### B1：**未解决，仍为阻塞项**

大部分第一次审查指出的语法差异已经对齐：`absolute_path` /
`target_file`、无扩展名文件、直接 shell command、wrapper/cd/nested-shell
排除、redirection 排除和 patch move pair 均已有相应实现和测试。但仍存在
以下静态可复现分歧：

1. **书面规范包含 `filepath`，两个 oracle 却不接受它。**
   `question_spec()` 明确列出 `filepath`；Rust
   `collect_path_fields` 也接受它，但 `rq7_measurement.py::PATH_KEYS` 和
   `rq7_source_oracle_check.py::PATH_KEYS` 均缺少 `filepath`。因此 oracle
   与书面规范/production 不是同一语法。
2. **同一 call 对同一路径的多个动作会被 production 覆盖，但两个
   oracle 会全部保留。** `agent-session/src/parser.rs::extract_tool_paths`
   用 `BTreeMap<String, (access, previous_path)>` 以 path 为唯一键；后续
   `rows.insert` 会覆盖同路径的先前动作。两个 Python oracle 则按
   `(path, access, previous_path)` 去重。公开反例中：
   `cat README; touch README`、`cp README README` 均被两个 oracle 解析为
   read + create，而 production 只能保留一个；`mv README README` 同理会
   丢失 rename pair 的一侧。书面规范当前说“one edge per distinct path”，
   但 frozen edge key 又包含 access；无论预期是保留一个还是两个，三条
   实现目前都没有采用同一规则。
3. **Tool-name admission 仍不同。** production 把 `replace` 当 write，
   把任何名称包含 `patch` / `exec` / `shell` 的工具纳入；两个 oracle
   使用明确的 exact-name 集合，且都不含 `replace`。当前书面 action
   mapping 也没有声明 `replace` 或 substring admission。
4. **公开 fixture 并未直接运行 production parser。**
   `check_action_fixtures` 只比较 primary Python oracle 和 independent
   Python checker；Rust 的相关单元测试是手写的相似案例，不是同一个
   data-driven fixture。现有 4 个 fixture 也没有覆盖 `filepath`、同路径
   多动作或 tool-name admission。

解封前需要明确同路径多动作的唯一规范，并让三条实现输出同一个**有序
action tuple list**；同时统一 `filepath` 和 Tool-name 集合。公开 fixture
runner 必须能检查 production，而不能只检查两个 oracle。

### B2：**scorer 循环验证已解决，但 lifecycle 语义仍阻塞**

- `production_projection` 直接读取 production 的
  `session_ordinal`、`action_ordinal` 和 `artifact_id`，不再注入 oracle
  session order，也不再用 Python `ArtifactTracker` 重建 production
  lineage。
- `projection_conformance` 独立比较 session order。
- `edge_key` 已包含 session/event/action order 和 artifact identity。
- 缺失 production artifact identity 会立即返回 join error。

因此第一次审查指出的 scorer 循环验证已消除。剩余 B1 若未修复，仍会使
完整 conformance 失败，但不再被 scorer 隐藏。

#### B2 补充边界审查：**仍有共享语义 bug，属于阻塞项**

按书面 lifecycle 语义检查以下公开合成序列：

1. `failed create(path)`；
2. `successful create(path)`；
3. `successful delete(path)`；
4. `later successful non-create access(path)`。

production `ArtifactIds::resolve` 的实际状态变化是：

- 第 1 步建立 `attempted[path] = path#0`；
- 第 2 步为 confirmed create 建立 `current[path] = path#1`，但没有清除
  `attempted[path] = path#0`；
- 第 3 步删除 `current[path] = path#1`，旧 attempted identity 仍残留；
- 第 4 步 successful non-create access 从 `attempted.remove(path)` 取回
  `path#0`，使早先 failed create 的 identity 在已完成一轮
  create/delete generation 后被错误复活。

两个 Python oracle 的 `ArtifactTracker` / `Identities` 具有同样的
confirmed-create 分支，因此这是 **production 与 oracle 共享的语义 bug**，
而不是 exact conformance 可以发现的 disagreement。它违反“failed/observed
mutation 不改变 artifact lifecycle”以及 confirmed delete 后 later
non-create access 应建立新的 left-censored generation 的规则。

修复后需要公开 lifecycle fixture 覆盖该四步序列，并由独立的预期
generation 断言验证：confirmed create 必须 supersede/清除同路径 attempted
identity；confirmed delete 后的 later non-create access 不能复活旧 failed
attempt。

对 failed/observed explicit rename 的补充判断：当前书面规范明确
“Explicit rename preserves identity only when its Tool result is `ok`”，因此
source/target 两条 failed/observed attempted edge **不要求**共享一个
persistent artifact identity；分别保留 attempt identity 且不迁移
`current` 状态，与现有文字一致，不单独构成 blocker。不过该语义应加入
公开 failed/observed rename fixture，明确断言 source/target identity 是否
相同，避免未来把“atomic action pair”误解为“unknown/failed lifecycle
transfer”。若作者希望 attempted rename pair 在查询层共享一个
operation-level identity，应新增独立 `operation_id`，不应借用会参与
lifecycle 的 `artifact_id`。

### B3：**主体已解决，受 B1 限制**

repository 已为 action 定义 canonical order，分配
`action_ordinal`，并在 production 中生成 artifact identity；rename
source 先于 destination，单元测试验证两侧共享 identity。scorer 也把
action order 和 identity 纳入 exact key。

但 `ToolEvent.paths` 在进入 repository 之前仍会按 path 覆盖同路径动作，
所以 canonical ordering 只能排序“幸存”的动作。该残余归入 B1，在解决
前不能认为 call-local action contract 完整。

### B4：**已解决**

最终书面规范已明确：没有 native timestamp 的 Tool call 位于 ordered
trajectory 之外，作为 coverage exclusion，而不是分配 synthetic time。
两个 oracle 都在建轨迹前过滤无时间戳 call；production
`append_session` 采用相同排除策略。Final Freeze 的 source facts 也更新
为 2,405 个 timestamped Tool calls。

### B5：**已解决**

`full` 现在强制读取 `--baseline`，为 current-v0 计算 B+C gate，并要求：

- strict-v1 B+C gate 通过；
- strict-v1 correct 严格高于 current-v0；
- wrong 与 abstain 均不劣于 current-v0。

三者与 exact conformance 共同决定最终 `status`，因此 v1-over-v0 已成为
不可跳过的 completion gate。

### 泄漏与剩余协议风险

本轮静态搜索没有发现 implementation 中嵌入项目答案、question answer
常量或 held-out hash；没有发现新的答案泄漏证据。

不过 freeze record 已记录两次 pre-result invalidation，且最终 question
spec/oracle/current-v0 是在第一轮 implementation/code review 之后重新
seal 的。由于 source/seed 未替换且所有结果仍未打开，这不是已证实的答案
泄漏；但它削弱“oracle/spec 在任何 production repair 之前完全冻结”的
表述。论文和 artifact 必须按实际顺序披露，不能把 Final Freeze 描述成
第一次实现前预注册。

### 第二次解封条件

1. 补齐两个 oracle 的 `filepath`，或从书面规范与 production 同时删除；
2. 统一同路径多动作的语义与去重键；
3. 统一 exact Tool-name admission，移除未声明的 substring/`replace`
   差异或将其正式写入三条实现；
4. 扩充公开 fixture，并让同一 fixture 直接核对 production、primary
   oracle、independent checker；
5. 修复 confirmed create 未清理同路径 attempted identity 的问题，并用
   failed-create → confirmed-create → confirmed-delete → later-access fixture
   断言 generation 不会复活；
6. 公开 fixture、18 个 `agent-session` tests、38 个 `agentvis` tests
   全部通过后，再做一次只读 hash/code-seal 复核。

完成这些条件前，不应运行 held-out preflight/full，也不应打开任何
baseline 或 strict-v1 score。

---

## 第三次审查

### 结论

**BLOCK：第二次审查列出的六个解封条件已经逐项满足，但完整 plan 中的
same-worktree rename identity 约束仍与 production repository lineage
冲突，不能解封 held-out evaluation。**

本轮只读复核当前 diff、plan/spec/freeze record、两个 shared fixtures
及指定 Rust/Python 文件。没有读取或运行 private held-out answers、
baseline results 或 strict-v1 results。

公开验证结果：

- shared fixture gate：8 action + 2 lifecycle，Rust production 和两个
  Python oracle 全部通过；
- `agent-session` library tests：19/19；
- `agentvis` library tests：39/39；
- Python `py_compile` 与 `git diff --check` 通过；
- question-spec SHA-256 为
  `018c7116f9781a998f53e1366424e104af5f00f70f7a0f75c45635a177f5fb2f`；
- 五个 code-seal hash 和两个 fixture hash 均与 Review-Ready Seal
  完全一致。

### 第二次解封条件逐项结果

1. **`filepath`：PASS。** 书面 spec、Rust `collect_path_fields`、primary
   oracle 和 independent checker 均包含 `filepath`；shared action fixture
   有显式案例。
2. **同路径多动作 tuple：PASS。** production 已从 path-keyed
   `BTreeMap` 改为 `Vec<ToolPath>`，按
   `(path, access, previous_path)` 去重并保留不同 access；两个 Python
   oracle 使用相同 tuple 语义。shared fixture 覆盖
   `cat README; touch README` 和 `cp README README`。
3. **exact Tool-name admission：PASS。** production 改为与两个 oracle
   相同的 exact-name 集合，删除 substring admission 和 `replace`；
   shared fixture 覆盖 `replace` 与 `patch_preview` 的排除。
4. **同一 shared fixture 直接覆盖 production + 两个 oracle：PASS。**
   `check-action-fixtures` 先用同一个 JSON 检查两个 Python 实现，再通过
   `RQ7_ACTION_FIXTURES` / `RQ7_LIFECYCLE_FIXTURES` 启动指定 Rust tests；
   本轮真实执行成功。
5. **stale attempted identity lifecycle：PASS。** 三个 tracker 均在
   confirmed effect 后清除 same-path attempted-only identity；共享四步
   fixture 得到 `artifact#0 → artifact#1 → artifact#1 → artifact#2`，
   failed generation 不再复活。
6. **failed/observed rename：PASS。** question spec 明确 failed/unknown
   source 与 destination 使用分离的 attempted identities，不迁移
   persistent identity；共享 fixture 断言 `old#0` 与 `new#0`。

### 新阻塞项 T1：跨 worktree rename 被 repository 错误保留 identity

`plan.md` 的 proposed method 明确规定：rename 只有在 **explicit 且
same-worktree** 时保留 identity。

但 `agentvis/src/repository.rs::ArtifactIds::resolve` 对任何 confirmed
rename 都会：

1. 从 `previous_worktree_id` 对应的 source key 取出 identity；
2. 将该 identity 插入 destination `worktree_id`；
3. 没有检查 `previous_worktree_id == worktree_id`。

因此 successful rename 从 worktree A 到 worktree B 时，repository
projection 会跨 worktree 迁移 artifact identity。与此同时，
`agentvis/src/rq1.rs::apply_action` 明确用
`previous_worktree_id == action.worktree_id` 过滤 source，跨 worktree 时会
创建 `unknown_rename_source` artifact。也就是说：

- scorer/B+C 使用的 serialized `action.artifact_id` 会把 A/B 连成同一
  artifact；
- 最终 RQ1--RQ4 使用的 tracker 会把它们视为不同 artifact；
- standalone per-worktree oracle 会排除 workspace 外 source，也不会做
  production 的跨 worktree identity transfer。

这是 plan、repository projection、scorer lineage 和 RQ1 lineage 之间的
真实语义分叉。现有 lifecycle fixture 的所有 step 都固定在 worktree
`w`，因此 2-case gate 无法发现它。

解封前应：

1. 在 repository `ArtifactIds` 中只对 same-worktree confirmed rename
   transfer identity；跨 worktree destination 建立独立/unknown
   generation，与 RQ1 规则一致；
2. 将 fixture schema 扩展为显式
   `worktree_id` / `previous_worktree_id`，加入 same-worktree 与
   cross-worktree rename 对照；
3. 用同一扩展 fixture 检查 production repository tracker、RQ1 行为和
   两个 oracle，或明确说明 per-worktree oracle 如何投影跨 worktree
   action；
4. 更新 code/fixture hashes 后再进行一次只读 seal 复核。

### 非阻塞清理风险

实验目录中的旧 `development-action-fixtures.json` 仍是早期 4-case
版本；Review-Ready Seal 实际绑定的是
`agent-session/tests/fixtures/strict-action-grammar.json` 的 8-case shared
fixture。当前 authoritative hash 没有歧义，但保留两个名字相近、内容不同
的 public fixture 容易导致后续误用。建议删除旧文件，或让它只引用/复制
authoritative shared fixture；这不单独改变本轮 BLOCK 判定。

在 T1 修复并重新 seal 前，不应运行 held-out preflight/full，也不应打开
baseline 或 strict-v1 score。

### 第三次审查：最终 candidate seal 复核

**PASS：Final Candidate Strict-v1 Code Seal 可以解封，允许按 plan 运行
held-out preflight/full。此结论仅表示 code/spec/oracle/scorer 的解封条件
满足，不预判 held-out 结果是否通过。**

T1 已修复并重新 seal：

- Rust repository tracker 只有在
  `previous_worktree_id == worktree_id` 时才对 confirmed rename 迁移
  identity；跨 worktree destination 取得独立 identity。
- 两个 Python tracker 都以 `(worktree, path)` 为状态键，并采用相同的
  same-worktree guard。
- shared lifecycle fixture 从 2 case 扩展到 4 case，新增
  same-worktree preserve 与 cross-worktree no-transfer 对照。
- RQ1 新增 cross-worktree regression，验证 source/destination 是不同
  artifact，destination birth 为 `unknown_rename_source`。
- 旧的 4-case `development-action-fixtures.json` 已删除；plan 明确两个
  shared fixture 是唯一 authoritative development fixtures。

复核命令与结果：

- shared gate：8 action + 4 lifecycle，production + 两个 independent
  Python oracles，PASS；
- `agent-session`：19/19 library tests，`cargo fmt --check` PASS；
- `agentvis`：40/40 library tests，`cargo fmt --check` PASS；
- 两个 Python 文件 `py_compile` PASS；
- `git diff --check` PASS。

Final Candidate Seal hashes经独立重算全部匹配：

- `agent-session/src/parser.rs`：
  `726fbde1cfb618f69e09b8221e339d202ddcb550da3909d9d4a25f7c8ac9a4f5`
- `agentvis/src/repository.rs`：
  `bf5e2ebff67cdba0128ce7fbf099fd93b20dd481d400bf7961364f58862459eb`
- `agentvis/src/rq1.rs`：
  `7b7dcfd8efcc147e83b9cb33b8c075867aa6b50f9306599ed3f7c600df7bca5c`
- experiment/scorer：
  `7ad2769ff0da00968ce5a68e52a618432021fc72fa213f846483938986d0916d`
- independent checker：
  `6936996a4bf80b47a458c24692df8a3eea39155b347eb9b2dfeaceaf01f02b73`
- shared action fixture：
  `685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7`
- shared lifecycle fixture：
  `08b614293d36966939d4b635e8bd879dd381e54af392e5647e22889fc85e71ba`
- question spec：
  `018c7116f9781a998f53e1366424e104af5f00f70f7a0f75c45635a177f5fb2f`

本次最终复核没有读取或运行 private held-out answers、baseline results
或 strict-v1 results。此前 B1--B5、六个第二次解封条件和 T1 均已在公开
fixtures/tests 或静态 contract 检查中关闭。因此 code-freeze 判定由
**BLOCK** 更新为 **PASS**。
