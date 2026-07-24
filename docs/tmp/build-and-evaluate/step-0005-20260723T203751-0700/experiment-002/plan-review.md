# Experiment 002 Preregistration Review

## Verdict

**BLOCK：研究问题值得执行，Codex native-root v3 的核心修复方向正确，
但当前 preregistration 和 runner 仍留下可直接泄漏答案、漏掉前序 freeze
排除、替换 baseline、以及静默重试 selection 的路径。修复这些合同前不得
freeze 新 corpus，也不得运行或查看任何新 held-out oracle/result。**

本次是只读审查。检查范围为 `experiment-002/plan.md`、公开 root fixture
和相关实现 diff；没有读取或运行 Experiment 002 的 held-out action
oracle、answers、baseline results 或 strict-v1 results。

## Scientific admission

Experiment 002 不是新增一个独立功能实验，而是修复 Experiment 001 暴露的
measurement-validity 失败。它对论文有直接决策价值：若严格的
source-conformance gate 失败，artifact-linked cross-session 实证结果不能
继续作为论文证据；若通过，论文也只能主张显式 strict boundary 内的
source conformance。正反结果会改变论文，因此该实验可以作为
**decisive measurement-validity experiment** 执行，而不是把 fixture、
freeze 或 checker pass 当作贡献。

`current-v0` 是唯一 main baseline，代表未修复 projection。ProcGrep 是
action-only control，source oracle/standalone checker 是 correctness
controls，Git snapshot 是 final-state control；plan 应显式使用这些角色，
避免把 controls 描述为多个 competing baselines。

## Findings

### P1. Experiment 001 的作废方向正确，但排除集合没有被完整冻结

**部分通过，仍阻塞。**

Plan 正确声明 Experiment 001 整体作废，不将其 score、edge count 或
question result 解释成正面/负面科学结果，并要求新实验排除 Step 0004 和
Experiment 001 暴露的 sources/roots。这是必要处置。

但当前 plan 没有枚举 authoritative exclusion manifests 及其 hashes。
工作区中存在 Step 0004 freeze，以及 Experiment 001 的 current 和多个
invalidated freeze。`freeze --exclude-freeze` 是可选、默认空列表；调用者
漏传任意一个 manifest 时 runner 仍会生成“zero overlap”报告，但这个
zero 只是针对不完整的 exclusion union。

必须修改为：

1. 在 plan 中列出 Step 0004 与 Experiment 001 **所有曾打开 source 的**
   authoritative freeze paths/hashes；若多个 Experiment 001 freeze 的
   source union 相同，也要用 hash/inventory 证明后再允许只引用一个。
2. 冻结时要求 exclusion manifest 集合与 preregistered 列表精确相等；
   少一个、多一个或 hash 不符都立即失败。
3. 单独保存 Experiment 001 invalidation note，说明作废原因、哪些 artifacts
   仅保留为 audit trail，以及任何旧 result 都不进入 paper aggregate。

### P2. Codex root v3 contract 已正确实现

**PASS。**

三条实现都采用：

`session_id → parent_thread_id → thread_id → id`

- selector/primary oracle：`codex_native_root_id`；
- standalone checker：`codex_root_identity`；
- production：`codex_native_root_id` JSON pointers。

公开 `native-root-identity.json` 覆盖 legacy root、新 root、legacy
subagent、新 subagent 和 `thread_id` fallback，并由 shared fixture gate
同时运行 production 和两个 Python implementations。该合同与 plan 一致。

建议但不阻塞：再增加一个包含多个 `session_meta` record 的 stream-level
fixture，明确“最后一个 session_meta”还是“第一个 authoritative
session_meta”；当前三条实现都会随 record 更新，但 plan 没写该边界。

### P3. Step 0004 + Experiment 001 split 的 archive 验证可静默退化

**BLOCK。**

Plan 明确说旧 manifests 必须从 archived source 重新读取并用 v3 resolver
计算 corrected root，不能信任 stored v2 root。实现却在 archived source
不存在时静默退回：

