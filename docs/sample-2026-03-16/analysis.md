# AgentSight 数据采集与分析报告

**日期**: 2026-03-16
**抓取目标**: Claude Code v2.1.77、OpenAI Codex v0.114.0
**抓取工具**: AgentSight sslsniff (eBPF uprobe)
**数据文件**: `claude-code-raw.jsonl` (92 事件)、`codex-raw.jsonl` (0 事件，rustls 不兼容)
**用途**: 为数据可视化与分析平台提供完整的字段定义和数据模型参考

---

## 1. 数据模型与完整字段说明

本节详细说明数据采集链路中两个层级的数据结构：sslsniff 原始事件 -> collector.py HTTP 交互。每个层级都列出所有字段、类型、取值范围和语义，为构建数据可视化和分析平台提供完整参考。

### 1.1 数据流全景

```
sslsniff (eBPF)              collector.py                下游存储/分析
┌──────────────┐   JSON    ┌──────────────┐   JSON      ┌──────────────┐
│ SSL_read/    │──stdout──►│ HTTP 配对     │────────────►│ 文件 / 数据库 │
│ SSL_write    │  per-event│ SSE 累积      │  per-event  │ / Web UI 等  │
│ uprobe 事件   │           │ gzip 解压     │             │              │
└──────────────┘           └──────────────┘             └──────────────┘
```

数据经过两层转换：**原始 eBPF 事件 → HTTP interaction**，之后可存入任意后端（文件、数据库、消息队列等）。

### 1.2 sslsniff 原始事件字段（第一层）

每行 JSON，12-13 个字段。以下基于本次 92 个事件的实际统计：

| 字段 | 类型 | 说明 | 本次数据范围 / 统计 |
|------|------|------|---------------------|
| `function` | string | SSL 操作类型。由 eBPF `rw` 字段映射 | `"WRITE/SEND"`: 11 次, `"READ/RECV"`: 81 次。另有 `"HANDSHAKE"` 需 `--handshake` 启用 |
| `timestamp_ns` | int64 | 内核启动后的纳秒时间戳 (`bpf_ktime_get_ns()`) | min=20579921342714, max=20583551460691, 92 个唯一值（每事件唯一） |
| `comm` | string | **线程名**（不是进程名，`bpf_get_current_comm()`，最长 16 字符） | 全部为 `"HTTP Client"`（Claude Code SSL 线程名） |
| `pid` | int | 进程 PID（实际上是内核 tgid） | 唯一值: `60228` |
| `tid` | int | 线程 TID（内核 task pid） | 唯一值: `60244` |
| `uid` | int | 用户 UID | 唯一值: `1000` |
| `len` | int | SSL_read/SSL_write 返回的实际字节数 | min=5, max=66,295, 53 个唯一值, 总计=186,985 字节 |
| `buf_size` | int | 实际拷贝到 eBPF 缓冲区的字节数（受 `MAX_BUF_SIZE` 512KB 限制） | 本次全部等于 `len`（无截断） |
| `latency_ms` | float | SSL 操作本身的耗时（毫秒），精度 0.001ms | min=0.001, max=0.063, mean=0.014, median=0.010 |
| `is_handshake` | bool | 是否为 TLS 握手事件 | 全部 `false`（未启用 `--handshake`） |
| `data` | string | **SSL 解密后的明文数据**。JSON 转义：控制字符用 `\uXXXX`，有效 UTF-8 多字节序列直接输出，无效字节用 `\uXXXX` | HTTP 请求/响应原文（含 gzip 二进制） |
| `truncated` | bool | 数据是否因超过缓冲区大小被截断 | 全部 `false` |
| `bytes_lost` | int | 截断丢失的字节数（仅在 `truncated=true` 时出现） | 本次不存在 |

**关键注意**：
- `comm` 是线程名不是进程名，Claude Code 的 SSL 线程名为 `"HTTP Client"`，所以 `--comm claude` 会丢失所有 SSL 事件
- `data` 包含原始 HTTP 文本（含 gzip 二进制），大请求会拆分成多个事件
- `timestamp_ns` 是 monotonic clock（启动后），不是 wall clock，需要通过 `/proc/stat` 的 `btime` 转换
- `len` 总是等于 `buf_size`（本次 92/92），意味着没有任何数据被截断

**WRITE/SEND 事件拆包行为**：当请求体超过 SSL 库缓冲区时，拆分成多个 `SSL_write` 调用：
- `POST /v1/messages`: 2 个事件 (32,768 + 66,295 = 99,063 字节)
- `POST /api/event_logging/v2/batch`: 2 个事件 (32,768 + 32,612 = 65,380 字节)
- 第一个事件包含 HTTP 请求行+头部+body 开头，后续事件只有 body 续传数据

**READ/RECV 事件特征**：
- SSE 流式响应分散在 65 个 READ/RECV 事件中
- 大部分响应使用 `Content-Encoding: gzip`，data 字段包含 gzip 二进制
- 大小范围: 5 字节（chunked TE 终止标记 `0\r\n\r\n`）到 1,369 字节

### 1.3 collector.py 输出的 HTTP interaction（第二层）

collector.py 的 HTTP 模式（`--mode http`）将多个原始 sslsniff 事件组装成完整的 HTTP 请求-响应交互对，以 JSON 格式输出（可写入文件、发送到任意后端、或通过 Web UI 展示）。

#### 1.3.1 批次信封 (batch envelope)

每批输出的 JSON 结构：

```json
{
  // ─── 批次信封 ───
  "session_id": UUID,           // collector 启动时生成的唯一会话 ID (uuid.uuid4())
  "agent": string,              // "claude-code" (固定字符串)
  "agent_version": string|null, // "2.1.77" (从 --binary-path 路径名自动推断或 --agent-version 指定)
  "uid": int,                   // collector 运行者的 Unix UID (os.getuid())
  "hostname": string,           // collector 运行所在的主机名 (socket.gethostname())
  "collector_mode": string,     // "http" 或 "raw"
  "capture_start": ISO8601,     // collector 启动时间 (UTC)

  // ─── interaction 数组 ───
  "interactions": [...]         // 每批 batch_size 个（默认 5）或每 flush_interval 秒（默认 3）
}
```

#### 1.3.2 单个 interaction 对象

```
{
  "timestamp": ISO8601,       // wall clock 时间（bpf_ktime_get_ns + /proc/stat btime 转换）
  "timestamp_ns": int64,      // 原始内核纳秒时间戳
  "pid": int,                 // 进程 PID
  "tid": int,                 // 线程 TID
  "uid": int,                 // 用户 UID
  "comm": string,             // 线程名

  "request": {
    "method": string,         // "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "OPTIONS" | "HEAD"
    "path": string,           // "/v1/messages?beta=true"（含 query string）
    "headers": {string: string},  // key 已转小写，authorization/x-api-key 替换为 "[REDACTED]"
    "body": object | string   // JSON 解析成功 → object，否则 → string
  },
  "request_size": int,        // 第一个 WRITE/SEND 事件的 len（不含续传）

  "response": {
    "status_code": int,       // 200, 202, 400, 500...
    "status_text": string,    // "OK", "Accepted"...
    "headers": {string: string}, // key 已转小写
    "body": object | string,  // gzip 解压 + chunked 剥离 + JSON 解析后的结果
    "is_sse": bool            // true = Server-Sent Events 流式响应
  },
  "response_size": int,       // SSE 流为所有 READ 事件的 len 累计

  "latency_ms": float,        // 请求到第一个响应的延迟 ((resp_timestamp_ns - req_timestamp_ns) / 1e6)
  "truncated": bool           // 是否有数据被截断
}
```

#### 1.3.3 response.body 处理逻辑

| 条件 | body 结果 |
|------|-----------|
| gzip + 非 SSE | 自动解压 gzip，剥离 chunked framing，尝试 JSON 解析。成功 → object，失败 → string |
| gzip + SSE | 所有 READ/RECV 事件的原始字节累积后一次性 gzip 解压，返回 SSE 文本流 |
| 非 gzip + JSON | 直接 JSON 解析为 object |
| 非 gzip + 非 JSON | 保持为原始 string |
| 解压失败 | `"[gzip binary, decompression failed]"` 或 `"[binary response, not decodable]"` |

#### 1.3.4 collector.py 关键处理逻辑

- 通过 `(pid, tid)` 配对请求和响应，使用 `defaultdict(deque)` 实现 **FIFO 队列**处理并发请求
- SSE 流式响应使用 **`active_streams`** 字典追踪活跃连接，累积后续 READ 数据，在新 WRITE 到来时 finalize
- gzip 响应先 `_strip_chunked_framing()` 剥离 chunked TE，再 `zlib.decompressobj(MAX_WBITS | 16)` 流式解压
- `Authorization` 和 `X-API-Key` 头部自动脱敏为 `[REDACTED]`
- 原始 sslsniff stdout 以 **binary 模式** (`text=False`) + **latin-1 解码**读取，避免 UTF-8 损坏 gzip 数据
- 字符串 body 中的 null 字节 `\x00` 会被替换（部分存储后端不支持 null 字节）

### 1.4 下游存储

collector.py 输出的 interaction JSON 可对接任意存储后端——关系型数据库、文档数据库、消息队列或本地文件均可。核心字段（`session_id`、`timestamp`/`timestamp_ns`、`pid`/`tid`/`uid`/`comm`、请求/响应的 method/path/headers/body/status_code/is_sse/latency_ms/size/truncated）完整保留了抓取到的所有语义，具体的表结构或 schema 设计由各使用方自行决定。

---

## 2. Claude Code 流量数据分析

### 2.1 总体统计

| 指标 | 数值 |
|------|------|
| 总事件数 | 92 |
| WRITE/SEND 事件 | 11 |
| READ/RECV 事件 | 81 |
| 总抓取数据 | 186,985 字节 (182.6 KB) |
| 发送数据量（WRITE） | 173,620 字节 (169.6 KB) |
| 接收数据量（READ） | 13,365 字节 (13.1 KB, gzip 压缩后) |
| 抓取时间跨度 | 3.630 秒 |
| 唯一进程 | 1 个 (PID 60228) |
| 唯一线程 | 1 个 (TID 60244, 线程名 "HTTP Client") |
| 截断事件 | 0 个 |
| SSL 操作延迟 (min/max/mean/median) | 0.001 / 0.063 / 0.014 / 0.010 ms |
| 每事件数据量 (min/max/mean) | 5 / 66,295 / 2,032 字节 |
| `len` == `buf_size` | 92/92 (100%，无截断) |

**11 个 WRITE/SEND 事件明细**：

| # | 目标 API | len (字节) | 备注 |
|---|----------|-----------|------|
| 0 | `GET /v1/mcp_servers?limit=1000` | 442 | 完整请求 |
| 1 | `POST /api/eval/sdk-zAZezfDKGoZuXXKe` | 962 | 完整请求 |
| 2 | `GET /api/claude_code_penguin_mode` | 376 | 完整请求 |
| 3 | `GET /api/oauth/claude_cli/client_data` | 418 | 完整请求 |
| 4 | `GET /api/oauth/account/settings` | 380 | 完整请求 |
| 5 | `GET /api/claude_code_grove` | 390 | 完整请求 |
| 6 | `POST /v1/messages?beta=true` (第 1 部分) | 32,768 | 请求头 + body 开头 |
| 7 | `POST /v1/messages?beta=true` (第 2 部分) | 66,295 | body 续传 |
| 8 | `POST /api/event_logging/v2/batch` (第 1 部分) | 32,768 | 请求头 + body 开头 |
| 9 | `POST /api/event_logging/v2/batch` (第 2 部分) | 32,612 | body 续传 |
| 10 | `POST /api/v2/logs` | 6,209 | 完整请求 |

### 2.2 捕获到的 API 端点

本次抓取捕获了 9 个独立的 HTTP 请求，涉及 2 个目标主机：

