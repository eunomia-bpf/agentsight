# Step 0077 entry: aggregate-aware annotation convergence

Timestamp: 2026-07-23T23:36:16-07:00
Outer gate: EXPERIMENT
Branch at entry: `research/semantic-flamegraph-artifacts-v2`
Commit at entry: `6a59433da4a755878fd2db4aac4de46efdbf5e51`

## Why this step exists

The current automatic backend produces valid variable-depth operation paths,
and the current paper reports complete RQ1--RQ4 experiments. However, the
annotation path is still effectively one-pass: an automatic backend creates
boundaries and names, then the CLI immediately materializes a profile. The
backend does not see the aggregate shape it created. Consequently, synonymous
names can remain separate across sessions, one-off operations can fragment
the aggregate, and a locally plausible hierarchy can still be unhelpful as a
cross-session profile.

This step implements and evaluates the smallest feedback mechanism discussed
with the user:

> generate -> diagnose the aggregate -> reread only implicated source
> context -> revise -> regenerate

The mechanism remains advisory. It does not impose a target depth, force a
merge, replace the automatic backend, add a frontend, or create any product
artifact other than the final pprof profile. The annotation workspace remains
the existing three-file model: `trace.jsonl`, `annotation.json`, and
`stacks.folded`.

## Fixed paper questions

This step does not rename or replace any paper-level research question:

1. **RQ1 — resource attribution:** whether semantic profiling exposes where
   agent resources are spent.
2. **RQ2 — real-problem localization:** whether semantic operations help
   prioritize operations associated with real failures.
3. **RQ3 — automatic structure:** whether operation structure can be recovered
   automatically.
4. **RQ4 — cost:** the time and token cost of automatic construction and
   iterative refinement, as well as deterministic pprof materialization.

Experiment 001 first tests the product-facing convergence loop on the two
already adopted real case-study populations. Later experiments may reuse the
same fixed mechanism for RQ3 standard scoring and RQ2 downstream localization.
No paper number changes until the corresponding complete run and independent
result review are finished.

## Research and product constraints

- The source traces, case populations, and user questions remain fixed.
- A subagent is an automatic Agent backend, not a human annotator.
- A backend may revise only `annotation.json`; the CLI derives the updated
  trace paths, folded projection, diagnostics, and `.pb.gz`.
- Tags remain one to three meaningful words, action first where possible.
- Depth is variable and never prescribed.
- Every source node remains covered and every additive sample remains
  conserved.
- Each iteration is retained as an auditable Markdown report with input,
  finding, local context read, annotation changes, output, and cost.
- Cost includes wall time and token/input volume for first-pass annotation and
  each local revision, not merely final pprof serialization time.
- Standard B-cubed and boundary F1 remain the primary RQ3 structure metrics;
  downstream MAP remains the primary RQ2 decision metric. Fragmentation and
  depth diagnostics are explanatory product measurements, not substitutes.
- No branch change, frontend, renderer in the product path, frozen packet,
  alternate output format, or new backend abstraction is introduced.

