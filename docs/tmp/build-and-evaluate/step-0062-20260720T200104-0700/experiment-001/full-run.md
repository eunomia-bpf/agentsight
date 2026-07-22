# Full Run — Source-Native Task Stack to Standard pprof

## Final Run Identity

- completed: 2026-07-21T08:55:29Z
- input: complete byte-prefix census of `~/.codex/sessions`
- discovered Codex JSONL files: 6,357
- input bytes: 46,469,655,787
- eligible root families: 1,769
- included sessions with scored operations: 4,839
- candidate/reference operations: 1,265,888 / 1,265,888
- product artifact: one standard deterministic pprof, with no custom frontend

Every file size was recorded before parsing because the active Codex session
can continue appending. Candidate and reference read only complete JSONL
records inside that ordinary byte prefix. This is input consistency for a live
log directory, not a Git/hash/freeze protocol.

## Repairs Since The First Rejected Run

The first full run was retained only as failure history. It mishandled copied
parent history in forked child files and recognized only one of Codex's exact
spawn-to-child encodings. The rerun keeps the same task-state algorithm and
adds two source-format repairs:

1. a child/fork starts owning records at the first native `task_started`
   whose numeric `started_at`, or legacy UUIDv7 `turn_id` time, reaches the
   canonical first `session_meta` timestamp; and
2. a `spawn_agent` call may bind its child through either the function result
   or the exact native `sub_agent_activity(event_id, agent_thread_id)` record,
   always requiring agreement with the child's declared parent session.

Completion counts now use unique state transitions. Remaining exceptions are
reported against a raw pre-construction denominator rather than disappearing
through candidate eligibility.

## Pre-Construction Coverage

- eligible source sessions: 4,886
- ownership-resolved sessions: 4,885
- ownership boundary missing: 1
- source-owned operations before task-path construction: 1,267,006
- scored operations: 1,265,888
- operation coverage: **0.9991176048**
- unscored source-owned operations: 1,118
- unresolved parent-session links: 44
- unresolved operations after replay: 5
- plan updates with multiple simultaneous `in_progress` items: 246
- parse-error records in the included population: 43 across 32 sessions

The remaining records are listed with source coordinates in the ignored raw
`exceptions.json`. No task text, child ID, parent link, or active plan item is
guessed to improve coverage.

## Source-Fidelity Result

Within the 99.9118% source-owned operation subset for which the native task
ancestry is observable:

- operation-level exact complete-path accuracy: **1,265,888 / 1,265,888 =
  1.000000**;
- task-transition precision/recall/F1: **1.000000 / 1.000000 / 1.000000** over
  27,824 source transitions;
- event weight: exactly conserved at 1,265,888; and
- token weight: exactly conserved at 73,999,344,068.

The 1.0 value is source-replay fidelity on the covered subset. It is not a
claim that source-declared plans are an ideal human decomposition, nor that the
lower phase/action/object/result suffix is semantically correct.

## Naturally Variable Task Depth

| Visible task depth | Operations | Fraction |
|---:|---:|---:|
| 1 | 390,781 | 30.870% |
| 2 | 743,595 | 58.741% |
| 3 | 99,330 | 7.847% |
| 4 | 32,182 | 2.542% |

The constructor has no depth limit. The population contains 10,234 concrete
root-task occurrences, 10,690 plan frames, 3,071 uniquely linked delegation
frames, and 176,145 operations (13.915%) on paths containing a delegation.
Ordinary model/tool/file/process events never create persistent task frames.

## Standard pprof Product Artifact

The representative family was fixed before profile construction as the
eligible root family with the most explicit task-control transitions,
lexicographic tie-break:

- root session: `019f25fa-3bfc-7a02-a147-8b4dcff94f41`
- task-control transitions: 1,100
- operations: 38,330
- unique folded stacks: 27,479
- pprof bytes: 1,118,275
- deterministic pprof SHA-256: `ca2e704a215d3fe07c3dd613baa3cb707324dc43d1a9dbadc44261b420bc859`

The emitted path is:

```text
task -> nested task* -> phase -> action -> object -> result
```

Repeated `task` field values become an uneven number of standard pprof stack
frames. Agent, model, session, tool type, command, path, and status are not
promoted into the task prefix. The only committed product artifact is:

- [`task-centric-source-native.pb.gz`](../../../../visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz)

It decodes with stock Go tooling:

```bash
go tool pprof -top \
  docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz

go tool pprof -top -focus=run_subagent_review \
  docs/visexp/out/source-native-task-stack-v1/task-centric-source-native.pb.gz
```

The second query narrows the same profile to 379 operations under matching
review responsibilities. One exact three-frame path inside that result is:

```text
verify idea novelty and collect papers
└── run subagent review, fix issues, commit and push
    └── review AgentCap top-conference claim evidence
```

That delegated path owns 95 operations. Existing pprof focus, ignore, top,
tree, list, and web commands provide the browsing surface; AgentPProf adds no
renderer or frontend.

## User-Value Reading

This result fixes the largest product-level error in the old view: the primary
hierarchy now follows concrete user work, active plan responsibilities, and
delegated subtasks instead of `agent -> session -> prompt -> tool -> path`.
The profile can therefore answer where a declared task spent operations, which
subtasks dominated it, where delegation occurred, and which branches contain
repeated calls, failures, or no source-visible conclusion.

Two boundaries remain explicit. First, deictic turns such as `继续` are
preserved rather than silently canonicalized to an earlier task. Second, the
lower suffix still contains generic results for many tool operations. Those
are evidence-quality limitations for a later mechanism, not reasons to replace
the source-native task stack or add a custom visualization layer.

## Hypothesis Verdict

**Supported for observable source-native task control, with 99.9118%
operation coverage.** The complete real population demonstrates deterministic,
variable-depth task-stack construction, exact replay fidelity on covered
operations, strict additive conservation, and standard-pprof usability.

This is supporting RQ3 evidence, not the complete answer to task/action tag
accuracy across agents with no explicit task controls. It does not change the
paper thesis, the four RQs, or the intended larger task-semantic story.
