# R408 Chinese Induction PDF Freshness

This artifact checks that the tracked Chinese PDF contains the induction display table text.
It is not a new empirical experiment.

- Status: pass
- Git commit: `65c17a77690931b28d5938544fc5b58a94366b3b`
- Extracted PDF characters: 58828

## Token Checks

| Token | Source | Required | Present | Detail |
| --- | --- | --- | --- | --- |
| 自动 operation-stack induction 的 claim-facing 证据 | Chinese PDF | True | True | present |
| 递归形成、hidden-label 定位消融和深度调优 | Chinese PDF | True | True | present |
| E1 recursive formation | Chinese PDF | True | True | present |
| E2 localization ablation | Chinese PDF | True | True | present |
| E3 depth actionability | Chinese PDF | True | True | present |
| work@5 | Chinese PDF | True | True | present |
| 0.653 | Chinese PDF | True | True | present |
| depth 3 | Chinese PDF | True | True | present |
| 0.2865 | Chinese PDF | True | True | present |
| R402 | Chinese PDF | False | False | must be absent from reader-facing PDF text |
| R403 | Chinese PDF | False | False | must be absent from reader-facing PDF text |
| R404 | Chinese PDF | False | False | must be absent from reader-facing PDF text |
| R407 | Chinese PDF | False | False | must be absent from reader-facing PDF text |
| R408 | Chinese PDF | False | False | must be absent from reader-facing PDF text |
| 读者问题 | R407 table fragment | True | True | present |
| 递归形成、hidden-label 定位消融和深度调优 | R407 table fragment | True | True | present |

## Checks

| Check | Passed | Detail |
| --- | --- | --- |
| pdftotext_extracts_chinese_pdf | True | ok |
| r407_display_passed | True | R407 table-generation checks still pass. |
| chinese_tex_inputs_r407_table | True | The Chinese TeX source inputs the R407 table fragment. |
| r407_table_is_reader_facing | True | The table fragment uses reader-facing labels and no R-run caption. |
| pdf_contains_required_induction_tokens | True | The tracked Chinese PDF contains the induction display rows and headline numbers. |
| pdf_has_no_induction_run_ledger_tokens | True | The tracked Chinese PDF does not expose R402/R403/R404/R407/R408 in the induction display text. |
| english_submodule_not_a_source | True | This gate reads only outer Chinese paper and R407 artifacts. |
