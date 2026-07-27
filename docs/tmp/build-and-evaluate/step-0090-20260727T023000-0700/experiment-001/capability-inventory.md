# Capability inventory

Inventory date: 2026-07-27  
Binary: `agentpprof 0.2.37`  
Scope: current source and retained artifacts only; no new capture and no LLM annotation

## Current product behavior

The current local-session adapter preserves timestamps, tool effects,
path groups, domains, status, token counts, and task paths in
`agentpprof/src/session.rs`.

The direct local-session profile builder in `agentpprof/src/profile.rs`
materializes five views:

| CLI view | Current additive value | Important boundary |
|---|---|---|
| `operations` | one per prompt/tool/LLM operation | available |
| `tokens` | provider-reported token components | available when the source reports them |
| `files` | one per `path_groups` entry on any tool carrying a path | combines reads and writes; it does not filter on `effect` |
| `network` | one per domain, or one `unknown` sample for a network-classified tool without a domain | source-tool/network-domain evidence, not an eBPF socket-connection counter |
| `time` | start-to-next-event wall time in integer seconds, with a one-second minimum and a one-second terminal sample | elapsed source-event interval, not active CPU time |

The annotation-workspace creator in
`agentpprof/src/annotation_workspace.rs` currently writes only:

- `operations` on tool nodes; and
- `tokens` on LLM nodes.

Annotation replay has metric-name branches for `files`, `network`, and
`time_ns`, but workspace creation does not populate those metrics. Therefore
an existing workspace cannot replay those three views unless a deterministic
adapter adds measure rows from retained source fields.

The normalized `--operation-file` importer accepts an arbitrary positive
integer `value`, arbitrary stack fields, a chosen view's pprof metadata, and
deterministic output. It is sufficient for this experiment; no product change
is needed.

## Input-family matrix

| Input family | Retained evidence | Materializable now | Not materializable from retained artifact |
|---|---|---|---|
| Frozen Git workspace | 735 nodes: 3 sessions, 3 prompts, 240 LLM calls, 489 tools; metrics are exactly 489 operations and 4,558,192 tokens | count and tokens directly; elapsed time by deterministic join to the three frozen raw CodeTrace archives | file read/write and network *system effects*; the workspace has no timestamps, effect tags, path groups, domains, or eBPF recording |
| Step-0086 self-profile workspace | 10,423 nodes: 42 sessions, 1,252 prompts, 5,620 LLM calls, 3,509 tools; 10,016 timestamped nodes; source data includes effect/status/path/domain fields | count and tokens directly; elapsed time derivable; source-level file-read, file-write, and network target-reference widths derivable | eBPF connection counts or kernel file effects; the workspace is local-session evidence, not a live AgentSight recording |
| R114 AgentSight suite | 20 real Codex tasks; 1,520 retained scoped effects across 20 tasks and one recorded wrapper-tool ID per task | effect-count width and drilldown through task/category, wrapper tool, effect, process, and retained target group | file-read (0 retained), network (0 retained), per-effect duration, exact file basename for coarse file groups, individual inner LLM/tool IDs, and raw event IDs; original `/tmp` snapshots/DBs/lineage CSVs are no longer present |

## Artifact facts

### Frozen Git case

`docs/visexp/out/codex-agent-long-horizon-v1/annotation-workspace-git-v1/trace.jsonl`
contains only the metric keys `operations` and `tokens`; none of its 735 nodes
has `data.timestamp_ms`. The accepted hierarchy and its 489 tool evidence IDs
are replayable unchanged through the already-validated sparse operation marks
under `.agentsight/experiments/rq1-matched-organization-v1/full/`.

The corresponding three raw CodeTrace archives are retained. OpenHands records
an ISO timestamp on every selected agent action. Terminus2 records every
selected command as an asciinema input timestamp. This makes elapsed
start-to-next-start time derivable for all 489 accepted evidence rows without
changing any boundary or operation name.

There is no eBPF recording for these three Git executions. Commands that mention
SSH, `curl`, or files are not treated as kernel network/file effects.

### Step-0086 self profile

Tool classifications in the frozen trace are:

| Source-adapter effect | Tool events |
|---|---:|
| read | 798 |
| write | 43 |
| network | 55 |
| process | 2,590 |
| repo | 20 |
| test | 3 |

All 55 network-classified events have status `ok`; the five failed tools are
not network-classified. The trace has 737 read path-group references and 30
write path-group references before exact `apply_patch` target repair. Six
`apply_patch` records retain `Add File`/`Update File` headers in
`arguments_preview`, including exact created filenames. These support the
amended created-file drilldown at source-tool level.

These effect labels are parser classifications. In particular, shell-command
classification can be coarse; the demonstration must call them source-adapter
effects, not kernel-observed effects.

### R114

The retained R114 operation population contains:

| Scoped real effect | Rows |
|---|---:|
| `process.exec` | 745 |
| `process.exit` | 740 |
| `file.write` | 35 |
| file read | 0 |
| network | 0 |
| **Total** | **1,520** |

R114's result record reports 100% precision, 96.569% recall, 1,520 true
positives, zero joined negative-control effects, and 20/20 completed tasks.
The 35 file-write rows retain only coarse target groups such as
`home/yunwei37` or a sandbox mount group. They do not identify `result.json` or
another exact basename, so the R114 profile must not claim that they do.

## Amendment disposition

- **FILE-READ and FILE-WRITE:** separate profiles will be constructed from
  Step-0086 source-adapter target references.
- **Created files:** exact `Add File` targets will be leaves below their
  accepted semantic operation, parent LLM node, and `apply_patch` call.
- **Network width:** Step-0086 supplies successful network/domain effects;
  R114 and the frozen Git workspace supply no retained network effects.
- **Network failure correlation:** unavailable. Step-0086 has no failed
  network-classified event, R114 has zero network rows, and the Git runs have
  no eBPF network capture. No command-text proxy will be substituted.
- **System-effect chain:** R114 supports
  task responsibility -> recorded Codex wrapper tool -> process/file system
  effects. It does not retain inner LLM call IDs or exact file basenames.
  Step-0086 separately supports the complete semantic-operation -> LLM ->
  tool -> read/write/network-target source-evidence chain. The results will
  present both and keep this provenance boundary explicit.

## Product-change decision

No product code change is required or justified for this run. A small
experiment-local, deterministic adapter and tests will:

1. join Git evidence IDs to retained raw timestamps;
2. project Step-0086 effect targets without changing semantic paths; and
3. attach R114's retained per-task wrapper-tool IDs to its retained effect
   rows.

The only product artifact for each replay remains one standard `.pb.gz`
profile.
