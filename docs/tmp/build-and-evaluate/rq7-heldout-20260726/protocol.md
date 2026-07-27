# P1 Preregistration: Held-Out Questions and Full Edge-Ledger Conformance

Date frozen: 2026-07-26 (America/Vancouver)

This protocol is frozen before any new held-out question, expected answer,
projection output, or score is generated.  The experiment tests the P1
uncertainty registered in
`experiment-gap-audit-20260726/report.md`: whether the repaired projection
conforms on native records that were not used by the 72-file/120-question
repair corpus or its error taxonomy.

## Scientific role and hypothesis

- **Role:** decisive measurement-validity evidence for the paper's separate
  conformance result.
- **Hypothesis:** on a root-disjoint held-out corpus, the repaired projection
  exactly reconstructs semantic session order, attempted strict artifact
  edges, confirmed-effect edges, and edge-call status, and therefore answers
  all held-out artifact-linked and cross-session questions exactly.
- **Competing explanation:** the repair fits the original selected questions
  or misses additional path, workdir, status, source-stream, session-join, or
  artifact-generation cases.  Such a result may preserve 60/60 on the repair
  corpus while failing the full held-out ledger.
- **Evidence boundary:** a pass establishes conformance only to the declared
  native-record grammar.  It does not prove that native records contain every
  system-level file effect or that the six projects are a population sample.

## Frozen implementation and external control

The projection tree was clean at registration (`git diff --quiet --
agent-session agentvis` returned zero).  Unrelated concurrent changes under
`docs/paper/` and other experiment directories are outside this run.

| Item | Frozen value |
|---|---|
| Repository revision at registration | `73120b00ab92c0f24ff9bef883d90ccc9f513dba` |
| `rq7_measurement.py` SHA-256 | `e50adb5cb3882e8eca83295a80716f9db4a73290de7fe648aeef5d79ed1f9240` |
| independent v4 checker SHA-256 | `bf12c98ec60b97c9ce4997b892288f65c10ffa8a1572b855b8ca8f92113e61cc` |
| `agent-session/src/parser.rs` SHA-256 | `62cb20600b628dbe83c7f6c9b1556f5c899292963f202df984c4456695db798b` |
| `agentvis/src/repository.rs` SHA-256 | `313e8fbe92eb966e44522f1de3635b5c6e8a362f28b68dc1eca7d1bf8b69ce6c` |
| strict action fixture SHA-256 | `685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7` |
| `agentvis/Cargo.lock` SHA-256 | `c117357cf567baad5a8867f8def4d43a5f4733f1904d94a2c4cf662243553143` |
| ProcGrep revision | `2e8277003dacaa774b5ef61ba150ae03a4f06693` |
| ProcGrep `uv.lock` SHA-256 | `e13620baf50cf9fbd6372128f3a6a020ae36d16ebceae22cc8a853d9ab8d73c3` |
| Codex CLI | `0.145.0` |
| Held-out v4 runner SHA-256 | `6df7a7ee8bed4ce2a5b4320da9b10aac1f710976b7af88623d21bd002fd6c33e` |
| Held-out project manifest SHA-256 | `2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a` |

The semantic grammar is `native-root-conformance-v4`: Codex root precedence
is `session_id`, `parent_thread_id`, `thread_id`, then `id`; source streams
are provenance, not sessions; event workdir overrides the session cwd;
lexical inline `cd` affects later direct shell-file operands; static wrapped
patches are decoded; failed/observed calls remain attempted actions; only
`status=ok` creates a confirmed effect; confirmed rename transfers identity;
confirmed delete followed by create starts a new generation.

The public fixture gate must pass before corpus selection.  In addition to
the shared root/action/lifecycle controls and their three Rust tests, it
checks four v4-only controls directly against the independently implemented
primary and standalone checker: lexical inline `cd`, dynamic-cwd exclusion,
static wrapped patch, and a wrapped exec envelope followed by inline `cd`.
The source oracle is
`agentvis/research/rq7_source_oracle_check.py`; it imports neither production
Rust code nor projection output.

## Held-out corpus

The six cases and repository roots are fixed:

| Case | Repository root |
|---|---|
| agentsight | `/home/yunwei37/workspace/agentsight` |
| ActPlane | `/home/yunwei37/workspace/ActPlane` |
| bpf-developer-tutorial | `/home/yunwei37/workspace/bpf-developer-tutorial` |
| eunomia.dev | `/home/yunwei37/workspace/eunomia.dev` |
| bpf-benchmark | `/home/yunwei37/workspace/bpf-benchmark` |
| bpftime | `/home/yunwei37/workspace/gpu/bpftime` |

The sample is exactly **72 complete native files from 72 distinct semantic
roots: 12 roots per case**.  No case may be replaced, no sample may be
reduced, and no second seed may be tried.

