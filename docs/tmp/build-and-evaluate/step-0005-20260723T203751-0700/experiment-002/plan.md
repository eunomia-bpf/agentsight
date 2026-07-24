# Experiment 002 Plan: Native-Root-Conformant Held-Out Validation

## Why Experiment 001 Is Invalid

Experiment 001 is discarded, not interpreted as a positive or negative
result. Its selector and two Python oracles preferred a Codex child stream
`payload.id` over `payload.session_id`. Production correctly joined that
stream to its root session, but the scorer silently discarded the resulting
unexpected root. The same semantic root also appeared in the development
corpus, so the advertised held-out split was not root-disjoint.

No score, edge count, or question result from Experiment 001 will enter the
paper. This experiment uses a new specification, seed, source selection, and
freeze. Every semantic root and source hash exposed by Experiment 001 is
excluded in addition to the Step 0004 development corpus. The permanent
disposition is recorded in `../experiment-001/INVALIDATED.md`.

## Research Question

Can a precision-first projection over existing `agent-session` fields
reconstruct the exact ordered, artifact-linked actions needed by the paper's
cross-session measurements on unseen native Agent records?

This is a measurement-validity question. It does not claim semantic intent
recovery, automatic supervision, or population-level generality.

## Frozen Contract

Specification: `native-root-conformance-v3`.

- A semantic session is `(vendor, native root ID)`.
- A source stream is provenance and is never counted as another session.
- Codex native root precedence is:
  `session_id → parent_thread_id → thread_id → id`.
- Calls are attempted actions even when their Tool result fails.
- Only `status=ok` actions mutate lifecycle state or establish confirmed
  reuse.
- Exact file edges come only from declared structured path fields, patch
  headers, and a finite direct shell-file grammar.
- Session order uses first included native Tool timestamp, then semantic root
  ID.
- Event order uses timestamp, stable source stream ID, source Tool ordinal,
  and source record/call position.
- Rename transfers identity only for a confirmed, explicit, same-worktree
  rename. Confirmed delete followed by confirmed create starts a generation.

The selector/primary oracle, standalone checker, and production parser each
implement the root resolver separately. One public hand-authored fixture
covers legacy roots, new roots, legacy subagents, new subagents, and the
`thread_id` fallback.

## Split And Workloads

The six fixed projects are listed in `heldout-projects.json`. They span
software implementation, documentation/tutorial work, and an auto-research
workspace:

- AgentSight
- ActPlane
- bpf-developer-tutorial
- eunomia.dev
- bpf-benchmark
- bpftime

The selector admits exactly six source files from six distinct semantic roots
per project, for 36 globally distinct roots total. If any project cannot meet
this contract, the experiment terminates; no project is replaced, sample size
reduced, or seed retried. Eligibility was checked before selection using only
native metadata, cwd, file size/hash, and corrected root identity; no action
oracle or answer was opened. `kernel-script-paper` had zero unexposed eligible
roots and was therefore rejected before preregistration. `semantic-flamegraph`
was also rejected because it is an AgentSight Git worktree rather than an
independent repository. The fixed sixth project is bpftime. No further
alternative was screened after this list was frozen.

`heldout-projects.json` SHA-256 is
`2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a`;
the runner rejects any other project inventory.

The new split must be disjoint from both:

1. Step 0004 development sources; and
2. every source opened in invalid Experiment 001.

Disjointness is checked over source SHA-256, corrected semantic native root,
and native root/call tuple. Old freeze manifests are re-read from their
archived source files with the v3 resolver instead of trusting their stored
v2 root IDs.

The authoritative exclusion manifests are exactly:

- Step 0004:
  `../../step-0004-20260723T181008-0700/experiment-001/private/freeze.json`,
  SHA-256
  `838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35`;
- invalid Experiment 001:
  `../experiment-001/private/freeze.json`, SHA-256
  `2a7148ee78d0a0fadb99c768cbf6bda9fea2dce6e1ce844a8ae953e0fea38767`.

