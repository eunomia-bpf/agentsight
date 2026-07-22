# AgentPProf：用标准 pprof 分析 AI Agent 的工作结构

AgentPProf 是一个无需 sudo 的离线 profiler。它读取 Codex、Claude Code、
portable agent trace、Chrome/Perfetto trace 或规范化 operation JSONL，并把
Agent 活动转换成带权重的语义 operation stack。

## 硬性产品边界

每次成功运行只写出一个标准 `.pb` 或 `.pb.gz` pprof。AgentPProf 不开发
自定义前端，也不提供 folded stack、SVG、PNG、HTML、JSON、dashboard 或
trace export 等第二条产品输出路径。火焰图、搜索、focus、比较和下钻全部
复用现有 pprof-compatible 工具。

命令会在 stdout 打印一小段 JSON 状态，但它不是第二个 profile 或可视化
artifact。portable trace 和标准 trace 只作为输入。

## 安装与第一次运行

```bash
cargo install --path agentpprof --locked --force
agentpprof --project-root . --view tokens -o tokens.pb.gz
go tool pprof -top tokens.pb.gz
go tool pprof -tags tokens.pb.gz
go tool pprof -http=:0 tokens.pb.gz
```

不希望读取本机私有会话时，显式使用公开 fixture：

```bash
agentpprof \
  --project-root . \
  --project-name agentsight-public-fixture \
  --session-file agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --tagger regex \
  --no-cache \
  --view operations \
  -o fixture.pb.gz
```

## Profile 视图

`--view` 选择度量，`--stack` 独立选择语义层级。

| View | 宽度含义 |
|---|---|
| `operations` | 观察到的 operation 数量 |
| `tokens` | 输入、输出、缓存或推理 token |
| `files` | 文件或路径 effect |
| `network` | 域名或网络 effect |
| `time` | 根据源时间戳推导的经过时间 |

```bash
agentpprof --view operations -o operations.pb.gz
agentpprof --view tokens     -o tokens.pb.gz
agentpprof --view files      -o files.pb.gz
agentpprof --view network    -o network.pb.gz
agentpprof --view time       -o time.pb.gz
```

这些是语义 profile，不是 CPU profile；宽度表示所选的 Agent 工作量。

## 任务语义栈

主层级应该表达任务，而不是系统日志字段：

```text
任务 -> 子任务 -> 阶段/策略 -> 语义动作 -> 对象 -> 结果 -> outcome
```

Agent、模型、session、工具类型、命令、路径、状态、source id、call id 和
时间戳保留为过滤和证据下钻信息，不应替代任务结构。

对规范化 operation 输入，可以显式选择字段：

```bash
agentpprof \
  --operation-file operations.jsonl \
  --view operations \
  --stack 'task,subtask,phase,action,object,result,outcome' \
  -o operations.pb.gz
```

每行 JSONL 是一个带权 operation：

```json
{"value":1,"fields":{"task":"write paper","subtask":"write abstract","action":"edit","object":"main.tex","result":"completed"}}
```

`--op-map`、`--op-map-file` 和 `--where` 在构造 stack 前派生和筛选可见
字段；`--stack-rule` 可以覆盖一个 frame。JSON `--profile-spec` 可以保存
同样的输入和配置，但输出仍必须是唯一的 `.pb` 或 `.pb.gz` pprof。

## 输入

- Codex 和 Claude Code 原生 session JSONL；
- `--session-file`：显式原生会话文件；
- `--trace-file`：`agentsight.agent-session.trace.v1` portable trace；
- `--standard-trace-file`：Chrome/Perfetto Trace Event JSON；
- `--operation-file`：规范化 operation JSONL。

所有适配器先把输入转换成 operation，再进行 profiling；它们不会增加新的
profiler 抽象或产品输出。

## 差分 pprof

比较同一任务的坏执行和好执行时，生成一个带符号的 candidate-minus-base
pprof：

```bash
agentpprof \
  --operation-file bad-trace.jsonl \
  --diff-base-operation-file good-trace.jsonl \
  --view tokens \
  --stack 'task,subtask,phase,action,object,result,outcome' \
  -o bad-minus-good.pb.gz
```

candidate sample 为正，base sample 为负。每个原始 sample 保留
`comparison_side` 和源证据标签，因此 pprof 工具可以按侧 focus，并定位回
源记录。

## 证据与隐私

在来源允许时，profile 会保留 source kind、source session、evidence/call
id、response phase、outcome 和时间戳标签。项目根目录之外的路径会映射到
稳定的 external bucket。

本机历史仍可能敏感。公开 artifact 应使用显式、已清理的输入，并在分享前
运行 `go tool pprof -tags` 检查标签。

## 开发验证

```bash
cargo test --manifest-path agent-session/Cargo.toml
cargo test --manifest-path agentpprof/Cargo.toml
cargo run --manifest-path agentpprof/Cargo.toml -- --help
```
