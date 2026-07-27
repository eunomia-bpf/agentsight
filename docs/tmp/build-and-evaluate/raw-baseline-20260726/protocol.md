# P2 Protocol — Bounded Raw Reader Full Matrix

Status: **frozen before any new model preflight or matrix call**  
Freeze date: 2026-07-26 (America/Vancouver)  
Planned role: decisive baseline for the separate measurement-capability question

Plan-review amendment, still before any model preflight or matrix call:

- any non-`complete` full-matrix cell is an explicit veto on a superiority or
  parity verdict, forcing `mixed_or_inconclusive`;
- the model runner writes its answer-blind intermediate result below
  `attempt-1/`, and only an atomic, hash-tagged corrected-v4 checkpoint is
  resumable; an interrupted post-call gold join is completed from that
  intermediate file without another model call; and
- preflight has at most three numbered attempts. Attempts after the first
  require a recorded infrastructure-repair note and never overwrite an earlier
  attempt.

These changes close the two run-validity blockers in the independent initial
plan review without changing the corpus, model, prompt, budgets, matrix,
scoring definitions, or interpretation thresholds.

## Research question and hypothesis

This run repairs experiment-gap audit item P2/e: the prior Raw baseline produced
0/360 planned scoreable rows, so it supplied no Raw accuracy or cost result.

The tested hypothesis is:

> On the same exact-fact questions and source bytes, the repaired stable
> artifact/session representation supplies B/C facts that bounded, on-demand
> Raw reconstruction cannot recover with comparable exact coverage and cost.

A Raw match or win weakens or removes the representation-necessity claim. A
Raw loss supports only an incremental exact-fact capability claim for this
fixed reader, corpus, and question protocol; it does not establish general LLM
inferiority or representation novelty.

## Frozen assets

- Repository at registration:
  `0ff0dce0c43bab092a92efe13c90fc6767487f14`
  (tree `24c3a30769c6a68fc0255bd1829f516e7da27c24`).
- Source freeze: the existing six-project, 72-file private archive, 12 native
  files per project, 224 MiB on disk. Its audit manifest passed
  `sha256sum -c` immediately before registration.
- Freeze JSON SHA-256:
  `838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35`.
- Question semantics SHA-256:
  `484d1c9af3b07511d2c0892166110387642d889f88b80bfc6927a7dc324de83e`.
- Corrected v4 answer table SHA-256:
  `bea810e09cd3925707714145c9a50d8804e57e26d99b6b1c308e9ec778e7e254`.
  It contains the same 120 question IDs and text as the original Raw plan, with
  24 corrected expected answers.
- Repaired Trajectory result SHA-256:
  `dd89048d5ba080066be2598d7582c65736c005fad9a1fdaa9c0e1d17b0ea8eac`.
- Historical approved Raw runner SHA-256:
  `7d19551bcc223db0dfdbc51ccbd8b8970cd2d23e2ecfa2ea52ea81e4a7f81b88`.
- Runtime: Codex CLI `0.145.0`, Bubblewrap `0.9.0`, model
  `gpt-5.6-terra`, reasoning `medium`.

The source archive, corrected answers, and comparison results are read-only
inputs. Every new file, sandbox, checkpoint, log, score, and report is written
only below `docs/tmp/build-and-evaluate/raw-baseline-20260726/`.

## Bounded Raw reader

### Visible evidence

Each model call sees one project only:

1. the complete 12 selected Claude/Codex/Gemini native records for that project;
2. `source-index.json`, giving answer-free source IDs, vendors, sizes, and
   hashes;
3. `cutoff-manifest.json`, giving the five P0--P4 paths and their cutoff
   index/presence/content facts;
4. the frozen answer-free question semantics; and
5. the 20 project question IDs and texts.

It does **not** see expected answers, corrected-answer metadata, source-oracle
rows, normalized events, ProcGrep atoms, projected edges, trajectory indexes,
other projects, paper text, or prior model outputs.

### Isolation and budgets

- Bubblewrap exposes the evidence directory read-only at `/work`, a
  cell-specific writable result directory at `/out`, the Codex binary and
  authentication file, and the system files needed to execute the CLI and
  reach its model API.
- The repository, parent experiment directories, oracle files, user home, and
  other project evidence are absent from the model filesystem namespace.
- Codex runs ephemeral, ignores user config and repository rules, uses a
  read-only inner sandbox, disables apps/browser/image/multi-agent features,
  and must return the frozen JSON schema.
- Local retrieval is capped at 64 tool calls and 1,048,576 returned tool bytes.
- One call is capped at 900 seconds and 65,536 response bytes.
- Network/remote shell commands (`curl`, `wget`, `ssh`, `scp`, `rsync`, and Git
  fetch/clone/pull) remain denied. Model API transport is the sole intended
  network use.
- Original absolute paths may appear as inert strings in native evidence and in
  local search output. They are not treated as access attempts. Filesystem
  access is bounded by actual mount visibility; the monitor enforces resource
  caps and the remote-command deny-list, not path literals found in evidence.

Before the real model preflight, two controls must pass:

1. a command whose output contains an original absolute workspace path is not
   stopped merely because of that text; and
2. an actual read of the parent repository/oracle path from the same Bubblewrap
   namespace fails because the path is not mounted.

## Matrix

One call answers all 20 questions for one project and one repetition:

