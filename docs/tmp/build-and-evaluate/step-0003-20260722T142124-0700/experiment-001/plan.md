# Experiment Plan: RQ7 Measurement Capability

## Research Question

- **RQ exactly as written in the paper:** Given the same frozen native evidence
  and an independent source-explicit oracle, which action-only,
  artifact-linked, cross-session, and final-state facts can Final State,
  Counts, ProcGrep, bounded Raw-log model analysis, and artifact-linked
  trajectories answer correctly, and at what evidence and inference cost?
- **Specific uncertainty tested here:** whether stable artifact identity and
  cross-session lineage add correct source-verifiable fact coverage beyond the
  official action-only procedure spine, rather than merely repackaging action
  counts, and whether a bounded model reading raw native records can recover the
  same facts at comparable correctness and cost.
- **Why the answer matters:** the empirical study is useful only if another
  Agent can recover its process facts from evidence. A readiness matrix or a
  by-design reconstruction does not establish that capability.

## Paper-Value Admission

- **Planned role:** decisive.
- **Largest credible paper story this experiment could unlock:** a persistent
  workspace trajectory contributes an independently measurable artifact and
  cross-session fact layer beyond an established action-only procedure
  representation, while preserving exact action facts and source links.
- **Strongest reject argument addressed:** the proposed method is either a
  deterministic restatement of Counts/ProcGrep, or any capable model can derive
  the same information directly from raw logs, making the extra representation
  unnecessary.
- **Independent evidence beyond existing runs:** Step 0002 measured six
  projects but never froze native source prefixes, built an independent oracle,
  ran ProcGrep, or called a model. This experiment prospectively freezes those
  contracts before generating questions.
- **Why not tautological or already settled:** the proposed method does not
  define the oracle; every accepted answer has a frozen native-record witness
  or cutoff filesystem/Git witness. ProcGrep is expected to tie on action-only
  facts. The artifact-linked method may fail through parser omissions,
  unresolved paths, lineage errors, or incorrect abstention.
- **Paper decision if positive:** retain a narrow incremental factual-coverage
  claim for artifact-linked and cross-session facts, plus an efficiency claim
  over Raw-log model analysis only if correctness is comparable.
- **Paper decision if contradictory, mixed, or inconclusive:** drop superiority;
  report an efficiency-only tie, a family-specific boundary, or no tool claim.
  The six-project descriptive findings remain independent.
- **Best alternative experiment:** another observational correlation over the
  six projects. It has lower decision value because RQ1--RQ6 already provide
  descriptive evidence while the tool claim has no executed comparison.

## Expected And Alternative Outcomes

- **Current expected answer:** Counts and ProcGrep tie on their eligible
  action-only questions; Final State ties on final-state questions;
  artifact-linked trajectories cover artifact and cross-session questions that
  standard ProcGrep atoms cannot express; Raw-log model analysis has lower or
  more variable exact accuracy and materially higher inference cost.
- **Strongest competing explanation:** path and lineage questions are made easy
  by oracle-aware question construction, or Raw-log model analysis matches the
  deterministic method once given a fair source bundle.
- **Contradictory result:** no incremental correct coverage over ProcGrep,
  trajectory errors on its claimed fact families, or Raw-log model parity at
  comparable cost.

## Published Precedent And Real Assets

- **Closest protocol:** ProcGrep's published episodic-search comparison of
  deterministic structural queries and LLM readers over the same trajectory
  questions.
- **Official assets:** `hamidahoderinwale/procgrep` commit
  `2e8277003dacaa774b5ef61ba150ae03a4f06693`; real local Claude, Codex, and
  Gemini native session files; six real repositories; Git and filesystem state
  at one prospective cutoff; Codex CLI `0.145.0`, model `gpt-5.6-sol`, and
  `model_reasoning_effort="medium"`. These values are fixed before preflight and
  never selected from its answers.
- **Reused:** official ProcGrep adapters and canonical atoms, its structural
  pattern/query semantics, exact-match episodic-search metrics, and native
  session loaders.
- **Necessary thin glue:** freeze closed session files and workspace state;
  construct source-witnessed questions; join the shared action spine to
  `agent-session` artifact effects; create bounded raw-record bundles; score and
  plot results. No new production IR, server, database, semantic labeler, or
  human annotation is added.