Experiment 001's current and four invalidated freezes contain the identical
48-source SHA inventory; the inventory digest is
`811595797b7c31fb1b60b1590dc13d03b014490b70f068833dc325dfa5870420`.
Therefore its current archive is the authoritative union, not a subset. The
runner requires exactly the two manifest hashes above; each archived source
must exist and match its frozen size and SHA-256 before its v3 root is used.

Fixed parameters:

- seed: `20260723-heldout-v3-001`
- sources per project: 6
- serialized native-source cap per project: 16,777,216 bytes
- source stability interval: 60 seconds
- absolute discovery cutoff:
  `1784871070206832949` ns since Unix epoch
- one selection attempt; no seed retry
- preflight project: the frozen project with the smallest total source bytes
  and then project name as the deterministic tie-breaker

The natural corpus contains only vendors with eligible data. Results are
reported per represented vendor and are not generalized to missing vendors.

## Baselines And Controls

- `current-v0`: commit `7e5464eca`, built in a detached clean worktree and
  sealed on the new frozen corpus before repaired production is run.
- source oracle: the selector-side parser.
- independent checker: a standalone implementation importing neither
  production nor the selector-side parser.
- action control: pinned ProcGrep revision
  `2e8277003dacaa774b5ef61ba150ae03a4f06693`.
- final-state control: Git index plus cutoff workspace snapshot.

There is no human annotation and no model-generated gold. All target facts
are source-native, deterministic, and independently recomputed.

The detached v0 worktree is `/tmp/agentsight-v0-7e`. Its locked build produces:

- Cargo.lock SHA-256:
  `c117357cf567baad5a8867f8def4d43a5f4733f1904d94a2c4cf662243553143`;
- binary SHA-256:
  `7f83e0f73fb8ab0b88e1dc257b27ffedd79ceb7ba1e5684b60c4b194773760f0`.

The baseline phase writes only blind candidate answers and provenance seals.
It does not write canonical answers, correctness, or aggregate scores.
Pre-result public `questions.csv` similarly omits `expected_answer`. Gold
remains only in the private oracle until v0 candidates and the repaired Git
tree/binary are sealed and the exact code seal has passed independent review.
The runner hard-checks the preregistered v0 Cargo.lock and binary hashes both
before baseline projection and before full scoring.

## Questions And Gates

Each project has 20 fixed questions:

- A1--A5: action counts and local action-order patterns;
- B1--B5: hotspot artifact facts;
- C1--C5: cross-session sharing, revisit, return, and span facts;
- D1--D5: cutoff workspace state.

Primary conformance object: the complete ordered multiset of attempted strict
artifact edges, including semantic root, stream, call, source Tool ordinal,
event/action ordinal, path, operation, prior path, status, and artifact
generation.

The first four conformance gates are mandatory overall and separately for
every vendor with at least one selected semantic session:

1. semantic session/order precision and recall = 1.0;
2. attempted-edge precision and recall = 1.0;
3. confirmed-effect-edge precision and recall = 1.0;
4. edge-call status precision and recall = 1.0;
The corpus-level decision additionally requires B+C = 60/60 correct, zero
wrong, zero abstain, and a repaired projection that is strictly more correct
than `current-v0` without increasing its wrong or abstain counts. There is no
undefined per-vendor B+C gate.

Any production root not present in the frozen oracle is an `extra`/failure;
it may not be filtered before scoring.

## Execution Order

1. finish public root/action/lifecycle fixtures and production unit tests;
2. independently review this plan without opening new held-out answers;
3. freeze the new corpus once with both prior freezes excluded;
4. run the standalone oracle checker and seal all hashes;
5. build and run `current-v0`, then seal its output;
6. commit the repaired implementation, generate its machine-readable
   code/binary/test seal, and obtain an independent review bound to that exact
   seal;
7. run only the pre-specified one-project preflight;
8. if every preflight gate passes, run the six-project full experiment once;
9. independently review the result before changing any paper claim;
10. rerun the six-project empirical extraction at one new stable cutoff and
    rewrite the paper using only validated measurements.