| Project | Native files | Source bytes | Repetitions | Raw rows |
|---|---:|---:|---:|---:|
| agentsight | 12 | 130,186,388 | 3 | 60 |
| ActPlane | 12 | 47,043,331 | 3 | 60 |
| bpf-developer-tutorial | 12 | 6,796,786 | 3 | 60 |
| eunomia.dev | 12 | 21,923,708 | 3 | 60 |
| agentskill-observability-paper | 12 | 6,602,732 | 3 | 60 |
| academic-writing-skills | 12 | 8,934,935 | 3 | 60 |
| **Total** | **72** | — | **18 calls** | **360** |

Every project contributes five A (action), five B (artifact-linked), five C
(cross-session), and five D (cutoff-state) questions per repetition. Calls may
run serially or with at most two concurrent cells. Scheduling does not change
the matrix or scoring.

## Preflight, failures, and recovery

- The smallest-source project is used for one real end-to-end preflight before
  the 18 registered matrix calls. It must make at least one local evidence read,
  remain within all caps, return exactly the 20 registered IDs, and write a
  parseable schema-valid response.
- Up to three preflight attempts are allowed only for demonstrated
  infrastructure defects. A completed schema-valid preflight is never rerun
  based on its answers. Any deviation is recorded.
- Full-matrix calls have no scientific retry and no majority vote. Timeout,
  malformed output, boundary violation, or transport failure is retained as a
  terminal cell and contributes 20 denominator abstentions.
- A completed `scored.json` is the cell checkpoint. Restarting the runner skips
  every existing terminal checkpoint and runs only missing cells; this is
  resumption, not a retry.
- Raw `response.json`, JSONL events, stderr, prompt, command, and scored rows are
  saved immediately per cell.

## Scoring

- Gold is joined only after the model call by question ID against
  `corrected_expected` in the frozen v4 answer table.
- `correct`: schema-valid `status=answer` and exact canonical string equality.
- `wrong`: schema-valid `status=answer` and unequal canonical string.
- `abstain`: explicit schema-valid abstention, plus protocol-mapped abstention
  for a terminal invalid cell.
- A **scoreable row** comes from a schema-valid 20-ID response; explicit
  abstentions remain scoreable. Rows synthesized from an invalid cell are
  denominator rows but are reported separately as unscoreable.
- Primary Raw score: exact correct coverage over all 360 registered rows.
- Claim-matched primary score: B+C exact correct coverage over 180 registered
  rows. Also report wrong, abstain, conditional exact accuracy, each 20-row
  cell, each family, project, and repetition.
- The three repetitions are not voted. Their rows remain separate; aggregate
  coverage is their arithmetic mean.
- Uncertainty follows the original protocol: 10,000 seeded hierarchical
  bootstrap draws, resampling six project blocks and then the three Raw
  repetitions within each sampled project. Intervals are fixed-corpus
  sensitivity, not population confidence intervals.
- The original symmetric B+C accuracy-parity gate is retained:
  Trajectory-minus-Raw is parity only if its full interval lies in
  `[-0.05, +0.05]`. A positive lower bound supports a fixed-reader Trajectory
  advantage; an interval spanning the decision boundaries is mixed or
  inconclusive.

## Matched baseline comparisons

All numerical comparisons use the corrected v4 oracle and identical question
IDs. The frozen comparison rows are:

| Method | All-family correct coverage | B+C correct coverage | Comparison role |
|---|---:|---:|---|
| Final State | 30/120 (0.250) | 0/60 (0.000) | state-only lower-information control |
| Counts | 3/120 (0.025) | 0/60 (0.000) | aggregate activity control |
| ProcGrep | 12/120 (0.100) | 0/60 (0.000) | official action-only baseline |
| repaired Trajectory | 102/120 (0.850) | 60/60 (1.000) | artifact/session representation under test |
| bounded Raw | pending | pending | on-demand same-source reconstruction |

The earlier State Diff, Session Local, and OCPM Features definitions came from
a superseded pathology-diagnosis protocol. That branch produced no compatible
120-question scores. They are therefore not numerically pooled here.
Comparability to any future run of those baselines requires the same 72 source
files, cutoff manifests, 120 IDs, corrected v4 answers, fixed reader/prompt and
repetitions, and the same terminal-failure denominator rule. Final State is the
available state-only exact-fact control, but it is not silently relabeled as
the richer historical State Diff condition.

Raw wall time, token use, source bytes, retrieval calls, and returned bytes are
reported. The old deterministic timing assigned one shared project-loop time to
four methods and was independently ruled non-comparable; therefore no
Raw/Trajectory speedup or cost ratio will be claimed unless a valid
method-specific Trajectory timing record is available. Accuracy comparison does
not depend on that timing.

## Frozen interpretation

- Raw matches the repaired Trajectory on B+C: remove any claim that the
  representation is necessary for these exact facts; report Raw's measured
  resource cost separately.
- Raw is materially lower with a positive Trajectory-minus-Raw lower interval:
  support only a fixed-reader, fixed-corpus incremental capability statement.
- Mixed projects, invalid cells, or an interval crossing the parity boundary:
  call the comparison mixed or inconclusive and retain the coverage/failure
  taxonomy.
- Regardless of outcome, this experiment adds one baseline result to the
  separate tool question. It does not change RQ1--RQ6, prove causal utility, or
  authorize edits to the paper.
