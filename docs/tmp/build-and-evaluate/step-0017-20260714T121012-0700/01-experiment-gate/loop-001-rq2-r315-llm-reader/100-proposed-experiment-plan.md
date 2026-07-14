# Proposed Experiment Plan — R315 Rank-Hidden LLM Reader

## 1. Paper-Level Question and Tested Hypothesis

**Paper-level RQ:** RQ2 — Does profiler output correspond to real problems?

**Tested hypothesis H17:** On the complete existing six-task R315 matrix, under an identical rank-hidden packet presentation and an exactly three-group selection budget for non-flat views, a fixed deterministic Qwen3.6-27B reader using operation-stack packets has higher selected-positive recall and precision than the same reader using fixed-session packets.

This hypothesis concerns one reader, six tasks, and existing top-five packets. It does not answer all of RQ2 and does not test remediation, human productivity, or general model capability.

## 2. Why This Experiment Has Paper Value

Step 0016 found that another compactness benchmark would repeat evidence already in the paper. R315 is the smallest existing artifact that tests a downstream decision: an analyst must choose which visible groups to inspect, and an independent hidden key scores whether those groups contain the real problem. A positive result would connect the profile to bounded AI-assisted prioritization; a mixed or null result would show that current packet semantics do not yet improve that decision.

The experiment is admitted instead of the proposed TraceElephant counterfactual because it reuses a complete ready-to-run packet set rather than building replay/intervention machinery across three agent systems.

## 3. Inputs and Reuse

### Existing inputs

- `docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json`
- `docs/visexp/out/analyst-study-protocol-r315/hidden-scoring-key.json`
- `docs/visexp/out/analyst-study-protocol-r315/study-protocol.json`
- `docs/visexp/out/analyst-study-readout-r316/trial-scores.csv`
- the local OpenAI-compatible endpoint at `http://127.0.0.1:8012/v1`
- model `/home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf`

### Complete population

- six tasks from four public dataset families;
- three views per task: flat, fixed-session, operation-stack;
- 18 unique task-view packets total;
- one fresh model context per unique packet;
- six paired tasks are the scientific units.

The 144 R315 assignment rows are not executed. They repeat the 18 packets for a planned 24-human-participant design and would create pseudo-replication for one fixed LLM.

## 4. Reader Presentation

For every packet, the collector creates a presentation using only the existing visible fields:

1. retain the task's natural-language problem statement and all existing group content;
2. remove the packet's `view` label from the model-visible request;
3. remove each group's exposed `rank` field;
4. order groups lexicographically by their original 12-hex-character `group_id`, a fixed visible-only order;
5. replace the original IDs in the model-visible request with opaque sequential aliases `G01` through `G05` after sorting, retaining the visible-only alias-to-original-ID map in the collection record;
6. retain stack text/frames, aggregate counts, visible field summaries, and operation/session examples; and
7. never load or include the hidden scoring key during collection.

This is a presentation control, not a new profile, ranker, dataset, or feature. The model never sees original IDs, view labels, or rank fields; it returns aliases that collection maps back to original IDs using visible data alone. This prevents the model from receiving credit for copying the existing query-aware order or an ID/ordinal cue. Preflight must verify that no original ID, original rank, or view label occurs in the serialized model request. The original R316 visible-order top-three policy remains a separately reused ranker control.

## 5. Fixed Reader Protocol

### Model and decoding

- server binary: `/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server`;
- observed server command: `llama-server -m /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf --host 127.0.0.1 --port 8012 -ngl 99 -c 131072 -np 4 --jinja --reasoning off --reasoning-budget 0`;
- endpoint: local llama.cpp OpenAI-compatible chat API at `http://127.0.0.1:8012/v1`;
- request `model`: `/home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf`, the exact value returned by `/v1/models`;
- temperature: `0`;
- seed: `20260714`;
- maximum generated tokens: `1024`;
- thinking/reasoning: disabled by the server's `--reasoning off --reasoning-budget 0` configuration and request field `chat_template_kwargs={"enable_thinking": false}`;
- at most three identical attempts for any transport failure, non-JSON response, or schema-invalid response, including wrong selection count, duplicate alias, or out-of-packet alias;
- retries use the identical prompt and decoding parameters and are not independent observations.

### Prompt contract

The fixed system prompt says the reader is diagnosing one visible profile packet, must use only provided fields, and must not assume any hidden labels. The user prompt supplies the target problem and rank-hidden, alias-labeled group records. For non-flat packets the reader must return exactly three distinct valid aliases, ordered from most to least likely to contain the target phenomenon. For flat packets it returns the sole alias. It also returns short visible-field evidence and a 1–5 confidence score, but evidence/confidence are descriptive rather than primary endpoints.

### Response schema

One JSON object:

```json
{
  "selected_group_aliases": ["G01", "G02", "G03"],
  "confidence": 1,
  "visible_evidence": ["brief visible-field reason"]
}
```

A valid response contains the required number of distinct aliases and every alias appears in the visible packet. Every transport, JSON, or schema failure uses the same identical-request limit of three total attempts. Any persistently invalid or missing cell makes the complete experiment `INVALID`: no cell or task is dropped, no response is imputed or manually repaired, and no paired verdict is computed over a reduced matrix.

## 6. Separation of Collection and Scoring

The thin runner has two explicit modes:

- `collect`: reads visible packets only, creates rank-hidden requests, calls the model, validates visible IDs, and writes locked raw request/response records;
- `score`: after all 18 collection cells finish, reads the locked responses and the existing hidden key, then computes metrics.

The scoring key is never imported by collection. No Git hash, packet seal, attestation, manifest, or private key is introduced; this is ordinary two-phase experiment hygiene rather than a research control protocol.

