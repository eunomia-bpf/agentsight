# Usage

**English** | [中文](usage.zh-CN.md)

## Building from Source

### 1. Clone the repository and initialize submodules

```sh
git clone https://github.com/eunomia-bpf/agentsight.git
cd agentsight
git submodule update --init --recursive
```

If you have already cloned the repository but the submodule directories (`libbpf/` and `bpftool/`) are empty, run:

```sh
git submodule update --init --recursive
```

### 2. Install system dependencies

```sh
make install
```

This installs the required build dependencies: libelf, zlib, clang, llvm, Node.js, and the Rust toolchain.

### 3. Build

```sh
make build
```

After a successful build, the agentsight binary is located at `collector/target/release/agentsight`.

You can also build individual components:

```sh
make build-bpf       # eBPF C programs only
make build-rust      # Rust collector only
make build-frontend  # Frontend only
```

## Command-line parameters for monitoring Claude Code with agentsight

Navigate to the source code root directory and run the following commands to test:

```sh
sudo ./collector/target/release/agentsight ssl --http-parser --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n"
```

```sh
sudo ./collector/target/release/agentsight agent -c "claude" --http-parser --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n"
```

```sh
sudo ./collector/target/release/agentsight agent -c claude --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n|data.type=binary"
```
