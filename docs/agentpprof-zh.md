# agentpprof: 用 operation stack 剖析 AI agent 轨迹

月底账单显示 agent 花了 $3000。哪些类型的工作消耗了这些预算？代码审查占多少、debug 占多少、文档生成占多少？这个问题看似简单，但在缺少任务特定的 operation fields 和 profile query 时，现有 agent 可观测性工具通常很难直接回答。

`agentpprof` 正是为回答这类问题而设计的分析工具。它读取本地 agent 的 trace 历史或外部已标注 agent 轨迹，把 prompt、tool call、GUI action、process/syscall、plan/subagent 等事件统一成 `operation`，再按用户指定的 `operation stack` 递归折叠。输出可以是 flamegraph，也可以是 JSON ranking、stack tree、boundary/actionability report 或 profile-spec replay 结果；flamegraph 只是序列化形式之一，不是核心抽象。当前支持 Codex 和 Claude Code 的本地 trace 文件，也支持外部 operation JSONL 和标准 trace exchange。

## 现有工具的局限

LangSmith、Langfuse、Phoenix 这类 LLM 可观测性平台能展示 trace、span、token、latency、dataset 和 evaluation 信息。问题不在于它们不能展示 trace，而在于如果只使用默认的 trace/span/timeline 维度，80000 次调用仍然需要分析者自己定义任务字段、聚合规则和 profile query。你可以逐条检查「这次调用花了 500 tokens」，但很难直接得到「审查类任务总共花了多少」。这些工具的设计目标更偏向单次 trace 调试：timeline view 帮你定位 14:03 那个失败的 span，span tree 展示调用层级，waterfall chart 显示并行度。它们在回答「发生了什么」这个问题上表现出色，但对于「预算花在哪类工作上」这种聚合问题，逐条检查 80000 个 span 显然行不通。

Datadog 和 Laminar 开始尝试语义分类。Datadog 用 topic clustering 对用户消息做聚类，Laminar 用 Signals 从 trace 中提取结构化事件。这是正确的方向，但这类聚类刻画的是用户输入的分布，并不产生「宽度代表预算占比」的聚合视图。你能看到「30% 的用户在问代码问题」，但看不到「代码审查消耗了 40% 的 token 预算」。

CPU profiler 早就解决了类似的聚合问题。Flamegraph 把百万次函数调用压缩成一张图，宽度代表时间占比。调用栈表示事件所属的上下文，对同一函数的重复调用会合并成更宽的条带。这之所以有效，是因为函数名是**确定性的**：相同的代码路径产生相同的调用栈，相同的调用栈可以直接合并。

Agent trace 打破了这个假设。Prompt 是自然语言：非确定性的、长度可变的、多语言的、往往还是对话式的。「Fix the bug」和「修一下这个 error」表达相同的意图，但字符串完全不同。如果直接用原始 prompt 文本作为 frame 标签，flamegraph 会宽得无法阅读，每个 prompt 都是独立的一条，失去了聚合的意义。而且原始 prompt 往往包含敏感信息，也不适合分享。

## Operation-stack profiler

`agentpprof` 通过**字段派生和 stack 查询**来恢复聚合能力：将自由格式 prompt、工具动作、进程事件和 benchmark 标签归一成稳定的 operation fields，如 `task=debug`、`phase=inspect`、`op=tool`、`status=failure` 或 `human_group=...`。这些字段可以来自 regex/LLM tagging、deterministic mapping、profile spec 或已有数据集标签。随后用户用 `--stack` 选择递归折叠深度；相同 stack 合并成更宽的条带或更高的 ranked group。

Operation stack 的价值不只是聚合，还在于**用可配置栈表达归因关联**。传统 CPU flamegraph 的堆栈是函数调用链：`main → parse → tokenize`，表示 tokenize 是被 parse 调用的，parse 是被 main 调用的。Agent 的 operation stack 是分析者选择的归因链：`task:debug → phase:execute → op:tool → tool:bash → status:error`。同一批 operations 可以换成 `dataset,task,human_group,action` 或 `task,phase,op,step_correct`，用不同深度定位同一问题。

| | 传统 CPU Flamegraph | Agent operation stack |
| --- | --- | --- |
| **堆栈含义** | 函数调用链 | 用户选择的 operation-field 归因链 |
| **聚合方式** | 相同函数名合并 | 相同 operation stack 合并 |
| **宽度含义** | CPU 时间占比 | token / 时间 / 操作次数占比 |
| **回答问题** | 程序在哪里花 CPU | agent 的失败、成本、质量和边界问题集中在哪里 |

