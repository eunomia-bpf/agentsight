# 新 RQ 设计提案（2026-07-26）

## 结论先行

当前 AAAI 稿件只有 6 个内容页，不宜把下面八个候选都升格。最有价值且
已经具备完整证据链的是 **候选 A：真实长期 Agent 的工具调用 workload 与
系统优化边界**。建议让它取代当前 main 中证据较弱的 Skill fingerprint
RQ，保持 main 仍为六个 RQ：RQ1--RQ4 不变，新 RQ5 研究 workload，RQ6
继续承担跨本地/公开语料的共性与边界；现有 Skill/instruction 分析移入
supplement，仍作为有效的负结果保留。

第二优先级是人类参与画像和共性/不变量分析。它们应先完成当前正在进行的
source-native 分析和独立审查：前者进入 supplement，并在 main 的
corpus/threats 中用一句话限定 mixed-initiative 程度；后者强化现有 RQ6，
而不是再造一个与 RQ6 重复的新编号。AgentSight eBPF 三方联合、晚期重读
机制和开放式增量计算都需要新采集或受控运行，应留给下一篇，不能把设计
写成当前论文的实证结果。

## 设计依据与共同纪律

本提案以当前论文、`docs/evaluation.md` 和 20260726 分析为边界。现有
本地语料是六个作者相关案例、551 个 project-root membership（550 个全局
唯一 session ID）、181,303 个 project-event row；去重后的系统 profile
包含 180,764 个唯一 Tool call。两个最大项目贡献约 90.3% 的去重调用，
因此 pooled 比例是语料描述，不是六项目等权总体，更不是 Agent 总体发生
率。

已有 workload 证据足以支持正式 RQ：Shell 占 68.6%，artifact-identity
read 的同 prompt 重复率为 46.7%，其中 76.2% 没有观察到中间 mutation；
24.76% 的相邻边已经并发，另有 1.05% 是已在同 batch 的 disjoint read，
剩余顺序 local-read 候选只有 2.98%；actionable next-read prefetch
precision 为 21.75%；last-test predictor 命中 26.22%，而每次 edit 后
eager test 的 stale-version 情景比例为 80.36%；同 handle 的保守
event-driven 上界为 1,456 calls/roundtrips，即 0.81%。这些都是描述量或
条件上界，不是已实现 speedup。

survey 已排除以下宽泛 novelty：工具分布、序列、重试、并行、投机、缓存、
CPU/内存 profile 和 provenance graph 都有先例。可用的七个窄空白是：
真实长期语料上的精确重复与恢复、跨 session 持久 repo 行为、真实轨迹的
安全并行上界、可变 workspace 的状态感知缓存、开放工具图的增量计算、
真实 Agent 的 syscall/I/O signature，以及语义动作×持久状态×系统成本
三方联合。

所有候选共同遵守以下规则：

1. 不构造“自主性”“效率”“退化”“进展”或“优化价值”的加权总分。每个
   RQ 输出一组有明确分母的估计量。
2. `ok`、`fail`、`observed` 和 missing 分开；没有观察到 mutation 不等于
   文件没有变化，recognized validation 不等于覆盖或正确。
3. 项目是案例，native root/session 是重采样块；连续 action 不作为独立
   项目样本。跨 vendor 差异首先是接口、任务、项目和时间的共同差异。
4. 每个子估计量有自己的 coverage gate。未通过就报告 within-case、
   coverage-only 或 N/A，不补零，也不让一个子估计量的充分覆盖替其他
   子估计量放行。
5. 所有预测器只作 chronological held-out 估计；不能用 in-sample
   ceiling 冒充泛化。所有“可省”结果必须注明是 execution、bytes、
   runtime overlap 还是 fused-roundtrip 上界。
6. 独立对账程序不得导入主分析的解析/分类函数；它从 native source 或
   独立系统计数器重建关键分母、状态、时间与目标。抽样人工核验只检查
   parser correctness，不提供语义 gold。

## 候选 A：真实长期 Agent 的工具调用 workload 与系统优化边界

### 一句话 RQ 与科学意义

**RQ：在真实、跨原生会话且持久 workspace 的长期 Agent 工作中，工具负载
呈现怎样的组成、重复、依赖与等待结构，这些结构分别给出多大的预取、
并行、推测、缓存和事件化安全机会边界？**

科学上有趣之处不是“Agent 会调用很多 Shell”或“有人做过缓存”，而是用
同一批长期自然轨迹把精确调用、workspace effect、状态变化和优化安全条件
联合起来。TraceLab 已测真实工具分布/延迟，但不保留原始参数、status、
artifact effect 或跨 session repo 演化；PASTE、AsyncFC、TVCACHE、
Cortex 和 AWO 已实现对应机制，但没有在可变的真实长期 workspace 上测
安全适用比例和失效边界；AgentCgroup 是 benchmark 上的 CPU/内存与 test
retry。survey 的空白 1、3、4、5 以及部分 7 都没有一篇先例同时覆盖。

### 估计量与可观察定义

主分析单位是去重后的唯一 native Tool invocation；181,303 个
project-event row 作为保留项目 membership 的敏感性。输出以下向量，不
合成总分：

1. **负载组成。** 各 tool family、Shell 主类、project/vendor、控制面
   （wait/control、coordination、task）份额；调用数、原生 tool runtime、
   preceding gap 和 result bytes 分开报告。
