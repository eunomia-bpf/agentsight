# Docker Usage

Use Docker when you want a packaged AgentSight runtime for container, CI, or isolated Linux environments. Docker does not remove the eBPF permission requirements: the container must observe the host kernel and host processes, so it needs privileged mode and host mounts.

For local day-to-day use, the release binary plus `agentsight top` or
`sudo agentsight record -- ...` in [README.md](https://github.com/eunomia-bpf/agentsight#quick-start) is usually simpler.

## Requirements

- Linux host with eBPF support
- Docker access
- `--privileged`
- `--pid=host`
- `--network=host` when you want the web UI and host-network behavior to be straightforward
- Host mounts for `/sys`, `/usr`, and `/lib` so process and SSL probes can resolve host state and libraries

## Monitor Python AI Tools

```bash
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm python
```

## Monitor Claude Code

Claude Code uses a user-local binary. Mount the Claude install directory and pass the binary path inside the container:

```bash
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v "$HOME/.local/share/claude:/claude:ro" \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm claude --binary-path /claude/versions/2.1.39
```

Adjust `/claude/versions/2.1.39` to the version installed on the host.

## Notes

- A normal unprivileged Docker container cannot load eBPF probes or inspect host processes.
- Docker's default seccomp profile can block eBPF-related syscalls; `--privileged` avoids that for local testing and CI runners where this is acceptable.
- Captured SQLite databases can contain prompts, responses, file paths, headers, and network targets. Treat saved session databases as sensitive.
