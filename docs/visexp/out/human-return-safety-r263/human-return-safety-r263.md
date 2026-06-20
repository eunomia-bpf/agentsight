# R263 Human Return Safety Gate

Status: `human_return_safety_passed`

## Checks

| check | passed |
|---|---:|
| `r195_command_passed` | `True` |
| `synthetic_status_rejected` | `True` |
| `synthetic_content_status_detected` | `True` |
| `synthetic_marker_hits_present` | `True` |
| `no_scorer_operations_on_synthetic` | `True` |
| `c5_stays_false` | `True` |
| `c6_stays_false` | `True` |
| `requires_real_human_data` | `True` |

## Claim Gate

- human_return_safety_supported: `True`
- c5_supported: `False`
- c6_supported: `False`
- weak_accept_supported: `False`

R263 is an ingestion-safety negative test. It rejects known synthetic R259 exports before scoring, but it adds no participant responses, human labels, tag adequacy evidence, developer utility evidence, or weak-accept evidence.
