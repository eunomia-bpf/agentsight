# TraceElephant Source And Context Pre-Plan Analysis

**Started:** 2026-07-13T17:24:52-07:00
**Completed:** 2026-07-13T17:31:32-07:00
**Phase / step / gate:** BUILD_AND_EVALUATE / 0004 / EXPERIMENT
**Loop:** loop-001-rq2-traceelephant
**Parent:** EXPERIMENT gate entry
**Status:** dependency analysis complete; no model inference and no target values loaded into the planned builder

## Question And Entry

Before committing the fixed RQ2 experiment to a plan, this node asks whether
the official TraceElephant data and released diagnosis path can support one
complete target-blind AgentProf-versus-raw-action comparison on the available
local model. It specifically checks population completeness, released methods,
prompt construction, label separation, and the actual 32,768-token context
boundary. Download and schema checks are setup; they do not answer RQ2.

The root reread `docs/user-instruction.md` before this node. The work preserves
the exact thesis and four RQs, uses the complete real benchmark instead of a toy
subset, does not inspect or edit the submodule, and does not change a claim or
story. No current skill file was edited.

## Official Sources And Population

The official repository is the ignored read-only clone
`.agentsight/sources/TraceElephant` at commit
`0ce8abb2855de9f454f27f6b0795a4b7e6c8d5fc`. The official Hugging Face dataset
is `TraceElephant/TraceElephant` at Hub commit
`a78a57cdcdf74a080b1bec0f56f85228d86acbac`. Its downloaded `data.zip` is
596,610,649 bytes with SHA-256
`8e5df3e402abfa6666ae1b656a5d516395134163774b5da1a3abae99cb83a582`.

The archive contains exactly 220 `trace_metadata.json` and 220
`step_records.json` files, with exactly 5,960 ordered atomic steps:

| Official cell | Traces | Steps | Min--max steps |
|---|---:|---:|---:|
| Captain-Agent / AssistantBench | 12 | 187 | 8--54 |
| Captain-Agent / GAIA | 73 | 1,559 | 5--59 |
| Magentic-One / AssistantBench | 17 | 603 | 18--48 |
| Magentic-One / GAIA | 74 | 2,060 | 6--50 |
| SWE-Agent / SWE-Bench | 44 | 1,551 | 14--94 |
| **Total** | **220** | **5,960** | **5--94** |

All step IDs are unique and sorted within each trace. All steps expose an
`input` and `output`; 2,414 steps have a list-valued `tool_logs` field and the
remaining 3,546 have no list. Task-directory identifiers are unique across all
five cells, avoiding the released evaluator's first-match ambiguity.

