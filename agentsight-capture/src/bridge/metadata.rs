// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Metadata derivation applied before anything leaves the process.
//!
//! Every helper here turns a content-bearing string (a path, a URL, an argv)
//! into a coarse class or a digest. Raw values never reach a bridge row outside
//! the optional `content` structs, which only research/incident disclosure
//! populates.

use sha2::{Digest, Sha256};

/// Version tag mixed into command fingerprints so a rule change is visible.
pub const REDACTION_VERSION: &str = "as-redact/v1";

/// Coarse path buckets. The same buckets are used for `cwd_class` and
/// `path_class`.
pub const CLASS_REPO: &str = "repo";
pub const CLASS_HOME: &str = "home";
pub const CLASS_TMP: &str = "tmp";
pub const CLASS_DEPENDENCY_CACHE: &str = "dependency_cache";
pub const CLASS_SYSTEM: &str = "system";
pub const CLASS_OTHER: &str = "other";

const DEPENDENCY_MARKERS: [&str; 12] = [
    "/node_modules/",
    "/.cargo/",
    "/.rustup/",
    "/.npm/",
    "/.pnpm/",
    "/site-packages/",
    "/.venv/",
    "/go/pkg/mod/",
    "/.m2/",
    "/.gradle/",
    "/.cache/",
    "/vendor/",
];

const SYSTEM_PREFIXES: [&str; 12] = [
    "/usr/",
    "/bin/",
    "/sbin/",
    "/lib/",
    "/lib64/",
    "/etc/",
    "/proc/",
    "/sys/",
    "/dev/",
    "/opt/",
    "/System/",
    "/Library/",
];

const HOME_PREFIXES: [&str; 3] = ["/home/", "/Users/", "/root"];

const TMP_PREFIXES: [&str; 5] = [
    "/tmp/",
    "/var/tmp/",
    "/private/tmp/",
    "/private/var/folders/",
    "/var/folders/",
];

const PACKAGE_REGISTRY_HOSTS: [&str; 9] = [
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "crates.io",
    "static.crates.io",
    "index.crates.io",
    "rubygems.org",
    "proxy.golang.org",
    "repo.maven.apache.org",
];

const VCS_HOSTS: [&str; 6] = [
    "github.com",
    "codeload.github.com",
    "raw.githubusercontent.com",
    "gitlab.com",
    "bitbucket.org",
    "git.sr.ht",
];

const MULTI_LABEL_SUFFIXES: [&str; 8] = [
    "co.uk", "org.uk", "ac.uk", "com.au", "co.jp", "com.br", "com.cn", "co.in",
];

/// Lowercase hex SHA-256 of an arbitrary string.
pub fn digest_hex(value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    format!("{:x}", hasher.finalize())
}

/// Bucket a filesystem path without disclosing it.
///
/// The buckets are deliberately coarse and evaluated in priority order:
/// temporary storage, dependency caches, system trees, then home. A path under
/// home that is not a dotted configuration directory is reported as `repo`,
/// which is a heuristic: nothing here stats the filesystem.
pub fn path_class(path: &str) -> Option<String> {
    let path = path.trim();
    if path.is_empty() {
        return None;
    }
    let normalized = if path.ends_with('/') {
        path.to_string()
    } else {
        format!("{path}/")
    };

    if TMP_PREFIXES
        .iter()
        .any(|prefix| normalized.starts_with(prefix))
    {
        return Some(CLASS_TMP.to_string());
    }
    if DEPENDENCY_MARKERS
        .iter()
        .any(|marker| normalized.contains(marker))
    {
        return Some(CLASS_DEPENDENCY_CACHE.to_string());
    }
    if SYSTEM_PREFIXES
        .iter()
        .any(|prefix| normalized.starts_with(prefix))
    {
        return Some(CLASS_SYSTEM.to_string());
    }
    if let Some(rest) = home_relative(&normalized) {
        return Some(if is_working_tree(rest) {
            CLASS_REPO.to_string()
        } else {
            CLASS_HOME.to_string()
        });
    }
    Some(CLASS_OTHER.to_string())
}

/// Same buckets as [`path_class`], named for working directories.
pub fn cwd_class(path: &str) -> Option<String> {
    path_class(path)
}

/// Workspace projection for host-session rows: the [`path_class`] bucket and the
/// workspace's own basename, e.g. `repo:agentsight`.
///
/// An operator reading a machine-wide session list needs to tell two checkouts
/// apart, which the bucket alone cannot do; the basename is the least that
/// answers it. Nothing that led to the workspace survives — not the parent
/// directories and, deliberately, not the account name: for a path that *is* a
/// home root (`/Users/alice`) the only basename available is the user, so the
/// class is returned alone rather than with it.
pub fn workspace_class(path: &str) -> Option<String> {
    let class = path_class(path)?;
    match workspace_basename(path) {
        Some(basename) => Some(format!("{class}:{basename}")),
        None => Some(class),
    }
}

