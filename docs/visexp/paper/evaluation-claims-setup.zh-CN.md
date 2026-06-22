# AgentFlame / agentpprof 评估说明：claim、实验 setup 与证据边界

本文档是一份论文形态的详细评估说明。它把 research branch 上分散的 claim
记录、结果摘要、实验 tracker 和生成 artifact 整理为一条可审稿的论证链：先定义
术语，再列出 claim，最后说明每个实验的 setup、oracle、结果和不能支持的结论。
为了让 `main` 保持可维护，这个分支只提交这份整理后的公开文档，不提交原始本机
session、大型输出目录或中间规划笔记。

当前结论很明确：我们已经有强的机制证据，说明语义帧可以把普通
process/effect summary 会混在一起的 agent 系统行为拆开；我们也有 scoped
exact-lineage 证据，说明固定命令模式下 `tool_call -> shell -> child process
-> file/network effect` 可以精确连接；但我们还没有证明开发者使用这个视图会
更快、更准，也没有证明一词标签在语义上充分正确。因此当前版本是一个有真实
数据和可复现实验的 systems research prototype，不是已经完成的 OSDI weak
accept 结果。

## 摘要

AI 编程 agent 的执行历史同时包含两类信息。第一类是上层语义：用户问了什么、
agent 在哪个 prompt 下工作、模型在什么上下文中调用。第二类是下层系统效果：
agent 运行了哪些工具、产生了哪些进程、读写了哪些文件、发起了哪些网络连接、
测试或构建失败了多少次。传统 agent tracing 工具通常擅长第一类信息，传统
profiling/audit 工具通常擅长第二类信息；真正困难的问题是把两者稳定地连起来，
并且在许多 session 之间聚合。

AgentFlame 的核心设计是语义系统效应剖析。系统先给 session、prompt 和 LLM
call 生成短的一词标签，然后把 tool、shell、child process 和 file/network
effect 通过确定性 lineage 归到对应语义上下文，再输出 folded stacks、pprof、
SVG flamegraphs 和 JSON。agentpprof 是当前产品化方向：它把这套思想收敛为一个
可以读取 Codex/Claude 本地 session 的 Rust CLI，并输出 pprof-compatible profile、
folded stack、SVG 和 JSON。

R170 full-history refresh 是当前最重要的 characterization run。它分析本机
AgentSight 相关的 325 个可读 Codex/Claude session、142,468 个 raw tool events、
114,837 个 raw LLM events，产生 183,714 个 system-effect observations，并折叠成
26,829 个 unique semantic system stacks。加入语义帧后，system-effect profile 的
压缩率是 6.848x；删除 session/prompt 语义后，90.402% 的系统权重进入 mixed
buckets；flat effect summary 的 mixed weight 是 90.918%。R224 在同一分母上消融
语义轴，显示 prompt-only 是最有用的单语义轴：mixed weight 从 no-semantic 的
90.402% 降到 36.722%，residual mixed weight 从 44.716% 降到 7.485%。

这个结果支持的 claim 是机制性的：语义帧能把传统 process/effect profile 会混合
的系统效果区域拆开。它不支持用户效用 claim。C5 用户任务实验还没有真实参与者
响应；C6 标签充分性实验还没有真实人工标签；R180、R251、R189--R218 只能分别支持
语法稳定、行为相关性和可逆 display-governance 机制，不能替代人工语义 adequacy。

## 术语表

本节定义本文档中使用的所有专门术语。普通中文词不逐词定义；所有会影响实验结论
的技术词都在这里给出工作定义。

- Agent：执行用户任务的 AI 编程工具，例如 Codex CLI 或 Claude Code。本文中的
  agent 不是抽象人格，而是会产生本地 session 日志、工具调用和系统行为的软件。
- Session：一次连续 agent 运行或一段可解析的 agent 历史。Codex/Claude 通常把
  session 保存为 JSONL。一个 session 可以包含多个 prompt、多个 LLM call 和多个
  tool call。
- Prompt：用户或系统在 session 中给 agent 的一次任务上下文。本文把 prompt 当作
  system-effect profile 的主要语义轴，因为一次 prompt 往往对应一个用户想解决的
 具体问题。
- Prompt row：解析 session 时得到的一条 prompt 记录。它是实验中的表格行，不一定
  等同于唯一自然语言字符串。R233 专门处理了 duplicate prompt indexes。
- LLM call：agent 向语言模型发出的一次模型请求。它可能包含 prompt tokens、
  completion tokens、模型名和响应状态。
- Tool call：agent 要求本地工具或 shell 执行的一次操作，例如 `rg`、`sed`、
  `cargo test`、`git status` 或文件编辑工具。
- Shell：执行命令行的进程层，例如 `bash`、`sh` 或 agent 内部启动命令的 wrapper。
- Child process：tool call 或 shell 启动的子进程，例如 `cargo` 启动的测试进程。
- System effect：进程、文件、网络、测试、构建、读写、状态码等可观测系统效果。
  本文中的 effect 是观测事实，不是 LLM 的解释。
- File effect：文件层面的 system effect，例如读取、写入、创建、删除、路径命中。
- Network effect：网络层面的 system effect，例如 bind、listen、connect、HTTP probe
  或 target process 产生的连接行。
- Raw event：解析器或 eBPF/collector 看到的原始事件。raw event 是最底层输入。
- Observation：用于 folded stack 计数的一条标准化观测。一个 raw event 可能被过滤、
  归一化或映射成一个 observation。
- Weight：folded stack 的宽度单位。system flamegraph 中 weight 是 system-effect
  observation count；token flamegraph 中 weight 是 token count；duration projection
  中 weight 是 wall-clock duration。
- Stack frame：folded stack 中由分号分隔的一段，例如 `session:review`、
  `prompt:test`、`process:cargo`。
