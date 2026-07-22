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
e_i = [(worktree_id, artifact_path, access, previous_path, scope)]
```

where `source_id` is the native call identifier when present, otherwise the
stable session and ordinal identifier. Sort by `(timestamp, source_id)`.
Failed calls remain actions but emit no successful file effect.

The projection performs one pass over sorted actions:

1. resolve Tool-level workdir before session cwd, normalize every
   source-qualified path relative to a known repository worktree, retain a
   hashed worktree ID, and discard paths outside the repository;
2. retain source-native read, write, create, rename and delete effects;
3. preserve explicit rename lineage; a later create at a deleted path is a new
   artifact unless the source says otherwise;
4. retain directory-scope references as weak scope effects rather than
   pretending every descendant was read;
5. retain adapter-derived command effect and status so the recognized
   test/check/build command families and their coverage can be observed; and
6. derive final path existence and tracked state from the current workspace and
   Git without moving the action-time axis onto commits; a missing or
   unqueryable worktree yields unknown final state, never inferred absence.

If inputs are ordered, projection time is `O(|A| + |E|)` plus repository-state
lookups; otherwise sorting costs `O(|A| log |A|)`. Artifact maps require
`O(|F|)` live state and exported rows require `O(|A| + |E|)` space.

## Measurement derivations

The core projection contains no progress score, pathology label or intent
inference. RQ analyses derive transparent measurements:

- **introduced-artifact persistence:** final tracked/existing state for
  identities born from a confirmed-success create in the same worktree;
  rename inherits source birth state and existing-file write content durability
  remains unknown; identities with unknown final worktree state are excluded;
- **reuse:** the next later access to the same artifact lineage and its event,
  time and session distance;
- **validation association:** adapter-recognized successful validation before
  the same artifact's next mutation/delete, with supersession as a competing
  outcome and arbitrary later validation reported only as global association;
- **repeated-mutation structure:** first/repeat-observed mutation episodes,
  per-identity load, exact concentration and action-atomic prefix evolution;
- **source-session continuity:** mutation-observed prefix composition,
  artifact/module overlap and first-mutation state between adjacent
  non-overlapping concurrency components; overlapping sessions are not forced
  into an invented serial order;
- **workspace activity allocation and migration:** path-resolved action/call
  allocation, same-artifact/same-module/cross-module transitions and return
  gaps in native action order, without interpreting them as duration or latent
  attention; and
- **skill/instruction source coverage:** exact visible Skill Tool and
  instruction-file signals. Association analysis is admitted only when positive
  and negative exposure can both be established; the current corpus cannot.

The three-way progress conjunction is restricted to eligible
observation-born introduction episodes; it is not a weighted scalar. Complete
distance and competing-risk curves are retained. No arbitrary fixed 24-event
window enters the research measurements.

## Source evidence and uncertainty

Every exported fact retains the project, session and source-call identifier.
Activity reports both all admitted actions and the subset whose Tool-level
workdir/session cwd resolves to a retained worktree; only the latter is used for
workspace activity--progress comparison.
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

## RQ7 comparison boundary and readiness gate

Final workspace, Counts, official ProcGrep, bounded Raw-log LLM and the
artifact-linked trajectory receive the same declared source universe. ProcGrep
is the strongest action-only procedure baseline and should tie or win on
action-only facts. The proposed method can support a claim only for incremental
artifact-linked or cross-session facts at comparable factual accuracy and
reported cost. Every answer cites source IDs or abstains; the representation
under test cannot generate its own truth set.

Before any question or performance value is produced, the matched run requires
immutable admitted native prefixes, a per-worktree cutoff revision manifest,
an untracked-state disposition, executable pinned baseline interfaces and a
separate source-explicit oracle specification. The current RQ1 freeze has the
normalized action spine but not those contracts. F10 therefore reports only
benchmark readiness with explicit N/A cells and `MATCHED COMPARISON STOPPED`;
it closes only the readiness question and is not evidence for trajectory
superiority.  The separate capability comparison remains future work.

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