The benchmark paper defines the decisive failure step as the earliest point at
which failure becomes inevitable under a role- and recoverability-aware
principle. It reports 220 expert-annotated failures drawn from 380 executions
over Captain-Agent, Magentic-One, and SWE-Agent, and motivates full execution
observability rather than output-only diagnosis. The primary source is
[Seeing the Whole Elephant](https://arxiv.org/abs/2604.22708); the released
repository and data are the executable sources for this experiment.

## Released Diagnosis Path

The one-click released `code/trace_locate/inference.py` exposes exactly three
prompting methods: `all_at_once`, `step_by_step`, and `binary_search`. The
paper also evaluates Static Agentic and Dynamic Agentic, but the public
one-click path does not expose a runnable implementation for those two methods.
They therefore cannot be treated as mandatory matched baselines without a new
official release.

Relevant released-code facts:

- `lib/utils.py:62-131` converts every official step into the history format;
- `lib/utils.py:468-501` defines the All-at-Once prompt;
- `lib/utils_parallel.py:32-110` runs one prediction per trace and parses one
  `agent_name`, `step_number`, and reason;
- `lib/utils_parallel.py:88-97` first tries the complete request/response trace
  and then falls back to response-only content on context overflow;
- `lib/utils.py:503-527` and `utils_parallel.py:178-296` implement the
  Step-by-Step prompt and stop at the first `Yes`;
- `utils_parallel.py:341-468` implements Binary Search, including random branch
  selection when a model response cannot be parsed; and
- `evaluate.py:73-137` is the first released point that needs
  `mistake_agent` and `mistake_step` values.

All-at-Once is the strongest simple released static prompt in the paper's
reported average step accuracy (28.1% with the reference outcome, versus 16.7%
for Step-by-Step and 12.9% for Binary Search). It also yields one common
target-blind predicted step per trace without introducing thousands of
different prefix prompts or an unseeded Binary Search fallback. It is therefore
the best released shared suspicion signal for the planned grouping comparison.

The paper's default “with ground truth” setting means a correct task answer or
test status is visible to diagnosis. That is not the hidden failure target:
`mistake_agent`, `mistake_step`, and `mistake_reason` remain scoring-only. The
plan will follow the official default because it is the stronger published
developer-facing setting and because both compared profile methods receive the
same signal and source fields.

The independent source auditor proposed excluding the reference outcome under
a stricter use of “target-blind.” The root does not adopt that interpretation:
the selected RQ forbids target failure labels, while the benchmark explicitly
defines with-reference and without-reference application scenarios and makes
the with-reference setting its default. The plan therefore calls this
**failure-target-blind**, exposes the same reference outcome to both conditions,
and does not add the without-reference scenario as a second experiment. Plan
review may still reject this choice if it makes the paper's intended RQ2 claim
scientifically invalid.

## Label-Isolation Boundary

The released loader returns `mistake_agent` and `mistake_step` in the same
Python object as visible fields even though inference does not use them. The
planned adapter must therefore not call that loader during construction. It
will read only this allow-list before terminal profile outputs exist:

- metadata: `task_instruction`, `ground_truth`, `agent_system_intro`,
  `agent_configuration`, and source directory/system identity;
- steps: `step_id`, `agent_id`, `agent_name`, `input`, `output`, and
  `tool_logs`.

Only a separate scorer phase may read `mistake_agent`, `mistake_step`, and
`mistake_reason`, after the shared model outputs, tag outputs, operation files,
and AgentProf profiles are terminal. The plan does not treat a Git hash, seal,
manifest, or other non-Markdown contract as the control mechanism; the adapter
uses ordinary process separation and the result review inspects the code path.

An independent read-only source audit identified two additional released-code
hazards. The current llama.cpp server describes overflow as “exceeds the
available context size,” while `lib/utils.py:276-280` recognizes only
`context_length_exceeded` or “maximum context length.” The unmodified runner
therefore returns `None` instead of reaching its fallback. In addition,
`evaluate.py:186-187` uses substring membership for correctness, so target step
`2` can incorrectly match prediction `12`. The adapter must call the uniform
response-only builder directly, retain transport and parse failures, and use
exact canonical equality in a separate scorer.

## Real Context-Window Measurement

The actual local server at `http://127.0.0.1:8012/v1` reports Qwen3.6-27B
Q4_K_M with a 32,768-token runtime context. The root reconstructed every
official All-at-Once prompt using the released formatter and prompt builder,
but with an allow-listed loader, then counted the real chat-templated tokens
through the server's `/tokenize` endpoint. No model inference ran and no target
value was printed or used.

| Prompt branch | Min | Median | P90 | P95 | Max | At least 32,768 |
|---|---:|---:|---:|---:|---:|---:|
| Full request + response | 9,061 | 168,197 | 557,396 | 940,910 | 3,419,904 | 184/220 |
| Released response-only fallback | 2,197 | 6,335 | 16,489 | 16,968 | 20,051 | 0/220 |

Even before reserving output tokens, 184 complete prompts exceed the runtime
context, with the longest more than one hundred times too large. Allowing the
released code to use full input for only 36 traces and response-only for 184
would make observability depend on trace length and system. The plan therefore
uses the released response-only prompt branch consistently for the shared
All-at-Once signal over all 220 traces. This is a declared source-code branch,
not silent truncation.

The proposed profile still uses bounded current-step input, output, role, and
tool information to derive its semantic fields. The raw-action baseline starts
from the same visible operation rows and shared All-at-Once hit signal; it
differs only in the grouping and propagation policy it chooses. Plan review
must decide whether that causal contrast is sufficiently clean.

The exact proposed tag prompt was materialized without inference and counted
through the same server tokenizer. Fixed batches of at most 20 source steps
produce 405 requests. Their prompt sizes range from 1,032 to 17,315 tokens
(median 9,896; P95 14,703); none reaches 30,720, leaving at least 2,048 tokens
for structured labels. The server exposes one inference slot, so model calls
must run with one worker. Profiling and bootstrap analysis may use separate CPU
workers after inference.

## Decision And Remaining Risk

Source admission passes. TraceElephant provides the complete official
population, independent decisive-step targets, real systems, and a released
target-blind prompt path. The actual context measurement rules out a naive
full-trace call but admits one consistent published fallback. The next node may
write a complete plan; no experiment inference or paper claim is authorized by
this dependency result.

The main unresolved scientific risks for plan review are:

1. whether a shared one-step All-at-Once signal plus semantic propagation tests
   AgentProf rather than merely the localizer;
2. whether the fixed role/intent/status tagger sees a fair bounded projection
   of each step and does not receive target information unavailable to the
   raw-action condition;
3. whether one headline raw-action baseline and the declared controls are the
   smallest credible comparison set; and
4. whether the macro-recall work metric and hierarchy score have an exact,
   target-independent definition before any scorer reads the 220 labels.

These questions are answered by the experiment plan and serial independent
plan reviews, not by more dependency checks.
