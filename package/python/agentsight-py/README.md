# agentsight-py

Official Python helper for [Eunomia AgentSight](https://github.com/eunomia-bpf/agentsight).

`agentsight-py` is the PyPI package name because the bare PyPI name
`agentsight` is owned by an unrelated project. The canonical AgentSight collector
is still installed with `cargo install agentsight`; the scoped npm package is
published as `@eunomia-bpf/agentsight`.

This package is a small, real Python utility for inspecting AgentSight exported
snapshots:

```bash
pipx install agentsight-py
agentsight-py --version
agentsight-py summary snapshot.json
agentsight-py summary snapshot.json --json
```

Create a snapshot with the AgentSight collector:

```bash
agentsight report export -o snapshot.json
```

The package is experimental and intentionally does not implement eBPF capture.
Live capture remains the job of the Linux AgentSight collector.