- Folded stack：一行形如 `a;b;c 7` 的聚合记录，表示 stack `a;b;c` 出现 7 次或权重
  为 7。它是 flamegraph 和 pprof profile 的中间表示。
- Flamegraph：把 folded stacks 画成横条图的可视化。横条宽度表示 weight，纵向表示
  stack 层级。本文的火焰图用于看哪里重、哪里绕、哪里重复，不默认表示 duration。
- Semantic frame：由 session、prompt 或 LLM-call tag 形成的语义栈帧，例如
  `session:refactor` 或 `prompt:review`。
- One-word tag：小模型或规则 tagger 输出的一个英文小写词。它是导航/聚合标签，不是
  verdict，也不是安全结论。
- Projection：从同一事实表生成不同 stack 的方法。例如 system projection 关注
  process/effect，token projection 关注 LLM token，prompt-only projection 只保留
  prompt tag。
- Baseline：用于比较的简化视图。本文主要 baseline 是 flat effect summary、
  nonsemantic folded stacks 和 session-only/prompt-only 消融。
- Flat effect summary：只按 process/effect/status 等系统事实聚合，不包含 session
  或 prompt 语义。
- Nonsemantic stack：去掉 session/prompt 语义帧后的 folded stack。它仍可能有
  process、effect、status，但不知道用户任务语义。
- Mixed bucket：一个 baseline bucket 对应多个 full semantic stacks 或多个语义区域。
  mixed bucket 表示 baseline 把不同语义来源合并了。
- Mixed weight：所有 mixed buckets 覆盖的 weight。比例越高，说明 baseline 越会把
  不同语义来源混在一起。
- Residual mixed weight：在去掉主导语义区域后，mixed bucket 中剩余非主导区域的
  weight。它衡量一个 bucket 内真正被掩盖的次要语义区域。
- Compression ratio：总 observations 除以 unique stacks。值越高表示重复路径越多、
  聚合越强；但过高也可能意味着语义信息被压掉。
- Oracle：判断实验是否通过的规则。oracle 不能是“看起来对”，必须是可执行检查、
  人工标注协议或明确阈值。
- In-scope effect：实验声明要归因的目标 effect。比如 R114 中 Codex command-mode
  目标进程家族内的 file/process effects。
- Out-of-scope effect：实验不应归因的 effect，例如 wrapper、sibling 或 unrelated
  process 产生的事件。
- Orphan：未被 join 到目标 session/tool/prompt lineage 的 effect。orphan 不一定是
  bug；out-of-scope events 应该保持 orphan。
- Negative control：故意制造但不应该被归因到目标任务的事件，用来检查 false positive。
- Scoped precision：在实验 scope 内，所有被 join 的 effect 中有多少是真正目标 effect。
- Scoped recall：在实验 scope 内，目标 effect 中有多少被成功 join。
- Target-network row：目标 workload 的子进程或目标程序产生的网络行，不是 agent runtime
  自身的网络行。
- Runtime witness：R238 使用的运行时证明，证明 agent-launched network probe 确实执行
  到目标端口。
- Adequacy：一词 tag 是否足以表达人类认为重要的任务语义。语法合法不等于 adequacy。
- Canonical tag：display 层把若干 raw tags 映射到的展示标签。raw tags 不被覆盖。
- Active display map：默认展示时真正生效的 raw-to-display 映射。
- Pending candidate：候选合并、重生成或拆分建议。没有审核前不能进入 active display map。
- Drilldown：从聚合 display label 回到 raw rows、raw tags 和原始支持证据的能力。
- Display governance：控制 raw tags、canonical tags、pending candidates、人工审核和
  update gate 的机制。
- Claim gate：每个 claim 是否 supported、partial、unsupported 的明确判定。
- C5：本文的用户效用 claim，即 semantic flamegraph 是否改善开发者任务结果。
- C6：本文的标签 adequacy claim，即 one-word tags 是否被人工认为语义充分。
- Weak accept：按 OSDI/SOSP 评审标准可能达到弱接收的整体证据水平。本文当前不满足。
- Public-safe artifact：可以提交到仓库的结果。它不能包含原始 prompt、私有路径、密钥、
  原始本机 session 或不可公开的真实用户响应。
- Private return：真实参与者或标注者返回的 CSV。它应保存在 `private/`，不能提交。
- Run ID：实验编号，例如 R170、R224。编号只标识一次实验或一组脚本，不代表论文
  claim 自动成立。
- JSONL：每行一个 JSON object 的日志格式。Codex/Claude session histories 常用这种格式。
- SQLite DB：SQLite 数据库文件。AgentSight collector 会把部分 live capture 结果写入
  SQLite，后续 `report export` 可以再导出。
- eBPF：Linux 内核中的可观测性/安全扩展机制。AgentSight 用 eBPF/uprobes/tracepoints
  观察 SSL、进程、stdio 和系统行为。
- pprof：Go 生态常见的 profile 数据格式和查看工具。agentpprof 生成 pprof-compatible
  `profile.pb.gz`，这样用户可以用 `go tool pprof` 打开。
- SVG：可缩放矢量图格式。本文的 flamegraph 示例用 SVG 保存，便于浏览器打开。
- JSON：结构化文本数据格式。本文的 summary artifacts 用 JSON 保存机器可读结果。
- Regex：regular expression，正则表达式。agentpprof 的 deterministic tagger 可以用
  `--tag-rule prompt:test='(?i)cargo test|pytest'` 这类规则打标签。
- Llama.cpp：本地运行 GGUF 语言模型的推理服务。本文用 llama.cpp HTTP server 提供
  one-word tagger。
- GGUF：llama.cpp 常用的量化模型文件格式，例如 `qwen2.5-3b-instruct-q4_k_m.gguf`。
- Cache hit：标签请求已经在 `tags.json` 中存在，系统不再调用模型。
- Dirty provenance：实验运行时 git worktree 不是干净状态。这样的结果可以作为机制证据，
  但不能当成 clean release artifact。
