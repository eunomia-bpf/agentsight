# Task spec: query-aware direct-reader baseline on TraceElephant (RQ2)

You are an autonomous engineering agent executing ONE fixed experiment inside
the repository `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Follow this spec exactly. Do not redesign the experiment.

## Scientific question (fixed — do not change)

How well does a query-aware LLM Agent that directly reads a trajectory's
source-visible evidence rank the independently annotated responsible
operations, compared with the existing RQ2 conditions (Direct-only,
Direct+AgentProf)? This is the strongest current-practice competitor for RQ2
(real-problem localization). It is query-specific, whereas the AgentPProf
hierarchy is constructed once and replayed; that asymmetry must be disclosed,
not hidden.

## Step 1: Locate the frozen TraceElephant RQ2 inputs (read-only)

The existing RQ2 evaluation used the complete TraceElephant workload: 220
target-bearing queries (one trajectory each) plus zero-positive trajectories.
Find the frozen inputs and scoring code by inspecting (READ ONLY):

- `script/` — files matching `rq2_*` (e.g. `rq2_current_agent_local_first.py`,
  `rq2_canonical_tag_compare.py`) reference the data locations and implement
  the exact AP/MAP scoring.
- `docs/tmp/build-and-evaluate/step-0072-*/` — the information-matched RQ2
  evaluation step; its reports name the exact data paths and per-query AP
  files for the existing conditions.

You need per trajectory: (a) the operation sequence with stable source IDs,
(b) the source-visible content the existing pipeline saw, (c) the annotated
target operations, (d) the stored per-query AP of Direct-only and
Direct+AgentProf for the paired comparison. If any of these cannot be found,
STOP and write what you found into `results.md` instead of improvising.

## Step 2: The direct-reader condition (fixed protocol)

For each target-bearing trajectory:

1. Build one packet: the benchmark's query/task text, plus every operation's
   source ID and its source-visible content (same visibility boundary as the
   existing pipeline — no target labels, no outcome labels, no gold answer).
2. Invoke the reader ONCE per trajectory as a single-turn model call:
   `grok -p "<packet + instruction>" --output-format plain`
   The instruction requires the reader to return a ranked list of source
   operation IDs (most likely responsible first), covering at least every
   operation it considers plausibly responsible, as strict JSON.
3. Parse the ranked list; operations not ranked by the reader are appended in
   original trace order after the ranked ones (deterministic completion).
   Malformed output gets ONE retry with a format reminder; a second failure
   scores that query with the deterministic original-order ranking and is
   counted in a reported failure tally.
4. Record wall time and packet size (characters and, if available, tokens)
   per query.

Fixed decoding settings; no per-query prompt tuning. Validate the harness on
at most 3 queries, then run ALL 220 target-bearing queries. Zero-positive
trajectories are excluded from MAP exactly as in the existing protocol.

## Step 3: Scoring (identical to existing RQ2)

- Non-interpolated per-query AP over the reader's operation ranking against
  the same annotated targets used by the existing conditions.
- MAP = arithmetic mean over the 220 target-bearing queries.
- Paired comparison: direct-reader vs Direct-only and vs Direct+AgentProf
  using 10,000 paired resamples of trajectory clusters within
  benchmark-defined strata (same procedure as step 0072; reuse its stored
  per-query AP values).

## Deliverables (all inside THIS directory)

- `direct_reader_eval.py` — complete harness (calls the grok CLI).
- `packets/` — the exact packet sent per query (or a deterministic script
  that regenerates them).
- `raw-responses/` — every raw reader response.
- `raw-results.json` — per-query AP for the reader, plus the paired deltas.
- `results.md` — population description, exact input provenance, MAP with
  intervals, failure tally, cost table (total and per-query wall time and
  packet volume), and an honest interpretation. Disclose: reader model is the
  external grok family, different from the annotation backend; the reader is
  query-specific while the profile is constructed once.
- `execution-log.md` — commands and wall time.

## Hard constraints

- NEVER modify, delete, or move any existing repository file.
- NEVER run any git command.
- NEVER touch `docs/agentpprof-paper/` or `docs/paper/`.
- No target or outcome label may appear in any reader packet.
- Complete population run; the ≤3-query harness validation is never reported
  as a result.
