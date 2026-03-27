# eBPF 监控工具

[English](README.md) | **中文**

本目录包含用于系统可观测性和安全分析的 eBPF 监控工具。

## 工具概述

### 1. 进程追踪器（`process`）

基于 eBPF 的高级进程监控工具，追踪进程生命周期和文件打开操作，并具备智能事件去重功能。

**核心特性：**
- 监控进程创建和终止
- 追踪文件打开操作并去重
- 可配置的过滤模式，适用于不同监控级别
- 60 秒滑动窗口聚合重复文件打开事件
- JSON 输出格式，便于与分析框架集成
- 详细调试模式用于故障排除

**使用方法：**
```bash
sudo ./process [OPTIONS]
```

**命令行参数：**

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `--help` | `-?` | 显示帮助信息并退出 | - |
| `--usage` | - | 显示简要用法 | - |
| `--version` | `-V` | 显示版本信息 | - |
| `--verbose` | `-v` | 启用详细调试输出到 stderr | 禁用 |
| `--duration=MS` | `-d MS` | 报告的最小进程持续时间（毫秒） | 0 |
| `--commands=LIST` | `-c LIST` | 逗号分隔的要追踪的命令列表 | 全部 |
| `--pid=PID` | `-p PID` | 仅追踪指定 PID | 全部 |
| `--mode=MODE` | `-m MODE` | 过滤模式（0=全部, 1=进程, 2=过滤） | 2 |
| `--all` | `-a` | 已弃用：请使用 `-m 0` | - |

**过滤模式：**
- `0（全部）`：追踪所有进程和所有文件打开操作
- `1（进程）`：追踪所有进程，但仅追踪已跟踪 PID 的文件打开
- `2（过滤）`：仅追踪匹配过滤条件的进程及其文件打开（默认）

**示例：**
```bash
# 追踪所有内容并启用详细输出
sudo ./process -v -m 0

# 追踪所有进程，选择性读写
sudo ./process -m 1

# 仅追踪特定进程
sudo ./process -c "claude,python,node"

# 追踪持续时间超过 1 秒的进程
sudo ./process -c "ssh" -d 1000

# 追踪指定 PID 并启用详细调试
sudo ./process -v -p 1234

# 追踪多个命令并设置最小持续时间
sudo ./process -c "curl,wget" -d 500
```

**文件打开去重：**
- 文件打开首次出现时立即报告（`count=1`）
- 60 秒窗口内的相同文件打开操作会被聚合
- 窗口过期时报告聚合结果（`count=N`）
- 进程退出时刷新所有待处理的聚合
- 对于重复的文件打开操作，事件量减少 80-95%

**详细调试输出（`-v`）：**
- 显示事件去重/聚合时机
- 报告聚合窗口过期
- 显示进程退出时的聚合刷新
- 展示聚合表统计信息
- 帮助排查去重行为

### 2. SSL 流量监控器（`sslsniff`）

基于 eBPF 的 SSL/TLS 流量拦截器，捕获加密通信用于安全分析。

**核心特性：**
- 实时拦截 SSL/TLS 流量
- 支持多种 SSL 库（OpenSSL、GnuTLS、NSS）
- 进程级过滤能力（PID、UID、命令）
- 从加密流中提取明文
- 握手事件监控
- JSON 输出格式用于分析

**使用方法：**
```bash
sudo ./sslsniff [OPTIONS]
```

**命令行参数：**

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `--help` | `-?` | 显示帮助信息并退出 | - |
| `--usage` | - | 显示简要用法 | - |
| `--version` | `-V` | 显示版本信息 | - |
| `--verbose` | `-v` | 启用详细调试输出到 stderr | 禁用 |
| `--pid=PID` | `-p PID` | 仅追踪指定 PID | 全部 |
| `--uid=UID` | `-u UID` | 仅追踪指定 UID | 全部 |
| `--comm=COMMAND` | `-c COMMAND` | 仅追踪匹配的命令 | 全部 |
| `--binary-path` | - | 静态链接 SSL 的二进制文件路径 | 自动检测 |
| `--no-openssl` | `-o` | 禁用 OpenSSL 流量捕获 | 已启用 |
| `--no-gnutls` | `-g` | 禁用 GnuTLS 流量捕获 | 已禁用 |
| `--no-nss` | `-n` | 禁用 NSS 流量捕获 | 已禁用 |
| `--handshake` | `-h` | 显示 SSL 握手事件 | 禁用 |

