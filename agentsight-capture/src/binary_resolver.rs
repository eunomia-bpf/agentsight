// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Resolution of the ELF binary that sslsniff should attach its SSL uprobe to.
//!
//! Three entry points are used by the CLI handlers in `main.rs`:
//!   - [`resolve_binary_path`] turns a command name/path into the underlying ELF
//!     (PATH search, symlink canonicalization, shebang interpreter resolution).
//!   - [`resolve_binary_path_for_ssl`] finds the concrete static TLS target.
//!   - [`binary_embeds_ssl`] detects statically-linked TLS (Node.js/OpenClaw).
//!   - [`resolve_container_binary_arg`] maps a container reference such as
//!     `docker://<container>` or `k8s://<namespace>/<pod>/<container>` to an
//!     explicit host SSL attach target.

/// Resolve a command name/path to the real ELF binary that should be passed
/// to sslsniff as `--binary-path`.
///
/// Handles three cases automatically:
///   1. A command on `$PATH` (e.g. `claude`, `node`) -> located via PATH search.
///   2. A symlink (e.g. `~/.local/bin/claude` -> `.../versions/2.1.150`) -> followed.
///   3. A shebang wrapper script (`#!/usr/bin/env node`) -> the interpreter ELF.
///
/// Returns the canonical path of the underlying ELF executable, or an error
/// describing why discovery failed.
pub fn resolve_binary_path(command: &str) -> Result<String, String> {
    // Limit shebang chasing so a pathological wrapper chain cannot loop forever.
    resolve_binary_path_inner(command, 0)
}

/// Resolve a command to the concrete ELF path sslsniff should attach to, when
/// one is needed for statically-linked TLS.
///
/// Codex's npm launcher is a Node.js script, but the network client runs in the
/// platform-native `@openai/codex-linux-*` binary. Prefer that native binary
/// before following the launcher's shebang to `node`; otherwise `record -- codex`
/// attaches to the wrapper and misses Codex's TLS traffic.
pub fn resolve_binary_path_for_ssl(command: &str) -> Result<Option<String>, String> {
    let launcher = resolve_command_path(command)?;
    if is_openai_codex_native_binary(&launcher) {
        return Ok(Some(canonicalize_path(&launcher)));
    }
    if let Some(path) = codex_native_binary_from_launcher(&launcher) {
        return Ok(Some(path));
    }

    let resolved = resolve_binary_path(command)?;
    if binary_embeds_ssl(&resolved) {
        Ok(Some(resolved))
    } else {
        Ok(None)
    }
}

fn resolve_binary_path_inner(command: &str, depth: u8) -> Result<String, String> {
    if depth > 5 {
        return Err(format!(
            "too many nested shebang wrappers resolving '{}'",
            command
        ));
    }

    let resolved = resolve_command_path(command)?;

    // Inspect the file header: ELF magic vs. shebang.
    let mut header = [0u8; 256];
    let n = {
        use std::io::Read;
        let mut f = std::fs::File::open(&resolved)
            .map_err(|e| format!("cannot open '{}': {}", resolved.display(), e))?;
        f.read(&mut header)
            .map_err(|e| format!("cannot read '{}': {}", resolved.display(), e))?
    };
    let header = &header[..n];

    if header.starts_with(b"\x7fELF") {
        return Ok(resolved.to_string_lossy().into_owned());
    }

    if header.starts_with(b"#!") {
        // Parse the shebang line: `#!/usr/bin/env node` or `#!/usr/bin/python3`.
        let line_end = header
            .iter()
            .position(|&b| b == b'\n')
            .unwrap_or(header.len());
        let line = String::from_utf8_lossy(&header[2..line_end]);
        let mut parts = line.split_whitespace();
        let interp = parts
            .next()
            .ok_or_else(|| format!("'{}' has an empty shebang", resolved.display()))?;
        // `/usr/bin/env foo` -> resolve `foo` on PATH instead of `env` itself.
        let next = if interp.ends_with("/env") || interp == "env" {
            parts
                .next()
                .ok_or_else(|| format!("'{}' uses env with no interpreter", resolved.display()))?
        } else {
            interp
        };
        return resolve_binary_path_inner(next, depth + 1);
    }

    Err(format!(
        "'{}' is neither an ELF binary nor a shebang script; specify --binary-path explicitly",
        resolved.display()
    ))
}

/// Locate a command and follow symlinks without chasing shebang interpreters.
fn resolve_command_path(command: &str) -> Result<std::path::PathBuf, String> {
    let candidate = if command.contains('/') {
        std::path::PathBuf::from(command)
    } else {
        find_in_path(command).ok_or_else(|| format!("'{}' not found in $PATH", command))?
    };

    std::fs::canonicalize(&candidate)
        .map_err(|e| format!("cannot resolve '{}': {}", candidate.display(), e))
}

