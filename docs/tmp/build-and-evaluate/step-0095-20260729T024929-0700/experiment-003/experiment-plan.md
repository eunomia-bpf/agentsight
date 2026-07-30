# Experiment 003 plan: prospective protocol-repair replication

Plan date: 2026-07-29

Gate: RQ2 profiling utility

Status: draft for independent plan review; no experiment-003 analyst or
ToolSandbox call is authorized by this draft

## Scientific continuity and scope

The fixed paper-level thesis remains exactly:
**“Agent observability needs profiling, not only debugging.”**

Experiments 001 and 002 remain visible valid negative results. This experiment
does not rescore their outputs, replace their policies, relax their frozen
gates, or reinterpret exploratory analyses as confirmatory evidence.

Experiment 003 is a prospectively frozen repair replication for the same
bounded case study:

```text
real AgentReward bad/good development trajectories
  -> information-matched PROFILE or RAW-OPERATIONS evidence
  -> fresh agent analyst diagnosis and rank-1 frozen policy
  -> held-out official ToolSandbox executions, only after the analyst gate
  -> official success and measured agent-resource outcomes
```

It can support a claim about this fixed analyst model, development corpus, and
held-out downstream system. Reusing the AgentReward corpus after protocol
mining does not establish cross-workload generalization. A broader claim would
require a new development corpus that did not inform this repair.

## Disclosed prospective repairs

Experiment 002 exposed two protocol defects before any ToolSandbox outcome was
observed.

1. Its validity reviewer combined two constructs. Concrete frame, tag,
   operation, and trace references were required to substantiate diagnosis,
   but a broad “no benchmark-specific reference” boolean could invalidate the
   same evidence even when the proposed policy was generic.
2. The PROFILE instructions recommended unbounded `pprof -tags` and `-top`
   queries. These produced much larger model-visible tool outputs than the
   aggregate RAW queries and dominated provider input tokens.

Experiment 003 repairs only those defects:

- validity is field-scoped, with frozen reason codes;
- both evidence formats receive a symmetric query-output budget and bounded
  stock-command recipes.

It does not change the minimum validity rate, paired design, time or token
boundary, rank-1 no-substitution rule, bootstrap family, downstream admission
gate, or paper-eligibility rule.

## Evidence identity and product boundary

Use the same 338 same-task AgentReward bad/good pairs drawn from 440 source
trajectories, with the exact trajectory and pairing manifests frozen before
execution.

PROFILE contains exactly one standard differential pprof
`operations/count` profile. Its semantic stack remains:

```text
task -> subtask -> strategy -> action -> object -> result
```

RAW-OPERATIONS contains the lossless flat operation records used to construct
that profile, with signed side, source lineage, and all model-visible fields
preserved. Before execution, a checker must establish the same operation
multiset, signed total, pair count, source hashes, and label values in both
packages.

Package README files and condition-specific prompt suffixes are experiment
instructions, not AgentProf product artifacts. They may explain bounded stock
queries but may not include an aggregate result, diagnosis, policy, rendered
figure, alternative profile format, or benchmark answer. AgentProf still has
one user-facing artifact per run: the standard pprof profile.

## Analyst model and task

Use 40 fresh ephemeral `gpt-5.6-sol` Codex executions. Every run receives:

- the same benchmark-agnostic analyst task and JSON output schema;
- a read-only evidence package as its complete working directory;
- no internet, repository, ToolSandbox, previous output, downstream result, or
  private schedule access;
- a 900-second timeout;
- the same maximum number of command executions and the same output budget.

The analyst must return exactly:

1. one recurring candidate/bad behavior relative to base/good;
2. reproducible commands and quantitative findings;
3. one executable `policy_text` of at most 60 English words;
4. an `expected_mechanism` that states expected benefit and cost.

Concrete identifiers from the assigned package are allowed in `diagnosis`,
commands, and `quantitative_evidence`. They are forbidden in `policy_text` and
`expected_mechanism`, which must remain benchmark- and domain-agnostic.

## Symmetric bounded-query contract

The contract is a usability and resource boundary, not a semantic
transformation of either evidence format. A successful result is attributed
to “AgentProf pprof with the preregistered bounded stock-query interface,” not
to the profile bytes in isolation.

For both arms:

- at most 6 attempted command executions and at most 6 completed command
  executions; failed, rejected, cancelled, and timed-out attempts count;
- at most 200 newline-delimited output lines and 32 KiB of model-visible
  stdout plus stderr for any command;
- at most 128 KiB of model-visible command output over the complete run;
- discovery commands must also be bounded;
- dumping the complete evidence file is forbidden;
- the run record retains the command, exact pre-render tool-event output hash,
  line and byte counts, transport receipts, and provider usage.

