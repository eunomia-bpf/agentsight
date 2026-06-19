# R254 agentpprof Pinned-Revision Install Smoke

Status: `passed`

R254 installs `agentpprof` with `cargo install --git --rev` from a pinned
GitHub revision, runs the installed binary on the committed public Codex fixture,
and checks Go pprof readback plus folded/JSON/SVG projections. It does not read
private Codex/Claude history, does not call a live tagger/model, and does not
add C5/C6 outcome evidence.

## Install Path

- git URL: `https://github.com/eunomia-bpf/agentsight`
- revision: `c43daf2b2565531dfd95de8654adabb30ac878d4`
- install rev matches driver commit: `True`
- installed help passed: `True`
- fixture: `agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl`
- fixture sha256: `391675afb8db6fda7516a4a4177b40f081e47528e0e36d8b19a4a0535abc1ad5`
- driver commit: `c43daf2b2565531dfd95de8654adabb30ac878d4`
- driver dirty before generation: `False`

## Views

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
| `tasks` | `pprof` | 6 | 6 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/tasks.pb.gz` |
| `tools` | `folded` | 4 | 4 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/tools.folded` |
| `tokens` | `json` | 190 | 4 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/tokens.json` |
| `files` | `folded` | 3 | 3 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/files.folded` |
| `network` | `folded` | 1 | 1 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/network.folded` |
| `tools_svg` | `svg` | 4 | 4 | `docs/visexp/out/agentpprof-pinned-rev-install-r254/profiles/tools.svg` |

## Gates

| Gate | Passed |
|------|--------|
| `cargo_git_install_ok` | `True` |
| `installed_help_ok` | `True` |
| `install_rev_matches_driver_commit` | `True` |
| `committed_fixture_exists` | `True` |
| `fixture_path_is_codex_session_shape` | `True` |
| `all_views_nonzero` | `True` |
| `all_outputs_exist` | `True` |
| `pprof_readback` | `True` |
| `folded_json_totals_match_stdout` | `True` |
| `fixture_projection_expected_stacks` | `True` |
| `output_containment` | `True` |
| `privacy_scan` | `True` |
| `explicit_session_file_only` | `True` |
| `no_llm_calls` | `True` |
| `no_private_history_discovery` | `True` |
| `c5_supported` | `False` |
| `c6_supported` | `False` |

## Boundary

`c7_pinned_rev_install_smoke_supported=True`
only means a GitHub-installed CLI from this exact revision can process the
committed public fixture and produce readable pprof/folded/JSON/SVG artifacts.
It does not support developer utility, tag adequacy, real-history privacy,
external-machine adoption, llama.cpp setup, crates.io release, or weak accept.
