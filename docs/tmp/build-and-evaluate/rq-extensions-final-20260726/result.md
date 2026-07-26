# RQ1/RQ3 Extensions Recomputed at Final HEAD

Date: 2026-07-26

Source revision: `f795cd0462e1e43ed7731245898d84c8b740c40f`

This run reuses the committed extension-analysis script with the authoritative
final-HEAD RQ1 export.  It changes no estimand: dormancy/revival remains a
descriptive artifact-lifecycle relation, and turnover/cooling remains a
rank-set measurement in Agent action order.

## Command

```bash
python3 docs/tmp/build-and-evaluate/rq-extensions-20260726/analyze_rq_extensions.py \
  --rq1-root docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw \
  --output docs/tmp/build-and-evaluate/rq-extensions-final-20260726
```

The command was run twice, once into this directory and once into a fresh
temporary directory.  `diff -qr` reported no difference across the ten
generated CSV/JSON files.

## Provenance and reconciliation

The script SHA-256 is
`91b8a9903e8229ee340af12119af1717b00481b34580b4a45d6696a9598f46ec`.
The authoritative `projects.json` and `rq1-artifacts.csv` SHA-256 values are
`2b2b38560c5d9e0c0a7f9ae0cf37dbea73d2bd1d919c78f127f23f3c5a4901bf`
and
`339da5069cc9adccc2578fcea0e01bf3fb8ce181496be03e4de2b9d5ea5f4df8`,
respectively.

| Project | Tool actions | Replay identities | Exported identities | Match |
|---|---:|---:|---:|:---:|
| AgentSight | 97,586 | 3,267 | 3,267 | yes |
| ActPlane | 66,238 | 1,809 | 1,809 | yes |
| bpf-developer-tutorial | 1,664 | 170 | 170 | yes |
| eunomia.dev | 13,876 | 360 | 360 | yes |
| agentskill-observability-paper | 991 | 24 | 24 | yes |
| academic-writing-skills | 948 | 116 | 116 | yes |
| **Total** | **181,303** | **5,746** | **5,746** | **yes** |

The six compressed event exports used by the script have SHA-256 values:

| Project | Event-export SHA-256 |
|---|---|
| AgentSight | `b2301390a9f665480a8efd87690653064ca989bfc4a3793d54ea7798793bc01b` |
| ActPlane | `7cee0b947d9cae85263894059674b069ec173d41907c9ba01938becaaa493ea2` |
| bpf-developer-tutorial | `0fe42215ca4aa6b28676a155608a6ce71bc6d2c38a921e918a0f76bfdf472b8b` |
| eunomia.dev | `f547f0607bfb2d81cc923f9292b34463cb4cd9a6054392d66268cf11869fd21e` |
| agentskill-observability-paper | `c5a866cc256458ae7cd75a570e537ddf66f9e8d12977a1bfd89546dce006a4ab` |
| academic-writing-skills | `04e5da6d202649d221e563bfb6bab21c51e9a5d4bfcccfdb55a1ee9e467c4d83` |

## RQ1: dormant-to-revived transitions

Thresholds are strictly more than 100 intervening Tool actions and strictly
more than 24 elapsed hours.  Gap percentiles use Hyndman--Fan type 7 linear
interpolation.  One identity may contribute multiple revival transitions.

### More than 100 intervening Tool actions

| Project | Observed / multi-touch artifacts | Revived/all | Revived/multi-touch | Transitions | Mutation revivals | Gap median/p90 (actions) |
|---|---:|---:|---:|---:|---:|---:|
| AgentSight | 3,267 / 1,853 | 1,271/3,267 (38.9%) | 68.6% | 6,856 | 197 | 349 / 4,965.5 |
| ActPlane | 1,809 / 881 | 662/1,809 (36.6%) | 75.1% | 3,518 | 133 | 469.5 / 5,014 |
| bpf-developer-tutorial | 170 / 98 | 42/170 (24.7%) | 42.9% | 73 | 7 | 271 / 661.2 |
| eunomia.dev | 360 / 243 | 174/360 (48.3%) | 71.6% | 805 | 9 | 449 / 2,339 |
| agentskill-observability-paper | 24 / 4 | 2/24 (8.3%) | 50.0% | 3 | 0 | 105 / 120.2 |
| academic-writing-skills | 116 / 30 | 13/116 (11.2%) | 43.3% | 16 | 2 | 167.5 / 360.5 |
| **Range/total** | **5,746 / 3,109** | **8.3--48.3%** | **42.9--75.1%** | **11,271** | **348** | |

### More than 24 elapsed hours