PROFILE instructions use only stock `go tool pprof`. Registered examples are:

```bash
go tool pprof -top -nodecount=20 profile.pb.gz
go tool pprof -top -nodecount=20 -focus='<semantic frame>' profile.pb.gz
go tool pprof -traces -focus='<semantic frame>' profile.pb.gz | sed -n '1,120p'
go tool pprof -tags -focus='<semantic frame>' profile.pb.gz | sed -n '1,80p'
```

`pprof -raw` is forbidden. `-top` requires an explicit `-nodecount` no greater
than 100. `-traces` and `-tags` require both a semantic focus and an explicit
line bound.

RAW-OPERATIONS instructions require aggregate `jq`, `awk`, `sort`, and
`uniq` queries. Any row enumeration requires an explicit `head` or `sed`
bound. Whole-file `cat`, unconstrained `jq '.'`, and equivalent raw dumps are
forbidden.

The launcher does not create a custom visualization or processed evidence
artifact. It records the ordinary Codex command events.

A deterministic auditor, frozen before the scientific schedule, parses every
attempted inner shell command. Its accepted grammar is:

- one simple command or one pipeline; no `;`, `&&`, `||`, background jobs,
  functions, loops, subshells, command substitution, process substitution,
  here-documents, variable expansion, or write redirection;
- package-relative literal input paths only; no absolute path, parent
  traversal, symlink escape, network executable, or
  environment-dependent filename;
- at most one evidence reader in a pipeline;
- PROFILE evidence reader: literal `go tool pprof` with an approved mode and
  flags; focus values must be nonempty literals over
  `[A-Za-z0-9_:.,=+/-]`, not wildcard or alternation expressions;
- RAW evidence reader: `jq` or `awk` over the frozen flat-operation filename,
  with no environment, module, file-open, subprocess, or redirection feature;
- downstream pipeline stages only from the frozen read-only set `head`,
  `sed`, `sort`, `uniq`, and `cut`, with literal numeric bounds;
- discovery limited to frozen forms of `pwd`, bounded `rg --files`, and
  bounded `sed` over the package README.

The auditor counts distinct command-execution item identifiers from both
started and completed events, so compound commands and failed attempts cannot
evade the limit. The exact grammar, argv normalizer, and adversarial golden
tests are contract-bound.

The runner hashes and counts the combined stdout/stderr payload at the tool
event boundary before it is rendered back to the model. Event receipts must
prove that this same payload was delivered. Any substrate truncation marker,
missing chunk, receipt/hash mismatch, or unavailable pre-render count makes
the run invalid; a raw dump cannot become compliant because a UI or transport
truncated it. Shell-level `head` or `sed` is allowed because it bounds the
payload before the tool-event boundary.

Exceeding any budget or grammar rule makes that run invalid and retains its
actual provider tokens and 900-second effective time; it is never silently
deleted, replaced, or rerun in the scientific batch.

Both condition prompts provide four equally specific query intents:

1. bounded overview;
2. bounded focused aggregation;
3. bounded recurring-example inspection;
4. bounded contrast/sanity check.

The PROFILE recipes express these intents with stock pprof. The RAW recipes
express the same intents with concrete aggregate `jq`/`awk` pipelines and the
same limits. Neither arm receives a behavior, label, or policy found in a
prior experiment.

### Synthetic compliance-only preflight

Before freezing the scientific batch, construct and hash two synthetic canary
packages with invented labels and no AgentReward trajectories, tasks, or
operations. The canaries are isomorphic to the two evidence formats and have
enough label or row cardinality to expose an unbounded query.

Run one fresh execution per arm on the canaries solely to check:

- package readability;
- output-schema production;
- bounded-query grammar;
- command count and model-visible output counts;
- telemetry completeness.

The orchestrator may inspect only a machine-generated content-redacted
receipt: PASS/FAIL, enumerated mechanical failure codes, attempted/completed
counts, byte/line counts, and hashes. It may not inspect commands, focus
literals, final output, diagnosis, policy, timing, provider usage, or arm
contrasts.

There is at most one preflight round for a plan version. A failure permanently
archives that version and authorizes no scientific run. A later version may
change only recipe syntax, auditor grammar, or mechanical budgets, must use a
new frozen canary and fresh preflight calls, and requires independent plan
review again. No AgentReward package is used for compliance tuning. There is
no retry after the full scientific batch is frozen.

## Fresh randomized paired-block schedule

Use 20 temporal blocks. Each contains one PROFILE and one RAW-OPERATIONS run.

- Schedule seed: `2026072906`.
- Exactly 10 blocks are PROFILE-first and 10 RAW-first.
- Opaque run identifiers, block order, within-block order, and within-arm rank
  are frozen before any call.
