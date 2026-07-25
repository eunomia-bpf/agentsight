# Task spec: index-study replication on HINTBench (three conditions)

You are an autonomous engineering agent executing ONE fixed experiment inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Baselines to replicate (protocols are FROZEN)

- Full-trace reader: `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/`
- Semantic-skeleton two-stage reader (v1, WITH skeleton in stage 2):
  `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/`
- Raw-action-skeleton two-stage reader:
  `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/`

Copy/adapt their harnesses into this directory. The ONLY changes: workload
inputs (HINTBench), reader invocation (kimi instead of grok), and the
HINTBench group identities (below).

## Step 1: locate frozen HINTBench inputs (read-only)

From the step-0072 artifact family (`.agentsight/experiments/`): the
HINTBench source packets, operation projection with stable IDs, annotated
targets, stored per-query AP for `local_only` and `local_agentprof`
(rq2-current-agent-local-first-v1 covers all three workloads — find the
HINTBench rows), the semantic group mapping (`fixed-groups.jsonl`-family
file with `source_preserving_agent` for HINTBench), and the raw
information-matched identity (method-index.json `methods.raw.operation_leaves`
equivalent for HINTBench). Follow the provenance documented in
`script/rq2_current_agent_local_first.py`. HINTBench has 400 target-bearing
queries out of 536 test trajectories; zero-positive trajectories are
consumed but excluded from MAP, exactly as the paper protocol states.
If any required frozen input cannot be located, STOP and write results.md
explaining what you found.

## Step 2: reader

Reader = `kimi` CLI in single-turn prompt mode with FIXED flags you
document (e.g. `kimi -p <packet+instruction>`; use a prompt file if the
packet exceeds ARG_MAX headroom). One format retry per call; deterministic
fallbacks exactly as the frozen protocols (stage-1 fail -> largest 5
groups; stage-2/full fail -> original-order; tally everything).
DISCLOSE in results.md: the reader family differs from the TraceElephant
study (grok); every condition on THIS workload uses the same kimi reader,
and no cross-workload pooling is performed.
Parallelize with a bounded worker pool (document the worker count) so the
complete run finishes in reasonable wall time.

## Step 3: three conditions, complete population each

1. **Full-trace reader**: one call per query, complete source-visible
   trajectory, ranked operation IDs (step-0079 protocol).
2. **Semantic skeleton**: two-stage v1 (skeleton in both stages), <=5-group
   ordered selection, evidence for selected groups only (step-0080
   protocol).
3. **Raw-action skeleton**: identical, group identity = HINTBench
   information-matched raw path (step-0081 protocol).

No target/outcome/judge/localizer signal in any packet.

## Step 4: scoring and comparisons (frozen machinery)

- sklearn non-interpolated AP; MAP over the 400 target-bearing queries.
- Paired 10,000-draw trajectory-cluster bootstrap within benchmark-defined
  strata (use HINTBench's stratum definition from step 0072; document
  seeds): every pairwise delta among the three new conditions plus stored
  local_agentprof and local_only.
- Content-opened fraction and paired semantic-vs-raw content delta with
  interval (the step-0081 review's decision metric).
- Costs: wall seconds, packet chars, tiktoken o200k_base logical tokens per
  query for every condition.
- Index-hit rate for both skeleton conditions (target group among selected).

## Deliverables (all inside THIS directory)

`hint_index_study_eval.py` (or split per condition), `packets-*/`,
`raw-responses-*/` per condition, `raw-results.json`, `results.md` (with
the two registered hypotheses from 000-step-entry.md explicitly evaluated),
`execution-log.md`.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command (including `git stash`).
- NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- Complete 400-query runs for all three conditions; <=3-query validation
  never reported as a result.
