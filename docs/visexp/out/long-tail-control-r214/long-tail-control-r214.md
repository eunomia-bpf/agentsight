# R214 Long-Tail Control Loop

Status: `long_tail_control_loop_ready_no_quality_claims`

## Boundary

- Reads generated R196/R201/R205/R209/R213 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM or update the canonical display map.
- Specifies display-control gates only; no semantic adequacy or merge-quality claim.

## Policy

The default compact view is active-alias-only with pending overlays. Profile merges, regenerated tags, and contextual splits may be shown as candidates, but they cannot change display membership until a reviewed display-map diff exists.

Active default merge rows: `63`.
Pending candidate rows: `209`.
Review-required rows/support: `323` / `1.926`%.
Regeneration candidates: `41` attempted, `41` grammar-valid, `0` promotable without human labels.
Rollup preview rows: `7`; active by default: `False`.
Failed control triggers: `prompt_review_budget, head_stability_under_high_tail_threshold`.

## Dimension Priorities

| dimension | raw tags | canonical tags | long-tail support % | review support % | priority | mode |
|---|---:|---:|---:|---:|---|---|
| overall | 1546 | 1364 | 1.746 | 1.926 | monitor_pending_load | display+pending |
| llm | 1423 | 1254 | 1.903 | 1.376 | stable_default | display |
| prompt | 328 | 279 | 2.996 | 3.258 | prioritize_review | pending |
| session | 60 | 49 | 0.397 | 0.938 | stable_default | display |

## Action Gates

| action | rows | default effect | gate |
|---|---:|---|---|
| active_alias_display | 63 | active | deterministic alias only; raw drilldown required |
| pending_profile_merge_candidate | 168 | pending | requires paired merge-risk review and display-map diff |
| pending_llm_regenerated_or_split_candidate | 41 | candidate_only | requires R202 grammar check plus R203 promotion review |
| review_required_total | 323 | candidate_only | any reviewed map update must be paired/adjudicated |
| keep_rare_distinct | 1241 | raw_preserved | none; rare distinct tags are not hidden in other |
| keep_head | 184 | active_raw_or_canonical | preserve unless sensitivity or human labels show risk |

## Trigger Gates

| trigger | actual | threshold | pass | response |
|---|---:|---:|---|---|
| overall_long_tail_budget | 1.746 | <= 3.0 | True | default display can stay alias-only with raw drilldown |
| overall_review_budget | 1.926 | <= 2.0 | True | pending overlay is acceptable as a default warning surface |
| prompt_review_budget | 3.258 | <= 3.0 | False | prioritize prompt-level review before promoting candidates |
| head_stability_under_high_tail_threshold | 65.217 | >= 80.0 | False | do not raise tail thresholds automatically; require review |
| hidden_other_bucket | 0.0 | <= 0.0 | True | no hidden other bucket is present |
| display_drilldown_membership | 1.0 | >= 1.0 | True | display drilldown matches active map membership |

## Rollup Preview

The rollup preview groups raw-tag rows by governance state so users can inspect long-tail burden. It is not the default flamegraph membership.

| bucket | rows | support | active display | gate |
|---|---:|---:|---|---|
| head_preserved | 184 | 464133 | True | none; preserve broad semantic heads unless later evidence shows harm |
| rare_distinct_preserved | 1241 | 6025 | True | none; keep visible rather than hiding under other |
| active_alias_overlay | 63 | 2947 | True | deterministic alias plus raw drilldown |
| pending_profile_merge | 168 | 5697 | False | paired merge-risk review plus reviewed display-map diff |
| pending_review_merge_no_candidate | 114 | 560 | False | paired merge-risk review; no candidate display tag is active |
| pending_llm_regeneration | 39 | 1413 | False | R202 grammar-valid candidate plus R203 promotion review |
| pending_contextual_split | 2 | 1623 | False | split review plus reviewed display-map diff |

## Review Priority Sample

| rank | dimension | raw tag | active display | candidate | support | reason |
|---:|---|---|---|---|---:|---|
| 1 | prompt | `ignored` | `ignored` | `refactor` | 1221 | review regenerated label before display-map promotion |
| 2 | session | `uxdesign` | `uxdesign` | `design` | 1148 | review profile merge before display-map promotion |
| 3 | prompt | `designcodex` | `designcodex` | `design` | 1074 | review profile merge before display-map promotion |
| 4 | prompt | `testcodex` | `testcodex` | `test` | 982 | review profile merge before display-map promotion |
| 5 | prompt | `codex` | `codex` | `codexnavigate` | 402 | review regenerated label before display-map promotion |
| 6 | llm | `uxdesign` | `uxdesign` | `design` | 357 | review profile merge before display-map promotion |
| 7 | llm | `check` | `check` | `review` | 294 | review regenerated label before display-map promotion |
| 8 | prompt | `reviewbu` | `reviewbu` | `review` | 254 | review profile merge before display-map promotion |
| 9 | session | `reviewbu` | `reviewbu` | `review` | 254 | review profile merge before display-map promotion |
| 10 | prompt | `testcodexrun` | `testcodexrun` | `test` | 198 | review profile merge before display-map promotion |
| 11 | prompt | `analyzesess` | `analyzesess` | `analyze` | 179 | review profile merge before display-map promotion |
| 12 | prompt | `codexcheck` | `codexcheck` | `codexanalyze` | 176 | review regenerated label before display-map promotion |

## Claim Boundary

R214 supports the existence of an auditable long-tail control loop: raw tags remain immutable, deterministic aliases may be active, and all LLM-regenerated/profile/split candidates stay pending until review. It does not prove that any candidate merge or regenerated label is correct.