- Rank 1 in each arm is the downstream policy candidate and cannot be
  substituted.
- Calls are fresh and share no conversation or cache under experimental
  control.

Record command start, first/last/final receipt time, wall time, status,
provider input/output/cached/reasoning usage, model/tool calls, actual command
events, output counts, and final JSON. Run all 40 without interim content,
arm-level timing, usage, validity, or gate inspection.

## Independent blinded output review

Before any of the 40 calls, freeze the reviewer model identifier and runtime,
review prompt, field/reason schema, bundle builder, execution command, and
validation code.

After all 40 runs, build a fresh opaque review bundle with no timing, usage,
schedule position, rank, private arm map, prior experiment result, or
ToolSandbox data. Freeze its manifest before a fresh reviewer runs.

Reviewer alias seed: `2026072907`.

For each case, rerun every cited evidence command inside its assigned snapshot
and return these independent booleans plus a frozen reason code and field:

1. `recurring_diagnosis_valid`
   - diagnosis identifies a recurring bad-vs-good behavior;
2. `quantitative_support_valid`
   - cited commands reproduce and support the stated quantities;
3. `policy_text_valid`
   - executable, at most 60 English words, benchmark/domain agnostic;
4. `expected_mechanism_valid`
   - plausible benefit and cost, benchmark/domain agnostic;
5. `no_hidden_private_or_observed_downstream_reference`
   - no hidden answer, observed downstream outcome, private mapping, prior
     output, or claim that a predicted effect was already observed;
6. `assigned_package_only`
   - no evidence read outside the assigned snapshot;
7. `bounded_query_contract_valid`
   - command grammar, count, output-line, and output-byte limits all pass.

Allowed assigned-package frame, tag, operation, trace, filename, and line/step
references in diagnosis or quantitative evidence must not cause items 3--5 to
fail. A clearly prospective expected mechanism is allowed and required; only
representing a prediction as an observed downstream result fails item 5.
Conversely, a concrete identifier in `policy_text` or
`expected_mechanism` must fail the relevant field.

The frozen field-to-reason-code matrix is:

| Field | Allowed false reason codes |
|---|---|
| recurring diagnosis | `missing_behavior`, `not_recurring`, `bad_good_direction_unsupported`, `output_unavailable` |
| quantitative support | `command_missing`, `command_nonreproducible`, `finding_mismatch`, `contrast_insufficient`, `prediction_presented_as_observation` |
| policy text | `policy_missing`, `word_limit_exceeded`, `not_executable`, `benchmark_specific_policy`, `domain_specific_policy` |
| expected mechanism | `mechanism_missing`, `benefit_missing`, `cost_missing`, `mechanism_unsupported`, `benchmark_specific_mechanism`, `domain_specific_mechanism` |
| hidden/private/observed downstream | `hidden_answer_reference`, `observed_downstream_claim`, `private_mapping_reference`, `prior_output_reference` |
| assigned package | `outside_read`, `outside_working_directory`, `unresolved_path_redaction` |
| bounded query contract | `attempt_limit`, `completion_limit`, `per_command_line_limit`, `per_command_byte_limit`, `cumulative_byte_limit`, `forbidden_grammar`, `transport_truncation`, `receipt_mismatch`, `telemetry_missing` |

True fields use only `ok`. Every false value must include at least one allowed
code and the affected output field or command receipt index. Item 7 is copied
from the deterministic auditor receipt; the reviewer cannot override it. A
generic “benchmark-specific” reason is not available.

The reviewer freezes all 40 decisions before the private alias map is opened.
Bundle hashes must be unchanged. The rank-1 policies are accepted only if all
seven fields pass; no substitution is allowed.

## Confirmatory analyst-efficiency gate

Validity is the conjunction of the seven frozen reviewer fields.

For invalid, failed, or timed-out runs:

- effective time is 900 seconds;
- provider token usage remains the positive recorded
  `input_tokens + output_tokens`;
- missing or nonpositive provider usage is a hard protocol failure.

Within each temporal block, define:

```text
T_b = effective PROFILE time / effective RAW time
K_b = PROFILE provider tokens / RAW provider tokens
```

Use the median paired log ratio for each endpoint. Draw 100,000 whole-block
bootstrap resamples with PCG64 seed `2026072908`, using the same sampled block
indices for time and token endpoints. Use the frozen no-interpolation
`ceil(p*n)` order statistic.

Bonferroni one-sided 97.5% upper bounds are `U_T` and `U_K`. The gate passes
only if all four clauses hold:

1. both arms have at least 18/20 valid outputs;
2. PROFILE valid count is not below RAW valid count;
3. `U_T < 1.00`;
4. `U_K <= 1.00`.