**SSL 库支持：**
- **OpenSSL**：默认启用（最常见），附加到系统 `libssl.so`
- **GnuTLS**：默认禁用，使用 `--gnutls` 启用或使用 `--no-openssl` 禁用 OpenSSL
- **NSS**：默认禁用，使用 `--nss` 启用
- **BoringSSL**（静态链接）：提供 `--binary-path` 时通过字节模式匹配自动检测。支持剥离符号的二进制文件（无需符号）。

**示例：**
```bash
# 监控所有 SSL 流量并启用详细输出
sudo ./sslsniff -v

# 按 PID 监控特定进程
sudo ./sslsniff -p 1234

# 监控指定用户的 SSL 流量
sudo ./sslsniff -u 1000

# 仅监控 curl 的 SSL 流量
sudo ./sslsniff -c curl

# 监控并显示握手事件
sudo ./sslsniff -h

# 仅监控 GnuTLS 流量（禁用 OpenSSL）
sudo ./sslsniff --no-openssl -g

# 监控特定进程，启用握手和详细输出
sudo ./sslsniff -v -h -p 1234

# 多条件监控
sudo ./sslsniff -c "python" -u 1000 -h
```

**监控静态链接 SSL 的应用（BoringSSL/OpenSSL）：**

某些应用（如 Claude Code/Bun、NVM Node.js）静态链接了 SSL 库而非使用系统 `libssl.so`。对于这些应用，使用 `--binary-path` 指向实际的可执行文件：

```bash
# 监控 Claude Code（Bun + 静态链接 BoringSSL）
# 注意：不要使用 -c claude，因为 SSL 流量来自 "HTTP Client" 线程
sudo ./sslsniff --binary-path ~/.local/share/claude/versions/2.1.39

# 监控 NVM Node.js（静态链接 OpenSSL）
sudo ./sslsniff --binary-path ~/.nvm/versions/node/v20.0.0/bin/node

# 启用详细输出以查看检测到的偏移量
sudo ./sslsniff --binary-path ~/.local/share/claude/versions/2.1.39 --verbose
# stderr: BoringSSL detected! SSL_read=0x5c38e80, SSL_write=0x5c39b20, ...
```

指定 `--binary-path` 时，sslsniff 会：
1. 首先尝试从二进制文件中解析 `SSL_read`/`SSL_write` 符号
2. 如果找不到符号（符号被剥离的二进制文件），回退到 BoringSSL 字节模式检测以自动找到函数偏移量
3. 在检测到的偏移量处附加 uprobe

> **重要提示**：`-c`（comm）过滤器匹配的是 `bpf_get_current_comm()` 返回的**线程名**，而非进程名。对于像 Claude Code 这样 SSL 在专用 "HTTP Client" 线程上运行的应用，使用 `-c claude` 会过滤掉所有流量。使用 `--binary-path` 时请省略 `-c`。

**输出格式：**
- 每个 SSL 事件以 JSON 对象输出
- 受内核限制，eBPF 捕获每个事件最大 32KB
- 事件包含时间戳、进程信息和 SSL 数据
- 握手事件显示 SSL 协商详情

**过滤选项：**
- **PID 过滤**：仅捕获指定进程的流量
- **UID 过滤**：仅捕获指定用户的流量
- **命令过滤**：仅捕获匹配命令名的流量
- **库过滤**：选择监控哪些 SSL 库

### 3. Stdio 载荷捕获（`stdiocap`）