- Smoke test：小范围端到端检查，证明路径能跑通。smoke test 不能替代完整实验。
- Fixture：人为构造或固定的小输入，用来稳定测试工具路径。public-safe generated
  fixture 是研究实验中可公开的小输入；real local session 通常不能提交。当前 `main`
  不在 `agentpprof/` 下提交这些 generated session inputs。
- Proxy metric：代理指标。它与目标问题有关，但不能直接等同目标结论。R251 的行为相关性
  是 tag adequacy 的 proxy，不是人工 adequacy。
- Outcome evidence：直接支持用户或标签结论的数据，例如真实参与者响应、真实人工标签。
- Protocol：收集或评分数据的流程和格式。Protocol ready 不等于结果 ready。
- Adjudication：两个标注者不一致时的裁决步骤。没有 adjudication 时，分歧行不能进入
  final label。
- Hygiene gate：检查论文措辞、路径泄漏、artifact 边界或编译状态的实验。它能防止
  过度声明，但不能增加新的 outcome evidence。

## 研究问题与 claim ledger

本文的 thesis 是：

> Agent system-effect profiling should connect user-task semantics to concrete
> file/process/network/token effects, then aggregate those connected effects as
> folded stacks.

换成中文：我们要剖析的不是 agent span 本身，也不是孤立进程列表，而是“用户语义
任务造成了哪些系统效果”。因此评估必须同时回答语义聚合、系统归因、标签成本、
artifact 可用性和用户效用。

### Claim C1：可以生成真实本地 agent 历史的语义 folded stacks

Scope 是本机 AgentSight 仓库相关的 Codex/Claude JSONL histories。证据来自 R170：
325 个可读 sessions、183,714 个 system-effect observations、26,829 个 semantic
system stacks。这个 claim 当前 supported，但只针对 local-history projection，不是
live eBPF exact-effect full-history。

### Claim C2：本地一词标签在工程上可行

Scope 是 llama.cpp 本地模型和 regex/rule fallback 的产品化路径。R170 显示 0 个最终
tag 失败；R180 显示 0.6B/1.1B/3B-class GGUF 在 300 个 redacted fragments 上均产生
900/900 grammar-valid outputs。这个 claim 对 syntax、latency 和 cache feasibility
supported；对 semantic adequacy partial/unsupported。

### Claim C3：语义帧能分开 nonsemantic baseline 混合的 system effects

Scope 是 R170 的同一分母。R170/R224/R223/R251/R211 支持这个机制 claim。最强结果是
nonsemantic mixed weight 90.402%、flat mixed weight 90.918%，prompt-only projection
把 mixed weight 降到 36.722%。这个 claim supported，但它不是用户效用 claim。

### Claim C4：system effects 可以被 exact lineage 归到 agent task

Scope 是固定 command-mode suite、controlled external repos、target HTTP probes 和局部
agent-family workloads。R114/R191/R229/R232/R234 给出 scoped precision/recall 和 0
negative joins；R235--R240 暴露并局部修复 harder network boundaries。这个 claim 在固定
范围内 supported，广义 full-history/arbitrary-agent/arbitrary-network 仍 partial。

### Claim C5：semantic flamegraphs 改善开发者任务结果

Scope 应是人类开发者完成 forensic/debugging tasks。当前没有真实参与者响应，因此
unsupported。R142/R249/R258/R259/R268/R271 是 collection 和 scoring readiness，不是
outcome evidence。

### Claim C6：one-word tags 语义充分

Scope 应是人工判断 session/prompt/LLM-call tags 是否表达了足够语义，并判断 merge/
regeneration 是否过合并或漏合并。当前没有真实人工标签，因此 adequacy unsupported。
R180 是 syntax/stability；R251 是 behavior-association proxy；R189--R218 是 reversible
display governance。

### Claim C7：agentpprof/AgentFlame 可以作为开源开发者工具使用

Scope 是 public-safe generated fixture smokes、install/readback、pprof output 和
packaging。R160/R200/R220/R248/R253/R254/R256 supported/partial。仍缺 crates.io
publish/readback、external-machine install、真实历史报告 sanitization、llama.cpp setup
文档和社区反馈。

## 系统模型

系统分为四层。

第一层是 agent-native history layer。它读取 Codex/Claude session logs，恢复 session、
prompt、LLM call、tool call 和部分系统行为。它不需要 sudo，也不需要 eBPF。R170、
R189--R225 和 agentpprof generated-fixture smokes 都属于这一层。

第二层是 semantic tagging layer。它只处理 session、prompt 和 LLM call 文本，输出一个
词。这个 layer 可以由小模型、regex rules 或未来的后端服务实现。重要的是：模型不直接
判断每个 file/network effect 的语义，避免让 LLM 猜系统事实。

第三层是 lineage layer。它把 tool call、shell、child process、file/network effect 连接
起来。AgentSight live capture 的目标正是这层：`tool_call -> shell -> child process ->
file/network effect`。R114/R191/R229/R232/R234 是这层的核心证据。

第四层是 projection/display layer。同一事实表可以输出 system flamegraph、token
flamegraph、duration baseline、prompt-only profile、session-only profile、nonsemantic
baseline、active display map、pending candidate overlay 和 raw drilldown。R223/R225/R209/
R212/R213/R214 证明这些 projection 的区别与边界。

## 实验方法

每个实验都用同一种描述格式：

- Setup：输入数据、机器或命令、模型、样本规模和运行方式。
- Workload：agent 实际处理的任务或历史。
- Baseline：比较对象。不是每个实验都有 baseline；没有时明确写出。
- Oracle：判断通过的规则。
- Metric：数字结果，例如 coverage、precision、recall、mixed weight、latency。
- Result：实验观察到什么。
- Claim boundary：这个结果能支持什么，不能支持什么。