/// Minimal `which`: find an executable file named `cmd` in the `$PATH` dirs.
///
/// When invoked under `sudo`, the inherited `$PATH` is often root's secure path,
/// which misses user-local installs like `~/.local/bin/claude`. Honor an
/// explicit `$PATH` first, then fall back to the invoking user's common bin dirs
/// derived from `$SUDO_USER`.
fn find_in_path(cmd: &str) -> Option<std::path::PathBuf> {
    let mut dirs: Vec<std::path::PathBuf> = Vec::new();

    if let Some(path) = std::env::var_os("PATH") {
        dirs.extend(std::env::split_paths(&path));
    }

    if let Some(user) = std::env::var_os("SUDO_USER")
        && let Some(home) = sudo_user_home(&user)
    {
        dirs.push(home.join(".local/bin"));
        dirs.push(home.join("bin"));
        // NVM keeps node under ~/.nvm/versions/node/<ver>/bin; pick the newest.
        if let Some(nvm_bin) = newest_nvm_bin(&home) {
            dirs.push(nvm_bin);
        }
    }

    find_executable_in_dirs(cmd, dirs)
}

fn find_executable_in_dirs(
    cmd: &str,
    dirs: impl IntoIterator<Item = std::path::PathBuf>,
) -> Option<std::path::PathBuf> {
    for dir in dirs {
        let full = dir.join(cmd);
        if let Ok(meta) = std::fs::metadata(&full)
            && meta.is_file()
        {
            return Some(full);
        }
    }
    None
}

/// Resolve the home directory of the `$SUDO_USER` by reading `/etc/passwd`.
fn sudo_user_home(user: &std::ffi::OsStr) -> Option<std::path::PathBuf> {
    let user = user.to_str()?;
    let passwd = std::fs::read_to_string("/etc/passwd").ok()?;
    for line in passwd.lines() {
        let mut fields = line.split(':');
        if fields.next() == Some(user) {
            // username:x:uid:gid:gecos:home:shell -> home is field index 5.
            return fields.nth(4).map(std::path::PathBuf::from);
        }
    }
    None
}

/// Find the newest NVM-installed node bin dir under a user's home, if any.
fn newest_nvm_bin(home: &std::path::Path) -> Option<std::path::PathBuf> {
    let versions = home.join(".nvm/versions/node");
    let mut entries: Vec<_> = std::fs::read_dir(&versions)
        .ok()?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .collect();
    entries.sort();
    entries.last().map(|p| p.join("bin"))
}

/// Heuristic: does this ELF statically embed its own SSL implementation?
///
/// Node.js bundles OpenSSL directly into the `node` binary, so there is no
/// system `libssl.so` for sslsniff to hook — it must attach to the binary
/// itself. We detect this by scanning for static OpenSSL/BoringSSL marker
/// strings in the file. Grok's native binary is also selected by its CLI
/// marker; sslsniff performs the stricter rustls signature check. Dynamically-
/// linked runtimes like CPython call into a separate `libssl.so` (via `_ssl.so`)
/// and do NOT contain these markers in the executable, so they keep using
/// sslsniff's system-libssl attachment with comm filtering intact.
pub fn binary_embeds_ssl(path: &str) -> bool {
    use std::io::Read;
    const NEEDLES: &[&[u8]] = &[
        b"SSL_write",
        b"BoringSSLError",
        b"OPENSSL_internal",
        b"grok-cli",
    ];
    let mut f = match std::fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return false,
    };
    let mut buf = vec![0u8; 1 << 20]; // 1 MiB chunks
    // Carry the tail of each chunk so a match spanning a boundary isn't missed.
    let mut carry: Vec<u8> = Vec::new();
    let keep = NEEDLES
        .iter()
        .map(|needle| needle.len())
        .max()
        .unwrap_or(1)
        .saturating_sub(1);
    loop {
        let n = match f.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => n,
            Err(_) => return false,
        };
        carry.extend_from_slice(&buf[..n]);
        if NEEDLES
            .iter()
            .any(|needle| carry.windows(needle.len()).any(|w| w == *needle))
        {
            return true;
        }
        if carry.len() > keep {
            carry.drain(..carry.len() - keep);
        }
    }
    false
}

fn codex_native_binary_from_launcher(launcher: &std::path::Path) -> Option<String> {
    let package_root = openai_codex_package_root(launcher)?;

    let nested_scope = package_root.join("node_modules").join("@openai");
    if let Some(path) = codex_native_binary_in_scope(&nested_scope) {
        return Some(path);
    }
    if let Some(scope) = package_root.parent() {
        if let Some(path) = codex_native_binary_in_scope(scope) {
            return Some(path);
        }
    }

    None
}

