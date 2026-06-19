# R256 agentpprof Crate Package Smoke

Status: `passed`

R256 runs `cargo package --list` and `cargo package` for `agentpprof` on a clean
repository snapshot, then records the crate file set and verification result.
This checks local crate-package readiness only. It does not publish to crates.io,
run on an external machine, collect user feedback, call a model, or add C5/C6
outcome evidence.

## Package

- package: `agentpprof 0.2.0`
- manifest: `agentpprof/Cargo.toml`
- crate archive: `<tmp-r256>/cargo-target/package/agentpprof-0.2.0.crate`
- crate archive bytes: `35438`
- cargo-reported size: `145.3KiB` (`34.6KiB compressed`)
- registry dependency observed: `True`
- source commit: `a388c89ce718849ebfa5b8610709cbb50cf66b48`
- repo dirty before package: `False`

## Files

| Packaged file |
|---------------|
| `.cargo_vcs_info.json` |
| `Cargo.lock` |
| `Cargo.toml` |
| `Cargo.toml.orig` |
| `README.md` |
| `examples/README.md` |
| `examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl` |
| `src/main.rs` |

## Gates

| Gate | Passed |
|------|--------|
| `repo_clean_before_package` | `True` |
| `package_list_ok` | `True` |
| `cargo_package_ok` | `True` |
| `required_files_present` | `True` |
| `archive_created` | `True` |
| `archive_files_match_list` | `True` |
| `forbidden_paths_absent` | `True` |
| `registry_dependency_observed` | `True` |
| `crate_verify_observed` | `True` |
| `no_private_history_discovery` | `True` |
| `no_llm_calls` | `True` |
| `c5_supported` | `False` |
| `c6_supported` | `False` |
| `crates_publish_supported` | `False` |
| `weak_accept_supported` | `False` |
| `summary_privacy_scan` | `True` |

## Boundary

`c7_crate_package_smoke_supported=True`
only means the crate can be packaged and verified locally with its intended file
set and registry dependency resolution. It is not a crates.io release,
community-adoption result, developer-utility result, tag-adequacy result, or
weak-accept result.