这种可配置的归因投影让你能从任意一层回溯或下钻：从某个文件被修改，定位到同一投影下关联的工具、模型调用上下文和用户任务字段；或者从某类 prompt 出发，看它关联了什么 LLM 调用、什么工具执行、什么系统效果。

在这个模型里，视图不是固定的图，而是对同一批数据的查询：选哪些事件、栈怎么排、宽度算什么，换一个问题只需换一组投影。`agentpprof` 内置了几个这样的视图，每种回答不同的问题：

| 视图 | 宽度含义 | 主要回答的问题 |
| --- | ---: | --- |
| `operations` | operation 次数 | 本地或外部轨迹里哪些递归 operation stack 占比最高？ |
| `tokens` | 报告的 token 数量（input/output/cache） | 哪些 prompt 消耗了最多的模型预算？ |
| `time` | 持续时间（秒） | 每个 prompt/活动花了多长时间？ |
| `files` | 文件/路径操作次数 | 哪些 prompt 触及了仓库的哪些部分？ |
| `network` | 网络/域名请求次数 | 哪些 prompt 联系了哪些域名？ |

用 `operations` 分析通用本地或外部轨迹，用 `tokens` 定位成本热点，再用 `time` 追踪 wall-clock 时间去向，`files` 和 `network` 则适合安全审计场景。

## Flamegraph 示例

以下示例来自 AgentSight 项目自身的开发 trace（Claude Code），展示了每个视图各自能回答什么问题。

### Tokens 视图

**问题：** 哪些活动消耗了最多的模型预算？

![Tokens flamegraph](https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/agentsight-tokens.svg)

Token 分布显示代码审查（`prompt:review`）主导了模型预算，其次是 git 操作（`prompt:git`）、代码工作（`prompt:code`）、编辑（`prompt:edit`）和调试（`prompt:debug`）。通过堆栈可以追溯每类 prompt 触发了哪些 LLM 调用：`call:llm/usage` 表示 token 统计事件，`call:llm/code` 和 `call:llm/test` 表示代码相关响应，`call:llm/tool` 表示工具调用，`call:llm/edit` 表示修改响应。

### Time 视图

**问题：** Wall-clock 时间花在了哪里？

![Time flamegraph](https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/agentsight-time.svg)

Wall-clock 时间分布与 token 消耗相似：review（`prompt:review`）领先，其次是 git、edit、docs 和 code 类 prompt。continuation prompt（`prompt:continue`）频繁出现，说明复杂任务往往需要多轮后续交流才能完成。`prompt:inspect` 捕获了迭代开发中常见的「看一下」类请求。

### Files 视图

**问题：** 代码库的哪些部分被触及了，以什么方式？

![Files flamegraph](https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/agentsight-files.svg)

文件访问模式显示 `collector/src/`（Rust 代码库）和 `collector/Cargo.toml` 活动频繁，与开发工作一致。外部路径（`external/tmp`、`external/home`、`external/codex`）也频繁出现，反映了工具调用触及临时文件、home 目录配置和 Codex session 数据。Flamegraph 区分读和写两类效果，可以看出在项目路径和外部路径上，检查和修改各占多少。

### Network 视图

**问题：** 联系了哪些外部服务？

