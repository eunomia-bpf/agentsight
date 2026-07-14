# Real Preflight And Independent Review: TraceElephant RQ2

**Node:** 005
**Timestamp:** 2026-07-13T19:11:14-07:00
**Phase / step / gate / loop:** BUILD_AND_EVALUATE / 0004 / EXPERIMENT / 001
**Parent:** [approved experiment plan](002-experiment-plan-20260713T173132-0700.md)
**Status:** REAL PREFLIGHT complete; independently reviewed `PASS`; FULL authorized

## Question And Entry

This node asks only whether the approved fixed-RQ2 TraceElephant experiment
can execute its real causal contrast end to end without answer leakage, proxy
profiling, or scorer-target ambiguity. It does **not** ask whether the tested
hypothesis is supported and cannot answer paper-level RQ2.

The selected RQ remains verbatim:

> **RQ2: Does Profiler Output Correspond to Real Problems?**

The paper's scientific contract, four RQs, thesis, story, baseline family,
metric meaning, workload coverage, and expected result relation are unchanged.
The current user instructions require a complete real-world experiment rather
than stopping after smoke tests, forbid narrowing the story around an
intermediate result, and designate the submodule narrative as read-only. This
node follows those instructions by treating the one-trace run as a path check
and proceeding to the complete 220-trace matrix.

## Inputs And Method

The real preflight used:

- the released TraceElephant data under
  `.agentsight/sources/traceelephant-data/extracted/data`;
- the official response-only trace localizer from the read-only TraceElephant
  source at `.agentsight/sources/TraceElephant/code/trace_locate`;
- Qwen3.6-27B Q4_K_M through the real OpenAI-compatible server at
  `http://127.0.0.1:8012/v1`;
- `agentpprof 0.2.37` from
  `agentpprof/target/release/agentpprof`;
- the reviewed thin adapter
  `script/traceelephant_profile_localization_eval.py`;
- seed `20260713`, one model worker, eight bootstrap workers, three permitted
  attempts, a 600-second request timeout, 1,024 localizer output tokens, and
  2,048 tagger output tokens.

The executed command was:

```bash
python3 script/traceelephant_profile_localization_eval.py preflight \
  --data-root .agentsight/sources/traceelephant-data/extracted/data \
  --official-code .agentsight/sources/TraceElephant/code/trace_locate \
  --base-url http://127.0.0.1:8012/v1 \
  --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out .agentsight/experiments/traceelephant-rq2-v1 \
  --model-workers 1 --bootstrap-workers 8 \
  --localizer-max-tokens 1024 --tag-max-tokens 2048 \
  --timeout 600 --attempts 3 --seed 20260713 --resume
```

The preflight selected the lexicographically first Captain-Agent / AssistantBench
failure,
`captain-runs-assistantbench/assistantbench_task_0_gpt-4o_8jqg5bbthx21`,
with all nine source steps. Its two real model requests, both primary profile
conditions, all declared controls, and all 200 matched semantic permutations
ran to terminal status. Raw and reconstructed evidence is under
`.agentsight/experiments/traceelephant-rq2-v1/`.

## Results And Raw Evidence

### Real model and source path

- Completion was exact: one trace, nine source steps, nine emitted operations,
  one terminal localizer output, and one terminal tag batch.
- Both real model calls succeeded on the first attempt without fallback.
- The official localizer selected `InformationExtraction_Expert`, step 5.
- The localizer request used 3,246 input tokens plus the 1,024-token output
  budget; the tagger request used 5,252 input tokens plus the 2,048-token
  output budget. Both are within the 32,768-token server context.
- The localizer request contains the official reference answer required by the
  released protocol but no `mistake_*` scorer annotation. The target-blind
  tagger request contains neither the reference answer nor scorer annotations.
- Request hashes were independently reconstructed from the official source at
  commit `0ce8abb...` and matched the archived requests.

The terminal run record is
`.agentsight/experiments/traceelephant-rq2-v1/run-preflight.json`; requests and
responses are under the sibling `requests/` and `responses/` directories.

### Real AgentProf causal contrast

Both conditions consumed identical count and shifted operations. The proposed
condition used
`system,role,intent,component,raw_action,status`; the sole headline raw
baseline used `system,component,raw_action`. The difference is therefore the
approved semantic organization rather than an extra trace, answer, operation,
tool, or scoring budget.