### Frozen runner, commands, and output paths

- runner: `script/r315_llm_reader_eval.py`
- experiment root: `.agentsight/experiments/r315-llm-reader-rq2-v1/`
- preflight output: `.agentsight/experiments/r315-llm-reader-rq2-v1/preflight/`
- full output: `.agentsight/experiments/r315-llm-reader-rq2-v1/full/`

Preflight collection command:

```bash
python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 \
  --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v1/preflight \
  --packet-id satraj_unsafe::operation_stack \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 3
```

Full collection command:

```bash
python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 \
  --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v1/full \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 3
```

Full scoring command, run only after full collection returns 18 valid cells:

```bash
python3 script/r315_llm_reader_eval.py score \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --hidden-key docs/visexp/out/analyst-study-protocol-r315/hidden-scoring-key.json \
  --ranker-scores docs/visexp/out/analyst-study-readout-r316/trial-scores.csv \
  --responses .agentsight/experiments/r315-llm-reader-rq2-v1/full/responses.jsonl \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v1/full
```

The collection command has no hidden-key or ranker-score argument. The scoring command performs no model call.

## 7. Baselines and Controls

### Primary baseline

The same fixed reader on the fixed-session packet for each task. Operation-stack and fixed-session requests use identical prompting, rank hiding, ordering, decoding, and selection budgets.

### Flat lower bound

The same reader on the one-group flat packet. Flat necessarily selects the full group and is interpreted as complete but non-selective, not as an accuracy competitor with the same granularity.

### Existing ranker control

Reuse `docs/visexp/out/analyst-study-readout-r316/trial-scores.csv`. For `top_k=3`, deduplicate its repeated assignment rows by `packet_id`, verify that all repeated rows for a packet have identical selected IDs and scores, and retain exactly one deterministic visible-order control for each of the 18 task-view packets. Assignment repetitions are never counted as observations. This establishes what the pre-existing query-aware packet ordering already provides without reader reasoning; it is not rerun or tuned.

Interpretation is explicit:

- if the rank-hidden reader improves over fixed-session but not over operation-stack's visible-order control, the result supports bounded profile usability but not added reasoning beyond the ranker;
- if it also improves over the operation-stack ranker control, it supports reader use of group content beyond order;
- if it fails against fixed-session, H17 is unsupported regardless of flat or ranker outcomes.

## 8. Endpoints and Decision Rule

For every selected set, reuse the hidden-key definitions already implemented by R316:

- selected positive operations;
- selected-positive recall;
- selected-positive precision;
- inspected operation work fraction;
- positive lift;
- positive/high-lift hit as descriptive secondary outcomes.

### Primary paired outcomes

For each of the six tasks compute operation-stack minus fixed-session deltas in:

1. selected-positive recall; and
2. selected-positive precision.

Report every task, the median paired delta, and the number of improved/tied/worse tasks. Inspected work is reported alongside both outcomes for every task and by view.

### Predeclared verdict

- **SUPPORTED:** both recall and precision have positive median paired deltas and each improves on at least four of six tasks.
- **MIXED:** exactly one primary outcome satisfies that rule, or both have positive medians but either improves on fewer than four tasks.
- **UNSUPPORTED:** neither primary outcome has a positive median paired delta, or both improve on at most three tasks.
- **INVALID:** the complete 18-cell matrix cannot be collected/scored under the fixed protocol.

No p-value is claimed from six heterogeneous tasks. Repeated decoding, bootstrap resampling, cutoff search, and post-hoc scalar utility are excluded.

## 9. Real Preflight

Run `satraj_unsafe::operation_stack`, a non-flat five-group packet, through `collect` only. The preflight checks:

- endpoint/model availability;
- rank, view, and original-ID removal from the serialized model request;
- stable visible-only alias mapping and lexicographic original-ID ordering;
- deterministic lexicographic group ordering;
- absence of hidden fields and hidden key access;
- valid strict JSON;
- exactly three distinct in-packet aliases mapped back to visible original IDs;
- raw request/response persistence; and
- successful identical-request retry behavior only if needed.

The preflight is a path check and is never included as scientific evidence. Before the full run, its output directory is separate; the full matrix recollects this cell once under the final plan.

## 10. Full Run

If preflight passes, collect all 18 unique packets once. The run is valid only when every cell has a valid response. Any persistent fixed-protocol failure makes the full matrix `INVALID` and ends scientific scoring. Otherwise invoke scoring once over the complete response set. Do not stop after favorable tasks or inspect the hidden key between requests.

Expected lightweight outputs:

- raw request/response JSONL;
- cell-level score CSV;
- task-paired comparison CSV;
- machine-readable summary JSON; and
- a Markdown result report.

These are generated evidence artifacts, not control contracts.

## 11. Threats and Claim Boundary

- One quantized local model is a fixed reader, not a population of AI analysts.
- Six tasks provide paired cross-task evidence but not broad statistical generalization.
- Packets contain only the existing top-five groups and do not test navigation of an entire unbounded profile.
- Removing rank tests content-based use and differs from the original human-facing R315 presentation; R316 retains the original-rank control.
- Flat has one group and is a non-selective lower bound.
- The result does not establish human productivity, time-to-answer, remediation, online deployment, automatic anomaly detection, or universal view dominance.

## 12. Stop Rule and Routing

This experiment runs once under the reviewed plan. A supported, mixed, unsupported, or invalid result is returned unchanged to independent result review. The hidden key cannot be used to revise the prompt, ordering, selection budget, model, dataset, or metric. Any changed scientific claim would require a new plan; RQ2 itself cannot be changed by this experiment.
