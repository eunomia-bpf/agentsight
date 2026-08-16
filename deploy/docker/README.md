# session-capture image

`Dockerfile.session-capture` packages the AgentSight collector in bridge-serve
mode — the component ARO calls **session capture**. It runs one command:

```
agentsight top --bridge-socket /run/aro/bridge.sock --headless
```

`top` refreshes a registry of live agent sessions (from the process table and
the agents' own transcripts) and the bridge server answers host-session queries
from that same registry. ARO's `aro-hostd` is the consumer on the other end of
the socket.

Published by `.github/workflows/session-capture-image.yml` to
`ghcr.io/<owner>/agent-sandbox/session-capture`, linux/amd64, tagged
`sha-<short7>` (immutable, what deploys pin) and `main` (moving, what local
compose files track).

Build it yourself from the repository root:

```
docker build -f deploy/docker/Dockerfile.session-capture -t session-capture .
```

## The bridge socket contract

The collector binds a Unix stream socket at the path given to
`--bridge-socket`, `/run/aro/bridge.sock` by default. Share it with `aro-hostd`
by mounting the *directory* — `/run/aro` — into both containers.

Three properties of that directory and socket are enforced by the collector at
startup, because the filesystem is the bridge's authentication boundary:

- **The parent directory must not be group- or world-accessible.** `/run/aro`
  is created `0700` in the image, which is what a Docker *named* volume mounted
  there inherits. A bind mount keeps the host directory's mode, and a `tmpfs`
  mount defaults to `1777` — either will fail the check with
  `bridge socket directory /run/aro must not be group- or world-accessible`.
  Fix it on the host (`chmod 700`) or with `tmpfs` mount options (`mode=0700`).
- **The parent must be a real directory, not a symlink.**
- **The socket is created `0600`, and the peer must share the collector's uid.**
  On Linux the collector checks `SO_PEERCRED` and rejects a connection whose uid
  differs from its own: `peer uid does not match the collector uid`. The image
  runs as root, so `aro-hostd` must connect as root too — or both must be run
  with the same `--user`.

A stale socket file from a previous run is removed at bind time; a
non-socket file at that path is an error rather than something to overwrite.
On shutdown (SIGINT/SIGTERM, handled directly — no init shim needed) the
collector tells connected consumers it is going away and unlinks the socket.

## Headless vs privileged

**Headless (the default, unprivileged).** No eBPF, no kernel probes, no
capabilities beyond the defaults. Sessions come from `/proc` scans and from the
agents' transcript files. The collector announces the degraded mode in its log:

```
no eBPF: showing process snapshots and agent-native sessions only
```

This mode serves the bridge fully; what it cannot report is anything only a
kernel probe sees (SSL payload capture, exec/file/network tracing).

Two mounts decide whether it sees anything worth serving:

- **Host PID namespace** (`--pid=host`, or compose `pid: host`). Without it the
  container's `/proc` contains only the collector itself, and the bridge serves
  an empty session list.
- **The host user's home directory**, plus `HOME` pointing at it. Transcript
  discovery reads `$HOME/.claude`, `$HOME/.codex`, `$HOME/.gemini` and friends,
  so mounting e.g. `/home/dev:/host-home:ro` with `-e HOME=/host-home` is what
  makes host agent sessions visible. (`SUDO_USER` is honoured ahead of `HOME`
  when set, resolved through `/etc/passwd`.)

**Privileged (eBPF capture).** On a Linux host, running the container
`--privileged` with `--pid=host` lets the collector extract its embedded eBPF
loaders and attach kernel probes; the log then reads `live eBPF process capture
enabled`. This is Linux-only and amd64-only — the loaders committed under
`agentsight-capture/vendor/bpf/` are x86-64 ELF binaries, and `libelf1`/`zlib1g`
are installed in the runtime stage for them. On a Docker Desktop (macOS or
Windows) host the container's "kernel" is the Linux VM's, so probes there
observe the VM, not the host.

Example, unprivileged:

```
docker run --rm --pid=host \
  -v aro-bridge:/run/aro \
  -v /home/dev:/host-home:ro -e HOME=/host-home \
  ghcr.io/<owner>/agent-sandbox/session-capture:main
```

and the privileged variant adds `--privileged`.

## Overriding the command

There is no `ENTRYPOINT`, so an override replaces the command line whole —
binary name included:

```
docker run --rm session-capture agentsight report list
docker run --rm session-capture agentsight top --bridge-socket /run/aro/bridge.sock --headless -i 5
```