`source["native_session_id"]`

而且没有验证 archived source 的 bytes/SHA-256 与旧 manifest 一致。该
fallback 正是本实验试图避免的 root-semantics 风险，会让 root overlap 被
低估。

必须修改为：

- 每个 exclusion source 的 archive 必须存在；
- size/hash 必须与旧 manifest 一致；
- 必须成功由 v3 resolver 导出 root；
- 任一 archive 缺失、损坏或无法解析都终止 freeze，不能回退到 stored
  v2 identity。

Root-disjoint 已经使 root/call overlap 在逻辑上冗余，但保留 root/call
audit 是合理的。若声称“native root/call tuple 完整 disjoint”，旧 call
集合应从全部 native Tool calls 导出，而不是只从 `oracle_edges` 中有严格
artifact edge 的 calls 导出；否则应把该字段准确改名为
`strict-edge-root-call overlap`。

### P4. “36 roots”尚未成为可执行 completion contract

**BLOCK。**

Plan 同时写“exactly six ... per project”和“when possible”，两者冲突。
Runner 的 CLI 默认仍为旧值：

- default seed：`20260722`，不是 preregistered
  `20260723-heldout-v3-001`；
- default sessions：12，不是 6；
- `select_sources` 只检查 `len(result) < 6`，并不检查
  `len(result) == sessions`；
- freeze 完成时没有断言六个项目各 6、总计 36 个 distinct corrected
  roots。

此外 selection 使用“当前时间减 600 秒”的 eligibility cutoff，但 plan
没有记录这条规则；同一 seed 在不同时间运行可能看到不同候选池。

必须修改为：

1. 删除 “when possible”：任一项目不足 6 个 eligible distinct roots
   就终止整个预注册实验，不换项目、不减样本、不重试 seed。
2. 将 v3 seed 和 sessions=6 设为 required/frozen values，runner 拒绝其他
   值。
3. freeze completion 显式断言 6 projects、每项目 6 sources/roots、总计
   36 distinct `(vendor, corrected_root)`。
4. 预注册 600 秒 eligibility age（或固定 absolute discovery cutoff），并
   把 cutoff 写入 freeze manifest。
5. 对 `heldout-projects.json` 记录 hash；说明
   `semantic-flamegraph` 的替换是在 action oracle/answers 未生成前、仅按
   eligibility 完成。若筛过多个替代项目，应列出候选和确定性替换规则，
   避免 workload cherry-picking 疑问。

### P5. 未知 production root 已改为错误，不再被过滤

**PASS。**

`production_projection` 对任何不在 `expected_sessions` 的
`native_session_id` 立即返回
`unexpected production native root`，而不是 `continue`。缺失全部
expected overlap 也会在 trace mapping 阶段失败；部分正确、部分未知的
trace 会进入 projection 并被上述 gate 拒绝。该修复关闭了 Experiment
001 的 silent-discard 路径。

### P6. Freeze 会把 held-out answers 写进 release

**BLOCK，属于直接 data-leakage path。**

`sanitize_question()` 当前把 `row["answer"]` 写为 `expected_answer`，
`freeze()` 随即将它输出到 `release/questions.csv`。这意味着在 baseline
和 repaired projection code freeze 之前，普通 release artifact 已包含
全部 canonical answers。仅靠“不要打开文件”的约定不足以称为 blind
held-out validation。

必须修改为：

- pre-result public/release questions 只能包含 ID、family/template、
  opaque path/witness hashes 和 spec hash，不能包含 `expected_answer`；
- canonical answers 只保存在独立 private oracle artifact，直到
  strict-v1 output 和 baseline candidate output 都完成、hash seal 后才能
  交给独立 scorer；
- freeze summary、checker output、stdout 和 audit manifest 在解封前也
  不得包含 per-question answers或 aggregate score。

### P7. `current-v0` baseline sealing 仍可泄漏 gold，也未绑定真实 v0 binary

**BLOCK。**