基于 eBPF 的 stdio 和管道载荷追踪器，用于本地进程通信。适用于 SSL/TLS 追踪不适用但仍需查看请求/响应载荷的场景（如本地 MCP 的 `stdio` 模式）。

**核心特性：**
- 从目标进程捕获 `read` 和 `write` 载荷
- 默认关注 `stdin` / `stdout` / `stderr`
- 可选全 FD 模式，用于追踪基于管道的客户端进程
- JSON 输出，包含 PID、FD 角色、FD 目标、延迟和载荷内容

**使用方法：**
```bash
sudo ./stdiocap -p PID [OPTIONS]
```

**命令行参数：**

| 参数 | 缩写 | 说明 | 默认值 |
|------|------|------|--------|
| `--pid=PID` | `-p PID` | 仅追踪此 PID | 必填 |
| `--uid=UID` | `-u UID` | 仅追踪此 UID | 全部 |
| `--comm=COMMAND` | `-c COMMAND` | 仅追踪匹配的命令 | 全部 |
| `--all-fds` | - | 捕获所有 FD 而非仅 `0/1/2` | 禁用 |
| `--max-bytes=BYTES` | - | 每个事件输出的最大字节数 | 8192 |
| `--verbose` | `-v` | 启用 libbpf 详细调试输出 | 禁用 |

**示例：**
```bash
# 追踪本地 MCP 服务器进程的 stdio 载荷
sudo ./stdiocap -p 12345

# 追踪 MCP 管道 FD 不是 0/1/2 的客户端进程
sudo ./stdiocap -p 12345 --all-fds
```

## 构建工具

### 前置依赖
```bash
# 安装依赖（Ubuntu/Debian）
make install

# 或手动安装：
sudo apt-get install -y libelf1 libelf-dev zlib1g-dev make clang llvm
```

### 构建命令
```bash
# 构建所有工具
make build

# 构建单个工具
make process
make sslsniff
make stdiocap

# 构建带调试符号的版本
make debug
make sslsniff-debug

# 运行测试
make test

# 清理构建产物
make clean
```

## 架构

两个工具使用相同的架构模式：

1. **eBPF 内核程序**（`.bpf.c` 文件）
   - 内核空间代码，挂钩到系统事件
   - 以极低的性能开销采集数据
   - 输出结构化事件数据

2. **用户空间加载器**（`.c` 文件）
   - 加载和管理 eBPF 程序
   - 处理内核事件并格式化输出
   - 处理命令行参数和配置

3. **头文件**（`.h` 文件）
   - 内核和用户空间之间的共享数据结构
   - 事件定义和配置常量

## 输出格式

两个工具都将 JSON 格式的事件输出到 stdout，启用详细模式时调试信息发送到 stderr。

### JSON Schema

所有事件遵循通用基础 schema，并包含事件特定字段：

**基础事件字段：**
- `timestamp`：Unix 时间戳，纳秒（uint64）
- `event`：事件类型字符串（EXEC、EXIT、FILE_OPEN、BASH_READLINE、SSL_READ、SSL_WRITE、SSL_HANDSHAKE）
- `comm`：进程命令名（字符串，最长 16 字符）
- `pid`：进程 ID（int32）

**进程事件字段：**
- `ppid`：父进程 ID（int32）
- `filename`：可执行文件路径（字符串，仅 EXEC 事件）
- `exit_code`：进程退出码（uint32，仅 EXIT 事件）
- `duration_ms`：进程生命周期，毫秒（uint64，仅 EXIT 事件）

**文件打开事件字段：**
- `count`：聚合的文件打开次数（uint32）
- `filepath`：文件完整路径（字符串，最长 256 字符）
- `flags`：文件打开标志（int32）
- `window_expired`：聚合窗口过期时出现（布尔值，可选）
- `reason`：聚合刷新原因（字符串，可选："process_exit"）

**Bash Readline 事件字段：**
- `command`：输入的命令行（字符串，最长 256 字符）

