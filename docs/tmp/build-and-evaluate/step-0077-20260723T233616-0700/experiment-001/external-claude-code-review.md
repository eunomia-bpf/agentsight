# External Claude Opus code review

Timestamp: 2026-07-24T00:13:00-07:00
Reviewer: Claude Opus via read-only Claude Code invocation
Verdict: **PASS**

The reviewer independently read the current implementation, integration tests,
and prior code review. The tool session denied Bash, so the reviewer
hand-traced the fixtures rather than rerunning tests; the root separately ran
the complete test and strict-Clippy commands.

## Verified repairs

### End inheritance

`resolve_region_end` resolves `next:null` recursively through declared
semantic parents with tri-state cycle detection. It is independent of
`BTreeMap` and source-ID order. The deliberately reverse-sorted child/parent
fixture resolves to the expected five-frame path.

### Parent and interval consistency

Direct-parent containment and pairwise laminarity checks jointly reject
crossing annotations and nested regions whose declared parents make them
siblings. Therefore the set of regions covering a node is exactly an ancestor
chain, making the current path scan equivalent to following declared parents.

### Source-root contiguity

`source_root_layout` derives each node's root through validated source parents
and rejects return to a closed root before any interval slice is formed. This
closes the malformed interleaving panic.

### Complete near-name reporting

`find_near_name_candidates` has no 25-pair truncation and uses character counts
consistently with Unicode-scalar Levenshtein distance. Tests cover more than 25
candidates, a formerly omitted late pair, and a multibyte pair.

### Depth-mass equality

The runtime rejects a workspace whose selected-view depth mass differs from
folded pprof sample mass. The metric mapping agrees with profile construction
for operations, tokens, files, network, and time, and the integration test
exercises all five.

### Structured issues and scope

The reviewer verified non-null exclusive end, session ownership, tool count,
and child counts in the coarse-span fixture. The sole product output remains
pprof; JSON is command status and the existing trace/folded files remain
workspace intermediates. No frontend, alternate artifact, backend framework,
or forced-depth rule was introduced.

## Blockers

None.

## Nonblocking observations

- The depth-mass equality primarily guards future metric/projection drift; it
  does not prove semantic path correctness by itself.
- Path application, pairwise interval validation, and lexical matching are
  nonlinear in region/tag count. They are acceptable for the fixed
  15,338-node population, but the fresh complete run must measure CLI
  time/RSS rather than extrapolate.