fn workspace_basename(path: &str) -> Option<String> {
    let trimmed = path.trim().trim_end_matches('/');
    let normalized = format!("{trimmed}/");
    // Under a home prefix only the home-relative part may be named, so the
    // account component can never become the basename.
    let nameable = home_relative(&normalized).unwrap_or(trimmed);
    let basename = nameable.trim_end_matches('/').rsplit('/').next()?.trim();
    (!basename.is_empty() && !basename.contains('=')).then(|| basename.to_string())
}

fn home_relative(normalized: &str) -> Option<&str> {
    HOME_PREFIXES.iter().find_map(|prefix| {
        let rest = normalized.strip_prefix(prefix)?;
        // "/home/<user>/..." and "/Users/<user>/..." carry a user component;
        // "/root/..." does not.
        if *prefix == "/root" {
            Some(rest.strip_prefix('/').unwrap_or(rest))
        } else {
            rest.split_once('/').map(|(_user, rest)| rest)
        }
    })
}

fn is_working_tree(home_relative: &str) -> bool {
    let first = home_relative.split('/').find(|part| !part.is_empty());
    first.is_some_and(|part| !part.starts_with('.'))
}

/// Lowercase file extension of a path, when it looks like one.
pub fn extension(path: &str) -> Option<String> {
    let basename = path.rsplit('/').next()?;
    let (_stem, extension) = basename.rsplit_once('.')?;
    let extension = extension.trim().to_ascii_lowercase();
    (!extension.is_empty()
        && extension.len() <= 16
        && extension.chars().all(|c| c.is_ascii_alphanumeric()))
    .then_some(extension)
}

/// Basename of an executable path or command string. Never a path, and never
/// a shell-style `KEY=value` assignment: leading environment prefixes
/// (`API_KEY=... cmd`) are skipped, and a candidate that still contains `=`
/// is refused outright rather than risk echoing a value.
pub fn executable_basename(command: &str) -> Option<String> {
    let command = command.trim();
    if command.is_empty() {
        return None;
    }
    let first = command
        .split_whitespace()
        .find(|token| !is_env_assignment(token))?;
    let basename = first.rsplit('/').next().unwrap_or(first);
    (!basename.is_empty() && !basename.contains('=')).then(|| basename.to_string())
}

fn is_env_assignment(token: &str) -> bool {
    match token.split_once('=') {
        None => false,
        Some((name, _value)) => {
            !name.is_empty()
                && name
                    .chars()
                    .enumerate()
                    .all(|(i, c)| c == '_' || c.is_ascii_alphabetic() || (i > 0 && c.is_ascii_digit()))
        }
    }
}

/// Token-class summary of an argument vector: no argument value survives.
pub fn argv_shape(argv: &[String]) -> Option<String> {
    const MAX_TOKENS: usize = 24;
    if argv.is_empty() {
        return None;
    }
    let mut shape = Vec::with_capacity(argv.len().min(MAX_TOKENS) + 1);
    for (index, token) in argv.iter().take(MAX_TOKENS).enumerate() {
        shape.push(if index == 0 {
            "cmd"
        } else if token.starts_with('-') {
            "<flag>"
        } else if !token.is_empty() && token.chars().all(|c| c.is_ascii_digit()) {
            "<num>"
        } else if token.contains('/') || token.starts_with('~') || token.starts_with('.') {
            "<path>"
        } else if token.contains('=') {
            "<kv>"
        } else {
            "<arg>"
        });
    }
    if argv.len() > MAX_TOKENS {
        shape.push("<trunc>");
    }
    Some(shape.join(" "))
}

/// AgentSight's own command fingerprint: a digest over the executable basename
/// and the argv shape, both already content-free.
pub fn command_fingerprint(basename: Option<&str>, shape: Option<&str>) -> Option<String> {
    if basename.is_none() && shape.is_none() {
        return None;
    }
    Some(digest_hex(&format!(
        "{REDACTION_VERSION}\n{}\n{}",
        basename.unwrap_or_default(),
        shape.unwrap_or_default()
    )))
}

/// Known model-provider hosts. Kept explicit so an unrecognized host can never
/// be echoed back inside a `model_provider:` label.
const MODEL_PROVIDER_HOSTS: [(&str, &str); 12] = [
    ("openai.azure.com", "azure.ai.openai"),
    ("api.openai.com", "openai"),
    ("api.anthropic.com", "anthropic"),
    ("generativelanguage.googleapis.com", "gcp.gen_ai"),
    ("aiplatform.googleapis.com", "gcp.gen_ai"),
    ("bedrock-runtime", "aws.bedrock"),
    ("api.mistral.ai", "mistral"),
    ("api.cohere.com", "cohere"),
    ("api.groq.com", "groq"),
    ("api.deepseek.com", "deepseek"),
    ("api.x.ai", "xai"),
    ("openrouter.ai", "openrouter"),
];

