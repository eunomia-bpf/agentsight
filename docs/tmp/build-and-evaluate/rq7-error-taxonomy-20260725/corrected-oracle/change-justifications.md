# RQ7 v4 oracle change-justification log

This log applies `native-root-conformance-v4` to the immutable 120 questions
and the frozen native sources. The experiment directory was read only. The
machine-readable evidence is in `corrected-answers.csv`,
`corrected-oracle-edges.json`, `oracle-edge-diff.json`, and
`source-evidence.json`.

## Evaluation bridge

HEAD cannot consume the v2 freeze ledger directly. The reassessment therefore
uses the same compatibility boundary as `rerun-at-HEAD`: it preserves each
frozen source file's `session_id`, frozen session ordinal, timestamp, source
SHA-256, record index, call index, cutoff snapshot, and the paths written into
the immutable questions. It rebuilds action atoms and artifact edges directly
from the hash-checked frozen native files with the v4 oracle grammar. This
tests the same 120 question identities without rewriting the freeze.

The v4 ranking is also emitted as an audit check. It is not substituted for
the P0--P4 paths already named by the frozen questions.

## Change 1: decode static Codex exec/apply_patch wrappers

Spec rule: apply_patch calls are `edit` atoms and their file headers
contribute artifact edges.

Before: `unwrap_exec` could unwrap `tools.exec_command({...})`, but a Codex
`exec` body such as

```text
const patch = "*** Begin Patch\n*** Update File: ...\n*** End Patch";
text(await tools.apply_patch(patch));
```

kept the patch in an escaped JavaScript string. The patch-header parser never
saw real line boundaries. If the same wrapper later called
`tools.exec_command`, the nested command replaced the outer arguments and the
patch was also lost.

After: v4 decodes only a statically assigned, double-quoted,
JSON-compatible string and only when that variable is passed to
`tools.apply_patch`. It does not evaluate JavaScript. The containing tool
invocation is classified as `edit`, like a native apply_patch call. It
preserves both a wrapped patch and a separately nested shell command, if
present. Patch content is parsed only as patch content, so text such as
`+touch file` inside a patch hunk cannot fabricate a shell edge.

Frozen-source evidence:

| Project | Wrapper calls recovered | Header edges recovered | Accesses |
|---|---:|---:|---|
| ActPlane | 393 | 482 | 466 write, 13 create, 3 delete |
| bpf-developer-tutorial | 4 | 15 | 15 write |
| Total | 397 | 497 | 481 write, 13 create, 3 delete |

Representative frozen calls are retained in
`source-evidence.json` under `wrapped_patch_samples`. For ActPlane they begin
with source `S001-dacddf675e`, call
`call_T3kUcdOGGsqFmd2XAkpjcIFq`; for bpf-developer-tutorial they begin with
source `S001-c4a632d03f`, call
`call_4sop8FqBsNmoZudPVdwvXCXn`.

Answer consequence relative to v3:

| Question | Before | After | Reason |
|---|---:|---:|---|
| ActPlane-A2 | 78 | 471 | 393 recovered apply_patch wrappers become edit atoms |
| ActPlane-A3 | 567 | 457 | edit classification takes precedence over nested shell test text |
| ActPlane-A4 | 3 | 4 | corrected action sequence adds one read-to-edit pattern |
| ActPlane-A5 | 0 | 1 | corrected action sequence adds one edit-to-test pattern |
| ActPlane-C1 | 1 | 3 | recovered shared artifacts in adjacent sessions |
| ActPlane-C2 | 1 | 3 | recovered later-session revisits |
| ActPlane-C5 | 4 | 12 | recovered artifacts present in two or more sessions |
| bpf-developer-tutorial-A2 | 31 | 35 | four recovered apply_patch wrappers become edit atoms |
| bpf-developer-tutorial-A3 | 42 | 39 | edit classification takes precedence over nested shell test text |
| bpf-developer-tutorial-A4 | 5 | 6 | corrected action sequence adds one read-to-edit pattern |
| bpf-developer-tutorial-A5 | 0 | 1 | corrected action sequence adds one edit-to-test pattern |
| bpf-developer-tutorial-C1 | 6 | 7 | recovered shared artifacts in an adjacent pair |
| bpf-developer-tutorial-C2 | 7 | 8 | recovered a later-session revisit |
| bpf-developer-tutorial-C5 | 17 | 22 | recovered five cross-session artifacts |

The six C changes exactly match the six previously unexplained wrapped-patch
C-family trajectory answers. The A rows are the corresponding action-sequence
consequences of parsing the wrappers as normal apply_patch calls.

## Change 2: track lexical inline `cd`

Spec rule: resolve a relative operand lexically from the command's effective
working directory and exclude paths outside the selected worktree.

Before: shell segments were parsed independently. In
`cd third_party/openreviewer && cat README.md`, `README.md` was resolved from
the event cwd. In `cd /tmp/... && touch fake/...`, the relative `touch`
operand could be fabricated inside the repository. `rmdir` was and remains
excluded because it is not one of the spec's mutators.