![Network flamegraph](https://github.com/eunomia-bpf/agentsight/raw/master/docs/flamegraph-example/agentsight-network.svg)

网络活动比文件操作少得多，说明大部分开发工作在本地完成。被联系的域名包括 `anthropic.com`（模型推理）、`crates.io`（Rust 依赖）、`github.com`（版本控制）以及各种 localhost 端口（本地开发服务器）。上层 frame 展示了发起请求的进程链，网络活动因此可以归因到具体的 agent 操作。

生成脚本及标签规则见 `docs/flamegraph-example/agentsight.sh`。

## 工作原理

`agentpprof` 的核心是两个抽象：**操作**（operation，历史中一次可计量的活动）和**操作栈**（operation stack，表达这次活动归因上下文的帧序列）。整个工具分三段围绕它们工作：解析段把本地 trace 还原成操作集合，字段派生段用 tagging 和 mapping 往操作上写稳定字段，投影段把带字段的操作折叠成操作栈并渲染。这三段是实现流程，不是三个 profiler 抽象。

### 解析层：从 trace 到操作

`agent-session` 解析器读取 Codex/Claude 的 JSONL 历史，恢复出 prompt、LLM 调用、工具调用以及它们触发的文件和网络效果。每个这样的活动就是一个操作，带着自己的属性（时间戳、token 数、路径、域名、状态等），构成后续两层共享的操作表。解析同时保留序列结构：每个操作都记着自己落在哪条 prompt 的跨度内。

### 字段派生段：从原始字段到可折叠标签

解析和投影都是常规工程，真正的难点是把自由格式字段变成稳定、可复现的 operation fields。同一个项目里的 prompt 可能混合多种语言（「fix the 编译 error」），长度从单个字符（「嗯」、「ok」）到长段落不等，还有很多孤立看来没有意义的片段（「继续」、「好」、系统生成的上下文恢复消息）。`agentpprof` 的 tagger 和 mapping 后端只负责写入字段，例如 `task=debug` 或 `phase=inspect`；它们不是新的 profiler object，也不自动声称发现了真实 intent boundary。为了派生这些字段，`agentpprof` 提供了一个可插拔的标签器框架，支持多种后端：

| 后端 | 方法 | 适用场景 |
| --- | --- | --- |
| Regex + Agent 迭代 | 正则匹配，由 AI agent 观察样本并迭代优化规则 | 生产环境、CI、可重复分析 |
| LLM 标签器 | 本地 LLM 推理（llama.cpp） | 复杂 prompt、初始规则发现 |
| Python 聚类 | TF-IDF + K-Means 无监督聚类 | 探索性分析、发现自然分组 |

#### Regex 标签器与 Agent 迭代工作流

Regex 标签器是生产环境的默认选择，但它的使用方式和传统正则表达式不同：**你不需要手写所有规则**，而是让 AI agent 观察实际的 prompt 样本，不断迭代规则，直到 unmatched 率降到 5% 以下。

AgentSight 提供了 `agentpprof-flamegraph` skill，指导 agent 完成这个迭代过程：

1. 运行 `agentpprof`，观察 unmatched 率和样本 prompt
2. 根据样本提出新的 `--tag-rule` 规则
3. 重新运行，测量覆盖率
4. 重复直到 unmatched < 5%、分布合理（10-20 个类别，无单一类别 > 50%）

这个迭代过程通常需要 5-10 轮，每轮 1-2 分钟。最终产出的规则集是确定性的、可重复的，适合提交到版本控制并在 CI 中使用。

默认不包含内置规则，所有 prompt 会被标记为 `unmatched`。这是有意的设计选择：通用规则很难匹配你项目的实际 prompt 分布，盲目应用反而会产生误导性的聚合结果。

规则格式是 `KIND:TAG=REGEX`：

```bash
agentpprof -o tokens.svg \
  --tagger regex \
  --tag-rule prompt:review='(?i)review|diff|regression' \
  --tag-rule prompt:test='(?i)cargo test|pytest|unit test' \
  --tag-rule prompt:debug='(?i)fix|error|bug|broken'
```

`KIND` 可以是 `prompt`、`llm` 或 `all`。`TAG` 必须是 3-12 个字母的小写英文单词。规则按命令行顺序求值，第一个匹配生效。

快速测试时可以用 `--preset` 启用内置的演示规则：

```bash
agentpprof -o tokens.svg --tagger regex --preset
```

#### LLM 标签器

对于复杂 prompt 或初始规则发现，可以用本地 LLM 生成标签。运行一个 llama.cpp 兼容的服务器：

```bash
llama-server -m /path/to/model.gguf --port 8080
agentpprof -o tokens.svg --tagger llm --llama-url http://127.0.0.1:8080
```

LLM 标签默认缓存在 `$XDG_CACHE_HOME/agentpprof/tags.json`。LLM 标签器的输出可以作为编写 regex 规则的参考：观察 LLM 产生了哪些类别，然后为每个类别写一条 regex 规则。它是字段派生辅助，不是自动边界 detector。

#### Python 聚类后端（实验性）

对于探索性分析，可以用 Python 聚类后端发现 prompt 的自然分组。这个后端使用 TF-IDF 向量化和 K-Means 聚类，无需预定义规则：

```bash
# 导出 prompt
agentpprof --project-root . --format json -o prompts.json

# 聚类并生成标签缓存
python agentpprof/backend/python/cluster_tagger.py \
  --input prompts.json --output tags.json --show-info

# 使用标签缓存
agentpprof --project-root . --tag-cache tags.json -o flamegraph.svg
```

聚类后端会自动选择最优的聚类数（5-25），并根据每个聚类的关键词生成标签名。这对于理解「我的 prompt 分布里有哪些候选字段」很有用，可以作为编写 regex 规则的起点。聚类结果应当通过规则、profile spec 或数据集已有标签固化后再用于可复现实验。

### 投影层：从操作到 folded stacks

前两个流程段的产出可以用一个小的形式模型精确刻画，投影段就是对这个模型的查询求值。开头说的两个核心抽象在这里给出正式定义。

**定义 1（operation，操作）。** 一次 agent 执行历史被解析为操作集合 O。一个操作 o ∈ O 是历史中一次可计量的活动：一条用户 prompt、一次 LLM 调用，或一次工具触发的文件/网络效果。每个操作携带属性元组 attr(o) = (project, agent, session, prompt, kind, model, path, domain, status, …) 以及若干可加度量，如 token 数、持续时间、发生次数。解析段产出 O，字段派生段只为其中的属性提供稳定取值。

操作的粒度在解析时就固定了，与视图无关。视图改变的是计量方式：一个操作可以展开成多个样本，tokens 视图把一次 LLM 调用按 input/output/cache 展开成三个样本，files 视图把一次工具调用按触碰的路径逐一展开。样本是视图相关的，操作不是。

**定义 2（operation stack，操作栈）。** 栈化函数 σ 把操作映射为有序帧序列 σ(o) = [f₁; f₂; …; f_k]。每一帧都是某种 operation 属性或 operation stack frame：project、agent、session、prompt、tool call、process、path、domain 都不是独立抽象，只是 operation 在不同粒度上的形态。与 CPU 调用栈不同，操作栈表达的是**归因链**而非控制流：每一帧回答「这个活动发生在什么上下文里」。

层级从哪里来？agent 历史本身是一条线性事件序列，没有现成的树。当前实现把 operation field mapping、operation predicate 和 operation stack rule 作为栈构造规则：`--op-map FIELD:LABEL=REGEX` 先把 task、subtask、phase 等派生成普通 operation 字段，`--where FIELD=REGEX` 或 `--where FIELD!=REGEX` 再选择参与本次查询的 operation 子集，`--stack` 最后选择栈中要出现的 frame，`--stack-rule FRAME:LABEL=REGEX` 只在构造某个 frame 时做局部覆盖。默认 `phase` 只是一个内置 frame，它根据 LLM 标签和 tool effect/category 给单个 prompt 内的事件生成阶段；用户也可以去掉 prompt、增加 `task,subtask,phase`，让几个 prompt 合并到同一个 intent/task 下。字段派生在前，按 `--stack` 折叠与聚合在后。

`--op-map` 和 `--stack-rule` 匹配的是由 operation 字段组成的 `key=value` 字符串，可用字段包括 `prompt`、`prompt_preview`、`op`、`tool`、`category`、`command`、`cmd`、`process`、`effect`、`status`、`path`、`domain`、`llm`、`llm_preview`、`model` 和 `token`。`--op-map` 先执行，并按顺序匹配已经派生出来的字段；同一个字段第一条匹配规则生效。`--where` 在 mapping 之后、stack 构造之前执行，多条 predicate 取 AND。默认栈使用 `phase`，但用户可以增删任意 frame。

在这两个抽象之上，视图只是一次查询求值，不是新的核心抽象。一次查询由三部分组成：谓词 φ 选择参与统计的 operation 子集，σ 决定 operation stack，权重函数 w 把每个 operation 映射为非负数。求值结果是 folded stacks，即按栈分组、权重求和的多重集：

```text
eval(V, O) = { (s, w_s) : w_s = Σ w(o), 对所有 o ∈ O 满足 φ(o) 且 σ(o) = s }
```

这个模型的直接推论是：栈不是预定义的固定结构，视图也不是预先画好的图，两者都由查询决定，换一个分析问题只需换一组 (φ, σ, w)。栈里的语义帧也不是内置词表，而是来自字段派生段中你为项目定义的 tagging、mapping 或数据集标签规则。内置视图就是几组预定义查询：

| 视图 | φ（选择哪些操作） | σ（栈结构） | w（权重） |
| --- | --- | --- | --- |
| `operations` | 全部 operation | 默认 project; agent; dataset; task; session; prompt; phase; op; tool; action; status，可用 `--stack` 覆盖 | operation 次数 |
| `tokens` | LLM 调用 | 默认 project; agent; session; prompt; phase; op; call; model; token，可用 `--stack` 覆盖 | token 数（input/output/cache 各为一个样本） |
| `time` | 全部带时间戳的操作 | 默认 project; agent; session; prompt; phase; op; ⟨子操作帧⟩，可用 `--stack` 覆盖 | 到下一事件的间隔秒数 |
| `files` | 有路径效果的工具操作 | 默认 project; agent; session; prompt; phase; op; tool; ⟨process⟩; path; effect; status，可用 `--stack` 覆盖 | 事件次数 |
| `network` | 有网络效果的工具操作 | 默认 project; agent; session; prompt; phase; op; tool; ⟨process⟩; domain; status，可用 `--stack` 覆盖 | 事件次数 |

这些视图共享同一操作集合 O 和同一低层语义前缀，只在高层帧和权重函数上不同，因此跨视图对照是良定义的：`tokens` 视图里的 `prompt:review` 与 `files` 视图里的 `prompt:review` 指同一批操作在不同 (σ, w) 下的投影。flamegraph、pprof、folded 文本和 JSON 只是同一求值结果的不同序列化，各视图的具体栈示例见后文「调用栈模型」。

## 安装

发布后可通过 `cargo install agentpprof` 安装，也可以从 AgentSight GitHub release artifacts 下载预编译的二进制文件。发布流水线从同一个 release tag 构建并测试 `agentsight` 和 `agentpprof`。

从源码构建：

```bash
cargo run --manifest-path agentpprof/Cargo.toml -- --version
cargo run --manifest-path agentpprof/Cargo.toml -- -o agent.pb.gz
```

## 第一个 profile

为当前仓库生成 token profile：

```bash
agentpprof --project-root . --view tokens -o tokens.pb.gz
```

使用标准 Go 工具打开 pprof profile：

```bash
go tool pprof -top tokens.pb.gz
go tool pprof -http=:0 tokens.pb.gz
```

生成可在浏览器打开的 flamegraph：

```bash
agentpprof --project-root . --view tokens -o tokens.svg
```

未指定 `--format` 时，扩展名决定输出格式：

```bash
agentpprof -o tokens.pb.gz  --view tokens   # pprof protobuf, gzip 压缩
agentpprof -o time.folded   --view time     # folded stack 文本
agentpprof -o files.svg     --view files    # 独立 SVG flamegraph
agentpprof -o network.json  --view network  # 脱敏后的 JSON 摘要和调用栈
```

## 读取什么数据？

`agentpprof` 读取 agent 原生的本地 trace 历史。目前支持通过 `agent-session` crate 解析的 Codex 和 Claude Code JSONL 文件。它不加载 eBPF 探针、不需要 root 权限、不录制实时进程。它是 AgentSight 的离线分析端：用 `agentsight` 观察实时系统行为，用 `agentpprof` 聚合已记录的 agent trace。

默认情况下，它扫描与 `--project-root` 匹配的近期本地 trace：

```bash
agentpprof --project-root /path/to/repo --view tokens -o tokens.svg
```

对于可重复的分析，传入明确的 trace 文件：

```bash
agentpprof \
  --project-root /path/to/repo \
  --session-file ~/.codex/sessions/.../session.jsonl \
  --session-file ~/.claude/projects/.../session.jsonl \
  --view tokens \
  -o tokens.folded
```

也可以先把本地原生 session 导出成可移植的 agent-session trace，再在没有原始
Codex/Claude 文件的环境里导入：

```bash
agentpprof \
  --session-file ~/.codex/sessions/.../session.jsonl \
  --export-trace agent-session-trace.json

agentpprof \
  --trace-file agent-session-trace.json \
  --view operations \
  --stack 'project,agent,op,phase,tool,status' \
  -o trace.folded
```

Trace schema 是 `agentsight.agent-session.trace.v1`。它只是解析后 session 的交换格式，
不是 profiler 的第三个抽象。`--export-trace` 支持 `--agent`、`--session-id`
这类原始来源筛选；`--session-tag` 和 `--prompt-tag` 是 profiler 后处理注解，
不能混在 trace export 中。导出的 trace 会归一化 filesystem 和 tool-command 字段：
session log 路径会变成稳定的 `trace/<agent>/<hash>.jsonl`，`cwd` 会归一成
`repo`，文件路径会合并成 path group，tool command 只保留抽取出的命令名而不是
完整 shell 文本。prompt 和 LLM preview 仍是解析后的 session 摘要；共享敏感内容前需要在上游省略或脱敏。若要让同一批数据走外部数据集路径，可以转成
operation JSONL：

```bash
python3 script/agent_trace_to_operations.py \
  --trace-file agent-session-trace.json \
  --project-name my-project \
  --out operations.jsonl

agentpprof --operation-file operations.jsonl --view operations -o operations.folded
```

转换脚本若没有产生任何 operation 会非零退出；有事件级 prompt/tool/LLM 行时优先使用
事件级数据，否则回退到 session 级 tool/token 摘要。

有用的筛选器：

```bash
agentpprof -o tokens.svg --agent codex
agentpprof -o tokens.svg --session-id 019ec5
agentpprof -o tokens.svg --session-tag debug
agentpprof -o tokens.svg --prompt-tag review
```

## 调用栈模型

语义 flamegraph 的调用栈是一种投影而非字面意义的函数调用栈：`--view` 决定采样哪些 operation 及其权重，`--op-map` 或 `--op-map-file` 在栈化前派生 operation 字段，`--stack` 决定 operation stack 的 frame 序列，frame 可以直接来自 operation 字段，也可以由 `--stack-rule` 局部生成，用来递归折叠 intent/task/subtask/phase 等层级。

对于第三方 trace 或 benchmark 数据集，`--operation-file` 可以直接读取规范化后的 operation JSONL。每一行是一条 operation，包含数值 `value` 和 `fields` 对象。它会跳过 Codex/Claude session discovery，但复用同一条 operation stack 投影路径：

```bash
agentpprof -o external.folded --view operations \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --stack 'project,agent,dataset,task,session,phase,op,action,target,status'
```

例如，下面的 stack 不保留 prompt，而是把多个 prompt/tool event 折到 task/phase 两层：

```bash
agentpprof -o files.folded --view files \
  --stack 'project,agent,task,phase,op,tool,path,status' \
  --op-map-file project-op-map.txt \
  --op-map 'task:verify=(effect=test|cmd=cargo|path=tests)' \
  --op-map 'task:explore=(effect=read|tool=read)' \
  --op-map 'phase:inspect=(effect=read)' \
  --op-map 'phase:execute=(effect=test)' \
  --where 'task=verify' \
  --stack-rule 'path:tests=(path=tests)'
```

`--op-map-file` 读取同样的 `FIELD:LABEL=REGEX` 规则文件，每行一条，空行和 `#` 注释会被忽略。命令行上的 `--op-map` 会排在文件规则前面，因此可以覆盖共享规则文件里的默认映射。`--where` 可用来把同一份 operation JSONL 切成不同查询视图，例如先派生 `task_family:looping`，再只折叠 `task_family=looping` 的操作。对于已有标注的外部轨迹，可以先用 `script/operation_map_infer.py` 从 `dataset`、`tool`、`task` 和 `action` 等字段生成规则文件：

```bash
python3 script/operation_map_infer.py \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --out op-map.txt \
  --json-out op-map.json

agentpprof -o external.folded --view operations \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-50.jsonl \
  --op-map-file op-map.txt \
  --stack 'project,dataset,task,phase,op,tool,action,status'
```

为了让外部标注轨迹实验可重复，可以把同一组参数写进 JSON profile spec：

```json
{
  "output": "agentnet-diagnostic.folded",
  "format": "folded",
  "view": "operations",
  "project_name": "external-agent-traces",
  "operation_files": ["../external-agent-trace-agentnet-r291/agentnet-operations.jsonl"],
  "op_map_files": ["../external-agent-trace-agentnet-r291/agentnet-op-map.txt"],
  "where_rules": ["dataset=agentnet"],
  "rank_rules": ["step-risk:2=status:failure|repeat_signal:loop-like"],
  "rank_op_rules": ["failure-density:2=status=failure"],
  "rank_mode": "rule-score",
  "stack": "project,dataset,benchmark,environment,task,phase,op,tool,action,status,step_correct,step_redundant,repeat_signal"
}
```

运行：

```bash
agentpprof --profile-spec docs/visexp/out/profile-spec-r293/agentnet-diagnostic-spec.json
```

Spec 内的路径相对 spec 文件所在目录解析。`-o`、`--view`、`--format`、`--stack`
这类命令行标量参数会覆盖 spec 默认值；命令行 `--op-map`、`--op-map-file` 会排在
spec 规则之前求值；命令行 `--where` 存在时会替换 spec 里的
`where_rules`，否则使用 spec predicate。命令行 `--rank-rule` 和
`--rank-op-rule` 会排在 spec `rank_rules` 和 `rank_op_rules` 之前求值。
两者都使用 `LABEL:WEIGHT=REGEX`：`rank_rules` 匹配 folded stack 文本，
`rank_op_rules` 匹配 mapping/filtering 之后的单个 operation `field=value`
token，并把命中的 operation weight 聚合成 stack 内部的 density score。
它们只影响 JSON 里的 operation-stack group 排序，不影响 pprof、folded 或
SVG 输出。默认 `rank_mode` 是 `width-boost`，即宽度仍是主要信号；
`rule-score` 会先按 visible rule 命中分数排序，再用宽度打破并列。因此
profile spec 只是 operation、mapping、predicate、rank policy 和 operation
stack 的复现实验配置，不是第三个 profiler 抽象。

`tokens` 视图以模型预算作为宽度：

```text
project:agentsight;agent:claude;session:profile;prompt:debug;phase:debug;op:llm;call:llm/debug;model:claude-opus-4-6;token:input 4200
project:agentsight;agent:claude;session:profile;prompt:debug;phase:debug;op:llm;call:llm/debug;model:claude-opus-4-6;token:output 980
project:agentsight;agent:claude;session:profile;prompt:debug;phase:debug;op:llm;call:llm/debug;model:claude-opus-4-6;token:cache 150000
```

`time` 视图以 wall-clock 持续时间（秒）作为宽度：

```text
project:agentsight;agent:claude;session:profile;prompt:debug;phase:debug;op:llm 45
project:agentsight;agent:claude;session:profile;prompt:debug;phase:test;op:tool 12
project:agentsight;agent:claude;session:profile;prompt:debug;op:prompt 2
```

`files` 视图以仓库区域作为主分支：

```text
project:agentsight;agent:codex;session:release;prompt:docs;phase:write;op:tool;tool:apply_patch;path:docs/flamegraph;effect:write;status:ok 1
```

`network` 视图以域名为中心：

```text
project:agentsight;agent:codex;session:release;prompt:publish;phase:network;op:tool;tool:exec_command;process:cargo;domain:crates.io;status:ok 1
```

## 隐私与脱敏

本地 agent 历史可能包含 prompt、工具输出、路径、命令、仓库名称和模型响应。`agentpprof` 默认采取保守策略：

- SVG、pprof 和 folded 输出只包含调用栈标签和权重，不包含原始 prompt 或模型响应。
- JSON 输出会脱敏预览内容，除非设置了 `--include-previews`。
- 所选项目根目录之外的绝对路径会被归类到稳定的桶中，如 `external/home`、`external/tmp`、`external/codex` 和 `external/claude`。
- 看起来私密的域名会被折叠，而不是暴露用户特定的主机名。

需要可重复性时使用明确的 `--session-file` 输入。仅在私有调试或已脱敏的 trace 中使用 `--include-previews`。

## 配合 AgentSight 使用

`agentsight` 提供实时可见性（进程树、文件效果、网络目的地），`agentpprof` 提供聚合分析（成本热点、时间分布）。典型工作流是先用 `agentsight` 录制，再用 `agentpprof` 分析：

```bash
sudo agentsight record -- claude
agentsight report
agentpprof --project-root . --view tokens -o tokens.svg
agentpprof --project-root . --view time -o time.svg
agentpprof --project-root . --view files -o files.svg
```

## 故障排除

如果找不到 trace，传入明确的 `--session-file` 路径，并确认 trace 的 `cwd` 与 `--project-root` 匹配。

如果标签过于笼统，为项目添加几条 `--tag-rule`，但不要试图让每个 prompt 都独一无二：好的标签保留有用的语义多样性，同时合并无意义的长尾碎片。

如果 pprof 输出能打开但看起来不太对劲，那通常是因为样本单位不是 CPU 时间。先用 `go tool pprof -top` 检查最宽的语义 frame，需要看完整调用栈形状时再生成 SVG 或 folded 输出。

如果要公开分享产物，优先使用 SVG、folded 或 pprof 输出，并且不要传 `--include-previews`，避免敏感信息外泄。