fn model_provider(host: &str) -> Option<&'static str> {
    MODEL_PROVIDER_HOSTS
        .iter()
        .find(|(needle, _)| host.contains(needle))
        .map(|(_, provider)| *provider)
}

/// Classify a network destination to at most eTLD+1, never a path or query.
///
/// `provider` is the provider name the capture pipeline already attributed to
/// the call; it is only trusted when it is one of the known provider names, so
/// a raw host can never leak through the `model_provider:` label.
pub fn destination_class(host: &str, provider: Option<&str>) -> Option<String> {
    let host = normalize_host(host)?;
    if let Some(provider) = provider.filter(|provider| {
        MODEL_PROVIDER_HOSTS
            .iter()
            .any(|(_, known)| known == provider)
    }) {
        return Some(format!("model_provider:{provider}"));
    }
    if let Some(provider) = model_provider(&host) {
        return Some(format!("model_provider:{provider}"));
    }
    if matches!(host.as_str(), "localhost" | "127.0.0.1" | "::1") || host.starts_with("127.") {
        return Some("localhost".to_string());
    }
    if is_private_address(&host) {
        return Some("private_net".to_string());
    }
    if PACKAGE_REGISTRY_HOSTS.contains(&host.as_str()) {
        return Some("package_registry".to_string());
    }
    if VCS_HOSTS.contains(&host.as_str()) {
        return Some("vcs_host".to_string());
    }
    Some(format!("public:{}", etld_plus_one(&host)))
}

/// Port carried by a `host:port` or URL-shaped target, when present.
pub fn destination_port(target: &str) -> Option<u16> {
    let target = strip_scheme(target);
    let authority = target.split(['/', '?', '#']).next()?;
    if authority.starts_with('[') {
        return authority.rsplit_once("]:")?.1.parse().ok();
    }
    let (_host, port) = authority.rsplit_once(':')?;
    port.parse().ok()
}

/// Host component of a raw target string (URL, `host:port`, or bare host).
pub fn target_host(target: &str) -> Option<String> {
    normalize_host(target)
}

fn strip_scheme(target: &str) -> &str {
    target
        .split_once("://")
        .map(|(_scheme, rest)| rest)
        .unwrap_or(target)
}

fn normalize_host(target: &str) -> Option<String> {
    let target = strip_scheme(target.trim());
    let authority = target.split(['/', '?', '#']).next()?;
    let authority = authority
        .rsplit_once('@')
        .map(|(_credentials, rest)| rest)
        .unwrap_or(authority);
    let host = if let Some(rest) = authority.strip_prefix('[') {
        rest.split_once(']').map(|(host, _)| host)?
    } else {
        authority.split(':').next()?
    };
    let host = host.trim().trim_end_matches('.').to_ascii_lowercase();
    (!host.is_empty()).then_some(host)
}

fn is_private_address(host: &str) -> bool {
    if let Ok(address) = host.parse::<std::net::Ipv4Addr>() {
        return address.is_private() || address.is_link_local() || address.is_loopback();
    }
    if let Ok(address) = host.parse::<std::net::Ipv6Addr>() {
        let first = address.segments()[0];
        return address.is_loopback() || (first & 0xfe00) == 0xfc00 || (first & 0xffc0) == 0xfe80;
    }
    false
}

