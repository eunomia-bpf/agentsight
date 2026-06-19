# R248 agentpprof Install Smoke

Status: `passed`

R248 installs `agentpprof` from the local package with `cargo install --path`,
runs the installed binary on a committed public Codex fixture, and checks Go
pprof readback plus folded/JSON/SVG projections. It does not read private
Codex/Claude history, does not call a model, and does not add C5/C6 outcome
evidence.

## Package Path

- install command: `cargo install --path agentpprof --locked --force`
- installed help passed: `True`
- fixture: `agentpprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl`
- fixture sha256: `391675afb8db6fda7516a4a4177b40f081e47528e0e36d8b19a4a0535abc1ad5`
- source commit: `4ac7e0907bf954567cc8a5d3962ceb008df33a13`
- source dirty before generation: `False`

## Views

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
| `tasks` | `pprof` | 6 | 6 | `docs/visexp/out/agentpprof-install-r248/profiles/tasks.pb.gz` |
| `tools` | `folded` | 4 | 4 | `docs/visexp/out/agentpprof-install-r248/profiles/tools.folded` |
| `tokens` | `json` | 190 | 4 | `docs/visexp/out/agentpprof-install-r248/profiles/tokens.json` |
| `files` | `folded` | 3 | 3 | `docs/visexp/out/agentpprof-install-r248/profiles/files.folded` |
| `network` | `folded` | 1 | 1 | `docs/visexp/out/agentpprof-install-r248/profiles/network.folded` |
| `tools_svg` | `svg` | 4 | 4 | `docs/visexp/out/agentpprof-install-r248/profiles/tools.svg` |

## Gates

| Gate | Passed |
|------|--------|
| `cargo_install_ok` | `True` |
| `installed_help_ok` | `True` |
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

`c7_install_smoke_supported=True` only
means the installed CLI can process the committed public fixture and produce
readable pprof/folded/JSON/SVG artifacts. It does not support developer utility,
tag adequacy, real-history privacy, external-machine adoption, llama.cpp setup,
or weak accept.
