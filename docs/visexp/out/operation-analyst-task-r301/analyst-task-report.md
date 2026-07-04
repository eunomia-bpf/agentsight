# R301 Width-Ranked Analyst Task Proxy

R301 reuses the labeled operation JSONL from R300 and ranks groups only by width. The visible packet excludes oracle labels; the answer key is separate.

## Headline

At a 30% inspected-operation budget, operation stacks recover a median 33.6% of hidden positives while inspecting 4.5 groups; fixed-session stacks recover 28.4% while inspecting 25.5 groups. At top-10 width-ranked groups, operation stacks recover a median 64.1% of positives, compared with 19.5% for fixed-session stacks, but they require a larger work fraction, so the result supports cross-session aggregation rather than a universal default-ranking win.

## Median Scores

| View | Budget | Tasks | Median recall | Median lift | Median work fraction | Median groups | Tasks recall >= 50% |
|---|---|---:|---:|---:|---:|---:|---:|
| fixed_session | budget_10pct_operations | 6 | 0.0754 | 0.7587 | 0.0999 | 9.0 | 0 |
| fixed_session | budget_20pct_operations | 6 | 0.186 | 0.9324 | 0.2 | 17.0 | 1 |
| fixed_session | budget_30pct_operations | 6 | 0.2844 | 0.9482 | 0.2999 | 25.5 | 1 |
| fixed_session | budget_50pct_operations | 6 | 0.4715 | 0.9433 | 0.4999 | 51.0 | 2 |
| fixed_session | top_10_groups | 6 | 0.1951 | 0.94 | 0.2124 | 10.0 | 2 |
| fixed_session | top_20_groups | 6 | 0.2488 | 0.9448 | 0.3001 | 20.0 | 2 |
| fixed_session | top_5_groups | 6 | 0.1313 | 0.897 | 0.1413 | 5.0 | 1 |
| flat | budget_10pct_operations | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| flat | budget_20pct_operations | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| flat | budget_30pct_operations | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| flat | budget_50pct_operations | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| flat | top_10_groups | 6 | 1.0 | 1.0 | 1.0 | 1.0 | 6 |
| flat | top_20_groups | 6 | 1.0 | 1.0 | 1.0 | 1.0 | 6 |
| flat | top_5_groups | 6 | 1.0 | 1.0 | 1.0 | 1.0 | 6 |
| label_drilldown | budget_10pct_operations | 6 | 0.0057 | 0.0571 | 0.0999 | 3.0 | 0 |
| label_drilldown | budget_20pct_operations | 6 | 0.0012 | 0.0061 | 0.2 | 4.0 | 1 |
| label_drilldown | budget_30pct_operations | 6 | 0.0741 | 0.2472 | 0.2999 | 6.0 | 1 |
| label_drilldown | budget_50pct_operations | 6 | 0.1226 | 0.2453 | 0.4999 | 6.5 | 1 |
| label_drilldown | top_10_groups | 6 | 0.4073 | 0.531 | 0.7561 | 10.0 | 3 |
| label_drilldown | top_20_groups | 6 | 0.8478 | 0.9481 | 0.8742 | 20.0 | 4 |
| label_drilldown | top_5_groups | 6 | 0.0 | 0.0 | 0.551 | 5.0 | 2 |
| operation_stack | budget_10pct_operations | 6 | 0.1159 | 1.1656 | 0.0999 | 3.0 | 0 |
| operation_stack | budget_20pct_operations | 6 | 0.2414 | 1.2073 | 0.2 | 4.0 | 1 |
| operation_stack | budget_30pct_operations | 6 | 0.3361 | 1.1203 | 0.2999 | 4.5 | 0 |
| operation_stack | budget_50pct_operations | 6 | 0.5585 | 1.1172 | 0.4999 | 7.0 | 4 |
| operation_stack | top_10_groups | 6 | 0.6415 | 1.0795 | 0.6713 | 10.0 | 5 |
| operation_stack | top_20_groups | 6 | 0.7736 | 1.0392 | 0.781 | 20.0 | 6 |
| operation_stack | top_5_groups | 6 | 0.4746 | 1.0488 | 0.5424 | 5.0 | 3 |