If a semantic change is required after opening preflight answers, this split
is invalidated. It is not repaired in place or retried with another seed.
The freeze is append-only: `freeze-attempt.json` is written before discovery,
failed attempts remain on disk, and existing private/release targets are never
deleted. `recover-freeze` and `rederive-freeze` are disabled for v3.
Preflight and full have the same one-attempt rule. Their permanent attempt
records bind the freeze, blind baseline, repaired code seal, and review. Full
refuses to run unless the unique matching preflight completed with `pass`;
failed or interrupted preflight permanently closes this split.

## Authoritative Commands And Artifacts

All commands run from the repository root. `<exp>` is
`docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/experiment-002`.

Public fixtures and unit gates:

```bash
python3 agentvis/research/rq7_measurement.py check-action-fixtures \
  --fixtures agent-session/tests/fixtures/strict-action-grammar.json
cargo test --manifest-path agent-session/Cargo.toml
cargo test --manifest-path agentvis/Cargo.toml
```

The one allowed freeze command is:

```bash
python3 agentvis/research/rq7_measurement.py freeze \
  --projects-file <exp>/heldout-projects.json \
  --private <exp>/private \
  --release <exp>/raw/freeze \
  --procgrep /tmp/procgrep-eval-2e827 \
  --exclude-freeze docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/private/freeze.json \
  --exclude-freeze <exp>/../experiment-001/private/freeze.json
```

The v0 build and blind baseline command is:

```bash
git -C /tmp/agentsight-v0-7e status --porcelain --untracked-files=no
cargo build --release --locked \
  --manifest-path /tmp/agentsight-v0-7e/agentvis/Cargo.toml
python3 agentvis/research/rq7_measurement.py baseline \
  --private <exp>/private \
  --output <exp>/private/heldout-v0 \
  --worktree /tmp/agentsight-v0-7e
```

Before preflight, the repaired branch is committed and the runner creates the
machine-readable code seal:

```bash
python3 agentvis/research/rq7_measurement.py seal-code \
  --private <exp>/private \
  --output <exp>/code-seal.json
```

This command requires a clean tracked Git tree, reruns the public fixtures,
both Rust test suites, formatting, Python compilation, and whitespace checks,
performs a locked release build, and seals the Git revision/tree, relevant
source and fixture files, Cargo.lock, binary, and test-output hashes. The
independent reviewer writes `<exp>/code-review.json` with:

```json
{
  "status": "pass",
  "reviewer": "independent-agent-id",
  "code_seal_sha256": "<sha256 of code-seal.json>"
}
```

`freeze-record.md` summarizes the freeze/audit/spec/checker, v0 candidate and
binary seals, repaired code seal, and independent review. Preflight/full
validate the machine-readable files, not the prose record.

Then:

```bash
python3 agentvis/research/rq7_measurement.py preflight \
  --private <exp>/private \
  --release <exp>/raw/preflight \
  --baseline <exp>/private/heldout-v0/baseline-candidates.json \
  --code-seal <exp>/code-seal.json \
  --code-review <exp>/code-review.json
python3 agentvis/research/rq7_measurement.py full \
  --private <exp>/private \
  --release <exp>/raw/full \
  --baseline <exp>/private/heldout-v0/baseline-candidates.json \
  --code-seal <exp>/code-seal.json \
  --code-review <exp>/code-review.json
```

`freeze-attempt.json`, `private/freeze.json`,
`private/audit-manifest.sha256`, `private/oracle-check.json`,
`raw/freeze/freeze-summary.json`, v0 `baseline-candidates.json` and
`baseline-seal.json`, `code-seal.json`, `code-review.json`,
`preflight-attempt.json`, `full-attempt.json`, preflight/full raw outputs,
review reports, and `freeze-record.md` are retained. No old result enters a
paper aggregate.

## Paper Decision

If all gates pass, the paper may claim that its artifact-linked
cross-session measurements are source-conformant under the explicit strict
projection boundary, and it will report the boundary rather than implying
complete Agent understanding.

If any gate fails, projection-sensitive empirical claims are removed or
restricted to a directly supported subset. The negative result is reported
without tuning on this held-out corpus.