## Comparison

- **Proposed method:** the official ProcGrep action spine plus deterministic
  `agent-session` artifact effects, stable worktree/path identity, rename
  lineage, source-session identity, and frozen final-state linkage.
- **Main baseline — official ProcGrep:** represents the strongest action-only
  procedural account. A matched run is necessary because the claim is
  incremental factual coverage on these exact multi-project native records.
- **Main baseline — bounded Raw-log model:** represents the competing position
  that a model can reconstruct the same facts without a precomputed artifact
  relation layer. A matched run is necessary because published ProcGrep results
  do not cover artifact identity or cross-session questions.
- **Controls:** Final State and aggregate Counts are lower-information controls,
  not main baselines. They test the beliefs that the final workspace or activity
  telemetry is sufficient.
- **If a baseline matches or wins:** ProcGrep parity outside action-only facts
  removes the incremental representation claim; Raw-log parity retains at most
  an efficiency claim if deterministic cost is lower; a Raw-log win removes
  both accuracy and general capability claims.
- **Fairness:** every condition uses the same selected closed sessions and
  cutoff workspace manifest. Counts and the proposed method reuse ProcGrep's
  exact canonical action spine, isolating only artifact relations. Raw-log
  model prompts contain native records and the relevant cutoff-state slice,
  never trajectory answers, and use one fixed input/output/reasoning budget.
  Public result rows hash session and path identifiers.
- **Leakage rule:** no candidate enters the benchmark from normalized rows. The fixed source-only
  grammar below enumerates every question from immutable native bytes before
  any method runs. No ProcGrep output, `agent-session` output, model answer, RQ1
  aggregate, or plot may define truth, selection, or eligibility.

## Frozen Measurement Contract

### Source universe and deterministic selection

For each of the six named projects, the freeze discovers native Claude, Codex,
and Gemini session files whose last byte and mtime are unchanged across two
reads 60 seconds apart and whose mtime is at least ten minutes before the
freeze. A source-only metadata pass admits a file when native JSON/JSONL parsing
finds its session ID, at least one native tool invocation, and a cwd/workdir
identifying one Git worktree for that project. The worktree with the most admitted files is
selected per project; ties use the SHA-256 of its canonical path. This keeps
session evidence and cutoff state in one actual workspace rather than silently
mixing worktrees.

Within that worktree, files are ordered by
`SHA256("20260722" || vendor || file_sha256)`. A round-robin over
`claude,codex,gemini` takes the next complete file from each available vendor
and stops at 12 files. At least six files and
every vendor available for that project must be represented; otherwise the
entire freeze stops before questions or method outputs exist. No file is
truncated and no action, path, answer, or method output affects selection.
After selection, every official vendor loader must return a non-empty trace;
failure stops the freeze but never triggers replacement by another file.

The copied files, not their mutable originals, are the evidence universe. The
copy preserves the vendor-relative path under `private/frozen-home/`; each file
has a source ID, byte length, mtime, and SHA-256. The source-prefix cutoff is
the maximum native timestamp in these bytes. Only after source selection, the
selected worktree is frozen at a later declared workspace cutoff by recording
HEAD, index entries, porcelain-v2 status, untracked paths, and SHA-256/content
copies or explicit absence markers for the five final-state paths. Revision and
status are read before and after the copy; any difference rejects and repeats
the project freeze. Thus `source_cutoff <= workspace_cutoff` is explicit.

### Source-only facts and artifact semantics

Two independent direct-source paths implement the same frozen semantics. The
primary Python enumerator reads native JSON/JSONL bytes and emits witness rows.
The checker is a separate `jq`/POSIX-shell implementation that does not import
the enumerator, ProcGrep, `agent-session`, or the proposed query code; it
reopens every source file, recomputes the fixed templates, and checks every
witness and answer. They may share only the written semantics, project list,
SHA-256 routine, and path-pseudonym salt. A disagreement makes the whole
project freeze invalid before methods run; it is never replaced after results
are visible.

Native records are ordered by `(native_timestamp, source_file_sha256,
record_index, call_index)`; missing timestamps are ordered at their record
position, never synthesized. Session order uses the first native timestamp and
file SHA-256 as tie-breaker. Session identity is the native session ID plus
source-file hash. Tool invocations, including failed or result-less calls, are
attempted actions; status is not used to select questions. Multi-path calls add
one call--artifact edge per distinct path but count once in a question about
one artifact.

