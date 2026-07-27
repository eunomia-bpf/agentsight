# Execution log

Execution window: 2026-07-27, America/Vancouver  
Final verification time: 2026-07-27T01:09:29-07:00  
Repository commands: **no git commands were run**

## Inputs read

- binding `task-spec.md`, including its amendment;
- complete `docs/user-instruction.md` and `docs/idea-story.md`;
- complete `docs/evaluation.md` and `docs/background-related-work.md`;
- current `agentpprof` session/workspace/profile source;
- frozen Git annotation workspace, matched-organization rows/marks, and three
  raw CodeTrace archives;
- Step-0086 workspace trace; and
- R114 current scoped rows and retained run result.

## Capability inventory and review gate

1. Wrote `capability-inventory.md`.
2. Registered `experiment-plan.md`.
3. A fresh independent reviewer returned `REVISE`.
4. Repaired exact Terminus mapping/imputation accounting, added a direct
   489-path hierarchy oracle, registered exact commands, separated Step-0086
   and R114 claim granularity, and restricted “created” to successful retained
   `Add File` headers.
5. Fixed the reviewer's final executable finding by keying hierarchy
   transitions on exact evidence IDs.
6. The frozen-artifact test passed 489/489 with zero path mismatch.
7. The independent reviewer returned final `APPROVED`.

Review details are in `plan-review.md`.

## Experiment-local code

Added only inside this experiment directory:

- `replay_measures.py` — deterministic fixed-artifact adapter;
- `test_replay_measures.py` — seven unit/integration tests; and
- `verify_outputs.py` — fail-closed conservation/determinism/output checker.

No product code was changed.

## Tests

Command:

```bash
python3 -m unittest -v test_replay_measures.py
python3 -m py_compile replay_measures.py test_replay_measures.py verify_outputs.py
```

Result: 7/7 tests passed.

Covered:

- elapsed floor/minimum/terminal convention;
- terminal `C-c` normalization;
- exact patch target and disposition extraction;
- stable target evidence IDs;
- root-to-leaf ancestry;
- patch-target deduplication; and
- frozen Git 489/489 exact hierarchy expansion.

## Preparation

Command:

```bash
python3 replay_measures.py \
  --repo /home/yunwei37/workspace/agentsight-research-semantic-flamegraph \
  --out-dir /home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0090-20260727T023000-0700/experiment-001
```

Result: `prepared-measures.json` with status `prepared`.

Key fail-closed checks:

- exact Git session set;
- exact OpenHands model-response joins;
- exact Terminus normalized nonblank sequence after initial `clear`;
- 489/489 evidence-to-operation paths with zero mismatch;
- one LLM ancestor per Step-0086 projected tool;
- disjoint read/write source evidence;
- one R114 wrapper-tool ID per task; and
- exact R114 input/output mass.

## Real preflight

Preflight inputs:

- 119 Git OpenHands/Claude rows;
- one successful exact created-file row; and
- 39 R114 failure-task rows.

The initial one-session Git invocation failed closed because the unfiltered
three-session marks referenced absent sequences. A preflight-only mark
projection retained the selected session's unchanged 25 transitions and the
complete 66-name dictionary. The rerun passed. The full run used the original
mark file unchanged.

All three profiles reported `status=ok`, no warnings, exact mass, and loaded
with both:

```bash
go tool pprof -top -unit=minimum PROFILE
go tool pprof -traces -unit=minimum PROFILE
```

See `preflight-report.md` and `preflight.*`.

## Full profile production

Unchanged binary:

```text
/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/agentpprof/target/release/agentpprof
agentpprof 0.2.37
```

Commands used the exact stacks registered in `experiment-plan.md`:

- Git: `project,agent,operation,call,tool`, view `time`, original complete
  accepted marks;
- Step-0086: `agent,operation,llm_evidence,tool_evidence,effect,disposition,target`,
  views `files`, `files`, and `network`; and
- R114: `task,session,tool_evidence,effect,process,target`, view `operations`.

Every command used `--deterministic-output`. Producer stdout is retained as
`*.stdout.json`.

## Determinism

Each profile was produced a second time with the identical command and input.
`sha256sum` output is in `determinism.sha256`.

Result: all five primary/second pairs are byte-identical.

## Stock-pprof checks

For every primary profile:

```bash
go tool pprof -top -unit=minimum PROFILE
go tool pprof -traces -unit=minimum PROFILE
```

For Git focus:

```bash
go tool pprof -top -unit=minimum \
  -focus=operation:diagnose_authentication git-multibranch.time.pb.gz
go tool pprof -tags -unit=minimum \
  -focus=operation:diagnose_authentication git-multibranch.time.pb.gz
```

All reads succeeded. Text output is retained as `*.top.txt`,
`*.traces.txt`, and `git-multibranch.time.diagnose.*.txt`.

## Rendering

Renderer:

```text
docs/visexp/r221_visual_gallery.py
```

It read each standard profile through `go tool pprof -traces -unit=minimum`
and wrote R221-style SVG. ImageMagick converted the SVGs to PNG. The five PNGs
were copied into this directory and also retained under:

```text
docs/visexp/out/r221-pprof-renderer-v1/
```

Files:

- `git-multibranch.time.png`
- `selfprofile.file-read.png`
- `selfprofile.file-write.png`
- `selfprofile.network.png`
- `r114.system-effects.png`

Visual inspection confirmed nonempty, legible flamegraph structure for the Git
time and FILE-WRITE figures. `file` confirmed all five are valid 1320-pixel-wide
PNG images.

## Final fail-closed verification

Command:

```bash
python3 verify_outputs.py
```

Result: `profile-checks.json` status `pass`.

The checker independently verified:

- normalized-input, producer, stock-pprof, and renderer mass equality;
- zero conservation delta for all five profiles;
- byte determinism;
- local and external PNG existence;
- unchanged Git factual fields/evidence order;
- exact 489-path Git hierarchy;
- exactly two successful exact created-file targets;
- Step-0086 network status population `{ok: 55}`;
- all 1,520 R114 original fields/values preserved;
- R114 failure task has one false negative; and
- the expected `python3` failure effect is absent.

## Product-change and safety disposition

- Product additions: none.
- Rust source/build changes: none.
- Cargo tests: not applicable because no product code changed.
- Experiment adapter tests: 7/7 pass.
- New live capture: none.
- LLM annotation calls: none.
- Destructive commands: none.
- Git commands: none.

## Independent result review

A fresh reviewer independently recomputed the core paths, totals, shares,
created targets, network status, R114 preservation, stock loads, and digests.
Verdict: **VALID**.

The reviewer required the result table to mark a single
semantic-operation-to-kernel chain partially materialized/inconclusive and
required the general network-failure predicate to test for an actual failed
network row. Both corrections were applied. No measured output changed.

The post-review `py_compile` and seven-test suite passed. An initial
post-review replay invocation omitted the adapter's required explicit
`--repo`/`--out-dir` arguments and exited before writing outputs; the exact
registered command above was then rerun successfully. The final fail-closed
checker again returned `status=pass`, and all five primary/second profile
digests remained identical.