#### Anthropic API (`api.anthropic.com`)

| # | 方法 | 路径 | 发送大小 | 用途 |
|---|------|------|----------|------|
| 1 | GET | `/v1/mcp_servers?limit=1000` | 0.4 KB | 获取 MCP 服务器列表 |
| 2 | POST | `/api/eval/sdk-zAZezfDKGoZuXXKe` | 0.9 KB | 获取 feature flags / A-B 测试配置 |
| 3 | GET | `/api/claude_code_penguin_mode` | 0.4 KB | 获取 penguin mode 配置 |
| 4 | GET | `/api/oauth/claude_cli/client_data` | 0.4 KB | 获取 OAuth 客户端数据 |
| 5 | GET | `/api/oauth/account/settings` | 0.4 KB | 获取账户设置 |
| 6 | GET | `/api/claude_code_grove` | 0.4 KB | 获取 grove 配置 |
| 7 | POST | `/v1/messages?beta=true` | 96.7 KB | **核心 API：发送消息给模型** |
| 8 | POST | `/api/event_logging/v2/batch` | 63.8 KB | 发送遥测事件批次 |

#### Datadog (`http-intake.logs.us5.datadoghq.com`)

| # | 方法 | 路径 | 发送大小 | 用途 |
|---|------|------|----------|------|
| 9 | POST | `/api/v2/logs` | 6.1 KB | 发送结构化日志到 Datadog |

#### 数据分类统计

- **核心 API 调用** (`/v1/messages`): 96.7 KB (占发送总量的 57%)
- **遥测数据** (`event_logging` + `v2/logs`): 69.9 KB (占 41%)
- **辅助 API**: 2.9 KB (占 2%)

### 2.3 POST /v1/messages — 完整字段树

这是 Claude Code 与模型交互的核心请求（本次 96.7KB），以下是从实际数据解析出的完整字段树。

#### 请求头（完整字段，可提取的元信息）

```
POST /v1/messages?beta=true HTTP/1.1
Accept: application/json
Authorization: Bearer [REDACTED]
Content-Type: application/json
User-Agent: claude-cli/2.1.77 (external, cli)
X-Stainless-Arch: x64
X-Stainless-Lang: js
X-Stainless-OS: Linux
X-Stainless-Package-Version: 0.74.0
X-Stainless-Retry-Count: 0
X-Stainless-Runtime: node
X-Stainless-Runtime-Version: v24.3.0
X-Stainless-Timeout: 600
anthropic-beta: oauth-2025-04-20,interleaved-thinking-2025-05-14,context-management-2025-06-27,prompt-caching-scope-2026-01-05,claude-code-20250219
anthropic-dangerous-direct-browser-access: true
anthropic-version: 2023-06-01
x-app: cli
Connection: keep-alive
Host: api.anthropic.com
Accept-Encoding: gzip, deflate, br, zstd
Content-Length: 98207
```

| 头部 | 示例值 | 可提取信息 |
|------|--------|-----------|
| `User-Agent` | `claude-cli/2.1.77 (external, cli)` | Claude Code 版本号、用户类型 (external)、入口 (cli) |
| `X-Stainless-Arch` | `x64` | CPU 架构 |
| `X-Stainless-Lang` | `js` | SDK 语言 |
| `X-Stainless-OS` | `Linux` | 操作系统 |
| `X-Stainless-Package-Version` | `0.74.0` | Anthropic JS SDK 版本 |
| `X-Stainless-Retry-Count` | `0` | 当前重试次数（0 = 首次请求） |
| `X-Stainless-Runtime` | `node` | 运行时环境 |
| `X-Stainless-Runtime-Version` | `v24.3.0` | Node.js 版本 |
| `X-Stainless-Timeout` | `600` | 请求超时（秒） |
| `anthropic-beta` | 逗号分隔列表 | 启用的 5 个 beta 特性 |
| `anthropic-dangerous-direct-browser-access` | `true` | 允许直接浏览器访问 |
| `anthropic-version` | `2023-06-01` | API 版本 |
| `x-app` | `cli` | 应用标识 |
| `Content-Length` | `98207` | 请求体大小（字节） |

**anthropic-beta 启用的特性列表**：
1. `oauth-2025-04-20` — OAuth 认证
2. `interleaved-thinking-2025-05-14` — 交错思考模式
3. `context-management-2025-06-27` — 上下文管理
4. `prompt-caching-scope-2026-01-05` — Prompt 缓存范围控制
5. `claude-code-20250219` — Claude Code 专属特性

#### 请求体完整字段树

```
root (POST /v1/messages?beta=true)
├── model: string                    # "claude-haiku-4-5-20251001" — 使用的模型 ID
├── max_tokens: int                  # 32000 — 最大输出 token 数
├── stream: bool                     # true — 是否使用 SSE 流式响应
├── thinking                         # 扩展思考配置
│   ├── budget_tokens: int           # 31999 — 思考预算 token
│   └── type: string                 # "enabled" — 思考模式
├── context_management               # 上下文管理（beta 特性）
│   └── edits[]: array
│       ├── type: string             # "clear_thinking_20251015"
│       └── keep: string             # "all"
├── metadata
│   └── user_id: string              # "user_{hash}_account_{uuid}_session_{uuid}"
│                                    # 包含用户 hash + 账户 UUID + 会话 UUID
├── system[]: array (4 个块)         # System Prompt
│   ├── [0]: {type: "text", text}    # 计费头 "cc_version=2.1.77.e19; cc_entrypoint=cli"
│   ├── [1]: {type: "text", text}    # Agent 身份声明
│   ├── [2]: {type: "text", text,    # 核心行为指令（12,644 字符）
│   │         cache_control: {       # ← 启用 prompt caching
│   │           type: "ephemeral",
│   │           ttl: "1h",
│   │           scope: "global"}}
│   └── [3]: {type: "text", text}    # auto memory 系统 + 项目记忆（12,204 字符）
│
├── tools[]: array (23 个工具)       # 工具定义
│   └── each tool:
│       ├── name: string             # 工具名（如 "Bash", "Read", "Agent"）
│       ├── description: string      # 工具描述
│       └── input_schema: object     # JSON Schema
│           ├── $schema: string
│           ├── type: "object"
│           ├── properties: {name: {type, description, enum?}}
│           ├── required: string[]
│           └── additionalProperties: false
│
└── messages[]: array                # 对话消息
    └── each message:
        ├── role: string             # "user" | "assistant"
        └── content[]: array         # content block 数组
            ├── {type: "text", text} # 用户文本 或 system-reminder 注入
            ├── {type: "tool_use", id, name, input}  # 工具调用
            └── {type: "tool_result", tool_use_id, content}  # 工具结果
```

**23 个工具完整列表（含 input_schema 参数和类型）：**

| 工具名 | required 参数 | optional 参数 (类型) | 用途 |
|--------|--------------|---------------------|------|
| `Agent` | description, prompt | subagent_type(str), model(str), run_in_background(bool), isolation(str) | 启动子代理 |
| `TaskOutput` | task_id, block, timeout | — | 获取后台任务输出 |
| `Bash` | command | timeout(num), description(str), run_in_background(bool), dangerouslyDisableSandbox(bool) | shell 命令 |
| `Glob` | pattern | path(str) | 文件模式匹配 |
| `Grep` | pattern | path(str), glob(str), type(str), output_mode(str), -A(num), -B(num), -C(num), context(num), -i(bool), -n(bool), head_limit(num), offset(num), multiline(bool) | 代码搜索 (ripgrep) |
| `ExitPlanMode` | — | allowedPrompts(array) | 退出计划模式 |
| `Read` | file_path | offset(num), limit(num), pages(str) | 读取文件 |
| `Edit` | file_path, old_string, new_string | replace_all(bool) | 编辑文件 |
| `Write` | file_path, content | — | 写入文件 |
| `NotebookEdit` | notebook_path, new_source | cell_id(str), cell_type(str), edit_mode(str) | 编辑 Notebook |
| `WebFetch` | url, prompt | — | 获取网页 |
| `TodoWrite` | todos | — | 任务清单 |
| `WebSearch` | query | allowed_domains(array), blocked_domains(array) | 网络搜索 |
| `TaskStop` | — | task_id(str), shell_id(str) | 停止任务 |
| `AskUserQuestion` | questions | answers(obj), annotations(obj), metadata(obj) | 向用户提问 |
| `Skill` | skill | args(str) | 执行技能 |
| `EnterPlanMode` | — | — | 进入计划模式 |
| `EnterWorktree` | — | name(str) | 进入 worktree |
| `ExitWorktree` | action | discard_changes(bool) | 退出 worktree |
| `CronCreate` | cron, prompt | recurring(bool) | 创建定时任务 |
| `CronDelete` | id | — | 删除定时任务 |
| `CronList` | — | — | 列出定时任务 |
| `LSP` | operation, filePath, line, character | — | Language Server |

**用户消息的 content blocks**：

| # | type | 长度 | 内容 |
|---|------|------|------|
| 0 | text (system-reminder) | 1,764 字符 | 可用 skills 列表 + deferred tools 列表 |
| 1 | text (system-reminder) | 305 字符 | CLAUDE.md 上下文注入 |
| 2 | text | 69 字符 | 实际用户输入 |

### 2.4 SSE 响应分析

响应使用 `text/event-stream` + `Content-Encoding: gzip` + `Transfer-Encoding: chunked`，分散在 65 个 READ/RECV 事件中，总计 4,200 字节（压缩后）。

#### 响应头（完整列表）

```
HTTP/1.1 200 OK
Date: Tue, 17 Mar 2026 01:11:31 GMT
Content-Type: text/event-stream; charset=utf-8
Transfer-Encoding: chunked
Connection: keep-alive
Cache-Control: no-cache
anthropic-ratelimit-unified-status: allowed
anthropic-ratelimit-unified-5h-status: allowed
anthropic-ratelimit-unified-5h-reset: 1773723600
anthropic-ratelimit-unified-5h-utilization: 0.08
anthropic-ratelimit-unified-7d-status: allowed
anthropic-ratelimit-unified-7d-reset: 1774123200
anthropic-ratelimit-unified-7d-utilization: 0.13
anthropic-ratelimit-unified-representative-claim: five_hour
anthropic-ratelimit-unified-fallback-percentage: 0.5
anthropic-ratelimit-unified-reset: 1773723600
anthropic-ratelimit-unified-overage-disabled-reason: org_level_disabled
anthropic-ratelimit-unified-overage-status: rejected
request-id: req_011CZ7mB5wPBc9sEWjhGgpXc
strict-transport-security: max-age=31536000; includeSubDomains; preload
anthropic-organization-id: [REDACTED_ORG_UUID]
Server: cloudflare
x-envoy-upstream-service-time: 1532
Content-Encoding: gzip
vary: Accept-Encoding
server-timing: proxy;dur=1534
cf-cache-status: DYNAMIC
X-Robots-Tag: none
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
CF-RAY: 9dd81fbec99d5e55-SJC
```

**通用响应头**（所有 Anthropic API 响应共有）：

| 头部 | 说明 |
|------|------|
| `request-id` | Anthropic 请求追踪 ID，格式 `req_{base62}`，用于关联日志和支持工单 |
| `x-envoy-upstream-service-time` | Envoy 代理记录的上游服务处理时间（毫秒） |
| `server-timing` | 服务端 timing，`dur` 为总代理耗时（毫秒） |
| `CF-RAY` | Cloudflare 请求追踪 ID，格式 `{hex_id}-{PoP_code}`，SJC = 圣何塞数据中心 |
| `cf-cache-status` | Cloudflare 缓存状态（`DYNAMIC` = 不缓存） |
| `strict-transport-security` | HSTS 策略（1 年） |

#### 速率限制头（仅 /v1/messages 响应）

