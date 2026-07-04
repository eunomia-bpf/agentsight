# Analyst Study Readout R316

R316 is a scripted readout of the R315 protocol, not a human or agent study result.
The scripted analyst policy selects the first top-k visible groups in each packet, then the hidden key scores the selection.

## Primary Findings

- Top-3 operation-stack packets contain a positive group on 100.0% of assigned trials, versus 83.3% for fixed-session and 100.0% for flat.
- Top-3 operation-stack packets contain a high-lift group on 83.3% of assigned trials, versus 66.7% for fixed-session and 0.0% for flat.
- The task-paired median recall delta for operation-stack over fixed-session is 0.1333, while the median work delta is 0.0207.
- The readout preserves the known tradeoff: operation-stack exposes more positives than fixed-session in most tasks, but it uses more work and does not dominate every metric.

## Top-3 View Summary

| View | Positive hit rate | High-lift hit rate | Median recall | Median work | Median lift |
|---|---:|---:|---:|---:|---:|
| flat | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| fixed_session | 0.8333 | 0.6667 | 0.0138 | 0.0098 | 1.6363 |
| operation_stack | 1.0 | 0.8333 | 0.1606 | 0.0809 | 1.4125 |

## Claim Boundary

This artifact supports protocol sensitivity and automated inspectability wording only.
It does not support human accuracy, agent accuracy, time-to-answer, productivity, automatic detection, detector, or single-view-dominance claims.
