# Held-Out Freeze Record

- Specification: `native-root-conformance-v2`
- Question-spec SHA-256:
  `c54af788a4f4dfeec770238a98b21a97e7ddf72d58341c08bc59ec8b5e68c2c1`
- Private audit-manifest SHA-256:
  `b14d6ad1506e59155e1f5b4d19b1c2afd4672703823e18d7fa431dd8ca6c4c64`
- Independent checker SHA-256:
  `e27ad4faf4818db0449327314b0b82306a007cf26999451c379dc764a5033195`
- Sources: 48 files from 48 native roots; 30 Claude and 18 Codex.
- Source facts: 2,556 Tool calls and 1,300 strict attempted artifact edges.
- Split audit: zero development file-hash, native-root, and root-call overlap.
- Questions: 120 total, 30 per A/B/C/D family.

## Pre-Result Invalidation

This first derivation was invalidated before any held-out answer or score was
opened. A specification audit found that both oracle implementations assigned
an unseen failed create/rename target to persistent identity state, contrary
to the written rule that failed and observed mutations cannot change artifact
lifecycle. The immutable 48 source files, project blocks, selection seed, and
split are retained. Correcting lifecycle identity changes two top-five anchor
sets, so a fresh workspace snapshot is required for their D-family controls;
that new cutoff is captured before any score is opened. Only oracle identity
derivation, the independently mirrored check, and this mechanically required
final-state snapshot are refreshed. No source is replaced and no seed is
retried.

## Current-v0 Seal

- Repository revision before production repair: `7e5464eca`
- `agent-session/src/parser.rs`:
  `42065e6398ed3358aaedc1fa5c2f259f819709a2cd07fc3aba48a2f1a7418849`
- `agentvis/src/repository.rs`:
  `99fca3330a8d9eab7dc8ff2c96eb597c85ddd7994b74d6e6335043fdf90df41d`
- `agentvis/src/rq1.rs`:
  `e3b09637ea0342e815e214f38f9b8661bda436a62d8e98fe1913da410a25a591`
- Sealed current-v0 deterministic rows:
  `ddb0e6f3d030ad8b461ffa1dbe2ecb3c308ee78c5ab36b9841a9681b14adfef3`
- Sealed current-v0 cost rows:
  `a9d45c3a9339d6770a9de440ba9402eb55954c3864162b8ad5df40d2331902b9`

The two hashes above belong to the invalidated first derivation and are
retained only as an audit trail. The corrected-oracle baseline was rebuilt
from the same repository revision in a detached worktree:

- Corrected-oracle current-v0 rows:
  `c17476cf292b7b59d3096b03a3bfe077bf51cf79d99b0323dfed3cf2c6d5ef16`
- Corrected-oracle current-v0 cost:
  `b23ed5dfbfbfec224cf857581d7096201cf84c2a4031ebb25c83066f7790efa8`

## Corrected Freeze

- Specification: `native-root-conformance-v2` (text unchanged)
- Question-spec SHA-256:
  `c54af788a4f4dfeec770238a98b21a97e7ddf72d58341c08bc59ec8b5e68c2c1`
- Private audit-manifest SHA-256:
  `1572c90cfdf3aaa2b922e8b18e30dca7a9fce36e4c172dec06884a98794336ac`
- Independent checker SHA-256:
  `f0cf7d157c73f92103f1621190c4ae7966a60de03eb1a6892a988159ff83028f`
- Sources and split: the same 48 files and 48 native roots, with zero
  development file/root/call overlap.
- Source facts: 2,556 Tool calls and 1,300 attempted artifact edges.
- Independent checks: complete edge ledger and complete call/status ledger
  both match.

## Strict-v1 Code Seal

- `agent-session/src/parser.rs`:
  `55284c3e8db2b1d70bf7c042fb80b01b6166c1bda8eb061799cd3a228bbf508c`
- `agentvis/src/repository.rs`:
  `95fda2f10599e4a8f32c9ceef58f7648f9ef1819b107168278b2156388cace05`
- `agentvis/src/rq1.rs`:
  `b46e6ed83345b8df6dd79cc6f3965865b239f6452757dd2863098115911f9960`
- Experiment/scorer:
  `23ed826766f8eb9cc4552e71d8df03cff9ee1e8b508a25c8ab805737cdf2017b`
- Independent source checker:
  `f0cf7d157c73f92103f1621190c4ae7966a60de03eb1a6892a988159ff83028f`

No held-out answer, baseline score, or strict-v1 score was opened before these
hashes were recorded.

## Pre-Result Invalidation After Code Review

