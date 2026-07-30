# Experiment 001 result review

Status: stopped before ToolSandbox preflight as a valid negative.

## Admitted analyst evidence

The two information-matched packages contained the same 11,146 pprof sample
tuples. Three fresh analyst runs per arm all produced independently accepted
diagnoses and benchmark-agnostic policies. The blinded reviewer reran all 17
cited commands and passed all six cases. Both preregistered replicate-1
policies passed.

All six runs independently identified the same recurring behavior:
candidate/bad trajectories repeat actions after no observable progress. The
evidence contains 1,485 repeated candidate operations and 224 repeated base
operations, a +1,261 excess. Candidate repetitions account for 20.16% of
operations versus 5.93% for base.

## Preregistered efficiency result

| Arm | Valid | Median answer time | Median provider tokens | Median tool calls |
|---|---:|---:|---:|---:|
| PROFILE | 3/3 | 36.614 s | 126,571 | 3 |
| RAW-OPERATIONS | 3/3 | 52.547 s | 126,066 | 4 |

PROFILE was 15.933 seconds (30.3%) faster by the descriptive median, but its
median provider usage was 505 tokens (0.40%) higher. The preregistered faster
rule required lower PROFILE time and no higher PROFILE tokens. It therefore
failed literally.

## Disposition

An independent gate reviewer classified this as a valid negative and required
the iteration to stop. Admission rule 4 was conjunctive, so no downstream
ToolSandbox outcome could make this exact iteration paper-eligible. No
ToolSandbox preflight or scientific episode was run, and no outcome was
observed. The result must not be repaired by post-hoc tolerance, time/token
tradeoff, or replacement of replicate-1 policies.

Any continuation is a new, disclosed, prospectively frozen iteration with
fresh analyst runs. Its resource tolerance must be justified independently of
the observed 505-token difference.