fn codex_native_binary_in_scope(openai_scope: &std::path::Path) -> Option<String> {
    const CANDIDATES: &[(&str, &str)] = &[
        ("codex-linux-x64", "x86_64-unknown-linux-musl"),
        ("codex-linux-arm64", "aarch64-unknown-linux-musl"),
    ];

    for (package, target) in CANDIDATES {
        let path = openai_scope
            .join(package)
            .join("vendor")
            .join(target)
            .join("bin")
            .join("codex");
        if is_elf_file(&path) {
            return Some(canonicalize_path(&path));
        }
    }
    None
}

fn is_openai_codex_native_binary(path: &std::path::Path) -> bool {
    if !is_elf_file(path) || !file_name_eq(path, "codex") {
        return false;
    }

    let Some(bin_dir) = path.parent().filter(|p| file_name_eq(p, "bin")) else {
        return false;
    };
    let Some(target_dir) = bin_dir.parent().filter(|p| {
        file_name_eq(p, "x86_64-unknown-linux-musl")
            || file_name_eq(p, "aarch64-unknown-linux-musl")
    }) else {
        return false;
    };
    let Some(vendor_dir) = target_dir.parent().filter(|p| file_name_eq(p, "vendor")) else {
        return false;
    };
    let Some(package_dir) = vendor_dir
        .parent()
        .filter(|p| file_name_eq(p, "codex-linux-x64") || file_name_eq(p, "codex-linux-arm64"))
    else {
        return false;
    };
    package_dir
        .parent()
        .is_some_and(|parent| file_name_eq(parent, "@openai"))
}

fn openai_codex_package_root(path: &std::path::Path) -> Option<std::path::PathBuf> {
    for ancestor in path.ancestors() {
        if file_name_eq(ancestor, "codex")
            && ancestor
                .parent()
                .is_some_and(|parent| file_name_eq(parent, "@openai"))
            && ancestor
                .parent()
                .and_then(|parent| parent.parent())
                .is_some_and(|parent| file_name_eq(parent, "node_modules"))
        {
            return Some(ancestor.to_path_buf());
        }
    }
    None
}

fn file_name_eq(path: &std::path::Path, expected: &str) -> bool {
    path.file_name().and_then(|name| name.to_str()) == Some(expected)
}

fn is_elf_file(path: &std::path::Path) -> bool {
    use std::io::Read;
    let mut header = [0u8; 4];
    let mut f = match std::fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return false,
    };
    f.read_exact(&mut header).is_ok() && header == *b"\x7fELF"
}

fn canonicalize_path(path: &std::path::Path) -> String {
    std::fs::canonicalize(path)
        .map(|p| p.to_string_lossy().into_owned())
        .unwrap_or_else(|_| path.to_string_lossy().into_owned())
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct KubernetesRef<'a> {
    namespace: &'a str,
    pod: &'a str,
    container: Option<&'a str>,
}