| 头部 | 实际值 | 含义 |
|------|--------|------|
| `anthropic-ratelimit-unified-status` | `allowed` | 统一速率限制状态 |
| `anthropic-ratelimit-unified-5h-status` | `allowed` | 5 小时窗口状态 |
| `anthropic-ratelimit-unified-5h-reset` | `1773723600` | 5 小时窗口重置时间 (Unix epoch) |
| `anthropic-ratelimit-unified-5h-utilization` | `0.08` | 5 小时窗口使用率 (8%) |
| `anthropic-ratelimit-unified-7d-status` | `allowed` | 7 天窗口状态 |
| `anthropic-ratelimit-unified-7d-reset` | `1774123200` | 7 天窗口重置时间 (Unix epoch) |
| `anthropic-ratelimit-unified-7d-utilization` | `0.13` | 7 天窗口使用率 (13%) |
| `anthropic-ratelimit-unified-representative-claim` | `five_hour` | 代表性限制窗口 |
| `anthropic-ratelimit-unified-fallback-percentage` | `0.5` | 降级百分比 |
| `anthropic-ratelimit-unified-reset` | `1773723600` | 主要窗口重置时间 |
| `anthropic-ratelimit-unified-overage-status` | `rejected` | 超额请求状态 |
| `anthropic-ratelimit-unified-overage-disabled-reason` | `org_level_disabled` | 超额被禁用的原因 |
| `anthropic-organization-id` | `[REDACTED_ORG_UUID]` | 组织 UUID |

#### SSE 数据恢复情况

由于 JSONL 文件中 gzip 二进制数据经过 UTF-8 JSON 编码时存在精度损失（多字节 UTF-8 序列将 > U+00FF 的 codepoints 引入，导致 latin-1 回转失败），本次数据的 gzip 解压**不完全成功**。

但根据 Datadog 日志中 `tengu_api_success` 事件的元数据，可以确认 SSE 响应包含以下内容：

- **input_tokens**: 10 (实际未缓存的输入 token)
- **cached_input_tokens**: 25,241
- **output_tokens**: 222
- **text_content_length**: 284 字符（模型回复文本）
- **thinking_content_length**: 451 字符（思考过程）
- **stop_reason**: `end_turn`
- **duration_ms**: 3,058 ms (端到端延迟)
- **ttft_ms**: 1,612 ms (首 token 时间)
- **cost_usd**: $0.0036441
- **request_id**: `req_011CZ7mB5wPBc9sEWjhGgpXc`

#### SSE 流完整事件类型和字段

Anthropic SSE 协议中每个事件格式为 `event: {type}\ndata: {json}\n\n`，完整事件类型和 JSON 结构：

**message_start** — 消息开始，包含完整的 message 信封：
```json
{"type": "message_start", "message": {
  "id": "msg_01...",                    // 消息唯一 ID，格式 "msg_{base62}"
  "type": "message", "role": "assistant",
  "content": [],                        // 初始为空，后续通过 delta 填充
  "model": "claude-haiku-4-5-20251001", // 实际使用的模型
  "stop_reason": null, "stop_sequence": null,
  "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 25241, "output_tokens": 1}
}}
```

**content_block_start** — 内容块开始：
```json
// 思考块: {"type":"content_block_start","index":0,"content_block":{"type":"thinking","thinking":""}}
// 文本块: {"type":"content_block_start","index":1,"content_block":{"type":"text","text":""}}
// 工具块: {"type":"content_block_start","index":2,"content_block":{"type":"tool_use","id":"toolu_01...","name":"Bash","input":{}}}
```

**content_block_delta** — 内容块增量：
```json
// 思考: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"..."}}
// 文本: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"..."}}
// 工具JSON: {"type":"content_block_delta","index":2,"delta":{"type":"input_json_delta","partial_json":"..."}}
// 签名: {"type":"content_block_delta","index":1,"delta":{"type":"signature_delta","signature":"..."}}
```

**content_block_stop** — 内容块结束：`{"type":"content_block_stop","index":0}`

**message_delta** — 最终 stop_reason 和 usage：
```json
{"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},
 "usage":{"output_tokens":222}}
```

**message_stop** — 消息结束信号：`{"type":"message_stop"}`

**ping** — 保活心跳：`{"type":"ping"}`

**本次响应的 content block 序列**（根据 tengu_api_success 元数据确认）：

| index | type | 长度 | 说明 |
|-------|------|------|------|
| 0 | thinking | 451 字符 | 模型思考过程 |
| 1 | text | 284 字符 | 模型回复文本 |
| 2 | signature | — | 内容完整性签名 |

### 2.5 辅助 API 调用分析

#### 2.5.1 GET /v1/mcp_servers?limit=1000

- **用途**: 查询用户配置的 MCP (Model Context Protocol) 服务器
- **请求头**: `anthropic-beta: mcp-servers-2025-12-04`，使用 `axios/1.13.4` 客户端
- **响应**: gzip 压缩的 JSON（本次无法解压，但根据上下文应为空列表或已配置的 MCP 服务器列表）

#### 2.5.2 POST /api/eval/sdk-{hash}

- **用途**: 获取 feature flags 和 A/B 测试配置（可能使用 Eppo 或类似的特性管理系统）
- **请求体**:
```json
{
  "attributes": {
    "id": "[REDACTED_USER_HASH]",
    "sessionId": "[REDACTED_SESSION_UUID]",
    "deviceID": "[REDACTED_USER_HASH]",
    "platform": "linux",
    "organizationUUID": "[REDACTED_ORG_UUID]",
    "accountUUID": "[REDACTED_ACCOUNT_UUID]",
    "userType": "external",
    "subscriptionType": "max",
    "rateLimitTier": "default_claude_max_5x",
    "firstTokenTime": 1750700835543,
    "email": "[REDACTED_EMAIL]",
    "appVersion": "2.1.77"
  },
  "forcedVariations": {},
  "forcedFeatures": [],
  "url": ""
}
```

**可提取信息**：用户邮箱、订阅类型 (max)、速率限制层级、组织/账户 UUID、设备 ID

#### 2.5.3 GET /api/claude_code_penguin_mode 和 GET /api/claude_code_grove

- **用途**: 获取 Claude Code 的特殊模式配置（penguin mode、grove 配置）
- **响应**: gzip 压缩的 JSON

#### 2.5.4 GET /api/oauth/claude_cli/client_data

- **用途**: 获取 OAuth 客户端配置
- **响应** (成功解析):
```json
{ "client_data": {} }
```

#### 2.5.5 GET /api/oauth/account/settings

- **用途**: 获取用户账户设置
- **响应**: gzip 压缩的 JSON

#### 2.5.6 POST /api/event_logging/v2/batch

这是 Claude Code 的内部遥测系统，单次批量发送 37 个事件，包含极其丰富的元数据：

**事件类型分布**:

| 事件名 | 数量 | 描述 |
|--------|------|------|
| `tengu_skill_loaded` | 5 | Skill 加载 |
| `tengu_dir_search` | 3 | 目录搜索 |
| `tengu_shell_set_cwd` | 2 | 设置工作目录 |
| `tengu_attachment_compute_duration` | 2 | 附件计算耗时 |
| `tengu_sysprompt_boundary_found` | 2 | System prompt 边界检测 |
| `tengu_api_cache_breakpoints` | 2 | API 缓存断点 |
| `tengu_version_lock_failed` | 1 | 版本锁失败 |
| `tengu_started` | 1 | Claude Code 启动 |
| `tengu_claudeai_mcp_eligibility` | 1 | MCP 资格检查 |
| `tengu_mcp_tools_commands_loaded` | 1 | MCP 工具加载 |
| `tengu_init` | 1 | 初始化完成 |
| `tengu_claudemd__initial_load` | 1 | CLAUDE.md 加载 |
| `tengu_prompt_suggestion_init` | 1 | 提示建议初始化 |
| `tengu_ripgrep_availability` | 1 | ripgrep 可用性检查 |
| `tengu_context_size` | 1 | 上下文大小统计 |
| `tengu_attachments` | 1 | 附件信息 |
| `tengu_input_prompt` | 1 | 用户输入提示 |
| `tengu_memdir_loaded` | 1 | 记忆目录加载 |
| `tengu_tool_search_mode_decision` | 1 | 工具搜索模式决策 |
| `tengu_api_before_normalize` | 1 | API 请求规范化前 |
| `tengu_api_after_normalize` | 1 | API 请求规范化后 |
| `tengu_sysprompt_block` | 1 | System prompt 块信息 |
| `tengu_api_query` | 1 | API 查询参数 |
| `tengu_headless_plugin_install` | 1 | 无头插件安装 |
| `tengu_claudeai_limits_status_changed` | 1 | 用量限制状态变化 |
| `tengu_api_success` | 1 | API 调用成功 |
| `tengu_config_cache_stats` | 1 | 配置缓存统计 |

**批次 JSON 信封结构**：
```json
{"events": [{"event_type": "ClaudeCodeInternalEvent", "event_data": {...}}]}
```

**重要**: `event_data` 中的 `process` 和 `additional_metadata` 字段是 **JSON 字符串**（不是嵌套对象），需要二次 `JSON.parse()` 才能得到结构化数据。

**请求头特征**：
```
User-Agent: claude-code/2.1.77
x-service-name: claude-code
anthropic-beta: oauth-2025-04-20
Content-Length: 64915
```

**每个 event_data 包含的通用字段**:

```json
{
  "event_name": "tengu_*",
  "event_id": "uuid-v4",               // 事件唯一标识
  "client_timestamp": "2026-03-17T01:11:29.959Z",  // 范围: 29.959Z ~ 33.425Z (3.5 秒)
  "session_id": "uuid",
  "model": "claude-opus-4-6[1m]",      // 启动阶段 vs "claude-haiku-4-5-20251001" (API 调用后)
  "user_type": "external",
  "client_type": "cli",
  "entrypoint": "cli",                 // 或 "claude" (tengu_init)
  "device_id": "user_hash",
  "email": "[REDACTED]",
  "is_interactive": false,
  "betas": "...",                       // 观察到 3 个不同值（不同阶段启用不同 beta）
  "auth": {"account_uuid": "...", "organization_uuid": "..."},
  "env": {                             // 见下方完整字段
    "platform": "linux", "arch": "x64", "node_version": "v24.3.0",
    "version": "2.1.77", "terminal": "vscode", ...
  },
  "process": "{\"uptime\":0.154,...}",  // JSON 字符串！需二次解析
  "additional_metadata": "{...}"        // JSON 字符串！需二次解析
}
```

**`tengu_api_success` 事件完整字段**（`additional_metadata` 中 28 个字段）：

| 字段 | 类型 | 示例值 | 含义 |
|------|------|--------|------|
| `rh` | string | `"6575cd9704d635a4"` | 请求 hash |
| `model` | string | `"claude-haiku-4-5-20251001"` | 实际使用的模型 |
| `originalModel` | string | `"claude-haiku-4-5-20251001"` | 原始请求模型（可能被路由改写） |
| `betas` | string | `"oauth-2025-04-20,..."` | 启用的 beta 特性 |
| `stop_reason` | string | `"end_turn"` | 停止原因：`end_turn` / `tool_use` / `max_tokens` |
| `inputTokens` | int | `10` | 非缓存输入 token |
| `cachedInputTokens` | int | `25241` | prompt cache 命中的 token |
| `outputTokens` | int | `222` | 输出 token |
| `durationMs` | int | `3058` | 端到端总耗时（ms） |
| `ttftMs` | int | `1612` | Time To First Token（ms） |
| `costUSD` | float | `0.0036441` | 本次调用费用（美元） |
| `provider` | string | `"firstParty"` | API 提供者 |
| `textContentLength` | int | `284` | 模型回复文本长度（字符） |
| `thinkingContentLength` | int | `451` | 思考过程长度（字符） |
| `attempt` | int | `1` | 重试次数 |
| `permissionMode` | string | `"acceptEdits"` | 用户权限模式 |
| `globalCacheStrategy` | string | `"system_prompt"` | 缓存策略 |
| `turns` | int | `0` | 对话轮次 |
| `userRequests` | int | `1` | 用户请求数 |
| `contentBlocks` | int | `3` | 响应 content block 总数 |
| `thinkingBlocks` | int | `1` | thinking block 数 |
| `textBlocks` | int | `1` | text block 数 |
| `signatureBlocks` | int | `1` | signature block 数 |
| `toolUseBlocks` | int | `0` | tool_use block 数 |
| `staleContextWarning` | bool | `false` | 是否有过期上下文警告 |
| `reasoningEffort` | string | `"auto"` | 推理力度配置 |
| `mcpToolCount` | int | `0` | MCP 工具数 |
| `usedMcpTools` | bool | `false` | 是否使用了 MCP 工具 |
| `usingExtendedThinking` | bool | `true` | 是否使用扩展思考 |
| `hasBetaHeader` | bool | `true` | 是否有 beta header |