这种写法的目的不是让文档更长，而是避免一个常见 research 失败模式：把一个 smoke
test 写成 strong claim，或把一个 collection kit 写成人类实验结果。

## RQ1：全量本地历史能否被语义标注和折叠

### R170：full-history semantic system profile

Setup：R170 在本机 AgentSight research branch 上运行 AgentFlame Rust prototype。命令
扫描最多 10,000 个 session files，并连接本地 llama.cpp HTTP server。模型是
`qwen2.5-3b-instruct-q4_k_m.gguf`。输出写入 `.agentsight/agentflame/r170-full-current`，
公开 summary 写入 `docs/visexp/out/full-history-r170.json` 和同目录 Markdown。

Workload：本机可读的 AgentSight 相关 Codex/Claude session histories。R170 共读取
325 个 sessions，来源是 Codex 198、Claude 50、Claude subagent 77。一个 root-owned
Claude JSONL 不可读，被记录为 warning 而不是静默跳过。

Oracle：报告必须可解析；folded totals 必须等于 summary totals；prompt tags 和 LLM-call
tags 的 final invalid count 必须为 0；warnings 必须显式记录。

Metrics：142,468 raw tool events、114,837 raw LLM events、2,859 prompt rows、
328 unique prompt tags、1,423 unique LLM-call tags、183,714 system observations、
26,829 semantic system stacks、6.848x semantic compression。tagger 总请求 118,021，
cache hits 82,886，llama.cpp HTTP calls 35,136，successful final tags 35,135，final
failures 0。

Result：R170 支持 C1 和 C2 的工程可行性，并给 C3 的 projection 实验提供分母。

Boundary：R170 是 dirty-provenance mechanism evidence，不是 clean release run；它也不
是 C5/C6 outcome evidence。它不能证明标签语义充分，也不能证明 live exact effect
lineage。

### R122/R123/R180/R124：标签语法、稳定性和人工 adequacy 协议

R122 Setup：从真实历史中采样 300 个 redacted fragments，包括 100 session、100 prompt、
100 LLM-call fragments。redaction 删除 home paths、secrets、emails、URL paths 和长 ID。
R122 的输出是 label packet，不是实验结果。

R123 Setup：用本地 3B llama.cpp server 对 R122 的 300 fragments 各跑三次 identical
repeat。Oracle 是每次输出必须是合法一词 tag，并统计 exact-stable fragment 数。
Result 是 900/900 valid tags、285/300 exact-stable fragments、p95 latency 31 ms。这个
结果支持 3B syntax/latency/stability，不支持 adequacy。

R180 Setup：用同一 300 fragments 比较 0.6B、TinyLlama 1.1B 和 3B-class GGUF，均用
`--reasoning off`。Oracle 与 R123 相同。Result 是三个模型都 900/900 valid；exact stability
分别是 299/300、279/300、285/300；p95 latency 分别是 23/18/32 ms。TinyLlama 1.1B
大量输出 localization/localized，说明“稳定合法”不能等同“语义好”。

R124 Setup：准备两个 blinded human labeler sheets 和 join/adjudication protocol。当前
scoring run 仍是 `human_labels_empty`，300 packet rows、300 candidate tags、0 final
labels。Boundary 是 C6 adequacy unsupported。

## RQ2：语义 projection 是否比传统 summary 更有信息量

### R131/R224：semantic-axis ablation

Setup：R131 是 semantic-axis ablation checker；R224 在 R170 current full-history folded
artifacts 上重跑 R131，使所有 system-axis rows 共享 183,714 的 effect denominator。输入
是生成过的 folded artifacts，不重新读取 raw traces，也不调用 LLM。

Variants：no semantic、session-only、prompt-only、session+prompt。所有 variants 必须
保持总 weight 183,714。

Oracle：每个 projection 的 total weight 必须等于 R170 denominator；mixed bucket 统计
必须基于 full semantic variants；full session+prompt 的 mixed weight 为 0 是定义上的
audit upper bound。

Results：

| Projection | Unique stacks | Compression | Mixed weight | Residual mixed weight |
| --- | ---: | ---: | ---: | ---: |
| No semantic | 11,967 | 15.352x | 90.402% | 44.716% |
| Session only | 15,027 | 12.225x | 84.407% | 33.434% |
| Prompt only | 24,703 | 7.437x | 36.722% | 7.485% |
| Session + prompt | 26,829 | 6.848x | 0.000% | 0.000% |

Claim supported：prompt tag 是最强的单 system-effect semantic axis。No-semantic 最紧凑，
但会严重混合不同语义来源；full session+prompt 最可审计，但不一定最适合作为默认图。

Boundary：这个实验不证明用户看图能更快；也不证明 tag 对人类充分。它只证明 projection
mechanism 分开了 baseline 会混合的 effect regions。

### R211/R251：混合行为案例与行为相关性

R211 Setup：从 R170/R189 outputs 中抽取 reviewer-facing stack examples、tag distribution
和 baseline-collapse examples。Oracle 是生成的 examples 能展示 baseline bucket 如何跨多个
prompt tags 混合。

R211 Results：`rg` 跨 176 个 prompt tags，`sed` 跨 180 个，`git` 跨 147 个，`cargo` 跨
68 个。`process:git;effect:read;status:ok` 有 116 prompt tags，top-prompt share 24.977%；
`process:cargo;effect:test;status:ok` 有 48 prompt tags，non-top-prompt weight 68.05%。

R251 Setup：扩展 R170 的 183,714 system-effect observations，构造 sanitized
process/effect/status behavior keys，并在每个 session 内随机打乱 prompt tags 1,000 次作为
session-preserving null。

R251 Oracle：真实 prompt tags 的 behavior information gain 应显著高于 session-preserving
shuffle null；privacy scan 必须 0 hits。

