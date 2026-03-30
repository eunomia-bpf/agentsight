# 开发指南

[English](development.md) | **中文**

## 前端开发模式（磁盘优先加载）

collector 二进制在编译时通过 `RustEmbed` 将前端资源内嵌。默认情况下，每次前端改动都需要重新编译 collector（`cargo build --release`）才能生效。

为加速前端开发，可设置 `AGENTSIGHT_FRONTEND_DIST` 环境变量，让 collector 直接从磁盘目录读取前端资源。这样只需重新构建前端并重启 collector，无需重新编译 Rust 代码。

### 使用方法

```sh
# 1. 构建前端
make build-frontend

# 2. 设置环境变量启动 collector
AGENTSIGHT_FRONTEND_DIST=./frontend/dist sudo -E ./collector/target/release/agentsight record -c claude --binary-path /opt/node-v22.20.0/bin/node
```

之后每次修改前端：

```sh
make build-frontend
# 重启 collector 即可生效，无需 cargo build
```

### 工作原理

- collector 启动时检查 `AGENTSIGHT_FRONTEND_DIST` 环境变量。
- **已设置** — 直接从指定目录读取文件，跳过内嵌资源解压流程。目录中必须包含 `index.html`。
- **未设置** — 使用默认行为：将 `RustEmbed` 内嵌资源解压到临时目录，退出时自动清理。

### 注意事项

- 使用 `sudo -E` 以在 sudo 下保留环境变量。
- 路径支持相对路径（如 `./frontend/dist`）和绝对路径。
- 生产环境中不要设置此变量，将正常使用内嵌资源。
