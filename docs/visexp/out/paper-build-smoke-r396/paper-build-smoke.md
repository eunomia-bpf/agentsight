# R396 Paper Build Smoke Gate

Status: `pass`
Checks: 7/7

Both paper drafts build locally in temporary output locations, final logs have no unresolved references/citations, and the English ACM draft has figure description metadata for the non-flamegraph portfolio figure.

## Commands

| Name | Return Code | Elapsed (s) | Command |
|---|---:|---:|---|
| english-make | 0 | 1.284 | `make` |
| chinese-xelatex-1 | 0 | 0.829 | `xelatex -output-directory=/tmp/agentsight-r396-paper-lraw2dey/chinese-build -interaction=nonstopmode main.tex` |
| chinese-xelatex-2 | 0 | 0.819 | `xelatex -output-directory=/tmp/agentsight-r396-paper-lraw2dey/chinese-build -interaction=nonstopmode main.tex` |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| build_commands_exit_zero | True | Return codes=[0, 0, 0] |
| paper_pdfs_exist | True | English PDF bytes=594228; Chinese PDF bytes=593719 |
| english_log_has_no_unresolved_refs_or_citations | True | Hits=[] |
| chinese_log_has_no_unresolved_refs | True | Hits=[] |
| english_acm_image_description_warning_absent | True | Hits=[] |
| r395_claim_alignment_still_passes | True | R395 status=pass |
| source_status_tracked_or_dirty_allowed | True | All build inputs/outputs are tracked or intentionally dirty while this build gate is generated. |
