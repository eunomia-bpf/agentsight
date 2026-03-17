# sslsniff 扩展支持 rustls (Codex CLI) 可行性研究报告

**日期**: 2026-03-16
**作者**: DatRail 团队
**状态**: 研究报告（仅分析，未修改源码）

---

## 1. 背景与目标

当前 sslsniff 通过 uprobe 钩取 OpenSSL (`SSL_read`/`SSL_write`)、GnuTLS (`gnutls_record_send`/`gnutls_record_recv`)、NSS (`PR_Read`/`PR_Write`) 的函数来捕获明文 TLS 流量。对于 stripped 的 BoringSSL 二进制（如 Claude CLI / Bun），sslsniff 已实现了基于字节模式匹配的 offset 检测机制。

**新需求**: OpenAI Codex CLI 是一个 Rust 编写的静态链接二进制，使用 **rustls 0.23.36** + **aws-lc-rs** (AWS-LC 1.67.0) 作为 TLS 库，没有任何 `SSL_read`/`SSL_write` 符号。我们需要评估如何捕获其 TLS 流量。

---

## 2. Codex 二进制分析

### 2.1 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `~/.nvm/versions/node/v22.22.0/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/codex/codex` |
| 类型 | ELF 64-bit LSB pie executable, x86-64, **static-pie linked, stripped** |
| 大小 | **125 MB** |
| .text 段 | **95.5 MB** (0x05f89817 字节) |
| .rodata 段 | **9.2 MB** |
| 编译器 | rustc 1.93.0 (2026-01-19) + clang 19.1.7 + GCC 9.4.0/13.3.0 |
| 符号表 | **完全 stripped** — `.dynsym` 仅 1 个空条目，`nm` 报告 "no symbols" |

### 2.2 TLS 栈确认

通过 `strings` 分析确认的依赖链：

```
codex binary
  ├── reqwest 0.12.28 (HTTP 客户端)
  │   └── hyper-rustls 0.27.7
  │       └── tokio-rustls (via rama-tls-rustls 0.3.0-alpha.4)
  │           └── rustls 0.23.36
  │               └── aws-lc-rs (AWS-LC 1.67.0) ← 实际加解密后端
  ├── rama (代理框架，用于内置网络代理)
  │   ├── rama-tls-rustls 0.3.0-alpha.4
  │   └── rama-net 0.3.0-alpha.4
  └── hyper-util 0.1.19 (HTTP/2 连接池)
```

### 2.3 关键发现

**无 OpenSSL/BoringSSL 的 SSL_* 符号**：二进制不包含任何 `SSL_read`、`SSL_write`、`SSL_do_handshake` 函数。BoringSSL 字节模式匹配也不适用。

**AWS-LC C 函数字符串残留**：虽然符号表被 strip，但 `.rodata` 中仍然保留了大量 AWS-LC 的 C 源码路径和错误消息字符串：
```
AWS-LC 1.67.0
/aws-lc/crypto/fipsmodule/cipher/aead.c
/aws-lc/crypto/fipsmodule/cipher/e_aes.c
EVP_AEAD_CTX_init for AES-128-GCM failed.
EVP_AEAD_CTX_seal for AES-128-GCM failed.
AES-GCM-decrypt KAT failed because EVP_AEAD_CTX_open failed
aes_gcm_init_key
aes_gcm_tls_cipher
```

**SSLKEYLOGFILE 支持**：二进制包含完整的 rustls `KeyLogFile` 实现以及 rama-net 的 KeyLog 支持：
```
SSLKEYLOGFILE
rustls::key_log_file
CLIENT_RANDOM
KeyLogFileHandle: try to create a new handle
create parent dir(s) of key log file
```

**代理环境变量支持**：reqwest 0.12.28 完整支持代理：
```
HTTP_PROXY, http_proxy
HTTPS_PROXY, https_proxy
ALL_PROXY, all_proxy
NO_PROXY, no_proxy
tunneling HTTPS over proxy
```

**内置网络代理 (MITM)**：Codex 有完整的内置网络代理子系统 `codex_network_proxy`，包括：
- HTTP CONNECT 代理
- SOCKS5 代理
- MITM TLS 拦截（使用 `proxyca.pem` / `ca.key`）
- 配置项 `dangerously_allow_non_loopback_proxy`
- 自签 CA 证书生成