R251 Results：263 prompt tags、882 behavior keys。prompt gain beyond session 是 8.419%，
null p95 是 1.903%，p=0.0010。prompt top-behavior purity 是 20.196%，null p95 是
18.367%，p=0.0010。373 behavior-observation weight 被 redacted 成 `process:local-artifact`。

Claim supported：prompt tags 与系统行为有非随机关联。Boundary：低绝对 purity 和 broad
tags 说明它不能替代人工 adequacy。

### R189--R218：长尾标签和 display governance

Setup：这一组实验只读取 R170/R189 等生成 artifacts，不重新读取 raw traces。目标是回答：
如何在保持语义多样性的同时减少无意义长尾碎片，并且不丢 raw drilldown。

R189 Result：raw unique tag strings 1,546 -> canonical unique 1,364；prompt-effect tags
263 -> 216；prompt-row tags 328 -> 279；LLM-event tags 1,423 -> 1,254；system stacks
26,829 -> 26,067；token stacks 8,569 -> 7,661。Boundary：这是 candidate display-noise
reduction，不是 merge correctness。

R190 Result：raw、alias-only、lexical-only、profile-guarded variants 的 prompt-effect
tag counts 分别为 263、241、200、216；LLM-event tag counts 分别为 1,423、1,392、
868、1,254；system-stack counts 分别为 26,829、26,612、25,985、26,067。它还输出
80 over-merge proxy rows 和 80 under-merge proxy rows，但 labels 为空。

R196 Result：治理 action 包含 231 existing canonical merges、114 review-merge rows、
39 regeneration candidates、2 contextual-split candidates、1,241 kept rare distinct tags、
184 kept head tags。Review-required support 是 session 0.938%、prompt 3.258%、LLM-call
1.376%。

R201 Result：七种 threshold/generic-vocabulary variants 下 review-required support 在
1.926%--1.931% 之间；higher-tail-threshold variant 的 head stability 降到 65.217%，
这被记录为 display-policy 风险。

R202 Result：41/41 regenerate/split rows 通过 llama.cpp 得到 grammar-valid one-word
candidate tags；32 个相对 raw tag 改变，9 个不变。Boundary：candidate-only，不证明更好。

R203 Result：生成 41-row promotion-review protocol 和两张 blank reviewer sheets；0 final
labels，canonical map 不更新。

R205 Result：raw unique tags 1,546 -> canonical 1,364，top-20 support coverage 93.683%
-> 95.186%，long-tail support 1.746%，review-required support 1.926%，R203 final labels
为 0，R190 over/under-merge rates 为 n/a。

R209 Result：1,811/1,811 raw rows 都有 active display rows；1,509 active display labels；
63 deterministic alias rows active；168 R189 lexical/profile merges pending；41 regenerated
labels candidate-only；0 hidden `other` rows；drilldown support preserved。

R212 Result：R209 conservative display 与 alias-only 等价，system stacks 26,829 -> 26,612；
profile-guarded-candidate-applied 可到 26,067，但会激活 2.532% unreviewed effect weight，
因此不能默认启用。

R213/R214/R215/R216/R217/R218 Result：raw/display/pending modes 都保持 482,398 support；
display/pending buckets 1,748；candidate overlays 209；review-required rows 323；
production React default display renders 1,748 buckets；synthetic unsafe promotion rows 被拒绝。

Claim supported：长尾治理机制可逆、可消费、不会自动隐藏到 `other`，并且保留 raw
drilldown。Boundary：仍不证明 tag adequacy、merge quality、promotion quality 或用户效用。

### R223/R225：projection tradeoff 与 duration baseline

R223 Setup：读取 R224/R205/R209/R212/R219 artifacts，总结 projection-selection tradeoff。
它不读 raw traces，不调用 LLM。

R223 Result：no-semantic 最紧凑但混合最严重；prompt-only 是最有用单语义轴；full
session+prompt 是 audit view；R209 conservative display 0.0% unreviewed active weight；
profile-guarded view 有 2.532% unreviewed active weight。

R225 Setup：从 R170 timestamps 重构 prompt wall-clock duration baseline，覆盖 prompt-index
system effects，并与 effect-count ranking 比较。

R225 Result：2,858 prompt spans，2,854 nonzero spans，324/325 sessions covered，859.019
total prompt-duration hours，183,714/183,714 system effects covered。Duration/effect top-10
overlap 7/10，top-20 overlap 12/20，Spearman correlation 0.623。

Boundary：R225 是 prompt wall-clock baseline，可能包含 idle/user-wait time；它不是 true
tool/LLM active runtime，也不是 span-duration flamegraph。

## RQ3：exact system-effect lineage 能否成立

### R020a/R110--R113：从 fixture 到 record capture path

R020a 是 AgentSight-shaped fixture checker。它证明 checker API 能把 process/file/network
events join 到 session/tool/prompt ancestry，但只是 fixture evidence。

R110 使用三个真实 AgentSight SQLite DB exports，并由 harness 添加 minimal agent-run envelope。
它覆盖并 join 182/318 raw effects；covered scope 内 182/182 joined，0 orphans，但 136
out-of-scope raw effects 仍 orphan。

R111 把 envelope 逻辑移入 native `collector report export`，同样 join 182/318 raw effects。
R112 在 DB copies 上持久化 backfill，persisted-only export 仍 join 182/318。R113 通过单元
测试验证 `record -- <command>` capture-time session/tool rows 写入 SQLite。R113-live 在五个
只读 Codex tasks 上创建 5/5 sessions/tools，join 508/508 raw effects。

Claim supported：capture-time envelope 和 checker path 可以工作。Boundary：这些 runs 还不
覆盖 fixed broad suite、network target rows 或任意历史。

### R114：固定 Codex command-mode exact lineage suite

