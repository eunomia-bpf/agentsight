# Independent Code Review 001

**Scope:** uncommitted Step 0077 aggregate-diagnostics implementation  
**Verdict:** **REVISE**

## Review boundary

I reviewed the current implementations and documentation in:

- `agentpprof/src/annotation_workspace.rs`;
- the annotation-workspace status path in `agentpprof/src/main.rs`;
- `agentpprof/tests/annotation_workspace_cli.rs`;
- `agentpprof/README.md`;
- `docs/design/visexp/agentpprof-annotation-workspace.md`;
- `docs/implementation.md`; and
- the Step 0077 entry, experiment plan, automatic-backend instruction, and
  three plan-review rounds.

I also read the complete repository instructions, `docs/user-instruction.md`,
and `docs/idea-story.md`. This was a read-only review. I did not change code,
the experiment plan, the paper, or Git state.

## Overall assessment

The change has the right product shape. It adds diagnostics to the existing
annotation-workspace projection instead of creating a frontend, renderer,
alternate artifact, in-process backend framework, or fixed-depth constructor.
The emitted profile remains the sole product artifact; JSON status is command
output and `trace.jsonl`/`stacks.folded` remain the existing workspace
intermediates. Depth remains variable and every new shape warning is advisory.

The depth-mass calculation also uses the selected view's exact additive field
and agrees with pprof mass on the two retained workspaces I replayed:

| workspace/view | nodes | annotations | reported sample mass | depth-mass sum |
|---|---:|---:|---:|---:|
| Git/tokens | 735 | 96 | 4,558,192 | 4,558,192 |
| AgentReward/operations | 15,338 | 2,131 | 7,229 | 7,229 |

The retained 15,338-node AgentReward workspace completed under the debug binary
in about 1.62 seconds with about 108 MiB peak RSS, so the current fixed
population is practical despite the non-linear implementation discussed
below.

The implementation is not ready for the real Step 0077 run, however. Two
functional blockers affect the exact convergence protocol, and a third input
validation defect can panic the CLI.

## Blocking findings

### 1. Region resolution is dependent on annotation-key order and does not enforce the declared semantic-parent tree

**Location:** `agentpprof/src/annotation_workspace.rs:566-612` and
`agentpprof/src/annotation_workspace.rs:615-637`

Regions are built by iterating a `BTreeMap<String, Annotation>`, so they are
processed by source-node ID rather than source order or semantic-parent order.
For a `next: null` child, lines 578-581 copy the parent's current end exactly
once. If the child sorts before its parent and the parent must itself inherit
an end from its parent, the child keeps the stale session end. A valid
three-level hierarchy is then rejected as crossing.

I reproduced this with one contiguous session containing:

```text
z_grand  [start, explicit end)
`- y_parent  [start, inherit z_grand end)
   `- a_child  [start, inherit y_parent end)
```

The source order and semantic parents are valid, but the IDs sort as
`a_child`, `y_parent`, `z_grand`. The CLI exits with:

```text
Error: annotations at "a_child" and "y_parent" cross; ranges must be nested or disjoint
```

The converse is also accepted incorrectly. Two annotations can declare the
same semantic parent while one interval is nested inside the other. The
pairwise check accepts them because their intervals are nested, and
`apply_paths()` then adds *every* containing region rather than following the
declared parent chain. In a minimal fixture:

```text
inspect outer       parent = prompt, interval [c1, c4)
diagnose sibling    parent = prompt, interval [c2, c3)
```

the weighted `c2` path becomes:

```text
execute task
-> fulfill request
-> inspect outer
-> diagnose sibling
```

even though `diagnose sibling` explicitly declares the prompt—not
`inspect outer`—as its semantic parent. This silently changes the aggregate
operation stack and attribution while conserving numeric mass, so mass checks
cannot detect the corruption.

This is blocking for Step 0077 because repeated automatic revisions may create
deeper `next: null` chains with arbitrary source IDs, and the experiment treats
the CLI-derived hierarchy as authoritative.

**Required repair:**

1. Resolve inherited ends recursively or in semantic-parent topological order,
   independent of JSON key order.
2. Recheck `start < end` after inherited-end resolution.
3. Validate that interval containment agrees with the declared semantic-parent
   relation. Nested intervals declared as siblings must be rejected; the
   nearest containing semantic region should be the declared parent.
