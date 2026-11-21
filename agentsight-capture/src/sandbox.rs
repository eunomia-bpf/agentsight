// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Best-effort runtime metadata, cached once per kernel cgroup ID.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SandboxIdentity {
    pub id: String,
    pub cgroup_id: u64,
    pub cgroup_path: Option<String>,
    pub pidns: u64,
    pub container_id: Option<String>,
    pub name: Option<String>,
    pub image: Option<String>,
    pub runtime: Option<String>,
}

#[derive(Default)]
pub struct SandboxResolver {
    cgroups: HashMap<u64, SandboxIdentity>,
}

impl SandboxResolver {
    pub fn enrich(&mut self, event: &mut Value) {
        let (Some(cgroup), Some(pidns), Some(pid)) = (
            event["cgroup_id"].as_u64().filter(|id| *id != 0),
            event["pidns"].as_u64().filter(|id| *id != 0),
            event["pid"].as_u64(),
        ) else {
            return;
        };
        let identity = self.resolve(cgroup, pidns, || resolve_cgroup(cgroup, pid));
        event["sandbox"] = serde_json::to_value(identity).unwrap_or(Value::Null);
    }

    fn resolve(
        &mut self,
        cgroup: u64,
        pidns: u64,
        lookup: impl FnOnce() -> SandboxIdentity,
    ) -> SandboxIdentity {
        let mut identity = self.cgroups.entry(cgroup).or_insert_with(lookup).clone();
        // A cgroup can contain multiple nested PID namespaces. Cache runtime
        // metadata by cgroup, but keep their lifetimes and commands separate.
        identity.id = format!("cgroup:{cgroup}:pidns:{pidns}");
        identity.cgroup_id = cgroup;
        identity.pidns = pidns;
        identity
    }
}

fn unified_path(contents: &str) -> Option<&str> {
    contents.lines().find_map(|line| line.strip_prefix("0::"))
}

fn container_ref(path: &str) -> Option<(&str, &str)> {
    for part in path.split('/').rev() {
        let part = part.strip_suffix(".scope").unwrap_or(part);
        let (runtime, id) = if let Some(id) = part.strip_prefix("docker-") {
            ("docker", id)
        } else if let Some(id) = part.strip_prefix("cri-containerd-") {
            ("containerd", id)
        } else if let Some(id) = part.strip_prefix("crio-") {
            ("cri-o", id)
        } else if path.contains("/docker/") {
            ("docker", part)
        } else if path.contains("/kubepods/") {
            ("containerd", part)
        } else {
            continue;
        };
        if id.len() == 64 && id.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Some((runtime, id));
        }
    }
    None
}

fn apply_runtime(identity: &mut SandboxIdentity, runtime: &str, value: &Value) {
    let text = |pointer| {
        value
            .pointer(pointer)
            .and_then(Value::as_str)
            .filter(|s| !s.is_empty())
            .map(str::to_owned)
    };
    if runtime == "docker" {
        identity.name = text("/Name").map(|name| name.trim_start_matches('/').to_string());
        identity.image = text("/Config/Image");
        identity.container_id = text("/Id").or(identity.container_id.take());
    } else {
        identity.name = text("/status/metadata/name");
        identity.image = text("/status/image/image").or_else(|| text("/status/imageRef"));
        identity.container_id = text("/status/id").or(identity.container_id.take());
    }
}

#[cfg(target_os = "linux")]
fn cgroup_inode(path: &Path) -> Option<u64> {
    use std::os::unix::fs::MetadataExt;
    std::fs::metadata(path).ok().map(|m| m.ino())
}
#[cfg(not(target_os = "linux"))]
fn cgroup_inode(_: &Path) -> Option<u64> {
    None
}

fn find_cgroup(root: &Path, id: u64) -> Option<std::path::PathBuf> {
    if cgroup_inode(root) == Some(id) {
        return Some(root.to_owned());
    }
    for entry in std::fs::read_dir(root).ok()?.flatten() {
        if entry.file_type().is_ok_and(|kind| kind.is_dir()) {
            if let Some(found) = find_cgroup(&entry.path(), id) {
                return Some(found);
            }
        }
    }
    None
}