2. **重复。** 对 artifact identity、exact path、canonicalized
   `(tool,target,args)` 和 exact result hash 分别报告重复率、action/time
   reuse distance、是否有中间 observed mutation，以及同 root/跨 root
   重现率。same target 不是 cache hit，same operation 不是 retry。
3. **依赖与并行。** 将相邻边互斥分为：已观测 overlap、已同 batch 的
   disjoint local read、剩余顺序 disjoint local-read candidate、强依赖
   evidence/proxy、unknown。逻辑 work/depth 只作乐观结构上界；新增余量
   只来自尚未 batch/overlap 的候选。
4. **Prefetch。** project-local chronological 80/20 下报告 exact-next-path
   precision、recall、issued、waste、unseen-context 和可隐藏 read runtime；
   range/limit/format 未命中时不得计作完整调用命中。
5. **Speculation。** mutation-to-validation cycle 中 last-command
   predictor 的命中率、positive overlap runtime，以及 eager-after-edit
   产生的 stale workspace version 数。透明 speculation 默认减少 0 个
   模型往返。
6. **Cache/delta。** exact-result observed reuse 是下界；exact invocation
   且无 observed mutation 是有版本 provider 的条件 eligibility；same-target
   snapshot 和写后 diff bytes 是更宽情景上界。三者必须分列。
7. **Event-driven control。** 只在 same tool、same handle、passive、
   consecutive no-progress 的 wait burst 中保留一次 await，报告可移除
   call/roundtrip 数；不把外部任务 runtime 算作收益。

当前数字可作为 sanity anchor，而不是预注册阈值：42,679 条边已并发，
1,801 条 disjoint read 已 batch，5,132 条是剩余顺序候选；actionable
prefetch 为 633/2,911；last-test 为 718/2,738；event-driven 上界为
1,456 calls。

### 数据来源与新增成本

现有 final-HEAD 语料、1,917 个可回链 native JSONL、tool-call behavior/
profile CSV 和 RQ1 artifact/mutation ledger，已经足够回答描述性 RQ 和
条件上界；不需要新模型调用，新增成本是一次冻结重算、独立 checker 和
结果审查。

现有数据不够回答 realized wall-time speedup、完整依赖 DAG、真实 cache
freshness 或外部写入。49.47% 相邻边仍为 unknown，workspace 没有统一
version ID，也缺模型 serving 时间。若要从“边界”升级为“系统效果”，需
前瞻记录 read/write set、side-effect class、workspace version、first
byte、cache/speculation outcome 和模型时间；那属于下一篇系统实验。

### 实验设计

- **分层。** project × vendor 为首层；operation/effect、root 长度、
  same-root/cross-root、decisive/observed status 为二层。pooled 结果必须
  同时给 project-equal 和 action-weighted 视图。
- **门禁。** 组成与重复的 cross-case 结论要求至少 4 个项目各有 100 个
  eligible calls；某个优化子估计量要求至少 4 个项目各有 30 个 eligible
  edges/cycles，否则只报 within-case。project-local prefetch 要求 train
  至少 200 个 transition、held-out 至少 30 个 next-read target；不满足
  的项目只进 coverage。
- **预注册。** 冻结 source-call 去重键、operation classifier、exact args
  hash、target canonicalization、batch/overlap 判定、strong/unknown 边、
  chronological split、workspace mutation/invalidation 规则和每种
  “可省”量的单位。不得在看结果后把 unknown 改判 independent。
- **结果判定。** 大边界和小边界都能改变论文结论：大而跨案例稳定，说明
  值得实现机制；小，说明真实长期 workload 已利用相关机会或机制适用面
  窄；unknown 主导则结论是测量不足。三种都不是失败。
- **独立对账。** 第二个 source-native parser 重建所有 source-call ID、
  start/end、batch 和 result hash；按 vendor×project 分层抽查至少 200
  个调用及所有 headline opportunity 分母，并从 RQ1 ledger 独立核对
  target mutation。checker 不导入主分析模块。

### 预期论文位置

**当前 AAAI main 的正式新 RQ。** 建议用它替换当前 Skill fingerprint
RQ 在 main 的位置，main 只放一句 RQ、一个紧凑估计量表或一段 headline
结果；完整定义、project/vendor 表、prefetch/speculation/cache/event
边界进入 supplement。角色是 headline characterization，但仍服务于
“持久 workspace 暴露 action count 看不到的结构”这一中心主张。

### 风险与最可能失败方式

最大风险是把条件上界写成速度收益。其他风险包括两个大项目支配 pooled
数、vendor 工具面决定 Shell/read 差异、batch ID 语义不一致、外部写入
使无 mutation 判定失真、partial read 使 exact-result hit 偏低，以及
unknown dependency 使并行上界不紧。最可能的科学结果不是“大量未利用
并行”，而是现有并发已经覆盖大部分显式 read burst、剩余安全余量有限。

## 候选 B：人类参与与可观察行为改向

### 一句话 RQ 与科学意义

**RQ：长期 Agent 会话中可观察的人类指令密度、无后续指令的行动跨度和
显式 follow-up/interruption 如何分布，而 follow-up 前后工具与 workspace
目标发生了怎样的可观察改向？**

