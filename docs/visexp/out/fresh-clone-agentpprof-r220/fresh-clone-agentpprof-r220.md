# R220 Fresh-Clone agentpprof Smoke

Status: `passed`

R220 clones the repository into a temporary clean checkout, creates a public
synthetic Codex fixture under `.codex/sessions/...`, and runs the real Rust
`agentpprof` CLI with the deterministic regex tagger. It does not read local
Codex/Claude histories, does not call an LLM, and does not create C5/C6 human
evidence.

## Main Results

- Source commit: `1d06372` on `research/semantic-flamegraph-artifacts`
- Clone clean before fixture: `True`
- `agentpprof` views passed: `True`
- `go tool pprof` readback passed: `True`
- Fixture expected-stack checks passed: `True`
- Output containment passed: `True`
- Redaction scan passed: `True`
- Weak accept supported: `False`

## View Samples

| View | Format | Samples | Unique stacks | Output |
|------|--------|---------|---------------|--------|
| `tasks` | `pprof` | 6 | 6 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/tasks.pb.gz` |
| `tools` | `folded` | 4 | 4 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/tools.folded` |
| `tokens` | `json` | 190 | 4 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/tokens.json` |
| `files` | `folded` | 3 | 3 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/files.folded` |
| `network` | `folded` | 1 | 1 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/network.folded` |
| `tools_svg` | `svg` | 4 | 4 | `docs/visexp/out/fresh-clone-agentpprof-r220/profiles/tools.svg` |

## Boundaries

- This is a community-tool smoke and C7 artifact-usability result, not a user
  study.
- It validates regex-tagged, public-fixture `agentpprof` operation from a clean
  clone; it does not validate llama.cpp setup, real-history privacy, external
  machine adoption, C5 developer task outcomes, or C6 tag adequacy.
- Parent worktree dirtiness is not a pass gate; the clean-clone oracle is the
  temporary clone status before fixture creation.
- `go tool pprof` output is saved at `docs/visexp/out/fresh-clone-agentpprof-r220/pprof-top-r220.txt`.
