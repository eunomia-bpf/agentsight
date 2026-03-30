# Development Guide

**English** | [中文](development.zh-CN.md)

## Frontend Dev Mode (Disk-First Assets)

The collector binary embeds frontend assets via `RustEmbed` at compile time. By default, every frontend change requires recompiling the collector (`cargo build --release`) to take effect.

To speed up frontend development, set the `AGENTSIGHT_FRONTEND_DIST` environment variable to serve assets directly from disk. This way you only need to rebuild the frontend and restart the collector — no Rust recompilation needed.

### Usage

```sh
# 1. Build the frontend
make build-frontend

# 2. Start the collector with disk-based frontend assets
AGENTSIGHT_FRONTEND_DIST=./frontend/dist sudo -E ./target/release/agentsight record -c claude --binary-path <path>
```

After each frontend change:

```sh
make build-frontend
# Restart the collector — changes take effect immediately, no cargo build needed
```

### How it works

- On startup, the collector checks for the `AGENTSIGHT_FRONTEND_DIST` environment variable.
- **Set** — serves files directly from the specified directory, skipping the embedded asset extraction. The directory must contain `index.html`.
- **Not set** — falls back to the default behavior: extracts `RustEmbed` assets to a temp directory and cleans up on exit.

### Notes

- Use `sudo -E` to preserve the environment variable when running with sudo.
- The path can be relative (e.g., `./frontend/dist`) or absolute.
- In production, do not set this variable — the embedded assets will be used as usual.