这不是给 session 打“自主性分”。TraceLab 虽来自真实开发者，却删除了
用户消息；benchmark 轨迹由固定 harness 驱动；survey 中没有工作把
source-verified 人类 follow-up 与同一持久 repo 中随后的工具/路径变化
联合起来。它扩展空白 2 和 7，并直接回答当前作者相关自然语料是否其实是
mixed-initiative 的审稿质疑。

### 估计量与可观察定义

1. 每 root 的 substantive human message、follow-up、字符/word-like
   token、assistant conversational message、Agent action 数和
   actions-per-human-message 分布。
2. `1` 条 substantive message 的 startup-only、`>=2` 的 guided，以及
   `0/unreadable` coverage；最大/中位 human-silent action span 单列。
3. native abort/interruption、approval request、visible Agent-to-human
   question 的频率与来源覆盖。user-role synthetic notice、tool result、
   context summary 和 system/developer record 不算人类消息。
4. 每个 eligible follow-up 前最后一个和后第一个 Agent action 的
   tool-family 变化、path-set overlap、same-artifact/same-module/
   cross-module 关系；立即变化只允许连接同一 native root source file
   和 source stream 的相邻动作。另报告到第一个 confirmed mutation 和
   recognized validation 的 action distance。它们叫“可观察改向”，不叫
   纠错、目标改变或干预成功。
5. startup-only/guided 及 project×vendor 内 guidance-density 上/下三分位
   的 mutation、reuse、validation 共现。它不形成 human guidance 的
   causal effect。
6. human prompt 到最后 Agent activity、再到下一 human prompt 的 elapsed
   envelope；它不是人类思考、打字或 attention time。

### 数据来源与新增成本

`human-involvement-20260726/plan.md` 已冻结 source-native parser、551
root coverage row、startup/guided 分层、follow-up 改向和 RQ1 mutation
join；`plan-review.md` 已批准修订后的 vendor record、dedup、同流邻接、
inactive-gap 命名和 outcome denominator，分析脚本也已出现，但还没有
terminal report/result-review。只要三个 vendor adapter 能区分真实人类
消息与 synthetic record，现有私有 native logs 足够，成本是本地解析和
隐私审查。

若某 vendor 不能可靠恢复 message origin，则现有数据只够给
`user-role record` 上界，不能回答人类参与。下一轮应在 opt-in 真实会话
里由 harness 显式记录 `message_origin={human,system,harness}`；目标 4 个
项目、每项目至少 20 roots，采集成本约 1--2 周自然使用，无需为本 RQ
额外生成模型任务。

### 实验设计

- **分层。** project × vendor，另分 root length、startup-only/guided、
  explicit interruption 与普通 follow-up；相同项目 membership 保留，
  全局唯一 event 作敏感性。
- **门禁。** 全量运行必须为 551 roots 各生成 coverage row。cross-case
  guidance profile 至少要求 4 个项目各 20 个可读 roots；行为改向至少
  要求 4 个 project×vendor strata 各 30 个两侧都有 Agent action 的
  follow-up。未过门禁时只报 strata 内分布。
- **预注册。** 冻结 vendor record type 白名单/排除表、message
  deduplication、follow-up 边界、prompt/action join、path-set 比较、
  timezone 和 density thirds；guidance density 沿用已批准的“每 100 个
  projected Agent actions 的 follow-up 数”，并同时报告 actions、raw
  mutations 和 mutations/action，避免机械相关。不读取正文做
  correction/goal-change 语义分类。
- **独立对账。** 每 vendor 选一条真实 root 做只读 preflight；第二个
  checker 直接按 native record type 重算 message timestamps/counts，
  并将 distinct prompt index 仅作为 disagreement control。输出不保存
  message text。

### 预期论文位置

**当前 AAAI supplement 扩展，main 只进入 corpus/threats 一句话。**
如果结果显示跨多个足量 strata 都高度 guided，它是解释所有 RQ 的必要
confound，但仍不值得在 6 页 main 中挤出一个独立 RQ。若未来有
prospective message-origin 数据和 matched follow-up 设计，可成为独立
mixed-initiative 论文。

### 风险与最可能失败方式

最可能失败在 source semantics：user role 可能包含 synthetic
interruption，多个 source stream 可能重复同一 prompt，root 中并发
subagent 让“下一 action”不代表收到指令的 lane。其次是隐私和作者相关
偏差。即使 follow-up 后模块改变，也不能证明人类导致改向；用户可能只是
确认了 Agent 已计划的下一步。

## 候选 C：跨项目、vendor 与公开语料的行为不变量

### 一句话 RQ 与科学意义

**RQ：哪些预先定义的工具/路径行为关系在本地项目×vendor strata 和公开
coding/scientific-process strata 中方向一致，哪些只在特定语料成立或因
缺少持久 lineage 而不可观察？**

已有研究分别刻画真实 serving trace 或 benchmark 轨迹，但 survey 未找到
在相同 operational definition 下，同时跨自然持久项目、vendor 和两类
公开语料检验“关系复现 + magnitude heterogeneity + N/A 边界”的工作。
这主要对应空白 2 和 7。当前 RQ6 已发现 path locality 与 2--3-call module
return 在公开数据复现，但跨模块比例存在明显幅度差；这正适合从“外部
边界”升级为严格的 observed-invariance 问题，而不是宣称普遍定律。

### 估计量与可观察定义