**rustls 模块路径残留**：大量 Rust 源码路径在 `.rodata` 中，可作为定位辅助：
```
rustls::conn
rustls::common_state
rustls::record_layer
rustls::client::tls12
rustls::client::tls13
```

---

## 3. 方案评估

### 方案 A: SSLKEYLOGFILE + Wireshark/解密 (推荐度: ★★★★☆)

**原理**: 设置 `SSLKEYLOGFILE` 环境变量，rustls 会将 TLS session keys 写入文件。配合 tcpdump 捕获密文，使用 keys 解密。

**可行性**: **高**
- 二进制中已确认包含 `SSLKEYLOGFILE` 处理逻辑和 `KeyLogFile` 实现
- rustls 的 `KeyLogFile` struct 会在检测到此环境变量时自动启用
- 导出格式为标准 NSS Key Log Format (`CLIENT_RANDOM ...`)

**优点**:
- 无需修改任何代码
- 无需 root 权限（非 eBPF 路径）
- 100% 可靠，不受二进制更新影响
- 捕获完整数据，无 32KB 截断限制

**缺点**:
- 需要同时运行 tcpdump 捕获密文网络包
- 后处理步骤多：tcpdump -> pcap + keylog -> tshark/wireshark 解密 -> 明文
- 非实时（需要事后解密）
- 如果 Codex 二进制未启用此 feature（虽然字符串存在但可能被条件编译禁用），则不可用

**实现步骤**:
```bash
# 1. 启动密钥记录
export SSLKEYLOGFILE=/tmp/codex-keys.log

# 2. 同时捕获网络包
tcpdump -i any -w /tmp/codex-traffic.pcap host api.openai.com &

# 3. 运行 Codex
codex "your prompt"

# 4. 解密
tshark -r /tmp/codex-traffic.pcap -o tls.keylog_file:/tmp/codex-keys.log -Y http
```

**风险评估**: 需要验证 Codex 的 rustls 配置是否实际调用了 `KeyLogFile::new()`。从 strings 分析看，`rustls::key_log_file` 模块代码确实被链接进来了，但运行时是否激活取决于 `ClientConfig` 的构建方式。rama-net 也有独立的 KeyLogFile 处理逻辑。

---

### 方案 B: MITM 代理 (推荐度: ★★★★★)

**原理**: 通过 `HTTPS_PROXY` 环境变量让 Codex 的 reqwest HTTP 客户端走 mitmproxy，在代理层拦截明文。

**可行性**: **最高**
- 二进制中确认存在完整的 reqwest 代理支持（`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`）
- 字符串 `tunneling HTTPS over proxy` 确认了 CONNECT 隧道功能
- reqwest 的代理实现默认读取环境变量