Artifact paths come only from structured path keys, `apply_patch` file headers,
or path operands of the frozen shell-command set
`cat,sed,head,tail,nl,less,more,touch,rm,mv,cp`. Event workdir overrides session
cwd. Relative paths are lexically resolved inside the selected worktree;
absolute paths outside it, unresolved variables/globs, symlink dereferencing,
search scopes, and ambiguous shell syntax are excluded. `.` and `..` are
normalized lexically. An artifact is `(worktree, normalized_relative_path)`;
an explicit `mv old new` keeps one identity, while delete followed by create
starts a new generation. No content-similarity rename is inferred. Reads are
structured Read/NotebookRead or frozen shell readers; mutations are
Edit/Write/NotebookEdit/`apply_patch`/`touch`/`rm`/`mv`/`cp`.

### Fixed question grammar

There is no sampled candidate pool, Boolean balancing, substitution, or
method-specific eligibility. Each project contributes the same 20 templates:

- **Action-only A1--A5:** total `read_file`, `edit`, and `run_test` atoms; number
  of selected sessions matching `read_file (?:[a-z_]+ )*edit `; and number
  matching `edit (?:[a-z_]+ )*run_test `. The source oracle independently
  applies the pinned adapter mapping. ProcGrep runs its official loader and
  adapter for each vendor, counts exact `Trace.atoms`, and invokes
  `match_patterns` with those two literal regexes.
- **Artifact-linked B1--B5:** for anchor P0, attempted call count, read count,
  mutation count, first action class, and distinct-session count. P0 is the
  source-enumerated artifact with maximum attempted-call count, ties broken by
  HMAC-SHA256 of its normalized path.
- **Cross-session C1--C5:** number of adjacent session pairs sharing any
  artifact; number of sessions after the first revisiting any prior artifact;
  P0 return episodes after one or more intervening sessions without P0; P0's
  first-to-last session ordinal gap; and number of artifacts referenced in at
  least two sessions.
- **Final-state D1--D5:** `{tracked, untracked, absent}` at the workspace cutoff
  for P0--P4, the five highest-call source artifacts with the same HMAC tie
  break. Final status never affects their selection.

The freeze succeeds only if all six projects yield P0--P4 and therefore exactly
30 questions per family. IDs are `project-family-template`; duplicates are
impossible by grammar. Every oracle row carries its canonical scalar/category,
all immutable source call/line locators or workspace-manifest witness, and the
two checker hashes. This produces deterministic source gold without human or
model annotation.

### Method interfaces and mechanism engagement

- **Official ProcGrep:** Claude uses `load_claude_transcript` and
  `claude_code_adapter`; Codex parses every JSONL dict and uses
  `load_codex_session` and `codex_adapter`; Gemini parses its JSON object or
  JSONL list and uses `load_gemini_session` and `gemini_cli_adapter`. A1--A3
  count official atoms and A4--A5 use official `Pattern`/`match_patterns`.
  B/C/D are explicit out-of-scope abstentions; no path extractor is added.
- **Counts:** receives only the project-wide official atom histogram. It can
  answer A1--A3 and abstains when order, artifact, session, or state is needed.
- **Final State:** receives only the frozen Git/filesystem manifest and answers
  D1--D5; all process questions are abstentions.
- **Artifact trajectory:** the existing `agent-session` parser runs only over
  `private/frozen-home`. Its artifact effects join to source calls by native
  call ID, falling back only to the unique tuple `(session, record index, call
  index)`. ProcGrep is run first and its atom arrays are retained unmodified as
  this arm's action spine. Before relations are added, every per-session atom
  array must be byte-for-byte equal to the pinned ProcGrep array; every admitted
  artifact edge must join one frozen call. Any mismatch invalidates the arm,
  not the baseline. B/C use only joined artifact/session relations; D uses their
  joined IDs against the frozen manifest.