| Project | Observed / multi-touch artifacts | Revived/all | Revived/multi-touch | Transitions | Mutation revivals | Gap median/p90 (hours) |
|---|---:|---:|---:|---:|---:|---:|
| AgentSight | 3,267 / 1,853 | 526/3,267 (16.1%) | 28.4% | 1,086 | 17 | 83.1 / 409.6 |
| ActPlane | 1,809 / 881 | 382/1,809 (21.1%) | 43.4% | 801 | 16 | 81.0 / 279.2 |
| bpf-developer-tutorial | 170 / 98 | 21/170 (12.4%) | 21.4% | 26 | 5 | 682.9 / 3,234.8 |
| eunomia.dev | 360 / 243 | 144/360 (40.0%) | 59.3% | 349 | 2 | 267.8 / 1,800.4 |
| agentskill-observability-paper | 24 / 4 | 0/24 (0.0%) | 0.0% | 0 | 0 | --- |
| academic-writing-skills | 116 / 30 | 18/116 (15.5%) | 60.0% | 23 | 1 | 60.2 / 605.3 |
| **Range/total** | **5,746 / 3,109** | **0.0--40.0%** | **0.0--60.0%** | **2,285** | **41** | |

Relative to the prior 5,792-artifact export, the paper-facing RQ1 changes are:

- all-artifact action-gap range: 11.2--48.3% to **8.3--48.3%**;
- multi-touch action-gap range: 42.9--74.9% to **42.9--75.1%**;
- revival transitions: 11,269/2,290 to **11,271/2,285**;
- mutation revivals: 352/42 to **348/41**;
- AgentSight: 1,269/3,287 to **1,271/3,267** and 524/3,287 to
  **526/3,267**;
- ActPlane: 660/1,834 to **662/1,809** and 382/1,834 to **382/1,809**;
- agentskill-observability-paper: 3/25 to **2/24** and 0/25 to **0/24**.

## RQ3: rank turnover and rank-set cooling

The primary view uses 100-action windows with a 50-action stride.  The
sensitivity view uses non-overlapping 100-action windows.  Each window ranks
the top 5 artifacts and top-level modules.  Cooling lags are measured in
windows, not elapsed time.

### Turnover

| Pooling/view | Entity | Adjacent pairs | Top-1 change | Any top-5 change | Mean top-5 replacement |
|---|---|---:|---:|---:|---:|
| transition-weighted primary | artifact | 3,372 | 49.6% | 91.5% | 43.5% |
| transition-weighted primary | module | 3,372 | 13.6% | 42.0% | 17.4% |
| project-median primary | artifact | 3,372 | 50.8% | 88.7% | 42.9% |
| project-median primary | module | 3,372 | 12.5% | 40.8% | 20.6% |
| transition-weighted sensitivity | artifact | 1,666 | 72.1% | 97.5% | 66.5% |
| transition-weighted sensitivity | module | 1,666 | 19.1% | 60.4% | 28.8% |

### Cooling

| View / lag | Entity | Origin memberships | Endpoint retention | Continuous retention |
|---|---|---:|---:|---:|
| primary / 1 window | artifact | 15,907 | 57.0% | 57.0% |
| primary / 1 window | module | 7,951 | 84.9% | 84.9% |
| primary / 8 windows | artifact | 15,755 | 20.4% | 4.5% |
| primary / 8 windows | module | 7,875 | 62.7% | 41.1% |
| sensitivity / 8 windows | artifact | 7,789 | 17.1% | 1.9% |
| sensitivity / 8 windows | module | 3,888 | 58.5% | 32.1% |

Relative to the prior export, the paper-facing RQ3 values change as follows:

- primary top-1 change: 49.7%/13.5% to **49.6%/13.6%**;
- primary any-top-5 change: 91.6%/42.6% to **91.5%/42.0%**;
- primary mean replacement: 43.5%/17.7% to **43.5%/17.4%**;
- project medians: 50.9%/12.5%, 88.7%/41.0%, and 43.0%/20.7% to
  **50.8%/12.5%, 88.7%/40.8%, and 42.9%/20.6%**;
- sensitivity top-1 and any-top-5 change: 72.2%/19.1% and 97.7%/61.3% to
  **72.1%/19.1% and 97.5%/60.4%**;
- primary endpoint retention at lags 1/8: 56.9%/20.4% for artifacts and
  84.6%/62.3% for modules to **57.0%/20.4%** and **84.9%/62.7%**;
- primary 8-window continuous retention: 4.5%/40.6% to **4.5%/41.1%**;
- sensitivity 8-window endpoint and continuous retention:
  17.1%/58.1% and 1.9%/31.8% to **17.1%/58.5% and 1.9%/32.1%**.

## Result judgment

```text
run status: valid
tested hypothesis: supported (the descriptive artifact-versus-module ordering is preserved)
research value: supporting
paper impact: additional RQ1/RQ3 evidence
next paper decision: update numeric values only; preserve RQ meanings, qualifiers, and conclusion direction
```
