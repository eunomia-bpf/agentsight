# Experiment 003 adaptation rationale

Date: 2026-07-29

Status: descriptive diagnosis of prior failures; not a rescoring record

## Prior evidence

Experiment 001 was a valid negative with three analyst runs per arm. PROFILE
had lower median elapsed time, but its median provider-token total exceeded
RAW-OPERATIONS by 505 tokens (0.4006%), so the literal faster-with-no-token-
increase gate failed. No downstream outcome was observed.

Experiment 002 was a prospectively frozen 20-paired-block replication.
Independent recomputation returned `NOT_SUPPORTED`:

- valid outputs: PROFILE 12/20, RAW-OPERATIONS 19/20;
- time median-ratio estimate: 0.749975;
- time Bonferroni one-sided 97.5% upper bound: 17.823645;
- provider-token median-ratio estimate: 1.290090;
- provider-token upper bound: 1.431173;
- all four analyst-gate clauses failed;
- PROFILE rank 1 was invalid and RAW rank 1 valid;
- no policy was frozen and ToolSandbox remained unobserved.

## Validity failure decomposition

The five experiment-002 reviewer fields decomposed as:

| Reviewer field | PROFILE | RAW-OPERATIONS |
|---|---:|---:|
| recurring bad-vs-good diagnosis | 20/20 | 20/20 |
| quantitative support | 20/20 | 19/20 |
| executable generic policy <=60 words | 20/20 | 20/20 |
| no benchmark-specific/hidden reference | 12/20 | 20/20 |
| assigned-package-only evidence | 20/20 | 20/20 |
| conjunction | 12/20 | 19/20 |

All eight invalid PROFILE outputs failed only the broad fourth field. Their
policies were independently accepted as executable and generic. Concrete
operations and trace steps appeared mainly in quantitative evidence that the
task explicitly required.

This is evidence of a construct-scope defect, not authority to rescore
experiment 002. An exploratory field-scope calculation, clearly outside the
frozen gate, would yield 20/20 PROFILE and 19/20 RAW validity, a paired time
ratio of 0.712097, and a time upper bound of 0.749975. The provider-token
estimate and upper bound remain 1.290090 and 1.431173, so even this exploratory
calculation cannot make experiment 002 pass.

## Provider-token failure decomposition

The prompt-length difference was only 29 characters and three English words.
The final outputs were not the source of the excess:

- PROFILE used 539,512 more provider input tokens in aggregate;
- PROFILE produced 15,516 fewer output tokens;
- the net excess was 523,996 tokens and was overwhelmingly input-side.

Recorded command output volume was:

- PROFILE: 10.63 million characters, 531,628 per run;
- RAW-OPERATIONS: 0.166 million characters, 8,318 per run.

The roughly 64-fold difference was dominated by unbounded pprof label output.
Ten commands combining top-level inspection with unbounded `-tags` produced
about 85% of PROFILE command-output characters. Within PROFILE, command count
and provider input tokens had an exploratory correlation of about 0.91.

These observations motivate a representation-neutral query-output budget and
bounded stock-command recipes. They do not justify deleting provider tokens,
changing their definition, or relaxing the zero-increase gate.

## Why the repair is prospective rather than a reanalysis

Experiment 003 uses:

- fresh model executions;
- a new randomized schedule and rank-1 selection;
- a new blind alias map and reviewer;
- a frozen field-scoped validity schema with reason codes;
- symmetric command/output budgets;
- the same strict confirmatory thresholds.

No experiment-002 output is reused as an observation or policy. The previous
negative analysis and its adjudication record remain immutable.

The repair targets generic interface defects:

- evidence may be concrete while a policy remains general;
- unbounded terminal output is a poor agent interface regardless of the
  observed diagnosis.

The instructions may not name the discovered repeated-action behavior, its
specific labels, the rank-1 output, or any ToolSandbox scenario.

## Generalization boundary

ToolSandbox has not been inspected and remains a legitimate held-out
downstream system for the fixed case-study chain. However, AgentReward itself
informed the repair. A successful experiment 003 may support only the disclosed
fixed-case replication claim.

For a cross-workload profiling-utility claim, add a second development corpus
whose profiles, raw records, diagnoses, and failure modes did not inform this
protocol repair.