当前 `baseline` path 直接读取 private question answers，并在
`baseline-results.json` 写出 `expected`、`correct`、`wrong`。因此 baseline
一生成就暴露 v0 score/gold-derived labels，可在 strict-v1 code freeze
之前指导后续修复。

此外 `RQ7_AGENTVIS_BINARY` 可以指向任意 binary；baseline cost 只记录路径
字符串，不记录 binary hash。`full --baseline` 也接受任意 JSON path，
没有验证它属于同一 v3 corpus/spec、commit `7e5464eca` 或 sealed hash。

必须修改为：

1. v0 在 detached clean worktree 用 documented locked command 构建；
   seal Git tree, Cargo.lock, binary SHA-256 和 build command。
2. baseline 阶段只输出 blind candidate answers/projection rows与 cost，
   不输出 expected/correct/wrong/score。
3. 在 strict-v1 code seal 后，独立 scorer 同时读取 sealed v0 candidates、
   sealed v1 candidates 和 private gold。
4. `full` 必须验证 baseline candidate file hash、question spec hash、
   corpus/freeze hash、row ID set 和 v0 binary seal；不能接受任意
   `--baseline` 文件。

### P8. Preflight/full gates 的主体合理，但 plan 与实现需精确定义

**部分通过。**

已实现的强门槛是合理的：

- session order、attempted edges、confirmed effects、call statuses exact
  precision/recall；
- unknown production roots fail；
- one smallest-source project preflight，B+C 10/10；
- full B+C 60/60；
- full 要求 v1 correct 严格高于 v0，且 wrong/abstain 不更差。

需要修订：

1. “all gates overall and for every represented vendor” 应只作用于
   conformance gates 1--4；B+C 60/60 和 v1-over-v0 是全 corpus gate，
   当前没有定义 per-vendor B+C question sets。
2. 明确 represented vendor 是“有 selected session 的 vendor”还是“有
   strict edge 的 vendor”。当前 by-vendor loop 只遍历 oracle-edge vendors；
   一个有 session 但零 strict edge 的 vendor 只受 overall session-order
   检查。
3. preflight project 的 bytes tie-breaker 要固定（建议 project name），
   避免列表顺序成为隐藏选择规则。
4. Plan 必须给出实际 freeze/baseline/code-seal/preflight/full commands、
   raw output paths、完成文件和 hash record；当前只有步骤说明，没有可复现
   command。

### P9. “one selection attempt”目前可以被静默重跑

**BLOCK，属于 retry loophole。**

`freeze()` 开始时会递归删除已有 private/release 目录。失败或不满意后再次
运行会覆盖前一次 attempt；同一 seed 也会因为 moving 600-second cutoff、
新 session files 或 workspace state 变化而产生不同 corpus。CLI 还允许任意
seed/session/exclusion 参数，现有 `recover-freeze` / `rederive-freeze` 路径
也未在 v3 plan 中禁止。

必须修改为：

- freeze 不得删除已有 attempt；目标存在就失败；
- 在输出目录之外或父 experiment 目录写一次性 attempt record，至少包含
  command、start time、seed、projects hash、exclusion hashes、discovery
  cutoff 和 terminal status；失败 attempt 也永久保留；
- preregistered attempt 已开始后，不得更换 seed、projects、source count、
  exclusions 或 cutoff；
- `recover-freeze` / `rederive-freeze` 不得用于 v3 scientific run；若发生
  I/O-only recovery，必须保留原 source list/hash并作为 deviation 记录，
  不能重新选择或重算不同 questions；
- preflight 失败后若需 semantic change，按 plan 作废整个 split；不得在同一
  corpus 调参后再次 preflight。

## Required revision before approval

下一版 plan/runner 至少必须同时完成：

1. 固定并验证 Step 0004 + Experiment 001 exclusion manifest union；
2. exclusion archives 缺失/hash 不符时 hard fail；
3. 固定 6×6 roots、v3 seed、projects hash 和 discovery cutoff；
4. 移除 public `expected_answer` 以及 baseline 的
   expected/correct/wrong；
