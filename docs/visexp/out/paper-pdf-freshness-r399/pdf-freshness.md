# R399 Paper PDF Freshness Gate

Status: `pass`
Checks: 9/9
Token checks: 29/29

The tracked Chinese and English paper PDFs contain the same main-display path that the TeX sources expose. This is an E4 replayability/scope-control check, not a new empirical experiment.

## Checks

| Check | Passed | Detail |
|---|---:|---|
| prerequisite_gates_pass | True | Prerequisite statuses={'R396 paper build smoke': 'pass', 'R398 current three-plus-one': 'pass'} |
| pdftotext_available | True | pdftotext=/usr/bin/pdftotext |
| tracked_pdfs_exist | True | PDF bytes={'chinese_pdf_bytes': 590073, 'english_pdf_bytes': 594286} |
| pdftotext_extraction_succeeds | True | Chinese rc=0 stderr=; English rc=0 stderr= |
| source_display_path_tokens_present | True | Chinese and English TeX sources contain the main-display path tokens. |
| tracked_pdfs_contain_display_path | True | Tracked Chinese and English PDFs contain the display-path text after PDF text extraction. |
| pdf_non_claim_scope_visible | True | Tracked English PDF keeps fifth-experiment, accuracy, productivity, boundary, and ecosystem non-claims visible. |
| english_submodule_captured_by_parent | True | submodule_head=444ef4c51c0d09ab65ef276ebc37a5ba26b7e63c; parent_index=444ef4c51c0d09ab65ef276ebc37a5ba26b7e63c |
| source_status_tracked_or_dirty_allowed | True | All inputs are tracked or intentionally dirty while this gate is generated. |

## Token Checks

| Kind | Present | Token |
|---|---:|---|
| chinese_source | True | `主文图表形成一条固定证据路径` |
| chinese_source | True | `表~\ref{tab:results} 是四个 block 的 claim map` |
| chinese_source | True | `hidden-label fidelity 和 baseline tradeoff` |
| chinese_source | True | `mechanism/actionability` |
| chinese_source | True | `replay/cost 证据` |
| chinese_source | True | `补充的 portfolio、case 和 verdict 视图只用于解释这些主图表的数据来源、反例和适用边界` |
| english_source | True | `The main-paper displays follow this path` |
| english_source | True | `Table~\ref{tab:core-results} is the four-block claim map` |
| english_source | True | `provide hidden-label fidelity and baseline tradeoff evidence` |
| english_source | True | `provide mechanism/actionability evidence` |
| english_source | True | `provide replay and cost evidence` |
| english_source | True | `Supporting materials contain the larger portfolio, case, verdict, and consistency tables` |
| chinese_pdf | True | `主文图表形成一条固定证据路径` |
| chinese_pdf | True | `四个 block 的 claim map` |
| chinese_pdf | True | `hidden-label fidelity 和 baseline tradeoff` |
| chinese_pdf | True | `mechanism/actionability` |
| chinese_pdf | True | `replay/cost 证据` |
| chinese_pdf | True | `适用边界` |
| english_pdf | True | `The main-paper displays follow this path` |
| english_pdf | True | `four-block claim map` |
| english_pdf | True | `hidden-label fidelity and baseline` |
| english_pdf | True | `mechanism/actionability evidence` |
| english_pdf | True | `provide replay` |
| english_pdf | True | `Supporting materials` |
| english_non_claims | True | `not a fifth core` |
| english_non_claims | True | `not a hidden-label accuracy result` |
| english_non_claims | True | `human productivity result` |
| english_non_claims | True | `not automatic boundary discovery` |
| english_non_claims | True | `complete ecosystem compatibility` |
