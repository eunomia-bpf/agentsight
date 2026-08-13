# 使用说明

[English](https://github.com/eunomia-bpf/agentsight/blob/master/docs/usage.md) | **中文**

## 从源代码编译

### 1. 克隆仓库并初始化子模块

```sh
git clone https://github.com/eunomia-bpf/agentsight.git
cd agentsight
git submodule update --init --recursive
```

如果你已经克隆过仓库但尚未初始化子模块（`libbpf/` 和 `bpftool/` 目录为空），请执行：

```sh
git submodule update --init --recursive
```

### 2. 安装系统依赖

```sh
make install
```

这会安装编译所需的 libelf、zlib、clang、llvm、Node.js 和 Rust 工具链。

### 3. 编译

```sh
make build
```

编译成功后，agentsight 二进制程序生成在 `collector/target/release/agentsight`。

也可以单独编译各组件：

```sh
make build-bpf    # 仅编译 eBPF C 程序
make build-rust   # 仅编译 Rust collector
make build-frontend  # 仅编译前端
```

## 从源码运行

`make build` 完成后，在仓库根目录运行下面的命令。除 `top` 外，需要加载 eBPF probes
的命令推荐显式使用 `sudo`；`top` 无需 sudo 也能工作，并在 sudo 已可用时启用 live
eBPF capture。没有 eBPF 权限时，它会退化到进程快照和 agent-native session。

```sh
# 实时查看本机智能体 session
./collector/target/release/agentsight top

# 启动并记录一个命令
sudo ./collector/target/release/agentsight record -- claude

# 查看最近保存的运行
./collector/target/release/agentsight report

# 附加到已经运行的进程族
sudo ./collector/target/release/agentsight record -c claude

# 可配置的底层调试追踪
sudo ./collector/target/release/agentsight debug trace --server -c claude

# 原始 SSL 调试捕获，启用 HTTP 解析
sudo ./collector/target/release/agentsight debug ssl --http-parser
```

## top、record 与 debug trace

日常使用先从 `top` 开始；需要保存一次运行用于复盘时使用 `record`；只有在需要
精细控制采集源和过滤规则时才使用 `debug trace`。

### top — 默认实时视图

`top` 是最直接的入口，用于实时查看本机正在活动的智能体 session。它会发现本地
智能体进程和 agent-native session 日志，并把系统活动关联到 session。

典型用法：

```sh
./agentsight top
```

### record — 开箱即用的智能体录制

适用于录制 AI 智能体（Claude Code、Python AI 工具等）的一次运行，生成可复盘的本地 session。

- `record -- <command>` 用于启动并记录一个命令；`record -c/-p` 用于附加到已运行进程
- **自动开启**：SSL 监控 + 进程监控 + 系统监控 + Web 服务器（端口 7395）
- **默认不丢弃事件**：如需过滤请求、响应或 SSL 片段，使用 `debug trace` 的显式过滤选项
- 默认**静默模式**（不输出到底层事件流），数据写入实时 view 和本地 SQLite session

典型用法：

```sh
sudo ./agentsight record -- claude
./agentsight report
```

### debug trace — 完全可控的灵活监控

适用于需要自定义监控范围、过滤规则的调试和分析场景。

- **无必填参数**，所有功能独立开关
- SSL（`--ssl`）、进程（`--process`）默认开启，但可关闭
- 系统监控（`--system`）、stdio 捕获（`--stdio`）、Web 服务器（`--server`）默认**关闭**，需手动开启
- 过滤规则完全由用户通过 `--ssl-filter`、`--http-filter` 自定义
- 默认输出到控制台，可用 `-q` 静默

典型用法：

```sh
sudo ./agentsight debug trace --ssl true --process false --server --http-filter "request.method=POST"
```

## 在前端连接 AgentSight Node

运行下面这个无需 sudo 的命令，在默认托管前端
`https://app.agentsight.us` 打开 Node 数据：

```sh
agentsight bind
```

该命令默认在 `127.0.0.1:7395` 启动 API，打开带认证信息的连接链接，并在前台持续运行。
不传 `--db` 时读取实时进程和本机 agent session index；使用 `--db <capture.db>` 才会明确读取
一次保存的捕获。首屏是机器级实时 `top`：统一显示运行中/已停止
的智能体、观测 Token 用量、数据源报告的订阅容量、Agent Plan、CPU 和 RSS。点击 session 后
可展开对话、进程树与 AI 提示或分析视图。分析视图统一呈现 Token/模型用量、工具/文件/网络影响、
失败、Session 资源和交互式时间线，并保留点击单个事件查看详情的能力；不再提供独立的 raw event
或性能面板。会话详情在有界文本预算内保留最新 1,000 条提示、2,000 条回复和 2,000 条工具事件。
Node 访问密钥保存在操作系统的 AgentSight
配置目录并跨重启复用；连接链接只通过 URL fragment 把密钥交给浏览器，SPA 读取后立即从
地址栏清除。Chrome 可能会请求允许该网页访问本地或私有网络。

使用 `agentsight bind --no-open` 可手动复制链接，使用 `agentsight bind --qr` 可打印
同一个链接的二维码。Local 只是自动发现的默认路径，并不是另一套协议：可以用
`--listen <IP>` 和 `--server-port <PORT>` 选择监听 socket；经过 hostname、tunnel 或
HTTPS reverse proxy 时用 `--endpoint <URL>` 指定浏览器实际访问的 Node URL；用
`--app-url <URL>` 选择自托管静态前端。例如：

```sh
agentsight bind --listen 0.0.0.0 --server-port 7395 \
  --endpoint https://node.example.net \
  --app-url https://agentsight.example.net/
```

监听 `0.0.0.0` 或 `::` 时必须显式提供 `--endpoint`。非 loopback Node 应使用浏览器信任的
HTTPS；私有网络本身不会绕过浏览器 mixed-content 规则。应把访问密钥视为长期凭据：任何
持有者都能在 Node 可达时调用 Node API。Direct 请求不经过 AgentSight Cloud；启用
Controller Relay 时，选中的请求和响应会经过 Cloud runtime，但不会持久化到 D1。登录会在
控制面保存账号、组织和 Node 协调数据。自托管登录还需要把 SPA 的
`NEXT_PUBLIC_CONTROL_PLANE_URL` 指向配套
Worker，并把 Worker 的 `APP_ORIGIN` 设为该 SPA origin。

### 对比总结

| 维度 | record | debug trace |
|------|--------|-------|
| 定位 | 一键录制，预设优化 | 灵活定制，精细控制 |
| 必填参数 | 无；可用 `-- <command>`、`-c <comm>` 或 `-p <pid>` | 无 |
| Web 服务器 | 默认开启，可用 `--no-server` 关闭 | 需 `--server` |
| 系统监控 | 默认开启 | 需 `--system` |
| 控制台输出 | 默认关闭 | 默认开启 |
| 过滤规则 | 默认不过滤 | 用户自定义 |
| 持久化 | 默认 SQLite | 传 `--db` 时写 SQLite |

简单来说：**实时查看用 `top`，保存复盘用 `record`，深度调试用 `debug trace`**。