impl KubernetesRef<'_> {
    fn label(&self) -> String {
        match self.container {
            Some(container) => format!("k8s://{}/{}/{}", self.namespace, self.pod, container),
            None => format!("k8s://{}/{}", self.namespace, self.pod),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct RuntimeContainerRef {
    runtime: String,
    id: String,
}

/// Strip a `docker://<ref>` or `docker:<ref>` scheme from a `--binary-path`
/// value, returning the container reference (name or id). Returns `None` for
/// ordinary filesystem paths, which are passed through to sslsniff unchanged.
pub fn parse_container_ref(binary_path: &str) -> Option<&str> {
    binary_path
        .strip_prefix("docker://")
        .or_else(|| binary_path.strip_prefix("docker:"))
        .filter(|r| !r.is_empty() && !r.contains('/'))
}

fn has_docker_scheme(binary_path: &str) -> bool {
    binary_path.starts_with("docker://") || binary_path.starts_with("docker:")
}

/// Parse a Kubernetes pod reference from `--binary-path`.
///
/// Supported forms:
///   - `k8s://pod` (default namespace)
///   - `k8s://namespace/pod`
///   - `k8s://namespace/pod/container`
///   - the same forms with `k8s:` or `kubernetes://` prefixes
fn parse_kubernetes_ref(binary_path: &str) -> Option<KubernetesRef<'_>> {
    let reference = binary_path
        .strip_prefix("k8s://")
        .or_else(|| binary_path.strip_prefix("k8s:"))
        .or_else(|| binary_path.strip_prefix("kubernetes://"))
        .or_else(|| binary_path.strip_prefix("kubernetes:"))?;

    let parts = reference.split('/').collect::<Vec<_>>();
    if parts.is_empty() || parts.iter().any(|part| part.is_empty()) {
        return None;
    }

    match parts.as_slice() {
        [pod] => Some(KubernetesRef {
            namespace: "default",
            pod,
            container: None,
        }),
        [namespace, pod] => Some(KubernetesRef {
            namespace,
            pod,
            container: None,
        }),
        [namespace, pod, container] => Some(KubernetesRef {
            namespace,
            pod,
            container: Some(container),
        }),
        _ => None,
    }
}

fn has_kubernetes_scheme(binary_path: &str) -> bool {
    binary_path.starts_with("k8s://")
        || binary_path.starts_with("k8s:")
        || binary_path.starts_with("kubernetes://")
        || binary_path.starts_with("kubernetes:")
}

pub fn resolve_container_binary_arg(
    binary_path: Option<&str>,
) -> Result<Option<(String, String)>, String> {
    let Some(binary_path) = binary_path else {
        return Ok(None);
    };

    if let Some(reference) = parse_container_ref(binary_path) {
        return resolve_container_binary_path(reference)
            .map(|path| Some((reference.to_string(), path)));
    }
    if has_docker_scheme(binary_path) {
        return Err(format!(
            "invalid Docker container reference '{}'; expected docker://<name|id>",
            binary_path
        ));
    }

    if let Some(reference) = parse_kubernetes_ref(binary_path) {
        let label = reference.label();
        return resolve_kubernetes_binary_path(&reference).map(|path| Some((label, path)));
    }
    if has_kubernetes_scheme(binary_path) {
        return Err(format!(
            "invalid Kubernetes pod reference '{}'; expected k8s://pod, k8s://namespace/pod, or k8s://namespace/pod/container",
            binary_path
        ));
    }

    Ok(None)
}

/// Resolve a Docker container reference to the explicit host path that
/// sslsniff should attach its SSL uprobe to.
///
/// This handles both statically-linked TLS runtimes (`/proc/<pid>/exe`, common
/// for Node.js/OpenClaw) and dynamically-linked OpenSSL (`/proc/<pid>/root/...`
/// for a loaded `libssl.so`). The host PID comes from `docker inspect`, so this
/// requires the Docker CLI and permission to read the target's `/proc` entries.
///
/// `docker inspect .State.Pid` returns the container's *init* process, which is
/// often a wrapper such as `tini` (OpenClaw's image uses `tini -s -- node …`).
/// That wrapper does not embed SSL, so we walk its descendant process tree and
/// require an actual SSL target.
pub fn resolve_container_binary_path(reference: &str) -> Result<String, String> {
    let init_pid = resolve_docker_container_pid(reference)?;

    find_ssl_target_in_tree(init_pid).ok_or_else(|| {
        format!(
            "container '{}' is running at host PID {}, but no SSL attach target was found in its process tree",
            reference, init_pid
        )
    })
}

fn resolve_docker_container_pid(reference: &str) -> Result<u32, String> {
    let output = std::process::Command::new("docker")
        .args(["inspect", "--format", "{{.State.Pid}}", reference])
        .output()
        .map_err(|e| format!(
            "failed to run `docker inspect` for container '{}': {} (is the Docker CLI installed and on $PATH?)",
            reference, e
        ))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "`docker inspect {}` failed: {}",
            reference,
            stderr.trim()
        ));
    }

    let init_pid: u32 = String::from_utf8_lossy(&output.stdout)
        .trim()
        .parse()
        .map_err(|_| format!("could not determine host PID for container '{}'", reference))?;

    if init_pid == 0 {
        return Err(format!(
            "container '{}' is not running (host PID 0)",
            reference
        ));
    }

    Ok(init_pid)
}

fn resolve_kubernetes_binary_path(reference: &KubernetesRef<'_>) -> Result<String, String> {
    let pod = kubectl_get_pod(reference)?;
    let container_id = select_kubernetes_container_id(&pod, reference)?;
    let runtime = parse_runtime_container_id(&container_id)?;
    let init_pid = resolve_runtime_container_pid(&runtime)?;

    find_ssl_target_in_tree(init_pid).ok_or_else(|| {
        let node = pod
            .pointer("/spec/nodeName")
            .and_then(serde_json::Value::as_str)
            .unwrap_or("unknown");
        format!(
            "Kubernetes pod '{}/{}' container target '{}' is running at host PID {}, but no SSL attach target was found in its process tree. AgentSight must run on the node that hosts the pod (node: {}).",
            reference.namespace,
            reference.pod,
            runtime.id,
            init_pid,
            node
        )
    })
}

