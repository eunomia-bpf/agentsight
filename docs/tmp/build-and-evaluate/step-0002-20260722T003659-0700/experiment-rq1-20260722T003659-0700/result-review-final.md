# Independent RQ1 Result Review — Authoritative Six-Project Run

**Reviewer:** `/root/rq1_result_review_final`  
**Reviewed:** 2026-07-22T01:35:57-07:00  
**Authoritative cutoff:** `1784708569241` epoch milliseconds  
**Verdict:** **PASS**

This review covers only the six-project run under `full-six-projects/`. The
preflight-cutoff successful run recorded in `commands.log` is superseded and
was not used for any recomputation or judgment.

## Result-review judgment

```text
run status: valid
tested hypothesis: inconclusive overall; the descriptive reuse relation is measured,
  while persistence and recognized-validation cross-case interpretations stop at coverage
research value: supporting
paper impact: additional RQ evidence plus a mechanism/measurement-coverage boundary
next paper decision: report the six-case reuse result and the two explicit coverage stops;
  do not claim a population relation, causal effect, full RQ1 answer, content durability,
  or mutation-level test coverage
```

The run is complete and internally reproducible. It validly characterizes the
planned observables for these six cases, but it does not justify a general
claim that activity predicts progress. In particular, only 3/6 cases have an
eligible adapter-recognized confirmed create and only 3/6 expose a recognized
successful validation, so the preregistered stopping rules correctly prevent
cross-case interpretation of those two dimensions.

## 1. Frozen inputs, commands, and hashes

I read the approved `plan.md`, all three plan reviews, the current extraction
and plotting code, `commands.log`, the source-linked event JSON, the three CSV
tables, `result.md`, and both F3/F4 renderings.

All hashes recorded in `commands.log` match the frozen files. The principal
checks are:

| Artifact | Verified SHA-256 |
|---|---|
| `raw/projects.json` | `2491c33ac5c5e64c877ea8c998731df2dad2999e37af715e528f997f909dc58b` |
| `raw/rq1-artifacts.csv` | `8e72aa19b5305b9c455c64cd009b535f45145d67729d9c8b58318e89ef767cc1` |
| `raw/rq1-mutations.csv` | `3d911332f7827afdee74a1f6a0f85aa002be297379e14909dbba1fee36d88964` |
| `raw/rq1-summary.csv` | `d04cee570c409ab1a8b1518657683e6ccb417663acb9933690c063adcf61406b` |
| F3 PNG | `704b084b90568be81e1e510fa7748828569cd433ed2ae3a242adc59491c21eb2` |
| F4 PNG | `14a1c08936c6600876233b2e3229c3f78a7a4a0ef74a449b4cf15ede7dfd6abf` |

The six compressed event hashes and both frozen PDF hashes also match the log.
Each `.json.gz` decompresses byte-for-byte to its local uncompressed event
JSON. Re-running `plot_rq1.py` from only the frozen CSVs reproduced both PNGs
byte-for-byte; PDF bytes differ on a rerun only because Matplotlib writes PDF
time metadata.

The documented first failed attempt and the later successful-but-superseded
run are not silently dropped: `commands.log` records both and explains why a
fresh cutoff preceded the authoritative run. The final command covers exactly
the six preregistered roots and reports 39.69 seconds wall time and 762,708 KiB
peak RSS.

## 2. Independent source and row reconciliation

I independently parsed all six event JSONs and rebuilt artifact identities and
mutation endpoints without reading `result.md`. The complete reconciliation is:

| Project | Tool events | Artifact identities | Confirmed mutation rows | Maximum admitted timestamp |
|---|---:|---:|---:|---:|
| AgentSight | 126,476 | 4,255 | 6,482 | 1784708567949 |
| ActPlane | 65,699 | 2,149 | 5,770 | 1784364131461 |
| bpf-developer-tutorial | 1,865 | 232 | 283 | 1784706678108 |
| eunomia.dev | 10,560 | 362 | 170 | 1784708509839 |
| agentskill-observability-paper | 991 | 25 | 196 | 1783842131999 |
| academic-writing-skills | 658 | 131 | 251 | 1784170767863 |
| **Total** | **206,249** | **7,154** | **13,152** | — |

Every event timestamp is at or before `1784708569241`, and every event stream
is sorted by `(ts_ms, event_id)` with unique event IDs. Candidate, parsed,
included, and attributed session counts reconcile with the per-vendor maps.
Tool-action, attributed-action, file-action, no-worktree, effect/status/vendor,
and per-worktree file-action totals all reconcile with `projects.json` and
`rq1-summary.csv`.

All 13,152 mutation rows resolve to one exported event and one non-scope
`create|write|rename|delete` action with `status == ok`. Event ID, source-call
ID, session ID, vendor, timestamp, event index, worktree ID, path, and operation
all match. No mutation row has a missing event, call, or session ID.

## 3. Artifact identity and final-state semantics

I independently replayed the identity state machine over every non-scope file
action. All artifact IDs, first/final paths, first/last event and timestamp,
session sets, read/mutation/rename/delete counts, close reasons, and mutation
history positions match the CSV rows.

The observed birth distribution is:

| Birth state | Identities |
|---|---:|
| left-censored existing | 5,304 |
| adapter-recognized confirmed create | 1,043 |
| create with unknown status | 790 |
| unknown rename source | 17 |

Only the 1,043 identities born from a successful adapter-recognized `create`
on an unoccupied observed `(worktree_id, path)` are marked introduction-
eligible. A rename inherits its source identity; each of the 17 unresolved
rename sources has unknown lineage and is excluded from persistence. Delete
then recreate starts a new identity, and identical paths in different
worktrees remain distinct.