5. seal 并验证真实 current-v0 binary/candidate output；
6. 使 freeze append-only、保留失败 attempt、关闭 silent retry；
7. 写出唯一 authoritative commands、paths、hashes 和 gates；
8. 运行公开 root/action/lifecycle fixtures 与 unit tests，再做一次
   preregistration follow-up review。

在这些修改完成并复核前，**不得开始 Experiment 002 freeze**。

---

## 第二轮 follow-up review（2026-07-23）

### Verdict

**仍为 BLOCK。** 第一轮 P1--P9 中关于 exclusion union、archive
完整性、6×6 selection contract、public gold、blind v0 candidates、
native-root failure、freeze append-only 和 authoritative commands 的主体
修改已经完成；公开 fixtures/tests 也全部通过。剩余阻塞不在 projection
语义，而在 held-out 执行顺序仍未由 runner 约束：当前可以绕过或重跑
preflight/full，也没有把 preregistered v0 binary 和 repaired-code seal
变成机器可验证的前置条件。

本轮仍是只读审查。没有运行或查看 Experiment 002 action oracle、answers、
baseline result、preflight result 或 full result。

### 已关闭的第一轮问题

1. **P1/P3 PASS：** runner 要求恰好两个 preregistered exclusion manifest
   hashes；每个 archived source 必须存在并匹配 size/SHA-256，再由 v3
   resolver 重建 root；call exclusion 从全部 native Tool calls 导出。
   `experiment-001/INVALIDATED.md` 单独记录旧实验不得进入论文。
2. **P4 PASS：** seed、6 projects × 6 roots、16 MiB、60 秒 stability、
   absolute cutoff 和 projects hash 均已固定；不足 6 roots 或全局不唯一
   会 hard fail。preflight 使用 `(total source bytes, project name)`。
3. **P5/P6 PASS：** unexpected production root 是 failure；公开
   `questions.csv` 不再含 `expected_answer`。
4. **P7 部分 PASS：** v0 baseline 现在只写 blind candidates，并 seal
   corpus/spec/candidate ID set、revision、Cargo.lock 和 binary hashes；
   `full` 在评分时验证这些自洽关系。
5. **P8 PASS：** plan 已把 per-vendor 范围限定为四个 conformance gates，
   vendor 集合由 selected sessions 定义；B+C 和 v1-over-v0 是 corpus-level
   gates；commands/artifacts 已列出。
6. **P9 的 freeze 部分 PASS：** `freeze-attempt.json` 在 discovery 前写入，
   private/release 已存在即失败；v3 recover/rederive 被禁用。

### R1. Preregistered v0 binary hash 只被“记录”，没有被“要求”

**BLOCK。**

Plan 预注册了 Cargo.lock SHA-256
`c117357c…3143` 和 binary SHA-256 `7f83e0f7…760f`，但 runner 只有
`V0_REVISION` 常量。`baseline` 接受 detached worktree 中当前存在的任意
`target/release/agentvis`，然后把其 hash 写入 `baseline-seal.json`；
`full` 只检查文件仍与这个自生成 seal 一致。换言之，一个不同 binary
也能生成一份内部自洽的 seal，plan 中预注册的两个 hashes 从未参与判断。

必须在产生任何 candidate 前：

- 将 preregistered Cargo.lock 与 binary hashes 固定为 runner constants，
  并分别 hard-check；
- baseline seal 继续记录它们，`full` 再与同一 constants 和文件同时核对；
- 最好先完成全部 baseline seal 验证，再运行 repaired deterministic
  projection；当前 `full()` 是先生成并评分 repaired result，之后才验证
  baseline。

### R2. Preflight/full 仍可覆盖重跑，full 也可绕过 preflight

**BLOCK，属于 held-out retry/tuning loophole。**

Plan 规定 preflight 只运行一次，失败后的 semantic change 必须使 split
作废，且只有 preflight pass 才能运行 full。实现没有执行这些约束：

