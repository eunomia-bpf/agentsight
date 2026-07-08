# R399 Paper PDF Freshness Gate

Status: `pass`
Checks: 9/9
Token checks: 13/30

The tracked Chinese paper PDF contains the same main-display path that the TeX source exposes. The English submodule is read-only in this worktree, so R405 records any English sync gap separately. This is an E4 replayability/scope-control check, not a new empirical experiment.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| prerequisite_gates_pass | True | Prerequisite statuses={'R396 paper build smoke': 'pass', 'R398 current three-plus-one': 'pass', 'R405 English read-only gap audit': 'pass'} |
| pdftotext_available | True | pdftotext=/usr/bin/pdftotext |
| tracked_pdfs_exist | True | PDF bytes={'chinese_pdf_bytes': 616854, 'english_pdf_bytes': 597905} |
| pdftotext_extraction_succeeds | True | Chinese rc=0 stderr=; English rc=0 stderr= |
| source_display_path_tokens_present | True | Chinese TeX source contains the main-display path tokens; English is synced or R405 records a read-only sync gap. |
| tracked_pdfs_contain_display_path | True | Tracked Chinese PDF contains the display-path text after extraction; English PDF is synced or R405 records a read-only sync gap. |
| pdf_non_claim_scope_visible | True | Tracked English PDF keeps scope non-claims visible, or R405 records the read-only English sync gap. |
| english_submodule_captured_by_parent | True | submodule_head=138b7a3ad3b6ae794ebf6c86ea94e8feaf8da86e; parent_index=b6672cbf3e2316af67b5312ca3f1d1dee32b9ab4 |
| source_status_tracked_or_dirty_allowed | True | All inputs are tracked or intentionally dirty while this gate is generated. |

## Token Checks

| Kind | Present | Token |
|---|---:|---|
| chinese_source | True | `主文图表按这条路径阅读` |
| chinese_source | True | `表~\ref{tab:results} 是四个 block 的 claim map` |
| chinese_source | True | `hidden-label fidelity 和 baseline tradeoff` |
| chinese_source | True | `mechanism/actionability` |
| chinese_source | True | `replay/cost 证据` |
| chinese_source | True | `补充的 portfolio、case 和 verdict 视图只用于解释这些主图表的数据来源、反例和适用边界` |
| english_source | False | `The main-paper displays follow this path` |
| english_source | False | `Table~\ref{tab:core-results} is the four-block claim map` |
| english_source | False | `provide hidden-label fidelity and baseline tradeoff evidence` |
| english_source | False | `provide mechanism/actionability evidence` |
| english_source | False | `provide replay and cost evidence` |
| english_source | False | `Supporting materials contain the larger portfolio, case, verdict, and consistency tables` |
| chinese_pdf | True | `主文图表按这条路径阅读` |
| chinese_pdf | True | `四个 block 的 claim map` |
| chinese_pdf | True | `hidden-label` |
| chinese_pdf | True | `baseline tradeoff` |
| chinese_pdf | True | `mechanism/actionability` |
| chinese_pdf | True | `replay/cost 证据` |
| chinese_pdf | True | `适用边界` |
| english_pdf | False | `The main-paper displays follow this path` |
| english_pdf | False | `four-block claim map` |
| english_pdf | False | `hidden-label fidelity and baseline` |
| english_pdf | False | `mechanism/actionability evidence` |
| english_pdf | False | `provide replay` |
| english_pdf | False | `Supporting materials` |
| english_non_claims | False | `not a fifth core` |
| english_non_claims | False | `not a hidden-label accuracy result` |
| english_non_claims | False | `human productivity result` |
| english_non_claims | False | `not automatic boundary discovery` |
| english_non_claims | False | `complete ecosystem compatibility` |
