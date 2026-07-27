# Experiment plan: deterministic multi-measure replay

Plan date: 2026-07-27  
Gate: RQ1 supporting demonstration  
Execution mode: deterministic replay; no LLM calls; no new live capture

## Scientific question

Can a fixed AgentProf semantic hierarchy retain its operation boundaries and
source evidence while its additive width changes from count/tokens to elapsed
time, file-read targets, file-write targets, and network targets? Where a
system recording exists, can the retained lineage expose system effects below
a responsible task/tool path without overclaiming fields that were not
persisted?

This supports resource attribution only. It does not change the fixed thesis
“Agent observability needs profiling, not only debugging.” It does not test
tag accuracy, debugging success, or user utility.

## Registered artifacts

1. **Git hierarchy and evidence**
   - fixed rows:
     `.agentsight/experiments/rq1-matched-organization-v1/full/operations-count.jsonl`
   - fixed hierarchy:
     `.agentsight/experiments/rq1-matched-organization-v1/full/accepted-operation-marks.json`
   - raw timing:
     the two OpenHands and one Terminus2 `git-multibranch` archives under
     `.agentsight/experiments/codetracebench-rq2/hub/bench_artifacts/full/`
2. **Local-session effects**
   - fixed Step-0086 trace:
     `docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/workspace/trace.jsonl`
3. **System effects**
   - fixed R114 rows:
     `.agentsight/experiments/rq1-r114-current-profile-v1/full/profile/scoped-lineage-operations.jsonl`
   - fixed per-task wrapper IDs:
     `.agentsight/experiments/rq1-r114-current-profile-v1/full/r114/live-record-r114.json`

No annotation, boundary, operation name, or source-evidence membership may be
generated or changed.

## Measures and deterministic rules

### A. Frozen Git elapsed-time width

For each of the same 489 fixed evidence rows:

- OpenHands start is the ISO timestamp of the agent action whose model response
  ID equals the row's `call` suffix.
- Terminus2 start is the asciinema input timestamp whose command equals the
  fixed `commands.txt` source line. Literal `C-c` maps to byte `0x03`; the
  one blank command has no input event and receives the next retained input
  timestamp. After excluding the initial recorded `clear`, the normalized
  nonblank `commands.txt` sequence must equal the complete asciinema input
  sequence exactly and in occurrence order.
- value is `max(1, floor(next_start - start))` seconds.
- the final operation in each session has value one second, matching the
  current local-session time-view terminal convention.

The one blank-command timestamp and three terminal one-second samples are
reported as imputations. The run also reports the number and mass of intervals
raised by the one-second minimum, raw observed inter-start gap mass, floored
gap mass, and the final defined integer measure. The resulting profile is a
product-compatible elapsed attribution convention, not exact observed wall
duration.

The accepted sparse operation marks and stack
`project,agent,operation,call,tool` are replayed unchanged.

Registered checks:

- exactly 489 rows and 489 unchanged evidence IDs;
- same ordered factual fields as the fixed count input, with only `value`
  changed;
- independently expand the accepted sparse marks and compare all 489 ordered
  evidence-ID -> full variable-depth operation paths with the frozen workspace
  tool paths, with zero missing paths or mismatches;
- every value positive;
- exact input/profile/stock-pprof conservation;
- byte-identical deterministic profile over two productions;
- exact cumulative focus on `operation:diagnose_authentication`.

The resulting unit is elapsed wall-clock seconds between source operation
starts, not active CPU seconds and not isolated tool execution time.

### B. Step-0086 source-effect widths

Each tool node retains its existing semantic `path`. Parent pointers supply
the recorded LLM evidence node; tool ID/call ID supplies the tool evidence.

- **FILE-READ:** one value per retained read target reference.
- **FILE-WRITE:** one value per retained write target reference.
  For `apply_patch`, `Add File`, `Update File`, `Delete File`, and `Move to`
  headers replace coarse path groups with exact repo-relative targets and an
  explicit disposition. Other tools retain their source path groups.
- **NETWORK:** one value per retained domain on a network-classified tool; a
  missing domain would become `unknown`.

Stack:
`agent,operation,llm_evidence,tool_evidence,effect,disposition,target`.
Repeated `operation` values preserve the accepted variable-depth path.

Registered checks:

- row count equals independently recomputed target-reference mass;
- every output row maps to one existing tool node and parent LLM node;
- read and write evidence-ID sets are disjoint;
- exact patch-created targets appear below their actual `apply_patch` node;
- all network status counts are reported, including whether any failure exists;
- exact input/profile/stock-pprof conservation;
- byte-identical deterministic profile over two productions.

These are source-adapter effects, not eBPF effects.

### C. R114 system-effect chain

Each of the 1,520 retained rows keeps its existing task/category, effect,
process, target, and value. The adapter joins `session == task_id` to the
single recorded `agent_tool_ids[0]` for that R114 task.

Stack:
`task,session,tool_evidence,effect,process,target`.

Registered checks:

- one and only one wrapper-tool ID exists for all 20 tasks;
- all 1,520 rows join;
- all existing factual fields and values are unchanged;
- exact input/profile/stock-pprof conservation;
- separate counts for file-write, process-exec, process-exit, file-read, and
  network;
- no exact-file or network-failure claim if the corresponding rows are absent.

This chain is complete only at task responsibility -> outer wrapper tool ->
retained system-effect granularity. The task/category frames are known
run-level responsibilities, not automatically inferred semantic tags. The
wrapper-tool ID is retained lineage evidence; inner LLM call IDs were not
persisted. It is not combined rhetorically with the separate Step-0086
source-adapter chain.

## Worked examples

