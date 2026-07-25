# Task spec: fine-grained decomposition of the step-0080 profile-guided reader

You are an autonomous analysis agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
This is OFFLINE analysis of already-collected data. No LLM calls, no new
experiment, no modification of any existing file.

## Data (all read-only)

- Step 0080 (profile-guided reader):
  `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/`
  — `raw-results.json` (per-query ap dict {profile_reader, direct_reader,
  local_agentprof, local_only}, target_operation_ids, stratum, costs),
  `raw-responses/<query>.json` (stage-1 selections, completed_ranking),
  `packets-stage1/`, `packets-stage2/`.
- Step 0079 (full-trace reader): `.../step-0079-20260724T235753-0700/experiment-001/raw-results.json`
  and its raw-responses (completed rankings, reader_rank_of_target).
- Frozen group mapping:
  `.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (field `source_preserving_agent`).

## Questions (answer ALL, each with exact numbers)

1. **Loss decomposition.** For each of the 220 queries, determine whether
   every target operation's group was among the stage-1 selected groups
   ("index hit") or not ("index miss").
   - Report: hit count/rate; MAP conditional on hit; MAP conditional on miss;
     the counterfactual MAP if every miss query were scored with the step-0079
     direct-reader AP instead (upper bound of fixing stage 1); and the share
     of the total (0.502-0.455) gap attributable to misses vs within-hit
     ranking differences.
2. **Per-stratum table.** MAP of profile_reader, direct_reader,
   local_agentprof per stratum (Captain/Magentic/SWE-agent × benchmark),
   with query counts, index-hit rate, and mean content-opened fraction per
   stratum. Identify where the profile reader loses most and where it ties
   or wins.
3. **Win/loss anatomy.** Count queries where profile_reader AP > / = / <
   direct_reader AP. For the wins, report mean AP gain and mean
   content-opened fraction (does reading less ever help?). List the 5
   largest wins and 5 largest losses with query_id, both APs, index
   hit/miss, and #groups.
4. **Index difficulty correlates.** Spearman correlation of per-query
   index-hit (0/1) and profile_reader AP against: #operations, #groups,
   largest-group size, target group size, content-opened fraction. Simple
   table, no modeling.
5. **Budget sensitivity (descriptive).** From stage-1 selections: how often
   were exactly 5 groups selected (budget saturated)? For miss queries,
   what rank would the target group have needed (was it the 6th-10th
   plausible choice, or completely absent from consideration)? If the
   stage-1 response includes an ordered selection, use that order; else
   report saturation only.

## Deliverables (all inside THIS analysis-001 directory)

- `decomposition_analysis.py` — one script, stdlib+numpy/scipy only,
  deterministic, rerunnable.
- `analysis-results.json` — every number behind the report.
- `analysis-report.md` — the five sections above, each led by its headline
  number, plus a short "what would most improve MAP" conclusion strictly
  limited to what the data shows.

## Hard constraints

- NEVER modify/delete/move any existing file; write only into this directory.
- NEVER run git commands. NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- If a needed field is absent (e.g. stage-1 selections unordered), say so in
  the report rather than approximating silently.
