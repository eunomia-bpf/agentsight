# Full result: stable-ID operation marks and two collection case studies

Timestamp: 2026-07-22T00:52:00-07:00
Status: complete for the interface and two fixed collection case studies

## Implemented interface

AgentPProf now accepts one `--operation-mark-file`. The file declares:

- the source sequence field;
- the replay-stable source operation-ID field;
- one shared map from semantic operation IDs to unique display names; and
- sparse per-sequence marks containing a start source ID and a full semantic
  operation-ID path.

AgentPProf applies mappings, then marks the complete source sequence, then
applies query filters. Each source operation inherits the latest path in its
sequence. Repeated `operation` field values become variable-depth frames. The
CLI rejects ambiguous source fields, duplicate source IDs, missing first marks,
unknown or out-of-order marks, empty paths, unknown semantic IDs, duplicate
display names, stacks that omit `operation`, and simultaneous recurrence
induction. Profile specs resolve the mark file as a scalar path. The sole
product output remains one `.pb` or `.pb.gz` pprof.

## Agent annotation

The current root Agent read the complete indexed summaries for four real
AgentCap Codex review sessions. It chose 64 semantic transition IDs and 29
shared semantic operation names over all 326 source operations. No regular
expression or source-field transition selected a semantic boundary. The path
depth distribution at transition points is:

| Depth | Marks |
|---:|---:|
| 3 | 24 |
| 4 | 39 |
| 5 | 1 |

The source mark input is retained under the ignored experiment directory at
`.agentsight/experiments/rq3-recursive-operation-segmentation-v1/agentcap-agent-marks.json`.
The complete source operations remain `/tmp/agentcap-selected-ops.jsonl` in the
local experiment environment.

## Pprof construction

Command:

```text
cargo run --quiet --manifest-path agentpprof/Cargo.toml -- \
  --operation-file /tmp/agentcap-selected-ops.jsonl \
  --operation-mark-file .agentsight/experiments/rq3-recursive-operation-segmentation-v1/agentcap-agent-marks.json \
  --view operations --deterministic-output \
  --output docs/visexp/out/agentcap-agent-recursive-v1/agentcap-review-operations.pb.gz
```

The output contains all 326 operations, 62 unique stacks, and no warning. Its
size is 7,410 bytes and its SHA-256 is
`6c086ac1f33cb5b6d85ad20a0bdb0939ae66d0c19b55a040c11f9a1e686835c9`.
`go tool pprof -top`, `-tree`, `-peek`, and `-focus` all read it successfully.

## Case study 1: repeated-review collection

The protocol and four questions are fixed in `case-study-protocol.md`.

### Q1 — Effort allocation

The four task roots contain 80 R024, 75 R025, 76 R035, and 95 R081
operations. Whole-profile cumulative operation totals expose the main shared
responsibilities: verifying requested fixes 125, validating experiment evidence
55, establishing review scope 51, inspecting implementation 37, inspecting
experiment results 37, and auditing claims/documentation 33.

### Q2 — Review-to-fix evolution

Fix verification accounts for 125/326 operations (38.3%): 20 R024, 32 R025,
23 R035, and 50 R081. Its children contain 30 scope-establishment operations,
21 fixed-artifact validations, 15 fix inspections, 14 fixed-documentation
audits, 14 focused-test operations, and smaller task-specific work.

### Q3 — Conclusion path

All four sessions eventually contain a terminal conclusion. The shared
`Report review conclusion` leaf contains eight operations, including four under
fix verification. Six earlier operations identify blocking findings: three in
R025 and three in R035; the R035 blocker is nested under the stale-documentation
path. The case therefore does not show an entire high-cost session without a
conclusion. It does separate large evidence-gathering paths from small
conclusion-bearing paths.

### Q4 — Recurrence and exceptions

Shared operation IDs aggregate common review work across all tasks. Task-specific
deep paths remain visible: R024's evaluator-deviation operation contains seven
action-semantics and three banking-fallback operations; R035 contains nine
stale-documentation operations; R081 contains five reference-corpus inspection
and five validation operations; R081 also contains seven operations diagnosing
a test-environment failure.

## Case study 2: aggregate bad-good differential collection

The second protocol is fixed in `case-study-2-protocol.md`. It reuses the
complete, independently reviewed Step 0063 AgentRewardBench run rather than
selecting one pair: 440 real trajectories across 125 mixed-outcome tasks form
338 complete bad-good pairs. The collection contains 202 distinct successful
and 238 distinct unsuccessful sessions. Pair formation reuses trajectories
within a task, so all collection statistics are explicitly pair-occurrence
weighted.

All 338 bad members and 338 good members are folded into one signed profile:

```text
docs/visexp/out/agentreward-diff-pprof-v1/
  agentreward-338-pairs-bad-minus-good.operations.pb.gz
```

The 125,865-byte artifact has SHA-256
`cb7a9b6f63c6ad88d2c88dca35312d6463f33308391710e876d08f8db9b13ccc`.
It represents 7,366 bad-side and 3,780 good-side operation occurrences. Exact
full-stack cancellation leaves 7,103 positive bad-only/excess occurrences and
3,517 negative good-only/excess occurrences over 4,140 differing stacks. Stock
pprof reports percentages over the 11,146 absolute source occurrences, not a
success probability.

### Q1 — Collection-level excess work

The largest bad-side result paths are `progress` (+1,825) and exact
action-state `repeated` (+1,261). These do not mean progress causes failure:
they show that unsuccessful pair members contain substantially more continuing
and repeated work. The major action-level cumulative excesses include click
(+2,311), scroll (+520), and no-op (+383). On the good side,
`send_msg_to_user` has a cumulative difference of -100.

### Q2 — Repetition and failure concentration

Focused pprof queries retain concrete failure families rather than merging
them into one scalar error rate. Bad-side excess includes click-on-invisible
element (+148), click timeout (+129), stopped execution (+92), fill applied to
a non-input element (+57), select-option applied to a non-select element (+46),
and a missing element ID (+39). The repeated-result excess decomposes into
click (+639), no-op (+356), and scroll (+277) cumulative paths, while smaller
negative children remain visible where successful members repeat more.

### Q3 — Completion paths

Successful members contain more terminal (-92) and conclusion (-67) result
occurrences. Within `send_msg_to_user`, conclusion contributes -69 and repeated
work contributes -17. The sign therefore separates completion-bearing paths
from bad-side excess work without placing the hidden outcome label in an
operation frame.

### Q4 — Value beyond a scalar

Step count remains the strongest tested scalar discriminator on this population
(pairwise accuracy .7633; trajectory ROC AUC .7517). The aggregate profile is
not proposed as a better classifier. Its additional value is localization: the
same collection exposes whether excess work is repetition, waiting/no-op,
wrong-widget interaction, timeout, stopping, or missing completion, and stock
pprof can descend from each family to action and object frames. AgentRewardBench
does not provide a gold semantic hierarchy, so this case supports broad
differential profiling and path exposure rather than semantic-stack accuracy
or causal diagnosis.

## Verification

- `cargo fmt --check`: pass.
- `cargo test --locked`: pass, 68 tests total across unit and integration
  targets (54 + 3 + 9 + 2).
- `cargo clippy --locked --all-targets -- -D warnings`: pass.
- `git diff --check`: pass.
- `make` in `docs/paper`: pass; final PDF is 10 pages and has no unresolved
  citation/reference or LaTeX error recorded in the final log.
