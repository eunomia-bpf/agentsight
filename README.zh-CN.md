# AgentSight：基于 eBPF 的零侵入 LLM 智能体可观测性工具

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eunomia-bpf/agentsight/actions/workflows/ci.yml/badge.svg)](https://github.com/eunomia-bpf/agentsight/actions/workflows/ci.yml)

[English](https://github.com/eunomia-bpf/agentsight/blob/master/README.md) | **中文**

AgentSight 是一款专为监控 LLM 智能体行为而设计的可观测性工具，通过 SSL/TLS 流量拦截和进程监控来实现。与传统的应用级插桩不同，AgentSight 使用 eBPF 技术在系统边界进行观测，以极低的性能开销提供对 AI 智能体交互的全面洞察。

**零侵入** - 无需修改代码，无需引入新依赖，无需集成 SDK。开箱即用，兼容任何 AI 框架或应用。

## 快速开始

```bash
cargo install agentsight
# 或：wget https://github.com/eunomia-bpf/agentsight/releases/latest/download/agentsight && chmod +x agentsight
agentsight top
```

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/top-mode-demo.png" alt="AgentSight top 实时 session 视图" width="1000">
  <p><em>按 model、session token、health、进程族、工具调用、文件活动和网络活动排序的实时智能体视图</em></p>
</div>

如果使用下载到当前目录的二进制，请运行 `./agentsight top`。
`top` 无需 sudo 也能工作，会读取进程快照以及 Claude、Codex、Gemini、OpenCode
和 OpenClaw 的本地 session 日志；当你用 sudo 运行，或当前用户已有免密/缓存 sudo
时，它会自动启用 live eBPF capture。

如果希望长期后台观察本机智能体，而不是一直开着终端，可以安装 systemd user
service：

```bash
agentsight monitor install-service
```

当 monitor service 正在运行时，`agentsight top` 会直接读取后台 monitor 已保存的窗口数据，
不会再启动另一套 live probes。
后台 monitor 是轻量模式：记录匹配到的本地 agent session，以及进程快照中的 CPU、内存、
I/O 和文件目标数量。它不会捕获 SSL/API payload 或其它 eBPF 事件；如果需要完整 live
eBPF capture，可以使用已有 sudo 权限运行 `agentsight top`，或使用
`sudo agentsight record -- <command>` 录制命令。

## 为什么选择 AgentSight？

### 传统可观测性 vs. 系统级监控

[LangSmith](https://docs.langchain.com/langsmith/observability-concepts)、[Langfuse](https://langfuse.com/docs/observability/overview)、[Phoenix](https://arize.com/docs/phoenix/) 这类应用级工具很适合在你拥有应用代码时追踪 trace、prompt、token、eval 和延迟。[Helicone](https://docs.helicone.ai/getting-started/integration-method/gateway) 这类 gateway/proxy 工具则适合在你可以把 provider 流量路由到托管入口时使用。

AgentSight 关注的是这些工具经常遗漏的一层：智能体在系统边界实际做了什么。它无需 SDK 或代理，就能从应用外部观察已有二进制和 CLI 智能体，并把 LLM 流量与进程执行、文件访问和系统活动关联起来。

| **挑战** | **应用级工具** | **AgentSight 方案** |
|----------|--------------|---------------------|
| **框架接入** | 每个应用需要接入 SDK、callback 或 gateway | 系统级追踪器，无需修改代码 |
| **闭源 CLI** | 只能看到工具主动暴露或记录的内容 | 从应用外部观察已有二进制和 CLI 智能体 |
| **智能体可控日志** | 日志可能不完整、被关闭或被修改 | 独立于应用日志的内核级事件 |
| **TLS LLM 流量** | 通过 SDK/代理路由时可见 | 无需代理，在 SSL/TLS 调用处捕获明文 |
| **系统动作** | 容易遗漏子进程和本地文件活动 | 追踪进程执行、文件访问和资源使用 |
| **跨边界行为** | Trace 通常停在框架或进程边界 | 关联 LLM 流量、进程事件和文件事件 |

AgentSight 能捕获应用级工具遗漏的关键交互：

- 绕过插桩的子进程执行
- SSL/TLS 调用边界处的 LLM 明文载荷
- 文件操作和系统资源访问
- 跨 LLM、进程和文件事件的边界行为

## 使用方法

### 前置要求

- **Linux 内核**：4.1+ 且支持 eBPF（推荐 5.0+）
- **sudo 权限**：`top` 可选；当 sudo 已可用时会自动启用 eBPF probes

从源码构建时还需要 Rust 1.88.0+、Node.js 18+、clang、llvm 和 libelf-dev。

### 安装

#### Cargo 或 Release Binary

本地使用优先安装 CLI，然后运行 `agentsight top`。需要记录某个具体命令时运行
`sudo agentsight record -- <command>`；默认会在当前目录生成 `agentsight-*.db`，
随后 `agentsight report` 和 `agentsight report list` 也默认查看当前目录里的记录。
如果要查看 Claude/Codex/Gemini 的原生日志总览，显式运行 `agentsight report --local`。

#### Docker

AgentSight 通过 Docker 运行，使用 `--privileged` 以支持 eBPF，`--pid=host` 以访问宿主机进程，`-v /sys:/sys:ro` 用于进程监控，`-v /usr:/usr:ro -v /lib:/lib:ro` 用于访问 SSL 库（在共享库如 `libssl.so` 上附加 uprobe 所需）。示例：

```bash
# 监控 Python AI 工具
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm python

# 监控 Claude Code（挂载 home 目录以访问二进制文件）
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $HOME/.local/share/claude:/claude:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm claude --binary-path /claude/versions/2.1.39
```

#### 从源码构建

```bash
# 克隆仓库（含子模块）
git clone https://github.com/eunomia-bpf/agentsight.git --recursive
cd agentsight

# 安装系统依赖（Ubuntu/Debian）
make install

# 构建所有组件（前端、eBPF 和 Rust）
make build

# 或单独构建：
# make build-frontend  # 构建前端资源
# make build-bpf       # 构建 eBPF 程序
# make build-rust      # 构建 Rust collector
```

### Web 界面

`record -- <command>` 默认启动 Web UI。低层 `debug trace` 需要传入 `--server`：
- **时间线视图**：http://127.0.0.1:7395/timeline
- **进程树**：http://127.0.0.1:7395/tree
- **原始日志**：http://127.0.0.1:7395/logs

查看已保存的 SQLite 会话可以运行 `agentsight report serve --db run.db`，然后打开同样的 Web 路由。

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-tree.png" alt="AgentSight 演示 - 进程树可视化" width="800">
  <p><em>进程树视图，展示智能体子进程和文件活动</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-timeline.png" alt="AgentSight 演示 - 时间线可视化" width="800">
  <p><em>时间线视图，展示 LLM、进程、文件和网络事件</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-metrics.png" alt="AgentSight 演示 - 指标可视化" width="800">
  <p><em>指标视图，展示内存和 CPU 使用情况</em></p>
</div>

### 支持的智能体

> **权限：** eBPF probe 需要 root。运行实时捕获命令时使用 `sudo`。

`record` 自动发现二进制、SSL 库和容器进程，开箱即用：

| 智能体 | 命令 |
|--------|------|
| Claude Code | `sudo ./agentsight record -- claude` |
| Gemini CLI | `sudo ./agentsight record -- gemini` |
| Python（aider、open-interpreter 等） | `sudo ./agentsight record -c python` |
| Docker 容器（OpenClaw 等） | `sudo ./agentsight record -c node --binary-path docker://openclaw` |
| 任意命令 | `sudo ./agentsight record -- <command>` |

详见 [docs/agents.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/agents.md)，了解各智能体的详细设置、SSL 注意事项、浏览器捕获、MCP stdio 和高级选项。

### OpenTelemetry 导出

AgentSight 可以将捕获的 LLM 调用导出为 OpenTelemetry **GenAI**（`gen_ai.*`）span，
通过 OTLP/HTTP 发送——无需任何进程内插桩即可获得符合标准的智能体遥测数据。

```bash
sudo ./agentsight debug trace --otel --otel-endpoint http://localhost:4318
```

详见 [docs/otel.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/otel.md)。

## 常见问题

### 通用问题

**问：AgentSight 与传统 APM 工具有什么区别？**
答：AgentSight 使用 eBPF 在内核级运行，提供独立于应用代码的系统级监控。传统 APM 需要插桩，而插桩可能被修改或禁用。

**问：性能影响如何？**
答：由于采用优化的 eBPF 内核空间数据采集，CPU 开销不到 3%。

**问：智能体能否检测到自己正在被监控？**
答：检测极其困难，因为监控在内核级进行，无需修改代码。

### 技术问题

**问：支持哪些 Linux 发行版？**
答：任何内核 4.1+（推荐 5.0+）的发行版。已在 Ubuntu 20.04+、CentOS 8+、RHEL 8+ 上测试通过。

**问：能否同时监控多个智能体？**
答：可以，使用组合监控模式可以对多个智能体进行并发观测和关联分析。

**问：如何过滤敏感数据？**
答：内置 Analyzer 可以移除认证头信息并过滤特定内容模式。

**问：为什么 AgentSight 无法捕获 Claude Code、Node.js 或 Gemini CLI 的流量？**
答：这些应用把 SSL 库静态链接进了自己的二进制（Claude/Bun 使用 BoringSSL，**所有** Node.js——NVM 和系统安装都是——使用 OpenSSL），而非使用系统 `libssl.so`，所以默认没有可供 sslsniff hook 的目标。AgentSight 已为你处理：`record -- <command>` 总会自动发现二进制，`record -c node` 现在也会自动发现 Node 二进制。对于 Claude attach 模式，请传 `--binary-path`。详见"零配置：record"和"监控 Node.js AI 工具"章节。

**问：为什么 `--comm claude` 无法捕获 SSL 流量？**
答：Claude Code 的 SSL 流量运行在内部 "HTTP Client" 线程上，而非主 "claude" 线程。sslsniff 中的 `--comm` 过滤器匹配的是线程名（来自 `bpf_get_current_comm()`），而非进程名。使用 `--binary-path` 时，collector 会自动跳过 SSL 监控的 `--comm` 过滤。

### 故障排除

**问："Permission denied" 错误**
答：确保使用 `sudo` 运行或拥有 `CAP_BPF` 和 `CAP_SYS_ADMIN` 能力。

**问："Failed to load eBPF program" 错误**
答：验证内核版本是否满足要求（见前置要求）。如需要，请为你的架构更新 vmlinux.h。


## 参与贡献

欢迎贡献！克隆并构建后（见上方安装章节），你可以：

```bash
# 运行测试
make test

# 前端开发服务器
cd frontend && npm run dev

# 使用 AddressSanitizer 构建调试版本
make -C bpf debug
```

### 关键资源

- [CLAUDE.md](https://github.com/eunomia-bpf/agentsight/blob/master/CLAUDE.md) - 项目指南和架构
- [docs/design/README.md](https://github.com/eunomia-bpf/agentsight/blob/master/docs/design/README.md) - 归档的设计笔记和研究草稿

## 许可证

MIT 许可证 - 详见 [LICENSE](https://github.com/eunomia-bpf/agentsight/blob/master/LICENSE)。

---

**AI 可观测性的未来**：随着 AI 智能体变得更加自主且具备自我修改能力，传统的可观测性方法变得力不从心。AgentSight 为大规模安全部署 AI 提供了独立的系统级监控。