fn etld_plus_one(host: &str) -> String {
    let labels = host.split('.').collect::<Vec<_>>();
    if labels.len() <= 2 {
        return host.to_string();
    }
    let last_two = labels[labels.len() - 2..].join(".");
    if MULTI_LABEL_SUFFIXES.contains(&last_two.as_str()) && labels.len() >= 3 {
        return labels[labels.len() - 3..].join(".");
    }
    last_two
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn path_classes_are_coarse_buckets() {
        assert_eq!(path_class("/tmp/build/out.o").as_deref(), Some(CLASS_TMP));
        assert_eq!(
            path_class("/Users/dev/project/node_modules/left-pad/index.js").as_deref(),
            Some(CLASS_DEPENDENCY_CACHE)
        );
        assert_eq!(
            path_class("/usr/lib/libc.so").as_deref(),
            Some(CLASS_SYSTEM)
        );
        assert_eq!(
            path_class("/Users/dev/project/src/main.rs").as_deref(),
            Some(CLASS_REPO)
        );
        assert_eq!(
            path_class("/home/dev/.config/app.toml").as_deref(),
            Some(CLASS_HOME)
        );
        assert_eq!(path_class("relative/path").as_deref(), Some(CLASS_OTHER));
        assert_eq!(path_class("   "), None);
    }

    #[test]
    fn workspace_class_names_the_workspace_and_nothing_above_it() {
        assert_eq!(
            workspace_class("/Users/dev/secret-project").as_deref(),
            Some("repo:secret-project")
        );
        assert_eq!(
            workspace_class("/home/dev/work/agentsight/").as_deref(),
            Some("repo:agentsight")
        );
        assert_eq!(
            workspace_class("/tmp/build-42").as_deref(),
            Some("tmp:build-42")
        );
        // A home root has no basename but the account name, so it gets none.
        assert_eq!(workspace_class("/Users/dev").as_deref(), Some("home"));
        assert_eq!(workspace_class("/home/dev/").as_deref(), Some("home"));
        assert_eq!(workspace_class("   "), None);
    }

    #[test]
    fn workspace_class_never_carries_the_path_that_led_to_it() {
        let projected = workspace_class("/Users/canaryuser/code/secret-project").unwrap();
        assert!(!projected.contains('/'), "{projected}");
        assert!(!projected.contains("canaryuser"), "{projected}");
        assert!(!projected.contains("code"), "{projected}");
    }

    #[test]
    fn extensions_are_short_alphanumeric_suffixes() {
        assert_eq!(extension("/repo/src/main.rs").as_deref(), Some("rs"));
        assert_eq!(extension("/repo/Makefile"), None);
        assert_eq!(extension("/repo/archive.tar.gz").as_deref(), Some("gz"));
        assert_eq!(extension("/repo/weird.a-b"), None);
    }

    #[test]
    fn argv_shape_keeps_no_argument_values() {
        let argv = [
            "/usr/bin/git".to_string(),
            "--no-pager".to_string(),
            "log".to_string(),
            "/repo/secret.txt".to_string(),
            "42".to_string(),
            "TOKEN=sk-live-abcdef".to_string(),
        ]
        .to_vec();
        let shape = argv_shape(&argv).unwrap();
        assert_eq!(shape, "cmd <flag> <arg> <path> <num> <kv>");
        assert!(!shape.contains("secret"));
        assert!(!shape.contains("sk-live"));
    }

    #[test]
    fn executable_basename_never_returns_a_path() {
        assert_eq!(
            executable_basename("/usr/bin/node").as_deref(),
            Some("node")
        );
        assert_eq!(
            executable_basename("/opt/tools/agent --flag").as_deref(),
            Some("agent")
        );
        assert_eq!(executable_basename("  "), None);
    }

    #[test]
    fn executable_basename_never_returns_an_env_assignment() {
        assert_eq!(
            executable_basename("API_KEY=sk-live-abcdef python train.py").as_deref(),
            Some("python")
        );
        assert_eq!(
            executable_basename("A=1 B=2 /usr/bin/env node run.js").as_deref(),
            Some("env")
        );
        // Nothing but assignments: refuse rather than echo a value.
        assert_eq!(executable_basename("TOKEN=sk-live-abcdef"), None);
        // A basename that still carries '=' (not a shell env name) is refused.
        assert_eq!(executable_basename("./weird=name"), None);
    }

    #[test]
    fn command_fingerprint_is_stable_and_shape_sensitive() {
        let first = command_fingerprint(Some("git"), Some("cmd <flag>")).unwrap();
        let same = command_fingerprint(Some("git"), Some("cmd <flag>")).unwrap();
        let different = command_fingerprint(Some("git"), Some("cmd <path>")).unwrap();
        assert_eq!(first, same);
        assert_ne!(first, different);
        assert_eq!(first.len(), 64);
        assert_eq!(command_fingerprint(None, None), None);
    }

    #[test]
    fn destination_classes_stop_at_etld_plus_one() {
        assert_eq!(
            destination_class("api.anthropic.com", None).as_deref(),
            Some("model_provider:anthropic")
        );
        assert_eq!(
            destination_class("https://registry.npmjs.org/left-pad", None).as_deref(),
            Some("package_registry")
        );
        assert_eq!(
            destination_class("github.com", None).as_deref(),
            Some("vcs_host")
        );
        assert_eq!(
            destination_class("127.0.0.1:8080", None).as_deref(),
            Some("localhost")
        );
        assert_eq!(
            destination_class("10.1.2.3", None).as_deref(),
            Some("private_net")
        );
        assert_eq!(
            destination_class("https://sub.deep.example.co.uk/path?q=secret", None).as_deref(),
            Some("public:example.co.uk")
        );
        assert_eq!(
            destination_class("https://a.b.example.com/x", None).as_deref(),
            Some("public:example.com")
        );
        assert_eq!(destination_class("", None), None);
    }

    #[test]
    fn destination_port_reads_authority_only() {
        assert_eq!(
            destination_port("https://example.com:8443/path"),
            Some(8443)
        );
        assert_eq!(destination_port("example.com"), None);
        assert_eq!(destination_port("[::1]:9000"), Some(9000));
    }
}