正在运行的 plan 已冻结 18-cell（六项目×三 vendor）grid 和 15 个本地
estimand：artifact reuse、top-10% session concentration、path locality、
same-prompt repeat read、Shell share、Shell→Shell bigram、zero-decisive-
validation session、startup extended median、late reread delta、
dormant revival、decisive failure rate、bigram entropy、Shell burst
p90、module return 和 per-session top-path share。公开兼容 registry
另含 path locality、module return、repeated exact-path explore/read、
any exact-path reuse、Shell share 和 median top-target share；不兼容的
lineage/revival/cross-session 指标必须 N/A。

当前 analysis 的 `invariant-candidate` 是探索性 evidence class：至少 6
个 eligible local cells、CV<0.30、direction consistency≥0.80，且兼容
RQ6 metric 不反向；`externally replicated` 还要求五个 public strata
全部与至少 80% eligible local cells 同向。vendor-shaped、
project-shaped 和 idiosyncratic 是描述类，不是因果归因。正式论文必须
保留 “candidate/recurring” 措辞；更强的 observed invariant 应留给新的
held-out 自然项目，并要求预注册方向在所有足量确认 strata 中不反向。
幅度始终单独报告 min--max/IQR/CV，不把“未显著反向”当不变量。

### 数据来源与新增成本

现有六案例、四个 Open-SWE strata 和一个 IdeaTrail stratum足够检验
兼容关系；公开部分已有 320 个分层选择、31,249 Tool calls 和 22,113
transitions 的独立对账。`invariance-mining-20260726/` 现在已有冻结
`plan.md` 和 `analysis.py`，但还没有 report、派生表或 result-review，
因此本提案不预设任何 invariant-candidate。

现有公开数据不能回答 persistent lineage、cross-session re-grounding、
human involvement 或 exact Skill attribution。要检验这些“长期不变量”，
必须新增至少 3 个作者无关、可保留 native session 与 repo lineage 的
自然项目；这是中等采集成本，而不是再分析现有 public trace 能解决的。

### 实验设计

- **发现/确认分离。** 当前本地结果只能生成候选；已经看过本地和 RQ6
  public 数字的关系一律标为 retrospective recurrence。新的 confirmatory
  invariant 必须先冻结 registry/方向，再进入作者无关项目或未读 public
  strata。
- **分层与门禁。** 直接沿用 running plan 的 metric-specific denominator：
  calls/transitions 通常 100、repeat read 50、session/prefix 通常 10、
  Shell runs 50；不能用一个总 gate 替所有 metric。public stratum 固定
  64 个独立 task/topic units。external replication 必须五个已登记
  public strata全部有定义值，并保留 coding/scientific 两类 family。
- **预注册。** 冻结 module mapping、transition eligibility、return
  censoring、candidate registry、兼容性矩阵和 invariant 判定。不能在
  看到一个 stratum 反向后更换 module 粒度。
- **独立对账。** local 与 public 使用两个互不共享 parser 的 checker；
  每条 registry relation 输出 source count conservation、N/A 原因和
  stratum estimate。`invariance-mining` 若从同一数据自动筛选候选，其
  输出只能叫 discovery，不得自我确认。

### 预期论文位置

**强化当前 main RQ6，而不是增加一个新编号。** main 保留一段“什么同向、
什么幅度不同、什么 N/A”，supplement 放 registry、compatibility matrix
和全 strata 表。只有取得作者无关的自然持久语料后，才足以成为独立的
跨环境 invariant 论文。

### 风险与最可能失败方式

最大风险是 selection leakage：先挖规律再用同一数据称 invariant。其次是
module 定义和工具接口共同制造表面稳定，公开 harness 又不具备本地 lineage。
最可能结果是只有 path locality/short return 在方向上复现，而绝大多数
持久行为保持 N/A 或 heterogeneous；这仍是有效边界结果。

## 候选 D：AgentSight 的语义动作×workspace effect×OS 成本三方联合

### 一句话 RQ 与科学意义

**RQ：真实 Agent 的每类语义工具动作在 workspace 中产生什么可观察效果，
同时触发怎样的 syscall、文件/网络 I/O 和进程成本，这三层关系如何随
成功、失败、重试与后续跨 session 复用而变化？**

这是 survey 空白 6+7 的直接命题。AgentCgroup 测 benchmark 上 CPU/内存，
AgentSight 论文展示 eBPF observability 与案例，CPU-centric work 测组件
资源；没有先例在同一批真实长期会话上系统报告 exact semantic action、
persistent workspace effect 与 syscall/I/O/process cost 的三方 join。

### 估计量与可观察定义

每个成功 join 的 Tool interval 输出：

1. tool family/exact invocation/status 和 workspace effect set；
2. `openat/openat2/statx/read/pread/write/pwrite/execve/clone/connect/
   send/recv` 的计数向量，文件/网络 bytes、独立 path/endpoint、process
   fan-out、CPU time、RSS peak/delta 和 block-I/O bytes；
3. 按 operation/status 的 per-call 分布以及 session/project 总量；
4. logical result bytes 与 OS read bytes、confirmed mutation bytes 与
   OS write bytes的成对比率（分母为零时 N/A），不合成“成本分”；
5. failed call 到 exact-target recovery 的累计 syscall/I/O/process
   cost，以及 later-reused artifact 对应的首次生产成本。它们是时序关联，
   不是“有价值成本”。