- `preflight()` 不拒绝已存在的 release target，也没有在读取/评分 gold
  前写不可覆盖的 attempt ledger；
- `full()` 使用 `mkdir(..., exist_ok=True)`，release summary 和 private
  results 都可被覆盖；
- `build_agent_session_projection()` 会递归删除已有 destination；
- `deterministic_methods()` 无论调用者传入什么 output，都复用并删除
  `private/deterministic/projection`；
- `full()` 不要求 `preflight-result.json` 存在且为 pass，因此 authoritative
  full command 可以被单独直接运行。

因此，当前 runner 允许“preflight fail → 改代码 → 在同一 split 重跑”，
也允许反复 full。仅在 plan 中写“不得重试”不足以封闭该路径。

必须：

1. 在 preflight/full 开始、且在读取任何 gold-derived score 前，各写一个
   位于不可覆盖位置的 attempt record，记录 command、时间、freeze hash、
   baseline seal hash、repaired-code seal hash 和 terminal status；
2. preflight/full 的 private 与 release target 已存在时 hard fail，任何
   projection builder 都不得删除这些 scientific-run artifacts；
3. `full` 必须要求唯一 preflight attempt 已完成且 pass，并验证 freeze、
   baseline 和 repaired-code hashes 与 preflight 完全相同；
4. 若 preflight failed，full 必须永久拒绝此 split。

### R3. Repaired-code seal 仍是不可执行的文字约定

**BLOCK，与 R2 可一次修复。**

Plan 说 `freeze-record.md` 会记录 repaired source files、Cargo.lock、
fixtures 和 test-output hashes，且 independent code-freeze review 必须
通过；但没有生成/校验该 record 的 authoritative command，preflight/full
也完全不读取它。Plan 还声称“v0 和 repaired candidates 都 sealed 后才
打开 gold”，而当前 repaired method 在 `deterministic_methods()` 内直接
读取 question answer 并立即写 `expected/correct/wrong`，没有独立的
repaired-candidate seal。

不必为 deterministic repaired method 强行复制一套 blind-candidate
pipeline。更小且同样严谨的修复是：

- 把 plan 改为“v0 candidates blind-sealed；repaired **code and binary**
  sealed；之后才运行一次 scored preflight”；
- 提供一个确定性命令生成 machine-readable `freeze-record.json`，至少
  seal repaired Git revision/dirty diff、指定 source files、Cargo.lock、
  release binary、public fixture inputs 和 test outputs；
- preflight/full 都在任何 projection/score 前验证这个 record；full 再
  验证其与 preflight attempt 的 hash 相同。

### R4. 非科学性但必须修正的结果标识

`full()` 成功日志仍写 `48 roots`，而固定 contract 是 36 roots。summary
中的 `sources` 会按实际数据计算，因此这是显示错误，不单独构成科学
BLOCK；但必须在运行前改为 36 或从 freeze contract 动态读取，避免 audit
记录自相矛盾。

### Public validation

- shared root/action/lifecycle fixture gate：PASS（5 root、8 action、4
  lifecycle；production + two independent oracles）；
- `agent-session`：20/20 tests PASS；
- `agentvis`：40/40 tests PASS；
- `python3 -m py_compile`：PASS；
- `git diff --check`：PASS。

### 最小解锁条件

无需再改 projection 算法。只需同时完成：

1. runner hard-check 预注册的 v0 Cargo.lock/binary hashes；
2. 生成并机器验证 repaired-code/binary freeze record；
3. 让 preflight/full append-only，并在执行前写永久 attempt ledger；
4. 让 full 强制依赖同 hash、唯一且 pass 的 preflight；
5. 修正 48→36 roots 日志。

完成后可做最后一次只读 follow-up；在此之前，**不得开始 Experiment 002
freeze 或打开任何新 held-out answer/result。**

---

## 最终 follow-up review（2026-07-23）

### Verdict

**PASS。Experiment 002 的 preregistration、公开 implementation gates 和
held-out 执行协议已满足运行条件；未发现剩余科学性阻塞。**