4. Build each active path from the validated semantic-parent chain, or prove
   through validation that scanning all containing intervals is equivalent.

Add tests whose source IDs deliberately sort child-before-parent and a test
that rejects nested sibling intervals.

### 2. `near_name_candidates` is silently truncated, so the predeclared convergence condition is not executable

**Location:** `agentpprof/src/annotation_workspace.rs:314-333`;
public claims in `agentpprof/README.md:116-121` and
`docs/design/visexp/agentpprof-annotation-workspace.md:264-276`

The lexical matcher stops after the first 25 matches in lexicographic nested-
loop order. The status does not report the total number of matches, whether the
list was truncated, or a cursor/page with which the next pass can inspect the
remaining candidates.

A 30-tag fixture using `inspect 00` through `inspect 29` returned exactly 25
candidates. All 25 had `inspect 00` as the left name; later near-name pairs
were omitted. Thus the cap is not merely a compact best-25 summary: it is a
lexicographically biased prefix.

This conflicts with the Step 0077 procedure. The terminal state is the first
complete pass in which every issued diagnostic is considered and no change is
accepted. With the current API, a backend can repeatedly keep the visible 25
pairs and stop while other mechanically qualifying pairs were never issued.
The README and design document present `near_name_candidates` as the feedback
input without disclosing that it is partial.

The length prefilter at line 318 also compares UTF-8 byte lengths while the
Levenshtein implementation counts Unicode scalar values. It can therefore
discard a pair whose character edit distance is at most two.

**Required repair:** make completeness explicit and consumable. Suitable
minimal choices include:

- emit all qualifying pairs for the fixed experiment populations; or
- retain a bound but add a deterministic total, `truncated` flag, and
  pagination/cursor or per-tag continuation that the convergence driver must
  exhaust before declaring a complete pass.

If output is bounded, select candidates by a documented deterministic priority
such as edit distance and tag reuse rather than the first lexicographic left
name. Use character counts consistently with the distance function. Add a CLI
test with more candidates than the bound and verify either exhaustiveness or
the continuation contract.

### 3. A source trace accepted by validation can panic aggregate diagnostics

**Location:** `agentpprof/src/annotation_workspace.rs:194-203`,
`agentpprof/src/annotation_workspace.rs:217`, and
`agentpprof/src/annotation_workspace.rs:422-441`

`validate_source_tree()` requires only that a parent appear earlier. Region and
diagnostic session ownership instead assume that all nodes belonging to one
root form one contiguous block and assign each node to the most recently seen
root. That stronger input invariant is neither validated nor clearly stated in
the public contract.

I reproduced this with two roots and a later node whose declared source parent
belongs to the first root:

```text
s1, p1, s2, p2, c1(parent=p1)
```

Every parent exists earlier, so source validation accepts the input. End
inheritance then produces a region with `start = 4, end = 2`, and aggregate
diagnostics panic at the slice on line 217:

```text
thread 'main' panicked at src/annotation_workspace.rs:217:39:
slice index starts at 4 but ends at 2
```

Even if Step 0077's current adapters serialize sessions contiguously, a public
CLI must reject malformed ordering with an actionable error rather than panic.
Chronological source adapters may also naturally interleave sessions unless
the contract requires a contiguous preorder.

**Required repair:** either derive root ownership through the source-parent
chain or explicitly validate the contiguous-root/preorder invariant before
region construction. In all cases, reject `end <= start` after inheritance and
make diagnostics consume only already-validated regions. Add a regression test
asserting a normal error and no workspace/profile replacement.

## Scaling and API observations

These are not additional blockers for the fixed 15,338-node case, but they
should guide the repair:

- `apply_paths()` scans every region for every node and repeatedly walks
  semantic parents while sorting, giving at least `O(nodes * regions)` work.
- `covered_tool_calls` rescans each complete region interval, giving work
  proportional to the sum of region widths and potentially
  `O(nodes * depth)` for nested spans.
- lexical matching is `O(unique_tags^2 * tag_length^2)`. The 25-result cap
  limits output but does not limit comparisons when few pairs qualify.

