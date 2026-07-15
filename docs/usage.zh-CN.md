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
的命令推荐显式使用 `sudo`；`top` 无需 sudo 也能工作，交互式 TUI 只在 sudo 已可用时
启用 live eBPF capture，plain/non-TTY 输出保持 snapshot-only。

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
- **内置过滤规则**：自动过滤掉注册请求（`/v1/rgstr`）、HEAD 请求、空响应体、202 状态码、二进制数据等噪音
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

### 对比总结

| 维度 | record | debug trace |
|------|--------|-------|
| 定位 | 一键录制，预设优化 | 灵活定制，精细控制 |
| 必填参数 | 无；可用 `-- <command>`、`-c <comm>` 或 `-p <pid>` | 无 |
| Web 服务器 | 默认开启，可用 `--no-server` 关闭 | 需 `--server` |
| 系统监控 | 默认开启 | 需 `--system` |
| 控制台输出 | 默认关闭 | 默认开启 |
| 过滤规则 | 内置预设 | 用户自定义 |
| 持久化 | 默认 SQLite | 传 `--db` 时写 SQLite |

简单来说：**实时查看用 `top`，保存复盘用 `record`，深度调试用 `debug trace`**。