`final_state_known` is handled correctly for the available final-state
snapshot. ActPlane has one available and one missing Git worktree: 24 artifact
rows and 60 mutation rows from the missing worktree are marked unknown rather
than absent. All other artifact rows have a queryable worktree. No confirmed
create in the authoritative corpus has unknown final state, so the persistence
denominators are exactly 983 AgentSight, 50 ActPlane, and 10 eunomia.dev; the
other three projects remain N/A. Existing-file writes retain
`content_durability=unknown` and never enter persistence.

This endpoint is path/lineage persistence, not byte-level durability. The
paper must preserve that wording. Status-`observed` lifecycle actions are
action evidence rather than confirmed filesystem success; they may shape
lineage boundaries or conservative competing outcomes, but only status-`ok`
actions enter the confirmed-mutation and confirmed-create endpoints. This is a
scope limitation, not a basis for a stronger system-effect claim.

## 4. Reuse, validation, and competing risks

For every confirmed non-delete mutation, I recomputed the next artifact access,
delete competitor, same-artifact next mutation/delete, and next recognized
successful validation. All endpoint IDs, event-step distances, wall-clock
distances, censoring outcomes, and cross-session flags match the mutation CSV.

Validation association is same-worktree and strictly after the focal mutation.
It counts as observed only when adapter-derived `effect == test` and
`status == ok` occurs before the same artifact's next mutation/delete. A test
from another worktree never qualifies. If supersession occurs first, the row is
`competing_supersede`; otherwise an unobserved endpoint is censored at the last
admitted action. This establishes temporal association only, not that the test
covered or validated the mutation.

The summary recomputation matches exactly:

| Project | Persistence | Reuse | Recognized validation before supersession |
|---|---:|---:|---:|
| AgentSight | 939/983 | 5,558/6,118 | 2,077/6,118 |
| ActPlane | 3/50 | 5,476/5,630 | 873/5,630 |
| bpf-developer-tutorial | N/A | 264/282 | N/A (coverage) |
| eunomia.dev | 4/10 | 141/157 | 32/157 |
| agentskill-observability-paper | N/A | 176/196 | N/A (coverage) |
| academic-writing-skills | N/A | 239/248 | N/A (coverage) |

The Aalen--Johansen implementation is correct for one event of interest plus
pooled competing outcomes: at each tied event-step it increments the CIF by
`S(t-) * d_interest / n_risk`, updates survival using interest plus competing
events, and removes censoring only after the event-time update. Risk tables use
the conventional `duration >= horizon` count. Independent final reuse CIFs are
93.67%, 97.38%, 97.69%, 89.91%, 91.15%, and 98.59% in project order; the three
qualified validation CIFs are 34.83%, 15.52%, and 20.65%. These values agree
with F3. They are descriptive mutation-episode curves; rows within a project
are not treated as independent samples for population inference.

## 5. Qualification and activity comparison

The preregistered gates recompute to:

- longitudinal-qualified: 6/6;
- persistence-qualified: 3/6;
- reuse-qualified: 6/6; and
- recognized-validation-qualified: 3/6.

Therefore persistence and validation correctly stop at source/measurement
coverage. F4 suppresses their rank correlations and labels both panels
`Coverage only (3/6 cases); correlation stopped`. For reuse, the six observed
proportions range from 89.80% to 97.26%. Independent average-rank calculation
gives Spearman `rho = 0.08571428571428572`, shown as `0.09` in F4. With only six
author-associated cases, this is a descriptive contrast and supplies neither a
population p-value nor a causal claim.

No external baseline is required for this descriptive census. F4's activity
volume is an internal competing description, not a method-superiority
baseline. The result cannot establish that the proposed representation is
better than a summary/log baseline; that question remains RQ7.

## 6. Figure audit

I inspected the full-resolution F3 and F4 PNGs and regenerated them from the
frozen CSVs.

- F3 labels exact persistence numerators/denominators, marks three projects as
  N/A, uses complete competing-risk horizons rather than a chosen success
  window, includes per-project curve denominators and at-risk tables, and
  visibly states both 3/6 coverage stops.
- F4 labels every point with its exact fraction, uses only worktree-attributed
  Tool actions on the log-scaled x-axis, and does not show stopped
  correlations for the two under-covered dimensions.

The figures are non-misleading under their captions and the plan's construct
definitions. Captions must retain the terms **adapter-recognized validation**,
**path/lineage persistence**, **worktree-attributed Tool actions**, and
**descriptive six-case result**. In particular, the shorter F4 panel title
“Validated before supersession” must not be quoted without the construct
qualification supplied by the caption.

## 7. Verification commands rerun

The independent review reran:

```text
cargo test --manifest-path agent-session/Cargo.toml --quiet  # 11 passed
cargo test --manifest-path agentvis/Cargo.toml --quiet       # 35 passed
python3 -m py_compile agentvis/research/plot_rq1.py           # passed
python3 agentvis/research/plot_rq1.py --input <frozen raw> --output <temporary dir>
                                                              # both PNG hashes reproduced
```

## 8. Non-blocking reporting limitations

1. `source_events` is a scanner/source-record coverage count that includes LLM
   records; it must not be described as the cutoff-bounded Tool-event
   denominator. `tool_actions` is the relevant admitted action count.
2. Final existence was queried in the same read-only run as extraction, but it
   is still a workspace snapshot rather than content durability or a historical
   filesystem snapshot reconstructed at each action.
3. Adapter-recognized validation is incomplete by construction and does not
   establish test coverage. Zero recognized validations is reported as N/A
   coverage, not “no validation.”
4. The six cases are author-associated and mutation rows are correlated within
   repositories. No population, causal, tool-ranking, or human-productivity
   inference is supported.

Subject to these already declared interpretation boundaries, the authoritative
RQ1 run and F3/F4 are valid for paper update.