1. Select one successful Step-0086 `apply_patch` `Add File` row and report its
   full operation -> LLM -> tool -> created-file leaf, with its exact filename.
   Only a retained `Add File` header with tool status `ok` counts as created;
   Update/Delete/Move remain distinct, and truncated/unseen targets are not
   inferred.
2. Select R114 `r114-failure-retry` and report its task -> wrapper tool ->
   retained process/file effect leaves. Compare those leaves with the task's
   known failure instruction and explicitly state whether the missing
   `python3` failure is present in the persisted profile rows.
3. Report network failure correlation only if a failed network row exists.
   The inventory predicts none; the full run must verify, not assume, this.

## Preflight

Before the full run:

1. map the 119-operation OpenHands/Claude Git session to 119 timestamps and
   produce a time profile using the fixed marks;
2. project the first exact Step-0086 `Add File` target through its parent LLM;
3. join all retained R114 rows for `r114-failure-retry` to exactly one wrapper
   tool ID;
4. load each preflight profile with stock `go tool pprof`.

Preflight fails on any missing/duplicate Git mapping, changed accepted path,
missing parent LLM, unmatched R114 task, nonpositive value, or conservation
delta.

## Full-run outputs

Profiles in this experiment directory:

- `git-multibranch.time.pb.gz`
- `selfprofile.file-read.pb.gz`
- `selfprofile.file-write.pb.gz`
- `selfprofile.network.pb.gz`
- `r114.system-effects.pb.gz`

R221-style PNGs are rendered both here and, for the new measure widths, under
`docs/visexp/out/r221-pprof-renderer-v1/`.

The Git `diagnose authentication` table will retain the already-validated
count/token reference values and add elapsed-time total, focused mass, and
share. File/network shares are not assigned to the Git hierarchy because no
Git effect recording exists.

## Exact runnable path

Let `REPO` be the repository root and `EXP` this experiment directory. Execute
from `EXP`:

```bash
python3 -m unittest -v test_replay_measures.py
python3 replay_measures.py --repo "$REPO" --out-dir "$EXP"
```

Use the unchanged binary
`$REPO/agentpprof/target/release/agentpprof`:

```bash
"$REPO/agentpprof/target/release/agentpprof" \
  --operation-file "$EXP/git-multibranch.time.jsonl" --view time \
  --stack project,agent,operation,call,tool \
  --operation-mark-file "$REPO/.agentsight/experiments/rq1-matched-organization-v1/full/accepted-operation-marks.json" \
  --deterministic-output -o "$EXP/git-multibranch.time.pb.gz"

"$REPO/agentpprof/target/release/agentpprof" \
  --operation-file "$EXP/selfprofile.file-read.jsonl" --view files \
  --stack agent,operation,llm_evidence,tool_evidence,effect,disposition,target \
  --deterministic-output -o "$EXP/selfprofile.file-read.pb.gz"

"$REPO/agentpprof/target/release/agentpprof" \
  --operation-file "$EXP/selfprofile.file-write.jsonl" --view files \
  --stack agent,operation,llm_evidence,tool_evidence,effect,disposition,target \
  --deterministic-output -o "$EXP/selfprofile.file-write.pb.gz"

"$REPO/agentpprof/target/release/agentpprof" \
  --operation-file "$EXP/selfprofile.network.jsonl" --view network \
  --stack agent,operation,llm_evidence,tool_evidence,effect,disposition,target \
  --deterministic-output -o "$EXP/selfprofile.network.pb.gz"

"$REPO/agentpprof/target/release/agentpprof" \
  --operation-file "$EXP/r114.system-effects.jsonl" --view operations \
  --stack task,session,tool_evidence,effect,process,target \
  --deterministic-output -o "$EXP/r114.system-effects.pb.gz"
```

For every profile, record:

```bash
go tool pprof -top -unit=minimum PROFILE
go tool pprof -traces -unit=minimum PROFILE
```

Raw/check artifacts are the five normalized JSONL files,
`prepared-measures.json`, producer stdout records, stock-pprof top/trace
records, `profile-checks.json`, and `determinism.sha256`.

Render SVG and PNG with:

```bash
python3 "$REPO/docs/visexp/r221_visual_gallery.py" \
  --profile PROFILE --out OUTPUT.svg --title TITLE
convert -background white OUTPUT.svg OUTPUT.png
```

External PNG names under
`docs/visexp/out/r221-pprof-renderer-v1/` are exactly:

- `git-multibranch.time.png`
- `selfprofile.file-read.png`
- `selfprofile.file-write.png`
- `selfprofile.network.png`
- `r114.system-effects.png`

Copies with the same names are retained in `EXP`.

Completion requires: all unit/preflight checks pass; all registered row,
evidence, path, join, conservation, stock-load, and double-production
determinism checks have zero delta; every PNG exists and is nonempty; and the
result report records each unavailable correlation instead of substituting a
proxy.

## Admission and claim boundary

Admit as a valid supporting demonstration only if all registered conservation,
stock-pprof, evidence-identity, path-preservation, and deterministic-output
checks pass.

Do not claim:

- CPU time from elapsed intervals;
- eBPF effects from Step-0086 session metadata;
- Git file/network effects from command text;
- network-failure correlation without a failed network effect;
- exact R114 filenames from coarse target groups; or
- individual R114 LLM/tool calls beyond the retained wrapper-tool ID.

## Product and test scope

No product code change is planned. The experiment-local replay adapter will
have unit tests for time rounding/terminal handling, Terminus2 control-key
normalization, patch-target extraction, repeated operation fields, and R114
join cardinality. `cargo test` is not required because no Rust source changes;
the current release binary will be used unchanged.