The first strict-v1 code seal and corrected freeze above were invalidated
before any held-out answer, baseline score, or strict-v1 score was opened.  The
independent code-freeze review found five executable-contract defects:
production and oracle action grammars differed, the scorer injected oracle
session order and recomputed production lineage with the oracle tracker,
call-local action order was not checked, timestamp-less calls had different
policies, and the v1-over-v0 condition was absent from the completion gate.
The immutable 48 native source files, project blocks, selection seed, and
zero-overlap split are retained.  Because the clarified grammar excludes
timestamp-less calls and ambiguous shell references, the source oracle,
questions, current-v0 output, and production code are all resealed below.  No
source was replaced and no selection seed was retried.

## Final Held-Out Freeze

- Specification: `native-root-conformance-v2`
- Question-spec SHA-256:
  `c6c8b5f45a9914304064abe1a99045c4d5867257a9980c2a58fe0bfa47fb800e`
- Private audit-manifest SHA-256:
  `c9a06cf41c4a6a035a1eae35249d6df46743543636b8149b664b9916730442b5`
- Independent checker SHA-256:
  `9caeb53a0e8a34fc80dc795895436e640916099a2f0d20f4094846c61fe61462`
- Sources: the same 48 files from 48 native roots; 30 Claude and 18 Codex.
- Source facts: 2,405 timestamped Tool calls and 1,187 strict attempted
  artifact edges.
- Questions: 120 total, 30 per A/B/C/D family.
- Split audit: zero development file-hash, native-root, and root-call overlap.
- Independent checks: complete ordered edge ledger and complete call/status
  ledger both match.

## Final Current-v0 Seal

- Repository revision before production repair: `7e5464eca`
- Deterministic rows:
  `69fc5bec56a1b765edac6bb738894e29f47fa3dada095c74665f69db9cc37a17`
- Cost rows:
  `adc469a32077c7f228a71917220736d2a9463d5b8255286f3c0b6aa855b8f22c`

## Final Strict-v1 Code Seal

- `agent-session/src/parser.rs`:
  `0f0f3dcffa6570787cca5fb4c31cf69fc068393cddd7dea870af4b4de6abd914`
- `agentvis/src/repository.rs`:
  `0381d6c090ceaaae4a2ee558b9ec77378adb057c96c859ca9b7e6fd84725dd1f`
- `agentvis/src/rq1.rs`:
  `7381702d1c733d0761407fc376c2020ca53e0394584e86eced1cd07bc6fd2a6e`
- Experiment/scorer:
  `c39639e1e179ddfb6ce9024819c17929c28a3b9acae75a409c954ed97d534c89`
- Independent source checker:
  `9caeb53a0e8a34fc80dc795895436e640916099a2f0d20f4094846c61fe61462`

The public four-case action-grammar fixture, 18 `agent-session` library tests,
38 `agentvis` library tests, Python syntax checks, and whitespace checks pass
at this seal.  Held-out results remain unopened pending the second independent
code-freeze review.

## Pre-Result Invalidation After Second Code Review

The second review blocked the preceding seal before any held-out answer,
baseline score, or strict-v1 score was opened.  It found remaining
production/oracle differences for `filepath`, same-path multi-action calls,
and Tool-name admission.  It also found a shared lifecycle bug: a failed
create's attempted identity could survive a confirmed create/delete generation
and be revived by a later access.  The repair makes Tool-name admission exact,
preserves distinct `(path, access, previous_path)` tuples, clears
attempted-only identity on a confirmed effect, and checks the same public
fixtures in Rust production plus both independently written Python oracles.
The same immutable 48 sources, project blocks, selection seed, and split are
retained; no source or seed was replaced.

## Review-Ready Held-Out Freeze

- Specification: `native-root-conformance-v2`
- Question-spec SHA-256:
  `018c7116f9781a998f53e1366424e104af5f00f70f7a0f75c45635a177f5fb2f`
- Private audit-manifest SHA-256:
  `a99c8bf83f8258b11465bd0723883263e8db5208b148b4c3479e6cc54ce35958`
- Independent checker SHA-256:
  `7f4cc041138e7002fe42b9539868f52fef3487024eb6960c2721d07e2d1145fa`
- Sources: the same 48 files from 48 native roots; 30 Claude and 18 Codex.
- Source facts: 2,405 timestamped Tool calls and 1,187 strict attempted
  artifact edges.
- Questions: 120 total, 30 per A/B/C/D family.
- Split audit: zero development file-hash, native-root, and root-call overlap.
- Independent checks: complete ordered edge ledger and complete call/status
  ledger both match.
- Oracle answer SHA-256 remains
  `5d0743acc626d1ae5f00053e208a38c733d8b0d6f11342493cf8f90de8a8cec8`;
  the clarified edge cases do not occur in the frozen sources.

## Review-Ready Current-v0 Seal

- Repository revision before production repair: `7e5464eca`
- Deterministic rows:
  `766d235711e7c48a0aea8960f0f4e515dda012dfa895e459dc4e8513c913d55f`