The retained AgentReward workspace is currently fast because it has only 30
normalized optional tags despite 2,131 annotations. A fresh open-vocabulary
first pass may have far more unique tags. An interval sweep/prefix count for
paths and tool coverage plus a bounded indexed lexical search would provide a
safer growth path. At minimum, the full preflight should record CLI time/RSS
with the fresh iteration-0 tag cardinality, not infer it from the compact
retained workspace.

The JSON field names are otherwise clear and stable enough for the experiment:
`tag_reuse` is exhaustive and includes normalized pprof identity, occurrence
count, and sorted source sessions; hierarchy issues include a source session,
start, exclusive end, child counts, and covered tool count; depth mass keys
serialize naturally as JSON object strings. The documentation correctly says
these are advisory locations rather than correctness judgments.

## Depth-mass conservation

The selected metric mapping matches `build_profile()` for all five views:

```text
operations -> operations
tokens     -> tokens
files      -> files
network    -> network
time       -> time_ns
```

For positive-weight nodes, summing `semantic_depth_mass` is therefore
mathematically equal to the reported folded sample mass after a valid path is
applied. The observed Git and AgentReward replays confirm this for tokens and
operations.

The current test suite checks one operations-view equality indirectly, but it
does not assert the invariant across all views. Because the experiment
explicitly makes this a preflight validity check, add one table-driven unit or
integration test over all five fields and preferably a direct runtime
assertion before returning status. Also test a non-null exclusive issue end;
the current coarse-span integration test covers only `end_node_id: null`.

Mass conservation does **not** make finding 1 safe: the sibling-as-ancestor
fixture preserves total mass while assigning that mass to the wrong semantic
path.

## Test and tooling results

The standard required suite passes:

```text
cargo test --manifest-path agentpprof/Cargo.toml --locked
80 passed; 0 failed
```

Formatting check passes. Strict Clippy does not:

```text
cargo clippy --manifest-path agentpprof/Cargo.toml \
  --locked --all-targets -- -D warnings
```

fails on the collapsible nested `if` at
`agentpprof/src/annotation_workspace.rs:252-263`. This is mechanical, but it
should be repaired before the change is considered clean.

The current tests cover:

- variable depth and ordinary sibling regions;
- pprof and folded-stack mass;
- atomic behavior for an early invalid annotation;
- one coarse-span issue;
- cross-session tag reuse and singleton counts; and
- the three-word limit.

Missing high-value regression coverage is:

1. inherited ends with child IDs sorting before parent IDs;
2. nested intervals whose declared semantic parents make them siblings;
3. source nodes that return to an earlier root after a later root appears;
4. a positive CLI near-name case and the over-25 completeness contract;
5. Unicode character/byte-length behavior;
6. all-view depth-mass equality; and
7. non-null exclusive issue endpoints.

## Scope audit

The implementation respects the requested scope:

- no frontend, dashboard, renderer, or bespoke visualization runtime;
- no new product artifact beyond `.pb`/`.pb.gz`;
- no alternate folded/JSON product output;
- no annotation editor, backend registry, or in-process model framework;
- no forced minimum, maximum, or target depth;
- no forced merge or forced elimination of singleton/unary/coarse/fan-out
  diagnostics;
- no outcome or human-stage field introduced into annotation construction; and
- no paper-story, RQ, thesis, or core-abstraction change.

The experiment's Markdown, per-iteration pprof files, diagnostics, and paper
figures are correctly scoped as research records/derivatives rather than new
AgentPProf product outputs.

## Final verdict

**REVISE.**

The aggregate diagnostics are a focused and appropriate extension, and their
mass accounting and product boundaries are sound. Real execution should wait
until:

1. region inheritance and interval containment are made independent of source
   ID sorting and faithful to `parent`;
2. lexical diagnostics expose a complete or explicitly pageable candidate
   set; and
3. source-session ordering cannot reach diagnostics with an invalid interval
   or panic.

Those repairs are local to the current annotation-workspace path. They do not
require a frontend, another artifact, a backend framework, a new experiment,
or any forced-depth policy.

---

## Round 2 Review

**Verdict:** **PASS**

I re-reviewed the repaired implementation in the same scope and reran both the
repository tests and independent black-box versions of the three Round 1
fixtures. All blockers are closed.

### 1. End inheritance and semantic-parent consistency — resolved

`resolve_regions()` now:

- derives source-root ownership before resolving regions;
- maps every semantic parent to a region index;
- resolves `next: null` ends recursively with explicit visit state, independent
  of `BTreeMap`/source-ID order;