同时报告三方 join coverage、ambiguous-overlap share、lost-event rate 和
无法解析 path 的比例。并发 Tool interval 不能按墙钟窗口重复归因：只有
PID/child lineage 唯一时做 per-call attribution，其余进入 shared/
ambiguous bucket。

### 数据来源与新增成本

当前 181k 语料没有 OS trace，不能回答本 RQ。现有
`sudo ./agentsight record -- claude` 会自动保存 SSL、process 和
system monitoring；但当前 `SystemRunner` 只输出 CPU/RSS/process
采样，`record` 路径并不提供逐 syscall 或逐 path I/O。`cmd_monitor`
虽有 `/proc` read/write bytes 和打开 target 的窗口采样，也不足以关闭
survey 空白 6。

因此需要一个最小 AgentSight eBPF 扩展：按 root PID/cgroup 和 PID
start-time 聚合上述 syscall，维护 fd→normalized path 的有界 map，只
保存计数、bytes、哈希/相对路径和时间，不采集文件内容。开发成本中等；
随后目标采集 4 个公开 repo、每 repo 至少 10 个独立 native roots 和
1,000 个成功 join calls，预计 40--80 个自然会话、2--4 周。

### 实验设计

- **两阶段。** 先用现有 `agentsight record -- <agent>` 在 2 repo×2
  vendor 的 6 个真实会话验证 native session、root PID、process tree、
  LLM TLS 和 SQLite 时间线 join；再启用 syscall/I/O 扩展做 full run。
- **分层。** project×vendor 为案例层，semantic operation、status、
  workspace-effect class、single/overlapping call 和 process-depth 为
  事件层；session/root 是重采样块，不把 syscall 当独立任务。
- **时间与归因。** 同一主机用 boot-time monotonic clock；native wall
  time 只作校验。Tool start/result、PID start time、parent tree、
  invocation hash 和 workspace version 共同 join。短命子进程必须在
  process event 中出现，否则该 call 的 OS cost 只报 session-level。
- **门禁。** pilot 要求 tool-interval join coverage ≥95%、eBPF lost
  event <1%、固定 tool-mix canary 的 tracing overhead 中位数 ≤3%；
  任一失败则 full run 停在 feasibility/coverage。cross-case cost
  estimate 至少要求 4 repo 各 1,000 joined calls，具体 operation 至少
  4 repo 各 30 calls。
- **预注册。** 冻结 syscall 列表、fd/path 生命周期、PID/cgroup
  ownership、overlap attribution、workspace-relative path policy、
  endpoint redaction、采样率、lost-event/overhead gate 和每项 cost 单位。
- **独立对账。** 5% 的短 canary calls 用 `strace -ff -c`/独立
  `/proc/<pid>/io` 计数对账 syscall 与 bytes；process tree 由另一个
  `/proc` snapshot reader重建；workspace effect 继续由 source-direct
  checker而非 eBPF 输出定义。

### 预期论文位置

**独立第二篇系统论文。** 当前 AAAI 只能在 future work 提一句，不能把
尚未采集的 OS 证据并入结果。后续论文可以把候选 A 的 trace-derived
机会边界作为动机，本 RQ 作为 headline measurement，再接候选 H 的
state-aware system。

### 风险与最可能失败方式

风险包括 root 权限与内核可移植性、极短进程漏失、并发 call 归因歧义、
eBPF overhead、静态链接 TLS、FD reuse、page cache 使 syscall bytes 与
block I/O 不同，以及 path/endpoint 隐私。最可能的阻塞是 Agent tool
call 与本地子进程没有稳定一对一 ID，导致只能得到 session/operation
级成本而非 call 级成本。

## 候选 E：晚期重读是必要 re-grounding 还是 context-pressure signature

### 一句话 RQ 与科学意义

**RQ：在相同 workspace checkpoint 和下一任务提示下，保留完整历史、
提供 source-grounded compact state 或只保留 workspace 的不同上下文条件，
如何改变 late-session reread、首次新 effect 和 validation 路径？**

现有 233 个长 roots 中，五个足量 project×vendor strata 的 late-minus-
early reread 都增加 16.7--28.9 pp，但 failure 和 edit fragmentation
没有共同上升，所以观察数据不能区分必要 re-grounding、任务阶段变化与
context degradation。AgingBench、Plans Don't Persist 和 TRAJEVAL 已研究
长上下文可靠性，不能声称 context aging 是新问题；survey 未找到把受控
context 条件与 persistent artifact identity、reread 和 workspace effect
共同测量的设计。它扩展空白 2，并为现有 late-reread 结果提供机制判别。

### 估计量与可观察定义

对同一 checkpoint 的三个条件做配对：

- **F：Full history**，重放完整已冻结 conversation/tool history；
- **S：Source-grounded compact state**，只提供由 source facts 构成的
  当前 task、已改 artifact、未完成 validation 和 workspace version；
- **R：Workspace-only reset**，只给原始任务/下一提示和完全相同 workspace。

主估计量为：

1. 首次 novel confirmed mutation 前的 reread calls、unique artifacts、
   result bytes 和 action distance；
2. reread 中 unchanged/changed-since-last-read、same-module/
   cross-module、内容是否进入随后 edit context 的可观察比例；
3. 到首次 confirmed mutation、recognized validation 和 task terminal
   state 的 action/runtime 分布；
4. fail、superseding mutation、重复 validation 和 final official test
   outcome；official outcome 只作 correctness/control，不与前述量加权。