**每个遥测事件的通用信封字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event_id` | UUID | 事件唯一 ID |
| `event_name` | string | 事件名（`tengu_*`） |
| `client_timestamp` | ISO8601 | 客户端时间 |
| `session_id` | UUID | Claude Code 会话 ID |
| `model` | string | 当前模型 |
| `user_type` | string | `"external"` / `"internal"` |
| `client_type` | string | `"cli"` |
| `entrypoint` | string | `"cli"` |
| `is_interactive` | bool | 是否交互模式 |
| `device_id` | string | 设备 ID |
| `email` | string | 用户邮箱 |
| `betas` | string | beta 特性列表 |
| `auth.account_uuid` | UUID | 账户 UUID |
| `auth.organization_uuid` | UUID | 组织 UUID |

**`env` 对象字段**（运行环境信息，共 23 个字段）：

| 字段 | 类型 | 实际值 | 说明 |
|------|------|--------|------|
| `platform` | string | `"linux"` | 操作系统 |
| `platform_raw` | string | `"linux"` | 原始平台标识 |
| `arch` | string | `"x64"` | CPU 架构 |
| `node_version` | string | `"v24.3.0"` | Node.js 版本 |
| `version` | string | `"2.1.77"` | Claude Code 版本 |
| `version_base` | string | `"2.1.77"` | 基础版本号 |
| `build_time` | string | `"2026-03-16T22:15:57Z"` | 构建时间 |
| `deployment_environment` | string | `"unknown-linux"` | 部署环境 |
| `terminal` | string | `"vscode"` | 终端环境 |
| `linux_distro_id` | string | `"ubuntu"` | Linux 发行版 |
| `linux_distro_version` | string | `"24.04"` | 发行版版本 |
| `linux_kernel` | string | `"6.15.11-061511-generic"` | 内核版本 |
| `package_managers` | string | `"npm,yarn,pnpm"` | 检测到的包管理器 |
| `runtimes` | string | `"node"` | 检测到的运行时 |
| `vcs` | string | `"git"` | 版本控制系统 |
| `is_ci` | bool | `false` | 是否在 CI 环境 |
| `is_claubbit` | bool | `false` | 内部标记 |
| `is_claude_ai_auth` | bool | `true` | 是否使用 Claude AI 认证 |
| `is_claude_code_action` | bool | `false` | 是否作为 GitHub Action |
| `is_claude_code_remote` | bool | `false` | 是否远程运行 |
| `is_conductor` | bool | `false` | 是否为 conductor 模式 |
| `is_github_action` | bool | `false` | 是否在 GitHub Action 中 |
| `is_local_agent_mode` | bool | `false` | 是否为本地 agent 模式 |
| `is_running_with_bun` | bool | `true` | 是否使用 Bun 运行时 |

**`process` 对象字段**（JSON 字符串，需二次解析。进程指标随时间变化）：

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `uptime` | float | 0.154 ~ 3.620 秒 | 进程运行时间 |
| `rss` | int | 295.7 ~ 320.9 MB | 常驻内存集大小（字节） |
| `heapTotal` | int | 35.5 ~ 37.0 MB | V8 堆总大小 |
| `heapUsed` | int | 34.0 ~ 83.8 MB | V8 堆已用大小 |
| `external` | int | 12.3 ~ 52.1 MB | V8 外部内存 |
| `arrayBuffers` | int | 399 ~ 14.5 MB | ArrayBuffer 大小 |
| `constrainedMemory` | int | 134.5 GB | 受限内存上限（系统总内存） |
| `cpuUsage.user` | int | 171,026 ~ 461,946 | 用户态 CPU 时间（微秒） |
| `cpuUsage.system` | int | 78,426 ~ 156,559 | 内核态 CPU 时间（微秒） |

**遥测事件时间线与进程指标变化**：

| 阶段 | uptime (秒) | RSS (MB) | 关键事件 |
|------|-------------|----------|----------|
| 启动 | 0.154-0.155 | 295.7-295.9 | version_lock_failed, dir_search(x2), started, shell_set_cwd |
| MCP 检查 | 0.302-0.322 | 297.9-314.1 | mcp_eligibility, mcp_tools_loaded, init, claudemd_load, context_size |
| 用户输入处理 | 0.548-0.561 | 308.6-312.7 | shell_set_cwd, input_prompt, skill_loaded(x5), api_query, cache_breakpoints |
| 插件加载 | 0.567 | 313.2 | headless_plugin_install |
| API 响应处理 | 3.619-3.620 | 320.7-320.9 | limits_status_changed, **api_success**, config_cache_stats |

**`tengu_context_size` 事件** 提供上下文统计：

| 字段 | 值 |
|------|-----|
| `git_status_size` | 615 |
| `claude_md_size` | 0 |
| `total_context_size` | 615 |
| `project_file_count_rounded` | 100 |
| `non_mcp_tools_count` | 24 |
| `non_mcp_tools_tokens` | 4,309 |
| `mcp_tools_count` | 0 |

**每种事件类型的 `additional_metadata` 关键字段**（JSON 字符串二次解析后）：

所有事件共有 `rh` 字段（运行时哈希，如 `"6575cd9704d635a4"`）。以下仅列出各事件的特有字段：

| 事件名 | 关键 additional_metadata 字段 |
|--------|------------------------------|
| `tengu_version_lock_failed` | `is_lifetime_lock`(bool), `is_pid_based`(bool) |
| `tengu_dir_search` | `subdir`(str: "commands"/"agents"/"output-styles"), `durationMs`(int), `userFilesFound`(int), `projectFilesFound`(int) |
| `tengu_started` | （仅 rh） |
| `tengu_shell_set_cwd` | `success`(bool) |
| `tengu_claudeai_mcp_eligibility` | `state`(str: "eligible") |
| `tengu_mcp_tools_commands_loaded` | `tools_count`(int), `commands_count`(int) |
| `tengu_init` | `hasInitialPrompt`(bool), `inputFormat`(str), `outputFormat`(str), `permissionMode`(str: "acceptEdits"), `thinkingType`(str: "adaptive"), `mcpClientCount`(int), `numAllowedTools`(int), `numDisallowedTools`(int), `autoUpdatesChannel`(str), `debug`(bool), `verbose`(bool), `worktree`(bool), `entrypoint`(str: "claude") |
| `tengu_claudemd__initial_load` | `file_count`(int), `total_content_length`(int), `duration_ms`(int), `user_count`(int), `project_count`(int), `automem_count`(int), `teammem_count`(int) |
| `tengu_prompt_suggestion_init` | `enabled`(bool), `source`(str: "growthbook") |
| `tengu_ripgrep_availability` | `working`(int), `using_system`(int) |
| `tengu_attachment_compute_duration` | `label`(str: "plan_mode"/"plan_mode_exit"), `attachment_count`(int), `attachment_size_bytes`(int), `duration_ms`(int) |
| `tengu_attachments` | `attachment_types`(array: ["skill_listing"]) |
| `tengu_input_prompt` | `is_keep_going`(bool), `is_negative`(bool) |
| `tengu_memdir_loaded` | `memory_type`(str: "auto"), `total_file_count`(int), `total_subdir_count`(int) |
| `tengu_skill_loaded` | `skill_source`(str: "bundled"), `skill_loaded_from`(str), `skill_budget`(int: 16000) |
| `tengu_tool_search_mode_decision` | `mode`(str: "standard"), `reason`(str: "model_unsupported"), `enabled`(bool), `checkedModel`(str), `mcpToolCount`(int) |
| `tengu_api_before_normalize` | `preNormalizedMessageCount`(int: 3) |
| `tengu_api_after_normalize` | `postNormalizedMessageCount`(int: 1) |
| `tengu_sysprompt_boundary_found` | `blockCount`(int: 4), `staticBlockLength`(int: 12644), `dynamicBlockLength`(int: 12204) |
| `tengu_sysprompt_block` | `length`(int: 80), `hash`(str: SHA-256), `snippet`(str: "x-anthropic-billing-") |
| `tengu_api_cache_breakpoints` | `cachingEnabled`(bool), `skipCacheWrite`(bool), `totalMessageCount`(int) |
| `tengu_api_query` | `model`(str), `messagesLength`(int), `temperature`(int: 1), `thinkingType`(str), `fastMode`(bool), `provider`(str: "firstParty"), `permissionMode`(str), `querySource`(str: "sdk"), `queryDepth`(int: 0), `queryChainId`(UUID), `buildAgeMins`(int: 175) |
| `tengu_headless_plugin_install` | `marketplaces_installed`(int: 0), `delisted_count`(int: 0) |
| `tengu_claudeai_limits_status_changed` | `status`(str: "allowed"), `hoursTillReset`(int: 4), `unifiedRateLimitFallbackAvailable`(bool) |
| `tengu_config_cache_stats` | `cache_hits`(int: 323), `cache_misses`(int: 3), `hit_rate`(float: 0.9908) |

#### 2.5.7 POST /api/v2/logs (Datadog)

Claude Code 直接将日志发送到 Datadog (`http-intake.logs.us5.datadoghq.com`)。本次捕获了 3 条日志：

| # | message | model | 关键 tags |
|---|---------|-------|-----------|
| 1 | `tengu_started` | `claude-opus-4-6` | `subscription_type:max, version:2.1.77` |
| 2 | `tengu_init` | `claude-haiku-4-5` | `has_initial_prompt:True, thinking_type:adaptive` |
| 3 | `tengu_api_success` | `claude-haiku-4-5` | `cost_u_s_d:0.0036441, stop_reason:end_turn, ttft_ms:1612` |

**请求头特征**：`User-Agent: axios/1.13.4`, `dd-api-key: [REDACTED]`, `Host: http-intake.logs.us5.datadoghq.com`

**Datadog 日志记录完整字段**（每条日志是一个扁平 JSON 对象）：

| 字段类别 | 字段名 | 类型 | 说明 |
|----------|--------|------|------|
| DD 标准 | `message` | string | 日志消息 = 事件名 |
| DD 标准 | `ddsource` | string | `"nodejs"` |
| DD 标准 | `service` | string | `"claude-code"` |
| DD 标准 | `env` | string | `"external"` (= user_type) |
| DD 标准 | `hostname` | string | `"claude-code"` (固定值) |
| DD 标准 | `ddtags` | string | 逗号分隔的标签: `event:{name},arch:x64,model:{m},platform:linux,...` |
| 会话 | `session_id` | string | Claude Code 会话 UUID |
| 版本 | `model` | string | 模型标识（简化版: `"claude-haiku-4-5"`） |
| 版本 | `version` | string | `"2.1.77"` |
| 版本 | `build_time` | string | 构建时间 |
| 用户 | `user_type` | string | `"external"` |
| 用户 | `user_bucket` | int | `1`（用于抽样/A-B 测试分桶） |
| 用户 | `subscription_type` | string | `"max"` |
| 用户 | `is_interactive` | string | `"false"` （注意：是 string 不是 bool！） |
| 环境 | `platform`, `arch`, `terminal`, `linux_*` | string | 同 event_logging 的 env 对象 |
| 环境 | `is_ci`, `is_claude_ai_auth`, ... | bool | 同 event_logging 的 env 布尔字段 |
| SWE-bench | `swe_bench_instance_id`, `swe_bench_run_id`, `swe_bench_task_id` | string | SWE-bench 相关（本次为空） |
| 指标 | `process_metrics` | object | 进程指标（同 event_logging 的 process，但这里是**嵌套对象**不是 JSON 字符串） |
| 指标 | `process_metrics.cpuPercent` | float | CPU 使用率百分比（仅部分日志有） |
| 事件特定 | （因事件而异） | — | 与 event_logging 的 additional_metadata 对应，但 key 用 **snake_case** |

**注意**: Datadog 日志的字段名使用 **snake_case**（如 `cached_input_tokens`, `cost_u_s_d`），而 event_logging 的 additional_metadata 使用 **camelCase**（如 `cachedInputTokens`, `costUSD`）。

**Datadog 响应**: `HTTP/1.1 202 Accepted`, body = `{}`

### 2.6 辅助 GET API 的 User-Agent 差异

不同 API 使用了不同的 HTTP 客户端：

| API 路径 | User-Agent | HTTP 客户端 |
|----------|-----------|-------------|
| `/v1/mcp_servers` | `axios/1.13.4` | axios |
| `/api/eval/sdk-*` | `Bun/1.3.11` | Bun 原生 fetch |
| `/api/claude_code_penguin_mode` | `axios/1.13.4` | axios |
| `/api/oauth/claude_cli/client_data` | `claude-code/2.1.77` | 自定义 |
| `/api/oauth/account/settings` | `claude-code/2.1.77` | 自定义 |
| `/api/claude_code_grove` | `claude-cli/2.1.77 (external, cli)` | Stainless SDK |
| `/v1/messages` | `claude-cli/2.1.77 (external, cli)` | Stainless SDK (带 X-Stainless-* 头) |
| `/api/event_logging/v2/batch` | `claude-code/2.1.77` | 自定义 |
| `/api/v2/logs` (Datadog) | `axios/1.13.4` | axios |

这说明 Claude Code 内部使用了至少 3 种不同的 HTTP 客户端：Stainless SDK、axios、Bun 原生 fetch。

---

## 3. AgentSight 完整数据采集能力

> 以下内容全部基于 AgentSight 最新版 master 分支源码的实际实现，不包含任何泛泛的 eBPF 理论猜测。

### 3.1 eBPF 探针清单

AgentSight 共实现了 **5 个独立的 eBPF/用户态程序**，分布在 `bpf/` 目录下：

| # | 程序名 | 源文件 | 探针类型 | 用途概述 |
|---|--------|--------|----------|----------|
| 1 | **sslsniff** | `sslsniff.bpf.c` + `sslsniff.c` | uprobe/uretprobe | SSL/TLS 明文流量捕获（OpenSSL, BoringSSL, GnuTLS, NSS） |
| 2 | **process** | `process.bpf.c` + `process.c` | tracepoint + uprobe | 进程生命周期、文件操作、bash 命令捕获 |
| 3 | **process_new** | `process_new.bpf.c` + `process_new.c` | tracepoint + kprobe + uprobe | 增强版进程追踪 + 文件系统变更 + 网络 + 信号 + 内存 + 资源采样 |
| 4 | **browsertrace** | `browsertrace.bpf.c` + `browsertrace.c` | uprobe/uretprobe | 浏览器(Chrome/Firefox)明文 HTTP 流量捕获 |
| 5 | **stdiocap** | `stdiocap.bpf.c` + `stdiocap.c` | tracepoint | 进程 stdin/stdout/stderr 负载捕获（用于本地 MCP 服务器） |

此外，Rust collector 中还有一个**纯用户态**的数据源：

| # | Runner 名 | 源文件 | 类型 | 用途概述 |
|---|-----------|--------|------|----------|
| 6 | **SystemRunner** | `collector/src/framework/runners/system.rs` | 用户态轮询 `/proc` | CPU/内存/线程等系统资源周期采样 |

---

### 3.2 sslsniff 详细字段说明

**源码位置**: `bpf/sslsniff.bpf.c`, `bpf/sslsniff.h`, `bpf/sslsniff.c`

#### 3.2.1 eBPF 内核态探针列表

| SEC 名称 | 探针类型 | 挂钩目标 | 功能 |
|----------|----------|----------|------|
| `uprobe/do_handshake` | uprobe | `SSL_read`/`SSL_write`/`SSL_do_handshake` 入口 | 记录缓冲区地址和起始时间戳 |
| `uretprobe/SSL_read` | uretprobe | `SSL_read` 返回 | 捕获读取的明文数据 |
| `uretprobe/SSL_write` | uretprobe | `SSL_write` 返回 | 捕获写入的明文数据 |
| `uprobe/SSL_write_ex` | uprobe | `SSL_write_ex` 入口 | 记录缓冲区、readbytes 指针 |
| `uprobe/SSL_read_ex` | uprobe | `SSL_read_ex` 入口 | 记录缓冲区、readbytes 指针 |
| `uretprobe/SSL_write_ex` | uretprobe | `SSL_write_ex` 返回 | 通过 readbytes 指针获取实际写入字节数 |
| `uretprobe/SSL_read_ex` | uretprobe | `SSL_read_ex` 返回 | 通过 readbytes 指针获取实际读取字节数 |
| `uprobe/do_handshake` (handshake enter) | uprobe | `SSL_do_handshake` 入口 | 记录握手开始时间 |
| `uretprobe/do_handshake` (handshake exit) | uretprobe | `SSL_do_handshake` 返回 | 捕获握手完成事件和耗时 |

用户态 (`sslsniff.c`) 还会尝试附着到：
- **OpenSSL**: `SSL_read`, `SSL_write`, `SSL_read_ex`, `SSL_write_ex`, `SSL_do_handshake`
- **GnuTLS**: `gnutls_record_recv`, `gnutls_record_send`（可用 `--no-gnutls` 禁用）
- **NSS**: `PR_Read`, `PR_Write`（可用 `--no-nss` 禁用）
- **BoringSSL (stripped)**: 当 `--binary-path` 指定时，通过**字节模式匹配**自动定位无符号二进制中的 SSL 函数偏移

#### 3.2.2 内核数据结构

定义在 `bpf/sslsniff.h`：

```c
#define MAX_BUF_SIZE (512 * 1024)  // 512KB
#define RING_BUFFER_SIZE (2 * 1024 * 1024)  // 2MB