**SSL 事件字段：**
- `uid`：进程的用户 ID（uint32）
- `data`：SSL 流量数据（字符串，最大 32KB）
- `data_len`：捕获的数据长度（uint32）
- `truncated`：数据是否因大小限制被截断（布尔值）

### 进程追踪器 JSON 事件

**进程事件：**
```json
{
  "timestamp": 1234567890123456789,
  "event": "EXEC",
  "comm": "python3",
  "pid": 1234,
  "ppid": 1000,
  "filename": "/usr/bin/python3"
}

{
  "timestamp": 1234567890123456789,
  "event": "EXIT",
  "comm": "python3",
  "pid": 1234,
  "ppid": 1000,
  "exit_code": 0,
  "duration_ms": 5000
}
```

**文件打开事件：**
```json
{
  "timestamp": 1234567890123456789,
  "event": "FILE_OPEN",
  "comm": "python3",
  "pid": 1234,
  "count": 1,
  "filepath": "/etc/passwd",
  "flags": 0
}

{
  "timestamp": 1234567890123456789,
  "event": "FILE_OPEN",
  "comm": "python3",
  "pid": 1234,
  "count": 5,
  "filepath": "/etc/passwd",
  "flags": 0,
  "window_expired": true
}

{
  "timestamp": 1234567890123456789,
  "event": "FILE_OPEN",
  "comm": "python3",
  "pid": 1234,
  "count": 3,
  "filepath": "/tmp/tempfile.txt",
  "flags": 577,
  "reason": "process_exit"
}
```

**Bash Readline 事件：**
```json
{
  "timestamp": 1234567890123456789,
  "event": "BASH_READLINE",
  "comm": "bash",
  "pid": 1234,
  "command": "ls -la"
}
```

### SSL 流量监控器 JSON 事件

每个 SSL 事件为单行 JSON，schema 如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `function` | string | `"READ/RECV"`、`"WRITE/SEND"` 或 `"HANDSHAKE"` |
| `timestamp_ns` | uint64 | 系统启动后的纳秒（`bpf_ktime_get_ns()`） |
| `comm` | string | 线程名（最长 16 字符），如 `"curl"`、`"HTTP Client"` |
| `pid` | int32 | 进程 ID（tgid） |
| `tid` | int32 | 线程 ID |
| `uid` | uint32 | 用户 ID |
| `len` | int32 | SSL_read/SSL_write 返回的总字节数 |
| `buf_size` | uint32 | 实际复制到事件缓冲区的字节数（可能 < `len`） |
| `latency_ms` | float | SSL_read/SSL_write 进入到退出之间的时间，毫秒 |
| `is_handshake` | bool | 如果是握手事件则为 `true` |
| `data` | string\|null | 解密的明文内容（JSON 转义），无数据时为 `null` |
| `truncated` | bool | 如果 `buf_size < len`（数据超过 512KB 缓冲区）则为 `true` |
| `bytes_lost` | int | 仅在 `truncated` 为 `true` 时出现：`len - buf_size` |

**SSL 读写事件：**
```json
{
  "function": "WRITE/SEND",
  "timestamp_ns": 242692590000000,
  "comm": "HTTP Client",
  "pid": 959023,
  "tid": 959035,
  "uid": 1000,
  "len": 2865,
  "buf_size": 2865,
  "latency_ms": 0.042,
  "is_handshake": false,
  "data": "POST /v1/messages?beta=true HTTP/1.1\r\nHost: api.anthropic.com\r\n...",
  "truncated": false
}

{
  "function": "READ/RECV",
  "timestamp_ns": 242692596213720,
  "comm": "HTTP Client",
  "pid": 959023,
  "tid": 959035,
  "uid": 1000,
  "len": 1192,
  "buf_size": 1192,
  "latency_ms": 0.014,
  "is_handshake": false,
  "data": "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream; charset=utf-8\r\n...",
  "truncated": false
}
```