Setup：20 个真实 Codex command-mode tasks 在 `agentsight record` 下运行。任务包括 read-only、
edit、test/debug、dependency、failure/retry 和 disposable-workspace write。每个 task 都有
negative controls。

Oracle：每个 target task 要完成；in-scope effects 必须 join；false positives 和 false
negatives 必须为 0；negative controls 必须不被 join；child-depth/path/redaction checks 必须
通过。

Results：20/20 tasks completed；20/20 tasks observed negative controls；1,273/1,273
in-scope effects joined；100.0% scoped precision；100.0% scoped recall；3,170 observed
negative-control effects，0 joined。Raw join 是 22.055%，因为 wrapper/sibling/out-of-scope
effects 正确保持 orphan。

Claim supported：固定 command-mode Codex suite 的 exact lineage supported。

Boundary：不支持 arbitrary agents、arbitrary repositories、target network payload/URL、
Claude-launched target network 或 full-history exact provenance。

### R182/R191/R229/R232/R234：network 和泛化扩展

R182 Setup：启用 record-mode process `--trace-net`，跑两个 loopback-task Codex runs。Result
是 35/35 low-level `codex` process network rows joined，0 network orphans，0/604 negative
controls joined；但 target-specific loopback/expected child-process network rows 是 0/0。
Boundary：network flag path smoke，不能证明 target workload capture。

R191 Setup：固定 Codex HTTP probe task，目标是 Python HTTP process 的 bind/listen/connect。
Result 是 4/4 target `python3` network rows joined，0/310 negative joins，scoped precision/
recall 100%。

R229 Setup：五个 controlled multi-workspace tasks，覆盖 repo-read、edit-test、write、edit。
Result 是 394/394 in-scope effects joined，0 false positives，0 false negatives，0/306
negative joins。

R232 Setup：四个 external fresh-repo normal tasks 加一个 external HTTP probe。Result 是
353/353 normal in-scope effects joined，4/4 target network rows joined，0/480 negative joins。

R234 Setup：一个 Claude command-mode JSON-write task 加两个 Codex HTTP-family probes。
Result 是 269/269 in-scope effects joined，8/8 target network rows joined，0/331 negative
joins。

Claim supported：controlled multi-workspace、external-repo 和 scoped target-network
lineage supported。

Boundary：这些不是任意仓库泛化，也不是所有 agent family 或 raw socket capture。

### R235--R240：困难 network boundary 和 regression guards

R235/R236 探测 raw TCP、multiprocess TCP 和 Claude-launched target-network capture。结果是
部分 negative boundary：Codex single-process TCP 可以产生 target rows 并 join，multiprocess
和 Claude probes 有 0 target rows 或 orphan cases。

R237/R238 加 runtime witness。R238 有 4 tasks，其中 direct-python 两个 ok 且 captured_joined；
Codex HTTP partial，4/5 target rows joined；Claude HTTP partial，2/4 target rows joined；
negative controls observed 186，joined 0。Runtime witness 和 witness-port capture 都通过，
但 boundary_resolved=false。

R240 把两个风险写成 regression checks：command-root fallback 只 join root process 自身，
避免 over-attribution；BPF runtime target-child loopback test 捕获 bind/listen/connect，并
排除 unrelated port。

Claim supported：direct positive controls 和 regression guards supported；agent-launched
Codex/Claude target-network boundary 仍 partial。

### R230--R233：full-history projection lineage audit

R230/R231/R233 只读 generated R170/R231 artifacts。R230 证明 folded rows 带有 semantic、
call 和 effect frames；R231 证明 display projection 与 event-local prompt tags 一致；R233
处理 duplicate prompt indexes。

R233 Result：325 sessions、2,859 prompt rows；12 duplicate prompt-index rows，跨 5 sessions；
legacy field-index drift 可复现，tool 346 weight、LLM 93 events；normalized semantic drift
降为 tool 0、LLM 0；same-tag duplicate row-identity ambiguity 仍有 tool 575 weight、LLM
432 events。

Claim supported：normalized semantic prompt-row lineage supported。Boundary：strict same-tag
prompt-row identity unsupported。

## RQ4：用户效用实验是否完成

当前没有完成。已有内容是 protocol、packet、scorer、collection kit、private return pipeline
和 public summary gate。

### R142/R184/R187/R193--R195/R207：早期 C5/C6 collection readiness

R142 生成 14 个 blinded forensic tasks、5 个 conditions、70 个 participant packets、
answer key 和 scorer。Conditions 包括 trace tree、event-count proxy、flat summary、
nonsemantic stack 和 semantic stack。当前 scored output 是 `participant_results_empty`，
C5 false。

R184 是 weak-accept gate，结果是 `not_weak_accept`。R187 生成五人 pilot launch package。
R193/R194 准备和 preflight R142/R124/R190/R203 human evidence materials。R195 是 ingestion/
scoring pipeline；默认没有 returned CSV，所以 `awaiting_human_inputs`。R207 做 launch
readiness audit 和 return filename mapping。

Claim supported：human study logistics ready/partial。Boundary：没有 outcome evidence。

### R242--R247/R263--R271：return safety、adjudication 和 public aggregate gates

R242 用 synthetic completed returns 测试 R195 contract，并验证 missing/duplicate/empty
negative cases。Synthetic rows 不算 C5/C6 evidence。

R243/R244/R247 生成 static local collection kit、headless Chrome export smoke 和 sendable
offline bundle。它们验证 forms/export/tarball，不产生真实响应。

R263 拒绝 R259 synthetic return markers。R264 是 private return intake preflight：当前 status
`awaiting_private_returns`，C5 rows 0/168，R124/R190/R203 missing，C5/C6/weak-accept false。

R265 用 synthetic disagreement fixtures 验证 adjudication workflow，不算 human evidence。

