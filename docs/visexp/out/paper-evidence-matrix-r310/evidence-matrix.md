# Paper Evidence Matrix R310

R310 is a paper-facing synthesis over tracked R307/R309 artifacts. It does not sync datasets, rerun converters, or introduce profiler abstractions.

## Headline

- Abstractions: operation, operation stack.
- Claims: 4 total; scoped paper-ready claims: C1, C2, C4; partial claims: C3.
- Problem-value suite: 4 datasets / 6 tasks / 34539 operations / 3699 positives.
- Operation-stack evidence: high-lift 5/6, more selective than flat 6/6, higher recall than fixed-session 5/6.
- Counterpoint: fixed-session lower selected work 4/6.

## Claim Matrix

| Claim | Verdict | Paper use | Headline evidence | Must not claim |
|---|---|---|---|---|
| C1 | supported | Use in abstract/design as heterogeneous operation model and trace exchange evidence. | 15 sampled public datasets / 47590 operations; R293 profile-spec replay and stack override; R294 claim-gated exchange plus R303 scripted agent-session exchange with 1 session / 6 operations and folded equality; +1 more | all public agent datasets are fully converted at full scale; Chrome/OpenTelemetry ecosystem compatibility is complete; +1 more |
| C2 | supported with scoped limits | Use in design/results as recursive stack-depth evidence. | R286 recursive depth sweep; R290 OSWorld-Human grouped boundary evidence; R291 AgentNet step-quality fields; +1 more | perfect intent recovery; one universal stack depth; +1 more |
| C3 | partial | Use as extension-point evidence, with negative controls and scoped language. | R282 held-out mapping; R285 leave-dataset-out mapping; R297 OSWorld-Human supervised boundary backend; +1 more | field derivation is unsupervised; one learned backend generalizes across all families; +1 more |
| C4 | supported as automated proxy, not user utility | Use in evaluation/discussion as real-problem proxy value and counterpoints. | 4 datasets / 6 tasks / 34539 task-operations; operation-stack more selective than flat: 6/6; high-lift evidence: 5/6; +3 more | human productivity improvement; automatic anomaly detection; +1 more |

## Global Must-Not-Claim

- Every public agent trajectory dataset can be profiled at full scale without additional engineering.
- R296 reviewer packet is itself empirical evidence
- R297 generalizes beyond OSWorld-Human
- R300-R305 prove human productivity
- R306 proves full OpenTelemetry/Chrome ecosystem compatibility
- The profiler fully discovers latent intent boundaries without labels or rules.
- The profiler improves human developer productivity.
- automatic anomaly detection
- case packets are a new profiler abstraction
- complete trace ecosystem compatibility
- human accuracy or time improvement
- universal dominance over fixed-session baselines
- unsupervised intent discovery

## Source Artifacts

- `r307_claim_readiness`: `docs/visexp/out/paper-claim-readiness-r307/paper-readiness-synthesis.json`
- `r309_problem_value`: `docs/visexp/out/operation-problem-value-r309/problem-value-report.json`