**截断事件**（数据超过 512KB 缓冲区时）：
```json
{
  "function": "WRITE/SEND",
  "timestamp_ns": 242692590000000,
  "comm": "HTTP Client",
  "pid": 959023,
  "tid": 959035,
  "uid": 1000,
  "len": 600000,
  "buf_size": 524288,
  "latency_ms": 0.100,
  "is_handshake": false,
  "data": "POST /v1/messages ...(前 512KB)...",
  "truncated": true,
  "bytes_lost": 75712
}
```

**SSL 握手事件**（仅在使用 `--handshake` / `-h` 参数时）：
```json
{
  "function": "HANDSHAKE",
  "timestamp_ns": 242692580000000,
  "comm": "HTTP Client",
  "pid": 959023,
  "tid": 959035,
  "uid": 1000,
  "len": 0,
  "buf_size": 0,
  "latency_ms": 12.345,
  "is_handshake": true,
  "data": null,
  "truncated": false
}
```

**注意事项：**
- `comm` 是 `bpf_get_current_comm()` 返回的**线程名**，而非进程名。例如，Claude Code 的 SSL 流量显示 `"HTTP Client"`，而非 `"claude"`。
- `data` 包含解密的明文。控制字符会被 JSON 转义（`\n`、`\r`、`\t`、`\uXXXX`）。有效的 UTF-8 序列直接传递。
- `len` 是 SSL_read/SSL_write 返回的值。`buf_size` 是实际复制的量（上限 512KB）。

### 常见使用模式

**实时监控：**
```bash
# 监控并格式化 JSON 输出
sudo ./process -v -c "python" | jq '.'

# 过滤特定事件类型
sudo ./process -c "curl" | jq 'select(.event == "FILE_OPEN")'

# 监控 SSL 流量并美化打印
sudo ./sslsniff -p 1234 | jq '.'
```

**日志收集：**
```bash
# 保存到文件并带时间戳
sudo ./process -m 1 > process_events.jsonl 2> process_debug.log

# 管道到 syslog
sudo ./sslsniff -c "nginx" | logger -t sslsniff

# 发送到日志聚合系统
sudo ./process -c "app" | ./log_shipper --index=security
```

**集成示例：**
```bash
# 与分析工具结合
sudo ./process -p 1234 | python3 analyze_events.py

# 实时告警
sudo ./sslsniff -u 1000 | grep -i "password" | alert_system.sh

# 统计分析
sudo ./process -c "python" | jq -r '.event' | sort | uniq -c
```

JSON 输出设计用于：
- 日志聚合系统（ELK、Splunk 等）
- 实时分析管道
- 与 Rust collector 框架集成
- 安全信息和事件管理（SIEM）系统
- 自定义分析和监控脚本

## 安全注意事项

**重要安全说明：**
- 两个工具都需要 root 权限来加载 eBPF 程序
- SSL 流量捕获包含潜在敏感数据
- 进程监控可能暴露系统信息
- 仅用于防御性安全和监控目的

## 集成

这些工具设计为与 `collector` 框架配合使用：
- 构建的二进制文件在编译时嵌入到 Rust collector 中
- Collector 提供流式分析和事件处理
- 输出可被多个 Analyzer 插件处理

## 故障排除

**权限问题：**
```bash
# 确保正确的权限
sudo ./process
sudo ./sslsniff
```

**内核兼容性：**
- 需要支持 eBPF 的 Linux 内核（4.1+）
- 推荐 CO-RE（编译一次，到处运行）支持
- 检查内核配置：`CONFIG_BPF=y`、`CONFIG_BPF_SYSCALL=y`

**调试模式：**
```bash
# 使用 AddressSanitizer 构建用于调试
make debug
sudo ./process-debug
```

## 相关文档

- 查看 `/collector/README.md` 了解 Rust 框架集成
- 查看 `/CLAUDE.md` 了解开发指南
- 查看项目主 README 了解整体架构