- rejects semantic-parent cycles and non-forward inherited ends;
- validates each child against its declared parent's interval; and
- rejects every nested interval pair unless the containing region is a declared
  semantic ancestor.

The new unit tests cover both failures from Round 1:

- `inherited_ends_follow_semantic_parents_not_annotation_key_order` uses
  `a_child -> y_parent -> z_grand`, whose IDs sort in the opposite order from
  the semantic chain, and obtains the intended five-frame path; and
- `nested_intervals_declared_as_siblings_are_rejected` confirms that interval
  nesting cannot silently manufacture an undeclared ancestor.

I independently replayed the same shapes through the CLI. The child-before-
parent fixture succeeds with:

```text
execute -> fulfill request -> inspect -> diagnose -> test
```

and the nested-sibling fixture fails normally with:

```text
Error: annotation "c2" is nested inside "c1" but does not declare it as a semantic ancestor
```

This makes the declared `parent` relation authoritative for the profile
hierarchy while preserving variable depth.

### 2. Source-root/session layout — resolved

`source_root_layout()` now propagates each node's root through its already
validated source parent and explicitly detects a return to a closed root.
Thus the implementation either receives one contiguous block per source
session or rejects the trace before constructing or slicing regions.

The new `noncontiguous_source_session_is_rejected_without_panicking` regression
test covers the exact Round 1 ordering. My independent CLI replay now exits
with status 1 and the actionable error:

```text
Error: trace node "c1" returns to an earlier source root; each session must be one contiguous source-tree block
```

There is no panic and no invalid interval reaches aggregate diagnostics.
Because accepted roots are contiguous, the sequential `root_at` used by the
diagnostic summaries is equivalent to the source-parent-derived ownership.

### 3. Near-name completeness and Unicode consistency — resolved

The lexical matcher no longer has the silent 25-result cap. It emits every
qualifying pair in deterministic name order. Its length prefilter now uses
`chars().count()`, matching the character units used by Levenshtein distance.

The new
`near_name_candidates_are_exhaustive_and_unicode_uses_character_length` test
checks both properties. It produces more than 25 matches, verifies a pair near
the end of the old truncated range, and includes a pair that the former UTF-8
byte-length filter would have skipped.

My 30-name CLI replay returns all 435 qualifying pairs and includes
`inspect 28 ~ inspect 29`. The Step 0077 backend can therefore exhaust the
candidate set before declaring a no-change convergence pass.

The exhaustive algorithm remains quadratic in distinct tag count and tag
length, as recorded in Round 1. That is an explicit scaling tradeoff rather
than a correctness ambiguity. The planned fresh-population preflight already
records CLI wall time and RSS, so it is sufficient for the current fixed
experiment.

### 4. Depth-mass conservation and issue endpoints — resolved

The export path now computes folded pprof sample mass and semantic-depth mass
before writing artifacts and returns an error unless they are exactly equal.
The returned `samples` value is the same mass checked by this runtime invariant.

`annotation_workspace_depth_mass_matches_every_profile_view` covers
`operations`, `tokens`, `files`, `network`, and `time`. The coarse-span
integration fixture now uses an explicit exclusive endpoint and asserts
`end_node_id == "c8"`, closing the previous non-null-end coverage gap.

### 5. Tests, formatting, and strict Clippy — resolved

The complete checks pass:

```text
cargo fmt --manifest-path agentpprof/Cargo.toml --all -- --check

cargo test --manifest-path agentpprof/Cargo.toml --locked
85 passed; 0 failed

cargo clippy --manifest-path agentpprof/Cargo.toml \
  --locked --all-targets -- -D warnings
```

The former collapsible-`if` warning is repaired, and strict Clippy produces no
warning or error.

### Round 2 scope audit

The repair remains local to the existing annotation-workspace implementation
and tests. It adds no frontend, custom renderer, additional product artifact,
backend framework, forced merge, or fixed/minimum/maximum depth. Diagnostics
remain advisory, semantic paths remain variable-depth, and the only product
output remains standard pprof.

### Round 2 final decision

**PASS.**

The Round 1 interval, convergence, session-mapping, conservation-test, and
strict-lint blockers are resolved. The implementation is ready for the
approved Step 0077 real preflight and experiment without additional code-review
conditions.