fn kubectl_get_pod(reference: &KubernetesRef<'_>) -> Result<serde_json::Value, String> {
    let output = kubectl_command()
        .args([
            "get",
            "pod",
            reference.pod,
            "-n",
            reference.namespace,
            "-o",
            "json",
        ])
        .output()
        .map_err(|e| format!(
            "failed to run `kubectl get pod {}` in namespace '{}': {} (is kubectl installed and configured?)",
            reference.pod, reference.namespace, e
        ))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "`kubectl get pod {} -n {}` failed: {}",
            reference.pod,
            reference.namespace,
            stderr.trim()
        ));
    }

    serde_json::from_slice(&output.stdout).map_err(|e| {
        format!(
            "`kubectl get pod {} -n {} -o json` returned invalid JSON: {}",
            reference.pod, reference.namespace, e
        )
    })
}

fn kubectl_command() -> std::process::Command {
    let mut command = std::process::Command::new("kubectl");
    if std::env::var_os("KUBECONFIG").is_none()
        && let Some(user) = std::env::var_os("SUDO_USER")
        && let Some(home) = sudo_user_home(&user)
    {
        let kubeconfig = home.join(".kube/config");
        if kubeconfig.is_file() {
            command.env("KUBECONFIG", kubeconfig);
        }
    }
    command
}

fn select_kubernetes_container_id(
    pod: &serde_json::Value,
    reference: &KubernetesRef<'_>,
) -> Result<String, String> {
    let statuses = pod
        .pointer("/status/containerStatuses")
        .and_then(serde_json::Value::as_array)
        .ok_or_else(|| {
            format!(
                "Kubernetes pod '{}/{}' has no status.containerStatuses yet",
                reference.namespace, reference.pod
            )
        })?;

    if let Some(container) = reference.container {
        let status = statuses
            .iter()
            .find(|status| {
                status.get("name").and_then(serde_json::Value::as_str) == Some(container)
            })
            .ok_or_else(|| {
                format!(
                    "Kubernetes pod '{}/{}' has no container named '{}'",
                    reference.namespace, reference.pod, container
                )
            })?;
        return container_id_from_status(status).ok_or_else(|| {
            format!(
                "Kubernetes pod '{}/{}' container '{}' has no containerID yet (is it running?)",
                reference.namespace, reference.pod, container
            )
        });
    }

    let containers = statuses
        .iter()
        .filter_map(|status| {
            let name = status.get("name").and_then(serde_json::Value::as_str)?;
            let id = container_id_from_status(status)?;
            Some((name, id))
        })
        .collect::<Vec<_>>();

    match containers.as_slice() {
        [(_, id)] => Ok(id.clone()),
        [] => Err(format!(
            "Kubernetes pod '{}/{}' has no running containers with a containerID",
            reference.namespace, reference.pod
        )),
        _ => {
            let names = containers
                .iter()
                .map(|(name, _)| *name)
                .collect::<Vec<_>>()
                .join(", ");
            Err(format!(
                "Kubernetes pod '{}/{}' has multiple containers ({}); specify one as k8s://{}/{}/<container>",
                reference.namespace, reference.pod, names, reference.namespace, reference.pod
            ))
        }
    }
}

fn container_id_from_status(status: &serde_json::Value) -> Option<String> {
    status.pointer("/state/running")?;
    let id = status.get("containerID")?.as_str()?.trim();
    (!id.is_empty()).then(|| id.to_string())
}

fn parse_runtime_container_id(container_id: &str) -> Result<RuntimeContainerRef, String> {
    let (runtime, id) = container_id.split_once("://").ok_or_else(|| {
        format!(
            "Kubernetes containerID '{}' is missing a runtime scheme",
            container_id
        )
    })?;
    let id = id.trim();
    if runtime.trim().is_empty() || id.is_empty() {
        return Err(format!(
            "Kubernetes containerID '{}' is incomplete",
            container_id
        ));
    }
    Ok(RuntimeContainerRef {
        runtime: runtime.to_string(),
        id: id.to_string(),
    })
}

fn resolve_runtime_container_pid(container: &RuntimeContainerRef) -> Result<u32, String> {
    match container.runtime.as_str() {
        "docker" => resolve_docker_container_pid(&container.id),
        "containerd" | "cri-o" | "crio" => resolve_cri_container_pid(&container.id),
        other => resolve_cri_container_pid(&container.id).map_err(|e| {
            format!(
                "unsupported Kubernetes container runtime '{}' for container '{}': {}",
                other, container.id, e
            )
        }),
    }
}