R266 是 public promotion gate：只允许把 private R195 aggregate 结果安全发布为 summary；
它不能创建 responses 或 labels。

R268 orchestrates private C5 returns through R264/R195/R266。当前 status
`awaiting_private_c5_returns`，private input 不存在，C5 supported false。

R270 orchestrates private C6 label returns through R264/R195/R266。当前 required inputs 0/6，
status `awaiting_private_c6_labels`，C6 adequacy false。

R271 joins R268/R270 public-safe aggregate gates。当前 status
`awaiting_private_c5_and_c6_returns`，human evidence ready for OSDI review false，weak accept
false。

Claim supported：safety and orchestration pipeline exists。Boundary：仍没有 C5/C6 outcome。

### R249/R255/R258/R259：paper-scale collection package

R249 生成 paper-scale C5 package：12 participant packets、168 assignment/response rows，每个
task-condition 有 2--3 replicates，blank template 被 scorer 接收为 empty，C5 false。

R255 把 R249 assignment 接入 R195：R249 blank template with R249 assignment scores through
R195 as empty；same template with old R142 assignment fails。Boundary：scoring path works，
没有 responses。

R258 生成统一 paper-scale C5/C6 human-evidence bundle：43-member tarball，12 C5 participant
packets，2 C6 labeler packets，1,002 required independent C6 label decisions，blank R195
inbox template，return checklist，leak scans pass。Boundary：collection logistics only。

R259 生成 paper-scale static forms：12 participant HTML forms、6 labeler HTML forms、C5
coordinator merge page、168-row synthetic C5 smoke CSV、1,002 C6 blank-label rows，6/6 Chrome
checks pass。Boundary：static collection UX/logistics only。

## RQ5：artifact 和开源工具路径

### R160/R200：AgentFlame bounded and generated-fixture smokes

R160 Setup：8 个 fixed historical Codex session files，LLM-call tags enabled。Clean run
生成 dashboard、folded stacks、SVGs 和 tag cache；76 tag requests 中 60 uncached llama.cpp
calls，耗时 1.64 s。Cached rerun 76/76 cache hits、0 LLM calls、0.11 s。Oracle 包含 artifact
keys、folded totals、redacted previews、path containment、dirty raw-trace-like paths 和
fixed-input equality。

R200 Setup：public-safe generated Codex fixture，不读真实 `.codex`/`.claude` traces。Clean
run 5 llama.cpp tag calls，cached rerun 0 calls with 5/5 hits；expected artifacts exist；
prompt previews redacted；fixture removed。

Claim supported：bounded local artifact path 和 public-safe generated-fixture path。
Boundary：不是 external adoption，也不是 real-history public sanitization。

### R220/R248/R253/R254/R256/R257：agentpprof productized path

R220 Setup：temporary clean clone、public-safe generated Codex fixture、deterministic regex
tagger、no llama.cpp。这个 fixture 是研究实验输入，不是 `main` 分支下的
`agentpprof/` example。Outputs 包括 `tasks.pb.gz`、`tools.folded`、`tokens.json`、
`files.folded`、`network.folded`、`tools.svg`。Oracle 是 `go tool pprof -top` 读回
6/6 task samples，expected stack checks pass，output containment 和 privacy scan pass。

R248 Setup：`cargo install --path agentpprof --locked --force`，explicit `--session-file`，
`--tagger regex`，`--no-cache`，public-safe generated fixture。Oracle 是 installed CLI
help、pprof/folded/JSON/SVG outputs 和 pprof readback。

R253 Setup：`cargo install --git` against `research/semantic-flamegraph-artifacts` branch。
Result 与 R248 同类，no private-history discovery，no live tagger calls。

R254 Setup：`cargo install --git --rev` against exact pushed revision，去掉 mutable branch
caveat。

R256 Setup：`cargo package --list` and `cargo package` for `agentpprof` 0.2.0。Result 是
35,438-byte crate archive，8 intended files，archive/list equality，forbidden paths absent，
registry `agent-session v0.3.3` observed。

R257 是 post-package review gate，确认 wording 和 scope。

Claim supported：local clean clone、installed CLI、GitHub branch install、pinned revision
install、pprof readback、crate-package dry-run。Boundary：仍不是 crates.io publish/readback、
external-machine install 或社区反馈。

## RQ6：论文和 claim hygiene

R245/R246/R250/R260/R261/R262/R267/R269/R271 都是 hygiene 或 review gates。
它们很重要，但不能提升 C5/C6。

R245 通过 9/9 hard evidence checks 和 13/13 wording checks，forbidden strong-claim hits 0。
R246 记录 R170 `repo_dirty=true`，并为 R224 加 `checker_id=R131` metadata。R250 修正
participant packets 和 real participants 的措辞。R260 检查 R258/R259 在 paper/docs 中只被
称为 collection logistics。R261/R262 是 layout/compaction gates：最终 `main.tex` 编译到
6 pages、495 source lines、0 oversized float warnings、0 undefined references。R267/R269
是 independent review hygiene，仍说 not weak accept。R271 是 human-evidence weak-accept
join gate，当前 still false。

## 总实验索引

下表按功能列出主要实验。`Claim boundary` 一栏是写论文时最重要的部分。