struct probe_SSL_data_t {
    __u64 timestamp_ns;   // bpf_ktime_get_ns() 内核启动后纳秒
    __u64 delta_ns;       // SSL 操作耗时（纳秒）
    __u32 pid;            // 进程 PID (tgid)
    __u32 tid;            // 线程 TID (内核 task pid)
    __u32 uid;            // 用户 UID
    __u32 len;            // SSL_read/SSL_write 返回的实际数据长度
    __u32 buf_size;       // 实际拷贝到 buf 的字节数（受 MAX_BUF_SIZE 限制）
    int buf_filled;       // 1=数据有效, 0=读取失败
    int rw;               // 0=READ, 1=WRITE, 2=HANDSHAKE
    char comm[16];        // 线程名 (bpf_get_current_comm)
    __u8 buf[MAX_BUF_SIZE]; // 明文数据缓冲区
    int is_handshake;     // true=TLS 握手事件
};
```

#### 3.2.3 JSON 输出字段（`sslsniff.c` print_event 函数）

sslsniff 用户态程序将内核事件格式化为 JSON，输出到 stdout，每行一个事件：

| 字段 | JSON 类型 | 来源 | 说明 |
|------|-----------|------|------|
| `function` | string | `rw` 字段映射 | `"READ/RECV"`, `"WRITE/SEND"`, 或 `"HANDSHAKE"` |
| `timestamp_ns` | uint64 | `timestamp_ns` | `bpf_ktime_get_ns()` 内核启动后纳秒时间戳 |
| `comm` | string | `comm[16]` | 线程名（注意：不是进程名！Claude SSL 线程名为 `"HTTP Client"`） |
| `pid` | int | `pid` | 进程 PID (实际上是 tgid) |
| `len` | int | `len` | 本次 SSL 操作的实际数据长度（字节） |
| `buf_size` | uint | `buf_size` | 实际拷贝到缓冲区的字节数（<= 512KB） |
| `uid` | int | `uid` | 用户 UID |
| `tid` | int | `tid` | 线程 TID |
| `latency_ms` | float | `delta_ns / 1e6` | SSL 操作耗时（毫秒），精度到 0.001ms |
| `is_handshake` | bool | `is_handshake` | 是否为 TLS 握手事件 |
| `data` | string/null | `buf[]` | SSL 解密后的明文数据。JSON 转义处理：`\n`, `\r`, `\t`, `\\`, `\"`, `\uXXXX`（控制字符）。有效 UTF-8 多字节序列直接输出，无效字节用 `\uXXXX` 转义。 |
| `truncated` | bool | `buf_size < len` | 数据是否因超过 512KB 被截断 |
| `bytes_lost` | int | `len - buf_size` | 截断时丢失的字节数（仅在 `truncated=true` 时出现） |

**示例输出**：
```json
{"function":"WRITE/SEND","timestamp_ns":20579921342714,"comm":"HTTP Client","pid":60228,"len":442,"buf_size":442,"uid":1000,"tid":60244,"latency_ms":0.006,"is_handshake":false,"data":"GET /v1/mcp_servers?limit=1000 HTTP/1.1\r\nAccept: ...","truncated":false}
```

**握手事件特殊性**（`is_handshake=true`）：
- `rw` 固定为 2，`function` 为 `"HANDSHAKE"`
- `data` 为 null（`buf_filled=0`），握手不捕获数据内容
- `len` 为 `SSL_do_handshake()` 的返回值（1=成功）
- `delta_ns` 为握手耗时
- 需要 `--handshake` 参数启用，默认不输出

#### 3.2.4 sslsniff 数据量限制

- 每个事件最大捕获 **512KB** 数据（`MAX_BUF_SIZE = 512 * 1024`，定义在 `sslsniff.h`）
- Ring buffer 大小 2MB
- 超大请求/响应体被 SSL 库拆分成多次 `SSL_write`/`SSL_read` 调用，每次调用产生独立事件
- Rust collector 的 `SSEProcessor` analyzer 可自动合并 SSE 流式响应的多个事件

#### 3.2.5 sslsniff 完整命令行参数

```
sslsniff [OPTIONS]
  --binary-path=PATH    附着到特定二进制（如 Node.js, Claude Code），支持 BoringSSL 字节模式匹配
  -c, --comm=COMMAND    按线程名过滤（bpf_get_current_comm）
  -g, --no-gnutls       不挂钩 GnuTLS 函数
  -h, --handshake       输出 TLS 握手事件
  -n, --no-nss          不挂钩 NSS 函数
  -o, --no-openssl      不挂钩 OpenSSL 函数
  -p, --pid=PID         按进程 PID 过滤（内核态过滤，高效）
  -u, --uid=UID         按用户 UID 过滤（内核态过滤）
  -v, --verbose         详细调试输出（输出到 stderr）
```

---

### 3.3 进程追踪器 (process tracer)

AgentSight 有两个进程追踪程序：基础版 `process` 和增强版 `process_new`。

#### 3.3.1 基础版 process

**源码位置**: `bpf/process.bpf.c`, `bpf/process.h`, `bpf/process.c`

**探针列表**：