fn resolve_cri_container_pid(container_id: &str) -> Result<u32, String> {
    let output = std::process::Command::new("crictl")
        .args(["inspect", "--output", "json", container_id])
        .output()
        .map_err(|e| format!(
            "failed to run `crictl inspect` for container '{}': {} (is crictl installed and configured for this node's CRI runtime?)",
            container_id, e
        ))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "`crictl inspect {}` failed: {}",
            container_id,
            stderr.trim()
        ));
    }

    let value: serde_json::Value = serde_json::from_slice(&output.stdout).map_err(|e| {
        format!(
            "`crictl inspect --output json {}` returned invalid JSON: {}",
            container_id, e
        )
    })?;

    parse_crictl_pid(&value).ok_or_else(|| {
        format!(
            "could not determine host PID for CRI container '{}'",
            container_id
        )
    })
}

fn parse_crictl_pid(value: &serde_json::Value) -> Option<u32> {
    ["/info/pid", "/status/pid"]
        .into_iter()
        .filter_map(|path| value.pointer(path))
        .find_map(value_as_u32)
        .filter(|pid| *pid != 0)
}

fn value_as_u32(value: &serde_json::Value) -> Option<u32> {
    if let Some(pid) = value.as_u64() {
        return u32::try_from(pid).ok();
    }
    value.as_str()?.parse().ok()
}

/// Breadth-first search the descendant process tree rooted at `root_pid` for a
/// concrete SSL attach path.
///
/// Children are read from `/proc/<pid>/task/<pid>/children`, which lists the
/// immediate child PIDs of a process. Requires permission to read those entries
/// (root in practice for containerized processes).
fn find_ssl_target_in_tree(root_pid: u32) -> Option<String> {
    let mut queue = std::collections::VecDeque::from([root_pid]);
    let mut seen = std::collections::HashSet::new();
    while let Some(pid) = queue.pop_front() {
        if !seen.insert(pid) {
            continue;
        }
        let exe = format!("/proc/{}/exe", pid);
        if binary_embeds_ssl(&exe) {
            return Some(canonicalize_attach_path(&exe));
        }
        if let Some(path) = find_loaded_ssl_library(pid) {
            return Some(path);
        }
        let children_path = format!("/proc/{}/task/{}/children", pid, pid);
        if let Ok(children) = std::fs::read_to_string(&children_path) {
            for child in children
                .split_whitespace()
                .filter_map(|s| s.parse::<u32>().ok())
            {
                queue.push_back(child);
            }
        }
    }
    None
}

fn find_loaded_ssl_library(pid: u32) -> Option<String> {
    let maps = std::fs::read_to_string(format!("/proc/{pid}/maps")).ok()?;
    for line in maps.lines() {
        let path = line.split_whitespace().last()?;
        if !path.starts_with('/') || !path.contains("libssl.so") {
            continue;
        }
        let host_path = format!("/proc/{pid}/root{path}");
        if std::fs::metadata(&host_path).is_ok() {
            return Some(canonicalize_attach_path(&host_path));
        }
    }
    None
}

