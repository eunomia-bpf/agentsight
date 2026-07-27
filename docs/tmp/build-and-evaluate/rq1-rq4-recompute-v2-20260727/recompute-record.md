# Recompute record

## Scope and immutable inputs

- Repository projection commit:
  `51f7cece251888a0bf559044b62188d499222e9a`
  (`research: repair shell boundary conformance`).
- Exact release binary:
  `shell-boundary-repair-20260726/build/cargo-target/release/agentvis`.
- Binary SHA-256:
  `8b1351911d72dd33f776613cb5f9b48d50ecfb85be95db17b0205e85c1f7c4b3`.
- Cutoff: `1784708569241` ms.
- Native-session source: the same real-HOME corpus used by the preceding
  authoritative run.
- Paper and evaluation files were read-only in this stage.

| Project | Root | Project revision at projection |
|---|---|---|
| agentsight | `/home/yunwei37/workspace/agentsight` | `273773d7cf5e94ffd27652e9357184e25ca7c9d0` |
| ActPlane | `/home/yunwei37/workspace/ActPlane` | `50a1619fae1c13553c13ea032f1dba67e7046879` |
| bpf-developer-tutorial | `/home/yunwei37/workspace/bpf-developer-tutorial` | `21e9d9996bf3097e888a764ef0d0b924a11d041a` |
| eunomia.dev | `/home/yunwei37/workspace/eunomia.dev` | `62410ec4537956af0fd46fb71696e4c859a33bc1` |
| agentskill-observability-paper | `/home/yunwei37/workspace/agentskill-observability-paper` | `83138a4edc0858f1e4678461af18ed595e3dbbf9` |
| academic-writing-skills | `/home/yunwei37/workspace/my-paper-work/academic-writing-skills` | `eb13203b199c694f20206dfebc2cf9f2995e7707` |

## Projection command

The first and second runs used the same command, changing only `--output`:

```bash
docs/tmp/build-and-evaluate/shell-boundary-repair-20260726/build/cargo-target/release/agentvis \
  research-rq1 \
  --cutoff-ms 1784708569241 \
  --output <run>/rq1-raw \
  /home/yunwei37/workspace/agentsight \
  /home/yunwei37/workspace/ActPlane \
  /home/yunwei37/workspace/bpf-developer-tutorial \
  /home/yunwei37/workspace/eunomia.dev \
  /home/yunwei37/workspace/agentskill-observability-paper \
  /home/yunwei37/workspace/my-paper-work/academic-writing-skills
```

Run 1 is this directory. Run 2 was produced under the temporary directory
`/tmp/agentsight-rq1-rq4-v2-rerun.ciVefV`.

Both scientific projections contain:

- 6 projects;
- 551 included and attributed native roots;
- 181,303 Tool actions, 176,288 worktree-attributed;
- 5,676 artifact identities;
- 13,809 confirmed mutation rows.

The uncompressed event JSON files are retained locally but ignored; their
deterministic gzip exports are part of the committed output.

## Downstream steps

The RQ1--RQ4 scripts were copied from `rq1-rq4-recompute-final` and executed
against each run's `rq1-raw`:

```bash
python scripts/plot_rq1.py --input <run>/rq1-raw --output <run>/rq1-figures
python scripts/plot_rq2.py --rq1-root <run>/rq1-raw --output <run>/rq2
python scripts/plot_rq3.py --rq1-root <run>/rq1-raw --output <run>/rq3
python scripts/plot_rq4.py --rq1-root <run>/rq1-raw --output <run>/rq4
```

RQ3 allocation/migration must retain both `ok` and `observed` path-resolved
actions. It therefore does **not** consume RQ4's confirmed-effect-only access
ledger. The compatibility-named `rq3-input/rq4-accesses.csv` was independently
rebuilt from repaired events:

```bash
python scripts/build_rq3_accesses.py \
  --events-dir <run>/rq1-raw/events \
  --output <run>/rq3-input/rq4-accesses.csv

python scripts/run_rq3_allocation.py \
  --rq1-root <run>/rq1-raw \
  --rq4-root <run>/rq3-input \
  --output <run>/rq3-allocation

python scripts/run_rq6_local_anchor.py \
  --input <run>/rq3-input/rq4-accesses.csv \
  --output <run>/rq6-local-anchor/local-anchor.csv \
  --metadata <run>/rq6-local-anchor/local-anchor.json
```

The status-preserving access ledger has 68,886 rows and SHA-256
`372584e828f1f46b8ae68b5381fcf90042a28397383f8adfa74ec3f638268ab0`.
Both the RQ3 allocation wrapper and the RQ6 local-anchor wrapper pin this hash.
This closes the audit's stale-anchor provenance finding.

The extension script was rerun against each repaired RQ1 root:

```bash
python docs/tmp/build-and-evaluate/rq-extensions-20260726/analyze_rq_extensions.py \
  --rq1-root <run>/rq1-raw \
  --output <run>/extensions
```

The sensitivity-only RQ7/user-question/session-dynamics checks are implemented
in `scripts/sensitivity_spotcheck.py`; they intentionally compute only the
selected identity-dependent estimands recorded in
`sensitivity-spotcheck.json`, not the full downstream bundles.

## Primary output hashes

| Output | SHA-256 |
|---|---|
| `rq1-raw/projects.json` | `55002b46cb1edaa580448d5c214f0401319eed82e5545a25c7e9d763d6407ce4` |
| `rq1-raw/rq1-artifacts.csv` | `2d6822f6e7db4ac7ba6807b450df716bb35a9855cfa751b4258e1e89722d5710` |
| `rq1-raw/rq1-mutations.csv` | `5832ce7b3212220f25a669481d5cc370050aec231d2476267d9acff609c70a38` |
| `rq1-raw/rq1-summary.csv` | `a988de69d86f57353f9d4f8b6e91ae968df68988d901a1ff89e265cbdd3ac348` |
| `rq3-input/rq4-accesses.csv` | `372584e828f1f46b8ae68b5381fcf90042a28397383f8adfa74ec3f638268ab0` |
| `sensitivity-spotcheck.json` | `a6cc801e984dd2f26cfb5b9bfcfe722c7473c98ecad1505c6caaa7781e4c35be` |

Event gzip hashes:

| Project | SHA-256 |
|---|---|
| agentsight | `29bffeef74683bfb4771c8bc6b4bec659f34bc43183693cd5840de16d435e79b` |
| ActPlane | `eb1a718f5560fab2c723a2a1da92b349498b9ff4b5cbeef4ba67c8c9b00290c8` |
| bpf-developer-tutorial | `9e9ded72578a322af86adc582f8e8cd5754f630ad8efc44fd0d5cf3345a3cd92` |
| eunomia.dev | `4cde11326722cbdfdbe052e87132d60cd91d420f55046bab4050ebaa5ff892fb` |
| agentskill-observability-paper | `4b303eec0880d2d3f28eda803d3db19d88695b8ec7c25930a4296c59218d55f6` |
| academic-writing-skills | `4d5a255679888e1b4e70e1ee6f9626ff700484b2ed1f7bf1d566a396133a50b6` |

The exact rerun comparison and its one non-estimand diagnostic difference are
documented in `consistency-check.md`.
