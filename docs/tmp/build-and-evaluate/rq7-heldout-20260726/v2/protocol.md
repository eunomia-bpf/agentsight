# P1-v2 Preregistration: Held-Out Questions and Full Edge-Ledger Conformance

Date frozen: 2026-07-26 (America/Vancouver)

This v2 protocol is frozen before any v2 held-out corpus, question, expected
answer, projection output, or score is generated.  The experiment tests the P1
uncertainty registered in
`experiment-gap-audit-20260726/report.md`: whether the repaired projection
conforms on native records that were not used by the 72-file/120-question
repair corpus or its error taxonomy.

## Sole revision, rationale, and authorization

This protocol inherits every scientific, semantic, independence, oracle,
ledger, metric, execution-order, one-attempt, and paper-decision provision
from v1 except the corpus quota rule and the question denominators mechanically
derived from that quota.

The v1 unique freeze was declared invalid after its fixed 6×12 contract found
only 10 eligible semantic sessions in one required case.  No v1 held-out
question, expected answer, private oracle, production projection, edge ledger,
or score was generated or observed.  After that invalid verdict and before any
result was observed, the orchestrator explicitly authorized this sole
revision: project \(i\) contributes
\(s_i=\min(12,e_i)\), where \(e_i\) is the number of all eligible semantic
roots under the unchanged v1 discovery, cutoff, exclusions, ranking, worktree,
vendor-round-robin, and byte-cap rules.  If any \(e_i<8\), freeze reports the
count truthfully and stops.  The seed is not changed and no project,
replacement source, or second attempt is permitted.  Because v1 produced no
oracle or projection result, this feasibility-driven re-preregistration is
scientifically clean rather than an outcome-conditioned retry.

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
| upstream independent v4 checker SHA-256 | `bf12c98ec60b97c9ce4997b892288f65c10ffa8a1572b855b8ca8f92113e61cc` |
| v2 proportional-ID checker SHA-256 | `8942a0f8c22681adb9fac993a611747c4d8e59de7aa64d227f3fee661743c234` |
| `agent-session/src/parser.rs` SHA-256 | `62cb20600b628dbe83c7f6c9b1556f5c899292963f202df984c4456695db798b` |
| `agentvis/src/repository.rs` SHA-256 | `313e8fbe92eb966e44522f1de3635b5c6e8a362f28b68dc1eca7d1bf8b69ce6c` |
| strict action fixture SHA-256 | `685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7` |
| `agentvis/Cargo.lock` SHA-256 | `c117357cf567baad5a8867f8def4d43a5f4733f1904d94a2c4cf662243553143` |
| ProcGrep revision | `2e8277003dacaa774b5ef61ba150ae03a4f06693` |
| ProcGrep `uv.lock` SHA-256 | `e13620baf50cf9fbd6372128f3a6a020ae36d16ebceae22cc8a853d9ab8d73c3` |
| Codex CLI | `0.145.0` |
| Held-out v2 runner SHA-256 | `b40eab3e6fd16a51d0edacbfff3f3c421ca9e0795dbc91865ae50115206e7c19` |
| Held-out project manifest SHA-256 | `2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a` |
| Reused v1 fixture attempt SHA-256 | `83879d59a4f2e7c2d85ed929df5d5ca8b734e2b7cb96644a610c0a2f20fab5d4` |
| Reused v1 fixture runner SHA-256 | `6df7a7ee8bed4ce2a5b4320da9b10aac1f710976b7af88623d21bd002fd6c33e` |

The semantic grammar is `native-root-conformance-v4`: Codex root precedence
is `session_id`, `parent_thread_id`, `thread_id`, then `id`; source streams
are provenance, not sessions; event workdir overrides the session cwd;
lexical inline `cd` affects later direct shell-file operands; static wrapped
patches are decoded; failed/observed calls remain attempted actions; only
`status=ok` creates a confirmed effect; confirmed rename transfers identity;
confirmed delete followed by create starts a new generation.

The working-tree copy of `rq7_measurement.py` advanced after v1 registration
for a non-conformance plotting-label change and no longer has the frozen hash.
V2 neither accepts that drift nor modifies/restores the working tree.  The
runner read-only loads
`73120b00ab92c0f24ff9bef883d90ccc9f513dba:agentvis/research/rq7_measurement.py`
from the local Git object database, verifies the registered
`e50adb5cb3882e8eca83295a80716f9db4a73290de7fe648aeef5d79ed1f9240`
SHA-256, and executes that exact v1 bytestring with its original
repository-relative `__file__`.  The production parser, repository projection,
fixture, checker provenance, and Cargo lock still match their v1 hashes.
Reading a frozen blob is not a Git write and does not change the registered
scientific contract.