fn resolve_cgroup(id: u64, pid: u64) -> SandboxIdentity {
    let root = Path::new("/sys/fs/cgroup");
    // Verify the inode: /proc can already refer to a reused PID or a process
    // that moved cgroups. Delayed exit/network events retain the kernel ID.
    let proc_path = std::fs::read_to_string(format!("/proc/{pid}/cgroup"))
        .ok()
        .and_then(|s| unified_path(&s).map(str::to_owned));
    let path = proc_path
        .filter(|p| cgroup_inode(&root.join(p.trim_start_matches('/'))) == Some(id))
        .or_else(|| {
            find_cgroup(root, id)
                .map(|p| format!("/{}", p.strip_prefix(root).unwrap_or(&p).display()))
        });
    let mut identity = SandboxIdentity {
        cgroup_id: id,
        cgroup_path: path.clone(),
        name: path.clone(),
        ..Default::default()
    };
    if let Some((runtime, container)) = path.as_deref().and_then(container_ref) {
        identity.runtime = Some(runtime.to_string());
        identity.container_id = Some(container.to_string());
        if let Some(value) = crate::binary_resolver::inspect_runtime_container(runtime, container) {
            apply_runtime(&mut identity, runtime, &value);
        }
        if identity.name.is_none() {
            identity.name = path;
        }
    }
    identity
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn cgroup_paths_and_runtime_metadata() {
        assert_eq!(
            unified_path("4:cpu:/old\n0::/system.slice/demo.scope\n"),
            Some("/system.slice/demo.scope")
        );
        assert_eq!(container_ref("/system.slice/ssh.service"), None);
        assert_eq!(container_ref(&format!("/tasks/{}", "a".repeat(64))), None);
        assert_eq!(
            container_ref(&format!("/docker/{}", "a".repeat(64))).map(|r| r.0),
            Some("docker")
        );
        assert_eq!(
            container_ref(&format!("/kubepods/pod123/{}", "a".repeat(64))).map(|r| r.0),
            Some("containerd")
        );
        for (prefix, runtime) in [
            ("docker-", "docker"),
            ("cri-containerd-", "containerd"),
            ("crio-", "cri-o"),
        ] {
            let path = format!("/kubepods.slice/{prefix}{}.scope", "a".repeat(64));
            assert_eq!(
                container_ref(&path),
                Some((runtime, "a".repeat(64).as_str()))
            );
        }
        let mut identity = SandboxIdentity::default();
        apply_runtime(
            &mut identity,
            "docker",
            &json!({"Id":"abc", "Name":"/worker", "Config":{"Image":"ubuntu:24.04"}}),
        );
        assert_eq!(identity.name.as_deref(), Some("worker"));
        assert_eq!(identity.image.as_deref(), Some("ubuntu:24.04"));
        apply_runtime(
            &mut identity,
            "containerd",
            &json!({"status":{"id":"def", "metadata":{"name":"task"}, "image":{"image":"python:3"}}}),
        );
        assert_eq!(identity.name.as_deref(), Some("task"));
        assert_eq!(identity.image.as_deref(), Some("python:3"));
    }

    #[test]
    fn caches_failures_and_separates_namespaces_in_one_cgroup() {
        let mut resolver = SandboxResolver::default();
        let first = resolver.resolve(42, 100, SandboxIdentity::default);
        let second = resolver.resolve(42, 200, || panic!("cgroup must only be resolved once"));
        assert_ne!(first.id, second.id);
        assert_eq!(second.pidns, 200);
        assert_eq!(second.cgroup_id, 42);
        assert!(second.container_id.is_none());
        let mut old = json!({"event":"EXEC", "pid":1});
        resolver.enrich(&mut old);
        assert!(old.get("sandbox").is_none());
    }
}