## Task Scores

| Task | View | Budget | Recall | Lift | Work fraction | Groups | Positives found |
|---|---|---|---:|---:|---:|---:|---:|
| agentreward_looping | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 504 |
| agentreward_looping | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 504 |
| agentreward_looping | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 504 |
| agentreward_looping | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_looping | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_looping | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_looping | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_looping | fixed_session | top_5_groups | 0.2976 | 0.7355 | 0.4047 | 5 | 150 |
| agentreward_looping | fixed_session | top_10_groups | 0.5952 | 0.9751 | 0.6104 | 10 | 300 |
| agentreward_looping | fixed_session | top_20_groups | 1.0 | 1.0535 | 0.9492 | 20 | 504 |
| agentreward_looping | fixed_session | budget_10pct_operations | 0.0595 | 0.6027 | 0.0988 | 3 | 30 |
| agentreward_looping | fixed_session | budget_20pct_operations | 0.1786 | 0.8978 | 0.1989 | 4 | 90 |
| agentreward_looping | fixed_session | budget_30pct_operations | 0.1786 | 0.5971 | 0.299 | 4 | 90 |
| agentreward_looping | fixed_session | budget_50pct_operations | 0.4167 | 0.8345 | 0.4993 | 8 | 210 |
| agentreward_looping | operation_stack | top_5_groups | 0.6508 | 1.0359 | 0.6283 | 5 | 328 |
| agentreward_looping | operation_stack | top_10_groups | 0.8948 | 1.1001 | 0.8134 | 10 | 451 |
| agentreward_looping | operation_stack | top_20_groups | 0.9841 | 1.0413 | 0.9451 | 20 | 496 |
| agentreward_looping | operation_stack | budget_10pct_operations | 0.0833 | 0.8438 | 0.0988 | 3 | 42 |
| agentreward_looping | operation_stack | budget_20pct_operations | 0.119 | 0.5985 | 0.1989 | 3 | 60 |
| agentreward_looping | operation_stack | budget_30pct_operations | 0.3552 | 1.1877 | 0.299 | 4 | 179 |
| agentreward_looping | operation_stack | budget_50pct_operations | 0.4901 | 0.9815 | 0.4993 | 4 | 247 |
| agentreward_looping | label_drilldown | top_5_groups | 0.8016 | 1.0984 | 0.7298 | 5 | 404 |
| agentreward_looping | label_drilldown | top_10_groups | 0.8988 | 1.0417 | 0.8628 | 10 | 453 |
| agentreward_looping | label_drilldown | top_20_groups | 0.994 | 1.0107 | 0.9835 | 20 | 501 |
| agentreward_looping | label_drilldown | budget_10pct_operations | 0.1429 | 1.4464 | 0.0988 | 2 | 72 |
| agentreward_looping | label_drilldown | budget_20pct_operations | 0.0635 | 0.3192 | 0.1989 | 3 | 32 |
| agentreward_looping | label_drilldown | budget_30pct_operations | 0.2083 | 0.6967 | 0.299 | 6 | 105 |
| agentreward_looping | label_drilldown | budget_50pct_operations | 0.7143 | 1.4305 | 0.4993 | 4 | 360 |
| agentreward_side_effect | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 202 |
| agentreward_side_effect | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 202 |
| agentreward_side_effect | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 202 |
| agentreward_side_effect | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_side_effect | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_side_effect | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_side_effect | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentreward_side_effect | fixed_session | top_5_groups | 1.0 | 2.4712 | 0.4047 | 5 | 202 |
| agentreward_side_effect | fixed_session | top_10_groups | 1.0 | 1.6382 | 0.6104 | 10 | 202 |
| agentreward_side_effect | fixed_session | top_20_groups | 1.0 | 1.0535 | 0.9492 | 20 | 202 |
| agentreward_side_effect | fixed_session | budget_10pct_operations | 0.0 | 0.0 | 0.0988 | 3 | 0 |
| agentreward_side_effect | fixed_session | budget_20pct_operations | 0.505 | 2.5387 | 0.1989 | 4 | 102 |
| agentreward_side_effect | fixed_session | budget_30pct_operations | 1.0 | 3.344 | 0.299 | 4 | 202 |
| agentreward_side_effect | fixed_session | budget_50pct_operations | 1.0 | 2.0027 | 0.4993 | 8 | 202 |
| agentreward_side_effect | operation_stack | top_5_groups | 0.6634 | 1.0559 | 0.6283 | 5 | 134 |
| agentreward_side_effect | operation_stack | top_10_groups | 0.8614 | 1.0589 | 0.8134 | 10 | 174 |
| agentreward_side_effect | operation_stack | top_20_groups | 0.9802 | 1.0371 | 0.9451 | 20 | 198 |
| agentreward_side_effect | operation_stack | budget_10pct_operations | 0.1139 | 1.1528 | 0.0988 | 3 | 23 |
| agentreward_side_effect | operation_stack | budget_20pct_operations | 0.5941 | 2.9867 | 0.1989 | 3 | 120 |
| agentreward_side_effect | operation_stack | budget_30pct_operations | 0.3069 | 1.0264 | 0.299 | 4 | 62 |
| agentreward_side_effect | operation_stack | budget_50pct_operations | 0.599 | 1.1997 | 0.4993 | 4 | 121 |
| agentreward_side_effect | label_drilldown | top_5_groups | 0.599 | 0.8334 | 0.7188 | 5 | 121 |
| agentreward_side_effect | label_drilldown | top_10_groups | 0.8267 | 0.9597 | 0.8615 | 10 | 167 |
| agentreward_side_effect | label_drilldown | top_20_groups | 0.9802 | 1.0022 | 0.9781 | 20 | 198 |
| agentreward_side_effect | label_drilldown | budget_10pct_operations | 0.3416 | 3.4585 | 0.0988 | 3 | 69 |
| agentreward_side_effect | label_drilldown | budget_20pct_operations | 0.599 | 3.0116 | 0.1989 | 5 | 121 |
| agentreward_side_effect | label_drilldown | budget_30pct_operations | 0.599 | 2.0031 | 0.299 | 6 | 121 |
| agentreward_side_effect | label_drilldown | budget_50pct_operations | 0.3416 | 0.6841 | 0.4993 | 4 | 69 |
| satraj_unsafe | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 622 |
| satraj_unsafe | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 622 |
| satraj_unsafe | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 622 |
| satraj_unsafe | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| satraj_unsafe | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| satraj_unsafe | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| satraj_unsafe | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| satraj_unsafe | fixed_session | top_5_groups | 0.0 | 0.0 | 0.035 | 5 | 0 |
| satraj_unsafe | fixed_session | top_10_groups | 0.0 | 0.0 | 0.07 | 10 | 0 |
| satraj_unsafe | fixed_session | top_20_groups | 0.0 | 0.0 | 0.14 | 20 | 0 |
| satraj_unsafe | fixed_session | budget_10pct_operations | 0.0129 | 0.1288 | 0.0999 | 15 | 8 |
| satraj_unsafe | fixed_session | budget_20pct_operations | 0.0 | 0.0 | 0.2 | 29 | 0 |
| satraj_unsafe | fixed_session | budget_30pct_operations | 0.0 | 0.0 | 0.2999 | 43 | 0 |
| satraj_unsafe | fixed_session | budget_50pct_operations | 0.0707 | 0.1415 | 0.4999 | 75 | 44 |
| satraj_unsafe | operation_stack | top_5_groups | 0.0 | 0.0 | 0.5181 | 5 | 0 |
| satraj_unsafe | operation_stack | top_10_groups | 0.1576 | 0.2412 | 0.6532 | 10 | 98 |
| satraj_unsafe | operation_stack | top_20_groups | 0.6785 | 0.8728 | 0.7774 | 20 | 422 |
| satraj_unsafe | operation_stack | budget_10pct_operations | 0.0 | 0.0 | 0.0999 | 2 | 0 |
| satraj_unsafe | operation_stack | budget_20pct_operations | 0.0 | 0.0 | 0.2 | 6 | 0 |
| satraj_unsafe | operation_stack | budget_30pct_operations | 0.1125 | 0.3753 | 0.2999 | 5 | 70 |
| satraj_unsafe | operation_stack | budget_50pct_operations | 0.0627 | 0.1254 | 0.4999 | 7 | 39 |
| satraj_unsafe | label_drilldown | top_5_groups | 0.0 | 0.0 | 0.5636 | 5 | 0 |
| satraj_unsafe | label_drilldown | top_10_groups | 0.2765 | 0.3861 | 0.7162 | 10 | 172 |
| satraj_unsafe | label_drilldown | top_20_groups | 0.8698 | 1.0549 | 0.8245 | 20 | 541 |
| satraj_unsafe | label_drilldown | budget_10pct_operations | 0.0 | 0.0 | 0.0999 | 4 | 0 |
| satraj_unsafe | label_drilldown | budget_20pct_operations | 0.0 | 0.0 | 0.2 | 4 | 0 |
| satraj_unsafe | label_drilldown | budget_30pct_operations | 0.1415 | 0.4718 | 0.2999 | 5 | 88 |
| satraj_unsafe | label_drilldown | budget_50pct_operations | 0.0 | 0.0 | 0.4999 | 6 | 0 |
| agentnet_incorrect_step | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 874 |
| agentnet_incorrect_step | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 874 |
| agentnet_incorrect_step | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 874 |
| agentnet_incorrect_step | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_incorrect_step | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_incorrect_step | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_incorrect_step | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_incorrect_step | fixed_session | top_5_groups | 0.0126 | 0.816 | 0.0154 | 5 | 11 |
| agentnet_incorrect_step | fixed_session | top_10_groups | 0.0263 | 0.9049 | 0.0291 | 10 | 23 |
| agentnet_incorrect_step | fixed_session | top_20_groups | 0.0481 | 0.8941 | 0.0537 | 20 | 42 |
| agentnet_incorrect_step | fixed_session | budget_10pct_operations | 0.0984 | 0.9845 | 0.0999 | 41 | 86 |
| agentnet_incorrect_step | fixed_session | budget_20pct_operations | 0.1934 | 0.967 | 0.2 | 92 | 169 |
| agentnet_incorrect_step | fixed_session | budget_30pct_operations | 0.2986 | 0.9955 | 0.3 | 154 | 261 |
| agentnet_incorrect_step | fixed_session | budget_50pct_operations | 0.5126 | 1.0252 | 0.5 | 300 | 448 |
| agentnet_incorrect_step | operation_stack | top_5_groups | 0.3284 | 1.1075 | 0.2965 | 5 | 287 |
| agentnet_incorrect_step | operation_stack | top_10_groups | 0.5137 | 1.1198 | 0.4588 | 10 | 449 |
| agentnet_incorrect_step | operation_stack | top_20_groups | 0.7265 | 1.1608 | 0.6259 | 20 | 635 |
| agentnet_incorrect_step | operation_stack | budget_10pct_operations | 0.1419 | 1.4195 | 0.0999 | 3 | 124 |
| agentnet_incorrect_step | operation_stack | budget_20pct_operations | 0.254 | 1.2703 | 0.2 | 5 | 222 |
| agentnet_incorrect_step | operation_stack | budget_30pct_operations | 0.3284 | 1.0947 | 0.3 | 6 | 287 |
| agentnet_incorrect_step | operation_stack | budget_50pct_operations | 0.5686 | 1.1373 | 0.5 | 13 | 497 |
| agentnet_incorrect_step | label_drilldown | top_5_groups | 0.0 | 0.0 | 0.2829 | 5 | 0 |
| agentnet_incorrect_step | label_drilldown | top_10_groups | 0.0 | 0.0 | 0.4442 | 10 | 0 |
| agentnet_incorrect_step | label_drilldown | top_20_groups | 0.0 | 0.0 | 0.6016 | 20 | 0 |
| agentnet_incorrect_step | label_drilldown | budget_10pct_operations | 0.0046 | 0.0458 | 0.0999 | 3 | 4 |
| agentnet_incorrect_step | label_drilldown | budget_20pct_operations | 0.0011 | 0.0057 | 0.2 | 6 | 1 |
| agentnet_incorrect_step | label_drilldown | budget_30pct_operations | 0.0057 | 0.0191 | 0.3 | 7 | 5 |
| agentnet_incorrect_step | label_drilldown | budget_50pct_operations | 0.0458 | 0.0915 | 0.5 | 14 | 40 |
| agentnet_redundant_step | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 733 |
| agentnet_redundant_step | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 733 |
| agentnet_redundant_step | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 733 |
| agentnet_redundant_step | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_redundant_step | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_redundant_step | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_redundant_step | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| agentnet_redundant_step | fixed_session | top_5_groups | 0.0205 | 1.0 | 0.0205 | 5 | 15 |
| agentnet_redundant_step | fixed_session | top_10_groups | 0.0341 | 0.8737 | 0.039 | 10 | 25 |
| agentnet_redundant_step | fixed_session | top_20_groups | 0.0709 | 0.9625 | 0.0737 | 20 | 52 |
| agentnet_redundant_step | fixed_session | budget_10pct_operations | 0.0914 | 0.9147 | 0.0999 | 29 | 67 |
| agentnet_redundant_step | fixed_session | budget_20pct_operations | 0.1774 | 0.8869 | 0.2 | 62 | 130 |
| agentnet_redundant_step | fixed_session | budget_30pct_operations | 0.2769 | 0.9232 | 0.3 | 102 | 203 |
| agentnet_redundant_step | fixed_session | budget_50pct_operations | 0.4679 | 0.936 | 0.5 | 199 | 343 |
| agentnet_redundant_step | operation_stack | top_5_groups | 0.3588 | 1.1159 | 0.3215 | 5 | 263 |
| agentnet_redundant_step | operation_stack | top_10_groups | 0.5866 | 1.2072 | 0.4859 | 10 | 430 |
| agentnet_redundant_step | operation_stack | top_20_groups | 0.7435 | 1.1659 | 0.6377 | 20 | 545 |
| agentnet_redundant_step | operation_stack | budget_10pct_operations | 0.1364 | 1.3652 | 0.0999 | 2 | 100 |
| agentnet_redundant_step | operation_stack | budget_20pct_operations | 0.2538 | 1.269 | 0.2 | 4 | 186 |
| agentnet_redundant_step | operation_stack | budget_30pct_operations | 0.3438 | 1.146 | 0.3 | 5 | 252 |
| agentnet_redundant_step | operation_stack | budget_50pct_operations | 0.5975 | 1.1952 | 0.5 | 12 | 438 |
| agentnet_redundant_step | label_drilldown | top_5_groups | 0.0 | 0.0 | 0.3048 | 5 | 0 |
| agentnet_redundant_step | label_drilldown | top_10_groups | 0.0 | 0.0 | 0.4676 | 10 | 0 |
| agentnet_redundant_step | label_drilldown | top_20_groups | 0.1392 | 0.2266 | 0.6141 | 20 | 102 |
| agentnet_redundant_step | label_drilldown | budget_10pct_operations | 0.0068 | 0.0683 | 0.0999 | 3 | 5 |
| agentnet_redundant_step | label_drilldown | budget_20pct_operations | 0.0 | 0.0 | 0.2 | 4 | 0 |
| agentnet_redundant_step | label_drilldown | budget_30pct_operations | 0.0068 | 0.0227 | 0.3 | 6 | 5 |
| agentnet_redundant_step | label_drilldown | budget_50pct_operations | 0.1405 | 0.2811 | 0.5 | 13 | 103 |
| osworld_group_start | flat | top_5_groups | 1.0 | 1.0 | 1.0 | 1 | 764 |
| osworld_group_start | flat | top_10_groups | 1.0 | 1.0 | 1.0 | 1 | 764 |
| osworld_group_start | flat | top_20_groups | 1.0 | 1.0 | 1.0 | 1 | 764 |
| osworld_group_start | flat | budget_10pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| osworld_group_start | flat | budget_20pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| osworld_group_start | flat | budget_30pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| osworld_group_start | flat | budget_50pct_operations | 0.0 | 0.0 | 0.0 | 0 | 0 |
| osworld_group_start | fixed_session | top_5_groups | 0.2421 | 0.9781 | 0.2476 | 5 | 185 |
| osworld_group_start | fixed_session | top_10_groups | 0.356 | 1.0035 | 0.3548 | 10 | 272 |
| osworld_group_start | fixed_session | top_20_groups | 0.4267 | 0.9271 | 0.4602 | 20 | 326 |
| osworld_group_start | fixed_session | budget_10pct_operations | 0.1466 | 1.4663 | 0.1 | 3 | 112 |
| osworld_group_start | fixed_session | budget_20pct_operations | 0.2134 | 1.067 | 0.2 | 5 | 163 |
| osworld_group_start | fixed_session | budget_30pct_operations | 0.2919 | 0.9732 | 0.2999 | 8 | 223 |
| osworld_group_start | fixed_session | budget_50pct_operations | 0.4751 | 0.9505 | 0.4999 | 27 | 363 |
| osworld_group_start | operation_stack | top_5_groups | 0.5903 | 1.0417 | 0.5667 | 5 | 451 |
| osworld_group_start | operation_stack | top_10_groups | 0.6963 | 1.0101 | 0.6894 | 10 | 532 |
| osworld_group_start | operation_stack | top_20_groups | 0.8037 | 1.0243 | 0.7846 | 20 | 614 |
| osworld_group_start | operation_stack | budget_10pct_operations | 0.1178 | 1.1783 | 0.1 | 4 | 90 |
| osworld_group_start | operation_stack | budget_20pct_operations | 0.2291 | 1.1456 | 0.2 | 4 | 175 |
| osworld_group_start | operation_stack | budget_30pct_operations | 0.4241 | 1.414 | 0.2999 | 4 | 324 |
| osworld_group_start | operation_stack | budget_50pct_operations | 0.5484 | 1.0971 | 0.4999 | 7 | 419 |
| osworld_group_start | label_drilldown | top_5_groups | 0.0 | 0.0 | 0.5383 | 5 | 0 |
| osworld_group_start | label_drilldown | top_10_groups | 0.538 | 0.6758 | 0.7961 | 10 | 411 |
| osworld_group_start | label_drilldown | top_20_groups | 0.8259 | 0.8939 | 0.924 | 20 | 631 |
| osworld_group_start | label_drilldown | budget_10pct_operations | 0.0 | 0.0 | 0.1 | 3 | 0 |
| osworld_group_start | label_drilldown | budget_20pct_operations | 0.0013 | 0.0065 | 0.2 | 4 | 1 |
| osworld_group_start | label_drilldown | budget_30pct_operations | 0.0 | 0.0 | 0.2999 | 4 | 0 |
| osworld_group_start | label_drilldown | budget_50pct_operations | 0.1047 | 0.2095 | 0.4999 | 7 | 80 |

## Claim Scope

- Supports: operation stacks provide a label-free, width-ranked browsing surface that often recovers more labeled problem operations than fixed-session stacks at far fewer inspected groups.
- Narrows: width ranking alone is not sufficient for all safety labels, and oracle label drilldown is not a valid default browsing baseline because it uses the hidden answer.
- Does not support: claims about human productivity or unsupervised anomaly detection without a separate user study or online detector.