本轮仍严格只读：只检查 plan、runner/code-seal diff 和公开
fixtures/tests；没有运行或查看 Experiment 002 action oracle、canonical
answers、baseline result、preflight result 或 full result。

### 第二轮阻塞关闭情况

1. **R1 PASS：v0 build identity 已成为硬约束。**
   `V0_CARGO_LOCK_SHA256` 和 `V0_BINARY_SHA256` 与 plan 一致；
   `baseline` 在 projection 前检查 revision、clean tracked tree、
   Cargo.lock 和 binary，`validate_baseline` 在 preflight/full 前再次核对
   preregistered constants、实际文件、freeze/spec、candidate hash 和完整
   ID set。`full` 也在运行 repaired projection 前完成这些验证。
2. **R2 PASS：preflight/full retry path 已关闭。**
   `main()` 在调用两者前写唯一、不可覆盖的 attempt ledger，永久绑定
   freeze、blind baseline、code seal、code review 和 result path；
   成功、失败与中断均不能在同一 split 重跑。preflight/full private 与
   release targets 是 append-only，projection builder 遇到已有 destination
   hard fail，不再删除旧输出。
3. **R2 PASS：full 不能绕过 preflight。**
   `full()` 要求唯一 preflight attempt 的 terminal status/decision 为
   `complete/pass`，并重新核对 freeze、baseline seal、code seal、review、
   preflight result path/hash/status。失败或中断 preflight 因此永久阻止
   full，符合 plan 的 invalidation rule。
4. **R3 PASS：repaired implementation 已机器封存。**
   `seal-code` 要求 committed clean tracked tree，记录 Git revision/tree、
   relevant source/fixture hashes、Cargo.lock、locked release binary 和
   public test-output hashes。preflight/full 在任何 projection/score 前
   检查现有 Git revision/tree、sealed files、binary、test records，并要求
   independent `code-review.json` 对 exact code-seal hash 给出 pass。
   Plan 也已准确改为“blind-sealed v0 candidates + sealed/reviewed repaired
   code/binary，然后才进行 scored preflight”，不再声称存在未实现的
   repaired-candidate blind phase。
5. **R4 PASS：** full 成功日志从 freeze summary 动态打印实际 source/root
   数，固定合同下为 36，不再硬编码 48。

### P1--P9 最终状态

第一轮所有问题均已关闭：两个 exclusion manifests 精确 hash-bound；
旧 archives 必须完整并以 v3 resolver 重算；6×6、seed、projects、cutoff、
size 和 stability 固定；unknown roots fail；public questions 与 blind
baseline 不泄漏 gold；per-vendor/corpus gates 定义一致；freeze、
preflight 和 full 均为单次 append-only scientific runs；Experiment 001
被明确 INVALIDATED 且不得进入任何 paper aggregate。

### Public validation

- shared root/action/lifecycle fixture gate：PASS（5 root、8 action、4
  lifecycle；production + two independent oracles）；
- `agent-session`：20/20 tests PASS；
- `agentvis`：40/40 tests PASS；
- 两个 Rust manifests 的 `cargo fmt --check`：PASS；
- `python3 -m py_compile`：PASS；
- `git diff --check`：PASS。

### 非阻塞审计建议

- `code-review.json` 的 plan schema 要求 `reviewer`；runner 的科学门槛已经
  由 exact seal hash + `status=pass` 形成，但可额外 hard-check reviewer
  非空以改善 provenance。
- `seal-code` 明确定义的是 clean **tracked** tree，并同时封存 relevant
  files、完整 Git tree 和实际 release binary；执行者仍应按 plan 先提交
  所有实现与 fixture 文件，避免无关 untracked 文件造成审计噪声。

Experiment 002 现在可以严格按 plan 的唯一命令序列开始 freeze。任何命令、
seed、corpus、seal 或执行顺序偏离都应作为 deviation 记录；一旦 preflight
失败或中断，不得在该 split 上修复或重试。