- **Bounded Raw-log model:** one invocation answers all 20 questions for one
  project from a read-only retrieval directory containing every complete
  selected native file, the five queried normalized paths, the cutoff manifest
  slice, and the question specification, but no oracle answer/witness,
  normalized row, ProcGrep atom, or proposed index. The model receives only a
  short instruction naming these files; it uses ordinary `rg`, `jq`, `sed`, or
  Python one-liners over the raw bytes rather than a project-authored index.
  Before the questions, the prompt includes the same frozen, answer-free
  measurement semantics used by the oracle and deterministic methods: the
  exact Claude/Codex/Gemini mapping for `read_file`, `edit`, and `run_test`;
  record/call and session ordering including tie breaks; attempted-action and
  multi-path rules; worktree/path normalization, shell-command set, explicit
  rename, delete--recreate, and exclusion rules; P0--P4 selection; all A1--D5
  template definitions; and canonical answer formats. The project-specific
  questions then state the actual P0--P4 normalized paths. This definition
  prefix is frozen once as `question-spec.md`; its SHA-256 is embedded in every
  Raw prompt and every deterministic result row. It contains no answer,
  witness, normalized event, atom sequence, or method output. A mismatch of the
  prompt/spec hash invalidates the cell. The remaining fixed instruction is:
  “Using only the complete native records and cutoff manifest below, answer
  every listed factual question. Use only local read-only retrieval tools in
  this directory; do not use outside files, network, or outside knowledge.
  Return the required JSON; use `abstain` when the bytes do not establish an
  exact answer, and cite source ID plus native locator.” The JSON
  schema fixes 20 rows of `{id,status,answer,evidence}`. CLI/model/reasoning are
  fixed above; `--ignore-user-config --ignore-rules --ephemeral`, read-only
  sandbox, and disabled browser/apps enforce the retrieval boundary.
  One call, 15-minute wall timeout, 64-KiB final-response ceiling, and no retry
  are allowed per project/repetition. Timeout, tool/returned-byte cap, outside
  access, schema/ID failure, or oversized output makes all 20 rows for that repetition abstentions and is
  retained. Three fresh invocations per project are never majority-voted.
  The wrapper's literal child command is
  `timeout --signal=TERM --kill-after=30s 900s codex exec --ignore-user-config --ignore-rules --strict-config --ephemeral --skip-git-repo-check --sandbox read-only --cd <project-raw-sandbox> --model gpt-5.6-sol --config 'model_reasoning_effort="medium"' --disable apps --disable browser_use --disable browser_use_external --disable image_generation --disable multi_agent_v2 --output-schema <frozen-schema.json> --json --output-last-message <response.json> -`.
  The wrapper terminates and marks the whole call abstain on tool call 65, more
  than 1 MiB cumulative tool-result bytes, access outside the sandbox, timeout,
  or schema failure. CLI JSONL records tool calls/results and exact input,
  cached-input, output, and reasoning-token counters; neither cached tokens nor
  reasoning tokens are treated as free.

## Workloads And Metrics

- **Workloads and common denominator:** the six fixed projects and exactly 120
  oracle-eligible questions above. Every method is scored on the same 30
  questions per family; an unsupported interface is an abstention, never a
  method-specific exclusion.
- **Primary metric:** exact correct factual coverage (`correct / 30`) per family,
  following ProcGrep's exact structural-query precedent. Canonical integers,
  categories, and ordered lists are compared after whitespace-only JSON
  normalization. Conditional exact accuracy (`correct / answered`), wrong, and
  abstain rates are secondary and always reported separately.
- **Primary contrasts:** (1) trajectory minus official ProcGrep paired correct
  coverage over B+C, with exact action preservation as a veto; (2) trajectory
  minus Raw mean correct coverage over B+C; and (3), only when accuracy is
  equivalent under the symmetric rule below, Raw divided by trajectory total
  wall time for all 20 questions.
  Final State and Counts remain interpretive controls.
- **Raw estimand and uncertainty:** a project's Raw score is the arithmetic mean
  of its three independent 20-question calls; the corpus score is the mean of
  six project scores. Ten-thousand seeded hierarchical bootstrap draws resample
  projects and then whole model repetitions within project, never individual
  answers from one call. Deterministic contrasts use project-block bootstrap.
  Intervals describe sensitivity within this frozen corpus, not a population.