The already completed v1 public fixture gate is reused before v2 corpus
selection because the semantic grammar, production/checker code hashes, strict
fixture hash, and all fixture expectations are unchanged.  Its attempt and
runner hashes are revalidated by the v2 freeze.  In addition to the shared
root/action/lifecycle controls and their three Rust tests, it checked four
v4-only controls directly against the independently implemented primary and
standalone checker: lexical inline `cd`, dynamic-cwd exclusion, static wrapped
patch, and a wrapped exec envelope followed by inline `cd`.  The source oracle is
the hash-frozen
`v2/scripts/rq7_source_oracle_check_v2.py`; it imports neither production Rust
code nor projection output.  It is byte-for-byte the upstream v4 checker
except for documentation and the mechanically necessary proportional-ID
adapter: it still reconstructs all 20 templates per project and the complete
edge/call ledgers, but requires the frozen \(Q\) IDs to be a subset of that
template universe, rejects duplicate IDs or a count different from the frozen
\(Q\), scores/hashes exactly those \(Q\), and reports both \(Q\) and the
120-template recomputation count.  The runner independently requires those
reported counts and the checker hash before freeze can complete.

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

For project \(i\), let \(e_i\) be the complete eligible-root count after the
unchanged v1 rules below and let \(s_i=\min(12,e_i)\).  The sample contains
exactly \(S=\sum_{i=1}^{6}s_i\) complete native files from \(S\) distinct
semantic roots.  Every \(e_i\) must be at least 8; otherwise the run reports the
count and stops before question/oracle generation.  No case may be replaced,
no selected quota may be manually reduced or filled from another project, and
no second seed may be tried.

Frozen selection parameters:

- seed: `20260726-heldout-v4-001`;
- absolute discovery cutoff:
  `1785107836380493543` ns since the Unix epoch;
- maximum individual file and serialized per-case bundle: 256 MiB;
- source stability interval after selection: 60 seconds;
- one source stream per `(vendor, semantic native root)`;
- within each case, rank eligible streams by
  `SHA256(seed || vendor || source_sha256)`, enumerate them
  vendor-round-robin under the unchanged per-case serialized byte cap, record
  the resulting \(e_i\), and take the first \(s_i=\min(12,e_i)\) distinct
  roots;
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

Question generation occurs only after the \(S\) source bytes and six cutoff
workspace manifests are copied and hash-sealed.

The v1 density was 30 questions per family over 72 roots.  The v2 integer
formula is frozen as follows:

\[
F=\left\lfloor\frac{30S}{72}+0.5\right\rfloor,\qquad Q=4F.
\]

Thus each family A/B/C/D contains exactly \(F\) questions and B+C contains
exactly \(2F\).  For integer allocation, project \(i\)'s ideal per-family quota
is \(F s_i/S\).  Assign every project its floor, then assign the remaining
per-family questions in descending fractional-remainder order (Hamilton
largest remainders); the fixed project-manifest order breaks equal remainders.
If project \(i\) receives \(f_i\), instantiate the first \(f_i\) templates in
the unchanged frozen order within every family: A1...A5, B1...B5, C1...C5,
and D1...D5.  This allocation depends only on selected-root counts, never on
answers, anchors, edges, projection output, or scores.

The matrix therefore contains exactly **\(Q=4F\) newly instantiated
questions**.  It reuses only the registered four-family semantics, never an
old question row, old P0--P4 anchor, old witness, old expected answer, or
paraphrased old instance.

- **A, action-only:** up to five exact counts/order predicates reconstructed from
  the newly selected native roots.
- **B, artifact-linked:** up to five facts about the newly ranked P0 identity:
  distinct attempted calls, reads, mutations, first action class, and
  distinct semantic sessions.
- **C, cross-session:** up to five facts newly derived over native-root session
  order: adjacent sharing, later revisit, P0 return after a gap, P0 ordinal
  span, and identities seen in at least two sessions.
- **D, final-state:** up to five tracked/untracked/absent facts for the
  correspondingly ranked P0--P4 at the sealed workspace cutoff.

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

Report A, B, C, and D separately, plus B+C.  The old result remains 60/60
repair-corpus B+C questions; the new result is \(2F\) root-disjoint held-out
B+C questions.  Report exact numerators and denominators separately without
pooling, rescaling, or treating unequal denominators as matched.  The old
questions do not enter the new score.

The conformance run itself makes **zero model calls**, exactly as the repaired
deterministic conformance replay did.  The prior bounded Raw reader
(`gpt-5.6-terra`, medium) was N/A and is outside P1.  After all deterministic
artifacts are sealed, an independent result audit is invoked in the same way
as the corrected-oracle audit: Codex CLI `0.145.0`,
`gpt-5.6-sol`, `xhigh`, approval `never`, read-only sandbox.  That model is an
auditor, not the oracle, and cannot change any score.

