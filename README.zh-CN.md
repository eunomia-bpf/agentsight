# AgentSight：基于 eBPF 的零侵入 LLM 智能体可观测性工具

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/eunomia-bpf/agentsight)

[English](README.md) | **中文**

AgentSight 是一款专为监控 LLM 智能体行为而设计的可观测性工具，通过 SSL/TLS 流量拦截和进程监控来实现。与传统的应用级插桩不同，AgentSight 使用 eBPF 技术在系统边界进行观测，以极低的性能开销提供对 AI 智能体交互的全面洞察。

**零侵入** - 无需修改代码，无需引入新依赖，无需集成 SDK。开箱即用，兼容任何 AI 框架或应用。

## 快速开始

```bash
wget https://github.com/eunomia-bpf/agentsight/releases/latest/download/agentsight && chmod +x agentsight
# 记录 Claude Code 活动（基于 Bun，静态链接 BoringSSL，需要 --binary-path）
sudo ./agentsight record -c claude --binary-path ~/.local/share/claude/versions/$(claude --version | head -1)
# 记录 Claude 智能体行为（旧版本）
sudo ./agentsight record -c "claude"
# 记录 gemini-cli 智能体行为（comm 为 "node"）
sudo ./agentsight record -c "node"
# 监控 Python AI 工具（如 aider、open-interpreter）
sudo ./agentsight record -c "python"
# 监控使用 NVM 的 Node.js 应用（静态链接 OpenSSL）
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node
```