- **Cost:** report source bytes made available, tool-result bytes returned to
  the model, rendered instruction bytes and tokens, output bytes and tokens,
  model/tool calls, wall time, and peak RSS. For
  deterministic methods report index construction and query time separately,
  plus total amortized at 1, 10, and 20 questions. Cached work is zero in the
  primary run. No unmeasured source-scan-efficiency claim is made for retrieval;
  source bytes available and bytes returned to the model are reported separately.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| freeze | dependency | six projects | native closed-session and cutoff-state manifests | 1 | Must pass before questions exist |
| oracle | correctness control | 120 fact candidates | direct source-witness checker | 2 independent implementations/checks | Invalidates any unreproduced item |
| counts | control | eligible questions | aggregate canonical counts | 1 | Tests activity telemetry sufficiency |
| final state | control | eligible questions | cutoff filesystem/Git manifest | 1 | Tests final-state sufficiency |
| action procedure | main baseline | eligible questions | official ProcGrep pinned commit | 1 | Strongest action-only comparison |
| raw reader | main baseline | six project bundles | frozen Codex model over raw records/state slice | 3 | Tests on-demand reconstruction and variance |
| artifact trajectory | proposed | eligible questions | shared action spine plus artifact/session/final-state relations | 1 | Tests incremental factual coverage |

## Execution

- **Authoritative entrypoints:**
  `agentvis/research/rq7_measurement.py` exposes `freeze`, `preflight`, `full`,
  and `score`; `agentvis/research/rq7_oracle_check.sh` is the independent
  source checker. They are research-only thin glue and do not alter product CLI
  behavior. The official checkout is `/tmp/procgrep-eval-2e827` at the pinned
  commit. Environment creation is
  `uv sync --project /tmp/procgrep-eval-2e827 --frozen --extra viz`; its
  `uv.lock` SHA-256 is
  `e13620baf50cf9fbd6372128f3a6a020ae36d16ebceae22cc8a853d9ab8d73c3`.
  The AgentSight revision, `agentvis/Cargo.lock` hash, Python version, CLI
  version, and all command lines enter the freeze manifest.
- **Literal freeze command:**
  `uv run --project /tmp/procgrep-eval-2e827 python agentvis/research/rq7_measurement.py freeze --projects-file docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw/projects.json --private docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/private --release docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/raw --procgrep /tmp/procgrep-eval-2e827 --seed 20260722 --sessions 12 --raw-bytes 0`.
- **Real preflight command:**
  `timeout --signal=TERM --kill-after=30s 2700s uv run --project /tmp/procgrep-eval-2e827 python agentvis/research/rq7_measurement.py preflight --private docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/private --release docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/preflight`.
  It runs the smallest real three-vendor path: one frozen Claude, Codex, and
  Gemini session through each official loader/adapter and `agent-session`, one
  real question from each family, all five methods, the independent source
  checker, and one actual bounded model call. If no selected project supplies a
  vendor, the freeze stops rather than silently reducing coverage.
- **Full and score commands:**
  `timeout --signal=TERM --kill-after=30s 21600s uv run --project /tmp/procgrep-eval-2e827 python agentvis/research/rq7_measurement.py full --private docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/private --release docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/raw --model gpt-5.6-sol --reasoning medium --repetitions 3`, followed by
  `uv run --project /tmp/procgrep-eval-2e827 python agentvis/research/rq7_measurement.py score --private docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/private --release docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/raw --figure docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/figures/rq7-measurement-capability.pdf`.
- **Full completion rule:** 30 independently witnessed eligible questions in
  each family; every deterministic method reaches terminal answer/abstain;
  all 18 project-by-repetition model calls terminate under the fixed budget;
  three-vendor engagement and action-spine identity pass; raw outputs and cost
  rows reconcile; the independent result review passes. A timeout or failed
  cell is retained with terminal status and never silently substituted.
- **Raw-result path:** `docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/`.
  `private/` is the access-controlled ignored audit bundle: immutable native
  archives, plaintext questions/paths, oracle witnesses, exact prompts, every
  model JSONL/response, deterministic outputs, and costs, covered by one sorted
  SHA-256 manifest. Committed `raw/` contains pseudonymous per-question IDs,
  template/form, expected and method answers after path-HMAC replacement,
  correct/wrong/abstain, cost, and witness hashes, plus frozen revisions and
  source hashes; it contains no native text, path, prompt, secret, or model
  rationale. This is sufficient for aggregate recomputation while the result
  reviewer on this machine can audit the private bundle.