| Runs | Setup summary | Main oracle | Claim boundary |
| --- | --- | --- | --- |
| R100/R170 | Full local Codex/Claude history scan with llama.cpp tags | folded totals match, invalid tags 0 | C1/C2/C3 mechanism; not C5/C6 |
| R101 | Rust test/clippy after implementation fixes | tests/clippy pass | implementation hygiene only |
| R102/R103 | Figure generation and paper compile | figures/PDF build | paper artifact hygiene |
| R060 | Legacy Python prototype | pipeline exits | superseded; not headline evidence |
| R020a | Exact-lineage fixture checker | fixture joins | interface smoke only |
| R110--R113 | AgentSight DB/export/backfill/record envelope path | covered effects join | partial C4 path setup |
| R113-live/R114 | Real Codex command-mode record suites | scoped precision/recall and negative controls | fixed command-mode C4 supported |
| R182/R191 | Network lineage smoke and target HTTP probe | target rows joined, negatives unjoined | R182 partial; R191 scoped target network supported |
| R229/R232/R234 | Controlled multi-workspace, external repos, agent-family expansion | in-scope and target rows joined | scoped generalization, not arbitrary |
| R235--R240 | Raw/multiprocess/Claude network boundary and guards | witness/capture/regression checks | direct controls pass, agent-launched boundary partial |
| R122--R124/R180 | Redacted tag packet and model stability | grammar validity/stability, label protocol | syntax supported, adequacy unsupported |
| R131/R224/R223/R225 | Projection ablation and duration baseline | weight preservation, mixed-weight metrics | projection tradeoff supported, not utility |
| R189--R218 | Canonical tags, long-tail governance, renderer/display gates | raw preserved, drilldown, pending candidates | reversible display governance, not tag correctness |
| R211/R251 | Stack examples and behavior association | baseline-collapse examples, shuffle null | behavior association proxy, not adequacy |
| R142/R187/R193--R195/R207 | User-task and label collection setup | packets/scorers/templates exist | collection readiness only |
| R242--R247/R263--R271 | Return safety, synthetic contract, public/private gates | unsafe inputs rejected, gates stay false | orchestration only; no outcome evidence |
| R249/R255/R258/R259 | Paper-scale C5/C6 collection package/forms | 12 C5 packets, 1,002 C6 decisions, Chrome/export smoke | logistics only |
| R160/R200 | Bounded/public AgentFlame artifact smokes | fixed-input caching, no private trace reads | local artifact path partial |
| R220/R248/R253/R254/R256/R257 | agentpprof clean clone/install/pinned/package smokes | pprof readback, package boundary | C7 partial; no adoption |
| R245/R246/R250/R260--R262/R267/R269 | Claim and paper hygiene | wording checks, compile/layout, review gates | prevents overclaim; adds no data |

## 能写进论文的结论

可以写：

- 在本机 325 个真实 Codex/Claude sessions 上，语义系统栈可生成，并且 0 个最终 tag
  失败。
- R170/R224 说明 nonsemantic 和 flat summaries 会把 90% 以上 system-effect weight 混合到
  多语义 buckets 中，而 prompt-only projection 能显著降低这种混合。
- R251 说明 prompt tags 对 process/effect/status behavior 有 session-beyond association。
- R189--R218 说明 tag compaction 必须是可逆 display overlay，而不是 raw-label rewrite。
- R114/R191/R229/R232/R234 支持固定/受控范围内 exact lineage 和 zero negative joins。
- R160/R200/R220/R248/R253/R254/R256 支持本机 artifact、public-safe generated-fixture
  smoke、install/readback 和 crate-package dry-run 路径。

不能写：

- 不能写 developer 一定 debug 更快；C5 还没有真实参与者响应。
- 不能写 one-word tags 已经语义正确；C6 还没有人工 adequacy labels。
- 不能写 arbitrary agents/arbitrary repositories/arbitrary network workloads 都有完整 exact
  provenance。
- 不能写 agentpprof 已经在社区开发者中验证；当前只是 local/pinned/package smokes。
- 不能写 span-duration flamegraph 已被完整比较；R225 只是 prompt wall-clock baseline。
- 不能写长尾 compaction 自动正确；unreviewed profile merges 和 regenerated labels 必须 pending。

## 下一步实验

要让论文进入 OSDI/SOSP weak-accept 级别，最小高价值下一步是：

1. 跑真实 C5 developer task study。使用 R249/R258/R259 的 paper-scale materials，收集
   12 个参与者的 168 行 response CSV，通过 R268/R195/R266 生成 public-safe aggregate。
   Metrics 应包括 answer accuracy、time、confidence、false positive、repeated-effect recall。
2. 跑真实 C6 human label study。收集 R124 tag adequacy、R190 merge-risk、R203 promotion
   labels，共 1,002 个 independent decisions，加必要 adjudication，通过 R270/R195/R266 输出
   public-safe aggregate。
3. 扩展 C4 network boundary。重点是 Codex/Claude-launched target-network rows 的 orphan/
   missing-action cases，而不是再重复 direct Python positive controls。
4. 做 external-machine artifact run。验证 `agentpprof` 从 clean install 到 pprof/flamegraph
   output 的路径，在另一台机器和真实但可公开 sanitization policy 下可复现。
5. 明确默认产品体验。默认输出应少而有用：pprof `.pb.gz`、folded stack、SVG 和 summary
   JSON；高级 raw drilldown、pending display map 和 tag cache 可按 flag 输出。

## 结论

AgentFlame/agentpprof 的研究价值不在于“第一次画 agent flamegraph”。已有工具和论文式
系统已经能把 agent spans 画成 duration flamegraph。这里真正的贡献是一个 semantic
system-effect projection：把 session/prompt/LLM-call 的短语义帧与 tool/process/file/network
系统效果连接，再以 folded stacks 聚合。R170/R224/R251 说明这个 projection 能揭示传统
summary 混合掉的结构；R114/R191/R229/R232/R234 说明 scoped exact lineage 可以做到严格
归因；R189--R218 说明标签长尾治理必须可逆、pending、可 drilldown；R160/R200/R220/R248/
R253/R254/R256 说明产品化 artifact 路径正在收敛。

当前最诚实的论文定位是：一个机制扎实、实验边界清楚、artifact path 可检查的 agent
semantic system-effect profiler。它还不是 complete OSDI paper，因为 C5 用户效用和 C6
人工标签 adequacy 仍缺真实数据。