关键 treatment contrasts 是 `R-F`（缺少历史造成的 reset-induced
re-grounding）、`F-S`（完整长历史相对 compact state 的 context-pressure
signature），以及它们在 early/late checkpoint 的差分。只有 `R>F≈S`
才支持 reset-induced re-grounding；`F>S` 且主要增加 unchanged reread/
pre-effect distance，才支持较窄的 context-pressure signature；二者同时
出现就是 mixed。仍不把单次 reread判为“必要”或“退化”。

### 数据来源与新增成本

现有自然语料只能用于选择 checkpoint 长度和估计方差，不能回答机制。需要
可精确 fork 的真实 agent/benchmark 任务、workspace snapshot、完整
message history 和 source-grounded state constructor。

建议 pilot 为 6 个任务×2 checkpoint ages×3 conditions=36 runs；full
run 为 24 个任务×2 ages×3 conditions×2 repetitions=288 continuations，
同时覆盖 coding 与 auto-research。模型、提示、预算和 official oracle
固定。成本高，且 source-grounded compact state 的构造必须确定性，不能
由另一个 LLM 充当隐藏 judge。

### 实验设计

- **工作负载。** 只纳入能在相同 snapshot 上精确 fork、checkpoint 前至少
  30 calls、后续有可执行 validation/terminal rule 的任务。checkpoint
  age 在看结果前冻结。
- **随机化与分层。** task×checkpoint 是 block，condition order/seed
  随机；coding/research、model 和 age 分层，不跨 task 把 calls 当独立。
- **门禁。** pilot 要求三条件 workspace hash、下一提示、model config
  完全相同，所有条件能走通真实 tool path；full result 至少 20 个完整
  task×checkpoint blocks。不能按结果好坏筛 checkpoint。
- **预注册。** 冻结 compact-state 字段、novel effect、reread、changed
  version、content-to-edit evidence、terminal/censoring、最大预算和
  condition contrasts。修改 oracle 或 summary 字段后必须重跑受影响块。
- **独立对账。** checker 验证 fork hash、message membership、tool
  action、artifact version 和 official oracle；不导入 treatment runner。

### 预期论文位置

**独立第二篇 Agent 行为/机制论文。** 当前 AAAI supplement 保留现有
观察性 late-reread 与“非 degradation”限定即可；没有受控结果前不要在
main 中新增机制 RQ。

### 风险与最可能失败方式

compact state 可能遗漏信息或本身提示 Agent，从而把 `F-S` 混入
representation effect；full-history replay 未必复现 provider 隐藏状态；
benchmark 阶段不代表自然长会话；288 runs 成本高。最可能结果是
reset 产生稳定额外 reread，而 full 与 compact 的差异小，说明当前观察
更像 phase/re-grounding 而非普遍退化。

## 候选 F：真实长期会话中的失败恢复路径与持久后果

### 一句话 RQ 与科学意义

**RQ：一次 source-verified 工具失败之后，Agent 以 exact retry、改参数、
换目标或换工具中的哪条路径恢复，恢复需要多少行动/时间/结果流量，并与
随后 workspace mutation、validation 和复用怎样共现？**

失败率、retry loop 和 recovery 已有大量 benchmark 先例，不能作为宽泛
novelty。survey 空白 1 的未覆盖部分是：真实长期语料上
canonicalized invocation、失败原因、恢复序列、恢复结果、代价和持久
workspace 后果的联合测量。现有 strict chain 只有 16 条/58 calls，说明
只数连续三次失败会漏掉更常见的“失败—诊断—改路—恢复”。

### 估计量与可观察定义

1. 以 native decisive status/exit code/errno 和规范化 error signature
   定义 fail；projection `status=fail` 作为敏感性。必须先解释现有
   5,185 projected fails 与 profile-derived 5,466 observable failures 的
   差异。
2. 后继路径互斥分为 exact same-input retry、same target changed args、
   same operation changed target、tool-family switch、modified route、
   prompt/stream end。
3. 从 fail 到 first exact-target `ok`、first confirmed workspace effect、
   next recognized validation 的 action distance、start-to-start gap、
   tool runtime 和 result bytes；观测末端无返回是 censored，不叫放弃。
4. 恢复后 mutation 的 later reuse、validation-before-supersession 和
   final artifact existence分列。它们是后续事实，不证明恢复“正确”。

### 数据来源与新增成本

现有 1,917 个 native logs、failure follow-up/profile、RQ1 mutation 和 RQ2
validation ledger 足以做主要分析；需要新增 deterministic errno/exit/
error-signature parser，但不需新采集。成本低到中等，主要风险是私有原始
error text 的安全解析与可发布聚合。

### 实验设计

- **分层。** project×vendor×operation/error family；root/source stream 是
  ordering block。
- **门禁。** cross-case recovery estimate 要求至少 4 个项目各 50 个 source-verified
  fails；具体 error family 要求至少 20 个事件，否则只报案例。
- **预注册。** 冻结 exact target key、error normalization、允许的 interleaving、
  recovery endpoint、censoring 和 cost 单位。主结果使用完整
  cumulative-incidence/action-distance 曲线，不挑一个“10 calls 内”阈值。
- **独立对账。** checker 从 native tool result/exit status 重建全部 fail 和
  exact-target return，并抽查每个 error family 至少 20 条；workspace
  后果从独立 RQ1 ledger join。

