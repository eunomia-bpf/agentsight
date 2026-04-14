# AgentSight

[English](README.md)

基于 eBPF 的 AI Agent 可观测性工具，在 Linux 系统上提供零侵入式的 LLM API 调用监控、Token 用量统计、进程行为追踪和 SSL/TLS 流量捕获。AgentSight 是 [ANOLISA](../../README_CN.md) 的可观测性组件。

## 特性

- **零侵入式监控** — 通过 eBPF 内核探针捕获事件，无需修改 Agent 代码或配置。
- **SSL/TLS 流量解密** — 基于 uprobe 拦截 OpenSSL/GnuTLS 库调用，捕获加密连接的明文 HTTP 流量。
- **LLM Token 精确计量** — 集成 Hugging Face tokenizer，支持 Qwen 等系列模型的精确 Token 计数。
- **AI Agent 自动发现** — 扫描 `/proc` 并监控 `execve` 事件，动态检测系统上运行的 AI Agent 进程。
- **流式响应支持** — 解析 Server-Sent Events (SSE)，追踪 LLM 流式响应。
- **审计日志** — 完整记录 LLM 调用和进程操作的结构化审计轨迹。
- **云端集成** — 原生支持导出至阿里云 SLS（日志服务）进行集中化日志分析。
- **GenAI 语义事件** — 构建 LLM 调用、工具使用和 Agent 交互的结构化语义事件。

## 架构

AgentSight 采用统一的数据流水线架构：

```
┌──────────┐    ┌────────┐    ┌────────────┐    ┌──────────┐    ┌───────┐    ┌─────────┐
│  Probes  │───▶│ Parser │───▶│ Aggregator │───▶│ Analyzer │───▶│ GenAI │───▶│ Storage │
└──────────┘    └────────┘    └────────────┘    └──────────┘    └───────┘    └─────────┘
  eBPF 事件      HTTP/SSE      请求-响应          Token/审计      语义         SQLite /
  (内核态)       结构化提取     关联聚合           信息提取        事件构建     SLS 导出
```

| 阶段 | 说明 |
|------|------|
| **Probes** | eBPF 程序（sslsniff、proctrace、procmon）通过 ring buffer 捕获内核事件 |
| **Parser** | 提取结构化的 HTTP 消息、SSE 事件和进程执行数据 |
| **Aggregator** | 关联请求-响应对；通过 LRU 缓存追踪进程生命周期 |
| **Analyzer** | 生成审计记录、Token 使用统计和 LLM API 消息 |
| **GenAI** | 将结果转换为语义事件（LLM 调用、工具使用、Agent 交互） |
| **Storage** | 持久化到本地 SQLite 数据库，可选上传至阿里云 SLS |

### eBPF 探针

| 探针 | 源文件 | 说明 |
|------|--------|------|
| **sslsniff** | `src/bpf/sslsniff.bpf.c` | 通过 uprobe 挂钩 SSL_read/SSL_write，捕获加密连接的明文数据 |
| **proctrace** | `src/bpf/proctrace.bpf.c` | 追踪 execve 系统调用，捕获命令行参数，构建进程树 |
| **procmon** | `src/bpf/procmon.bpf.c` | 轻量级进程监控，追踪进程创建/退出事件（用于 Agent 发现） |

### 项目结构

```
agentsight/
├── src/
│   ├── bpf/            # eBPF C 程序（sslsniff、proctrace、procmon）
│   ├── probes/         # eBPF 探针管理和事件轮询
│   ├── parser/         # HTTP、SSE 和进程事件解析器
│   ├── aggregator/     # 请求-响应关联和进程聚合
│   ├── analyzer/       # Token 提取、审计记录、消息解析
│   ├── genai/          # GenAI 语义事件构建器和 SLS 上传器
│   ├── storage/        # 基于 SQLite 的存储（审计、Token、HTTP、GenAI）
│   ├── discovery/      # AI Agent 进程扫描器（/proc + eBPF）
│   ├── tokenizer/      # HuggingFace tokenizer 集成，用于 Token 计数
│   ├── bin/            # CLI 入口（agentsight 及子命令）
│   ├── unified.rs      # 主流水线编排器
│   ├── config.rs       # 统一配置管理
│   └── event.rs        # 统一事件类型定义
├── Cargo.toml
├── build.rs            # 为三个探针生成 eBPF skeleton
└── agentsight.spec     # RPM 打包规范
```

## CLI 命令

### `agentsight trace`

启动基于 eBPF 的 AI Agent 活动追踪。

```bash
# 前台模式
sudo agentsight trace

# 守护进程模式，配合 SLS 导出
sudo agentsight trace --daemon \
  --sls-endpoint <endpoint> \
  --sls-project <project> \
  --sls-logstore <logstore>
```

