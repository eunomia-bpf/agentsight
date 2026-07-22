# Research Design Frontier

## Current method

The project studies long-running Agent work as an ordered process that changes
a persistent workspace across native session boundaries. It reuses
`agent-session` as the only cross-vendor source abstraction and adds no second
general event IR. `agentvis` performs a repository-scoped projection for two
consumers:

```text
Claude / Codex / Gemini native sessions
                 |
                 v
        agent-session ToolEvent
                 |
       repository identity + path resolution
                 |
                 v
   ordered actions + artifact effects + session lineage
          |                              |
          v                              v
 empirical metrics and tables     Agent Nebula media
```

The empirical path consumes structured events, not pixels. The visual path
uses the same event order and artifact effects but may apply presentation-only
layout forces, decay and media compaction. The scientific contract is in
`docs/empirical-study.zh-CN.md`; the visual algorithm is in
`docs/repository-nebula.zh-CN.md`.

## Repository and session selection

For repository root `R`, discover native Claude, Codex and Gemini sessions and
admit a complete session when its native project directory, cwd/worktree root,
or Git remote identifies `R`. Preserve all Tool events in admitted sessions,
including Bash, validation and other actions with no resolved file path.

An optional global path scan can recover file effects from external sessions
that mention `R`, but those rows lack surrounding no-file actions. They form a
separate coverage sensitivity source and never enter validation-cadence or
session-reset denominators.

## Deterministic projection

For each admitted native action retain:

```text
a_i = (timestamp, source_id, session_id, vendor,
       tool_name, category, command_effect, status)
e_i = [(artifact_path, access, previous_path, scope)]
```

where `source_id` is the native call identifier when present, otherwise the
stable session and ordinal identifier. Sort by `(timestamp, source_id)`.
Failed calls remain actions but emit no successful file effect.

The projection performs one pass over sorted actions:

1. normalize every source-qualified path relative to a known repository
   worktree and discard paths outside the repository;
2. retain source-native read, write, create, rename and delete effects;
3. preserve explicit rename lineage; a later create at a deleted path is a new
   artifact unless the source says otherwise;
4. retain directory-scope references as weak scope effects rather than
   pretending every descendant was read;
5. retain source-native command effect and status so successful test/check/
   build/experiment actions can be observed; and
6. derive final path existence and tracked state from the current workspace and
   Git without moving the action-time axis onto commits.

If inputs are ordered, projection time is `O(|A| + |E|)` plus repository-state
lookups; otherwise sorting costs `O(|A| log |A|)`. Artifact maps require
`O(|F|)` live state and exported rows require `O(|A| + |E|)` space.

## Measurement derivations

The core projection contains no progress score, pathology label or intent
inference. RQ analyses derive transparent measurements:

- **durability:** final tracked/existing state and explicit lifecycle survival;
- **reuse:** the next later access to the same artifact lineage and its event,
  time and session distance;
- **validation association:** the next later successful source-native
  validation event and the mutation backlog before it;
- **rework:** repeated mutation and validation-followed mutation on the same
  artifact, reported as distributions;
- **continuity:** actions before a session's first mutation, overlap with the
  preceding session's artifacts/modules, and cross-session rework;
- **attention:** action allocation and transitions over artifact types and
  modules; and
- **configuration association:** observable process differences following
  explicit skill/harness/config events, without causal language.

“Durable verified progress” is the conjunction of observable durability,
reuse and validation association, not a weighted scalar. Complete distance and
survival curves are retained. No arbitrary fixed 24-event window enters the
research measurements.

## Source evidence and uncertainty

Every exported fact retains the project, session and source-call identifier.
The analysis distinguishes:

- `observed`: a native adapter exposes the action/effect/status;
- `unknown`: the source lacks enough evidence; and
- `not_applicable`: the fact is not meaningful for the action.

Unknown is never converted into `no_effect`, failed validation is never counted
as successful validation, and a successful validation is never described as
covering a specific mutation without independent evidence. File-level final
existence is not content survival. Content survival requires native diff,
snapshot or Git line evidence and is reported separately.

## Artifact classification

Artifact type is a deterministic, inspectable path/extension classification
with an `unknown` class: source, test, configuration, paper/documentation,
data/input, result/figure/log, and other. Repository top-level module is the
default structural unit; language-specific module mappings may be added only as
declared secondary analyses. Classification changes presentation and grouped
statistics, never the underlying action or artifact identity.

## RQ7 comparison boundary

Final workspace, Counts, official ProcGrep, bounded Raw-log LLM and the
artifact-linked trajectory receive the same declared source universe. ProcGrep
is the strongest action-only procedure baseline and should tie or win on
action-only facts. The proposed method can support a claim only for incremental
artifact-linked or cross-session facts at comparable factual accuracy and
reported cost. Every answer cites source IDs or abstains; the representation
under test cannot generate its own truth set.

## Presentation-only choices

Agent Nebula's path and directory attraction, collision, attention brightness,
point size, color interpolation, layout stability, GIF/MP4 compaction, legend
and commit flash are visualization choices. They cannot enter empirical metric
definitions. Action time remains authoritative in both paths, while media may
map actions uniformly to a requested playback duration without dropping layout
snapshots.

## Explicit non-goals

- no new event database, canonical evidence artifact or parallel IR;
- no generated semantic labels in the primary study;
- no claim that local observational correlations establish skill/harness
  causality;
- no claim that Git commits represent Agent work time; and
- no current intervention, human-usability or visualization-superiority RQ.
