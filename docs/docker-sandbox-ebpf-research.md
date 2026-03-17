# eBPF-Based Monitoring in Docker Sandbox Environments for AI Agents

**Date:** 2026-03-16
**Context:** AgentSight eBPF monitoring applied to Docker-based AI agent sandboxes

---

## Table of Contents

1. [Current AI Agent Sandbox Landscape](#1-current-ai-agent-sandbox-landscape)
2. [eBPF in Docker and Container Environments](#2-ebpf-in-docker-and-container-environments)
3. [Deployment Architectures](#3-deployment-architectures)
4. [CLI and Syscall Interception in Sandboxes](#4-cli-and-syscall-interception-in-sandboxes)
5. [Existing Solutions and Prior Art](#5-existing-solutions-and-prior-art)
6. [Practical Considerations](#6-practical-considerations)
7. [Recommendations for AgentSight](#7-recommendations-for-agentsight)

---

## 1. Current AI Agent Sandbox Landscape

### 1.1 What Problem Sandboxes Solve

AI coding agents (Claude Code, Codex CLI, Cursor, Devin, Aider) autonomously execute shell commands, edit files, run build tools, and call external APIs. A compromised or misbehaving agent can cause significant damage if it runs on a developer's workstation without any containment. Sandboxes enforce boundaries so that mistakes — or prompt injection attacks — cannot escape a defined perimeter.

### 1.2 Survey of Sandbox Solutions

#### E2B
E2B ([e2b.dev](https://e2b.dev)) is a commercial sandbox-as-a-service platform marketed specifically at AI agent workloads. Each sandbox is a **fast, isolated Linux VM** — the documentation describes it as "a fast, secure Linux VM created on demand for your agent." E2B uses Firecracker microVMs under the hood (common for sub-second cold-start VM workloads). The VM isolation model means:
- The guest kernel is separate from the host kernel.
- eBPF uprobes placed in the host **cannot cross the VM boundary** to hook guest processes.
- Monitoring inside an E2B sandbox requires either (a) installing eBPF tooling inside the VM, which requires privileged access inside the VM, or (b) using E2B's own observability APIs.

#### Fly.io Machines
Fly.io Machines are also **virtual machines** (not Docker containers), with "sub-second" start times. Each Machine gets its own lightweight VM. The same eBPF isolation boundary applies: host uprobes cannot cross into a Fly Machine's guest kernel.

#### Modal
Modal runs Python workloads in containers with strong isolation. Modal builds custom container images and runs them on its own infrastructure. The containers run inside VMs for multi-tenant isolation.

#### Daytona
Daytona provides development workspace management, spinning up workspace containers for development environments. It is primarily container-based rather than VM-based, making it potentially more amenable to eBPF monitoring from a sidecar.

#### Docker-based sandboxes (self-hosted)

Many teams build their own sandbox using stock Docker. Claude Code's official devcontainer reference implementation ([github.com/anthropics/claude-code/.devcontainer](https://github.com/anthropics/claude-code/tree/main/.devcontainer)) is one example:
- Container built on Node.js 20 base image.
- Includes `init-firewall.sh` that enforces outbound firewall rules (allowlist of domains: npm registry, GitHub, Claude API, etc.).
- Uses `--dangerously-skip-permissions` flag for unattended operation inside the container.
- The security boundary relies on the container's network and filesystem isolation, not on VM-level isolation.

#### Claude Code's Own Sandboxing
Claude Code (as of early 2026) has a native `/sandbox` command that uses OS-level primitives:
- **macOS**: Apple's Seatbelt (`sandbox-exec`) for filesystem and network isolation.
- **Linux / WSL2**: `bubblewrap` (`bwrap`) for namespaced filesystem and network isolation.

The sandbox uses a proxy server for network filtering (allowlist of domains). Filesystem restrictions apply to all child processes spawned by bash commands. A `--enableWeakerNestedSandbox` mode exists to support running inside Docker environments without privileged namespaces, but the documentation explicitly notes this "considerably weakens security."

#### OpenAI Codex CLI
OpenAI's Codex CLI (the open-source CLI released in 2025) includes a sandboxing feature that runs agent-executed commands in Docker containers on the local machine. It creates temporary containers with restricted network access for code execution. The Claude Code web execution environment uses "isolated, Anthropic-managed VMs" per session.

#### Devin (Cognition AI)
Devin runs each session in a fully isolated cloud environment with a browser, terminal, and code editor. The exact infrastructure (containers vs. VMs) is not publicly documented, but the isolation model is understood to be per-session VMs with persistent-if-needed storage.

### 1.3 Security Boundaries Enforced by Common Sandboxes

| Sandbox | Isolation Level | Network | Filesystem | Root in sandbox? |
|---------|----------------|---------|-----------|------------------|
| E2B | Full VM (Firecracker) | Configurable | Per-VM | Yes |
| Fly.io Machines | Full VM | Configurable | Per-VM | Yes |
| Claude Code devcontainer | Docker container | Firewall (iptables) | Container FS | Yes (in container) |
| Claude Code /sandbox (Linux) | bubblewrap namespaces | Domain allowlist proxy | Path-restricted | No (user-level) |
| Codex CLI | Docker container | Restricted | Container FS | Yes (in container) |
| Daytona | Docker container | Configurable | Container FS | Configurable |

---

## 2. eBPF in Docker and Container Environments

### 2.1 How eBPF Requires Privileges

eBPF programs are loaded with the `bpf()` syscall and require elevated permissions. The relevant capabilities, all introduced in Linux 5.8, are:

| Capability | Purpose |
|-----------|---------|
| `CAP_BPF` | Load BPF maps, programs; load BTF data; retrieve JITed code |
| `CAP_PERFMON` | Call `perf_event_open()`; use BPF operations with perf implications |
| `CAP_SYS_ADMIN` | Legacy catch-all; still required for some eBPF map types and older kernels |
| `CAP_SYS_PTRACE` | Trace arbitrary processes; read `/proc/<pid>/maps` for uprobe address resolution |

Prior to Linux 5.8, `CAP_SYS_ADMIN` was required for all eBPF operations. Linux 5.8 introduced `CAP_BPF` and `CAP_PERFMON` to enable least-privilege use. For tracing programs (uprobes, kprobes), in practice you still need all of `CAP_BPF + CAP_PERFMON + CAP_SYS_PTRACE`.

Docker's default seccomp profile **blocks the `bpf()` syscall entirely**, meaning eBPF cannot be used in a standard unprivileged container without modifications.

### 2.2 Docker Flags for eBPF

**Option A: Full privileged (simplest, least secure)**
```bash
docker run --privileged ...
```
Grants all capabilities and disables seccomp and AppArmor. Sufficient for all eBPF operations. Used by Tracee, Tetragon, and AgentSight in their Docker examples.

**Option B: Minimal capability set (modern kernels >= 5.8)**
```bash
docker run \
  --cap-add=BPF \
  --cap-add=PERFMON \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  ...
```
Still requires `--security-opt seccomp=unconfined` because Docker's default seccomp profile blocks `bpf()` regardless of capabilities. AppArmor may also need adjustment.

**Option C: Legacy kernels (< 5.8), requires SYS_ADMIN**
```bash
docker run \
  --cap-add=SYS_ADMIN \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  ...
```

**Note on `perf_event_paranoid`**: The host kernel's `/proc/sys/kernel/perf_event_paranoid` setting (default: 2) restricts unprivileged perf access. Level 2 disallows kernel profiling without `CAP_PERFMON`. This is a host-level sysctl and applies to all containers unless they have `CAP_SYS_ADMIN` (which allows setting it per namespace).

### 2.3 Namespace Isolation and eBPF Visibility

eBPF programs loaded on the host have visibility into **all processes** across all containers sharing the same kernel. This is the fundamental property that makes host-level eBPF monitoring so powerful.

However, eBPF programs themselves are subject to namespace restrictions in the following ways:
- **PID namespace**: `bpf_get_current_pid_tgid()` returns the PID as seen from the initial PID namespace (host PID). Container-internal PIDs differ. When monitoring from a container, you need `--pid=host` to ensure PIDs are consistent.
- **Mount namespace**: For uprobe attachment, the binary path used in `SEC("uprobe/path:symbol")` must be accessible from the monitor's mount namespace. Mounting `/usr`, `/lib`, and `/proc` from the host into the monitor container (as AgentSight does) addresses this.
- **Network namespace**: eBPF programs attached to `tc` (traffic control) or XDP hooks are per-interface. To monitor cross-container traffic, attach at the host network namespace level.
- **Cgroup namespace**: `--cgroupns=host` is needed when the monitor needs to identify containers by cgroup path.

### 2.4 Uprobe-Specific Constraints in Containers

Uprobes (what AgentSight's `sslsniff` uses) require:

1. **Binary accessibility**: The uprobe must be attached to a specific binary file path. The monitor must be able to open the target binary. This is why AgentSight mounts `-v /usr:/usr:ro -v /lib:/lib:ro` — these paths contain `libssl.so` or the target application binary.
2. **PID visibility**: `--pid=host` allows the monitor to see all host processes and their memory maps.
3. **No VM boundary crossing**: Uprobes cannot reach across a VM hypervisor boundary. They are purely a kernel→userspace instrumentation mechanism within a single kernel instance.

Key implication: **eBPF uprobes work for Docker containers but NOT for VM-based sandboxes** (E2B, Fly.io Machines, Kata Containers, Firecracker) when the monitor runs outside the VM.

### 2.5 seccomp-BPF vs. eBPF Tracing

These are two different uses of BPF that are often confused:

| | seccomp-BPF | eBPF Tracing |
|---|---|---|
| **Purpose** | Filter/restrict syscalls for security policy | Observability and monitoring |
| **Attachment point** | Per-process, at syscall entry | kprobes, uprobes, tracepoints |
| **Kernel version** | 3.5+ | 4.1+ (uprobes: 4.1+; ringbuf: 5.8+) |
| **Privilege** | Can be used by unprivileged processes | Requires `CAP_BPF` or `CAP_SYS_ADMIN` |
| **Scope** | Only the current process and descendants | System-wide |
| **Docker default** | Applied by default (restricts ~44 syscalls) | Blocked by default |

Docker's default seccomp profile blocks `bpf()`, `ptrace()`, `clone()` with new namespace flags, and other syscalls that eBPF tracing tools depend on. This is why eBPF monitors always need `--security-opt seccomp=unconfined` or `--privileged`.

### 2.6 Docker Desktop (macOS and Windows)

Docker Desktop on macOS and Windows runs containers inside a Linux VM (using Apple's Virtualization.framework on ARM, or QEMU/HyperKit on Intel). The eBPF programs run inside this VM, not on the macOS/Windows host. Implications:
- eBPF monitoring from "the host" on macOS actually means from within the Docker Desktop Linux VM.
- The Linux VM kernel version determines eBPF feature availability (Docker Desktop ships a recent kernel).
- There is no way to reach macOS or Windows processes from this eBPF environment.
- Cross-container monitoring within Docker Desktop works fine — all containers share the same Linux VM kernel.

### 2.7 Rootless Docker and Podman

Rootless Docker (running dockerd as a non-root user) and Podman (rootless OCI containers) use user namespaces. In this mode:
- eBPF tracing programs require `CAP_BPF + CAP_PERFMON` in the **initial user namespace** — i.e., the user running the monitor must have these capabilities on the host, or the monitor must run as root.
- Rootless containers themselves do NOT get these capabilities.
- Falco explicitly documents that it does not support rootless Docker environments without additional configuration.
- For AgentSight, running the monitor itself as root (or with the appropriate capabilities) while monitoring rootless containers still works, because eBPF operates at the kernel level regardless of which user namespace launched the container.

---

## 3. Deployment Architectures

### Architecture A: Host-Level Monitor (Current AgentSight Model)

```
┌─────────────────────────────────────────────────────────────────┐
│ Host                                                             │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │ AgentSight (host)    │    │ AI Agent Container           │   │
│  │                      │    │                              │   │
│  │  sslsniff (uprobe)  ─┼───>│  libssl / BoringSSL         │   │
│  │  process (tracepoint)│    │  Node.js / Python / Claude   │   │
│  └──────────────────────┘    └──────────────────────────────┘   │
│                                                                  │
│  Kernel: eBPF programs loaded here, see all containers          │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:** AgentSight runs directly on the host with `sudo` (or `CAP_BPF + CAP_PERFMON + CAP_SYS_PTRACE`). The eBPF programs load into the host kernel and hook into any process on the host — including those running inside Docker containers. `--pid=host` is not needed when running on the actual host.

**Docker invocation of AgentSight itself:**
```bash
docker run --privileged --pid=host --network=host \
  -v /sys:/sys:ro -v /usr:/usr:ro -v /lib:/lib:ro \
  -v $HOME/.local/share/claude:/claude:ro \
  -v $(pwd)/logs:/logs \
  ghcr.io/eunomia-bpf/agentsight:latest \
  record --comm claude --binary-path /claude/versions/2.1.39 --log-file /logs/record.log
```

**Pros:**
- Simplest architecture.
- Monitors all containers on the host simultaneously.
- Cannot be disabled by the monitored agent (kernel-level).
- No changes to the agent container.

**Cons:**
- Requires host access or `--privileged` on the monitor container.
- Does not work with VM-based sandboxes (E2B, Fly.io, Kata).
- In a cloud multi-tenant environment, "the host" is typically a VM; the operator of that VM must install AgentSight.
- Cannot monitor agents running on other machines without deploying an AgentSight instance there.

**Feasibility:** Production-ready for single-host deployments. Used by AgentSight today.

---

### Architecture B: Privileged Sidecar Container

```
┌─────────────────────────────────────────────────────────────────┐
│ Docker Compose / Kubernetes Pod                                  │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │ AgentSight Sidecar   │    │ AI Agent Container           │   │
│  │ (--privileged)       │    │ (unprivileged)               │   │
│  │                      │    │                              │   │
│  │  sslsniff (uprobe)  ─┼───>│  libssl / BoringSSL         │   │
│  │  process (tracepoint)│    │  Node.js / Python / Claude   │   │
│  └──────────────────────┘    └──────────────────────────────┘   │
│                                                                  │
│  Shared: --pid=host or shared PID namespace                     │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:** A second container in the same pod or Docker Compose stack runs AgentSight with `--privileged` (or `--cap-add=BPF --cap-add=PERFMON --cap-add=SYS_PTRACE --security-opt seccomp=unconfined`). PID namespace sharing allows the sidecar to see the agent's processes.

**Docker Compose example:**
```yaml
version: '3.8'
services:
  agent:
    image: my-ai-agent:latest
    # unprivileged

  agentsight:
    image: ghcr.io/eunomia-bpf/agentsight:latest
    privileged: true
    pid: host          # or 'service:agent' to share only with this container
    volumes:
      - /sys:/sys:ro
      - /usr:/usr:ro
      - /lib:/lib:ro
    command: record --comm python --log-file /logs/record.log
```

**Kubernetes Pod spec:**
```yaml
spec:
  shareProcessNamespace: true   # shares PID namespace within the pod
  containers:
  - name: agent
    image: my-ai-agent:latest
    # no special privileges

  - name: agentsight
    image: ghcr.io/eunomia-bpf/agentsight:latest
    securityContext:
      privileged: true
    volumeMounts:
    - name: sys
      mountPath: /sys
      readOnly: true
  volumes:
  - name: sys
    hostPath:
      path: /sys
```

**Important note on `pid: service:agent` vs `pid: host`:** Docker Compose supports `pid: "service:agent"` which shares only the PID namespace of the named service (not the full host). However, eBPF programs loaded inside the sidecar still load into the **host kernel** due to how eBPF works — they are not namespaced. This means the sidecar will see all host processes, not just the agent, once eBPF programs are active. The `--comm` filter in AgentSight limits captured data to the target process name.

**Pros:**
- Isolates privileged workload (monitor) from agent container.
- Agent container remains unprivileged.
- Works with any container orchestration system.
- Can be shipped as part of the agent deployment manifest.

**Cons:**
- Still requires a privileged container somewhere in the pod.
- Security teams may object to `--privileged` in production.
- Sidecar adds resource overhead per pod (memory for eBPF maps and ring buffers).
- PID namespace sharing must be explicitly configured (`shareProcessNamespace: true` in Kubernetes).

**Feasibility:** Straightforward to implement. This is how Tetragon and Tracee are deployed in containerized environments.

---

### Architecture C: Kubernetes DaemonSet

```
┌─────────────────────── Node 1 ───────────────────────────────┐
│                                                                │
│  ┌─────────────────────────────────┐                          │
│  │ AgentSight DaemonSet Pod        │                          │
│  │ (privileged, --pid=host)        │                          │
│  │                                 │                          │
│  │  Monitors ALL pods on this node │                          │
│  └─────────────────────────────────┘                          │
│                                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ Agent Pod A    │  │ Agent Pod B    │  │ Agent Pod C    │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

**DaemonSet manifest (excerpt):**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: agentsight
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: agentsight
  template:
    spec:
      hostPID: true
      hostNetwork: true
      containers:
      - name: agentsight
        image: ghcr.io/eunomia-bpf/agentsight:latest
        securityContext:
          privileged: true
        volumeMounts:
        - name: sys
          mountPath: /sys
          readOnly: true
        - name: usr
          mountPath: /usr
          readOnly: true
        - name: lib
          mountPath: /lib
          readOnly: true
      volumes:
      - name: sys
        hostPath: { path: /sys }
      - name: usr
        hostPath: { path: /usr }
      - name: lib
        hostPath: { path: /lib }
      tolerations:
      - operator: Exists    # Run on all nodes including tainted ones
```

**Kubernetes Pod Security Standards:** The Privileged PSS profile must be used for the DaemonSet namespace (or an exemption must be granted), because DaemonSet pods need `hostPID: true` and `privileged: true`. The Baseline and Restricted profiles both forbid these.

**Pros:**
- One DaemonSet covers all agent pods on all nodes.
- Standard pattern used by Falco, Tetragon, Tracee, Datadog Agent.
- Centralized configuration; single place to update.
- New agent pods are automatically monitored when scheduled.

**Cons:**
- Requires cluster-admin access to deploy privileged DaemonSets.
- In multi-tenant clusters, this grants broad visibility across all tenants.
- DaemonSets count against node resource limits.
- All events from all nodes must be aggregated — requires a backend (Prometheus, Loki, custom).

**Feasibility:** Industry-standard approach. Directly applicable to AgentSight with minor manifest additions.

---

### Architecture D: Embedded in Sandbox Image

In this architecture, the eBPF monitor is baked into the agent container image and runs as a background process alongside the agent.

```
┌─────────────────────────────────────────────────────┐
│ Single Container (privileged or with CAP_BPF)       │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Supervisor (supervisord / s6-overlay)         │   │
│  │                                               │   │
│  │  Process 1: AI Agent (python / node / etc.)  │   │
│  │  Process 2: agentsight record -c agent        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Dockerfile example:**
```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y supervisor libelf1 python3

# Install AgentSight
COPY agentsight /usr/local/bin/agentsight

# Install agent
COPY my_agent.py /app/my_agent.py

# Supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-n"]
```

**supervisord.conf:**
```ini
[program:agent]
command=python3 /app/my_agent.py
autostart=true

[program:agentsight]
command=agentsight record -c python --log-file /logs/record.log
autostart=true
user=root
```

**Pros:**
- No separate sidecar or DaemonSet needed.
- Can work with sandbox providers that allow privileged containers.
- Monitor runs in the same security domain as the agent.
- Useful for debugging agent behavior in development.

**Cons:**
- The agent can detect and potentially disable its monitor (monitor is co-located).
- Requires building a custom container image per agent type.
- Monitoring is tied to the container lifecycle — if the container crashes, monitor data may be lost.
- Container still needs elevated privileges for eBPF.
- Not suitable for security-sensitive production use (monitor and monitored share trust domain).

**Feasibility:** Good for development and debugging use cases. Not appropriate for adversarial monitoring scenarios.

---

### Architecture E: eBPF-as-a-Service / Centralized Agent

This model is how Falco, Tetragon, and Datadog Cloud Workload Security operate in production. A centralized eBPF management service runs on each node, exposing a policy and event API that other services consume.

```
┌──────────── Node ─────────────────────────────────────────────┐
│                                                                │
│  ┌────────────────────────────────┐                           │
│  │ eBPF Agent (e.g. Tetragon)    │──► Central Event Store    │
│  │ (DaemonSet, privileged)        │    (Kafka / Loki / S3)   │
│  └────────────────────────────────┘                           │
│          ↑ shares kernel                                       │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ All agent pods on this node                            │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
              ↓ events flow to
┌───────────────────────────────────────────────────────────────┐
│ Central Backend                                                │
│  AgentSight Analyzer ─► PostgreSQL / ClickHouse / TimescaleDB │
└───────────────────────────────────────────────────────────────┘
```

**Pros:**
- Fully decoupled monitoring from agent deployment.
- Single eBPF agent per node covers all workloads.
- Existing infrastructure (Falco/Tetragon) can be extended with AI-specific analyzers.
- Scales horizontally.

**Cons:**
- High integration complexity.
- The existing tools (Falco, Tetragon) focus on security events — they do not capture SSL/TLS payload content the way AgentSight does.
- Adding SSL payload capture to Tetragon would require custom TracingPolicy CRDs with uprobe attachment to OpenSSL/BoringSSL — feasible but non-trivial.
- Adds latency to event processing pipeline.

**Feasibility:** Medium-term. Adding AgentSight's SSL payload capture to the Tetragon/Falco event pipeline would make this the most production-grade architecture.

---

### Architecture Comparison Matrix

| Architecture | Agent change needed? | Privileged needed? | VM sandbox works? | Multi-host? | Production-grade? |
|---|---|---|---|---|---|
| A: Host-level | No | Yes (host root) | No | No | Yes (for single-host) |
| B: Sidecar | No (compose change) | Yes (sidecar) | No | With orchestration | Yes |
| C: DaemonSet | No | Yes (DaemonSet) | No | Yes (per-node) | Yes |
| D: Embedded | Yes (image rebuild) | Yes (in container) | No | No | Dev/debug only |
| E: eBPF-as-a-service | No | Yes (eBPF agent) | No | Yes | Yes (complex) |

---

## 4. CLI and Syscall Interception in Sandboxes

Beyond SSL/TLS traffic, AI agents interact with the system through shell commands, file operations, and network connections. eBPF can monitor all of these.

### 4.1 Process Execution Monitoring (execve/execveat)

**eBPF attachment point:** `tracepoint/syscalls/sys_enter_execve` and `tracepoint/syscalls/sys_enter_execveat`.

AgentSight's `process.bpf.c` already uses this via the tracepoint-based process monitor. It captures:
- Command name (`comm`)
- Full argument list (`argv`)
- Parent PID and parent command
- Working directory
- Exit code and duration

**Example: tracking what commands Claude Code runs**
```
{"type":"exec","pid":12345,"ppid":12300,"comm":"git","command":"git diff HEAD","timestamp_ns":1710000000000}
{"type":"exec","pid":12346,"ppid":12300,"comm":"npm","command":"npm test","timestamp_ns":1710000001000}
```

This provides a full audit trail of every shell command an AI agent runs, which is invaluable for:
- Detecting unexpected commands (e.g., `curl` to an unexpected domain).
- Correlating shell commands with the LLM API requests that preceded them.
- Building a timeline of agent actions.

**Kernel requirement:** Tracepoints for `execve` are available since kernel 4.7. CO-RE-based programs need 5.8+.

### 4.2 File System Monitoring (openat, read, write, unlink)

**eBPF attachment points:** `tracepoint/syscalls/sys_enter_openat`, `sys_enter_unlinkat`, `sys_enter_renameat`, or `LSM hooks` for policy enforcement.

Relevant for AI agent monitoring:
- Which source files did the agent read before making a change?
- Which configuration files did it access?
- Did it access secrets (`.env`, `~/.ssh/id_rsa`, `.aws/credentials`)?
- What files did it create or modify?

**BPF LSM (Linux Security Modules)** — available since Linux 5.7 with `CONFIG_BPF_LSM=y` — allows eBPF programs to be attached to LSM hooks (e.g., `lsm/file_open`, `lsm/bprm_check_security`). This enables **policy enforcement** (return `-EPERM` to deny the operation) rather than just observation.

Example use: block an AI agent from reading private key files even if it tries to do so. This requires `BPF_PROG_TYPE_LSM` and `CAP_MAC_ADMIN`.

### 4.3 Network Connection Monitoring (connect, bind, sendmsg)

**eBPF attachment points:** `tracepoint/syscalls/sys_enter_connect`, `kprobe/tcp_connect`, or cgroup eBPF programs.

Captures:
- Which IP addresses and ports the agent connects to.
- DNS queries (via monitoring UDP port 53).
- Data volumes per connection.

**cgroup-based eBPF (BPF_PROG_TYPE_CGROUP_SKB, BPF_PROG_TYPE_CGROUP_SOCK):** Programs can be attached to a cgroup (which maps to a container in Docker/Kubernetes). This allows per-container network policy enforcement without requiring `--net=host`. Available since Linux 4.10 (cgroup v2 integration).

```bash
# Attach an eBPF program to a container's cgroup for network monitoring
# Identify cgroup from: cat /sys/fs/cgroup/system.slice/docker-<id>.scope/...
bpftool cgroup attach /sys/fs/cgroup/... connect4 pinned /sys/fs/bpf/monitor_connect4
```

### 4.4 bash readline Interception

AgentSight's `process.bpf.c` already includes a `uretprobe` on `/usr/bin/bash:readline`:

```c
SEC("uretprobe//usr/bin/bash:readline")
int BPF_URETPROBE(bash_readline, const void *ret)
```

This captures typed bash commands before they are executed — useful for capturing interactive agent commands and distinguishing them from programmatically-generated subcommands.

### 4.5 stdio Capture (stdiocap)

AgentSight includes `stdiocap`, a BPF tool that captures stdin/stdout/stderr of a specific PID by attaching uprobes to the `read()` and `write()` syscalls on file descriptors 0, 1, and 2. This is particularly useful for:
- MCP servers communicating over stdio.
- Agent subprocesses that do not use TLS.
- Capturing raw output of tools like `git`, `npm`, `cargo`.

Usage:
```bash
sudo ./bpf/stdiocap -p <mcp_server_pid>
```

### 4.6 Comparison with Existing Sandbox Isolation Tools

| Tool | Mechanism | Monitoring? | Enforcement? | Container-compatible? |
|---|---|---|---|---|
| gVisor | Intercepts all syscalls in user-space (ptrace or KVM) | Indirect only | Yes (deny syscalls) | Yes (OCI runtime) |
| Kata Containers | Full VM per container | Via guest eBPF only | Via VM hypervisor | Yes (OCI runtime) |
| seccomp-BPF | Classic BPF filter on syscalls | No (filter only) | Yes (SECCOMP_RET_KILL) | Yes (default in Docker) |
| BPF LSM | eBPF programs on LSM hooks | Yes | Yes (return -EPERM) | Requires kernel 5.7+ |
| AgentSight (eBPF) | uprobes + tracepoints | Yes (rich payload) | No (observation only) | Yes (with --privileged) |

**gVisor** is particularly interesting in the context of AI agent sandboxing. It intercepts every syscall the container makes by running an application kernel (the Sentry) in userspace. All syscalls must pass through the Sentry before reaching the host kernel. This provides strong isolation but:
1. Reduces host kernel attack surface by ~30% (237 of ~350 syscalls supported).
2. Incurs significant performance overhead for syscall-heavy workloads.
3. Makes eBPF uprobes inside the gVisor container **not visible to host eBPF** because the Sentry mediates system interactions — the host kernel may not see `SSL_read()` uprobes from inside a gVisor container at all.

**For AgentSight specifically:** gVisor sandboxes are incompatible with the current uprobe-based SSL monitoring approach because uprobes rely on the host kernel executing the binary's SSL functions directly. With gVisor, the Sentry intercepts those calls.

---

## 5. Existing Solutions and Prior Art

### 5.1 Falco

Falco ([falco.org](https://falco.org)) is a CNCF project for runtime security monitoring. It uses eBPF to detect anomalous behavior in containers.

**Drivers:**
- Modern eBPF probe (default, kernel >= 5.8, requires BTF at `/sys/kernel/btf/vmlinux`): needs `CAP_BPF + CAP_PERFMON + CAP_SYS_RESOURCE + CAP_SYS_PTRACE`
- Legacy eBPF probe (deprecated in v0.43, kernel >= 4.14): needs `CAP_SYS_ADMIN + CAP_SYS_RESOURCE + CAP_SYS_PTRACE`
- Kernel module (oldest, kernel >= 3.10): requires full privileges

**Deployment:**
- Docker: `docker run --privileged --pid=host --cgroupns=host -v /var/run:/var/run:ro falcosecurity/falco`
- Kubernetes: DaemonSet with hostPID, hostNetwork, and privileged security context (or specific capabilities for modern eBPF)

**What Falco captures:** Syscall-level events (execve, open, connect, etc.). It does NOT capture SSL/TLS payload content. For AI agent monitoring, Falco can detect "agent executed unexpected command" but cannot capture the LLM prompt/response.

**Relevance to AgentSight:** Falco's Rules engine could be extended with AI agent-specific rules. The AgentSight use case goes deeper than Falco's typical threat-detection focus.

### 5.2 Tetragon (Cilium)

Tetragon ([tetragon.io](https://tetragon.io)) is Cilium's eBPF security observability and runtime enforcement tool. Key differentiator from Falco: Tetragon can apply policies and **enforce** them in-kernel (terminate processes, block syscalls) using BPF programs.

**Deployment (Docker):**
```bash
docker run --name tetragon --rm -d \
    --pid=host --cgroupns=host --privileged \
    -v /sys/kernel/btf/vmlinux:/var/lib/tetragon/btf \
    quay.io/cilium/tetragon:v1.6.0
```

**TracingPolicy CRDs (Kubernetes):** Tetragon allows defining custom eBPF tracing policies as Kubernetes CRDs. For example, attaching uprobes to SSL functions is theoretically expressible as a TracingPolicy, though this is not a built-in feature.

**Relevance to AgentSight:** Tetragon's `TracingPolicy` API could be used to deploy AgentSight's SSL probes across a cluster without writing DaemonSet manifests. However, Tetragon's event serialization format differs from AgentSight's.

### 5.3 Tracee (Aqua Security)

Tracee ([aquasecurity.github.io/tracee](https://aquasecurity.github.io/tracee)) provides 400+ system call monitoring, network event detection, and forensic capabilities. It exports to Falco-compatible event formats.

**Docker deployment:**
```bash
docker run --name tracee -it --rm \
  --pid=host --cgroupns=host --privileged \
  -v /etc/os-release:/etc/os-release-host:ro \
  -v /var/run:/var/run:ro \
  aquasec/tracee:latest
```

**Relevance to AgentSight:** Tracee's network capture feature (`--capture network`) and its support for forensic binary capture are complementary to AgentSight's SSL focus. However, Tracee also does not capture SSL plaintext — it can see encrypted TCP payloads but not the decrypted content.

### 5.4 Datadog Cloud Workload Security

Datadog's CWS product uses eBPF for runtime security monitoring in container environments. It focuses on file integrity monitoring (FIM), network anomaly detection, and process execution tracking. Like Falco and Tracee, it does not capture SSL plaintext.

### 5.5 What Distinguishes AgentSight

The key capability that distinguishes AgentSight from all the above tools is **SSL/TLS payload capture**:

- Falco, Tetragon, Tracee, and Datadog CWS can tell you "process X made a TCP connection to api.anthropic.com:443."
- AgentSight tells you the **actual prompt and response** inside that connection.

This is the critical data point for AI agent observability. The prompt and response contain:
- What task the agent was performing.
- What tool calls the agent made.
- What the LLM decided to do next.
- Evidence of prompt injection attempts.

No other production-grade eBPF monitoring tool currently captures this data.

---

## 6. Practical Considerations

### 6.1 Performance Overhead

AgentSight claims less than 3% CPU overhead. This is consistent with how eBPF tools are designed — data collection happens in kernel space, with ring buffers minimizing copies. Key performance factors:

- **Ring buffer size:** AgentSight uses `BPF_MAP_TYPE_RINGBUF` (kernel 5.8+). The ring buffer size is configured in the eBPF program. If the buffer fills (high-traffic agent), events are dropped.
- **SSL payload size:** Large API responses (multi-turn conversations, large context windows) generate large SSL read events. The AgentSight HTTP parser accumulates SSE chunks — this is the primary memory pressure point.
- **Concurrent agents:** Monitoring multiple agents simultaneously multiplies event volume. The `--comm` filter limits eBPF events to specific process names, reducing overhead.

**For production:** Per-container monitoring with specific `--comm` filters is advisable over broad system-wide monitoring.

### 6.2 Ephemeral and Short-Lived Containers

AI agent containers are often ephemeral — spawned for a single task and then terminated. Challenges:
- eBPF uprobes are attached based on binary path. If the container is removed, the binary is gone, but the uprobe remains (it will simply never trigger again). This is safe but requires cleanup.
- For very short-lived containers (< 1 second), AgentSight's startup time may cause it to miss initial SSL traffic. The uprobe attaches at program start; the agent may have already completed its first API call.

**Mitigation:** Pre-attach uprobes to known binary paths at monitor startup, before any agents launch. For dynamically-discovered paths, use the process monitor to watch for `execve` events and attach uprobes when new agent processes start.

### 6.3 Data Collection from Multiple Sandboxes

For a fleet of agent sandboxes, event data must be aggregated. Options:
1. **Per-host JSON log files** (current AgentSight default): Simple, but requires log shipping (Fluentd, Filebeat, Promtail).
2. **OpenTelemetry export**: AgentSight's architecture supports this via the Rust analyzer framework. Add an OTLP exporter analyzer.
3. **Central webhook**: Send events to a webhook endpoint as they are collected (low latency, suitable for real-time monitoring).
4. **DaemonSet + Prometheus**: Export metrics (token counts, latency, error rates) to Prometheus; export raw logs to Loki.

### 6.4 Handling Binary Diversity

Different AI agent deployments use different SSL libraries:
- Python agents (aider, open-interpreter): use system `libssl.so` — standard uprobe attachment works.
- Node.js agents with NVM: statically link OpenSSL — require `--binary-path`.
- Claude Code (Bun): statically links BoringSSL with stripped symbols — require `--binary-path` AND byte-pattern matching.
- Java agents (various): use Java's built-in TLS (JSSE) — can hook via `javax.net.ssl.SSLSocket` but requires JVM-specific uprobe placement.
- Go agents: use Go's `crypto/tls` package — hook `crypto/tls.(*Conn).Read` and `(*Conn).Write`.

In containerized environments, you must mount the binary paths into the monitor container. For dynamic containers where the binary path is not known ahead of time, watch `execve` events and attach uprobes reactively.

### 6.5 Privacy and Security Implications

SSL payload capture captures ALL traffic from the monitored process, not just LLM API calls:
- Authentication tokens and API keys in HTTP headers.
- User data (file contents, code snippets passed to the LLM).
- Third-party API credentials.

Mitigations:
- AgentSight includes an `AuthHeaderRemover` analyzer that strips `Authorization` headers.
- Add additional analyzers to redact PII patterns (email addresses, credit card numbers, etc.).
- Encrypt log files at rest.
- Apply access controls to the AgentSight web server (`--server-port` endpoint is unauthenticated by default).
- In multi-tenant environments, each tenant's monitor should only have access to their own data.

**Legal considerations:** In enterprise deployments, employees may have a reasonable expectation that their code and prompts are private. Capture policies should be disclosed in organizational security policies.

### 6.6 Compatibility Matrix

| Environment | eBPF Uprobe Support | Notes |
|---|---|---|
| Linux kernel >= 5.8 (native Docker) | Full support | Recommended. BTF required for CO-RE. |
| Linux kernel 4.1-5.7 (older distros) | Partial | Ring buffer unavailable; use perf buffer. No BPF LSM. |
| Docker Desktop (macOS) | Supported (in Linux VM) | Cannot monitor macOS-native processes. |
| Docker Desktop (Windows) | Supported (in Hyper-V VM) | Cannot monitor Windows-native processes. |
| Rootless Docker | Monitor must run as root | Containers can be rootless; monitor cannot. |
| Podman (rootless) | Same as rootless Docker | |
| gVisor containers | Not supported for uprobe | gVisor intercepts syscalls, breaking uprobe delivery. |
| Kata Containers | Not from host | Deploy monitor inside guest; monitor has full eBPF access inside VM. |
| Firecracker / E2B / Fly.io | Not from host | VM boundary is opaque to host eBPF. |
| Kubernetes (standard runtime) | Full support | DaemonSet with hostPID + privileged. |
| Kubernetes + gVisor (gke-sandbox) | Not for gVisor pods | Works for non-gVisor pods on same node. |

---

## 7. Recommendations for AgentSight

### 7.1 Short-Term: Sidecar Container Support

Publish an official Docker Compose sidecar template that allows deploying AgentSight alongside any AI agent container. Minimal changes needed:

1. Add documentation for `--pid=host` vs `pid: "service:agent"` in Docker Compose.
2. Test and document the `--cgroupns=host` requirement for accurate container identification.
3. Add a `--container-id` filter to AgentSight's CLI to limit monitoring to a specific container (by matching cgroup path).

### 7.2 Short-Term: Kubernetes DaemonSet Manifest

Provide an official DaemonSet manifest and Helm chart for deploying AgentSight in Kubernetes. Include:
- `hostPID: true`, `hostNetwork: true`, privileged security context.
- Host volume mounts for `/sys`, `/usr`, `/lib`.
- Tolerations to run on all nodes.
- Service for accessing the web UI.
- ConfigMap for `--comm` and `--binary-path` configuration.

### 7.3 Medium-Term: Dynamic Uprobe Attachment

The current model requires knowing the binary path ahead of time (`--binary-path`). For dynamic sandboxes where agent containers are ephemeral:

1. Use the process monitor (`execve` tracepoint) to detect new agent process launches.
2. On detection, read `/proc/<pid>/exe` to discover the binary path.
3. Reactively attach uprobes to the discovered binary.

This would make AgentSight fully automatic for containerized environments — no pre-configuration of binary paths needed.

### 7.4 Medium-Term: VM Sandbox Support via In-Guest Agent

For VM-based sandboxes (E2B, Fly.io Machines, Kata Containers), eBPF monitoring from outside the VM is not feasible. An alternative:

1. Build a minimal AgentSight agent (just sslsniff + process monitor, no frontend) that can be injected into the guest VM.
2. For E2B: provide an E2B custom sandbox template that includes the AgentSight agent. The agent runs inside the VM and exports events via HTTP to a collector outside the VM.
3. For Fly.io: provide a Fly Machine configuration that bundles the AgentSight agent and exports events to a fly.io-external collector.

This is the only viable approach for VM-isolated sandboxes.

### 7.5 Long-Term: Integration with Tetragon TracingPolicy

Tetragon's `TracingPolicy` CRD allows expressing uprobe attachment policies as Kubernetes resources. Adding AgentSight's SSL capture capability to Tetragon would allow cluster operators to deploy one eBPF framework (Tetragon) that handles both security enforcement and AI agent observability. This requires:

1. Contributing an SSL/TLS uprobe capture feature to Tetragon, or
2. Implementing a Tetragon TracingPolicy that exports raw SSL buffer events and processing them in AgentSight's analyzer.

### 7.6 Security Hardening for Production

For production deployments:
1. Replace `--privileged` with the minimal capability set: `--cap-add=BPF --cap-add=PERFMON --cap-add=SYS_PTRACE --security-opt seccomp=unconfined`.
2. Add authentication to the AgentSight web server (currently unauthenticated).
3. Enable TLS on the web server for remote access.
4. Implement data retention policies and log rotation (AgentSight has log rotation support per `LOG_ROTATION_DESIGN.md`).
5. Add a `--redact` analyzer that strips sensitive patterns from captured payloads before storage.

---

## Summary

eBPF-based monitoring via AgentSight is well-suited to Docker container environments but faces hard limitations with VM-based sandboxes:

- **Docker containers** sharing the host kernel: full eBPF visibility (SSL payload, process events, file operations, network connections).
- **VM-based sandboxes** (E2B, Fly.io, Kata, Firecracker): eBPF from outside the VM is blocked by the hypervisor boundary; requires deploying an in-guest monitor.
- **gVisor-sandboxed containers**: eBPF uprobes are not effective because gVisor mediates syscalls; the host kernel does not execute the container's SSL library code directly.

The three architectures with the best production fit are:
1. **Architecture A (host-level)** for single-machine deployments.
2. **Architecture B (sidecar)** for per-deployment monitoring in Docker Compose or Kubernetes.
3. **Architecture C (DaemonSet)** for cluster-wide coverage.

The combination of process execution tracing (execve), file access monitoring (openat), network connection tracking (connect), and SSL plaintext capture provides complete visibility into AI agent behavior — covering what the agent was told to do (LLM API response), what it decided to do (tool calls), what commands it ran (execve), what files it accessed (openat), and where it sent data (connect).

---

## References

- AgentSight repository: [github.com/eunomia-bpf/agentsight](https://github.com/eunomia-bpf/agentsight)
- Falco documentation: [falco.org/docs](https://falco.org/docs)
- Tetragon: [tetragon.io/docs](https://tetragon.io/docs)
- Tracee: [aquasecurity.github.io/tracee](https://aquasecurity.github.io/tracee)
- Linux capabilities(7) man page: `CAP_BPF`, `CAP_PERFMON` introduced in kernel 5.8
- Kubernetes Pod Security Standards: [kubernetes.io/docs/concepts/security/pod-security-standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- Claude Code Security: [code.claude.com/docs/en/security](https://code.claude.com/docs/en/security)
- Claude Code Sandboxing: [code.claude.com/docs/en/sandboxing](https://code.claude.com/docs/en/sandboxing)
- gVisor Architecture: [gvisor.dev](https://gvisor.dev)
- Falco modern eBPF probe: requires kernel >= 5.8 with BTF at `/sys/kernel/btf/vmlinux`
- Docker seccomp documentation: [docs.docker.com/engine/security/seccomp](https://docs.docker.com/engine/security/seccomp/)
- `perf_event_paranoid` sysctl: defaults to 2; controls unprivileged perf/eBPF access
- BPF LSM: available since kernel 5.7 with `CONFIG_BPF_LSM=y` and `lsm=...,bpf` kernel parameter
- E2B: [e2b.dev](https://e2b.dev) — Firecracker microVM-based AI agent sandboxes
- Fly.io Machines: [fly.io/docs/machines](https://fly.io/docs/machines) — VM-based, sub-second startup