访问 [http://127.0.0.1:7395](http://127.0.0.1:7395) 查看记录的数据。

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-tree.png" alt="AgentSight 演示 - 进程树可视化" width="800">
  <p><em>实时进程树可视化，展示 AI 智能体交互和文件操作</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-timeline.png" alt="AgentSight 演示 - 时间线可视化" width="800">
  <p><em>实时时间线可视化，展示 AI 智能体交互和系统调用</em></p>
</div>

<div align="center">
  <img src="https://github.com/eunomia-bpf/agentsight/raw/master/docs/demo-metrics.png" alt="AgentSight 演示 - 指标可视化" width="800">
  <p><em>实时指标可视化，展示 AI 智能体内存和 CPU 使用情况</em></p>
</div>

## 为什么选择 AgentSight？

### 传统可观测性 vs. 系统级监控

| **挑战** | **应用级工具** | **AgentSight 方案** |
|----------|--------------|---------------------|
| **框架适配** | 每个框架都需要新的 SDK/代理 | 即插即用的守护进程，无需修改代码 |
| **闭源工具** | 对内部运作的可见性有限 | 完整可见提示词和行为 |
| **动态智能体行为** | 日志可能被静默或篡改 | 内核级钩子确保可靠监控 |
| **加密流量** | 只能看到封装后的输出 | 捕获真实的未加密请求/响应 |
| **系统交互** | 遗漏子进程执行 | 追踪所有进程行为和文件操作 |
| **多智能体系统** | 隔离的单进程追踪 | 全局关联和分析 |

AgentSight 能捕获应用级工具遗漏的关键交互：

- 绕过插桩的子进程执行
- 智能体处理前的原始加密载荷
- 文件操作和系统资源访问
- 跨智能体通信与协调

## 架构

```ascii
┌─────────────────────────────────────────────────┐
│              AI 智能体运行时                      │
│   ┌─────────────────────────────────────────┐   │
│   │       应用级可观测性                      │   │
│   │  (LangSmith, Helicone, Langfuse 等)      │   │
│   │         可被绕过                          │   │
│   └─────────────────────────────────────────┘   │
│                     ↕ (可被绕过)                  │
├─────────────────────────────────────────────────┤ ← 系统边界
│  AgentSight eBPF 监控（内核级）                    │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │   SSL 流量       │  │    进程事件          │   │
│  │   监控           │  │    监控             │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Rust 流式分析框架                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────┐  │
│  │   Runner    │  │  Analyzer    │  │  输出   │  │
│  │ （收集器）   │  │ （处理器）    │  │        │  │
│  └─────────────┘  └──────────────┘  └────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│             前端可视化                            │
│     时间线 · 进程树 · 事件日志                     │
└─────────────────────────────────────────────────┘
```

### 核心组件

1. **eBPF 数据采集**（内核空间）
   - **SSL 监控器**：通过 uprobe 钩子拦截 SSL/TLS 读写操作
   - **进程监控器**：通过 tracepoint 追踪进程生命周期和文件操作
   - **性能开销 <3%**：在应用层之下运行，影响极小

2. **Rust 流式框架**（用户空间）
   - **Runner**：执行 eBPF 程序并流式传输 JSON 事件（SSL、进程、智能体、组合）
   - **Analyzer**：可插拔的处理器，用于 HTTP 解析、块合并、过滤、日志记录
   - **事件系统**：标准化的事件格式，包含丰富的元数据和 JSON 载荷

3. **前端可视化**（React/TypeScript）
   - 交互式时间线、进程树和日志视图
   - 实时数据流和分析
   - 详见"Web 界面访问"章节

### 数据流管道

```
eBPF 程序 → JSON 事件 → Runner → Analyzer 链 → 前端/存储/输出
```

## 使用方法

### 前置要求

- **Linux 内核**：4.1+ 且支持 eBPF（推荐 5.0+）
- **Root 权限**：加载 eBPF 程序所需
- **Rust 工具链**：1.88.0+（用于构建 collector）
- **Node.js**：18+（用于前端开发）
- **构建工具**：clang、llvm、libelf-dev

### 安装

#### 方式一：使用 Docker（推荐）

AgentSight 通过 Docker 运行，使用 `--privileged` 以支持 eBPF，`--pid=host` 以访问宿主机进程，`-v /sys:/sys:ro` 用于进程监控，`-v /usr:/usr:ro -v /lib:/lib:ro` 用于访问 SSL 库（在共享库如 `libssl.so` 上附加 uprobe 所需）。示例：

```bash
# 监控 Python AI 工具
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm python --log-file /logs/record.log

# 监控 Claude Code（挂载 home 目录以访问二进制文件）
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $HOME/.local/share/claude:/claude:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm claude --binary-path /claude/versions/2.1.39 --log-file /logs/record.log
```

#### 方式二：从源码构建

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

### 使用示例

#### 监控 Claude Code

Claude Code 是基于 Bun 的应用，静态链接了 BoringSSL 且符号被剥离。提供 `--binary-path` 时，AgentSight 通过字节模式匹配自动检测 BoringSSL 函数：

```bash
# 找到 Claude 二进制版本
CLAUDE_BIN=~/.local/share/claude/versions/$(claude --version | head -1)

# 记录所有 Claude 活动并启用 Web UI
sudo ./agentsight record -c claude --binary-path "$CLAUDE_BIN"
# 打开 http://127.0.0.1:7395 查看时间线

# 高级用法：使用自定义过滤器的完整追踪
sudo ./agentsight trace --ssl true --process true --comm claude \
  --binary-path "$CLAUDE_BIN" --server true --server-port 8080
```

这将捕获：
- **对话 API**：`POST /v1/messages` 请求，包含完整的提示词/响应 SSE 流
- **遥测数据**：心跳、事件日志、Datadog 日志
- **进程活动**：文件操作、子进程执行

> **注意**：Claude 中所有 SSL 流量都通过内部 "HTTP Client" 线程传输，而非主 "claude" 线程。当指定 `--binary-path` 时，`--comm` 过滤器会自动跳过 SSL 监控（但仍应用于进程监控），以确保流量被正确捕获。

#### 监控 Python AI 工具

```bash
# 监控 aider、open-interpreter 或任何基于 Python 的 AI 工具
sudo ./agentsight record -c "python"

# 自定义端口和日志文件
sudo ./agentsight record -c "python" --server-port 8080 --log-file /tmp/agent.log
```

#### 监控 Node.js AI 工具（Gemini CLI 等）

对于通过 NVM 安装的静态链接 OpenSSL 的 Node.js 应用，使用 `--binary-path` 指向实际的 Node.js 二进制文件：

```bash
# 监控 Gemini CLI 或其他 Node.js AI 工具
sudo ./agentsight record -c node --binary-path ~/.nvm/versions/node/v20.0.0/bin/node

# 或使用系统 Node.js（使用动态 libssl，无需 --binary-path）
sudo ./agentsight record -c node
```

#### 高级监控

```bash
# SSL 和进程组合监控，启用 Web 界面
sudo ./agentsight trace --ssl true --process true --server true

# 自定义端口和日志文件
sudo ./agentsight record -c "python" --server-port 8080 --log-file /tmp/agent.log
```

#### 浏览器明文捕获

要进行浏览器特定的明文捕获，请使用独立的 `browsertrace` BPF 工具代替 `sslsniff`：

```bash
# Chrome / Chromium
sudo ./bpf/browsertrace --binary-path /opt/google/chrome/chrome

# Ubuntu Snap 上的 Firefox
sudo ./bpf/browsertrace --binary-path /snap/firefox/current/usr/lib/firefox/firefox
```

> **注意**：在 Ubuntu 上，`/usr/bin/firefox` 通常是一个包装脚本而非真正的浏览器 ELF 文件。请将 `browsertrace` 指向实际的 Firefox 二进制文件。

#### 本地 MCP（stdio 模式）

对于通过 `stdio` 而非 HTTP/TLS 通信的本地 MCP 服务器，请使用独立的 `stdiocap` BPF 工具：

```bash
# 捕获本地 MCP 服务器进程的 stdin/stdout/stderr 载荷
sudo ./bpf/stdiocap -p <mcp_server_pid>
```

AgentSight 还在 [`docs/mcp-test/README.md`](docs/mcp-test/README.md) 下包含了一个用于本地测试的最小 MCP 测试套件。它提供了 `stdio` 和 HTTP 两种测试模式，让你可以在接入 Rust collector 之前生成可预测的 MCP 流量。

#### 直接使用 eBPF 程序

```bash
# 直接对 Claude 二进制运行 sslsniff
sudo ./bpf/sslsniff --binary-path ~/.local/share/claude/versions/2.1.39

# 对 NVM Node.js 运行 sslsniff
sudo ./bpf/sslsniff --binary-path ~/.nvm/versions/node/v20.0.0/bin/node --verbose

# 直接对 Chrome 运行 browsertrace
sudo ./bpf/browsertrace --binary-path /opt/google/chrome/chrome

# 直接对本地 MCP 服务器 PID 运行 stdiocap
sudo ./bpf/stdiocap -p 12345

# 运行进程追踪器
sudo ./bpf/process -c python
```

#### Web 界面访问

所有带 `--server` 参数的监控命令都在以下地址提供 Web 可视化：
- **时间线视图**：http://127.0.0.1:7395/timeline
- **进程树**：http://127.0.0.1:7395/tree
- **原始日志**：http://127.0.0.1:7395/logs


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

**问：为什么 AgentSight 无法捕获 Claude Code 或 NVM Node.js 的流量？**
答：这些应用静态链接了 SSL 库（Claude/Bun 使用 BoringSSL，NVM Node.js 使用 OpenSSL），而非使用系统 `libssl.so`。请使用 `--binary-path` 指向实际的二进制文件，AgentSight 将通过字节模式匹配自动检测 SSL 函数。详见"监控 Claude Code"和"监控 Node.js AI 工具"章节。

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

- [CLAUDE.md](CLAUDE.md) - 项目指南和架构
- [collector/DESIGN.md](collector/DESIGN.md) - 框架设计详情
- [docs/why.md](docs/why.md) - 问题分析和动机（[中文版](docs/why.zh-CN.md)）

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

---

**AI 可观测性的未来**：随着 AI 智能体变得更加自主且具备自我修改能力，传统的可观测性方法变得力不从心。AgentSight 为大规模安全部署 AI 提供了独立的系统级监控。
