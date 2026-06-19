# R247 Human Evidence Distribution Bundle

Status: `distribution_bundle_ready_no_outcomes`

R247 packages the already-tested R243 static collection kit into one offline
tarball and records the exact R195 return filenames. It does not create or
score human evidence.

## Package

- path: `docs/visexp/out/human-evidence-distribution-r247/agentflame-human-evidence-r247.tar.gz`
- sha256: `2012288df25904774e71efa18b63a5ee61f1e7ef7b08619c8901c5ba7d582043`
- bytes: `182992`
- members: `17`

## Return Files

| File | Source | Rows | Required gate |
|------|--------|------|---------------|
| `r142-pilot-responses.csv` | `coordinator/r142-merge.html` | 70 | yes |
| `r124-labeler-1.csv` | `labelers/r124-labeler-1.html` | 300 | yes |
| `r124-labeler-2.csv` | `labelers/r124-labeler-2.html` | 300 | yes |
| `r190-labeler-1.csv` | `labelers/r190-labeler-1.html` | 160 | if claiming merge quality |
| `r190-labeler-2.csv` | `labelers/r190-labeler-2.html` | 160 | if claiming merge quality |
| `r203-labeler-1.csv` | `labelers/r203-labeler-1.html` | 41 | if claiming regenerated-tag promotion |
| `r203-labeler-2.csv` | `labelers/r203-labeler-2.html` | 41 | if claiming regenerated-tag promotion |

## Checks

| Check | Passed |
|-------|--------|
| `r243_ready` | `True` |
| `r244_export_smoke_passed` | `True` |
| `r207_launch_ready` | `True` |
| `r195_awaiting_inputs` | `True` |
| `r246_gate_passed` | `True` |
| `form_counts_match` | `True` |
| `return_checklist_rows` | `True` |
| `html_links_local` | `True` |
| `source_leak_scan_passed` | `True` |
| `tar_member_count_matches` | `True` |
| `tar_leak_scan_passed` | `True` |
| `no_synthetic_exports_packaged` | `True` |

## Claim Gate

- weak_accept_supported: `False`
- c5_supported: `False`
- c6_adequacy_supported: `False`
- canonicalization_quality_supported: `False`
- long_tail_promotion_review_supported: `False`
- outcome_evidence_added: `False`