### `agentsight token`

查询 Token 用量数据。

```bash
# 查看今日 Token 用量
agentsight token

# 本周用量，与上周对比
agentsight token --period week --compare

# 按角色和类型的详细分解
agentsight token --detail

# JSON 格式输出
agentsight token --json
```

### `agentsight audit`

查询审计事件（LLM 调用、进程操作）。

```bash
# 查看最近的审计事件
agentsight audit

# 按 PID 和事件类型过滤
agentsight audit --pid 12345 --type llm

# 汇总统计
agentsight audit --summary
```

### `agentsight serve`

启动 HTTP API 服务器，同时提供嵌入式 Dashboard UI。

```bash
# 使用默认配置启动（绑定到 127.0.0.1:7396）
agentsight serve

# 绑定到所有网络接口并指定端口
agentsight serve --host 0.0.0.0 --port 8080

# 指定数据库文件路径
agentsight serve --db /path/to/genai_events.db
```

### `agentsight discover`

发现系统上运行的 AI Agent。

```bash
# 扫描运行中的 Agent
agentsight discover

# 列出所有已知 Agent 类型
agentsight discover --list

# 详细输出（包含可执行文件路径）
agentsight discover --verbose
```

## Dashboard

Dashboard 是基于 React 的 Web 可视化界面，用于查看对话历史、Trace 详情和 Token 统计数据。它在编译时嵌入到 `agentsight serve` 二进制文件中。

### 构建 Dashboard

```bash
cd src/agentsight

# 构建前端并输出到 frontend-dist/（cargo build 前必须先执行）
make build-frontend

# 再构建包含嵌入 UI 的 Rust 二进制
make build

# 或一步完成
make build-all
```

### 场景一 — 同时采集数据并查看 Dashboard

在两个终端中分别运行追踪器和 API 服务器：

```bash
# 终端 1：启动 eBPF 追踪（写入 SQLite）
sudo agentsight trace

# 终端 2：启动 API 服务器（读取同一 SQLite 文件）
agentsight serve
```

在浏览器中打开 `http://127.0.0.1:7396`，Dashboard 会随新数据自动刷新。

> **在远程服务器上运行？** 绑定到所有网络接口，通过服务器公网 IP 访问：
> ```bash
> agentsight serve --host 0.0.0.0 --port 7396
> ```
> 然后在本地浏览器中打开 `http://<服务器公网IP>:7396`。
> 请确保服务器防火墙 / 安全组已放行 7396 端口。

### 场景二 — 仅查看历史数据

无需启动追踪，直接指向已有数据库启动服务器：

```bash
agentsight serve --db /path/to/genai_events.db
```

打开 `http://127.0.0.1:7396` 即可浏览已记录的对话和 Trace。


## 快速开始

### 环境要求

| 组件 | 版本 |
|------|------|
| Linux 内核 | >= 5.8（需要 BTF 支持） |
| Rust | >= 1.80 |
| clang / llvm | >= 11（用于 eBPF 编译） |
| libbpf | >= 0.8 |

### 从源码构建

```bash
cd src/agentsight
cargo build --release
```

二进制文件输出至 `target/release/agentsight`。

### 通过 RPM 安装

```bash
sudo yum install agentsight
```

安装内容：
- `/usr/local/bin/agentsight` — CLI 可执行文件

### 开始追踪

```bash
# 需要 root 权限以加载 eBPF 程序
sudo agentsight trace
```

## 配置

通过 `AgentsightConfig` 进行统一配置：

| 类别 | 选项 | 说明 |
|------|------|------|
| 存储 | `db_path` | SQLite 数据库文件路径 |
| 存储 | `data_retention_days` | 数据保留天数 |
| 探针 | `target_uid` | 按 UID 过滤事件 |
| 探针 | `poll_timeout_ms` | Ring buffer 轮询超时 |
| HTTP | `connection_cache_capacity` | 连接追踪的 LRU 缓存大小 |
| SLS | `sls_endpoint` / `sls_project` / `sls_logstore` | 阿里云 SLS 导出配置 |
| Tokenizer | `tokenizer_file` | HuggingFace tokenizer 文件路径或 URL |

## 支持的 LLM 提供商

Token 解析支持多种 LLM API 格式：

- OpenAI / OpenAI 兼容 API
- Anthropic（Claude，包括缓存 Token 处理）
- Google Gemini
- 通义千问 Qwen（支持原生 Chat Template）

## 项目起源

本项目源于 [https://github.com/eunomia-bpf/agentsight.git](https://github.com/eunomia-bpf/agentsight.git)。

## 许可证

Apache License 2.0 — 详见 [LICENSE](../../LICENSE)。