**优点**:
- 最成熟的方案，无需修改 sslsniff
- 与 TLS 库无关 — 在应用层以上拦截
- 实时获取明文 HTTP 请求/响应
- 已有现成工具 [llm-interceptor](https://github.com/chouzz/llm-interceptor) 专门用于 AI 工具流量拦截
- 可获取完整数据，无截断

**缺点**:
- 需要安装 mitmproxy CA 证书（`SSL_CERT_FILE` 或系统证书存储）
- Codex 的沙箱网络策略可能干扰（但可通过配置绕过）
- 增加一跳延迟
- 需要额外进程（mitmproxy）

**实现步骤**:
```bash
# 1. 启动 mitmproxy
mitmproxy --mode regular --listen-port 8080 --set stream_large_bodies=0

# 2. 设置环境变量
export HTTPS_PROXY=http://127.0.0.1:8080
export SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem

# 3. 运行 Codex
codex "your prompt"
```

**补充发现**: Codex 也支持 `SSL_CERT_FILE` 环境变量（在二进制中明确发现此字符串及其回退路径列表），这意味着可以通过设置自定义 CA 证书来信任 mitmproxy 的证书。

---

### 方案 C: 扩展 sslsniff 钩取 rustls 函数 (推荐度: ★★☆☆☆)

**原理**: 类似当前对 OpenSSL 的支持，通过 uprobe 钩取 rustls 的明文读写函数。

**挑战分析**:

#### C.1 符号完全 stripped

Codex 二进制没有任何可用的函数符号。`readelf -s` 仅返回 1 个空条目，`nm` 报告 "no symbols"。无法通过 `func_name` 参数附加 uprobe。

#### C.2 rustls 与 OpenSSL 架构差异巨大

OpenSSL 的 API 非常简洁：
```c
int SSL_read(SSL *ssl, void *buf, int num);   // buf 指向明文输出
int SSL_write(SSL *ssl, void *buf, int num);  // buf 指向明文输入
```
参数 `buf` 直接指向明文缓冲区，在 entry/exit 时读取即可。

rustls 的等价接口是 Rust trait 方法：
```rust
// 实际的明文通过 std::io::Read/Write trait 传递
impl Read for ConnectionCommon<Data> {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize>;
}
impl Write for ConnectionCommon<Data> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize>;
}
```

问题在于：
1. **Rust 泛型单态化**: `ConnectionCommon<ClientData>` 和 `ConnectionCommon<ServerData>` 会生成不同的函数实例
2. **内联优化**: Release 模式下，这些函数极大概率被内联到调用者中
3. **名称修饰 (mangling)**: 即使未 strip，Rust 函数名包含 hash（如 `_ZN6rustls4conn16ConnectionCommon...h1a2b3c4d5e6f7g8h`），每次编译都不同
4. **async/await 状态机**: tokio-rustls 将同步 rustls 包装在 async 中，编译器会生成复杂的状态机代码

#### C.3 字节模式匹配不可行

当前 sslsniff 对 BoringSSL 使用的字节模式匹配方法不适用于 rustls：

| 维度 | BoringSSL (当前方案) | rustls (需要的) |
|------|---------|---------|
| 函数数量 | 3 个固定函数 | 多个泛型实例 + async wrapper |
| 函数间距 | 固定（同一编译单元） | 不确定（跨 crate、LTO） |
| 序言模式 | C ABI，标准 push/sub | Rust ABI，不规律 |
| .text 扫描范围 | ~几十 MB | **95.5 MB** |
| 二进制稳定性 | BoringSSL 较稳定 | Rust 每次编译结果不同 |
| 参数传递 | C 调用约定 (rdi, rsi, rdx) | Rust ABI（可变，无规范） |

**结论**: 字节模式匹配在技术上可以尝试，但维护成本极高，每个 Codex 版本都需要重新标定模式。95.5 MB 的 .text 段也增加了误匹配风险。

---

### 方案 D: 钩取 AWS-LC 底层加密函数 (推荐度: ★★★☆☆)

**原理**: rustls 使用 aws-lc-rs 作为加密后端，aws-lc-rs 内部调用 AWS-LC (C 代码)。找到 `EVP_AEAD_CTX_seal`/`EVP_AEAD_CTX_open` 等 C 函数的地址并 hook。

**发现**:
- AWS-LC 的错误字符串清楚表明了关键函数的存在：
  ```
  EVP_AEAD_CTX_init for AES-128-GCM failed.
  EVP_AEAD_CTX_seal for AES-128-GCM failed.
  AES-GCM-decrypt KAT failed because EVP_AEAD_CTX_open failed
  ```
- 这些是 **C 语言函数**，遵循标准 C 调用约定
- 但它们操作的是 **密文/密钥级别** 的数据，不是明文 HTTP

**问题**:
1. **不是明文接口**: `EVP_AEAD_CTX_seal` 执行的是 AEAD 加密，输入是明文 + nonce + AAD，输出是密文。虽然可以在 entry 时捕获明文参数，但这是 TLS record 级别的明文，不是 HTTP 语义的明文
2. **TLS record framing**: 捕获到的数据需要理解 TLS record protocol 才能还原为 HTTP 消息
3. **函数地址查找**: 虽然字符串存在，但函数本身没有符号。需要从错误字符串的引用反向追踪到函数地址 — 这需要反汇编分析
4. **调用频率高**: AEAD 操作在每个 TLS record 上都会调用，数据量大、处理复杂

**技术可行路径**:
可以通过以下方式找到 `EVP_AEAD_CTX_seal` 的地址：
1. 在 `.rodata` 中定位错误字符串 `"EVP_AEAD_CTX_seal for AES-128-GCM failed."` 的地址
2. 在 `.text` 中搜索引用该字符串地址的代码
3. 该引用点附近就是 `EVP_AEAD_CTX_seal` 函数体

但即使找到了地址，hook 该函数获得的是 TLS record 的明文载荷（可能被分片），需要额外的 TLS record 解析逻辑才能还原 HTTP 数据。

---

### 方案 E: kTLS 内核钩子 (推荐度: ★☆☆☆☆)

**原理**: 如果应用使用 kTLS (kernel TLS)，可以在内核态 `tls_sw_sendmsg`/`tls_sw_recvmsg` 上挂 kprobe。

**可行性**: **极低**
- 二进制中搜索 `kTLS`/`ktls` 仅发现字符串 `KTLS` 和 `KTLSTxZerocopySendfile`，这些来自 AWS-LC 的代码，但 rustls 本身**不使用 kTLS**
- rustls 是纯用户态 TLS 实现，加解密全部在用户空间完成
- `SSL_sendfile` 字符串存在但来自 AWS-LC 的 compat 层，Codex 不会通过此路径

---

### 方案 F: Codex 内置网络代理利用 (推荐度: ★★★☆☆)

**原理**: Codex 自身包含了完整的 MITM 代理（`codex_network_proxy`），用于沙箱网络策略执行。我们可能可以利用此机制。

**发现**:
- Codex 内部有 `network-proxy/src/mitm.rs` 实现
- 支持 `proxyca.pem` / `ca.key` 自签 CA
- 在沙箱模式下，子进程的网络流量被路由通过此代理
- 配置项: `proxy_url`, `enable_socks5`, `socks_url`, `allow_upstream_proxy`

**问题**:
- 此代理是 Codex 用于**管控子进程**网络访问的，不是用于监控 Codex 自身的 API 流量
- Codex 自身到 OpenAI API 的流量不经过此代理
- 我们无法轻易将 Codex 的出站流量重定向到其自身的代理

---

## 4. 推荐实施路线

### 短期 (立即可用): 方案 B — MITM 代理

**这是唯一无需修改代码即可立即工作的方案。**

```bash
# 安装 mitmproxy
pip install mitmproxy

# 方式 1: mitmproxy + HTTPS_PROXY
HTTPS_PROXY=http://127.0.0.1:8080 \
SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem \
codex "hello"

# 方式 2: 集成到 AgentSight collector
# 在 collector 中启动一个轻量 MITM proxy，
# 自动设置 HTTPS_PROXY 后启动 codex 子进程
```

**与 AgentSight 的集成方案**:
1. Collector 启动时内嵌一个轻量 HTTP CONNECT 代理（可用 Rust 的 `hyper` 实现）
2. 生成临时 CA 证书
3. 设置 `HTTPS_PROXY` 和 `SSL_CERT_FILE` 环境变量
4. 启动 Codex 进程
5. 代理层拦截明文 HTTP 请求/响应，转换为与 sslsniff 相同的事件格式
6. 复用现有的 analyzer chain (HTTPParser, SSEProcessor 等)

### 中期 (需要验证): 方案 A — SSLKEYLOGFILE

在 MITM 代理方案之外，也可以尝试 `SSLKEYLOGFILE`：

```bash
SSLKEYLOGFILE=/tmp/codex-keys.log codex "hello"
# 如果 /tmp/codex-keys.log 被写入，说明方案可行
```

如果此方案可用，可以开发一个实时解密管道：
- tcpdump 实时捕获 + SSLKEYLOGFILE 实时读取 → 在线解密 TLS 流量

### 长期 (高复杂度): 方案 D — AWS-LC 层 hook

如果未来需要纯 eBPF 方案（无代理依赖），可以投资开发 AWS-LC 层的 hook：
1. 开发自动化的 `.rodata` 字符串引用定位工具
2. 从错误字符串反向追踪 `EVP_AEAD_CTX_seal`/`EVP_AEAD_CTX_open` 函数地址
3. 在 sslsniff 中添加 TLS record 解析逻辑
4. 此方案可推广到所有使用 aws-lc-rs 的 Rust 应用

---

## 5. 现有工具生态调研

| 工具 | 是否支持 rustls | 备注 |
|------|----------------|------|
| sslsniff (本项目) | 否 | 仅 OpenSSL/GnuTLS/NSS/BoringSSL |
| eCapture | 否 | 支持 OpenSSL/GnuTLS/NSS/GoTLS，不支持 rustls |
| Pixie / stirling | 否 | 仅 OpenSSL |
| spliff | 否 | 仅 OpenSSL |
| Kubeshark | 否 | 仅 OpenSSL |
| llm-interceptor | **是** (通过 MITM) | mitmproxy 方案，支持 Claude Code/Cursor/Codex |
| bpftrace | 理论可行 | 需要手动指定 uprobe offset |

**结论**: 目前没有任何 eBPF 工具原生支持 rustls 的 uprobe hook。所有成功拦截 rustls 流量的方案都是基于 MITM 代理。

---

## 6. 技术总结

### sslsniff 当前架构分析

sslsniff 的 uprobe 机制设计精巧，核心是：
1. **entry hook** (`BPF_UPROBE`): 记录 `buf` 指针和时间戳到 BPF map
2. **exit hook** (`BPF_URETPROBE`): 从 map 取回 `buf`，读取返回值作为长度，通过 `bpf_probe_read_user` 复制明文数据到 ring buffer

此模式要求目标函数具有 **`(ctx, buf, len)` 签名**且 **`buf` 在函数返回时包含明文**。OpenSSL 的 `SSL_read(ssl, buf, num)` 完美符合此模式。

### rustls 不适配的根本原因

rustls 的架构不适合 uprobe hook，因为：

1. **没有单一的 "明文缓冲区传递" 函数**: rustls 内部通过 `DeframerVecBuffer` 分层处理——TLS record 解析、解密、重组都在不同的内部函数中完成
2. **async 异步模型**: 数据流经 tokio-rustls 的 `TlsStream::poll_read()`，这是一个 Future 状态机，不是简单的同步函数调用
3. **零拷贝设计**: rustls 尽量避免不必要的内存复制，明文可能直接写入调用者提供的缓冲区，中间没有 "标准" 的传递点
4. **LTO 优化**: 整个 TLS 栈可能被 Link-Time Optimization 合并，函数边界被消除

### 核心结论

**对于 rustls 类型的纯 Rust TLS 库，MITM 代理方案是最佳实践**。eBPF uprobe 方案在技术上存在根本性障碍（stripped + Rust ABI + 内联优化 + 无标准 C 接口），投入产出比极低。

建议在 AgentSight 的 collector 中增加一个 **ProxyRunner**（与现有的 SslRunner 平行），使用内嵌 MITM 代理来处理 rustls 应用的流量捕获。这样可以保持统一的事件流架构，同时覆盖所有 TLS 库类型。

---

## 附录 A: Codex 二进制依赖组件版本

| 组件 | 版本 |
|------|------|
| rustc | 1.93.0 (2026-01-19) |
| rustls | 0.23.36 |
| aws-lc-rs (AWS-LC) | 1.67.0 |
| reqwest | 0.12.28 |
| hyper-rustls | 0.27.7 |
| hyper-util | 0.1.19 |
| rama-tls-rustls | 0.3.0-alpha.4 |
| rama-net | 0.3.0-alpha.4 |
| tokio-tungstenite | (git checkout 132f5b3) |

## 附录 B: Codex 代理相关环境变量

从二进制 strings 中确认的环境变量：

```
HTTP_PROXY / http_proxy
HTTPS_PROXY / https_proxy
ALL_PROXY / all_proxy
NO_PROXY / no_proxy
SSL_CERT_FILE
SSL_CERT_DIR
SSLKEYLOGFILE
CODEX_SANDBOX_NETWORK_DISABLED
```

## 附录 C: 参考资料

- [eBPF TLS tracing: The Past, Present and Future (Pixie)](https://blog.px.dev/ebpf-tls-tracing-past-present-future/)
- [eBPF 实践: 使用 uprobe 捕获 SSL/TLS 明文](https://medium.com/@yunwei356/ebpf-practical-tutorial-capturing-ssl-tls-plain-text-using-uprobe-fccb010cfd64)
- [Reverse Engineering Claude Code's SSL Traffic with eBPF (eunomia)](https://eunomia.dev/en/blog/posts/claude-code-analysis/)
- [eBPF Practice: Tracing User Space Rust Applications with Uprobe (eunomia)](https://eunomia.dev/tutorials/37-uprobe-rust/)
- [RustBound: Function Boundary Detection over Rust Stripped Binaries](https://homepages.uc.edu/~wang2ba/files/pub/smartsp24_ryan.pdf)
- [rustls KeyLogFile 文档](https://docs.rs/rustls/latest/rustls/struct.KeyLogFile.html)
- [llm-interceptor: AI 工具 MITM 拦截器](https://github.com/chouzz/llm-interceptor)
- [eCapture: eBPF SSL/TLS 明文捕获](https://github.com/gojue/ecapture)
- [OpenAI Codex 代理支持 Issue #4242](https://github.com/openai/codex/issues/4242)
- [OpenAI Codex 安全文档](https://developers.openai.com/codex/security/)
- [OpenAI Codex 高级配置](https://developers.openai.com/codex/config-advanced/)
