# R267 Post-R266 OSDI Review Gate

Run ID: `R267`
Status: `post_r266_osdi_review_gate_passed`
Generated at: `2026-06-20T03:05:14+00:00`
Source command: `python3 docs/visexp/r267_post_r266_osdi_review_gate.py`

## Verdict

Credible conference-paper mechanism evidence, but not a Level 4 systems narrative and not weak-accept-ready because C5 and C6 have no admissible human outcome evidence.

R267 is review hygiene only. It adds no participant responses, no human labels, and no weak-accept support.

## Severity-Ranked Findings

| Severity | Claim | Finding |
|----------|-------|---------|
| `blocker` | C5 developer utility | No admissible participant outcome evidence; packets/forms/scorers exist but responses remain zero. |
| `blocker` | C6 tag adequacy | No human adequacy labels; syntax/stability and behavior association remain proxies only. |
| `major` | C4 exact lineage | Strong in fixed/controlled scopes, but broad Claude/Codex-launched target-network coverage remains partial. |
| `major` | C7 artifact readiness | Install/package smokes are useful but do not prove crates.io, external-machine, write-set, or external-developer success. |
| `minor` | R264/R265/R266 naming | Names are easy to overread, but contents and paper/state wording keep them scoped as hygiene gates. |

## Claim Verdict

| Claim | Verdict |
|-------|---------|
| `C1` | supported for this local history run |
| `C2` | syntax/latency supported; adequacy not supported |
| `C3` | mechanism supported; quality/user value not supported |
| `C4` | supported in fixed/controlled scopes; broad scope partial |
| `C5` | unsupported |
| `C6` | protocol ready only; human adequacy unsupported |
| `C7` | partial |

## First Next Experiment

- Name: `paper-scale C5 user-task study`.
- Private input: `private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv`.
- Preflight: `python3 docs/visexp/r264_human_return_intake_preflight.py`.
- Score: `python3 docs/visexp/r195_human_evidence_pipeline.py --r142-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv --r142-bundle docs/visexp/out/user-task-benchmark.json --r142-answer-key docs/visexp/out/user-task-answer-key.csv --r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv --scored-dir private/completed-paper-scale-r264/r195-scored --out-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json --out-md private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.md`.
- Oracle: C5 passes only if all four baselines are beaten on primary utility tasks by >=10 pp exact accuracy or >=20% median time reduction, Holm-corrected participant/task/order fixed-effect permutation p<=0.05, at least 12 participants, at least 8 task pairs per baseline, and no >5 pp false-positive increase.

## Mechanical Checks

| Check | Passed | Observed |
|-------|--------|----------|
| `subagent_review_keeps_level3_not_weak_accept` | `True` | `{"maturity": "Level 3", "weak_accept_ready": false}` |
| `c5_still_has_zero_participant_responses` | `True` | `{"c5_supported": false, "participant_count": 0, "response_count": 0, "status": "participant_results_empty"}` |
| `c6_label_gates_still_empty` | `True` | `{"r124_adequacy_supported": false, "r124_final_label_count": 0, "r190_canonicalization_quality_supported": false, "r190_final_label_count": 0, "r203_final_label_count": 0, "r203_long_tail_promotion_review_supported": false}` |
| `r264_r265_r266_are_hygiene_only` | `True` | `{"r264_status": "awaiting_private_returns", "r264_weak_accept_supported": false, "r265_adjudicated_claim_gates_false": true, "r265_status": "passed", "r266_public_claim_update_allowed": false, "r266_status": "awaiting_private_scored_r195", "r266_weak_accept_supported": false}` |
| `paper_keeps_post_r266_review_boundary` | `True` | `{"c5_missing": true, "c6_missing": true, "no_upgrade_boundary": true, "r267_review_hygiene_scoped": true, "weak_accept_boundary": true}` |
| `state_and_followup_record_r267_without_upgrading_claims` | `True` | `{"followup_mentions_r267": true, "state_false_weak_accept": true, "state_latest_r267": true, "state_no_upgrade_boundary": true}` |
| `evidence_docs_keep_real_human_requirement` | `True` | `{"claim_verdict_mentions_r266": true, "experiment_audit_mentions_r266": true, "human_labels": true, "real_participant_responses": true, "subagent_review_boundary": true}` |

## Claim Gate

- c5_supported: `False`
- c6_supported: `False`
- developer_utility_supported: `False`
- tag_adequacy_supported: `False`
- outcome_evidence_added: `False`
- weak_accept_supported: `False`

## Residual Risks

- Weak accept still requires real C5 participant responses and real C6 human labels scored through R195/R266.
- R267 is a read-only review gate and cannot substitute for outcome evidence.
- C4 exact lineage remains scoped to fixed/controlled workloads; broad agent-launched target-network coverage is partial.
- C7 still lacks crates.io publish/readback, external-machine install, full write-set audit, and external developer feedback.