fn canonicalize_attach_path(path: &str) -> String {
    std::fs::canonicalize(path)
        .map(|p| p.to_string_lossy().into_owned())
        .unwrap_or_else(|_| path.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parses_docker_double_slash_scheme() {
        assert_eq!(parse_container_ref("docker://openclaw"), Some("openclaw"));
        assert_eq!(
            parse_container_ref("docker://my-agent-1"),
            Some("my-agent-1")
        );
    }

    #[test]
    fn parses_docker_colon_scheme() {
        assert_eq!(parse_container_ref("docker:openclaw"), Some("openclaw"));
        // A 64-char container id is a valid reference too.
        assert_eq!(
            parse_container_ref("docker:abc123def456"),
            Some("abc123def456")
        );
    }

    #[test]
    fn ignores_plain_filesystem_paths() {
        assert_eq!(parse_container_ref("/proc/1234/exe"), None);
        assert_eq!(parse_container_ref("/usr/bin/node"), None);
        assert_eq!(
            parse_container_ref("~/.nvm/versions/node/v20.0.0/bin/node"),
            None
        );
    }

    #[test]
    fn rejects_empty_container_reference() {
        assert_eq!(parse_container_ref("docker://"), None);
        assert_eq!(parse_container_ref("docker:"), None);
    }

    #[test]
    fn rejects_slash_separated_docker_reference() {
        assert_eq!(parse_container_ref("docker://foo/bar"), None);
        assert_eq!(parse_container_ref("docker:foo/bar"), None);
    }

    #[test]
    fn parses_kubernetes_pod_reference_with_default_namespace() {
        assert_eq!(
            parse_kubernetes_ref("k8s://openclaw"),
            Some(KubernetesRef {
                namespace: "default",
                pod: "openclaw",
                container: None,
            })
        );
    }

    #[test]
    fn parses_kubernetes_namespaced_pod_reference() {
        assert_eq!(
            parse_kubernetes_ref("k8s://agents/openclaw"),
            Some(KubernetesRef {
                namespace: "agents",
                pod: "openclaw",
                container: None,
            })
        );
    }

    #[test]
    fn parses_kubernetes_container_reference() {
        let reference = parse_kubernetes_ref("kubernetes://agents/openclaw/gateway");
        assert_eq!(
            reference,
            Some(KubernetesRef {
                namespace: "agents",
                pod: "openclaw",
                container: Some("gateway"),
            })
        );
        assert_eq!(
            reference.as_ref().map(KubernetesRef::label),
            Some("k8s://agents/openclaw/gateway".to_string())
        );
    }

    #[test]
    fn rejects_invalid_kubernetes_references() {
        assert_eq!(parse_kubernetes_ref("k8s://"), None);
        assert_eq!(parse_kubernetes_ref("k8s://agents/"), None);
        assert_eq!(
            parse_kubernetes_ref("k8s://agents/openclaw/gateway/extra"),
            None
        );
        assert_eq!(parse_kubernetes_ref("/usr/bin/node"), None);
    }

    #[test]
    fn invalid_container_scheme_errors_before_running_external_tools() {
        assert!(
            resolve_container_binary_arg(Some("docker://"))
                .unwrap_err()
                .contains("invalid Docker container reference")
        );
        assert!(
            resolve_container_binary_arg(Some("k8s://agents/openclaw/gateway/extra"))
                .unwrap_err()
                .contains("invalid Kubernetes pod reference")
        );
    }

    #[test]
    fn selects_single_kubernetes_container_id() {
        let pod = json!({
            "status": {
                "containerStatuses": [
                    {
                        "name": "gateway",
                        "state": {"running": {"startedAt": "2026-07-01T00:00:00Z"}},
                        "containerID": "containerd://abc123"
                    }
                ]
            }
        });
        let reference = KubernetesRef {
            namespace: "agents",
            pod: "openclaw",
            container: None,
        };

        assert_eq!(
            select_kubernetes_container_id(&pod, &reference).unwrap(),
            "containerd://abc123"
        );
    }

    #[test]
    fn selects_explicit_kubernetes_container_id() {
        let pod = json!({
            "status": {
                "containerStatuses": [
                    {
                        "name": "sidecar",
                        "state": {"running": {"startedAt": "2026-07-01T00:00:00Z"}},
                        "containerID": "containerd://sidecar123"
                    },
                    {
                        "name": "gateway",
                        "state": {"running": {"startedAt": "2026-07-01T00:00:00Z"}},
                        "containerID": "containerd://gateway123"
                    }
                ]
            }
        });
        let reference = KubernetesRef {
            namespace: "agents",
            pod: "openclaw",
            container: Some("gateway"),
        };

        assert_eq!(
            select_kubernetes_container_id(&pod, &reference).unwrap(),
            "containerd://gateway123"
        );
    }

    #[test]
    fn requires_container_name_for_multi_container_pod() {
        let pod = json!({
            "status": {
                "containerStatuses": [
                    {
                        "name": "sidecar",
                        "state": {"running": {"startedAt": "2026-07-01T00:00:00Z"}},
                        "containerID": "containerd://sidecar123"
                    },
                    {
                        "name": "gateway",
                        "state": {"running": {"startedAt": "2026-07-01T00:00:00Z"}},
                        "containerID": "containerd://gateway123"
                    }
                ]
            }
        });
        let reference = KubernetesRef {
            namespace: "agents",
            pod: "openclaw",
            container: None,
        };

        let err = select_kubernetes_container_id(&pod, &reference).unwrap_err();
        assert!(err.contains("multiple containers"));
        assert!(err.contains("k8s://agents/openclaw/<container>"));
    }

    #[test]
    fn ignores_non_running_kubernetes_container_id() {
        let pod = json!({
            "status": {
                "containerStatuses": [
                    {
                        "name": "gateway",
                        "state": {"terminated": {"exitCode": 0}},
                        "containerID": "containerd://old123"
                    }
                ]
            }
        });
        let reference = KubernetesRef {
            namespace: "agents",
            pod: "openclaw",
            container: None,
        };

        let err = select_kubernetes_container_id(&pod, &reference).unwrap_err();
        assert!(err.contains("no running containers"));
    }

    #[test]
    fn parses_kubernetes_runtime_container_id() {
        assert_eq!(
            parse_runtime_container_id("containerd://abc123").unwrap(),
            RuntimeContainerRef {
                runtime: "containerd".to_string(),
                id: "abc123".to_string(),
            }
        );
        assert_eq!(
            parse_runtime_container_id("docker://def456").unwrap(),
            RuntimeContainerRef {
                runtime: "docker".to_string(),
                id: "def456".to_string(),
            }
        );
        assert!(parse_runtime_container_id("abc123").is_err());
    }

    #[test]
    fn parses_crictl_pid_shapes() {
        assert_eq!(
            parse_crictl_pid(&json!({"info": {"pid": 1234}})),
            Some(1234)
        );
        assert_eq!(
            parse_crictl_pid(&json!({"status": {"pid": "5678"}})),
            Some(5678)
        );
        assert_eq!(parse_crictl_pid(&json!({"info": {"pid": 0}})), None);
    }

    #[test]
    fn canonicalize_attach_path_resolves_proc_root_when_available() {
        assert_eq!(
            canonicalize_attach_path("/proc/self/root/etc/hosts"),
            "/etc/hosts"
        );

        let dead_proc_path = "/proc/999999999/root/usr/lib/libssl.so";
        assert_eq!(canonicalize_attach_path(dead_proc_path), dead_proc_path);
    }

    #[test]
    fn detects_boringssl_marker_in_static_binary() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("claude-like");
        std::fs::write(&path, b"prefix BoringSSLError suffix").unwrap();

        assert!(binary_embeds_ssl(path.to_str().unwrap()));
    }

    #[test]
    fn detects_grok_static_binary_marker() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("grok-like");
        std::fs::write(&path, b"prefix grok-cli suffix").unwrap();

        assert!(binary_embeds_ssl(path.to_str().unwrap()));
    }

    #[test]
    fn resolves_codex_npm_launcher_to_native_ssl_binary() {
        let dir = tempfile::tempdir().unwrap();
        let package_root = dir.path().join("node_modules/@openai/codex");
        let launcher = package_root.join("bin/codex.js");
        let native = package_root.join(
            "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex",
        );
        std::fs::create_dir_all(launcher.parent().unwrap()).unwrap();
        std::fs::create_dir_all(native.parent().unwrap()).unwrap();
        std::fs::write(&launcher, b"#!/usr/bin/env node\n").unwrap();
        std::fs::write(&native, b"\x7fELFnative codex binary").unwrap();

        let resolved = resolve_binary_path_for_ssl(launcher.to_str().unwrap()).unwrap();
        let expected = native
            .canonicalize()
            .unwrap()
            .to_string_lossy()
            .into_owned();

        assert_eq!(resolved.as_deref(), Some(expected.as_str()));
    }

    #[test]
    fn resolves_codex_npm_launcher_to_sibling_native_package() {
        let dir = tempfile::tempdir().unwrap();
        let package_root = dir.path().join("node_modules/@openai/codex");
        let launcher = package_root.join("bin/codex.js");
        let native = dir.path().join(
            "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex",
        );
        std::fs::create_dir_all(launcher.parent().unwrap()).unwrap();
        std::fs::create_dir_all(native.parent().unwrap()).unwrap();
        std::fs::write(&launcher, b"#!/usr/bin/env node\n").unwrap();
        std::fs::write(&native, b"\x7fELFnative codex binary").unwrap();

        let resolved = resolve_binary_path_for_ssl(launcher.to_str().unwrap()).unwrap();
        let expected = native
            .canonicalize()
            .unwrap()
            .to_string_lossy()
            .into_owned();

        assert_eq!(resolved.as_deref(), Some(expected.as_str()));
    }

    #[test]
    fn resolves_codex_native_package_binary_for_ssl() {
        let dir = tempfile::tempdir().unwrap();
        let native = dir.path().join(
            "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex",
        );
        std::fs::create_dir_all(native.parent().unwrap()).unwrap();
        std::fs::write(&native, b"\x7fELFnative codex binary").unwrap();

        let resolved = resolve_binary_path_for_ssl(native.to_str().unwrap()).unwrap();
        let expected = native
            .canonicalize()
            .unwrap()
            .to_string_lossy()
            .into_owned();

        assert_eq!(resolved.as_deref(), Some(expected.as_str()));
    }

    #[test]
    fn ignores_binary_without_static_ssl_markers() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("plain");
        std::fs::write(&path, b"no tls marker here").unwrap();

        assert!(!binary_embeds_ssl(path.to_str().unwrap()));
    }

    #[test]
    fn path_search_prefers_earlier_dirs() {
        let first = tempfile::tempdir().unwrap();
        let second = tempfile::tempdir().unwrap();
        let first_cmd = first.path().join("agent");
        let second_cmd = second.path().join("agent");
        std::fs::write(&first_cmd, b"first").unwrap();
        std::fs::write(&second_cmd, b"second").unwrap();

        let found = find_executable_in_dirs(
            "agent",
            [first.path().to_path_buf(), second.path().to_path_buf()],
        )
        .unwrap();

        assert_eq!(found, first_cmd);
    }
}