## Execution and one-attempt rule

1. Revalidate and reuse the completed v1 public shared
   root/action/lifecycle fixture gate and four v4-only primary/checker
   controls; do not rerun or change them.
2. Freeze the one v2 corpus using \(s_i=\min(12,e_i)\); stop if any
   \(e_i<8\).  Compute \(S\), \(F\), \(Q=4F\), and generate exactly \(Q\)
   private oracle rows.
3. Run the independent source checker over all \(Q\) questions, calls, and
   edges.
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

At freeze completion, `private/audit-manifest.sha256` lists and hashes every
frozen source, workspace blob, question/spec/oracle file, and freeze record.
Build validates that list against the unique completed freeze attempt and
stores its hash in `build/code-seal.json`; preflight and full revalidate every
listed freeze-stage file read-only while ignoring only their later
append-only output directories.

## Authoritative runner, commands, and paths

The only runner is
`docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/scripts/heldout_v4.py`
at the hash frozen above.  It binds v4, the six fixed cases, the authorized
12-root cap/8-root floor, the seed/cutoff/cap, all three exclusion manifests
and their hashes, the code/checker/fixture hashes, `display_path` equality,
the project inventory, the frozen question formula, and append-only attempt
files.  It refuses a changed runner or projection source after the code seal.

From repository root, the unique command sequence is:

```bash
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/scripts/heldout_v4.py freeze
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/scripts/heldout_v4.py build
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/scripts/heldout_v4.py preflight
python3 docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/scripts/heldout_v4.py full
```

Each command writes `<command>-attempt.json` before doing work and refuses an
existing attempt.  `freeze`, `build`, `preflight`, and `full` are therefore
single, append-only attempts and must run in exactly that order.  The locked
Rust build uses
`CARGO_TARGET_DIR=docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2/build/cargo-target`.
The freeze only validates the already completed v1 fixture attempt; build
reruns the unchanged shared action fixture as v1 did and places its build
products under v2 `build/fixture-cargo-target/`.  The runner sets
`PYTHONDONTWRITEBYTECODE=1` before local module imports and sets Cargo offline
mode for fixture subprocesses, so generated build products and Python caches
remain inside the authorized v2 output directory.

Authoritative paths:

- private source/oracle/workspace archive: `private/`;
- public freeze metadata: `raw/freeze/`;
- reused public fixture evidence: `../check-fixtures-attempt.json` and
  `../fixture/cargo-target/`;
- build-time shared-fixture products: `build/fixture-cargo-target/`;
- binary and code seal: `build/`;
- real mechanism preflight: `raw/preflight/` and `private/preflight/`;
- six-case outputs and ledgers: `raw/full/` and `private/full/`;
- human reports: `result.md` and `result-review.md`.

## Frozen decision rule

The tested hypothesis is **supported** only if all conditions hold:

1. every \(e_i\ge8\), every selected count is exactly
   \(s_i=\min(12,e_i)\), totals are exactly \(S\) sources/roots and
   \(Q=4F\) questions under the frozen formula, and all split overlaps are
   zero;
2. the independent checker matches all \(Q\) answers, the complete edge
   ledger, and the complete call/status ledger;
3. session order, attempted-edge, confirmed-effect-edge, and edge-call-status
   precision = recall = F1 = 1.0 overall, for every project, and for every
   represented vendor;
4. held-out B+C = \(2F/2F\) correct, 0 wrong, 0 abstain;
5. held-out D = \(F/F\) correct, 0 wrong, 0 abstain.

A is reported but is not a pass gate because the repair history already
established a deliberate source-action/ProcGrep grammar boundary.  Any failed
condition 3--5 in a complete, valid run **contradicts** exact held-out
conformance.  A corpus/oracle/integrity failure makes the run **invalid** and
the hypothesis inconclusive.  Missing terminal workloads make it
**incomplete** and must not be interpreted as a prefix result.

## Paper decisions fixed before results

- **Pass:** add the held-out \(2F/2F\) B+C and exact full-edge-ledger evidence
  as independent support; retain the old 60/60 explicitly as repair-corpus
  regression evidence rather than merging or rescaling the two.
- **Valid fail:** retain the repair-corpus limitation; identify the failing
  edge class and check whether the same mechanism can affect RQ1--RQ4 before
  using their projection-sensitive values.
- **Invalid/incomplete:** make no new conformance claim and retain the prior
  boundary.

This experiment does not edit `docs/paper/` or `docs/evaluation.md`, and it
performs no Git stage, commit, or push.
