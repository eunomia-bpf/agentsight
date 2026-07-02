// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Resolution of the ELF binary that sslsniff should attach its SSL uprobe to.
//!
//! Three entry points are used by the CLI handlers in `main.rs`:
//!   - [`resolve_binary_path`] turns a command name/path into the underlying ELF
//!     (PATH search, symlink canonicalization, shebang interpreter resolution).
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
pub(crate) fn resolve_binary_path(command: &str) -> Result<String, String> {
    // Limit shebang chasing so a pathological wrapper chain cannot loop forever.
    resolve_binary_path_inner(command, 0)
}

fn resolve_binary_path_inner(command: &str, depth: u8) -> Result<String, String> {
    if depth > 5 {
        return Err(format!(
            "too many nested shebang wrappers resolving '{}'",
            command
        ));
    }

    // 1. Locate the file: an explicit path is used as-is, otherwise search $PATH.
    let candidate = if command.contains('/') {
        std::path::PathBuf::from(command)
    } else {
        find_in_path(command).ok_or_else(|| format!("'{}' not found in $PATH", command))?
    };

    // 2. Follow symlinks to the real file (e.g. claude -> versions/2.1.150).
    let resolved = std::fs::canonicalize(&candidate)
        .map_err(|e| format!("cannot resolve '{}': {}", candidate.display(), e))?;

    // 3. Inspect the file header: ELF magic vs. shebang.
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

/// Minimal `which`: find an executable file named `cmd` in the `$PATH` dirs.
///
/// When invoked under `sudo`, the inherited `$PATH` is root's secure path, which
/// usually misses user-local installs like `~/.local/bin/claude`. To make
/// `sudo agentsight record -- claude` find the *invoking user's* tools, we search
/// that user's common bin dirs first (derived from `$SUDO_USER`).
fn find_in_path(cmd: &str) -> Option<std::path::PathBuf> {
    let mut dirs: Vec<std::path::PathBuf> = Vec::new();

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

    if let Some(path) = std::env::var_os("PATH") {
        dirs.extend(std::env::split_paths(&path));
    }

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
/// strings in the file. Dynamically-linked runtimes like CPython call into a
/// separate `libssl.so` (via `_ssl.so`) and do NOT contain these markers in the
/// executable, so they keep using sslsniff's system-libssl attachment with comm
/// filtering intact.
pub(crate) fn binary_embeds_ssl(path: &str) -> bool {
    use std::io::Read;
    const NEEDLES: &[&[u8]] = &[b"SSL_write", b"BoringSSLError", b"OPENSSL_internal"];
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
pub(crate) fn parse_container_ref(binary_path: &str) -> Option<&str> {
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

pub(crate) fn resolve_container_binary_arg(
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
pub(crate) fn resolve_container_binary_path(reference: &str) -> Result<String, String> {
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
    fn ignores_binary_without_static_ssl_markers() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("plain");
        std::fs::write(&path, b"no tls marker here").unwrap();

        assert!(!binary_embeds_ssl(path.to_str().unwrap()));
    }
}
