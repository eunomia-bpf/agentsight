# AgentSight npm package

Official npm entrypoint for [Eunomia AgentSight](https://github.com/eunomia-bpf/agentsight).

This package claims the global `agentsight` command for the Node ecosystem and
ships the AgentSight Web viewer for exported trace snapshots. The Linux eBPF
collector remains the Rust `agentsight` binary published through crates.io and
GitHub Releases.

## Install

```bash
npm install -g @eunomia-bpf/agentsight
agentsight --help
```

## Web viewer

```bash
agentsight serve --snapshot snapshot.json --port 7395
agentsight open snapshot.json
```

Create a snapshot with the Rust collector:

```bash
cargo install agentsight
agentsight report export -o snapshot.json
```

## Collector commands

Commands such as `agentsight record`, `agentsight top`, `agentsight monitor`,
`agentsight stat`, and `agentsight report` delegate to a real AgentSight
collector binary when one is available. eBPF capture requires Linux privileges.

Install the collector with:

```bash
cargo install agentsight
```

or download the official binary from:

```text
https://github.com/eunomia-bpf/agentsight/releases/latest
```

This npm package does not download or execute hidden binaries during
installation, and it does not run privileged commands from `postinstall`.