### 预期论文位置

**当前 supplement 扩展；不占 main 新 RQ。** 可替换目前过窄的 strict
failure-chain 小节，或与候选 A 的 recovery 维度合并。若加入候选 D 的
OS cost，则升级为下一篇系统论文的一部分。

### 风险与最可能失败方式

vendor status/error schema 不可比，changed args 可能是全新任务，恢复
`ok` 不代表目标正确，长 action distance 中夹杂其他工作。最可能结果是
exact retry 很少、modified route 很多，导致“失败额外成本”的归因只能
保守到时序上界。

## 候选 G：文档性 artifact 是否承载跨 session 连续性

### 一句话 RQ 与科学意义

**RQ：Agent 创建的论文、文档、计划和状态 artifact 有多少在后续独立
native roots 中被再次读取或修改，并在何种 action distance 上与恢复同
module 工作、首次 mutation 和 validation 相邻？**

措辞刻意不用“文档是记忆”。现有 1,066 个 observation-born 文档中
62.4% 后来被读、29.8% 无后续 confirmed action，但该结果没有拆同 root/
跨 root，也不知道文档是否被指令要求。survey 空白 2 没有先例系统研究
真实 persistent repo 中 agent-created documentary artifacts 的跨 session
lineage；AgentTrails 有 provenance prototype，但没有这种规模化纵向
估计。

### 估计量与可观察定义

1. confirmed-created documentary identity 的 final existence、same-root
   reread、later-root reread/mutation、first cross-root distance 和
   right censoring；
2. later root 首次 mutation 前是否读取该文档，以及随后 first mutation
   与文档是 same artifact/module/cross-module；
3. project product docs、instruction、plan/status、experiment-process
   docs 分层；code/config 为描述性 reference，不作价值比较；
4. reread 后 recognized validation-before-next-mutation 和 revived
   artifact 状态。只称 temporal association。

### 数据来源与新增成本

现有 artifact lineage、RQ4 components、user-question artifact type 和
bookkeeping classifier 足以做 within-case 分析；无需新模型调用。能否做
cross-case 取决于跨 root eligible denominator，当前尚未计算。若 gate
停止，需要继续自然采集，而不能降低阈值。

### 实验设计

- 按 project×vendor、document class、birth root 和 later-root
  availability 分层；重叠 session component 不强行排序。
- cross-case gate：至少 4 个项目各有 20 个 confirmed-created docs、
  20 个后续非重叠 boundaries 和 10 个 observed cross-root returns；
  任何一项不足即 within-case。
- 冻结 path classification、birth/rename/delete lineage、root component、
  reread status 和 competing outcome；不能用文档正文作语义标签。
- 独立 checker 从 native records 重建所有 document births 和 later-root
  reads，并用 final workspace/Git 只核对 final existence。

### 预期论文位置

**当前 supplement 中合并进 RQ1+RQ4 的扩展，不做 main 独立 RQ。**
若跨案例 gate 通过，可在 main RQ4 的一句话里增加“documentary
continuity”；若停止，就只保留覆盖结果。

### 风险与最可能失败方式

文档可能是最终产品而非外部记忆，path classifier 在 Skill/论文项目中
构念混淆，后续读者可能是人或另一个 Agent，且一个大项目可能贡献绝大
多数文档。最可能失败是只有两个大项目达到 cross-root denominator，
因此无法形成跨案例结论。

## 候选 H：开放式 Agent 工具图的状态感知增量计算

### 一句话 RQ 与科学意义

**RQ：当持久 workspace 只发生局部变化时，开放式 Agent 工具图中哪些
历史结果仍然有效、哪些节点必须重算，状态感知增量执行能在保持结果与
workspace 一致的前提下复用多少执行、时间和结果字节？**

这直接对应 survey 空白 4+5。TVCACHE 依赖完整历史前缀等价，Cortex 是
读侧语义缓存，AWO/tool-making 编译重复流程，AgentTrails 恢复 provenance；
没有先例像 build system 一样维护开放式工具的 read/write/side-effect
依赖并在跨 session 局部 mutation 后做安全增量重算。

### 估计量与可观察定义

每个 tool node 记录 exact args、input/output hash、read/write set、
side-effect class、environment/network dependency、workspace version 和
status。每次 mutation 后报告 invalidated transitive closure、仍有效
nodes、实际 reused executions/runtime/bytes、stale-result mismatch 和
fallback。nondeterministic/network/unknown-effect nodes 默认 volatile；
不把潜在 eligibility 算作 hit，也不构造综合“增量价值分”。

### 数据来源与新增成本

当前 trace 的 49.47% unknown edges、无统一 workspace version 和不可见
外部写入，使它只能给乐观上界，不能验证 correctness。需要候选 D 的
eBPF read/write set、版本化 sandbox、可 replay 的真实任务和一个实际
state-aware executor，开发与运行成本最高。

### 实验设计

- 先用 6 个真实 tasks 做 read/write-set 与 replay preflight；full run
  至少 30 个 coding/research tasks、多个真实 mutation checkpoints。
- project/task family × operation × side-effect class 分层；task/checkpoint
  是比较块，不能把一个任务中的 tool nodes 当成独立任务。
- 对比 current no-reuse、完整历史前缀等价 cache（代表最强安全现有
  position）和 state-aware incremental executor；不能用已知弱的
  same-command memoization 充当主 baseline。