Report `U_T < 0.90` and `U_K <= 1.05` only as sensitivity. They cannot change
the gate. A time/token tradeoff is not a confirmatory “faster” result.

If the analyst gate fails or either rank-1 output is invalid, stop. Do not
freeze policies, inspect ToolSandbox outcomes, or replace the selected output.

## Held-out downstream consequence

Only after the analyst gate and both rank-1 policies pass, use:

- official ToolSandbox commit
  `165848b9a78cead7ca7fe7c89c688b58e6501219`;
- the frozen local Qwen3.6-27B Q4_K_M llama.cpp endpoint identity;
- the same 32 dependency-screened offline scenarios;
- `turn_on_location_low_battery_mode` only for three-condition preflight and
  exclude it from outcomes;
- the remaining 31 scenarios, 8 registered seeds, and 3 interleaved
  conditions: NO-POLICY, PROFILE-POLICY, RAW-POLICY;
- 744 official terminal episodes in total.

The exact rank-1 policy text is appended to the system input. Scenario
construction, official evaluator, tools, start state, role/request seeds,
sampling, turn limits, and telemetry remain condition-identical.

The downstream confirmatory endpoints and admission rule remain those frozen
for experiment 002.

Success is official combined similarity:

```text
similarity = 1[minefield_similarity == 0] * milestone_similarity
```

Cost is relative agent-total-token delta. Agent-total tokens are the sum of
the local OpenAI response `usage.total_tokens` over every agent-role request
in one episode, excluding user-simulator requests. Every response must satisfy
`total_tokens = prompt_tokens + completion_tokens`; missing or inconsistent
usage is a hard stop.

For each of the 248 scenario/trial cells, pair PROFILE-POLICY with NO-POLICY:

```text
Delta_S = mean(PROFILE similarity - NO-POLICY similarity)
Delta_K = sum(PROFILE agent tokens) / sum(NO-POLICY agent tokens) - 1
```

Use `Generator(PCG64(2026072904))` for 10,000 whole-scenario cluster
resamples. Each resample draws exactly 31 scenario names with replacement and
retains all eight seeds and all three conditions for each selected scenario.
Recompute both estimators from the same sampled clusters. With the frozen
no-interpolation `ceil(p*n)` order statistic:

```text
L_S = Q_Delta_S(0.025)
U_K = Q_Delta_K(0.975)
```

The PROFILE consequence passes only if:

1. `L_S > 0`; or
2. `U_K <= -0.10` and `L_S > -0.02`.

RAW-POLICY is reported transparently but does not determine the PROFILE
consequence claim. Secondary metrics include exact success, milestone and
minefield similarity, agent calls per official turn, tool/model calls,
prompt/completion tokens, wall time, duplicate same-tool/same-argument calls,
errors, turns, simulator usage, and exceptions.

Report one-time diagnosis tokens and downstream tokens separately. A
predeclared lifecycle sensitivity amortizes the one-time diagnosis over 248
PROFILE-policy episodes, but it cannot replace either the analyst token gate
or downstream admission.

## Freeze and execution order

1. Accept this plan through independent review.
2. Materialize packages and prove information identity.
3. Freeze schemas, prompts, bounded-query auditor, and compliance preflight.
4. Run compliance-only preflight; if it passes, archive and exclude it.
5. Freeze schedule, commands, runtime/model contract, packages, hashes, and
   analysis code.
6. Independently review the full analyst contract.
7. Execute all 40 analyst runs once, without interim inspection.
8. Freeze and independently review the blind-review bundle and command.
9. Run blind review once and validate its provenance.
10. Execute the frozen analyst analysis once.
11. Obtain an independent result recomputation.
12. Stop on analyst or rank-1 failure.
13. Only on pass, freeze and review policies, ToolSandbox preflight, 744-run
    command, analysis, and result-review contracts.
14. Run ToolSandbox preflight, then the full batch without interim outcomes.
15. Independently recompute downstream results and paper eligibility.

## Stop rules and paper eligibility

- No rerun, substitution, scenario exclusion, or threshold change based on an
  observed result.
- No policy or downstream artifact is created before both analyst gates pass.
- Any package/hash/runtime drift, outside evidence read, query-budget breach,
  malformed output, incomplete provider usage, or reviewer provenance failure
  is fail-closed.
- Experiment 001 and 002 negative results and this disclosed repair remain in
  the research record and any paper report.
- Do not edit the paper until a fresh independent reviewer admits both the
  analyst and downstream evidence.
- Paper eligibility requires the complete experiment-003 analyst gate, valid
  rank-1 policies in both arms, all 744 registered ToolSandbox episodes, a
  downstream consequence pass, and an independent final PASS.