- **Recovery:** each project/repetition model response is an independent
  checkpoint; completed cells are never rerun unless the fixed plan, oracle, or
  budget changes, in which case every affected comparison is rerun.
- **Upper-bound budget:** 18 model calls, at most 64 retrieval tool calls and
  1 MiB returned tool-result bytes per call, 64 KiB final output per call, 15 minutes per call, and six
  hours for the full command. Freeze/preflight failures do not consume the full
  matrix. Exit 0 means every planned cell is terminal; exit 2 means a retained
  partial/failed cell; any other nonzero status is an invalid run requiring a
  bounded repair and rerun of affected cells.

## Interpretation

- **Positive versus ProcGrep:** the 95% project-block bootstrap lower bound of
  trajectory-minus-ProcGrep B+C correct coverage is greater than zero, and all
  30 A answers are correct and byte-equal in both arms. Any action mismatch is
  an isolation veto, not a small tolerated regression.
- **Trajectory correctness veto:** because ProcGrep abstains on B+C, a sparse
  or broadly wrong trajectory arm cannot win merely by answering. A positive
  artifact/cross-session claim additionally requires B+C correct coverage at
  least `0.80` (48/60), conditional exact accuracy at least `0.95`, wrong-answer
  rate at most `0.05` (3/60), and no project's B+C conditional accuracy below
  `0.80`. Failure makes the ProcGrep contrast mixed/negative regardless of its
  bootstrap sign. These finite-corpus thresholds are fixed before preflight.
- **Trajectory versus Raw:** let `delta = trajectory - mean(Raw repetitions)`
  on B+C. Accuracy superiority requires the hierarchical-bootstrap 95% lower
  bound `> 0`; non-inferior/comparable accuracy requires the lower bound
  `>= -0.05`; Raw wins only when the upper bound `< -0.05`; otherwise the
  comparison is mixed/inconclusive. Raw parity requires the whole interval to
  lie within `[-0.05,+0.05]`.
- **Efficiency:** only when the entire 95% interval for
  `trajectory - mean(Raw repetitions)` lies inside the symmetric parity region
  `[-0.05,+0.05]`, claim lower cost when the 95% project-block lower bound of
  `log(Raw_total_wall / trajectory_build_plus_20_queries_wall)` is greater than
  zero. One-sided trajectory non-inferiority alone is insufficient. If the
  trajectory is accuracy-superior rather than equivalent, report accuracy and
  cost separately instead of relabeling the result as a parity-conditioned
  efficiency win. Tokens, bytes, and 1/10/20-query amortization remain descriptive.
- **Negative or mixed:** no positive ProcGrep contrast removes incremental
  coverage; an action veto invalidates isolation; a Raw win removes accuracy
  and efficiency superiority; parity permits only the predeclared cost test.
  Source/model execution failure is never promoted to a method win.
- **Target figure/table:** one four-family correct/incorrect/abstain matrix with
  a separate log-scale cost panel; readiness remains a prerequisite annotation,
  not a performance bar.

## Reproducibility Notes

- Freeze exact ProcGrep commit, Python environment, AgentSight commit, Codex CLI
  version/model/reasoning configuration, project revisions, worktree status,
  native file hashes, and random seed `20260722`.
- The fixed templates are instantiated once from the copied native bytes after
  the source freeze and before any method output. Question IDs and expected
  answers are content-hashed; plaintext paths stay in the private bundle.
- The six local author-associated projects limit external validity. This
  experiment supports a capability claim on the frozen corpus, not population
  rates or skill/harness causality.

## Recorded REAL PREFLIGHT Repair

Preflight attempt 1 stopped during source selection before question generation,
method output, or model execution. Four projects could not fit even their six
smallest complete sessions under the reviewed 160-KiB static-input ceiling
(for example, the six smallest summed to 382--471 KiB in three projects). The
repair above replaces static serialization with the reviewer's originally
preferred read-only raw retrieval path. It preserves complete same-source
membership, model/reasoning, one-call-per-project unit, question grammar,
oracle, baselines, repetitions, metrics, and decision rules; only the Raw input
transport and its corresponding cost counters change. This is a bounded broken
data-path repair under REAL PREFLIGHT, not tuning from answers: no questions or
method/model results existed when the repair was made.