| SEC 名称 | 探针类型 | 挂钩点 | 功能 |
|----------|----------|--------|------|
| `tp/sched/sched_process_exec` | tracepoint | 进程 exec | 捕获进程启动，含完整命令行参数 |
| `tp/sched/sched_process_exit` | tracepoint | 进程退出 | 捕获进程退出，含退出码和生命时长 |
| `tp/syscalls/sys_enter_openat` | tracepoint | openat 系统调用 | 捕获文件打开操作，含文件路径和 flags |
| `tp/syscalls/sys_enter_open` | tracepoint | open 系统调用 | 捕获文件打开操作（旧式） |
| `uretprobe//usr/bin/bash:readline` | uretprobe | bash readline | 捕获 bash 用户输入的命令 |

**内核数据结构** (`process.h`)：

```c
enum event_type {
    EVENT_TYPE_PROCESS = 0,        // 进程 exec/exit
    EVENT_TYPE_BASH_READLINE = 1,  // bash 命令
    EVENT_TYPE_FILE_OPERATION = 2, // 文件操作
};

struct event {
    enum event_type type;
    int pid;                          // 进程 PID
    int ppid;                         // 父进程 PID
    unsigned exit_code;               // 退出码
    unsigned long long duration_ns;   // 生命时长（纳秒）
    unsigned long long timestamp_ns;  // 内核启动后纳秒
    char comm[16];                    // 进程名
    char full_command[256];           // 完整命令行（含参数，null 字节替换为空格）
    union {
        char filename[127];           // exec 的二进制路径
        char command[256];            // bash readline 的命令
        struct {                      // 文件操作
            char filepath[127];       // 文件路径
            int fd;                   // 文件描述符
            int flags;                // open flags
            bool is_open;             // true=open, false=close
        } file_op;
    };
    bool exit_event;                  // true=进程退出, false=进程启动
};
```

**JSON 输出字段**（对应三种事件类型）：