- primary correctness gate 是 tool status/output、workspace hash 和
  official validation 一致；任一 stale result 未被 version check 拦截，
  该 comparison 判 invalid，而不是用 speedup 抵消。
- 至少 90% 的 admitted deterministic nodes 要有 complete read/write set，
  至少 20 个 tasks 完整结束。预注册 exact cache key、workspace version、
  invalidation closure、volatile/unknown-effect policy、fallback、baseline
  budgets 和每个 execution/runtime/bytes estimand。
- 独立 fresh rerun 和 `strace` canary 重建 dependency/fallback；checker
  不读取 incremental engine 的 hit/valid 标志，而从文件版本、系统访问和
  fresh output 自行判断。

### 预期论文位置

**独立第二篇系统论文，最好与候选 D 合并。** 当前 AAAI 不应出现除
future-work 外的任何效果表述。

### 风险与最可能失败方式

隐藏环境依赖、网络与时钟 nondeterminism、编译器/daemon 外部写入、
read/write-set 采集 overhead 和 side effect rollback 都可能使通用缓存
退化为只支持 local read/search。最可能的可信首版是窄的
versioned-file/query graph，而不是所有工具通用增量执行。

## 推荐优先级

下面是按 **novelty × 可行性 × 对当前论文的边际增益** 的粗粒度顺序。
高/中/低是决策标签，不是科学评分。

| 排名 | 候选 | Novelty | 当前可行性 | 对当前 AAAI 增益 | 推荐动作 |
|---:|---|---|---|---|---|
| 1 | A Workload 与优化边界 | 高 | 高：证据已完成 | 高 | 立即升为 main 正式 RQ |
| 2 | B 人类参与/改向 | 高 | 高：approved plan/review/脚本已在、只待结果 | 中高：关闭 corpus 自主性 confound | supplement + main 限定一句 |
| 3 | C 共性/不变量 | 中高 | 中：plan/脚本已冻结，尚无 terminal 结果 | 中高：强化 external validity | 重构现有 RQ6，不新增编号 |
| 4 | G 文档性连续性 | 高 | 中高：可复用现有 lineage | 中：紧贴 artifact 主线 | supplement，过 gate 才进 main 一句 |
| 5 | F 失败恢复 | 高 | 中高：原始数据已有 | 中低：会挤压中心故事 | supplement；以后与 OS cost 合并 |
| 6 | D eBPF 三方联合 | 很高 | 中低：需新 probe 和真实采集 | 当前低、下一篇很高 | 下一篇 systems headline |
| 7 | E 晚期重读机制 | 高 | 低：需 288 次左右受控 continuation | 当前低、机制价值高 | 独立行为/机制论文 |
| 8 | H 增量计算 | 很高 | 低：需系统实现与 replay | 当前低、下一篇高 | 与 D 合并为后续系统论文 |

## 对当前 AAAI 稿件的具体取舍

### Main：只做一个净新增

建议 main 保持六个正式 RQ，而不是扩成七到九个：

1. RQ1 artifact consolidation/revival：保留；
2. RQ2 validation response：保留；
3. RQ3 workspace focus：保留；
4. RQ4 cross-session continuity：保留 stopped gate；
5. **新 RQ5 workload characterization and optimization bounds：采用候选 A；**
6. **RQ6 cross-corpus invariants and boundaries：由当前 external-boundary
   RQ6 强化而来。**

当前 named-Skill fingerprint 只有一个项目支持 two-Skill comparison，
科学增益低于 workload；建议移到 supplement 的 source-attribution/
negative-result 小节。这样无需增加 main RQ 数量，也不牺牲已完成证据。

### Supplement：吸收已完成或低成本分析

- 候选 A 放完整估计量族、project/vendor 异质性、所有安全限定；
- 候选 B 在 source-native run 与独立 review 通过后加入；
- 候选 C 放 candidate registry、compatibility/N/A matrix 和全 strata；
- 候选 G 仅在跨 root gate 通过时作为 RQ1/RQ4 extension；
- 候选 F 可取代当前只覆盖 0.032% calls 的 strict-chain 小节，但不应与
  A 重复堆数字。

不要为了 supplement 完整而同时加入 G 和 F；优先选择能关闭审稿质疑的
B，其次选择更贴主线的 G。

### 下一篇

最自然的 systems paper 组合是 **A 的 observational bounds → D 的
AgentSight 三方 profile → H 的 state-aware incremental executor**。
最自然的行为机制论文是 **当前 late-reread 观察 → E 的 matched
checkpoint fork**。二者需要不同 workload、truth contract 和审稿社区，
不建议合成一篇，也不应塞回当前 6 页 AAAI 稿。

## 最终门槛

任何候选只有在以下条件全部满足后才可从“提案”进入论文事实：

1. 分母、去重、status、session/component 和 censoring 已冻结；
2. 结果不是由同一个 parser 自我对账；
3. positive、contradictory、mixed 和 stopped 都有预先写明的论文处置；
4. 不把 opportunity bound、temporal association 或 proxy 改写成
   speedup、causality、quality、waste、memory 或 degradation；
5. running 分析必须有 terminal report/result-review。当前
   `human-involvement-20260726` 有 approved plan、review 和脚本，
   `invariance-mining-20260726` 有 plan 和脚本，但两者都还没有 terminal
   report/result-review，因此本提案没有预设其结论。