After: v4 carries a known lexical cwd through later simple shell segments.
An absolute `cd /tmp/...` therefore makes later operands absolute and
`repo_path` excludes them. A dynamic, globbed, tilde, or ambiguous `cd`
invalidates cwd knowledge, so v4 does not guess a repository path.

Frozen-source evidence for academic-writing-skills includes correctly scoped
reads of `third_party/openreviewer/README.md` and
`third_party/openreviewer/llm_training/generate.py`, and exclusion of the
`/tmp/.../fake/...` create. The before/after edge ledger records 6 v4-only and
7 v3-only edges for this project.

Answer consequence:

| Question | Before | After | Reason |
|---|---:|---:|---|
| academic-writing-skills-C2 | 9 | 8 | session ordinal 9 no longer revisits the fabricated repo-root `README.md`; its reads are scoped under `third_party/openreviewer/` |

Inline-cd edge changes in eunomia.dev do not change any of its 20 immutable
answers.

## Change 3: verify option arity and sed programs

No code change was needed in this area. The existing v3 command-specific
grammar is retained:

- `cat` has no argument-taking `-n`; therefore
  `cat -n collector/src/view/mod.rs` retains the file operand.
- `head`, `tail`, and `nl` skip arguments only for their own
  argument-taking options.
- For `sed -n '1,5p' README.md`, `-n` is a flag, the first remaining
  non-option is the sed program, and `README.md` is the only artifact operand.
- For `sed -e '...' README.md` and `sed -f rules.sed README.md`, the
  expression or program-file option argument is not treated as a target
  artifact; subsequent file operands are retained.
- A program-only pipeline segment such as `find . | sed 's#...##'` contributes
  no sed artifact.

The focused regression suite covers `cat -n`, inline and explicit sed
programs, patch decoding, patch-body isolation, nested shell preservation,
inline `cd`, and out-of-worktree exclusion.

### AgentSight `cat -n` source-row finding

Retaining the operand does not make the call a P0 access. Frozen source
`S000-007c5d5ec4`, zero-based record 313, call
`toolu_01QdMaxMofN8AJdpWurjqbnR`, has:

```text
cwd:     /home/yunwei37/workspace/agentsight/collector
command: cat -n collector/src/view/mod.rs
result:  Exit code 1; collector/src/view/mod.rs: No such file or directory
```

The spec's lexical resolution therefore yields
`collector/collector/src/view/mod.rs`, not P0
`collector/src/view/mod.rs`. The option-arity diagnosis was correct, but the
source cwd proves that this particular attempt cannot increase P0 B1 or B2.

The corrected oracle has one edge for that call at
`collector/collector/src/view/mod.rs`. The HEAD projection instead has one
edge at `collector/src/view/mod.rs`; both sides of the exact diff are in
`oracle-edge-diff.json`.

## All corrected-answer changes

Twenty-four of 120 expected answers change. Seven are the C-family corrections
above. The other seventeen are action-only answers:

| Question | Frozen | Corrected |
|---|---:|---:|
| agentsight-A1 | 81 | 97 |
| agentsight-A2 | 19 | 6 |
| ActPlane-A1 | 104 | 331 |
| ActPlane-A2 | 161 | 471 |
| ActPlane-A3 | 595 | 457 |
| ActPlane-A4 | 3 | 4 |
| ActPlane-A5 | 0 | 1 |
| bpf-developer-tutorial-A1 | 214 | 217 |
| bpf-developer-tutorial-A2 | 33 | 35 |
| bpf-developer-tutorial-A3 | 42 | 39 |
| bpf-developer-tutorial-A4 | 5 | 6 |
| bpf-developer-tutorial-A5 | 0 | 1 |
| eunomia.dev-A1 | 225 | 229 |
| eunomia.dev-A2 | 268 | 212 |
| eunomia.dev-A3 | 102 | 103 |
| agentskill-observability-paper-A2 | 234 | 140 |
| academic-writing-skills-A2 | 357 | 250 |

The A2 changes combine two corrections. First, v4 excludes non-tool Claude
`file_snapshot` records that v2 classified as edits: 13 agentsight, 83
ActPlane, 2 bpf-developer-tutorial, 56 eunomia.dev, 94
agentskill-observability-paper, and 107 academic-writing-skills records.
Second, the 393 ActPlane and four bpf-developer-tutorial recovered wrappers
are edit atoms. The other A shifts come from applying the current native
exec-wrapper grammar to frozen calls. Counts and representative call IDs for
every old-to-new atom transition are in `source-evidence.json`.

Eight trajectory rows that were correct against the old expected values become
wrong: agentsight-A2, ActPlane-A2, ActPlane-A4, ActPlane-A5,
bpf-developer-tutorial-A5, eunomia.dev-A2,
agentskill-observability-paper-A2, and academic-writing-skills-A2.
bpf-developer-tutorial-A1 moves from wrong to correct. No previously correct
B- or C-family row becomes wrong.