**进程启动事件** (`exit_event=false`, `type=PROCESS`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | `"EXEC"` |
| `timestamp` | uint64 | 纳秒时间戳 |
| `pid` | int | 进程 PID |
| `ppid` | int | 父进程 PID |
| `comm` | string | 进程名 (16字符) |
| `filename` | string | 可执行文件路径 (127字符) |
| `full_command` | string | 完整命令行含参数 (256字符) |

**进程退出事件** (`exit_event=true`, `type=PROCESS`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | `"EXIT"` |
| `timestamp` | uint64 | 纳秒时间戳 |
| `pid` | int | 进程 PID |
| `ppid` | int | 父进程 PID |
| `comm` | string | 进程名 |
| `exit_code` | uint | 退出码 |
| `duration_ns` | uint64 | 进程生命时长（纳秒） |

**文件操作事件** (`type=FILE_OPERATION`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | `"FILE_OPEN"` |
| `timestamp` | uint64 | 纳秒时间戳 |
| `pid` | int | 进程 PID |
| `comm` | string | 进程名 |
| `filepath` | string | 文件路径 (127字符) |
| `flags` | int | open flags（O_RDONLY, O_WRONLY 等） |

**Bash 命令事件** (`type=BASH_READLINE`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | `"BASH_READLINE"` |
| `timestamp` | uint64 | 纳秒时间戳 |
| `pid` | int | bash 进程 PID |
| `comm` | string | `"bash"` |
| `command` | string | 用户输入的 bash 命令 (256字符) |

#### 3.3.2 增强版 process_new

**源码位置**: `bpf/process_new.bpf.c`, `bpf/process_new.h`, `bpf/process_ext/*.h`

process_new 在 process 的基础上增加了以下模块，所有新模块使用**聚合映射** (`event_agg_map`) 而非逐事件输出，由用户态周期性刷新：

**新增探针列表**（按模块分组）：

**文件系统变更模块** (`process_ext/bpf_fs.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `tp/syscalls/sys_enter_unlinkat` | tracepoint | `FILE_DELETE` (10) | 文件删除 |
| `tp/syscalls/sys_enter_unlink` | tracepoint | `FILE_DELETE` (10) | 文件删除 (旧式) |
| `tp/syscalls/sys_enter_renameat2` | tracepoint | `FILE_RENAME` (11) | 文件重命名 |
| `tp/syscalls/sys_enter_renameat` | tracepoint | `FILE_RENAME` (11) | 文件重命名 |
| `tp/syscalls/sys_enter_rename` | tracepoint | `FILE_RENAME` (11) | 文件重命名 (旧式) |
| `tp/syscalls/sys_enter_mkdirat` | tracepoint | `DIR_CREATE` (12) | 目录创建 |
| `tp/syscalls/sys_enter_mkdir` | tracepoint | `DIR_CREATE` (12) | 目录创建 (旧式) |
| `tp/syscalls/sys_enter_ftruncate` | tracepoint | `FILE_TRUNCATE` (13) | 文件截断 |
| `tp/syscalls/sys_enter_chdir` | tracepoint | `CHDIR` (14) | 工作目录变更 |

**写操作模块** (`process_ext/bpf_write.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `tp/syscalls/sys_enter_write` + `sys_exit_write` | tracepoint | `WRITE` (15) | write 系统调用字节数聚合 |
| `tp/syscalls/sys_enter_pwrite64` + `sys_exit_pwrite64` | tracepoint | `WRITE` (15) | pwrite64 字节数聚合 |
| `tp/syscalls/sys_enter_writev` + `sys_exit_writev` | tracepoint | `WRITE` (15) | writev 字节数聚合 |

**网络模块** (`process_ext/bpf_net.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `tp/syscalls/sys_enter_bind` | tracepoint | `NET_BIND` (20) | 端口绑定，记录 `A.B.C.D:PORT` |
| `tp/syscalls/sys_enter_listen` | tracepoint | `NET_LISTEN` (21) | 端口监听 |
| `tp/syscalls/sys_enter_connect` | tracepoint | `NET_CONNECT` (22) | 网络连接，记录目标 `A.B.C.D:PORT` |

**信号/进程协调模块** (`process_ext/bpf_signals.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `tp/syscalls/sys_enter_setpgid` | tracepoint | `PGRP_CHANGE` (30) | 进程组变更 |
| `tp/syscalls/sys_enter_setsid` | tracepoint | `SESSION_CREATE` (31) | 会话创建 |
| `tp/syscalls/sys_enter_kill` | tracepoint | `SIGNAL_SEND` (32) | 信号发送，记录目标 PID 和信号号 |
| `tp/sched/sched_process_fork` | tracepoint | `PROC_FORK` (33) | 进程 fork 计数 |

**内存模块** (`process_ext/bpf_mem.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `tp/syscalls/sys_enter_mmap` | tracepoint | `MMAP_SHARED` (40) | MAP_SHARED 共享内存映射 |

**CoW 页错误模块** (`process_ext/bpf_cow.h`)：

| SEC 名称 | 探针类型 | 事件类型 | 功能 |
|----------|----------|----------|------|
| `kprobe/do_wp_page` | kprobe | `COW_FAULT` (41) | Copy-on-Write 页错误计数 |

**聚合数据结构** (`process_new.h`)：

```c
struct agg_key {
    __u32 pid;
    __u32 event_type;        // 上表中的事件类型 ID
    char detail[64];         // 聚合键详情（如 "fd=3", "1.2.3.4:443", "target=1234,sig=9"）
};

struct agg_value {
    __u64 count;             // 事件发生次数
    __u64 total_bytes;       // 累计字节数（仅 write/mmap 使用）
    __u64 first_ts;          // 首次发生时间
    __u64 last_ts;           // 最后发生时间
    char comm[16];           // 进程名
    char extra[127];         // 额外信息（如完整文件路径）
};
```

**聚合 SUMMARY 事件的 JSON 输出**（由 `map_flush.h` 中的 `print_summary_json` 生成）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | uint64 | 最后发生时间 (纳秒) |
| `event` | string | 固定为 `"SUMMARY"` |
| `comm` | string | 进程名 |
| `pid` | uint32 | 进程 PID |
| `type` | string | 事件类型名（如 `"FILE_DELETE"`, `"NET_CONNECT"`, `"SIGNAL_SEND"` 等） |
| `detail` | string | 聚合键（如 `"1.2.3.4:443"`, `"fd=5"`, `"target=1234,sig=9"`）。WRITE 类型会尝试通过 `/proc/<pid>/fd/<N>` 解析为文件路径 |
| `count` | uint64 | 事件发生次数 |
| `total_bytes` | uint64 | 累计字节数（仅 WRITE/MMAP_SHARED 有此字段） |
| `fd` | int | 文件描述符（仅 WRITE 类型） |
| `path_resolved` | bool | fd 是否成功解析为路径（仅 WRITE 类型） |
| `extra` | string | 额外信息，如完整文件路径 |

**进程退出时的内存信息**：

process_new 在进程退出时通过 `exit_mem` BPF 映射记录峰值 RSS（`task->signal->maxrss`），用户态在 EXIT 事件中附加 `peak_rss_kb` 字段。

**过滤功能**：

| 功能标志 | 编译时变量 | 说明 |
|---------|-----------|------|
| PID 过滤 | `filter_pids` + `tracked_pids` map | 只追踪指定 PID 集合 |
| cgroup 过滤 | `filter_cgroup` + `target_cgroup_id` | 只追踪指定 cgroup（支持子 cgroup 递归过滤） |
| 文件系统变更 | `trace_fs_mutations` | 启用文件删除/重命名/目录创建等追踪 |
| 网络追踪 | `trace_network` | 启用 bind/listen/connect 追踪 |
| 信号追踪 | `trace_signals` | 启用 kill/fork/setpgid/setsid 追踪 |
| 内存追踪 | `trace_memory` | 启用 MAP_SHARED mmap 追踪 |
| CoW 追踪 | `trace_cow` | 启用 CoW 页错误追踪 |

---

### 3.4 资源采样器 (resource sampler)

**源码位置**: `bpf/process_ext/resource_sampler.h`, `bpf/process_ext/mem_info.h`

资源采样器是**用户态**组件（非 eBPF），内嵌在 process_new 程序中，通过周期性读取 `/proc` 文件系统来采集指标。

#### 3.4.1 采集方式

- 通过 `/proc/<pid>/stat` 读取每个进程的 CPU 时间和 RSS
- 通过 `/proc/<pid>/statm` 和 `/proc/<pid>/status` 读取详细内存信息
- 通过 `/proc/<pid>/cgroup` 检测 cgroup v2 路径
- 从 cgroup 控制器读取 `memory.current`, `memory.peak`, `cpu.stat`
- 通过 `/proc` 目录扫描递归发现目标 PID 的所有子进程（最多 10 层深度、4096 个 PID）

#### 3.4.2 输出字段

**RESOURCE_SAMPLE 事件**（聚合）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | uint64 | `CLOCK_MONOTONIC` 纳秒 |
| `event` | string | `"RESOURCE_SAMPLE"` |
| `target_pid` | int | 目标根进程 PID |
| `total_rss_kb` | long | 进程树总 RSS (KB) |
| `total_cpu_user_ms` | uint64 | 进程树总用户态 CPU 时间 (ms) |
| `total_cpu_sys_ms` | uint64 | 进程树总内核态 CPU 时间 (ms) |
| `num_processes` | int | 进程树中的进程数 |
| `cgroup_memory_bytes` | int64 | cgroup 当前内存 (字节，可选) |
| `cgroup_memory_peak_bytes` | int64 | cgroup 峰值内存 (字节，可选) |
| `cgroup_cpu_usage_usec` | int64 | cgroup CPU 使用时间 (微秒，可选) |

**RESOURCE_DETAIL 事件**（每个进程一行，仅在 detail 模式）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | uint64 | 纳秒 |
| `event` | string | `"RESOURCE_DETAIL"` |
| `pid` | int | 进程 PID |
| `comm` | string | 进程名 |
| `rss_kb` | long | RSS (KB) |
| `cpu_user_ms` | uint64 | 用户态 CPU 时间 (ms) |
| `cpu_sys_ms` | uint64 | 内核态 CPU 时间 (ms) |

---

### 3.5 Rust Collector 的 SystemRunner

**源码位置**: `collector/src/framework/runners/system.rs`

这是纯 Rust 实现的资源监控 Runner，与 process_new 的资源采样器功能类似但独立运行。

#### 3.5.1 输出字段

**system_metrics 事件**（针对特定进程）：

```json
{
  "type": "system_metrics",
  "pid": 12345,
  "comm": "claude",
  "timestamp": 1234567890000,
  "cpu": {
    "percent": "23.45",
    "cores": 8
  },
  "memory": {
    "rss_kb": 524288,
    "rss_mb": 512,
    "vsz_kb": 1048576,
    "vsz_mb": 1024
  },
  "process": {
    "threads": 12,
    "children": 5
  },
  "alert": false
}
```

**system_wide 事件**（全系统）：

```json
{
  "type": "system_wide",
  "timestamp": 1234567890000,
  "cpu": {
    "cores": 8,
    "load_avg_1min": 2.15,
    "load_avg_5min": 1.83,
    "load_avg_15min": 1.42
  },
  "memory": {
    "total_kb": 16384000,
    "total_mb": 16000,
    "used_kb": 8192000,
    "used_mb": 8000,
    "free_kb": 4096000,
    "available_kb": 8192000,
    "used_percent": "50.00"
  }
}
```

#### 3.5.2 配置选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--system-interval` | 2秒 | 采样间隔 |
| `-p, --pid` | 无 | 监控特定 PID |
| `-c, --comm` | 无 | 按进程名监控 |
| `--no-children` | false | 排除子进程 |
| `--cpu-threshold` | 无 | CPU 使用率告警阈值 (%) |
| `--memory-threshold` | 无 | 内存告警阈值 (MB) |

---

### 3.6 stdio 捕获 (stdiocap)

**源码位置**: `bpf/stdiocap.bpf.c`, `bpf/stdiocap.h`, `bpf/stdiocap.c`

stdiocap 用于捕获本地 MCP 服务器等通过 stdio（stdin/stdout/stderr）通信的进程的负载数据。

#### 3.6.1 探针列表

| SEC 名称 | 探针类型 | 挂钩点 | 功能 |
|----------|----------|--------|------|
| `tp/syscalls/sys_enter_read` | tracepoint | read 入口 | 记录缓冲区地址、fd、开始时间 |
| `tp/syscalls/sys_exit_read` | tracepoint | read 返回 | 捕获读取数据 |
| `tp/syscalls/sys_enter_write` | tracepoint | write 入口 | 记录缓冲区地址、fd、开始时间 |
| `tp/syscalls/sys_exit_write` | tracepoint | write 返回 | 捕获写入数据 |

#### 3.6.2 内核数据结构 (`stdiocap.h`)

```c
#define MAX_BUF_SIZE 8192

struct stdiocap_event_t {
    __u64 timestamp_ns;   // 内核启动后纳秒
    __u64 delta_ns;       // IO 操作耗时
    __u32 pid;            // 进程 PID
    __u32 tid;            // 线程 TID
    __u32 uid;            // 用户 UID
    __s32 fd;             // 文件描述符 (0=stdin, 1=stdout, 2=stderr)
    __u32 len;            // 实际 IO 长度
    __u32 buf_size;       // 捕获的字节数
    __u8 is_read;         // 1=read, 0=write
    char comm[16];        // 进程名
    __u8 buf[8192];       // 数据负载
};
```

#### 3.6.3 JSON 输出字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp_ns` | uint64 | 内核启动后纳秒 |
| `delta_ns` | uint64 | IO 操作耗时 (纳秒) |
| `pid` | uint32 | 进程 PID |
| `tid` | uint32 | 线程 TID |
| `uid` | uint32 | 用户 UID |
| `fd` | int32 | 文件描述符 (0/1/2 = stdin/stdout/stderr) |
| `len` | uint32 | 实际 IO 长度 |
| `buf_size` | uint32 | 实际捕获字节数 |
| `is_read` | bool | true=read, false=write |
| `comm` | string | 进程名 |
| `data` | string | 负载数据 |

#### 3.6.4 过滤选项

| 参数 | 说明 |
|------|------|
| `-p, --pid` | 目标进程 PID（必需） |
| `-u, --uid` | 按 UID 过滤 |
| `-c, --comm` | 按进程名过滤 |
| `--all-fds` | 捕获所有 fd，不限于 0/1/2 |
| `--max-bytes` | 每事件最大捕获字节数（默认 8192） |

默认 `trace_stdio_only=true`，仅捕获 fd 0/1/2。设置 `--all-fds` 后可捕获任意 fd 的 read/write。

---

### 3.7 浏览器流量追踪 (browsertrace)

**源码位置**: `bpf/browsertrace.bpf.c`, `bpf/browsertrace.h`, `bpf/browsertrace.c`

browsertrace 是专门用于捕获浏览器（Chrome/Firefox）明文 HTTP 数据的工具。与 sslsniff 不同，它不挂钩 SSL 函数，而是挂钩浏览器内部处理明文 HTTP 的代码路径。

#### 3.7.1 探针列表

**Chrome 明文数据捕获**（通过字节模式匹配定位内部函数偏移）：

| SEC 名称 | 探针类型 | 功能 |
|----------|----------|------|
| `uprobe/chrome_plaintext_request_1` | uprobe | Chrome 明文请求路径 1（memcpy 模式） |
| `uprobe/chrome_plaintext_request_2` | uprobe | Chrome 明文请求路径 2 |
| `uprobe/chrome_plaintext_request_3` | uprobe | Chrome 明文请求路径 3 |
| `uprobe/chrome_plaintext_response` | uprobe | Chrome 明文响应 |

**Firefox (NSS) 流量捕获**：

| SEC 名称 | 探针类型 | 功能 |
|----------|----------|------|
| `uprobe/SSL_ImportFD` | uprobe | 记录 NSS SSL fd 创建 |
| `uretprobe/SSL_ImportFD` | uretprobe | 追踪 SSL fd 映射 |
| `uprobe/PR_Write` | uprobe | NSS 写入（仅追踪 SSL fd） |
| `uretprobe/PR_Write` | uretprobe | 捕获写入数据 |
| `uretprobe/PR_Read` | uretprobe | 捕获读取数据 |
| `uprobe/PR_Close` | uprobe | 清理 SSL fd 映射 |

#### 3.7.2 输出格式

与 sslsniff 使用相同的 `probe_SSL_data_t` 数据结构和 JSON 输出格式（同样的字段：`function`, `timestamp_ns`, `comm`, `pid`, `tid`, `uid`, `len`, `data`, `truncated` 等），因此可以复用 Rust collector 的 SSL 分析管道。

**使用方式**：
```bash
# Chrome
sudo ./bpf/browsertrace --binary-path /opt/google/chrome/chrome
# Firefox (必须指向实际 ELF，不是 wrapper 脚本)
sudo ./bpf/browsertrace --binary-path /snap/firefox/current/usr/lib/firefox/firefox
```

---

### 3.8 Rust Collector 的数据处理管道

**源码位置**: `collector/src/framework/`

#### 3.8.1 架构

```
eBPF 程序 (stdout JSON) → Runner → Analyzer 链 → 输出 (文件/控制台/Web Server)
```

#### 3.8.2 Runner 类型

| Runner | 源文件 | 数据源 | Event.source |
|--------|--------|--------|-------------|
| `SslRunner` | `runners/ssl.rs` | sslsniff 二进制 | `"ssl"` |
| `ProcessRunner` | `runners/process.rs` | process 二进制 | `"process"` |
| `StdioRunner` | `runners/stdio.rs` | stdiocap 二进制 | `"stdio"` |
| `SystemRunner` | `runners/system.rs` | `/proc` 轮询 | `"system"` |
| `AgentRunner` | `runners/agent.rs` | 多 Runner 编排 | 透传子 Runner |
| `FakeRunner` | `runners/fake.rs` | 测试用假数据 | `"ssl"` |

#### 3.8.3 Analyzer 链（按处理顺序）

| # | Analyzer | 源文件 | 输入 source | 输出 source | 功能 |
|---|----------|--------|------------|------------|------|
| 1 | `TimestampNormalizer` | `timestamp_normalizer.rs` | 任意 | 不变 | 将纳秒 boot 时间转换为毫秒 epoch 时间 |
| 2 | `SSLFilter` | `ssl_filter.rs` | `"ssl"` | 丢弃 | 按表达式过滤 SSL 事件（支持 `data`, `function`, `comm`, `len`, `pid`, `tid`, `uid`, `latency_ms`, `timestamp_ns`, `data.type` 字段，支持 `=`, `!=`, `>`, `<`, `>=`, `<=`, `~`(contains) 运算符，支持 `&`(AND) / `|`(OR) 组合） |
| 3 | `SSEProcessor` | `sse_processor.rs` | `"ssl"` | `"sse_processor"` | 将多个 SSL READ 事件中的 SSE 流合并为单个事件。解析 `event:` / `data:` 字段，累积 `content_block_delta` 中的文本/思考/JSON 内容，在 `message_stop` 时输出完整的合并事件 |
| 4 | `HTTPParser` | `http_parser.rs` | `"ssl"` | `"http_parser"` | 将原始 SSL 数据解析为结构化 HTTP 请求/响应。提取 method, path, status_code, headers, body 等 |
| 5 | `HTTPFilter` | `http_filter.rs` | `"http_parser"` | 丢弃 | 按表达式过滤 HTTP 事件（支持 `request.method`, `request.path`, `request.path_prefix`, `request.host`, `request.body`, `response.status_code`, `response.status_text`, `response.content_type`, `response.body` 等字段） |
| 6 | `AuthHeaderRemover` | `auth_header_remover.rs` | `"http_parser"` | 不变 | 自动移除敏感头部：`authorization`, `x-api-key`, `x-auth-token`, `bearer`, `token`, `x-access-token`, `x-session-token`, `cookie`, `set-cookie` |
| 7 | `FileLogger` | `file_logger.rs` | 任意 | 不变 | 写入日志文件（支持日志轮转，可配置最大文件大小） |
| 8 | `OutputAnalyzer` | `output.rs` | 任意 | 不变 | 输出到控制台 |

#### 3.8.4 核心 Event 结构

定义在 `collector/src/framework/core/events.rs`：

```rust
pub struct Event {
    pub timestamp: u64,       // 时间戳（经 TimestampNormalizer 后为毫秒 epoch）
    pub source: String,       // 数据源标识
    pub pid: u32,             // 进程 PID
    pub comm: String,         // 进程/线程名
    pub data: serde_json::Value,  // JSON 负载（包含完整的原始或解析后数据）
}
```

#### 3.8.5 SSEProcessor 输出事件结构

当 SSE 流完成（遇到 `message_stop` 事件）时，`SSEProcessor` 输出一个合并后的事件：

| 字段 | 类型 | 说明 |
|------|------|------|
| `connection_id` | string | 连接标识 (`pid:tid:message_id`) |
| `message_id` | string/null | Anthropic API 消息 ID（如 `"msg_01..."`) |
| `start_time` | uint64 | SSE 流开始时间 |
| `end_time` | uint64 | SSE 流结束时间 |
| `duration_ns` | uint64 | SSE 流持续时间 |
| `original_source` | string | `"ssl"` |
| `function` | string | `"READ/RECV"` |
| `tid` | uint64 | 线程 TID |
| `json_content` | string | 累积的 partial_json 内容（如工具调用参数） |
| `text_content` | string | 累积的 text_delta + thinking_delta 文本 |
| `total_size` | uint | text + json 总大小 |
| `event_count` | uint | SSE 流中的事件数 |
| `has_message_start` | bool | 是否包含 message_start |
| `sse_events` | array | 所有原始 SSE 事件的数组 |

#### 3.8.6 HTTPParser 输出事件结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `tid` | uint64 | 线程 TID |
| `message_type` | string | `"request"` 或 `"response"` |
| `first_line` | string | HTTP 首行 |
| `method` | string/null | HTTP 方法（请求时） |
| `path` | string/null | 请求路径（请求时） |
| `protocol` | string/null | HTTP 协议版本 |
| `status_code` | uint16/null | 状态码（响应时） |
| `status_text` | string/null | 状态文本（响应时） |
| `headers` | object | HTTP 头部（key 已转小写） |
| `body` | string/null | HTTP body |
| `total_size` | uint | 总大小估算 |
| `has_body` | bool | 是否有 body |
| `is_chunked` | bool | 是否使用 chunked TE |
| `content_length` | uint/null | Content-Length 值 |
| `original_source` | string | `"ssl"` |
| `raw_data` | string/null | 原始 SSL 数据（可通过 `--ssl-raw-data` 启用） |

---

### 3.9 CLI 子命令与组合模式

AgentSight 提供以下 CLI 子命令（定义在 `collector/src/main.rs`）：

| 子命令 | 功能 | 启用的 Runner | 默认端口 |
|--------|------|--------------|---------|
| `record` | 优化的 Agent 监控（推荐） | SSL + Process + System | 7395 |
| `trace` | 灵活的组合监控 | 可选 SSL/Process/Stdio/System | 7395 |
| `ssl` | 仅 SSL 流量 | SSL | 7395 |
| `process` | 仅进程事件 | Process | 7395 |
| `stdio` | 仅 stdio 负载 | Stdio | 7395 |
| `system` | 仅系统资源 | System | 7395 |

`record` 子命令的预定义过滤规则：
- SSL 过滤: `data=0\r\n\r\n | data.type=binary`（排除空 chunked 终止标记和二进制数据）
- HTTP 过滤: `request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=`（排除注册心跳、202 响应、HEAD 请求和空 body 响应）

---

### 3.10 Codex/rustls 的情况

#### 3.10.1 为什么抓不到 Codex 流量

OpenAI Codex CLI (v0.114.0) 的流量**完全无法**被 sslsniff 捕获，原因如下：

**根本原因: Codex 使用 rustls，不使用 OpenSSL**

```
Codex 架构:
  1. /usr/bin/codex -> Node.js 脚本 (codex.js)
  2. codex.js 通过 child_process.spawn() 启动原生 Rust 二进制
  3. Rust 二进制: static-pie 链接 (musl libc), stripped
     - HTTP 客户端: hyper 1.8.1 + hyper-util 0.1.19
     - TLS: rustls (通过 tokio-rustls 0.26.4, rama-tls-rustls 0.3.0-alpha.4)
     - 无 OpenSSL SSL_* API 函数
```

sslsniff 通过 uprobe 挂钩以下函数：
- `SSL_read` / `SSL_write` / `SSL_read_ex` / `SSL_write_ex` / `SSL_do_handshake`（OpenSSL / BoringSSL）
- `gnutls_record_recv` / `gnutls_record_send`（GnuTLS）
- `PR_Read` / `PR_Write`（NSS）

rustls 是纯 Rust 实现的 TLS 库，没有上述任何函数符号。sslsniff 尝试附着时报错：
```
"libbpf: elf: failed to find symbol 'SSL_write' in '...codex'"
"Failed to attach: no SSL symbols or BoringSSL patterns found"
```

#### 3.10.2 AgentSight 当前版本是否支持 rustls？

**不支持**。经过完整源码审查确认：
- `bpf/sslsniff.bpf.c` 中的所有 SEC 名称均为 OpenSSL/GnuTLS/NSS 的 uprobe
- `bpf/sslsniff.c` 的 uprobe 附着逻辑只处理 OpenSSL（含 BoringSSL 字节模式匹配）、GnuTLS、NSS 三种库
- 代码库中搜索 "rustls" 仅出现在文档（`analysis.md`, `codex-summary.txt`）和无关的 MITM proxy 示例项目中
- 没有任何 Rust TLS 内部函数的 uprobe 定义
- `browsertrace.bpf.c` 虽然也不依赖 SSL 符号，但其字节模式匹配仅适用于 Chrome/Firefox 的内部数据结构，不适用于通用 rustls 二进制

#### 3.10.3 解决方案评估

| 方案 | 可行性 | 难度 | 说明 |
|------|--------|------|------|
| **1. MITM Proxy** | **高** | 低 | 设置 `HTTPS_PROXY` 环境变量，通过 mitmproxy/mitmdump 捕获。Codex 二进制中存在 proxy 相关字符串，很可能支持 HTTP_PROXY。**推荐方案。** |
| **2. 扩展 sslsniff 支持 rustls** | 中 | 高 | 需要对 rustls 的内部函数（如 `rustls::client::ClientConnection::read_tls`）添加 uprobe。但 Codex 二进制已 stripped，需要通过字节模式匹配找到函数偏移。 |
| **3. LD_PRELOAD** | **不可行** | - | Codex 二进制使用 static-pie 链接（musl libc），不支持 LD_PRELOAD。 |
| **4. 内核级 kprobe** | 低 | 很高 | 在 `tcp_sendmsg`/`tcp_recvmsg` 上设置 kprobe 只能看到加密后的数据。需要额外关联 TLS record layer 才能恢复明文，实际不可行。 |
| **5. ptrace/strace** | **不可行** | - | syscall 层面数据已经是加密的。 |
| **6. 修改 rustls 编译** | 理论可行 | 很高 | 如果能重新编译 Codex 并启用 OpenSSL 后端或保留 rustls 调试符号，就可以 hook。但无法修改闭源二进制。 |

**推荐方案**: 使用 MITM proxy（方案 1），这是最简单且最可靠的方式：

```bash
# 启动 mitmproxy
mitmdump -w codex-traffic.flow --set stream_large_bodies=10m

# 使用 proxy 运行 codex
HTTPS_PROXY=http://127.0.0.1:8080 \
SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem \
codex "your prompt"
```

---

### 3.11 AI Agent CLI 工具 TLS 兼容性

以下表格基于 AgentSight sslsniff 实际支持的 TLS 库（OpenSSL, BoringSSL, GnuTLS, NSS）进行判断：

| 工具 | 运行时 | TLS 库 | sslsniff 可抓取 | 说明 |
|------|--------|--------|-----------------|------|
| **Claude Code** | Bun (Node.js) | BoringSSL (静态链接, stripped) | **可以** | 需要 `--binary-path`，sslsniff 通过字节模式匹配自动检测 BoringSSL 函数偏移 |
| **OpenAI Codex** | Rust (static-pie, musl) | rustls | **不可以** | 纯 Rust TLS，无 SSL_* 符号，见 3.10 |
| **GitHub Copilot CLI** | Node.js | OpenSSL (静态链接) | **可以** | 需要 `--binary-path` 指向 node 二进制 |
| **Cursor (IDE)** | Electron (Node.js) | BoringSSL | **可以** | 类似 Claude Code，需要 `--binary-path` |
| **Aider** | Python | OpenSSL (系统 libssl.so) | **可以** | 无需 `--binary-path`，直接挂钩系统 libssl |
| **Continue.dev** | Node.js (VSCode 扩展) | BoringSSL | **部分** | 运行在 VSCode 的 Node.js 中，需指向 VSCode 二进制 |
| **Open Interpreter** | Python | OpenSSL (系统库) | **可以** | 同 Aider |
| **Amazon Q CLI** | Rust | 取决于构建 | **未知** | 需检查使用 openssl-sys 还是 rustls |
| **Google Gemini CLI** | Node.js | OpenSSL (静态链接) | **可以** | 需要 `--binary-path` 指向 node 二进制 |

**关键判断规则**：
1. **Python 工具**: 几乎都使用系统 OpenSSL (`libssl.so`)，sslsniff 直接可抓
2. **Node.js/Bun 工具**: 静态链接 OpenSSL/BoringSSL，需要 `--binary-path`。注意使用 `--binary-path` 时 `--comm` 过滤不传给 sslsniff（因为 SSL 线程名与进程名不同）
3. **Rust 工具**: 使用 `openssl-sys` crate 可抓，使用 `rustls` 不可抓（AgentSight 当前无 rustls 支持）
4. **Go 工具**: Go 标准库使用 `crypto/tls`（纯 Go 实现），sslsniff **不可抓**
5. **Electron 应用**: 内嵌 Chromium 使用 BoringSSL，sslsniff 支持字节模式匹配；或者可用 `browsertrace` 直接捕获明文数据

---

### 3.12 前端可视化能力

**源码位置**: `frontend/` (Next.js/React/TypeScript)

AgentSight 内嵌 Web 前端（通过 `collector/src/server/` 的 Hyper Web Server 提供），端口默认 7395。

提供三个视图：
- **Timeline** (`/timeline`): 按时间线展示所有事件
- **Process Tree** (`/tree`): 进程树可视化，展示 agent 的进程层级和文件操作
- **Raw Logs** (`/logs`): 原始日志查看

数据通过 `/api/events` SSE 端点实时推送，并从日志文件读取历史数据。

---

### 3.13 数据编码说明

sslsniff (`sslsniff.c` 第 558-607 行) 的 JSON 数据编码策略：

- ASCII 可打印字符 (32-126) 直接输出
- `"`, `\`, `\n`, `\r`, `\t`, `\b`, `\f` 使用 JSON 标准转义
- 有效 UTF-8 多字节序列直接输出（通过 `validate_utf8_char` 验证）
- 无效高位字节用 `\uXXXX` 转义
- 控制字符 (0-31, 127) 用 `\uXXXX` 转义

这意味着：
- **Rust collector** 可正确处理所有数据（Rust serde_json 支持上述所有转义）
- **Python collector** 读取 gzip 二进制响应时可能遇到编码问题（有效 UTF-8 序列被 JSON 解析器还原后无法用 latin-1 回转），建议使用 Rust collector

---

## 附录：数据流时序

```
时间线 (3.6 秒):
┌─ t=0.000s   WRITE  GET /v1/mcp_servers?limit=1000
├─ t=0.000s   WRITE  POST /api/eval/sdk-...
├─ t=0.000s   WRITE  GET /api/claude_code_penguin_mode
├─ t=0.000s   WRITE  GET /api/oauth/claude_cli/client_data
│
├─ t=0.157s   READ   HTTP 200 (mcp_servers 响应, gzip)
├─ t=0.157s   READ   HTTP 200 (client_data 响应, JSON)
├─ t=0.157s   READ   HTTP 200 (eval 响应, gzip, 多块)
├─ t=0.157s   READ   HTTP 200 (penguin_mode 响应, gzip)
│
├─ t=0.320s   WRITE  GET /api/oauth/account/settings
├─ t=0.320s   WRITE  GET /api/claude_code_grove
├─ t=0.350s   READ   HTTP 200 (account/settings 响应, gzip)
├─ t=0.350s   READ   HTTP 200 (grove 响应, gzip)
│
├─ t=0.700s   WRITE  POST /v1/messages?beta=true (99 KB, 分 2 个事件)
├─ t=1.200s   READ   HTTP 200 SSE 流开始 (text/event-stream, gzip)
│  ... 65 个 READ/RECV 事件 (SSE 流数据) ...
├─ t=3.200s   READ   SSE 流结束
│
├─ t=3.300s   WRITE  POST /api/event_logging/v2/batch (64 KB, 分 2 个事件)
├─ t=3.400s   WRITE  POST /api/v2/logs (Datadog, 6 KB)
├─ t=3.500s   READ   HTTP 200 (event_logging 响应)
└─ t=3.600s   READ   HTTP 202 (Datadog 响应)
```

**请求-响应配对**:
- 启动阶段（前 6 个 GET/POST）几乎同时发出（并行请求）
- 核心 API 调用（`/v1/messages`）耗时约 2 秒（含 SSE 流传输）
- 遥测数据在 API 调用完成后才发送
