# Step 0071 report: update every RQ to the current algorithm

Timestamp: 2026-07-23T03:04:00-07:00
Outer transition: EXPERIMENT → WRITE
Status: COMPLETE

## Objective

This step answers the user's instruction that every paper RQ use the latest
accepted algorithm and current AgentPProf binary. It does not change the
thesis, the four RQs, their workloads, or their standard metrics. The work
began with an evidence-currency audit so that “latest” meant a complete
same-population replay rather than a new benchmark selected for a better
number.

## Completed experiment work

### RQ1 — multi-resource attribution

The current `agentpprof 0.2.37` release replayed the fixed three-run Git
annotation workspace at operation and token widths. The two resulting pprof
files are byte-identical to the paper inputs:

- operations:
  `325a9d1cabd0e6b8946722f90dfa1c5f1c5bd9a9313add78e46329dc645485e6`;
- tokens:
  `d23b7b68314da5477118154dc2370b4d2d3603740eae7ae7bde24007c341293a`.

The replay conserves 489 operations and 4,558,192 provider-reported tokens.
The focused `diagnose authentication` subtree contains 105 operations and
2,103,587 tokens, so it is 21.47% of operation count but 46.15% of token
weight. This is the current RQ1 case evidence; no replacement attribution
experiment was introduced.

### RQ2 — correspondence to real problems

The current release replayed the complete final automatic candidates for
AgentProcessBench, HINTBench, and TraceElephant. Every `per-query.jsonl` and
`summary.json` is byte-identical to Step 0070. Standard MAP therefore remains:

| Workload | Agent+Evidence | Raw action | Difference |
|---|---:|---:|---:|
| AgentProcessBench | 0.790615 | 0.773 | +0.017 |
| HINTBench | 0.432392 | 0.281 | +0.151 |
| TraceElephant | 0.259313 | 0.121 | +0.138 |

The separate population case remains the complete 440-trajectory
AgentRewardBench collection. Recovery exposure has AP 0.634 at expert-looping
prevalence 0.398, with a positive task-cluster interval over prevalence. The
paper does not claim causal diagnosis or superiority over the registered
fixed-chain detector.

### RQ3 — automatic operation structure

Experiment 001 applied the current action-first operation identity to all
405 CodeTraceBench sessions, 20,866 operations, and 5,752 adopted A2 marks.
The source-only mapping reduces 5,537 open names to 1,434 reusable two- or
three-word identities. A boundary-safe refinement reduces 717 initial adjacent
display-path collisions to zero without changing a temporal occurrence or
boundary.

The current complete result is ordinary B-cubed F1 0.704113 and exact adjacent
boundary F1 0.393916. Multi-resolution recurrence obtains 0.662740 and
0.265571; raw action obtains B-cubed F1 0.541. The paired task-cluster interval
for A2 minus recurrence B-cubed F1 is [0.021367, 0.060596]. This is a genuine
complete-population improvement from the adopted Agent segmentation. The
name-only replay intentionally preserves that score rather than manufacturing
an increase.

### RQ4 — current profiling cost

Experiment 002 rebuilt `agentpprof 0.2.37` from
`db465c32b312ce96f466a3975ede7d73525855fc` and completed the full public
matrix: five input sizes, semantic and raw-action construction, and three
repetitions per cell, for 30/30 valid pprof outputs.

The 27,765-operation union takes 1.16 seconds median and 465.16 MiB maximum
RSS. Throughput is 23,935 operations/s; the semantic descriptive fit has slope
0.041825 ms/operation and R² 0.999679. Relative to the matched raw-action
construction, the union adds 0.19 seconds (19.6%) and 5.25 MiB (1.14%).

The same binary completes six latest-A2 runs. Operation width takes 0.79
seconds median and token width 0.81 seconds, with at most 307.32 MiB RSS and
exact masses of 20,866 operations and 494,862,929 tokens.

## Figure regeneration and visual inspection

The paper's focused long-horizon panel was regenerated directly from the
current RQ1 token pprof using:

```bash
python3 docs/visexp/r221_visual_gallery.py \
  --profile .agentsight/experiments/rq1-current-replay-v1/profiles/git.tokens.pb.gz \
  --out docs/visexp/out/r221-pprof-renderer-v1/git-authentication.tokens.svg \
  --sample-index tokens \
  --focus diagnose_authentication \
  --title 'Where did the Git agents spend their token budget?' \
  --subtitle 'Three independent runs · shared semantic hierarchy · 4.56M provider-reported tokens'
```

The renderer read 105 positive pprof samples with total weight 2,103,587,
rendered maximum stack depth eight, and preserved the existing paper SVG and
PNG byte-for-byte. Visual inspection confirmed:

- a clear shared task path before the branch;
- variable-depth hypothesis and control branches;
- LLM-call and tool-call leaves beneath semantic operations;
- readable one-to-three-word action labels;
- a visible token concentration under authentication diagnosis.

The figure therefore supports a concrete user question rather than merely
showing that a hierarchy exists.

## Failures found and repaired

1. The initial adapter plan did not specify an executable reconstruction or
   distinguish temporal occurrence identity from cross-session display
   identity. Independent plan review rejected it; the final adapter
   independently expands all operations from marks and states both identities.
2. Naive short-name canonicalization erased 717 visible adjacent distinctions.
   A source-only, action-first, fail-closed refinement removed all collisions.
3. The product correctly rejected assigning one display name to multiple
   semantic IDs. The adapter now derives one stable ID per canonical name.
4. The old RQ4 evaluator requested JSON output, which the pprof-only product
   rejects. The evaluator now emits only `.pb.gz` and validates each file with
   stock `go tool pprof`.

These are implementation or compatibility repairs. None changes an RQ,
benchmark, target, metric, or hypothesis.

## Final decision

All four RQs now point to the current algorithm and current binary. The paper
may report the stronger A2-versus-recurrence structure result, the complete
automatic-versus-raw RQ2 gains, the current repeated-task attribution case,
and the new full RQ4 measurements. It may not claim that name canonicalization
alone increases B-cubed, that the differential case is causal, or that the
1,434 identities are gold semantic classes.

The next outer gate is REVIEW: inspect the complete paper against these raw
results and repair only factual, terminology, figure, or presentation
inconsistencies.

## Validation

- `python3 -m unittest script/test_canonicalize_operation_marks.py
  script/test_rq2_canonical_tag_compare.py`: eight tests pass.
- `cargo test --manifest-path agentpprof/Cargo.toml`: 78 tests pass across the
  unit and CLI integration suites.
- `make -B -C docs/paper`: succeeds and produces a 12-page AAAI-format PDF
  with no undefined reference, undefined citation, or overfull-box warning.
- Native-resolution inspection of PDF pages 9 and 10 confirms that both case
  figures fit the page, retain readable hierarchy labels, and match their
  captions.