- Cost rows:
  `b91e41aa4a41158148c315c0a8d59448ffc38144803b2fff119b8efda266625a`

## Review-Ready Strict-v1 Code Seal

- `agent-session/src/parser.rs`:
  `c9af8d6fa099f6f64e075546fb175aa4c60510104ee26a959bb317d90b9f57c8`
- `agentvis/src/repository.rs`:
  `9cf213b6467e69aa870bd029c7622dfe2d3fe27302f7397327b3f6ba5dfb0dc8`
- `agentvis/src/rq1.rs`:
  `7381702d1c733d0761407fc376c2020ca53e0394584e86eced1cd07bc6fd2a6e`
- Experiment/scorer:
  `87ba4361d59fe8ff6742832976bbbe9f5f92726b97f0b0a6d56802f4975f89cc`
- Independent source checker:
  `7f4cc041138e7002fe42b9539868f52fef3487024eb6960c2721d07e2d1145fa`
- Shared action fixture:
  `685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7`
- Shared lifecycle fixture:
  `f092a62cd28919e284195226f04f27a4ccf5f128146348c22567d85cb4f04a1e`

The shared fixture gate passes 8 action and 2 lifecycle cases against Rust
production and both independent oracles.  All 19 `agent-session` and 39
`agentvis` library tests, Python syntax checks, and whitespace checks pass.
Held-out results remain unopened pending a third independent code-freeze
review.

## Pre-Result Invalidation After Third Code Review

The third review verified every second-review condition but blocked one
additional lifecycle boundary before any held-out result was opened:
`RepositoryEvent` identity transferred across worktrees on a confirmed rename,
while the RQ1 lineage implementation and written specification preserve rename
identity only within one worktree.  The repair keys both Python trackers by
worktree, prevents cross-worktree identity transfer in Rust production, adds
same- and cross-worktree rename lifecycle fixtures, and adds an RQ1 regression
test.  The same 48 sources and selection remain unchanged.

## Final Candidate Held-Out Freeze

- Specification: `native-root-conformance-v2`
- Question-spec SHA-256:
  `018c7116f9781a998f53e1366424e104af5f00f70f7a0f75c45635a177f5fb2f`
- Private audit-manifest SHA-256:
  `d0fe2d18821dd9a2fed0551fce0cc7e1b2d8fb21be584bde43740ba57fa88ac0`
- Independent checker SHA-256:
  `6936996a4bf80b47a458c24692df8a3eea39155b347eb9b2dfeaceaf01f02b73`
- Sources: the same 48 files from 48 native roots; 30 Claude and 18 Codex.
- Source facts: 2,405 timestamped Tool calls and 1,187 strict attempted
  artifact edges.
- Questions: 120 total, 30 per A/B/C/D family.
- Split audit: zero development file-hash, native-root, and root-call overlap.
- Independent checks: complete ordered edge ledger and complete call/status
  ledger both match.
- Oracle answer SHA-256 remains
  `5d0743acc626d1ae5f00053e208a38c733d8b0d6f11342493cf8f90de8a8cec8`.

## Final Candidate Current-v0 Seal

- Repository revision before production repair: `7e5464eca`
- Deterministic rows:
  `766d235711e7c48a0aea8960f0f4e515dda012dfa895e459dc4e8513c913d55f`
- Cost rows:
  `80fa22ecd52fd6b5ba98e28f4b605b5bc02ae8e7aecb5006e727bbe8bd961587`

## Final Candidate Strict-v1 Code Seal

- `agent-session/src/parser.rs`:
  `726fbde1cfb618f69e09b8221e339d202ddcb550da3909d9d4a25f7c8ac9a4f5`
- `agentvis/src/repository.rs`:
  `bf5e2ebff67cdba0128ce7fbf099fd93b20dd481d400bf7961364f58862459eb`
- `agentvis/src/rq1.rs`:
  `7b7dcfd8efcc147e83b9cb33b8c075867aa6b50f9306599ed3f7c600df7bca5c`
- Experiment/scorer:
  `7ad2769ff0da00968ce5a68e52a618432021fc72fa213f846483938986d0916d`
- Independent source checker:
  `6936996a4bf80b47a458c24692df8a3eea39155b347eb9b2dfeaceaf01f02b73`
- Shared action fixture:
  `685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7`
- Shared lifecycle fixture:
  `08b614293d36966939d4b635e8bd879dd381e54af392e5647e22889fc85e71ba`

The shared fixture gate passes 8 action and 4 lifecycle cases against Rust
production and both independent oracles.  All 19 `agent-session` and 40
`agentvis` library tests, both Rust formatting checks, Python syntax checks,
and whitespace checks pass.  Held-out results remain unopened pending the
reviewer's final hash-only and cross-worktree recheck.