All four primary profiles were replayed through the actual AgentProf binary and
matched the stored stacks exactly. Independent reconstruction recovered:

| Condition | Leaves | Total count / shifted operations | Work at this one target |
|---|---:|---:|---:|
| AgentProf semantic organization | 5 | 9 / 10 | 2 / 9 |
| exact raw-action hierarchy | 3 | 9 / 10 | 3 / 9 |

Session, source-native, independent-step, flat, width-only, and oracle controls
also completed. The 200 target-blind matched permutations preserved every raw
leaf and prefix invariant; their 400 count/shifted real-binary profiles and
scores were independently regenerated and matched the archived artifacts.

### Scorer mapping and preflight boundary

The first independent preflight review found one material defect: the scorer
selected the target by exact trace and step but did not yet reject a mismatch
between the operation component and the official `mistake_agent`. That could
silently mis-score a FULL trace even though this one preflight trace happened
to match.

The adapter was repaired before FULL. The scorer now requires exactly one
operation at `mistake_step` and equality after the declared normalized-agent
comparison. The scorer-only preflight was rerun without another model call.
The resulting
`.agentsight/experiments/traceelephant-rq2-v1/scorer/target-mapping.json`
records one operation at step 5 and an exact normalized match to
`InformationExtraction_Expert`; any mismatch makes the execution invalid
before point estimates, permutations, bootstrap, or a scientific verdict.

The final preflight summary is
`.agentsight/experiments/traceelephant-rq2-v1/metrics/summary-preflight.json`:

- execution status: `VALID`;
- tested-hypothesis verdict: `PREFLIGHT_ONLY`;
- scorer subprocess isolation: true;
- target mappings valid: 1 / 1;
- bootstrap: absent, as required for preflight;
- FULL summary and FULL bootstrap artifacts: absent.

The one-trace numerical comparison is intentionally not scientific evidence.
Its matched-permutation value was `p=1.0`, with no observed mechanism
engagement on this trace. This is neither a positive nor negative paper result
because the preflight trace was selected for deterministic path coverage, not
inference, and the approved population contains 220 failures.

## Independent Review

The initial reviewer returned `MUST-FIX` solely for the missing normalized-agent
target validation described above and passed every other real-path check. After
the repair and scorer-only rerun, a fresh reviewer independently reread
`research-experiment-design`, `docs/user-instruction.md`, the approved plan,
the adapter, and the raw preflight artifacts. It did not run model inference or
edit repository files.

The fresh review returned **PASS** after independently confirming:

1. the real source/model path completed with all nine steps and both real calls;
2. official localizer reconstruction and reference/scorer isolation;
3. identical operations and budgets for the proposed and headline baseline;
4. exact replay of all four primary AgentProf profiles with version 0.2.37;
5. unique exact-step and normalized-agent target mapping;
6. deterministic regeneration and equality of all 200 permutations and 400
   associated real-binary profiles;
7. scorer loading only after target-blind profiles were materialized; and
8. an explicit `VALID / PREFLIGHT_ONLY` boundary with no FULL artifact.

The independent review authorizes the transition to FULL under the approved
plan. It authorizes no RQ conclusion and no paper edit.

## Scientific Impact And Decision

This node adds dependency evidence only: the planned real comparison exists,
uses the intended official external assets, and can be scored without the
identified target-mapping ambiguity. It answers no paper-level RQ and does not
change the research frontier.

The decision is to execute the complete approved matrix unchanged. No prompt,
field, score, metric, threshold, workload, baseline, hypothesis, RQ, or story
was tuned from the preflight values. If FULL exposes a systematic execution
defect, only the affected implementation stage will be repaired and affected
cells rerun; partial prefixes will not be interpreted.

## Completion And Next Action

REAL PREFLIGHT is complete and independently approved. The next action is the
FULL run over all 220 TraceElephant failures, every approved primary and control
profile, 200 matched semantic permutations, and 10,000 stratified bootstrap
resamples. Completion requires every planned trace and tag batch to reach a
terminal state, all declared invariants to hold, and a fresh independent result
review to recompute the result before any targeted WRITE action.