Frozen selection parameters:

- seed: `20260726-heldout-v4-001`;
- absolute discovery cutoff:
  `1785107836380493543` ns since the Unix epoch;
- maximum individual file and serialized per-case bundle: 256 MiB;
- source stability interval after selection: 60 seconds;
- one source stream per `(vendor, semantic native root)`;
- within each case, rank eligible streams by
  `SHA256(seed || vendor || source_sha256)`, take them vendor-round-robin,
  and stop only at exactly 12 distinct roots;
- include every naturally represented vendor, but make no claim for a vendor
  absent from the selected corpus.

Eligibility uses only native metadata, cwd/worktree membership, file
size/hash, timestamps, Tool-call presence, and semantic-root identity.  It
does not inspect a candidate's derived artifact edges, anchors, question
answers, or projection output.

Every selected source must be disjoint by source SHA-256, corrected
`(vendor, semantic root)`, and `(vendor, semantic root, native call ID)` from
all three archived manifests below:

1. Step 0004 repair corpus, SHA-256
   `838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35`;
2. invalid Experiment 001, SHA-256
   `2a7148ee78d0a0fadb99c768cbf6bda9fea2dce6e1ce844a8ae953e0fea38767`;
3. the previously frozen but unexecuted Experiment 002, SHA-256
   `1d58ac89ceb074efdaea782a00e86cfbdb2f2a5d968a172623089d2d11a02d59`.

Each exclusion archive must exist and match its recorded source sizes and
hashes before its roots/calls are reconstructed with the v4 resolver.  Any
overlap, archive mismatch, unstable selected source, insufficient roots, or
workspace change invalidates this one run.  It is not repaired by replacing a
file or rerunning selection.

## Held-out question generation

Question generation occurs only after the 72 source bytes and six cutoff
workspace manifests are copied and hash-sealed.

The matrix contains **120 newly instantiated questions**: six cases times 20,
with five questions in each family A/B/C/D.  It reuses only the registered
four-family semantics, never an old question row, old P0--P4 anchor, old
witness, old expected answer, or paraphrased old instance.

- **A, action-only:** five exact counts/order predicates reconstructed from
  the newly selected native roots.
- **B, artifact-linked:** five facts about the newly ranked P0 identity:
  distinct attempted calls, reads, mutations, first action class, and
  distinct semantic sessions.
- **C, cross-session:** five facts newly derived over native-root session
  order: adjacent sharing, later revisit, P0 return after a gap, P0 ordinal
  span, and identities seen in at least two sessions.
- **D, final-state:** tracked/untracked/absent for the newly generated P0--P4
  at the sealed workspace cutoff.

P0--P4 are regenerated separately per case from the v4 oracle as the five
artifact generations with the most distinct attempted calls, with the frozen
HMAC path ID as tie-breaker.  Canonical answers are base-10 integers or one of
`read`, `mutate`, `tracked`, `untracked`, `absent`.  Question IDs, anchors,
witness hashes, expected answers, and source ledgers are generated entirely
from the new bytes.  Before projection is run, the public question release
omits expected answers.

## Full edge ledger

The edge ledger contains every strict file edge produced by every selected
native Tool call, including failed and observed calls.  One row contains:

`project, vendor, native_session_id, session_ordinal, source_stream_id,
source_tool_ordinal, call_id, event_ordinal, action_ordinal, artifact_id,
path, display_path, access, previous_path, status, confirmed_effect`.

The attempted-edge comparison key is the ordered tuple:

`(project, session_ordinal, native_session_id, source_stream_id, call_id,
source_tool_ordinal, event_ordinal, action_ordinal, path, display_path,
access, previous_path, artifact_id)`.

The confirmed-effect ledger is the attempted ledger restricted to
`status=ok`.  The edge-call status ledger is keyed by
`(session_ordinal, native_session_id, source_stream_id, call_id,
source_tool_ordinal, status)`.  Session order separately compares
`(native_session_id, session_ordinal)`.

For session order, attempted edges, confirmed-effect edges, and edge-call
statuses, report matched/missing/extra counts and precision, recall, and F1
overall, by project, and by represented vendor.  Preserve a row-level
`edge-diff.csv`; do not collapse duplicate edges before multiset scoring.

## Question scoring and comparison

Question scoring is exact and deterministic:

- `correct`: the method returns an answer whose canonical string equals the
  oracle;
- `wrong`: the method returns a different canonical string;
- `abstain`: the method does not establish an answer;
- no partial credit, normalization beyond canonical integer/string
  serialization, majority vote, or question exclusion.

Report A, B, C, and D separately, plus B+C.  The direct comparison with the
old `60/60` is denominator-matched but not pooled: old = 60 repair-corpus B+C
questions; new = 60 root-disjoint held-out B+C questions.  The old questions
do not enter the new score.

The conformance run itself makes **zero model calls**, exactly as the repaired
deterministic conformance replay did.  The prior bounded Raw reader
(`gpt-5.6-terra`, medium) was N/A and is outside P1.  After all deterministic
artifacts are sealed, an independent result audit is invoked in the same way
as the corrected-oracle audit: Codex CLI `0.145.0`,
`gpt-5.6-sol`, `xhigh`, approval `never`, read-only sandbox.  That model is an
auditor, not the oracle, and cannot change any score.

## Execution and one-attempt rule

1. Run the public shared root/action/lifecycle fixture gate and the four
   v4-only primary/checker controls.
2. Freeze the one 72-root corpus and generate the 120 private oracle rows.
3. Run the independent source checker over all questions, calls, and edges.
4. Seal source/spec/oracle/code hashes.
5. Run the real preflight on the frozen case with the smallest total source
   bytes (project name breaks a tie).  Preflight gates only that the sealed
   binary, real archived sources, projection, scorer, and output path execute
   to completion.  Its scientific conformance/B+C/D result is retained but
   does not gate the full run.
6. If the preflight mechanism completes without an infrastructure, corpus,
   oracle, or integrity failure, run all six cases once even when the
   preflight exposes a genuine method-level conformance failure.
7. Materialize per-question decisions, the complete source and projection
   ledgers, row-level diffs, aggregate metrics, and the independent result
   review.

Preflight and full outputs are append-only.  A failed or interrupted
**mechanism path** blocks the full run; a completed scientific negative does
not.  No semantic/code/question/corpus repair is allowed after any held-out
answer or projection result is opened; a required method repair makes the
result contradicted if the run is otherwise valid, or invalid/inconclusive if
the oracle/corpus/execution contract failed.

## Authoritative runner, commands, and paths

The only runner is
`docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py`
at the hash frozen above.  It binds v4, 6×12, the seed/cutoff/cap, all three
exclusion manifests and their hashes, the code/checker/fixture hashes,
`display_path` equality, the project inventory, and append-only attempt files.
It refuses a changed runner or projection source after the code seal.

From repository root, the unique command sequence is:

```bash
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py check-fixtures
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py freeze
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py build
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py preflight
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/scripts/heldout_v4.py full
```

Each command writes `<command>-attempt.json` before doing work and refuses an
existing attempt.  `freeze`, `build`, `preflight`, and `full` are therefore
single, append-only attempts.  The locked Rust build uses
`CARGO_TARGET_DIR=docs/tmp/build-and-evaluate/rq7-heldout-20260726/build/cargo-target`,
while the two fixture invocations use experiment-local Cargo target
directories.  The runner sets `PYTHONDONTWRITEBYTECODE=1` before local module
imports and sets Cargo offline mode for the fixture subprocesses, so generated
build products and Python caches remain inside the only authorized output
directory.

Authoritative paths:

- private source/oracle/workspace archive: `private/`;
- public freeze metadata: `raw/freeze/`;
- public fixture build products: `fixture/cargo-target/`;
- binary and code seal: `build/`;
- real mechanism preflight: `raw/preflight/` and `private/preflight/`;
- six-case outputs and ledgers: `raw/full/` and `private/full/`;
- human reports: `result.md` and `result-review.md`.

## Frozen decision rule

The tested hypothesis is **supported** only if all conditions hold:

1. exactly 72 sources/roots and 120 questions; all split overlaps are zero;
2. the independent checker matches all 120 answers, the complete edge ledger,
   and the complete call/status ledger;
3. session order, attempted-edge, confirmed-effect-edge, and edge-call-status
   precision = recall = F1 = 1.0 overall, for every project, and for every
   represented vendor;
4. held-out B+C = 60/60 correct, 0 wrong, 0 abstain;
5. held-out D = 30/30 correct, 0 wrong, 0 abstain.

A is reported but is not a pass gate because the repair history already
established a deliberate source-action/ProcGrep grammar boundary.  Any failed
condition 3--5 in a complete, valid run **contradicts** exact held-out
conformance.  A corpus/oracle/integrity failure makes the run **invalid** and
the hypothesis inconclusive.  Missing terminal workloads make it
**incomplete** and must not be interpreted as a prefix result.

## Paper decisions fixed before results

- **Pass:** add held-out B+C and exact full-edge-ledger evidence as independent
  support; retain the old 60/60 explicitly as repair-corpus regression
  evidence rather than merging the two.
- **Valid fail:** retain the repair-corpus limitation; identify the failing
  edge class and check whether the same mechanism can affect RQ1--RQ4 before
  using their projection-sensitive values.
- **Invalid/incomplete:** make no new conformance claim and retain the prior
  boundary.

This experiment does not edit `docs/paper/` or `docs/evaluation.md`, and it
performs no Git stage, commit, or push.
