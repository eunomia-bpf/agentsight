# Local agent-session sizing inventory

Generated: 2026-07-26T04:05:34Z

## Outcome

The read-only scan inventoried **7,977 session files**
(49,221,984,881 bytes), including
**1,389 long-horizon candidates**. A
session is long-horizon when its recorded duration is at least one hour or it
contains at least 100 source-visible tool calls.

No prompt, response, command, tool-output, absolute path, or raw session ID is
present in this report or `inventory-results.json`. Session keys are one-way
hashes of source-relative filenames; project labels are coarse cwd basenames.
The scan opened session files read-only and wrote only in this experiment
directory.

## Access and scan quality

- None. Both requested roots were readable.

- Selective JSON decode errors on relevant records: 6
- Sessions using file-mtime timestamp fallback: 14
- Codex: 6,589 rows,
  48,418,582,217 bytes read.
- Claude: 1,388 rows,
  803,402,664 bytes read.

## Measurement definitions

- Start and end are the earliest and latest source-record timestamps owned by
  the session. A missing timestamp falls back to file mtime (and a reported
  Claude duration when available).
- User prompts exclude tool-result messages and deduplicate repeated
  source-visible prompt records within one second.
- LLM calls are source-visible assistant-response records, deduplicated within
  one second like `agent-session`; they are not an estimate of hidden provider
  API requests.
- Tool calls are Claude `tool_use` items and Codex `function_call` or
  `custom_tool_call` items. A Codex composite custom call is one source call,
  matching the repository parser.
- Provider tokens use the final Codex cumulative total when present. Claude
  uses the result-level model total when present, otherwise deduplicated
  message-level input, output, cache-creation, and cache-read counters.
- “Known tokens” sums only sessions with provider counters. Coverage is shown
  beside every aggregate; an uncovered session contributes no invented token
  count.

## Aggregate by project

| Project (coarse) | Sessions | Prompts | LLM | Tools | Operations | Known tokens | Token coverage | Duration h | Long-horizon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bpf-benchmark | 2,341 | 11,625 | 126,625 | 451,549 | 578,174 | 176,016,696,282 | 2292/2341 | 3,996.7 | 828 |
| agentsight | 1,507 | 5,722 | 55,304 | 147,361 | 202,665 | 858,648,315,637 | 1479/1507 | 2,101.4 | 109 |
| ebpf-verifier-agent | 817 | 2,887 | 23,255 | 56,879 | 80,134 | 111,037,718,210 | 813/817 | 763.0 | 38 |
| workspace | 729 | 3,045 | 33,486 | 90,626 | 124,112 | 421,832,758,890 | 718/729 | 1,394.5 | 79 |
| ActPlane | 474 | 7,529 | 55,171 | 72,220 | 127,391 | 16,236,570,268 | 419/474 | 1,258.5 | 75 |
| namei_ext | 210 | 1,053 | 14,496 | 32,084 | 46,580 | 43,494,699,766 | 207/210 | 1,049.7 | 10 |
| temporary | 182 | 356 | 453 | 473 | 926 | 10,809,671 | 180/182 | 1.1 | 0 |
| eunomia-bpf | 171 | 609 | 3,750 | 12,776 | 16,526 | 1,736,285,779 | 169/171 | 91.8 | 18 |
| geoperf | 153 | 745 | 11,159 | 25,601 | 36,760 | 49,234,956,269 | 153/153 | 540.9 | 4 |
| eunomia.dev | 140 | 1,080 | 6,987 | 13,871 | 20,858 | 2,677,554,819 | 135/140 | 596.3 | 21 |
| paper | 129 | 390 | 3,028 | 5,576 | 8,604 | 412,893,246 | 128/129 | 46.3 | 16 |
| linux-framework | 122 | 248 | 2,183 | 10,373 | 12,556 | 692,490,590 | 121/122 | 29.6 | 37 |
| bpftime | 97 | 417 | 5,884 | 12,988 | 18,872 | 1,207,980,225 | 93/97 | 585.8 | 24 |
| corpus | 60 | 61 | 2,058 | 1,451 | 3,509 | 68,254,979 | 60/60 | 5.3 | 2 |
| nccl-eBPF | 58 | 172 | 808 | 3,348 | 4,156 | 181,072,734 | 58/58 | 82.4 | 10 |
| gpu_ext | 51 | 108 | 717 | 2,799 | 3,516 | 135,042,442 | 50/51 | 9.4 | 6 |
| bpf-developer-tutorial | 51 | 181 | 1,626 | 1,647 | 3,273 | 116,660,317 | 48/51 | 38.7 | 6 |
| agentpprof-paper | 51 | 10 | 815 | 577 | 1,392 | 117,920,369 | 51/51 | 1.6 | 0 |
| bpfopt | 43 | 86 | 505 | 4,332 | 4,837 | 276,296,656 | 43/43 | 9.6 | 17 |
| agentsight-research-semantic-flamegraph | 42 | 1,132 | 5,540 | 3,451 | 8,991 | 897,606,071 | 42/42 | 95.2 | 10 |
| sandlock | 42 | 412 | 2,225 | 1,595 | 3,820 | 456,975,911 | 41/42 | 132.2 | 3 |
| collector | 37 | 45 | 1,538 | 1,012 | 2,550 | 56,256,973 | 37/37 | 1.1 | 2 |
| papers | 36 | 36 | 782 | 643 | 1,425 | 13,106,590 | 35/36 | 1.0 | 0 |
| bpftime-gpu-verifier | 34 | 68 | 573 | 2,439 | 3,012 | 144,473,323 | 30/34 | 6.1 | 8 |
| ebpf27-bpfoptbench | 30 | 30 | 847 | 649 | 1,496 | 21,334,170 | 30/30 | 1.1 | 0 |
| ephemeral | 28 | 141 | 1,598 | 1,003 | 2,601 | 91,926,215 | 26/28 | 13.1 | 4 |
| kernel-script-paper | 24 | 372 | 2,382 | 1,355 | 3,737 | 134,807,795 | 24/24 | 140.6 | 8 |
| academic-writing-skills | 24 | 218 | 1,228 | 713 | 1,941 | 57,604,558 | 23/24 | 22.6 | 3 |
| bpftime-worktree-552 | 17 | 34 | 260 | 1,002 | 1,262 | 46,679,688 | 17/17 | 2.4 | 2 |
| sysom-paper | 15 | 145 | 729 | 598 | 1,327 | 35,243,479 | 15/15 | 47.0 | 4 |
| agentskill-observability-paper | 14 | 259 | 1,604 | 873 | 2,477 | 162,269,379 | 14/14 | 9.5 | 3 |
| my-paper-work | 14 | 159 | 784 | 1,300 | 2,084 | 91,503,859 | 13/14 | 104.5 | 7 |
| unknown | 14 | 0 | 0 | 0 | 0 | 0 | 0/14 | 0.0 | 0 |
| linux | 13 | 26 | 210 | 973 | 1,183 | 80,199,394 | 13/13 | 2.5 | 3 |
| bpftime-worktree-542 | 12 | 25 | 240 | 1,032 | 1,272 | 67,575,670 | 11/12 | 2.5 | 6 |
| reward-guard | 11 | 193 | 798 | 457 | 1,255 | 167,612,838 | 11/11 | 15.0 | 2 |
| repo | 11 | 19 | 210 | 181 | 391 | 4,277,141 | 10/11 | 0.4 | 0 |
| agentsight-evolution-gallery | 11 | 20 | 195 | 122 | 317 | 4,738,327 | 8/11 | 0.4 | 0 |
| agentcap | 8 | 104 | 586 | 337 | 923 | 93,233,414 | 8/8 | 19.0 | 1 |
| daemon | 8 | 16 | 108 | 598 | 706 | 30,375,622 | 8/8 | 1.5 | 0 |
| bpf-developer-tutorial-four | 8 | 16 | 175 | 108 | 283 | 7,710,508 | 7/8 | 0.7 | 0 |
| bpf-developer-tutorial-egress | 7 | 22 | 373 | 229 | 602 | 13,638,637 | 7/7 | 1.4 | 1 |
| bpf-developer-tutorial-54-monitor | 7 | 14 | 303 | 146 | 449 | 5,333,731 | 7/7 | 0.6 | 0 |
| work | 7 | 14 | 7 | 0 | 7 | 123,387 | 7/7 | 0.0 | 0 |
| os-for-agent.github.io | 6 | 65 | 210 | 296 | 506 | 14,220,969 | 6/6 | 553.2 | 2 |
| extension | 6 | 13 | 75 | 200 | 275 | 7,855,989 | 6/6 | 0.8 | 0 |
| bpf-developer-tutorial-pr2 | 6 | 12 | 4 | 0 | 4 | 61,293 | 2/6 | 0.1 | 0 |
| datrail | 5 | 118 | 468 | 1,525 | 1,993 | 116,487,420 | 5/5 | 988.6 | 4 |
| app | 5 | 5 | 149 | 130 | 279 | 2,606,934 | 5/5 | 0.2 | 0 |
| bpf-developer-tutorial-prs | 5 | 10 | 49 | 31 | 80 | 867,984 | 5/5 | 0.2 | 0 |
| agentsight-pr-agentpprof | 4 | 8 | 129 | 125 | 254 | 4,501,618 | 4/4 | 0.1 | 0 |
| scanner | 4 | 8 | 39 | 156 | 195 | 8,474,493 | 4/4 | 0.7 | 0 |
| home | 4 | 27 | 52 | 61 | 113 | 1,728,301 | 3/4 | 0.6 | 0 |
| agentsight-docs-agentpprof-flamegraphs | 4 | 8 | 74 | 39 | 113 | 1,582,103 | 4/4 | 0.1 | 0 |
| poc | 4 | 8 | 0 | 0 | 0 | 0 | 0/4 | 0.0 | 0 |
| ebpf-correctness-verifier | 3 | 105 | 2,310 | 4,622 | 6,932 | 397,590,941 | 3/3 | 78.8 | 2 |
| bpf-developer-tutorial-skills | 3 | 10 | 311 | 193 | 504 | 17,436,133 | 3/3 | 0.6 | 0 |
| gpu | 3 | 18 | 58 | 74 | 132 | 2,388,080 | 2/3 | 0.3 | 0 |
| reference | 3 | 0 | 65 | 52 | 117 | 23,404,505 | 3/3 | 0.2 | 0 |
| 3 | 3 | 14 | 10 | 45 | 55 | 1,169,453 | 1/3 | 3.4 | 1 |
| agentcgroup | 2 | 136 | 750 | 2,164 | 2,914 | 183,476,964 | 2/2 | 46.7 | 2 |
| my-new-blog | 2 | 67 | 209 | 836 | 1,045 | 66,940,378 | 2/2 | 25.8 | 1 |
| agentfs | 2 | 65 | 219 | 620 | 839 | 39,567,858 | 2/2 | 8.0 | 2 |
| agent-a236e24052c2442e3 | 2 | 4 | 194 | 116 | 310 | 9,020,684 | 2/2 | 0.7 | 0 |
| llvmbpf | 2 | 4 | 31 | 124 | 155 | 14,249,118 | 2/2 | 0.5 | 1 |
| eBPF-Grant---eBPF-runtime-optimization | 2 | 2 | 60 | 46 | 106 | 2,906,048 | 2/2 | 0.2 | 0 |
| figures | 2 | 2 | 38 | 50 | 88 | 470,693 | 2/2 | 0.1 | 0 |
| monitor-poc | 2 | 4 | 18 | 57 | 75 | 736,465 | 2/2 | 0.1 | 0 |
| guarded-shell-poc | 2 | 4 | 12 | 33 | 45 | 654,506 | 2/2 | 0.2 | 0 |
| llama.cpp | 2 | 6 | 3 | 38 | 41 | 761,751 | 1/2 | 0.2 | 0 |
| co-processor-demo | 2 | 10 | 8 | 20 | 28 | 159,422 | 2/2 | 0.1 | 0 |
| agentsight-agent-nebula-research | 2 | 5 | 3 | 23 | 26 | 1,952,146 | 1/2 | 0.1 | 0 |
| wasm-bpf | 1 | 13 | 296 | 992 | 1,288 | 62,041,627 | 1/1 | 2.6 | 1 |
| thesis | 1 | 31 | 124 | 406 | 530 | 29,205,885 | 1/1 | 11.0 | 1 |
| eunomia | 1 | 4 | 85 | 263 | 348 | 13,255,184 | 1/1 | 1.0 | 1 |
| agent-a32ae6d0a8dbd25db | 1 | 1 | 138 | 102 | 240 | 7,337,921 | 1/1 | 0.1 | 1 |
| ebpf-verifier | 1 | 2 | 35 | 125 | 160 | 7,078,593 | 1/1 | 0.2 | 1 |
| paper-review | 1 | 19 | 85 | 42 | 127 | 4,255,688 | 1/1 | 0.8 | 0 |
| passes | 1 | 2 | 11 | 110 | 121 | 5,513,480 | 1/1 | 0.3 | 1 |
| Zettai.github.io | 1 | 17 | 34 | 78 | 112 | 7,498,032 | 1/1 | 20.0 | 1 |
| dyn | 1 | 11 | 8 | 81 | 89 | 1,908,224 | 1/1 | 0.3 | 0 |
| xsched | 1 | 6 | 4 | 79 | 83 | 2,509,178 | 1/1 | 0.5 | 0 |
| results | 1 | 2 | 8 | 71 | 79 | 2,815,434 | 1/1 | 0.2 | 0 |
| draft | 1 | 4 | 14 | 55 | 69 | 1,349,033 | 1/1 | 0.5 | 0 |
| apps | 1 | 2 | 12 | 55 | 67 | 1,841,452 | 1/1 | 0.2 | 0 |
| pytorch | 1 | 2 | 14 | 33 | 47 | 697,727 | 1/1 | 0.1 | 0 |
| retune-reliable-llm-agent-parameter-tuning-production-file-systems | 1 | 2 | 28 | 14 | 42 | 793,550 | 1/1 | 0.3 | 0 |
| agentsight-pr19 | 1 | 2 | 12 | 9 | 21 | 276,685 | 1/1 | 0.0 | 0 |
| coala-standard-based-framework-cli-agentic-toolsets | 1 | 2 | 6 | 13 | 19 | 293,338 | 1/1 | 0.1 | 0 |
| paper-pre | 1 | 3 | 1 | 15 | 16 | 135,749 | 1/1 | 0.1 | 0 |
| workload | 1 | 4 | 2 | 6 | 8 | 34,663 | 1/1 | 0.2 | 0 |
| agentsight-report-token-agent-sessions | 1 | 2 | 2 | 0 | 2 | 33,454 | 1/1 | 0.0 | 0 |
| codex-work | 1 | 2 | 1 | 0 | 1 | 19,192 | 1/1 | 0.0 | 0 |
| ruleset | 1 | 2 | 0 | 0 | 0 | 0 | 0/1 | 0.1 | 0 |
| bpf-developer-tutorial-50-53 | 1 | 2 | 0 | 0 | 0 | 0 | 0/1 | 0.0 | 0 |
| UVM_benchmark | 1 | 1 | 0 | 0 | 0 | 0 | 0/1 | 0.0 | 0 |
| Suika | 1 | 3 | 0 | 0 | 0 | 0 | 0/1 | 0.0 | 0 |

## Aggregate by duration bucket

| Duration bucket | Sessions | Prompts | LLM | Tools | Operations | Known tokens | Token coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <10 min | 5,562 | 8,845 | 52,351 | 133,119 | 185,470 | 1,159,615,192,980 | 5345/5562 |
| 10-60 min | 1,846 | 4,795 | 42,973 | 183,755 | 226,728 | 317,295,035,863 | 1846/1846 |
| 1-6 h | 347 | 3,912 | 36,214 | 90,973 | 127,187 | 124,564,871,620 | 347/347 |
| >6 h | 222 | 23,171 | 246,535 | 573,725 | 820,260 | 86,414,649,704 | 222/222 |

## Long-horizon sessions

The following is the complete identified set, not a sample. The same rows carry
`long_horizon_candidate: true` in `inventory-results.json`.

| Session key | Agent | Project | Start (UTC) | Duration | Prompts | LLM | Tools | Known tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1f57539b057b599e | codex | namei_ext | 2026-06-29T21:30:54.005Z | 629.55h | 386 | 5,799 | 12,274 | 794,566,436 |
| e5684439e7ccf58c | claude | datrail | 2026-05-05T01:54:29.656Z | 577.52h | 13 | 78 | 47 | 2,827,467 |
| 905706799b45b40f | claude | os-for-agent.github.io | 2026-05-27T02:27:40.219Z | 532.67h | 29 | 93 | 58 | 2,369,626 |
| 95d178e2e56075eb | codex | geoperf | 2026-07-01T01:23:04.478Z | 527.12h | 440 | 9,967 | 22,031 | 1,955,508,732 |
| 5e0ab863db634a50 | codex | bpf-benchmark | 2026-07-10T22:02:11.334Z | 365.97h | 164 | 4,371 | 23,811 | 3,483,587,275 |
| 9bb5fe200edcdaff | codex | agentsight | 2026-07-10T21:59:28.676Z | 365.11h | 650 | 4,640 | 30,521 | 4,640,621,271 |
| fc145677635f302a | codex | datrail | 2026-04-28T00:55:01.018Z | 337.56h | 86 | 312 | 1,066 | 80,520,388 |
| 71fc171259a36137 | codex | namei_ext | 2026-06-16T16:37:41.300Z | 316.83h | 92 | 1,949 | 3,847 | 308,396,412 |
| cccca59a27fbf730 | codex | bpf-benchmark | 2026-06-29T21:20:02.672Z | 264.13h | 67 | 2,535 | 5,110 | 389,432,112 |
| dbdeb1cc141e0f6a | codex | agentsight | 2026-06-13T18:24:41.974Z | 224.46h | 442 | 7,868 | 15,669 | 1,365,115,869 |
| 314e4ce4751e2776 | codex | bpf-benchmark | 2026-06-13T19:44:52.866Z | 220.21h | 44 | 109 | 179 | 13,010,485 |
| 9a746c557d4b5807 | claude | bpf-benchmark | 2026-06-10T20:58:26.844Z | 217.27h | 42 | 261 | 179 | 15,863,282 |
| eb02f4d0c40c998f | codex | bpftime | 2026-06-21T07:24:20.322Z | 215.71h | 12 | 689 | 1,160 | 102,397,851 |
| 0218573aa3598ee6 | codex | agentsight | 2026-07-15T08:49:33.829Z | 215.15h | 310 | 1,532 | 12,601 | 1,827,670,003 |
| 9960c9b7090203f2 | codex | ebpf-verifier-agent | 2026-07-02T07:59:02.007Z | 214.48h | 20 | 166 | 379 | 55,153,990 |
| ab8384c23a74ca1c | codex | bpf-benchmark | 2026-06-14T01:49:24.155Z | 213.82h | 110 | 13,255 | 24,049 | 2,020,104,613 |
| a4d28bd00c1a99e4 | codex | workspace | 2026-07-14T09:12:02.317Z | 208.56h | 167 | 1,090 | 5,660 | 749,137,242 |
| 7b656b925057217d | codex | workspace | 2026-07-11T08:51:00.083Z | 207.41h | 253 | 2,926 | 16,140 | 2,732,130,486 |
| 895ef34a4feb9ff4 | codex | ebpf-verifier-agent | 2026-06-13T04:38:15.764Z | 191.76h | 520 | 12,113 | 23,115 | 2,065,749,731 |
| 98708790f64759bf | codex | eunomia.dev | 2026-07-11T06:18:42.511Z | 188.81h | 56 | 210 | 977 | 152,581,734 |
| 90c16a6183e7d1d7 | codex | workspace | 2026-07-03T03:17:32.025Z | 186.16h | 479 | 11,829 | 22,728 | 2,043,932,947 |
| 51483f49e53cfb72 | codex | bpftime | 2026-07-06T22:01:24.248Z | 179.21h | 13 | 384 | 915 | 59,838,844 |
| d31eaf819ebdfdbb | codex | agentsight | 2026-07-10T02:11:57.151Z | 168.51h | 218 | 2,716 | 6,001 | 562,304,655 |
| a8eaa91b3d1f3868 | codex | eunomia.dev | 2026-07-19T04:49:13.251Z | 155.19h | 52 | 263 | 1,473 | 193,690,262 |
| a50691d163374fca | codex | workspace | 2026-07-03T19:56:32.277Z | 154.10h | 190 | 4,423 | 8,794 | 712,335,590 |
| 453073d451591017 | codex | bpf-benchmark | 2026-04-03T18:59:24.428Z | 145.09h | 586 | 7,503 | 25,657 | 2,488,000,456 |
| 5ab3fa42a5ecb3b6 | codex | bpf-benchmark | 2026-05-14T02:17:11.287Z | 142.37h | 727 | 3,807 | 17,481 | 1,917,121,001 |
| 69df292ba9940c2b | codex | bpf-benchmark | 2026-05-23T20:29:44.865Z | 139.35h | 199 | 3,963 | 19,140 | 1,872,174,683 |
| 8c39707a1388e206 | claude | ActPlane | 2026-06-21T00:16:45.613Z | 122.97h | 175 | 780 | 308 | 38,765,078 |
| 66ae13730385c187 | codex | ActPlane | 2026-07-03T02:03:11.265Z | 119.26h | 22 | 872 | 1,554 | 136,301,655 |
| e83aaf3df9df1f63 | codex | agentsight | 2026-07-03T06:29:23.837Z | 114.20h | 572 | 10,070 | 20,259 | 1,718,973,648 |
| c6a1c1e3fe0c4552 | codex | bpf-benchmark | 2026-06-25T06:25:43.507Z | 113.42h | 17 | 44 | 105 | 8,038,463 |
| 64044b11d785e65b | codex | bpf-benchmark | 2026-05-15T16:46:45.961Z | 111.18h | 517 | 1,972 | 9,106 | 928,543,500 |
| f1ce99e3fd77454c | codex | ActPlane | 2026-06-03T21:11:22.725Z | 106.23h | 613 | 8,040 | 12,733 | 1,132,051,698 |
| f8ec07e2295c57c2 | codex | agentsight | 2026-06-15T18:49:11.531Z | 103.83h | 82 | 1,133 | 1,898 | 166,231,279 |
| b59c1f04f0648e01 | codex | ActPlane | 2026-06-13T06:22:34.560Z | 98.49h | 183 | 3,996 | 7,583 | 689,903,617 |
| 012c0507df5021ee | codex | bpf-benchmark | 2026-06-04T00:50:34.454Z | 96.53h | 102 | 4,383 | 6,739 | 661,378,287 |
| 1ac4ed92649286f6 | claude | sandlock | 2026-07-02T05:58:59.291Z | 96.38h | 47 | 242 | 154 | 24,383,911 |
| e037af7e39fa1e8f | codex | bpf-benchmark | 2026-05-31T04:50:30.586Z | 91.98h | 79 | 4,667 | 9,197 | 846,893,322 |
| 9f3d2a5314e95cab | codex | ActPlane | 2026-06-26T03:41:13.152Z | 90.03h | 14 | 140 | 248 | 17,687,647 |
| 5c339b92d29ccd64 | claude | ebpf-verifier-agent | 2026-06-27T08:31:57.515Z | 86.15h | 221 | 817 | 469 | 53,659,373 |
| bc9faf3b325095ff | claude | my-paper-work | 2026-07-02T07:36:54.964Z | 85.44h | 3 | 5 | 1 | 42,808 |
| 2a50ffb4f1f7d4f1 | codex | bpf-benchmark | 2026-05-20T07:59:08.848Z | 84.84h | 289 | 2,361 | 10,211 | 1,053,414,081 |
| d4eeb1dbbcd2be7f | codex | workspace | 2026-07-17T22:24:37.575Z | 82.79h | 17 | 64 | 115 | 11,187,031 |
| 2113abd17542fb60 | claude | bpf-benchmark | 2026-06-24T21:30:03.961Z | 82.43h | 809 | 3,201 | 1,452 | 225,365,005 |
| 93faa4c592de43ab | codex | namei_ext | 2026-06-13T06:33:55.639Z | 82.05h | 168 | 4,710 | 9,689 | 572,340,663 |
| 7998a1082a5dcd79 | codex | agentsight | 2026-06-29T21:39:00.110Z | 75.84h | 26 | 122 | 228 | 19,415,991 |
| b7477092adf649bf | claude | workspace | 2026-06-01T06:29:24.341Z | 73.63h | 88 | 839 | 539 | 139,142,386 |
| 10ca09ee31de0a23 | claude | nccl-eBPF | 2026-06-26T05:03:40.033Z | 73.36h | 55 | 177 | 110 | 10,421,152 |
| a3c119bf1364f8e1 | codex | datrail | 2026-07-21T01:34:57.892Z | 73.00h | 10 | 30 | 166 | 21,274,110 |
| 006dcc2dcfd68124 | claude | kernel-script-paper | 2026-06-26T06:55:53.916Z | 71.49h | 178 | 1,188 | 557 | 66,759,739 |
| 8fd5b9da0231f1f0 | codex | ebpf-correctness-verifier | 2026-07-01T04:51:14.575Z | 70.21h | 98 | 2,261 | 4,499 | 390,878,595 |
| 37226e96c21da3c8 | codex | bpf-benchmark | 2026-05-25T06:15:52.687Z | 68.06h | 63 | 1,101 | 5,180 | 477,960,017 |
| 4fb1bd79a70fb9d3 | codex | workspace | 2026-03-06T20:54:03.414Z | 67.75h | 257 | 983 | 3,547 | 323,961,529 |
| 07a6621e21ae1b51 | codex | ActPlane | 2026-06-03T01:11:05.399Z | 67.22h | 302 | 4,453 | 6,286 | 600,997,389 |
| a8083bf626c40f47 | codex | agentsight | 2026-07-20T03:45:26.424Z | 67.12h | 9 | 49 | 174 | 22,384,301 |
| e7c8ef8a64bec503 | codex | ebpf-verifier-agent | 2026-06-27T09:07:24.813Z | 66.60h | 11 | 183 | 473 | 28,206,177 |
| 71081d2f48ad49bd | codex | ebpf-verifier-agent | 2026-06-21T07:25:16.359Z | 66.18h | 31 | 1,456 | 2,651 | 230,089,748 |
| 24a7365883d3e10a | codex | bpf-benchmark | 2026-05-21T04:32:35.709Z | 65.58h | 102 | 1,303 | 4,457 | 448,689,124 |
| 280a07982bda10c8 | codex | bpftime | 2026-07-16T08:50:43.721Z | 62.74h | 7 | 51 | 215 | 21,239,473 |
| 9f0a8fb25d022271 | claude | eunomia.dev | 2026-07-16T08:00:29.792Z | 61.64h | 152 | 749 | 414 | 80,132,998 |
| 8661d9f9e710e418 | codex | eunomia.dev | 2026-07-18T21:40:58.080Z | 59.44h | 72 | 188 | 1,208 | 170,900,884 |
| 98bea95f7a6bad7c | claude | ActPlane | 2026-05-30T09:31:39.759Z | 57.49h | 512 | 2,483 | 1,393 | 428,451,271 |
| d363729d35d4d8b6 | codex | ActPlane | 2026-06-08T04:17:33.676Z | 49.37h | 114 | 5,348 | 9,127 | 649,963,997 |
| 65d60f4804d882b3 | codex | agentsight | 2026-07-24T02:53:06.635Z | 49.15h | 11 | 71 | 282 | 38,892,185 |
| 8b27b7991224c52b | codex | bpf-benchmark | 2026-04-15T01:43:40.184Z | 48.83h | 49 | 976 | 3,329 | 238,205,232 |
| c210964f9bade587 | codex | agentsight | 2026-06-20T04:24:35.172Z | 48.79h | 88 | 458 | 860 | 64,193,075 |
| 8a99a7d394a57513 | codex | bpftime | 2026-05-26T04:20:51.381Z | 48.41h | 15 | 400 | 712 | 82,721,075 |
| 765dbb565a3b3a1a | codex | workspace | 2026-06-15T03:50:13.334Z | 45.17h | 61 | 409 | 812 | 53,838,190 |
| 89ccb8b4645a9999 | claude | agentsight | 2026-06-23T03:29:51.224Z | 41.88h | 257 | 2,016 | 1,249 | 159,230,942 |
| 46fb6a1f93938a15 | codex | bpf-benchmark | 2026-06-25T06:30:32.122Z | 40.11h | 42 | 4,545 | 7,260 | 685,102,987 |
| a1adeb17453c1ece | codex | bpf-benchmark | 2026-05-19T07:32:03.794Z | 39.10h | 160 | 811 | 3,690 | 310,186,051 |
| 1924e5e431a2dfaf | codex | bpf-benchmark | 2026-03-24T11:20:58.540Z | 38.61h | 545 | 2,669 | 7,730 | 679,886,989 |
| ff7eef2ac8e9ed44 | claude | ActPlane | 2026-05-28T03:08:42.522Z | 38.47h | 570 | 2,368 | 1,360 | 602,986,605 |
| d92ff4092c8638ef | codex | bpf-benchmark | 2026-03-27T03:46:19.849Z | 36.44h | 166 | 1,157 | 3,730 | 288,261,197 |
| 6a0a7be885b8a9bb | codex | bpf-benchmark | 2026-04-02T05:52:06.410Z | 36.00h | 42 | 446 | 1,542 | 138,065,825 |
| 5e2dd65abf3c9c2a | codex | bpf-benchmark | 2026-05-29T15:53:00.166Z | 34.33h | 23 | 842 | 4,040 | 346,520,260 |
| a20ffb901d2c9ca8 | claude | agentsight-research-semantic-flamegraph | 2026-07-07T22:04:22.190Z | 33.89h | 378 | 2,183 | 1,290 | 438,071,625 |
| 556401bba956493a | claude | ActPlane | 2026-06-17T21:44:49.449Z | 33.19h | 198 | 968 | 512 | 49,797,887 |
| 555bb422afa69686 | codex | bpf-benchmark | 2026-06-26T22:29:01.620Z | 32.25h | 25 | 1,669 | 2,750 | 236,532,542 |
| 46aa1924898af619 | claude | sandlock | 2026-07-06T23:21:25.535Z | 31.50h | 310 | 1,384 | 766 | 300,532,983 |
| 129c8ee5740324f0 | codex | ActPlane | 2026-07-17T01:45:26.492Z | 30.96h | 19 | 492 | 3,208 | 451,711,054 |
| f23116803aa919be | codex | bpf-benchmark | 2026-03-30T13:34:45.294Z | 30.05h | 87 | 988 | 3,107 | 280,688,840 |
| 7d4aa682770057b0 | codex | workspace | 2026-06-15T01:40:53.961Z | 29.40h | 52 | 578 | 977 | 78,819,660 |
| d93cdfe50cf8d846 | codex | agentsight | 2026-05-26T21:31:49.811Z | 29.34h | 35 | 200 | 1,403 | 144,008,383 |
| 04599a3437117735 | codex | ebpf-verifier-agent | 2026-04-29T21:34:24.292Z | 28.89h | 228 | 673 | 2,988 | 260,395,629 |
| 8cbb279fe79d26d0 | codex | agentsight | 2026-06-09T04:29:01.594Z | 28.62h | 61 | 497 | 1,006 | 70,959,399 |
| 750d14fcbaaf246f | codex | bpf-benchmark | 2026-05-13T03:51:47.416Z | 27.20h | 213 | 761 | 3,529 | 308,913,089 |
| 31f0e24626f1df74 | claude | paper | 2026-07-07T23:40:45.538Z | 27.19h | 108 | 318 | 176 | 38,003,873 |
| 6d8227f8365ad5ed | codex | bpf-benchmark | 2026-04-09T20:05:28.676Z | 26.95h | 115 | 885 | 3,654 | 288,658,704 |
| 3098df6bfaf040ae | codex | bpf-benchmark | 2026-06-22T22:08:57.551Z | 26.83h | 23 | 160 | 330 | 22,631,444 |
| abd148f21b5fba25 | codex | bpf-benchmark | 2026-04-12T03:58:05.476Z | 26.72h | 33 | 447 | 1,394 | 131,548,102 |
| a531051b098852ea | codex | eunomia.dev | 2026-05-21T23:33:07.603Z | 26.65h | 79 | 470 | 2,521 | 248,619,205 |
| 6701a0eb3138c730 | codex | bpf-benchmark | 2026-05-20T02:34:17.244Z | 26.41h | 108 | 812 | 3,294 | 296,257,985 |
| 3673d3d7495955cf | codex | eunomia-bpf | 2026-03-06T07:11:34.680Z | 25.86h | 55 | 655 | 1,626 | 115,175,823 |
| 5170539cd218f1eb | codex | workspace | 2026-06-13T05:28:50.304Z | 25.48h | 66 | 1,931 | 4,199 | 307,838,517 |
| b5c320a385cf8f39 | codex | my-new-blog | 2026-05-24T05:01:21.151Z | 25.41h | 50 | 173 | 782 | 64,588,309 |
| c98f3fd76a9367b1 | codex | agentsight | 2026-07-15T07:18:41.205Z | 24.53h | 32 | 122 | 527 | 70,853,173 |
| 34024a25264cb3e6 | codex | agentcgroup | 2026-03-05T02:41:07.349Z | 24.14h | 88 | 285 | 822 | 79,419,491 |
| 68fff0c3c80f0224 | codex | workspace | 2026-06-30T04:33:48.783Z | 23.61h | 41 | 697 | 1,243 | 115,602,998 |
| 60be0ae750bb51e3 | claude | ActPlane | 2026-06-02T06:11:43.727Z | 23.55h | 98 | 539 | 348 | 118,648,684 |
| 4f657947fe2fac1f | claude | kernel-script-paper | 2026-07-17T22:28:42.071Z | 23.17h | 35 | 208 | 132 | 9,602,457 |
| 471c8c862ff8f709 | codex | agentsight | 2026-06-23T03:56:17.056Z | 22.93h | 32 | 251 | 481 | 35,016,026 |
| d25e9c10eb702bd6 | codex | agentcgroup | 2026-03-06T03:44:28.102Z | 22.59h | 48 | 465 | 1,342 | 104,057,473 |
| 997b2a0d85a9b8f1 | codex | workspace | 2026-07-22T01:17:41.076Z | 22.53h | 30 | 161 | 864 | 107,600,858 |
| af7d933ba810ba51 | codex | bpftime | 2026-06-15T07:25:26.466Z | 22.21h | 23 | 1,034 | 1,725 | 157,188,807 |
| 9a049da888d9a039 | codex | ActPlane | 2026-05-23T05:57:14.277Z | 22.11h | 51 | 213 | 1,074 | 97,624,672 |
| f7a8e2864b48b49c | claude | agentsight-research-semantic-flamegraph | 2026-07-25T06:04:50.622Z | 21.95h | 130 | 433 | 229 | 72,186,655 |
| e39daf1b66916373 | claude | ActPlane | 2026-06-11T09:28:56.590Z | 21.84h | 305 | 937 | 531 | 60,368,479 |
| 6edc379692d73977 | claude | agentsight | 2026-06-10T09:06:37.509Z | 21.78h | 30 | 352 | 247 | 55,595,483 |
| f5b676c3576ea2c4 | codex | eunomia.dev | 2026-05-24T22:38:21.469Z | 21.41h | 49 | 99 | 185 | 13,015,166 |
| 6b5939964c6e3177 | codex | eunomia-bpf | 2026-03-08T05:01:36.749Z | 21.34h | 219 | 444 | 928 | 76,266,454 |
| 091f24c5a9b09e63 | codex | workspace | 2026-07-23T07:40:39.988Z | 20.38h | 14 | 29 | 77 | 9,255,838 |
| 17d402829b561f2b | codex | os-for-agent.github.io | 2026-05-16T06:33:17.144Z | 20.36h | 29 | 77 | 183 | 11,088,967 |
| b6ef3a1784e68c3c | claude | ActPlane | 2026-06-09T10:29:07.341Z | 20.03h | 129 | 787 | 510 | 50,492,815 |
| c1d16f1b595e07de | codex | Zettai.github.io | 2026-05-16T07:07:11.630Z | 19.99h | 17 | 34 | 78 | 7,498,032 |
| 53813f88aa65c5d4 | codex | ActPlane | 2026-06-04T22:34:37.857Z | 18.88h | 21 | 1,392 | 2,701 | 190,937,017 |
| ac8d42e93b4741e7 | codex | ebpf-verifier-agent | 2026-05-22T06:03:09.921Z | 18.79h | 74 | 246 | 1,145 | 97,116,703 |
| bc4a023cf5c3148e | claude | agentcap | 2026-07-09T02:26:10.881Z | 18.58h | 97 | 479 | 286 | 91,825,265 |
| 1132f549f7808d9d | codex | bpf-benchmark | 2026-04-13T06:41:19.506Z | 18.37h | 20 | 364 | 2,085 | 92,950,774 |
| bb12e2f582a9bd26 | codex | agentsight | 2026-06-02T23:25:25.984Z | 18.32h | 89 | 1,057 | 2,235 | 176,645,416 |
| 244f580a056008a1 | claude | kernel-script-paper | 2026-07-25T07:30:36.037Z | 18.24h | 33 | 149 | 71 | 7,717,951 |
| d46e774838a713f5 | claude | eunomia.dev | 2026-07-19T04:19:16.993Z | 17.94h | 71 | 178 | 62 | 12,716,402 |
| d1b3f99430a6c458 | claude | academic-writing-skills | 2026-07-12T07:55:43.944Z | 17.75h | 124 | 452 | 222 | 36,404,901 |
| 2aaab9e7c259728e | codex | ActPlane | 2026-06-02T07:00:13.978Z | 17.67h | 29 | 249 | 479 | 34,535,153 |
| e9eb07932ff3aa4c | claude | ActPlane | 2026-05-30T02:01:11.935Z | 17.66h | 291 | 809 | 428 | 159,941,775 |
| 6bd04be91d6ef3a5 | claude | kernel-script-paper | 2026-06-24T04:25:40.366Z | 17.00h | 6 | 20 | 10 | 278,444 |
| 3c803243e936dacc | codex | workspace | 2026-07-21T08:40:56.301Z | 16.18h | 22 | 32 | 85 | 9,542,628 |
| ea0783513cd24ddc | claude | ActPlane | 2026-06-09T11:23:11.436Z | 16.13h | 85 | 241 | 149 | 21,227,984 |
| 4b81d9c83754a538 | codex | ActPlane | 2026-06-01T02:57:22.165Z | 16.06h | 114 | 275 | 1,011 | 87,060,768 |
| ff118c6146f5685e | codex | agentsight | 2026-07-22T06:49:42.995Z | 15.81h | 1 | 55 | 180 | 3,880,784,984 |
| 0f7c48761870ca7e | codex | agentsight | 2026-07-22T07:08:32.083Z | 15.63h | 1 | 33 | 208 | 3,890,558,771 |
| 3c216f6c49c148bc | codex | agentsight | 2026-07-22T07:08:03.117Z | 15.62h | 1 | 60 | 257 | 3,897,899,165 |
| b8a461744374be3d | codex | bpf-benchmark | 2026-04-14T02:24:49.376Z | 15.37h | 60 | 213 | 1,474 | 125,692,392 |
| d521155af215996a | claude | ActPlane | 2026-06-02T03:18:39.203Z | 15.30h | 24 | 260 | 159 | 21,245,608 |
| 03755478601acf88 | codex | agentsight | 2026-06-02T02:54:16.102Z | 15.27h | 78 | 337 | 720 | 48,896,456 |
| 05cc5a3f464d8922 | claude | bpf-developer-tutorial | 2026-07-21T10:06:09.562Z | 14.90h | 14 | 67 | 35 | 3,564,728 |
| a183f744193944c5 | codex | agentsight | 2026-06-09T06:51:20.656Z | 14.60h | 13 | 225 | 448 | 30,456,872 |
| ee90526c79da805c | claude | sysom-paper | 2026-06-10T06:35:26.524Z | 14.40h | 16 | 142 | 99 | 5,533,563 |
| fe2c5b0edc3369af | claude | ActPlane | 2026-06-20T05:18:10.097Z | 14.02h | 220 | 838 | 360 | 53,796,801 |
| 310108fb56a8d4a8 | claude | ActPlane | 2026-05-31T04:35:06.082Z | 14.00h | 6 | 11 | 2 | 179,477 |
| f9a6375644ccbad9 | claude | eunomia.dev | 2026-06-13T16:01:48.308Z | 13.98h | 68 | 354 | 211 | 19,778,716 |
| 390a65d56f800526 | codex | my-paper-work | 2026-07-07T07:24:27.153Z | 13.86h | 36 | 185 | 422 | 22,947,234 |
| afe728f1dfe76f9a | claude | sysom-paper | 2026-06-10T20:59:31.989Z | 13.74h | 76 | 295 | 169 | 16,722,338 |
| 97b631646d80f7cf | claude | agentsight-research-semantic-flamegraph | 2026-07-09T07:58:25.797Z | 13.25h | 24 | 62 | 36 | 1,815,034 |
| 2343aae2ecb61ab6 | codex | bpf-benchmark | 2026-03-24T02:42:05.463Z | 13.03h | 47 | 407 | 1,177 | 104,531,089 |
| 73a132776a9f74b5 | codex | workspace | 2026-06-13T06:51:08.125Z | 12.85h | 17 | 133 | 257 | 18,507,323 |
| 55df94dcb5bbf907 | claude | ActPlane | 2026-06-08T07:26:03.525Z | 12.80h | 22 | 93 | 65 | 4,874,076 |
| 3184d9c915477ab9 | claude | ActPlane | 2026-06-08T05:16:24.907Z | 12.74h | 66 | 205 | 120 | 10,964,134 |
| e339df3923f707e9 | claude | bpf-benchmark | 2026-07-13T07:41:44.409Z | 12.71h | 80 | 459 | 255 | 69,455,477 |
| 42467ca96905976b | codex | workspace | 2026-07-13T11:18:26.843Z | 12.47h | 1 | 45 | 124 | 1,597,618,606 |
| da5bd676d5eca65c | claude | reward-guard | 2026-07-09T08:37:23.628Z | 12.40h | 179 | 711 | 414 | 165,910,603 |
| 82bdabdf46c00040 | claude | ActPlane | 2026-06-10T21:07:28.451Z | 12.31h | 317 | 967 | 528 | 73,119,833 |
| 66925bd27637bc65 | codex | workspace | 2026-07-19T08:21:14.094Z | 12.20h | 4 | 28 | 390 | 50,205,369 |
| a77efdf78c35bd30 | claude | bpf-developer-tutorial | 2026-07-19T08:42:13.238Z | 12.18h | 18 | 263 | 153 | 15,010,118 |
| f7382c1075122661 | claude | bpf-benchmark | 2026-07-13T08:20:15.683Z | 12.14h | 41 | 226 | 146 | 16,270,926 |
| 7354b394704cb799 | claude | ActPlane | 2026-06-10T06:13:50.576Z | 11.77h | 66 | 388 | 244 | 23,249,216 |
| a5b735e6fffb7d5b | claude | agentsight | 2026-06-04T06:45:13.952Z | 11.49h | 36 | 705 | 476 | 47,060,451 |
| 6682313f1cbd0a1e | codex | bpf-benchmark | 2026-05-13T21:22:02.074Z | 11.07h | 114 | 464 | 1,853 | 158,215,092 |
| 3266841b66feb67e | codex | thesis | 2026-05-27T15:31:42.952Z | 10.99h | 31 | 124 | 406 | 29,205,885 |
| aaed984ff7861660 | claude | ActPlane | 2026-06-19T06:57:11.027Z | 10.88h | 122 | 257 | 82 | 12,603,566 |
| c1d8988661b06df3 | claude | workspace | 2026-07-09T10:09:41.677Z | 10.87h | 9 | 211 | 128 | 12,802,508 |
| af7cea7ae050554d | codex | agentsight | 2026-06-13T05:20:31.721Z | 10.86h | 15 | 364 | 710 | 52,688,158 |
| 5755b925dcb41f63 | codex | agentsight | 2026-07-22T09:56:15.845Z | 10.81h | 0 | 14 | 49 | 1,461,254,013 |
| c8c2b3df296fa81a | codex | bpf-benchmark | 2026-04-08T16:15:26.026Z | 10.69h | 22 | 184 | 948 | 1,596,296,550 |
| d6548dcc0b2e7ca0 | codex | bpf-benchmark | 2026-04-08T16:15:27.786Z | 10.68h | 14 | 122 | 426 | 1,575,512,022 |
| ef73da4db11732f0 | claude | ActPlane | 2026-06-08T22:24:12.628Z | 10.37h | 231 | 611 | 310 | 42,862,274 |
| 05313f3e3bcdc003 | codex | sysom-paper | 2026-06-11T00:40:20.089Z | 10.29h | 9 | 30 | 72 | 5,082,119 |
| 733c72304bc363fb | codex | ActPlane | 2026-06-09T21:27:45.290Z | 9.85h | 22 | 121 | 266 | 20,244,588 |
| afb75f37f999b8a0 | codex | bpf-benchmark | 2026-04-11T05:38:45.783Z | 9.79h | 12 | 119 | 521 | 32,175,013 |
| aab5f0fd0d9e1ca4 | codex | agentsight | 2026-06-04T08:52:51.347Z | 9.70h | 25 | 127 | 387 | 20,579,532 |
| 7bcce857b5d5c58c | codex | ActPlane | 2026-06-29T21:23:12.763Z | 9.66h | 23 | 725 | 1,350 | 125,699,684 |
| 93978c78ce7b76a5 | codex | bpf-benchmark | 2026-05-22T22:36:57.434Z | 9.63h | 20 | 156 | 785 | 61,369,874 |
| a7dc1218dd9d3045 | codex | bpf-benchmark | 2026-04-06T07:14:50.496Z | 9.54h | 3 | 58 | 198 | 1,055,724,250 |
| bf797330588afda0 | codex | agentsight | 2026-07-01T22:56:32.464Z | 9.42h | 5 | 102 | 196 | 12,004,114 |
| 96674714696b7395 | codex | bpf-benchmark | 2026-04-26T08:45:00.157Z | 9.24h | 2 | 156 | 161 | 26,515,956 |
| 038e3b92a6c11678 | codex | agentsight | 2026-07-12T00:15:09.216Z | 9.19h | 27 | 50 | 116 | 19,382,642 |
| 6c61aa8588a30ed4 | codex | bpf-benchmark | 2026-04-06T07:11:59.196Z | 9.13h | 2 | 28 | 82 | 1,047,601,705 |
| 363f36b6a19d783a | claude | ActPlane | 2026-06-07T19:35:23.272Z | 9.04h | 109 | 491 | 282 | 27,195,503 |
| 1f2274377c6f8888 | codex | workspace | 2026-07-02T20:34:24.630Z | 9.04h | 29 | 486 | 746 | 55,595,300 |
| 569a79356e08245b | codex | bpf-benchmark | 2026-04-05T05:41:03.299Z | 9.03h | 13 | 104 | 323 | 803,941,836 |
| 82da36b348b0ba32 | codex | bpf-benchmark | 2026-05-14T21:23:29.252Z | 8.98h | 38 | 307 | 1,991 | 202,216,956 |
| 2fe682857d5899f0 | codex | bpf-benchmark | 2026-07-10T22:09:39.699Z | 8.85h | 20 | 83 | 386 | 66,767,543 |
| 8bce7a227f583708 | codex | workspace | 2026-03-19T15:40:06.185Z | 8.81h | 26 | 159 | 306 | 26,737,687 |
| e70b8bc8d079c365 | codex | agentsight | 2026-06-05T23:52:42.364Z | 8.80h | 4 | 25 | 75 | 2,362,524 |
| 876a10c957e418a1 | claude | agentsight | 2026-06-03T16:02:30.288Z | 8.67h | 58 | 306 | 204 | 21,055,536 |
| 9d9e05c556612827 | claude | agentsight-research-semantic-flamegraph | 2026-07-09T02:05:13.666Z | 8.64h | 273 | 949 | 527 | 190,504,237 |
| 8a10bf97a7e6b4b2 | claude | ActPlane | 2026-06-20T17:05:36.954Z | 8.58h | 62 | 464 | 210 | 24,625,811 |
| 0b4f55fdb790b49d | codex | bpf-benchmark | 2026-04-07T17:10:01.299Z | 8.57h | 16 | 106 | 446 | 1,238,564,208 |
| 84f9a4b022d3818d | codex | bpf-benchmark | 2026-04-07T17:09:59.930Z | 8.50h | 16 | 66 | 466 | 1,236,374,230 |
| b6ccd6cf3692ce3b | codex | ebpf-correctness-verifier | 2026-07-05T20:26:22.606Z | 8.38h | 3 | 39 | 95 | 6,252,765 |
| 6596fc1c2c9ddbd6 | claude | agentsight | 2026-06-05T00:19:32.904Z | 8.28h | 43 | 1,405 | 973 | 98,381,885 |
| 3963d8bbebebe4b8 | codex | bpf-benchmark | 2026-04-07T17:27:11.623Z | 8.20h | 11 | 30 | 218 | 1,233,983,777 |
| 52433e0bf08c656b | codex | bpftime | 2026-03-08T20:45:53.457Z | 7.91h | 26 | 130 | 337 | 24,057,824 |
| 54d89d3246c934a4 | codex | bpftime | 2026-06-13T18:28:10.056Z | 7.91h | 9 | 221 | 411 | 20,541,737 |
| 32862080f60bb35a | codex | bpf-benchmark | 2026-05-21T20:11:59.390Z | 7.89h | 7 | 23 | 180 | 14,978,923 |
| 9aea4856ee23b569 | codex | bpf-benchmark | 2026-04-05T06:54:50.023Z | 7.77h | 12 | 65 | 209 | 800,457,110 |
| 5c8c265434e2b031 | codex | bpf-benchmark | 2026-06-05T20:37:36.240Z | 7.71h | 15 | 76 | 167 | 7,880,860 |
| 8e76cf8612a48e8a | codex | bpf-benchmark | 2026-04-30T06:13:27.053Z | 7.61h | 3 | 253 | 1,298 | 140,199,405 |
| 9944a42e007a6227 | codex | ebpf-verifier-agent | 2026-06-29T21:29:25.920Z | 7.58h | 28 | 357 | 675 | 52,961,549 |
| 24f4ccab1ec3fadd | codex | bpf-benchmark | 2026-04-28T05:58:51.252Z | 7.47h | 2 | 506 | 777 | 107,581,912 |
| 8d0cbffaff410192 | codex | bpftime | 2026-03-06T04:00:24.338Z | 7.46h | 38 | 589 | 972 | 81,723,026 |
| 1c8e0afb1e60ab64 | codex | bpf-benchmark | 2026-04-04T19:14:53.550Z | 7.44h | 21 | 118 | 617 | 29,343,817 |
| 46696225617a16cc | codex | agentsight | 2026-06-04T00:43:32.636Z | 7.42h | 61 | 751 | 1,858 | 132,402,936 |
| af20b494c6336fe5 | codex | workspace | 2026-07-14T01:02:05.221Z | 7.28h | 2 | 8 | 55 | 6,304,050 |
| 0625b70b402b5bc5 | codex | bpf-benchmark | 2026-04-14T18:27:59.255Z | 7.27h | 17 | 61 | 393 | 22,594,675 |
| 9916340dbc2f601f | codex | bpf-benchmark | 2026-04-04T19:28:50.487Z | 7.20h | 23 | 163 | 563 | 577,846,188 |
| b9ef3d92add7d8a3 | codex | ActPlane | 2026-06-22T20:23:47.918Z | 7.17h | 24 | 733 | 1,347 | 125,943,728 |
| 9c8a7e4e1f416e21 | claude | sysom-paper | 2026-06-06T23:48:10.650Z | 7.03h | 21 | 141 | 98 | 4,060,416 |
| 1ce8228e09adbaf0 | claude | ephemeral | 2026-07-17T06:34:16.820Z | 7.00h | 98 | 242 | 90 | 37,585,817 |
| 1c1f60885e382d46 | claude | eunomia.dev | 2026-05-28T02:33:19.961Z | 6.97h | 17 | 25 | 8 | 731,839 |
| 5e478f65b1078ced | codex | bpf-benchmark | 2026-04-08T17:39:12.964Z | 6.96h | 16 | 147 | 512 | 1,638,542,054 |
| 61e11f50b3e6c548 | codex | ActPlane | 2026-06-11T00:41:16.453Z | 6.93h | 40 | 138 | 229 | 17,375,507 |
| c9cb9e8fa14aa0bc | claude | agentsight-research-semantic-flamegraph | 2026-07-06T23:45:59.378Z | 6.73h | 79 | 318 | 169 | 36,238,192 |
| bae7abd0965f1606 | codex | ActPlane | 2026-06-10T17:21:48.706Z | 6.54h | 103 | 583 | 1,059 | 90,806,976 |
| 55d14ea5a57ad14b | codex | bpf-benchmark | 2026-04-04T06:25:35.582Z | 6.52h | 9 | 101 | 304 | 257,824,343 |
| fbb2155216e63398 | codex | bpf-benchmark | 2026-04-06T16:17:00.246Z | 6.50h | 5 | 13 | 43 | 586,277 |
| 307ecbd90784d722 | codex | bpf-benchmark | 2026-04-09T13:39:09.432Z | 6.43h | 25 | 150 | 694 | 35,371,134 |
| 4e457899e33ab35f | codex | workspace | 2026-07-14T13:16:54.215Z | 6.37h | 1 | 10 | 43 | 5,163,828 |
| caad0a48ad1449fe | codex | eunomia-bpf | 2026-03-06T03:28:45.756Z | 6.21h | 37 | 471 | 1,014 | 74,832,258 |
| 709e494f10cbc866 | codex | agentsight | 2026-06-02T22:04:00.144Z | 6.07h | 40 | 442 | 876 | 63,885,571 |
| a9edc44e7eb8f8dd | claude | ActPlane | 2026-06-07T23:15:16.900Z | 6.02h | 299 | 1,056 | 594 | 73,498,284 |
| b9915b4e03711963 | codex | bpf-benchmark | 2026-04-20T21:54:59.979Z | 6.00h | 2 | 273 | 833 | 78,895,697 |
| ae07247abe25e065 | codex | bpf-benchmark | 2026-04-27T20:46:25.818Z | 5.99h | 2 | 202 | 239 | 30,454,212 |
| 59deeb21807874b0 | codex | bpftime | 2026-03-06T20:50:23.994Z | 5.99h | 25 | 141 | 392 | 29,987,206 |
| d0355c1c87f2d84d | codex | ActPlane | 2026-06-24T00:07:20.192Z | 5.95h | 9 | 84 | 131 | 10,725,822 |
| 566bbe617b0e2e14 | codex | bpf-benchmark | 2026-04-10T23:02:42.029Z | 5.85h | 32 | 241 | 1,376 | 105,020,436 |
| 050b5034ab700584 | codex | workspace | 2026-07-22T02:49:30.481Z | 5.73h | 1 | 15 | 125 | 632,212,480 |
| 9f96ced6c3cb361a | codex | bpf-benchmark | 2026-04-19T04:12:37.593Z | 5.72h | 2 | 247 | 707 | 103,237,969 |
| 20cb84cf4410dff8 | codex | agentsight | 2026-06-03T18:21:51.071Z | 5.68h | 33 | 694 | 1,642 | 132,599,337 |
| 538d22ae70811031 | codex | workspace | 2026-03-06T02:53:44.307Z | 5.63h | 40 | 293 | 861 | 63,826,804 |
| 868a9060e264d189 | codex | workspace | 2026-07-11T21:45:23.139Z | 5.59h | 0 | 4 | 9 | 380,069,239 |
| 28face93a350f7d2 | codex | agentsight | 2026-07-24T01:59:07.762Z | 5.56h | 1 | 16 | 42 | 1,659,443,010 |
| 778913a38305c973 | codex | agentfs | 2026-05-19T07:05:01.717Z | 5.56h | 29 | 96 | 235 | 12,252,108 |
| 7649c56ced637220 | codex | agentsight | 2026-07-24T02:09:35.145Z | 5.43h | 1 | 20 | 155 | 1,678,721,066 |
| cb3e8c8ff00992d2 | codex | eunomia.dev | 2026-05-23T02:21:49.104Z | 5.36h | 55 | 201 | 1,085 | 113,736,379 |
| a59b99e61cee4777 | codex | bpf-benchmark | 2026-03-27T14:51:55.012Z | 5.33h | 24 | 157 | 428 | 37,461,902 |
| 3937628f7abf3c2c | codex | workspace | 2026-07-11T13:40:21.027Z | 5.28h | 0 | 24 | 129 | 110,830,100 |
| 4fd9c2874fcfb261 | codex | bpf-benchmark | 2026-04-04T18:00:13.335Z | 5.26h | 8 | 55 | 227 | 499,478,200 |
| 20d058d8b3bb26bf | codex | eunomia-bpf | 2026-03-07T23:39:04.483Z | 5.18h | 17 | 89 | 264 | 17,221,008 |
| 215cbb176294c3ea | codex | eunomia.dev | 2026-05-24T00:26:53.048Z | 5.17h | 42 | 155 | 867 | 87,744,007 |
| 70540d245c74dea9 | codex | ActPlane | 2026-06-07T22:48:43.093Z | 5.10h | 26 | 64 | 85 | 3,197,840 |
| 530b875078969034 | codex | bpf-benchmark | 2026-04-05T18:45:16.347Z | 5.09h | 13 | 104 | 378 | 874,428,684 |
| cfd95ea8201d0897 | codex | bpf-benchmark | 2026-04-21T17:09:57.058Z | 5.09h | 2 | 280 | 893 | 90,353,017 |
| cd6919c5a08c3e44 | codex | agentsight | 2026-06-02T18:20:52.493Z | 5.07h | 30 | 194 | 440 | 28,477,228 |
| 62d7d6d9c81011a7 | codex | workspace | 2026-07-11T21:39:30.316Z | 5.04h | 0 | 5 | 44 | 381,176,868 |
| 5f61f80b8b54141b | codex | bpf-benchmark | 2026-04-29T11:21:21.322Z | 5.01h | 2 | 42 | 110 | 10,905,138 |
| 806bab4908bffed3 | codex | bpf-benchmark | 2026-03-29T09:15:04.417Z | 4.98h | 2 | 127 | 176 | 15,867,227 |
| 9164655359c9fb01 | codex | bpf-benchmark | 2026-03-25T11:52:08.751Z | 4.96h | 12 | 98 | 250 | 427,996,035 |
| bbaa7fe2453082fb | claude | ActPlane | 2026-05-30T04:45:34.217Z | 4.89h | 144 | 293 | 143 | 38,892,251 |
| c16d23c9dd4ccf77 | codex | bpftime | 2026-03-08T06:24:40.013Z | 4.82h | 52 | 133 | 393 | 26,468,810 |
| 74d2571d8f2628cf | codex | bpf-benchmark | 2026-04-25T23:52:08.899Z | 4.71h | 2 | 252 | 879 | 65,266,291 |
| 22e3b6b7be6c2606 | codex | workspace | 2026-07-14T13:29:30.292Z | 4.65h | 1 | 23 | 87 | 10,675,616 |
| 45baecd8695f97dc | codex | bpf-benchmark | 2026-05-12T17:53:25.848Z | 4.52h | 38 | 141 | 921 | 74,157,529 |
| 67707db6095ce29e | codex | bpf-benchmark | 2026-04-08T05:14:01.316Z | 4.52h | 26 | 179 | 879 | 1,453,367,345 |
| 0b0292bbd69afda2 | codex | agentsight | 2026-07-23T04:58:00.783Z | 4.52h | 2 | 69 | 377 | 47,339,237 |
| 7adc74bc1e194aec | codex | bpf-benchmark | 2026-04-18T00:50:04.829Z | 4.50h | 2 | 242 | 670 | 71,382,747 |
| 2a181e17f25dd47e | codex | bpf-benchmark | 2026-04-18T00:50:04.839Z | 4.50h | 2 | 229 | 1,041 | 142,392,569 |
| 96898f5400efbd7d | codex | bpf-benchmark | 2026-04-18T00:50:06.737Z | 4.49h | 2 | 138 | 533 | 72,223,073 |
| bcf7a2d26cec7dc7 | codex | bpf-benchmark | 2026-04-23T23:49:36.782Z | 4.47h | 2 | 315 | 672 | 56,936,297 |
| 3f5365b2b097ab49 | claude | agentsight | 2026-06-04T18:32:37.594Z | 4.45h | 18 | 333 | 228 | 21,295,769 |
| de68342feccc7d81 | codex | agentsight | 2026-07-13T03:37:46.773Z | 4.45h | 2 | 23 | 88 | 972,108,211 |
| c30e26440511f3e3 | codex | eunomia-bpf | 2026-03-07T04:42:58.086Z | 4.42h | 20 | 110 | 401 | 23,001,333 |
| 0fd64a65eaee1bad | codex | bpf-benchmark | 2026-04-29T22:46:34.419Z | 4.37h | 2 | 136 | 670 | 68,872,537 |
| e1c62530ec9c8986 | codex | ebpf-verifier-agent | 2026-06-18T00:53:08.647Z | 4.34h | 40 | 211 | 558 | 29,050,727 |
| 50ad469dbdc4238f | codex | bpf-benchmark | 2026-04-17T02:58:16.584Z | 4.31h | 2 | 144 | 475 | 39,114,611 |
| 1cb6dd454ad93346 | claude | kernel-script-paper | 2026-06-29T23:41:01.912Z | 4.29h | 14 | 81 | 52 | 4,410,791 |
| de83cb22b11b46da | codex | bpf-benchmark | 2026-04-24T17:42:08.551Z | 4.26h | 2 | 253 | 734 | 47,957,121 |
| 073e6aeacfdcbd25 | claude | ActPlane | 2026-06-09T04:55:56.453Z | 4.25h | 102 | 380 | 227 | 26,017,254 |
| 0ebc5ed94163890a | codex | bpftime | 2026-07-14T09:13:33.939Z | 4.18h | 7 | 190 | 584 | 58,074,223 |
| 6e5bf4d509907da1 | codex | bpf-benchmark | 2026-04-28T17:24:51.020Z | 4.18h | 2 | 114 | 355 | 43,219,469 |
| 8f37532a8c8342bb | codex | agentsight | 2026-07-12T00:24:40.776Z | 4.18h | 1 | 11 | 27 | 3,259,458 |
| ed76294e8973e34d | codex | agentsight | 2026-07-24T02:35:19.330Z | 4.16h | 1 | 19 | 165 | 4,309,914,098 |
| c525a5b98c598a9a | codex | bpf-benchmark | 2026-04-05T18:39:50.685Z | 4.07h | 11 | 95 | 410 | 870,159,870 |
| e659dc22075d965d | claude | ActPlane | 2026-06-10T17:24:09.701Z | 4.06h | 85 | 428 | 267 | 30,358,543 |
| c5757c9bdfa980e5 | codex | bpf-benchmark | 2026-04-20T17:48:01.171Z | 4.04h | 2 | 327 | 526 | 68,439,279 |
| 20eb859c939eb788 | codex | bpf-benchmark | 2026-04-04T19:14:53.577Z | 4.03h | 6 | 21 | 143 | 7,919,009 |
| 9d2d93dfaa2a662d | codex | eunomia.dev | 2026-07-18T21:50:48.929Z | 4.01h | 1 | 15 | 113 | 13,847,230 |
| f30bb4f06a9cbddb | codex | bpf-benchmark | 2026-04-23T18:59:34.846Z | 3.88h | 2 | 236 | 704 | 59,712,659 |
| ae7fb9c6396c4046 | codex | kernel-script-paper | 2026-07-22T01:37:38.597Z | 3.85h | 8 | 8 | 29 | 2,157,252 |
| 24c0d1749a012047 | codex | bpf-developer-tutorial | 2026-03-07T04:47:49.875Z | 3.84h | 10 | 74 | 346 | 19,083,856 |
| 8b7b5acca20c1964 | codex | agentsight | 2026-07-13T08:04:41.799Z | 3.82h | 1 | 63 | 230 | 1,123,119,210 |
| 49d422f80c8a9c99 | claude | bpf-benchmark | 2026-06-23T00:20:22.547Z | 3.80h | 48 | 268 | 177 | 19,921,028 |
| 17c569fe38dcb999 | codex | bpf-benchmark | 2026-03-29T05:28:09.518Z | 3.77h | 2 | 246 | 743 | 58,069,417 |
| ef769c564e77a60e | codex | bpf-benchmark | 2026-04-29T23:23:10.690Z | 3.76h | 2 | 332 | 760 | 77,493,436 |
| b63a7fa87f2b129e | codex | ebpf-verifier-agent | 2026-06-17T02:23:05.216Z | 3.75h | 7 | 132 | 273 | 19,653,743 |
| 9343a2bc4b7c86f0 | codex | agentsight | 2026-07-24T03:42:07.009Z | 3.75h | 1 | 47 | 213 | 1,706,145,383 |
| c838ce09ca45d09e | codex | workspace | 2026-03-07T19:52:25.902Z | 3.72h | 12 | 56 | 169 | 9,806,699 |
| d29ffd23eaa41b52 | claude | ActPlane | 2026-06-21T00:16:13.955Z | 3.71h | 121 | 374 | 191 | 24,994,318 |
| 0ad827012dd8e385 | codex | eunomia.dev | 2026-06-26T04:41:54.971Z | 3.70h | 11 | 172 | 317 | 20,741,006 |
| 8e755fb1f213bd5b | codex | bpf-benchmark | 2026-04-29T06:21:48.217Z | 3.68h | 2 | 191 | 663 | 70,751,098 |
| 8beb2ace81ab6ba2 | codex | bpf-benchmark | 2026-04-13T22:31:08.428Z | 3.68h | 21 | 94 | 565 | 39,884,760 |
| 6bd8cdac8b1ea5d0 | codex | bpf-benchmark | 2026-04-28T17:24:46.065Z | 3.62h | 2 | 120 | 388 | 34,028,309 |
| 29389e6edb107e73 | codex | agentsight | 2026-06-23T03:35:48.193Z | 3.61h | 19 | 154 | 376 | 29,171,584 |
| 2837fbec77236dc1 | codex | bpf-benchmark | 2026-03-26T15:27:40.611Z | 3.60h | 32 | 200 | 619 | 42,088,663 |
| 46387af99ef0bf11 | codex | bpf-benchmark | 2026-04-08T06:06:11.441Z | 3.57h | 17 | 150 | 439 | 1,462,878,152 |
| a0e2288c6021d4a7 | codex | eunomia.dev | 2026-05-31T22:58:35.694Z | 3.57h | 26 | 94 | 379 | 31,084,580 |
| 4dc2d933ab356bb9 | codex | bpf-benchmark | 2026-03-31T14:01:23.688Z | 3.56h | 4 | 40 | 99 | 252,670,799 |
| 25d0f9739c561736 | codex | agentsight | 2026-06-05T00:44:18.762Z | 3.54h | 13 | 123 | 287 | 17,729,661 |
| f4d4287b46ffb85c | codex | agentsight | 2026-06-04T20:51:10.701Z | 3.50h | 21 | 326 | 774 | 49,163,462 |
| 6e2104cc0c0b024a | claude | bpf-developer-tutorial | 2026-07-20T00:45:02.987Z | 3.47h | 22 | 139 | 90 | 11,934,701 |
| 50cf352445523807 | codex | agentsight | 2026-07-15T09:04:12.873Z | 3.46h | 1 | 41 | 162 | 2,179,372,351 |
| a829726c5b6c8eb7 | codex | bpf-benchmark | 2026-04-04T18:43:07.373Z | 3.46h | 4 | 69 | 313 | 532,069,131 |
| ca56347e1c23ef9e | codex | bpf-benchmark | 2026-04-22T01:28:38.912Z | 3.44h | 2 | 307 | 594 | 59,336,741 |
| 5548aafa254f2276 | codex | agentsight | 2026-07-24T03:21:41.724Z | 3.44h | 1 | 24 | 74 | 9,587,568 |
| 363bf0884ce84cfd | codex | bpf-benchmark | 2026-05-21T01:00:47.622Z | 3.44h | 35 | 99 | 391 | 28,156,864 |
| 4d5f8592e3f98289 | codex | ActPlane | 2026-07-17T12:35:31.694Z | 3.39h | 1 | 26 | 194 | 168,856,204 |
| 6a3eb16c2852cec0 | codex | agentsight | 2026-07-20T01:34:02.732Z | 3.37h | 0 | 14 | 38 | 957,702,538 |
| f334b149f70d88d9 | codex | 3 | 2025-11-01T04:09:40.125Z | 3.35h | 11 | 10 | 45 | 1,169,453 |
| 136fb66256c057a4 | codex | eunomia-bpf | 2026-03-07T19:48:13.751Z | 3.33h | 26 | 118 | 331 | 20,749,224 |
| 7ec76b05335ee8eb | codex | bpf-benchmark | 2026-04-30T20:44:13.743Z | 3.27h | 2 | 143 | 386 | 49,811,118 |
| cfc9f35a96cd9dd4 | codex | bpf-benchmark | 2026-04-09T04:35:28.503Z | 3.25h | 12 | 88 | 314 | 1,939,119,171 |
| 4a488057e82cb889 | codex | bpf-benchmark | 2026-04-30T20:46:33.289Z | 3.21h | 2 | 145 | 521 | 48,736,667 |
| f075d19e7dc70ca4 | codex | bpf-benchmark | 2026-04-25T06:54:49.248Z | 3.17h | 2 | 187 | 553 | 35,209,881 |
| 5698d9f61bbbb7cc | codex | workspace | 2026-06-23T04:18:20.421Z | 3.11h | 13 | 203 | 426 | 34,379,521 |
| fb3c64992d190a36 | codex | bpf-benchmark | 2026-04-09T09:34:01.322Z | 3.11h | 17 | 90 | 193 | 2,086,147,774 |
| 93e7ff8cfe114302 | codex | bpf-benchmark | 2026-04-04T19:28:49.862Z | 3.09h | 3 | 40 | 228 | 546,760,386 |
| b3222b3ec085397f | codex | agentsight | 2026-07-14T11:33:31.813Z | 3.09h | 0 | 9 | 40 | 1,796,051,150 |
| ddce86a2434fb88a | codex | agentsight | 2026-07-04T05:48:44.015Z | 3.07h | 6 | 37 | 106 | 4,130,252 |
| 5ba811f6085ac986 | codex | bpf-benchmark | 2026-05-03T15:44:05.496Z | 3.05h | 2 | 124 | 486 | 55,365,773 |
| 7881d15b9dd455bd | codex | workspace | 2026-07-14T16:22:38.587Z | 2.99h | 0 | 5 | 56 | 2,272,000,864 |
| c1b8df31c66fe9dc | codex | bpf-benchmark | 2026-04-24T21:59:01.016Z | 2.98h | 2 | 164 | 747 | 53,866,082 |
| 8e5ac15352959223 | codex | bpf-benchmark | 2026-03-23T03:50:18.894Z | 2.97h | 2 | 145 | 939 | 94,001,246 |
| 66be9f031ff753ec | codex | bpf-benchmark | 2026-04-26T19:22:56.075Z | 2.95h | 2 | 183 | 230 | 24,535,418 |
| 9d61e50338d440ea | codex | agentsight | 2026-07-23T04:34:46.674Z | 2.93h | 2 | 13 | 67 | 8,038,795 |
| 785a6a62c67c82c0 | codex | agentsight | 2026-07-12T23:25:22.409Z | 2.89h | 0 | 14 | 88 | 820,904,868 |
| b925ef24e27f0167 | codex | ActPlane | 2026-06-26T03:16:08.107Z | 2.88h | 14 | 355 | 558 | 49,414,493 |
| 4e2002ae8bd238ba | codex | bpf-benchmark | 2026-04-23T08:44:07.231Z | 2.88h | 2 | 183 | 598 | 46,861,645 |
| 6130f80703f70689 | codex | bpf-benchmark | 2026-04-08T01:51:40.824Z | 2.85h | 16 | 122 | 645 | 1,329,244,040 |
| 1907a475733057f5 | codex | workspace | 2026-07-11T14:24:37.387Z | 2.83h | 1 | 25 | 153 | 25,074,144 |
| 17b547b59f889cb7 | claude | agentsight | 2026-06-04T03:51:45.274Z | 2.82h | 19 | 138 | 93 | 10,461,072 |
| df7ab9b2e78458a6 | claude | bpf-benchmark | 2026-06-23T04:23:08.995Z | 2.81h | 15 | 74 | 53 | 3,903,232 |
| ffb57fff27477872 | codex | agentsight | 2026-07-20T05:52:31.938Z | 2.80h | 10 | 29 | 166 | 24,536,783 |
| 5e415a1754bf78aa | codex | ebpf-verifier-agent | 2026-06-14T22:05:47.471Z | 2.79h | 8 | 46 | 133 | 406,376,975 |
| 45f2305b07592de3 | codex | bpf-benchmark | 2026-04-09T09:52:52.503Z | 2.78h | 14 | 58 | 297 | 18,262,882 |
| b094182711bddaeb | codex | agentsight | 2026-07-23T04:48:29.622Z | 2.75h | 2 | 34 | 140 | 16,164,234 |
| cd91e0b7bcf91ceb | codex | agentsight | 2026-06-02T02:47:24.567Z | 2.75h | 11 | 132 | 274 | 20,579,067 |
| 36023c4efa3c8edd | codex | bpf-benchmark | 2026-03-23T18:37:35.889Z | 2.74h | 62 | 210 | 604 | 39,937,041 |
| caa667bef72b6a8f | codex | bpf-benchmark | 2026-04-21T17:27:06.620Z | 2.71h | 2 | 93 | 229 | 22,890,786 |
| 7f10df981697b1f3 | codex | agentsight | 2026-07-15T13:03:51.405Z | 2.71h | 1 | 16 | 196 | 114,313,731 |
| e7490ba05a01d631 | codex | agentsight | 2026-06-04T21:14:28.046Z | 2.69h | 9 | 54 | 155 | 14,209,567 |
| 1c04f21b677ef338 | claude | agentskill-observability-paper | 2026-07-12T04:16:18.218Z | 2.68h | 108 | 647 | 345 | 85,515,828 |
| 4b199090a07be00c | codex | eunomia.dev | 2026-05-27T00:48:11.312Z | 2.66h | 6 | 24 | 97 | 3,418,754 |
| be4c348d5f5e7e93 | codex | bpf-benchmark | 2026-03-28T22:09:16.075Z | 2.65h | 2 | 135 | 444 | 37,761,420 |
| 6895c498fdee3711 | codex | wasm-bpf | 2026-03-06T03:58:20.428Z | 2.64h | 13 | 296 | 992 | 62,041,627 |
| cce9f9b0d9211f4e | codex | workspace | 2026-07-11T12:46:56.972Z | 2.63h | 0 | 5 | 19 | 58,373,477 |
| 1dc72e2aa34ec70c | codex | agentsight | 2026-07-15T08:51:10.344Z | 2.62h | 1 | 18 | 48 | 2,157,391,125 |
| fb8144520b007a7e | codex | bpf-benchmark | 2026-04-28T06:27:55.593Z | 2.58h | 2 | 59 | 150 | 14,297,123 |
| 5402fcb43e9963e1 | codex | agentsight | 2026-07-22T23:11:52.928Z | 2.57h | 1 | 14 | 60 | 1,546,633,197 |
| 479b0fcb8a2e9031 | codex | bpf-benchmark | 2026-04-29T11:21:13.535Z | 2.56h | 2 | 132 | 524 | 49,778,455 |
| 90e80d2725996a26 | claude | ActPlane | 2026-06-20T03:12:30.035Z | 2.55h | 28 | 302 | 152 | 18,117,241 |
| 6514789bb07b1473 | codex | bpf-benchmark | 2026-05-21T04:27:50.316Z | 2.54h | 25 | 136 | 651 | 42,654,261 |
| b6b531f22e341fcd | codex | bpf-benchmark | 2026-05-22T05:32:29.331Z | 2.52h | 15 | 79 | 518 | 44,903,961 |
| 2df0aad17790eb83 | codex | bpf-benchmark | 2026-04-08T02:11:11.564Z | 2.52h | 15 | 110 | 416 | 1,317,434,318 |
| a57d9545739cee55 | codex | bpf-benchmark | 2026-04-30T17:43:44.526Z | 2.51h | 2 | 114 | 816 | 78,806,216 |
| 3ccbb5b233407bc9 | codex | agentsight | 2026-07-22T22:43:33.824Z | 2.51h | 1 | 11 | 42 | 1,529,124,712 |
| 09db1ff7ff91563d | codex | bpf-benchmark | 2026-04-30T20:46:26.377Z | 2.50h | 2 | 98 | 328 | 27,199,806 |
| 3889e6740a187ebe | codex | bpf-benchmark | 2026-04-29T18:58:25.462Z | 2.49h | 2 | 129 | 860 | 73,228,285 |
| 446518db59dd61ac | codex | workspace | 2026-06-24T06:14:11.353Z | 2.49h | 10 | 67 | 167 | 8,988,890 |
| 0b1fda4e1f3e2a07 | codex | bpf-benchmark | 2026-03-29T05:36:42.503Z | 2.49h | 2 | 143 | 407 | 34,699,467 |
| 0bb9e9a5acba0c1c | codex | agentsight | 2026-07-13T20:36:24.591Z | 2.48h | 0 | 8 | 59 | 1,382,454,126 |
| ac0445b621c99bf6 | codex | agentsight | 2026-07-24T03:38:22.844Z | 2.46h | 1 | 24 | 114 | 14,330,526 |
| 840e836a316ce67c | codex | bpf-benchmark | 2026-04-26T06:17:01.972Z | 2.45h | 2 | 52 | 70 | 5,894,178 |
| 0c806b26abb0291b | codex | workspace | 2026-06-24T21:54:19.402Z | 2.44h | 11 | 157 | 346 | 20,597,157 |
| a7d345f8504ecd58 | codex | agentsight | 2026-07-13T00:52:09.704Z | 2.44h | 1 | 13 | 34 | 856,982,433 |
| 5844396f4b52783a | codex | agentfs | 2026-05-17T02:45:09.757Z | 2.43h | 36 | 123 | 385 | 27,315,750 |
| 289a38b3a22cac0d | codex | agentsight | 2026-07-15T10:06:14.524Z | 2.42h | 2 | 14 | 118 | 2,203,338,560 |
| cfe7b2b0a88f9b6f | codex | workspace | 2026-07-13T05:23:32.520Z | 2.42h | 2 | 28 | 70 | 1,440,338,374 |
| eec42c4341125b7f | codex | bpftime | 2026-03-06T07:16:39.351Z | 2.41h | 13 | 127 | 376 | 24,462,456 |
| 1246dd34da8c3c88 | codex | bpf-benchmark | 2026-04-22T21:33:44.593Z | 2.41h | 2 | 179 | 697 | 56,648,927 |
| 900cc2e9449be818 | claude | ActPlane | 2026-06-01T04:05:19.597Z | 2.40h | 25 | 139 | 84 | 4,508,922 |
| 32857a22bc4cfeb0 | claude | agentsight | 2026-06-26T04:43:59.541Z | 2.38h | 6 | 30 | 23 | 531,321 |
| 1c9ad10f54d23bcd | codex | workspace | 2026-06-30T22:57:22.804Z | 2.36h | 21 | 143 | 288 | 18,552,149 |
| 5253afde60a0fe64 | codex | eunomia-bpf | 2026-03-08T20:25:34.478Z | 2.36h | 6 | 44 | 129 | 9,560,298 |
| 64deccaf129581a1 | codex | workspace | 2026-07-12T03:26:50.442Z | 2.35h | 1 | 7 | 31 | 566,895,889 |
| 075a1a27aaa11f7e | codex | agentsight-research-semantic-flamegraph | 2026-07-09T05:43:08.548Z | 2.35h | 11 | 31 | 61 | 2,665,033 |
| c9b25de95b144622 | claude | agentsight | 2026-07-03T03:38:43.969Z | 2.33h | 25 | 129 | 61 | 6,376,087 |
| 439bfa9cc7be4822 | codex | paper | 2026-03-28T23:53:18.811Z | 2.32h | 2 | 133 | 389 | 30,350,404 |
| 528bb079da71973b | codex | agentsight | 2026-07-15T13:39:56.374Z | 2.31h | 1 | 11 | 80 | 116,877,375 |
| 59d75b87eab3840d | claude | ActPlane | 2026-06-05T20:24:43.375Z | 2.30h | 70 | 456 | 278 | 30,479,772 |
| 093ac13f1e1ec962 | claude | ephemeral | 2026-07-17T06:10:28.067Z | 2.30h | 3 | 77 | 41 | 2,743,031 |
| 741da6e55b43eb9b | claude | agentskill-observability-paper | 2026-07-12T04:40:23.535Z | 2.30h | 63 | 481 | 281 | 57,921,492 |
| 9c640d7ffa9d56bc | codex | workspace | 2026-07-05T20:06:19.276Z | 2.30h | 5 | 20 | 42 | 1,343,911 |
| fbf11297acb7f399 | codex | bpf-benchmark | 2026-07-22T07:31:21.794Z | 2.29h | 0 | 20 | 203 | 2,944,038,552 |
| 7f8d45bd63067d46 | codex | bpf-benchmark | 2026-04-30T21:02:17.794Z | 2.28h | 2 | 152 | 578 | 50,740,364 |
| e11b0292d7f754bc | codex | workspace | 2026-07-13T08:39:25.014Z | 2.25h | 1 | 14 | 33 | 1,524,710,930 |
| e94104b63d503267 | claude | ActPlane | 2026-06-11T07:10:17.066Z | 2.25h | 71 | 216 | 110 | 15,587,168 |
| 1aef6052f627336c | codex | workspace | 2026-06-23T04:44:46.286Z | 2.24h | 6 | 45 | 148 | 5,867,502 |
| c5d9ea9694375d14 | claude | ActPlane | 2026-05-31T20:13:59.332Z | 2.24h | 1 | 49 | 54 | 5,715,188 |
| 53179b3ccb29b9c6 | codex | workspace | 2026-07-10T02:01:28.942Z | 2.23h | 9 | 27 | 69 | 1,048,152 |
| ba873306b9019787 | codex | bpf-benchmark | 2026-04-05T00:20:40.643Z | 2.22h | 18 | 105 | 428 | 677,241,537 |
| af1b4d844bf1128a | codex | agentsight | 2026-07-20T05:07:49.461Z | 2.21h | 2 | 17 | 67 | 7,366,068 |
| 4d8eb65dc311842d | codex | bpftime | 2026-03-08T07:28:20.382Z | 2.21h | 1 | 310 | 319 | 19,670,721 |
| ba0a46b570382404 | codex | bpftime | 2026-03-08T06:16:27.018Z | 2.17h | 11 | 200 | 501 | 36,576,853 |
| af284ed510de3b2c | claude | reward-guard | 2026-07-09T03:40:58.481Z | 2.16h | 5 | 19 | 17 | 431,031 |
| 2cace3360101efbd | codex | agentsight | 2026-07-19T02:45:21.154Z | 2.16h | 1 | 21 | 61 | 766,568,997 |
| ae677b218ffbac98 | codex | sandlock | 2026-05-23T22:30:26.402Z | 2.15h | 34 | 115 | 312 | 25,146,154 |
| 48884cc349f490a7 | codex | bpf-benchmark | 2026-04-08T02:12:47.685Z | 2.14h | 14 | 62 | 244 | 1,310,247,576 |
| 65af081397e34a87 | codex | namei_ext | 2026-06-15T10:15:42.316Z | 2.14h | 16 | 89 | 283 | 245,191,602 |
| 4923bd1dd13cf902 | codex | ActPlane | 2026-06-09T08:34:19.694Z | 2.11h | 49 | 153 | 277 | 25,845,501 |
| f11cfd85af4b7030 | claude | eunomia.dev | 2026-06-01T01:48:34.166Z | 2.09h | 74 | 340 | 175 | 40,989,551 |
| 4817d66371e405f9 | codex | bpf-benchmark | 2026-04-22T06:14:51.142Z | 2.08h | 2 | 61 | 210 | 17,550,524 |
| 2cb82a114e719817 | claude | agentskill-observability-paper | 2026-07-26T01:57:03.486Z | 2.08h | 33 | 81 | 31 | 3,186,958 |
| f1cbfebbfce3460b | codex | bpf-benchmark | 2026-04-25T01:05:29.561Z | 2.04h | 2 | 112 | 343 | 32,666,819 |
| ab8792cc469e03e9 | codex | ActPlane | 2026-06-01T01:43:27.527Z | 2.04h | 83 | 171 | 532 | 41,944,259 |
| 7c7c9b1ee811d787 | codex | geoperf | 2026-07-13T03:22:30.556Z | 2.03h | 6 | 18 | 24 | 3,147,919 |
| b45eb0ac59399066 | codex | bpf-benchmark | 2026-04-09T03:51:38.488Z | 2.01h | 11 | 59 | 195 | 1,894,630,421 |
| b59e41408c17c7c9 | codex | bpf-benchmark | 2026-04-08T16:35:20.813Z | 2.00h | 9 | 118 | 527 | 1,588,236,491 |
| e81fa429704ffbcb | codex | workspace | 2026-07-14T10:51:22.835Z | 2.00h | 1 | 8 | 49 | 2,087,883,272 |
| 746123464ad685a7 | codex | agentsight | 2026-07-13T00:41:04.034Z | 1.99h | 1 | 8 | 24 | 850,749,694 |
| d9e1129360b93676 | codex | bpf-benchmark | 2026-04-06T03:22:04.229Z | 1.99h | 7 | 75 | 321 | 945,567,883 |
| 7b991ccc9baf2e02 | claude | academic-writing-skills | 2026-07-14T19:49:00.429Z | 1.98h | 21 | 165 | 102 | 7,966,330 |
| 5d58f6d7d2ff2c87 | codex | bpf-benchmark | 2026-04-30T16:46:44.654Z | 1.97h | 2 | 122 | 547 | 49,869,000 |
| 7bb574c2179d5273 | codex | bpf-benchmark | 2026-03-30T03:39:52.918Z | 1.97h | 2 | 137 | 527 | 43,664,906 |
| 902a5978efa94209 | codex | bpf-benchmark | 2026-04-22T23:59:35.325Z | 1.94h | 2 | 116 | 318 | 30,125,079 |
| 32c5b286a9b22c48 | claude | ActPlane | 2026-06-01T03:50:47.501Z | 1.93h | 33 | 229 | 132 | 12,987,096 |
| 7879dd8db48a8ce2 | claude | my-paper-work | 2026-07-07T21:32:43.666Z | 1.92h | 49 | 329 | 211 | 22,859,683 |
| cbbf99ca0efef90b | codex | agentsight | 2026-07-20T07:40:46.742Z | 1.90h | 0 | 21 | 50 | 1,107,344,223 |
| c9133e57f148675f | codex | bpf-benchmark | 2026-05-10T20:17:29.528Z | 1.89h | 2 | 75 | 503 | 53,450,697 |
| b32c68952e812a09 | codex | ActPlane | 2026-06-09T21:14:04.391Z | 1.88h | 12 | 32 | 84 | 3,138,600 |
| 7919f9673dac4ee2 | codex | bpf-benchmark | 2026-04-24T04:23:51.235Z | 1.86h | 2 | 124 | 454 | 49,106,794 |
| addfdda56418cde7 | codex | agentsight | 2026-07-14T12:35:01.868Z | 1.86h | 0 | 9 | 61 | 1,831,418,793 |
| 4d8180aa2f413ea4 | codex | bpf-benchmark | 2026-03-29T20:17:09.510Z | 1.85h | 21 | 46 | 106 | 5,484,813 |
| 4c649423561907b0 | claude | agentsight-research-semantic-flamegraph | 2026-07-07T06:30:16.791Z | 1.85h | 40 | 396 | 280 | 25,642,956 |
| 75cf5a313641d46e | codex | agentsight | 2026-07-21T03:04:12.055Z | 1.84h | 0 | 19 | 128 | 3,699,433,502 |
| 32b0e50308b1d092 | codex | namei_ext | 2026-06-14T05:12:25.775Z | 1.83h | 4 | 27 | 67 | 2,999,808 |
| 67ab4840ca177dbe | codex | workspace | 2026-07-22T07:47:54.929Z | 1.83h | 15 | 35 | 181 | 24,342,445 |
| 36a8498ec018cf03 | codex | namei_ext | 2026-06-17T12:23:23.651Z | 1.83h | 16 | 69 | 178 | 241,956,946 |
| 62c1990111bfb0ff | codex | agentsight | 2026-07-12T02:41:36.162Z | 1.81h | 0 | 15 | 65 | 301,898,230 |
| 5323c56c8e1e2f70 | codex | workspace | 2026-07-13T05:35:33.535Z | 1.81h | 2 | 8 | 26 | 1,879,583 |
| 163520558620488d | codex | bpf-benchmark | 2026-04-04T15:00:25.174Z | 1.81h | 1 | 67 | 291 | 448,342,483 |
| 0a46e518d4d4bf8f | codex | bpf-benchmark | 2026-06-23T00:41:17.005Z | 1.80h | 5 | 27 | 57 | 2,181,858 |
| 0b0cd6a056a17f14 | codex | linux-framework | 2026-03-29T00:23:56.108Z | 1.79h | 2 | 89 | 285 | 20,431,584 |
| a238d7d299e73839 | codex | geoperf | 2026-07-13T03:22:31.488Z | 1.79h | 5 | 26 | 77 | 7,069,923 |
| b17946718018b9b1 | codex | bpf-benchmark | 2026-04-30T00:08:52.778Z | 1.79h | 2 | 56 | 340 | 30,417,306 |
| 03a3ece90bf96757 | codex | bpf-benchmark | 2026-03-30T05:24:14.479Z | 1.78h | 2 | 145 | 581 | 44,478,726 |
| 96d59c81c3f9ba5f | codex | bpf-benchmark | 2026-03-25T03:38:32.216Z | 1.77h | 8 | 52 | 212 | 355,592,935 |
| 6e224bf6dd15276b | codex | bpf-benchmark | 2026-04-21T22:28:11.339Z | 1.76h | 2 | 98 | 275 | 20,216,819 |
| bb3da810fc448d07 | codex | bpf-benchmark | 2026-04-19T01:16:36.335Z | 1.75h | 2 | 55 | 265 | 40,534,396 |
| 7018512193551077 | codex | workspace | 2026-07-03T20:24:32.235Z | 1.74h | 3 | 13 | 55 | 135,037,129 |
| 376143ce8780e657 | codex | agentsight | 2026-07-17T09:21:02.462Z | 1.73h | 0 | 8 | 60 | 2,805,010,485 |
| 00cc21a9733951d4 | claude | agentsight | 2026-07-15T07:04:31.627Z | 1.73h | 32 | 80 | 34 | 2,663,709 |
| 693de30502985d11 | codex | namei_ext | 2026-06-29T22:08:24.676Z | 1.71h | 21 | 176 | 376 | 30,735,202 |
| 7995ff1278629db1 | codex | bpf-benchmark | 2026-04-18T08:11:56.297Z | 1.71h | 2 | 38 | 233 | 17,474,464 |
| 4e81d6ca1540a3ae | codex | bpf-benchmark | 2026-03-28T14:42:31.278Z | 1.71h | 2 | 79 | 143 | 12,651,569 |
| f368a6d8f1d9b8be | codex | ActPlane | 2026-06-10T07:46:19.401Z | 1.69h | 5 | 69 | 151 | 9,701,955 |
| 956cc1dd9e2c962c | codex | bpf-benchmark | 2026-03-29T10:43:57.290Z | 1.69h | 2 | 127 | 340 | 33,011,916 |
| cc85f625f04df63f | codex | bpf-benchmark | 2026-03-12T04:26:46.548Z | 1.68h | 3 | 65 | 145 | 11,428,216 |
| cd98dbbc3482b17f | codex | workspace | 2026-07-14T10:58:22.914Z | 1.67h | 1 | 30 | 58 | 2,092,231,607 |
| afb51adbb46e6bc5 | codex | bpf-benchmark | 2026-04-24T04:36:10.346Z | 1.66h | 2 | 101 | 229 | 12,771,077 |
| a45d455e339aad2b | codex | bpf-benchmark | 2026-04-08T16:53:06.743Z | 1.66h | 9 | 121 | 429 | 1,596,500,934 |
| b60afdb9a950d92c | codex | bpf-benchmark | 2026-04-24T04:37:09.515Z | 1.62h | 2 | 100 | 311 | 25,628,848 |
| 87883848066d517b | codex | bpf-benchmark | 2026-03-21T03:15:00.368Z | 1.62h | 2 | 96 | 301 | 17,926,490 |
| d44f981f99c6720b | codex | bpf-benchmark | 2026-03-29T05:28:37.514Z | 1.61h | 2 | 72 | 236 | 16,533,418 |
| 6a1fba992888469e | claude | my-paper-work | 2026-07-17T06:02:09.806Z | 1.61h | 26 | 81 | 45 | 4,431,786 |
| 08f28cda06143a2a | codex | agentsight | 2026-07-12T22:11:59.300Z | 1.60h | 1 | 6 | 21 | 752,096,666 |
| 7b6419e0984f3792 | codex | bpf-benchmark | 2026-03-25T03:49:23.093Z | 1.60h | 5 | 37 | 233 | 359,998,165 |
| a730df3f8e3e2cc7 | codex | bpf-benchmark | 2026-05-08T23:49:23.434Z | 1.60h | 2 | 59 | 404 | 48,505,177 |
| 415ac35e554c1c59 | codex | geoperf | 2026-07-07T23:05:12.347Z | 1.59h | 11 | 37 | 71 | 4,317,494 |
| db83fff6e2e53a60 | claude | agentsight-research-semantic-flamegraph | 2026-07-25T06:04:50.622Z | 1.58h | 26 | 122 | 58 | 8,991,258 |
| ddd173c7654e93ac | codex | agentsight | 2026-07-20T14:51:03.871Z | 1.57h | 1 | 14 | 59 | 3,397,357,074 |
| 13bf9d36c8e0e114 | codex | bpf-benchmark | 2026-04-30T23:04:45.146Z | 1.57h | 2 | 170 | 192 | 7,167,454 |
| 956a748fc9fe53c4 | claude | eunomia.dev | 2026-07-16T23:11:18.606Z | 1.57h | 3 | 137 | 75 | 10,785,544 |
| ea56d208c9969cf9 | codex | agentsight | 2026-07-20T15:45:06.130Z | 1.56h | 1 | 2 | 63 | 3,416,943,004 |
| 52a5dd4cf211ce2c | codex | agentsight | 2026-07-20T09:25:40.745Z | 1.56h | 1 | 14 | 60 | 3,249,758,290 |
| 2760c3cc6d084f2e | codex | bpf-benchmark | 2026-04-28T03:35:24.256Z | 1.55h | 2 | 213 | 310 | 31,882,595 |
| dd2b786c555320e0 | codex | bpf-benchmark | 2026-03-20T17:07:38.417Z | 1.54h | 2 | 62 | 184 | 17,863,629 |
| cec29a09f9c2dcb9 | claude | eunomia.dev | 2026-07-16T22:58:58.469Z | 1.54h | 8 | 215 | 85 | 7,987,649 |
| e2e2d26383b5ff99 | codex | agentsight | 2026-07-15T10:48:28.761Z | 1.54h | 2 | 7 | 91 | 2,218,090,854 |
| 18f4c5d0e27f2248 | codex | bpf-benchmark | 2026-04-07T03:50:09.554Z | 1.53h | 9 | 43 | 93 | 1,145,819,277 |
| 5a12dab944db231c | codex | bpf-benchmark | 2026-04-07T03:50:10.834Z | 1.53h | 3 | 27 | 64 | 1,144,024,075 |
| 5ecd9b6689db3300 | codex | bpf-benchmark | 2026-03-12T03:53:53.734Z | 1.53h | 2 | 40 | 106 | 10,860,068 |
| 74b2858d63251b28 | codex | bpf-benchmark | 2026-03-29T01:40:08.887Z | 1.52h | 2 | 112 | 398 | 39,285,782 |
| 7fe5351cd51708eb | codex | agentsight | 2026-07-11T20:26:50.264Z | 1.49h | 0 | 16 | 40 | 149,180,496 |
| fabd0190204669e4 | codex | paper | 2026-03-11T00:54:15.130Z | 1.48h | 4 | 81 | 299 | 18,704,941 |
| b11e46c186a681ba | codex | bpf-benchmark | 2026-04-08T17:19:00.110Z | 1.46h | 6 | 28 | 109 | 1,603,534,474 |
| c70ebe2e5dd55a99 | codex | bpf-benchmark | 2026-03-29T09:16:38.423Z | 1.45h | 2 | 81 | 282 | 22,342,813 |
| 80c3a93f4f1531a0 | codex | workspace | 2026-07-19T02:14:21.247Z | 1.43h | 1 | 20 | 75 | 9,049,692 |
| 777528b757405ebf | codex | agentsight | 2026-07-05T21:39:06.885Z | 1.43h | 4 | 25 | 96 | 3,640,517 |
| 9a1c5be9e1cddb6f | claude | paper | 2026-06-11T10:24:38.433Z | 1.43h | 39 | 247 | 162 | 13,016,507 |
| 0264f0dd9cebddc7 | codex | ActPlane | 2026-06-10T04:47:08.443Z | 1.42h | 21 | 91 | 205 | 14,181,301 |
| 015bf44cdfe291fe | codex | bpf-benchmark | 2026-03-19T00:46:57.883Z | 1.42h | 2 | 69 | 160 | 5,375,714 |
| 5ab7c1c398a46b37 | codex | bpf-benchmark | 2026-03-29T18:46:08.670Z | 1.41h | 2 | 85 | 289 | 25,305,818 |
| 56d37a4b7003dff4 | codex | bpf-benchmark | 2026-04-06T03:28:00.715Z | 1.41h | 6 | 50 | 250 | 948,906,527 |
| 2d9a4b0a4c824d39 | codex | workspace | 2026-07-14T10:37:44.025Z | 1.40h | 1 | 7 | 34 | 2,079,397,433 |
| 199afcb8ba072d23 | codex | agentsight | 2026-07-15T14:47:09.575Z | 1.40h | 1 | 8 | 52 | 2,315,034,402 |
| f0b03d423f966d38 | claude | agentsight-research-semantic-flamegraph | 2026-07-09T06:35:43.982Z | 1.39h | 54 | 414 | 247 | 55,216,693 |
| 01544683fbf7413a | codex | bpf-benchmark | 2026-03-11T19:45:05.946Z | 1.39h | 4 | 59 | 209 | 22,674,652 |
| f32e680ed668f568 | codex | bpf-benchmark | 2026-04-26T08:28:52.774Z | 1.39h | 2 | 78 | 157 | 14,694,883 |
| cd3cd7744dc95d63 | codex | bpf-benchmark | 2026-04-29T18:58:25.568Z | 1.39h | 2 | 54 | 263 | 24,840,931 |
| d7cfb54634abde60 | claude | ActPlane | 2026-06-11T08:05:10.500Z | 1.38h | 23 | 75 | 46 | 4,560,090 |
| 14e7097e1006f5d4 | claude | ActPlane | 2026-05-28T17:49:41.526Z | 1.37h | 28 | 106 | 36 | 3,931,147 |
| 06d9871951efeadb | codex | bpf-benchmark | 2026-04-07T04:00:03.329Z | 1.37h | 6 | 13 | 120 | 1,156,714,955 |
| bd04c872f2e56814 | codex | bpf-benchmark | 2026-04-07T04:00:04.683Z | 1.37h | 5 | 22 | 80 | 1,153,388,762 |
| c57ebc819399755b | codex | agentsight | 2026-06-23T21:02:46.129Z | 1.35h | 8 | 209 | 414 | 33,827,945 |
| 6e35d59f775d3e64 | codex | bpf-benchmark | 2026-04-30T19:36:10.009Z | 1.35h | 2 | 32 | 300 | 23,872,860 |
| 0286d021eaeea77b | codex | bpf-benchmark | 2026-04-26T08:28:57.761Z | 1.35h | 2 | 66 | 252 | 22,146,260 |
| 12f47731e5d8ca73 | codex | bpf-benchmark | 2026-04-23T04:10:05.558Z | 1.33h | 2 | 63 | 275 | 25,094,985 |
| fd9bc83d9c43d9f2 | codex | bpf-benchmark | 2026-03-29T05:28:40.174Z | 1.31h | 2 | 106 | 322 | 22,837,564 |
| ee9e51b29938c5f8 | codex | ActPlane | 2026-06-07T21:29:28.310Z | 1.31h | 58 | 135 | 199 | 16,259,159 |
| 0d3a5644af8636f4 | codex | linux-framework | 2026-03-29T18:01:36.947Z | 1.30h | 2 | 78 | 303 | 24,492,679 |
| 3a7467051b5352e8 | codex | agentsight | 2026-07-05T18:02:59.497Z | 1.29h | 6 | 40 | 144 | 591,275,381 |
| a97c12e5f1bc5200 | codex | namei_ext | 2026-06-17T11:01:19.579Z | 1.28h | 2 | 14 | 48 | 211,495,145 |
| 3ceb000fd14f9805 | codex | bpf-benchmark | 2026-03-29T18:43:17.360Z | 1.28h | 2 | 60 | 217 | 15,040,212 |
| 922cacf8babbc2b3 | codex | agentsight | 2026-07-05T18:03:12.437Z | 1.28h | 6 | 29 | 89 | 590,204,439 |
| 0a906274aed3248b | codex | agentsight | 2026-07-05T18:03:24.094Z | 1.27h | 7 | 37 | 133 | 592,596,021 |
| abc54149a2c349fd | codex | bpf-benchmark | 2026-04-23T11:38:23.804Z | 1.27h | 2 | 44 | 158 | 10,775,096 |
| 23a328bfb860640d | claude | agentsight | 2026-06-04T02:14:52.299Z | 1.27h | 11 | 59 | 52 | 2,766,705 |
| 998c720b168029e2 | codex | agentsight | 2026-07-05T18:03:36.629Z | 1.27h | 7 | 42 | 156 | 593,446,766 |
| c927a903d4863acc | codex | agentsight | 2026-07-03T01:29:32.638Z | 1.27h | 8 | 75 | 146 | 5,878,335 |
| 41a8888b9c6f8b83 | codex | bpf-benchmark | 2026-03-29T02:20:51.836Z | 1.26h | 2 | 115 | 256 | 19,697,819 |
| 70b672178e88d5f0 | codex | bpf-benchmark | 2026-03-27T14:55:45.128Z | 1.26h | 1 | 27 | 148 | 100,161,515 |
| b014765f7d178f3a | claude | ActPlane | 2026-06-09T08:46:56.639Z | 1.25h | 79 | 223 | 112 | 15,089,553 |
| 2669e9eed9748739 | claude | eunomia.dev | 2026-06-03T06:51:07.671Z | 1.24h | 19 | 328 | 290 | 26,753,854 |
| c9308889edaf6d28 | codex | bpf-benchmark | 2026-06-28T06:11:57.803Z | 1.23h | 28 | 110 | 159 | 12,697,227 |
| 89684cd6a8c4729d | codex | bpf-benchmark | 2026-04-29T22:46:34.498Z | 1.23h | 2 | 100 | 295 | 28,070,206 |
| e1f5725aa0ab3ff1 | codex | workspace | 2026-07-19T02:13:56.060Z | 1.22h | 1 | 19 | 60 | 7,781,242 |
| b86380e38cd1dd09 | codex | bpf-benchmark | 2026-04-09T08:41:21.699Z | 1.22h | 6 | 54 | 179 | 2,061,726,380 |
| 69ffaac2890d439c | codex | bpf-benchmark | 2026-03-19T03:36:04.539Z | 1.21h | 2 | 116 | 294 | 24,516,670 |
| c7ae7c5d42da65ab | claude | ephemeral | 2026-07-17T09:21:06.056Z | 1.20h | 3 | 346 | 217 | 29,086,501 |
| f436aa9bae4b9c83 | claude | eunomia.dev | 2026-06-15T01:11:45.042Z | 1.20h | 15 | 237 | 156 | 11,861,116 |
| 2ce82e6d067d7317 | codex | bpf-benchmark | 2026-04-09T09:53:54.573Z | 1.19h | 3 | 16 | 144 | 7,385,143 |
| 55e70023bd5fc9b3 | codex | bpf-benchmark | 2026-04-23T05:43:03.795Z | 1.19h | 2 | 48 | 129 | 8,216,594 |
| d6451024e354fa2b | codex | bpf-benchmark | 2026-04-22T18:09:14.281Z | 1.18h | 2 | 70 | 213 | 19,991,862 |
| 84792f0b2abef3ad | codex | namei_ext | 2026-07-10T02:35:22.436Z | 1.18h | 4 | 6 | 8 | 538,832,069 |
| 6686c7bfcbc20b8a | codex | bpf-benchmark | 2026-04-19T03:02:02.964Z | 1.17h | 2 | 49 | 208 | 15,312,134 |
| c6e8d0c00559ff75 | codex | bpf-benchmark | 2026-04-29T13:09:43.965Z | 1.16h | 2 | 69 | 229 | 20,808,606 |
| 55d4aef9d777558b | claude | academic-writing-skills | 2026-07-16T01:53:15.105Z | 1.16h | 4 | 24 | 16 | 533,466 |
| 326c06c9ef6b2b10 | codex | bpf-benchmark | 2026-04-28T01:20:06.220Z | 1.16h | 2 | 50 | 353 | 30,759,666 |
| b1214ff999555f25 | codex | bpftime | 2026-03-06T05:38:07.531Z | 1.15h | 20 | 87 | 270 | 18,362,453 |
| 1031f3c3f7924a84 | codex | bpf-benchmark | 2026-04-09T10:27:21.567Z | 1.15h | 6 | 34 | 127 | 2,104,480,645 |
| 91fae1569d785128 | codex | bpf-benchmark | 2026-04-29T11:21:02.484Z | 1.15h | 2 | 50 | 256 | 12,484,815 |
| cbd3872771d2abe5 | codex | linux-framework | 2026-03-20T02:43:07.864Z | 1.14h | 2 | 73 | 270 | 19,364,399 |
| aeda02c3fa12765b | codex | agentsight | 2026-07-12T22:43:31.922Z | 1.14h | 1 | 6 | 20 | 781,855,118 |
| ea07ff78fcac6735 | codex | agentsight | 2026-07-17T10:32:50.638Z | 1.12h | 2 | 14 | 107 | 12,155,717 |
| d75d63a63168aef4 | codex | bpfopt | 2026-04-29T22:12:54.713Z | 1.12h | 2 | 45 | 326 | 33,817,158 |
| 384250def71fb608 | codex | bpf-benchmark | 2026-04-30T06:13:01.919Z | 1.12h | 2 | 46 | 526 | 53,928,172 |
| 3d952731a74eede8 | codex | workspace | 2026-03-08T22:38:58.838Z | 1.12h | 1 | 131 | 389 | 322,585,235 |
| c9bc2381bca9451f | codex | bpf-benchmark | 2026-04-30T19:06:04.803Z | 1.12h | 2 | 35 | 278 | 26,239,622 |
| da1bb3800f4ec080 | claude | agentsight | 2026-06-20T05:53:30.167Z | 1.11h | 12 | 60 | 50 | 1,922,354 |
| 2576a4ab6c46d0cc | codex | bpf-benchmark | 2026-04-07T02:17:28.102Z | 1.11h | 4 | 14 | 36 | 1,094,865,822 |
| 3c68cdaaff379b95 | codex | bpf-benchmark | 2026-04-22T00:19:30.794Z | 1.11h | 2 | 40 | 142 | 10,602,045 |
| 812ce6b21eb3fc3d | codex | bpf-benchmark | 2026-03-23T09:12:37.805Z | 1.11h | 2 | 51 | 211 | 21,841,848 |
| 32c21ff9ce2058d3 | claude | bpf-benchmark | 2026-06-28T06:11:22.746Z | 1.11h | 18 | 90 | 64 | 3,674,882 |
| 1c6060a3aa6114a5 | codex | workspace | 2026-06-24T08:47:45.605Z | 1.11h | 3 | 112 | 174 | 21,892,512 |
| 783b01b9dbef9e44 | codex | bpf-benchmark | 2026-03-08T21:45:40.761Z | 1.11h | 2 | 128 | 155 | 8,115,773 |
| c473f57b64a01e30 | codex | bpf-benchmark | 2026-04-28T05:41:46.564Z | 1.11h | 2 | 38 | 88 | 4,575,750 |
| fae6b3bbc0d1dc5c | codex | bpf-benchmark | 2026-03-20T21:54:25.136Z | 1.11h | 2 | 59 | 251 | 25,982,511 |
| 4dda0e335c6df3bc | codex | bpf-benchmark | 2026-04-22T00:19:34.378Z | 1.10h | 2 | 18 | 75 | 5,768,116 |
| 6de4671f4fa79539 | codex | workspace | 2026-07-12T00:19:51.169Z | 1.09h | 0 | 36 | 46 | 491,178,495 |
| 5d5dccaf0367eae0 | claude | bpf-developer-tutorial-egress | 2026-07-19T08:26:08.721Z | 1.09h | 8 | 236 | 135 | 10,193,540 |
| e5fed3f14d23939f | codex | bpf-benchmark | 2026-04-26T04:42:21.035Z | 1.09h | 2 | 72 | 129 | 7,225,369 |
| aa30b2e92f7356c4 | codex | bpf-benchmark | 2026-04-07T02:10:33.006Z | 1.09h | 2 | 26 | 53 | 1,095,991,341 |
| 71ed2bdd37d55d32 | codex | bpf-benchmark | 2026-03-29T01:14:47.972Z | 1.07h | 2 | 57 | 206 | 21,594,783 |
| 724ab9b6d3311356 | codex | agentsight | 2026-07-17T09:46:20.058Z | 1.07h | 0 | 6 | 52 | 2,815,368,515 |
| 118aca16832204a6 | codex | bpf-benchmark | 2026-03-27T13:50:15.999Z | 1.05h | 1 | 41 | 135 | 83,626,357 |
| f7dfd1392ddd54c2 | codex | ActPlane | 2026-07-18T06:40:42.024Z | 1.05h | 1 | 13 | 64 | 425,548,541 |
| edc6c35c136487a0 | codex | bpf-benchmark | 2026-04-30T19:36:18.310Z | 1.04h | 2 | 26 | 221 | 24,995,121 |
| 1b40a96dcb0f4b49 | codex | bpf-benchmark | 2026-04-27T23:18:05.202Z | 1.04h | 2 | 56 | 178 | 14,351,988 |
| 90e96d8656c0b9f4 | claude | agentsight-research-semantic-flamegraph | 2026-07-09T06:45:33.734Z | 1.03h | 38 | 194 | 115 | 13,428,721 |
| b684b3509358377d | codex | bpf-benchmark | 2026-03-25T15:44:04.271Z | 1.03h | 7 | 14 | 53 | 483,687,538 |
| 0ecba36f7e26e62e | codex | bpf-benchmark | 2026-03-18T22:01:42.399Z | 1.02h | 2 | 124 | 153 | 9,716,916 |
| 548ce2a959bff873 | codex | eunomia-bpf | 2026-03-08T06:11:27.002Z | 1.01h | 7 | 55 | 144 | 5,917,991 |
| 68ef3dce6e86d83d | codex | bpftime | 2026-03-08T07:26:04.391Z | 1.01h | 1 | 56 | 187 | 44,421,023 |
| 3f887e04ca451587 | codex | bpf-benchmark | 2026-04-07T02:15:05.364Z | 1.01h | 3 | 7 | 23 | 1,093,004,619 |
| 6a1e844bb04ba10d | claude | ActPlane | 2026-06-05T19:18:33.585Z | 1.01h | 16 | 31 | 19 | 683,189 |
| 058e25dd5e479443 | codex | bpf-benchmark | 2026-03-19T19:05:32.255Z | 1.01h | 2 | 45 | 122 | 12,244,129 |
| aca95e86db69b4ea | codex | bpf-benchmark | 2026-03-27T03:02:46.698Z | 1.00h | 2 | 86 | 270 | 16,734,078 |
| 7fdd76696bf7e83c | codex | bpf-benchmark | 2026-04-29T22:46:15.403Z | 1.00h | 2 | 73 | 236 | 22,055,276 |
| cdf6759a2ca958a3 | codex | bpf-benchmark | 2026-04-29T10:04:09.112Z | 60.0m | 2 | 62 | 210 | 11,156,030 |
| d25db0f843c8b01c | codex | bpf-benchmark | 2026-03-29T01:44:04.500Z | 59.9m | 2 | 69 | 260 | 27,932,054 |
| 6ba1881e600bb8f5 | codex | bpftime | 2026-03-08T09:55:56.282Z | 59.3m | 1 | 104 | 113 | 4,294,775 |
| 012c8278be554db1 | codex | bpf-benchmark | 2026-03-27T17:43:54.802Z | 58.9m | 10 | 34 | 192 | 13,237,751 |
| 9d2585113aef12b2 | codex | bpf-benchmark | 2026-04-07T04:27:34.322Z | 58.9m | 11 | 43 | 116 | 1,165,554,149 |
| 3aa4e99fc7139c56 | codex | bpf-benchmark | 2026-03-11T03:09:31.877Z | 58.7m | 4 | 19 | 142 | 4,624,139 |
| 063bbab0c290850a | codex | bpf-benchmark | 2026-04-05T03:36:31.298Z | 58.5m | 5 | 29 | 129 | 714,215,543 |
| 3af24a577c8369be | claude | paper | 2026-06-11T10:48:50.452Z | 58.4m | 37 | 170 | 131 | 10,481,849 |
| 120ce72c587f5f31 | codex | bpf-benchmark | 2026-03-21T02:08:14.368Z | 58.3m | 2 | 59 | 235 | 14,602,834 |
| 7a6ed23927208fb2 | codex | eunomia-bpf | 2026-03-08T06:11:27.014Z | 58.2m | 5 | 39 | 168 | 10,994,717 |
| ad9b264ba0d28765 | codex | eunomia | 2026-03-06T02:57:15.776Z | 58.2m | 4 | 85 | 263 | 13,255,184 |
| 2b649e6c43a9f337 | claude | ActPlane | 2026-06-12T06:44:06.676Z | 57.3m | 23 | 203 | 128 | 11,283,024 |
| 3704599b23a863bc | codex | eunomia-bpf | 2026-03-08T06:11:27.066Z | 57.0m | 7 | 51 | 166 | 11,451,088 |
| 66cfc8bdf6af2b2e | codex | bpf-benchmark | 2026-04-26T06:17:23.502Z | 56.6m | 2 | 74 | 195 | 13,489,922 |
| 669239ed6f9430fa | codex | bpf-benchmark | 2026-03-18T20:28:32.810Z | 56.4m | 2 | 48 | 132 | 11,572,180 |
| a1920b46dce1d5e3 | codex | bpf-benchmark | 2026-03-26T09:39:18.705Z | 55.9m | 2 | 34 | 106 | 6,063,974 |
| 2d9818232caf8c8f | codex | bpf-benchmark | 2026-05-02T01:37:34.302Z | 55.6m | 2 | 37 | 257 | 31,783,846 |
| c6e22d1de8028bd1 | claude | kernel-script-paper | 2026-07-25T06:02:41.558Z | 55.4m | 47 | 258 | 147 | 16,246,707 |
| 3c6cef68d5d4fb90 | codex | bpf-benchmark | 2026-06-30T23:01:35.158Z | 54.4m | 6 | 65 | 171 | 7,502,479 |
| d79485032f0c2a9b | codex | eunomia-bpf | 2026-03-08T06:11:27.028Z | 53.8m | 6 | 50 | 154 | 7,482,290 |
| 79e2e80629e62877 | codex | bpf-benchmark | 2026-03-27T15:38:14.131Z | 53.8m | 2 | 71 | 228 | 15,095,677 |
| 5c899240b884b734 | codex | bpf-benchmark | 2026-04-30T19:04:03.203Z | 53.0m | 2 | 34 | 169 | 17,085,009 |
| 569419adab1bdb13 | codex | bpf-benchmark | 2026-03-20T16:05:08.139Z | 53.0m | 2 | 43 | 131 | 16,512,571 |
| b6dd278155b0f306 | codex | ebpf-verifier-agent | 2026-06-14T09:17:39.830Z | 52.8m | 6 | 47 | 167 | 6,390,312 |
| 998c74ae2ca9c02d | codex | bpf-benchmark | 2026-03-29T04:07:01.891Z | 52.2m | 2 | 69 | 317 | 28,385,215 |
| e492551bc1fd4cb8 | codex | bpf-benchmark | 2026-03-27T13:27:43.279Z | 52.1m | 2 | 120 | 374 | 31,578,663 |
| e3ce974d639ba7d6 | codex | bpf-benchmark | 2026-03-19T20:25:51.856Z | 52.0m | 2 | 78 | 139 | 9,821,337 |
| 80423d8b4a6aae52 | codex | bpf-benchmark | 2026-04-30T23:08:37.974Z | 51.8m | 2 | 18 | 100 | 9,722,536 |
| a9f53daf7cb79e0d | codex | bpf-benchmark | 2026-03-29T06:48:38.475Z | 51.8m | 2 | 60 | 192 | 11,867,303 |
| 08393b6ddf1b54ce | codex | bpf-benchmark | 2026-03-28T18:32:43.986Z | 51.1m | 2 | 128 | 190 | 11,309,113 |
| c3f961035e9011fe | codex | ebpf-verifier-agent | 2026-06-14T09:17:34.158Z | 50.9m | 9 | 70 | 215 | 11,203,050 |
| ac65ebbb632134e3 | codex | eunomia-bpf | 2026-03-08T06:18:12.991Z | 50.5m | 6 | 42 | 166 | 6,661,192 |
| 86320826fd5d668a | codex | ActPlane | 2026-06-07T20:27:53.815Z | 50.2m | 41 | 94 | 166 | 10,847,133 |
| dfa330a474b2efc8 | codex | my-paper-work | 2026-07-10T22:30:31.013Z | 50.1m | 14 | 41 | 147 | 26,951,884 |
| 1583265032c11d60 | codex | bpf-benchmark | 2026-05-10T06:16:30.930Z | 49.8m | 2 | 48 | 453 | 55,485,819 |
| ff2864d18b14826f | codex | bpf-benchmark | 2026-05-06T21:06:01.077Z | 49.8m | 2 | 41 | 257 | 19,798,107 |
| c5ba865764bd5fa0 | codex | bpf-benchmark | 2026-03-18T18:46:45.313Z | 49.4m | 2 | 47 | 111 | 9,814,558 |
| 43cf347801d83a3d | codex | bpf-benchmark | 2026-03-23T12:47:44.786Z | 49.3m | 2 | 55 | 112 | 4,965,094 |
| d06746a799d9c048 | codex | bpf-benchmark | 2026-03-07T00:26:15.489Z | 48.9m | 10 | 61 | 274 | 15,938,438 |
| 505d0d3b83a961cc | codex | bpf-benchmark | 2026-03-12T04:27:13.931Z | 48.8m | 4 | 45 | 209 | 22,476,344 |
| fe1a88f05584b66d | codex | bpf-benchmark | 2026-03-24T23:48:13.179Z | 48.2m | 2 | 20 | 154 | 239,205,277 |
| 46b4ef232374095e | codex | ebpf-verifier-agent | 2026-03-20T01:50:46.579Z | 48.0m | 2 | 86 | 188 | 18,026,425 |
| f0df857b170b9427 | codex | bpf-benchmark | 2026-03-24T23:48:12.885Z | 47.8m | 2 | 21 | 149 | 239,830,060 |
| 03d2621dafa48d4d | codex | ActPlane | 2026-06-09T07:54:04.086Z | 47.7m | 12 | 109 | 277 | 15,277,023 |
| f611dc2154f251ad | claude | bpf-benchmark | 2026-07-13T08:39:29.016Z | 47.4m | 20 | 177 | 104 | 12,416,728 |
| 0fab38210c1887db | codex | bpf-benchmark | 2026-03-12T23:01:07.035Z | 46.7m | 3 | 49 | 126 | 9,430,587 |
| b98b1f11cd8c91f5 | codex | bpf-benchmark | 2026-03-30T02:46:56.075Z | 46.7m | 2 | 33 | 341 | 30,292,101 |
| 84a8e52a2214de80 | codex | eunomia-bpf | 2026-03-08T21:28:48.354Z | 46.5m | 6 | 45 | 166 | 8,605,546 |
| 11579caa03772b70 | codex | bpf-benchmark | 2026-03-29T04:33:08.634Z | 46.3m | 2 | 63 | 150 | 6,521,725 |
| 0dc9a0756066d4ab | codex | bpf-benchmark | 2026-04-26T06:11:47.702Z | 46.2m | 2 | 98 | 151 | 18,911,611 |
| 9b258dfb36e3b624 | codex | gpu_ext | 2026-03-19T20:24:23.552Z | 46.1m | 2 | 90 | 132 | 10,729,865 |
| bdd6438ae01b034e | codex | bpf-benchmark | 2026-03-12T02:11:03.734Z | 45.9m | 3 | 49 | 115 | 5,583,903 |
| d522976a06a4670e | codex | bpf-benchmark | 2026-03-20T16:14:29.680Z | 45.7m | 2 | 90 | 215 | 16,097,302 |
| ea204b003ae6ce90 | codex | bpf-benchmark | 2026-05-01T15:25:12.488Z | 45.6m | 2 | 28 | 223 | 26,520,199 |
| 5eb66867a2f95999 | codex | bpf-benchmark | 2026-03-24T01:54:52.422Z | 45.0m | 2 | 34 | 166 | 12,256,236 |
| 42f4821fa7f45eed | codex | workspace | 2026-07-22T00:52:21.737Z | 44.6m | 2 | 18 | 156 | 17,357,522 |
| c9ec39e04ebb5606 | codex | bpf-benchmark | 2026-04-25T18:01:46.470Z | 43.7m | 2 | 55 | 121 | 8,505,694 |
| 45f8a892ae7c65d7 | codex | bpf-benchmark | 2026-03-11T22:35:27.287Z | 43.4m | 2 | 31 | 145 | 17,350,679 |
| d4448dcbeb4c6419 | codex | agentsight | 2026-06-02T07:18:55.654Z | 43.3m | 12 | 73 | 167 | 11,856,504 |
| 5adcf366f05b4f3f | codex | bpf-benchmark | 2026-03-23T12:11:58.634Z | 43.2m | 2 | 54 | 137 | 9,589,821 |
| 86a2550886bfd9eb | codex | bpf-benchmark | 2026-04-05T03:53:00.334Z | 43.0m | 2 | 62 | 302 | 742,212,989 |
| 48995186d0950c29 | codex | bpf-benchmark | 2026-03-28T20:41:56.276Z | 43.0m | 2 | 58 | 137 | 7,154,220 |
| 7faa9aaae86aa7c9 | codex | bpf-benchmark | 2026-05-11T06:44:45.760Z | 42.9m | 2 | 22 | 347 | 39,947,101 |
| 865755215a02bad9 | codex | bpf-benchmark | 2026-05-03T14:54:51.377Z | 42.9m | 2 | 29 | 198 | 10,571,723 |
| a5710dc2c06f5f2f | codex | agentsight | 2026-07-07T02:39:25.842Z | 42.7m | 5 | 131 | 248 | 18,034,734 |
| 408ee9feee78ef82 | codex | linux-framework | 2026-03-13T02:17:33.937Z | 42.7m | 2 | 24 | 167 | 12,537,378 |
| 33cdd3abdf1a8761 | codex | bpf-benchmark | 2026-03-11T19:45:38.490Z | 42.6m | 4 | 53 | 248 | 20,534,818 |
| 59423badb00c76ed | codex | bpf-benchmark | 2026-05-11T01:58:42.468Z | 42.3m | 2 | 27 | 310 | 37,056,355 |
| 7619adc3971c8783 | codex | bpf-benchmark | 2026-03-19T02:04:33.650Z | 42.2m | 2 | 60 | 206 | 18,898,715 |
| 11860d0d7cbac5fc | codex | bpf-benchmark | 2026-03-29T04:06:42.581Z | 42.0m | 2 | 30 | 102 | 11,664,157 |
| 5cdad53b605446b3 | codex | bpf-benchmark | 2026-03-25T23:05:09.325Z | 41.9m | 4 | 40 | 114 | 603,285,554 |
| 92d289f7ef71c734 | codex | linux | 2026-03-09T16:41:04.628Z | 41.7m | 6 | 37 | 260 | 15,882,010 |
| 97fd4e230f1763ac | codex | gpu_ext | 2026-03-08T00:16:12.922Z | 41.7m | 7 | 25 | 112 | 4,508,210 |
| 6755def137d71c54 | codex | bpf-benchmark | 2026-03-20T21:09:52.968Z | 41.6m | 2 | 35 | 175 | 12,811,105 |
| 9589d260bcb0744a | codex | bpf-benchmark | 2026-03-26T11:25:12.808Z | 41.4m | 2 | 43 | 114 | 5,600,282 |
| 1cafa2570a160b7a | codex | bpf-benchmark | 2026-05-20T00:53:39.888Z | 41.2m | 7 | 39 | 217 | 14,821,749 |
| 8b14e756f828e4af | codex | bpf-benchmark | 2026-03-11T16:02:18.304Z | 41.1m | 2 | 34 | 161 | 17,726,352 |
| e6b3638ec409395d | codex | bpf-benchmark | 2026-03-28T21:36:36.354Z | 40.9m | 2 | 50 | 135 | 8,393,511 |
| ec0722d0bb843adf | codex | paper | 2026-03-28T22:22:16.930Z | 40.9m | 2 | 49 | 157 | 12,078,171 |
| c352a7aeb13c750b | codex | bpf-benchmark | 2026-05-11T05:46:24.982Z | 40.5m | 2 | 18 | 331 | 37,515,989 |
| be326ecfe56e24d7 | codex | bpf-benchmark | 2026-03-06T23:38:10.259Z | 40.5m | 5 | 23 | 137 | 13,874,306 |
| b7c3eb0bcc1e0cb3 | codex | paper | 2026-03-12T22:59:49.063Z | 40.4m | 7 | 39 | 255 | 23,224,270 |
| 6ed84586f3d9b84a | codex | bpf-benchmark | 2026-04-27T20:33:28.439Z | 40.4m | 2 | 32 | 109 | 4,979,117 |
| 9a41490d59231b00 | codex | bpf-benchmark | 2026-03-28T14:21:07.566Z | 40.2m | 2 | 49 | 162 | 7,982,934 |
| 314d5e7415fd48a4 | codex | bpf-benchmark | 2026-03-27T15:36:22.214Z | 40.2m | 2 | 35 | 132 | 5,522,251 |
| f7f6b365a1959c57 | codex | workspace | 2026-03-07T03:40:30.794Z | 40.2m | 12 | 51 | 222 | 12,749,969 |
| 7cae2cbda62513cb | codex | bpf-benchmark | 2026-04-06T05:13:23.215Z | 40.2m | 2 | 48 | 179 | 1,011,832,679 |
| a284d7e72ee26152 | codex | bpfopt | 2026-05-12T20:25:27.083Z | 40.0m | 2 | 34 | 182 | 15,472,722 |
| 8b3407912db7488a | codex | bpf-benchmark | 2026-05-02T06:43:05.942Z | 40.0m | 2 | 23 | 188 | 25,716,893 |
| 24e2220364751364 | codex | bpf-benchmark | 2026-04-30T03:26:39.406Z | 39.9m | 2 | 53 | 418 | 36,500,826 |
| 3d031261851c1903 | codex | bpf-benchmark | 2026-03-12T02:44:21.152Z | 39.9m | 2 | 53 | 210 | 19,237,321 |
| e0991d81af92c458 | codex | bpf-benchmark | 2026-03-12T20:50:28.732Z | 39.8m | 2 | 68 | 123 | 8,714,819 |
| 732c229bff44e64b | codex | bpf-benchmark | 2026-03-23T10:31:28.007Z | 39.7m | 2 | 40 | 120 | 10,318,792 |
| 675c37ad4a43361a | codex | bpf-benchmark | 2026-04-26T07:38:14.262Z | 39.7m | 2 | 24 | 113 | 8,121,926 |
| 84507fc68317ecfd | codex | bpf-benchmark | 2026-03-30T00:19:26.181Z | 38.9m | 2 | 36 | 290 | 23,268,778 |
| f88887d9b0108294 | codex | bpf-benchmark | 2026-04-27T20:43:46.694Z | 38.8m | 2 | 55 | 131 | 6,492,524 |
| ed76bdbb366e3d9e | codex | bpf-benchmark | 2026-03-12T04:28:25.974Z | 38.7m | 1 | 36 | 208 | 26,591,412 |
| c6471070f71a4bef | codex | bpf-benchmark | 2026-06-11T00:39:03.370Z | 38.7m | 10 | 46 | 118 | 6,104,227 |
| e07e5995dbd0cd10 | codex | bpf-benchmark | 2026-03-26T23:53:29.030Z | 38.6m | 2 | 80 | 116 | 9,873,472 |
| cc3289d2aaf70163 | codex | bpf-benchmark | 2026-03-27T02:22:14.518Z | 38.5m | 2 | 40 | 183 | 13,510,489 |
| 3bdfa017dcccd447 | codex | nccl-eBPF | 2026-03-09T03:37:33.808Z | 38.3m | 4 | 46 | 219 | 16,529,393 |
| 689d2d03d2c089a9 | codex | bpf-benchmark | 2026-03-28T18:41:52.083Z | 38.1m | 2 | 46 | 268 | 22,211,502 |
| f67d9c21ea5e3100 | codex | bpf-benchmark | 2026-05-10T22:12:10.084Z | 38.0m | 2 | 21 | 226 | 24,722,722 |
| c04da2c8fed2ecc2 | codex | bpf-benchmark | 2026-05-08T19:42:23.806Z | 37.9m | 2 | 37 | 184 | 14,558,017 |
| 8c965058079aecd2 | codex | bpf-benchmark | 2026-03-30T02:46:44.213Z | 37.8m | 2 | 65 | 264 | 22,316,385 |
| 4a31b0251d11488e | codex | linux-framework | 2026-03-21T00:49:20.426Z | 37.7m | 2 | 89 | 167 | 16,526,733 |
| 31876ee0686c58ad | codex | bpf-benchmark | 2026-03-19T18:25:03.283Z | 37.6m | 2 | 26 | 156 | 16,055,961 |
| fe1a55f9a2d7f826 | codex | bpf-benchmark | 2026-03-12T04:28:25.784Z | 37.5m | 1 | 33 | 164 | 21,121,956 |
| 6f229cd4196bb159 | codex | workspace | 2026-03-08T23:21:50.866Z | 37.4m | 3 | 52 | 102 | 304,263,410 |
| 57129633f92a24c7 | codex | bpf-benchmark | 2026-03-11T13:31:38.254Z | 37.4m | 2 | 60 | 204 | 16,110,918 |
| 668b1bb977da9f82 | codex | bpf-benchmark | 2026-03-11T15:11:47.375Z | 37.1m | 5 | 30 | 176 | 15,449,747 |
| 2a0446a11c5729cf | codex | eunomia-bpf | 2026-03-07T02:57:24.293Z | 37.1m | 9 | 23 | 125 | 3,313,483 |
| e08361b002d548d1 | codex | workspace | 2026-03-09T03:39:39.274Z | 36.9m | 4 | 74 | 190 | 332,775,715 |
| c4575a03e6dca720 | codex | bpf-benchmark | 2026-03-27T03:14:34.424Z | 36.9m | 2 | 89 | 314 | 20,137,578 |
| 9bc6710384d8c20d | codex | ebpf-verifier-agent | 2026-06-15T11:13:51.280Z | 36.7m | 8 | 61 | 182 | 695,754,581 |
| d698a06166cd6e77 | codex | bpf-benchmark | 2026-03-21T03:47:57.823Z | 36.7m | 2 | 55 | 283 | 27,771,488 |
| 7a35139b24f76315 | codex | bpf-benchmark | 2026-03-25T04:18:24.002Z | 36.7m | 2 | 60 | 229 | 21,817,107 |
| bf99b2c41b735490 | codex | bpf-benchmark | 2026-03-29T16:20:58.629Z | 36.6m | 2 | 45 | 325 | 25,542,723 |
| 26bf2d60ebd5b1ae | codex | bpf-benchmark | 2026-03-31T03:01:33.957Z | 36.5m | 2 | 31 | 125 | 221,554,530 |
| e44586a0a03e7757 | codex | bpf-benchmark | 2026-03-13T04:34:17.308Z | 36.1m | 5 | 43 | 219 | 17,938,026 |
| 77b2812309ed924f | codex | bpftime-gpu-verifier | 2026-03-18T23:09:58.534Z | 36.1m | 2 | 75 | 360 | 23,613,072 |
| e705111819e311fa | codex | bpf-benchmark | 2026-04-18T00:13:23.327Z | 35.7m | 2 | 32 | 119 | 7,536,853 |
| 4efa53b0e1031757 | codex | bpf-benchmark | 2026-05-01T19:42:29.836Z | 35.7m | 2 | 35 | 206 | 18,553,102 |
| 5f33d05f5257698d | codex | bpf-benchmark | 2026-03-11T22:35:41.428Z | 35.6m | 2 | 45 | 143 | 10,173,085 |
| b0a3d3b521a64ad3 | codex | bpf-benchmark | 2026-03-29T23:35:37.548Z | 35.6m | 2 | 47 | 284 | 18,542,443 |
| 40cc8cc8726d9a04 | codex | bpf-benchmark | 2026-03-21T16:39:55.316Z | 35.6m | 2 | 12 | 154 | 11,429,001 |
| a1adb0515e67e141 | codex | bpf-benchmark | 2026-06-05T03:52:14.116Z | 35.2m | 2 | 77 | 125 | 7,477,288 |
| 0043042f8e43aad1 | codex | agentsight | 2026-07-17T01:31:20.618Z | 35.2m | 1 | 10 | 100 | 12,309,905 |
| 4438f620b6a9297d | claude | bpf-developer-tutorial | 2026-07-22T04:11:10.959Z | 35.2m | 10 | 133 | 118 | 5,242,618 |
| 074a614782ced008 | codex | bpf-benchmark | 2026-03-11T21:38:05.022Z | 35.1m | 3 | 43 | 240 | 18,359,799 |
| a9b5ca33a9756d3b | codex | linux-framework | 2026-03-20T20:06:57.763Z | 34.8m | 2 | 39 | 248 | 20,470,668 |
| 4e16c0b06eefe77c | codex | linux-framework | 2026-03-13T02:25:32.994Z | 34.8m | 1 | 10 | 120 | 13,291,658 |
| 2752c78fe288d0e7 | codex | bpf-benchmark | 2026-03-27T15:59:14.461Z | 34.7m | 1 | 37 | 149 | 102,181,604 |
| 49cb68f771e30c83 | codex | bpf-benchmark | 2026-03-31T01:42:26.975Z | 34.7m | 1 | 67 | 126 | 193,978,751 |
| 3c24605269971763 | codex | bpf-benchmark | 2026-05-11T23:05:29.977Z | 34.6m | 2 | 24 | 229 | 26,166,596 |
| 2a9f0ea793abab06 | codex | linux-framework | 2026-03-29T17:10:48.770Z | 34.6m | 2 | 33 | 203 | 17,117,075 |
| 556b888c7c127d2a | codex | bpf-benchmark | 2026-03-23T07:43:11.161Z | 34.5m | 2 | 18 | 163 | 15,027,843 |
| 1755c01b51e417b6 | codex | bpf-benchmark | 2026-05-06T05:10:12.155Z | 34.4m | 2 | 24 | 304 | 32,730,159 |
| 520a4012ea0189d2 | codex | linux-framework | 2026-03-20T03:16:44.758Z | 34.3m | 2 | 63 | 183 | 14,272,513 |
| 75504f3f75c63df2 | codex | bpf-benchmark | 2026-03-30T04:49:28.718Z | 34.1m | 2 | 26 | 247 | 23,050,490 |
| 7531a718186fe425 | codex | bpf-benchmark | 2026-03-29T05:29:17.196Z | 33.9m | 2 | 37 | 204 | 20,721,783 |
| 475b94b59aae0156 | codex | bpf-benchmark | 2026-03-30T03:43:49.267Z | 33.9m | 2 | 19 | 191 | 17,473,520 |
| 0ba4d25279a7fc40 | codex | bpf-benchmark | 2026-03-11T18:05:22.607Z | 33.9m | 3 | 28 | 195 | 17,952,131 |
| 904cc91aef1aff91 | codex | bpf-benchmark | 2026-04-24T03:04:55.164Z | 33.8m | 2 | 54 | 290 | 21,074,720 |
| 59dd6415e149e0bf | codex | bpf-benchmark | 2026-03-26T08:56:39.301Z | 33.8m | 2 | 17 | 139 | 7,470,993 |
| 0fed871b35eb4482 | codex | bpf-benchmark | 2026-03-27T03:34:48.298Z | 33.7m | 2 | 35 | 104 | 6,239,307 |
| fd3270f1f221e0dd | codex | bpf-benchmark | 2026-05-05T17:52:04.633Z | 33.7m | 2 | 45 | 159 | 12,434,737 |
| 9b4245825e557a4d | codex | bpf-benchmark | 2026-03-11T16:57:42.729Z | 33.5m | 2 | 63 | 144 | 8,918,925 |
| 504cd7401c8de41a | codex | bpf-benchmark | 2026-03-27T12:56:10.782Z | 33.3m | 2 | 28 | 164 | 15,131,438 |
| 348d3650e4223232 | codex | workspace | 2026-03-08T01:31:40.015Z | 33.2m | 1 | 17 | 130 | 258,989,062 |
| 106198c5fd2b0182 | codex | bpf-developer-tutorial | 2026-07-20T00:12:21.844Z | 32.9m | 5 | 22 | 182 | 23,521,060 |
| e7322dcb990bf429 | codex | bpf-benchmark | 2026-05-12T04:11:37.059Z | 32.9m | 2 | 60 | 216 | 24,428,813 |
| 77ff1037f588b6c8 | codex | bpf-benchmark | 2026-03-12T04:26:57.413Z | 32.8m | 3 | 50 | 118 | 7,409,630 |
| 7e8565b8843058d5 | codex | workspace | 2026-03-08T23:12:03.628Z | 32.7m | 3 | 52 | 138 | 306,902,778 |
| 88a40328376dd66b | codex | bpf-benchmark | 2026-05-11T00:09:02.545Z | 32.7m | 2 | 25 | 315 | 39,250,408 |
| 38faf62d2cbc8818 | codex | bpf-benchmark | 2026-04-24T07:16:48.080Z | 32.6m | 2 | 41 | 158 | 12,759,878 |
| b5636f81c13ee11c | codex | bpf-benchmark | 2026-03-26T05:05:01.625Z | 32.6m | 2 | 27 | 123 | 11,913,740 |
| 65a481b192d76d69 | codex | ebpf-verifier-agent | 2026-03-12T00:45:20.092Z | 32.6m | 3 | 53 | 109 | 11,411,501 |
| d0077e1751d58e41 | codex | bpf-benchmark | 2026-03-27T02:52:34.018Z | 32.5m | 2 | 41 | 137 | 8,355,056 |
| f5dc8fa137577595 | codex | linux-framework | 2026-03-13T02:23:05.725Z | 32.4m | 2 | 19 | 123 | 8,078,682 |
| 0a43c5424d4c947c | codex | linux-framework | 2026-03-20T20:03:18.849Z | 32.2m | 2 | 45 | 259 | 21,201,503 |
| 27956412ba7f882d | codex | bpf-benchmark | 2026-03-26T00:36:54.782Z | 32.1m | 1 | 49 | 201 | 666,584,301 |
| 233da60709b44cf9 | codex | bpf-benchmark | 2026-03-29T21:56:37.000Z | 32.0m | 2 | 47 | 206 | 16,811,884 |
| e82e710c226e72b1 | codex | ebpf-verifier-agent | 2026-03-11T18:59:19.919Z | 32.0m | 3 | 33 | 156 | 10,531,147 |
| 390aa6d8a5d002aa | codex | bpf-benchmark | 2026-04-30T04:49:54.569Z | 31.9m | 2 | 29 | 374 | 34,090,519 |
| d5d1c9edb09b0ac9 | codex | ebpf-verifier-agent | 2026-03-20T02:50:51.707Z | 31.8m | 2 | 34 | 201 | 14,869,682 |
| 75815a4d8e5bc15f | codex | nccl-eBPF | 2026-03-09T18:38:57.022Z | 31.8m | 3 | 37 | 205 | 16,625,656 |
| e0bf5f53f38c28fe | codex | bpf-benchmark | 2026-03-27T16:23:02.379Z | 31.6m | 1 | 31 | 202 | 118,571,142 |
| e54be12e405144ef | codex | bpf-benchmark | 2026-03-21T07:08:27.416Z | 31.5m | 2 | 16 | 199 | 13,820,993 |
| cae0865149bce366 | codex | bpf-benchmark | 2026-05-11T08:53:19.562Z | 31.4m | 2 | 17 | 156 | 11,835,015 |
| e70c0e3d50dc8263 | codex | bpf-benchmark | 2026-05-11T04:32:04.767Z | 31.3m | 2 | 17 | 201 | 26,107,414 |
| 46dc6f245d540c49 | codex | bpf-benchmark | 2026-03-27T01:52:24.823Z | 31.2m | 2 | 25 | 135 | 8,753,205 |
| 1ca9ae3b04cf28a4 | codex | paper | 2026-03-12T23:00:20.722Z | 31.1m | 1 | 21 | 224 | 26,219,427 |
| 241d6568df17fa2f | codex | bpf-benchmark | 2026-03-12T23:00:43.404Z | 31.1m | 3 | 43 | 120 | 12,731,993 |
| d2bb2614f7985329 | codex | bpf-benchmark | 2026-05-01T20:50:43.066Z | 31.1m | 2 | 34 | 249 | 20,323,797 |
| 81be4a4f7907883a | codex | bpf-benchmark | 2026-03-27T16:23:02.601Z | 31.1m | 1 | 37 | 245 | 120,441,301 |
| 2b3725e5bc529950 | codex | bpf-benchmark | 2026-03-19T15:06:42.471Z | 31.1m | 2 | 43 | 130 | 8,878,215 |
| 4da5fdebf0d918cf | codex | bpf-benchmark | 2026-04-29T03:32:02.145Z | 31.0m | 2 | 35 | 187 | 14,343,545 |
| af376a9669a0130f | codex | bpf-benchmark | 2026-05-13T02:37:13.189Z | 30.9m | 4 | 20 | 220 | 6,880,101 |
| ef436c402f41be41 | codex | bpf-benchmark | 2026-03-27T01:56:20.236Z | 30.9m | 2 | 31 | 154 | 11,293,448 |
| 8ee8d8a9ae57fd2a | codex | bpf-benchmark | 2026-05-05T14:47:40.064Z | 30.8m | 2 | 26 | 200 | 22,464,655 |
| 1187c89a6a2ac4e2 | codex | bpf-benchmark | 2026-05-05T14:47:34.797Z | 30.7m | 2 | 27 | 214 | 18,551,021 |
| fec77b1b2d395ea2 | codex | bpf-benchmark | 2026-03-11T21:59:18.604Z | 30.6m | 3 | 43 | 218 | 15,945,748 |
| 4fb12ee250a6c23f | codex | bpf-benchmark | 2026-03-26T23:05:33.205Z | 30.6m | 2 | 75 | 193 | 15,352,560 |
| 4b204c62f9789d28 | codex | workspace | 2026-03-08T01:01:57.766Z | 30.6m | 1 | 38 | 144 | 243,993,926 |
| 24c74fa6478d3775 | codex | bpf-benchmark | 2026-03-30T02:46:19.595Z | 30.4m | 2 | 26 | 102 | 9,101,891 |
| 273767d587a72e0a | codex | bpf-benchmark | 2026-05-06T18:35:22.934Z | 30.3m | 2 | 28 | 240 | 23,284,072 |
| eec9208985a30182 | codex | bpf-benchmark | 2026-03-29T21:14:51.390Z | 30.3m | 2 | 25 | 125 | 8,157,377 |
| 1c1c123be07a4c60 | codex | linux-framework | 2026-03-21T01:03:56.770Z | 30.3m | 2 | 45 | 236 | 18,525,056 |
| 7ab38ce00e22ced7 | codex | linux | 2026-03-09T03:34:32.077Z | 30.1m | 5 | 35 | 160 | 12,413,824 |
| a3302332c2d69865 | codex | bpf-benchmark | 2026-04-28T17:53:57.906Z | 29.9m | 2 | 29 | 176 | 16,506,423 |
| 164e04685cd29531 | codex | bpf-benchmark | 2026-03-31T01:42:26.690Z | 29.7m | 1 | 56 | 122 | 192,852,447 |
| d5256375ef70f971 | claude | agentsight | 2026-06-02T02:38:39.832Z | 29.5m | 9 | 150 | 123 | 5,728,546 |
| 4f2e111231c8801a | codex | bpf-benchmark | 2026-03-27T13:00:32.727Z | 29.4m | 2 | 24 | 128 | 10,808,383 |
| b38c476def5ea268 | codex | bpf-benchmark | 2026-05-05T15:19:15.549Z | 29.3m | 2 | 21 | 102 | 7,544,391 |
| f8517c5c112b070d | codex | bpf-benchmark | 2026-03-27T17:09:15.738Z | 29.3m | 2 | 51 | 218 | 155,670,603 |
| 30989f6069e7404c | codex | bpf-benchmark | 2026-03-10T19:23:05.100Z | 29.3m | 2 | 31 | 152 | 16,542,545 |
| 73267689aa027e41 | codex | workspace | 2026-03-08T22:42:47.930Z | 29.3m | 2 | 53 | 155 | 302,639,827 |
| d19ea80bc4bfb586 | codex | bpf-benchmark | 2026-03-21T02:13:00.127Z | 29.3m | 2 | 40 | 120 | 9,745,639 |
| 86d0a5ef1bc7f323 | codex | bpftime | 2026-03-08T06:17:34.350Z | 29.2m | 1 | 38 | 241 | 19,600,586 |
| bc1393ccde9f075a | codex | bpf-benchmark | 2026-05-06T02:26:09.414Z | 29.2m | 2 | 19 | 270 | 27,235,328 |
| 5fa3fb4a4e1c77a3 | codex | bpf-benchmark | 2026-05-01T07:28:14.839Z | 29.2m | 2 | 26 | 251 | 16,624,338 |
| dd564722211e9782 | codex | bpf-benchmark | 2026-03-23T11:41:23.170Z | 29.2m | 2 | 33 | 101 | 4,985,845 |
| b698c06c27ffd675 | codex | linux-framework | 2026-03-13T03:02:14.699Z | 29.1m | 5 | 17 | 144 | 16,051,501 |
| 64989976b8e865e4 | codex | bpf-benchmark | 2026-03-29T16:27:44.659Z | 29.1m | 2 | 56 | 206 | 16,934,253 |
| bbd56743a04a89a5 | codex | bpf-benchmark | 2026-03-27T17:09:15.482Z | 29.0m | 1 | 23 | 209 | 156,862,070 |
| c6fc6a4d43ee32fb | codex | bpf-benchmark | 2026-03-29T20:18:34.554Z | 29.0m | 2 | 50 | 180 | 15,939,784 |
| 9efc3f0f3807136e | codex | bpf-benchmark | 2026-03-29T23:59:45.161Z | 28.9m | 2 | 52 | 180 | 13,800,365 |
| b808f1142909c4e4 | codex | bpf-benchmark | 2026-03-11T21:30:47.664Z | 28.9m | 4 | 25 | 142 | 12,263,701 |
| 3ce0015d3a1418db | codex | bpf-benchmark | 2026-03-12T03:53:13.282Z | 28.8m | 4 | 28 | 168 | 12,359,342 |
| d5eaeee200b36be5 | codex | bpf-benchmark | 2026-04-30T20:15:15.916Z | 28.6m | 2 | 25 | 236 | 17,638,431 |
| fa6f5ecd67510d71 | codex | bpf-benchmark | 2026-03-23T12:50:44.383Z | 28.5m | 2 | 33 | 135 | 13,441,039 |
| fc91bf6a5743bd43 | codex | bpf-benchmark | 2026-05-10T19:44:06.029Z | 28.4m | 2 | 17 | 141 | 11,467,793 |
| e21af431199e3edd | codex | bpf-benchmark | 2026-03-28T21:02:29.717Z | 28.4m | 2 | 74 | 246 | 13,330,931 |
| c2a25b05684f3b0e | codex | bpf-benchmark | 2026-05-07T03:33:50.949Z | 28.4m | 2 | 17 | 180 | 13,756,905 |
| a7abdc68cfcf3f3e | codex | bpf-benchmark | 2026-05-05T15:45:52.309Z | 28.3m | 2 | 25 | 260 | 24,346,228 |
| d9e1336d51d91270 | codex | bpf-benchmark | 2026-03-29T02:18:45.562Z | 28.3m | 2 | 49 | 262 | 20,992,422 |
| 543eb09383cd0497 | codex | bpf-benchmark | 2026-03-27T12:47:10.502Z | 28.2m | 2 | 22 | 185 | 15,655,377 |
| 3ef60f680885def7 | codex | bpf-benchmark | 2026-04-23T08:10:08.597Z | 28.1m | 2 | 20 | 170 | 13,400,315 |
| 23e3ea5cc9578966 | codex | bpf-benchmark | 2026-03-30T00:30:27.878Z | 28.0m | 2 | 55 | 159 | 11,938,038 |
| 663d7b6d5ff172f8 | codex | bpf-benchmark | 2026-04-25T23:23:34.288Z | 28.0m | 2 | 21 | 131 | 9,901,499 |
| b1ae4a43abcb0d3a | codex | bpf-benchmark | 2026-03-20T05:08:09.460Z | 28.0m | 2 | 58 | 179 | 21,157,619 |
| 12026f5eb9ca7dc0 | codex | bpf-benchmark | 2026-05-11T18:40:17.207Z | 27.9m | 2 | 17 | 254 | 31,363,102 |
| 9a11ab886f87f0a8 | codex | bpf-benchmark | 2026-05-01T09:38:26.067Z | 27.9m | 2 | 22 | 197 | 13,788,035 |
| c4958d3756a9dca1 | codex | bpftime-gpu-verifier | 2026-03-18T22:04:06.436Z | 27.8m | 2 | 55 | 168 | 13,060,915 |
| e6fa04690527f55b | codex | ActPlane | 2026-06-15T08:59:10.264Z | 27.8m | 4 | 47 | 210 | 7,969,337 |
| 4e918a9aa0ceba59 | codex | bpf-benchmark | 2026-03-11T13:55:11.987Z | 27.8m | 2 | 35 | 109 | 8,345,785 |
| ff629bb89cb860fe | codex | bpf-benchmark | 2026-03-18T20:23:06.127Z | 27.8m | 2 | 56 | 114 | 9,486,914 |
| 072939dd944f5b23 | codex | bpftime-gpu-verifier | 2026-03-18T19:31:28.905Z | 27.7m | 2 | 19 | 112 | 7,441,738 |
| 405cc8a0eacef522 | codex | bpf-benchmark | 2026-04-29T05:29:46.452Z | 27.7m | 2 | 34 | 122 | 7,764,193 |
| cb5f30061904f8ef | codex | bpf-benchmark | 2026-05-07T03:23:11.121Z | 27.7m | 2 | 31 | 200 | 12,050,838 |
| c8a5f3466072736e | codex | bpf-benchmark | 2026-04-30T17:01:52.647Z | 27.6m | 2 | 20 | 170 | 21,304,322 |
| dc6877dfc66c58fa | codex | bpf-benchmark | 2026-03-10T20:07:01.424Z | 27.5m | 4 | 35 | 157 | 7,798,792 |
| d032f8fa7308bc9c | codex | bpf-benchmark | 2026-03-27T18:14:46.876Z | 27.5m | 1 | 29 | 153 | 189,832,202 |
| bea2e036439b0480 | codex | bpf-benchmark | 2026-03-11T18:38:00.945Z | 27.4m | 4 | 23 | 182 | 21,905,907 |
| 216ab41d60767e1e | codex | bpf-benchmark | 2026-03-27T18:14:47.168Z | 27.4m | 1 | 37 | 173 | 190,454,379 |
| 343ee8152b35ed4b | codex | bpf-benchmark | 2026-04-07T09:26:22.848Z | 27.3m | 5 | 33 | 131 | 1,201,787,421 |
| c8ce38869a079989 | codex | bpf-benchmark | 2026-03-29T22:39:55.831Z | 27.3m | 2 | 41 | 120 | 9,729,793 |
| 964cb4d6b791b75a | codex | linux-framework | 2026-03-13T03:03:42.998Z | 27.3m | 3 | 18 | 154 | 13,981,844 |
| 671d4dddad1e9150 | codex | bpf-benchmark | 2026-03-27T19:10:04.020Z | 27.2m | 3 | 49 | 145 | 197,387,919 |
| 9fda9c19639577f4 | codex | bpf-benchmark | 2026-05-11T00:44:24.129Z | 27.2m | 2 | 14 | 250 | 25,051,053 |
| 0ceecacdd99e9931 | codex | eunomia-bpf | 2026-03-08T06:11:27.063Z | 27.2m | 3 | 29 | 125 | 7,588,613 |
| 9cf603c3e436f776 | codex | workspace | 2026-03-08T22:53:29.317Z | 27.2m | 1 | 49 | 151 | 304,370,858 |
| d999c5f09113a68a | claude | kernel-script-paper | 2026-07-20T08:45:38.204Z | 27.2m | 15 | 155 | 109 | 10,935,101 |
| ee40ce81ad7ae92f | codex | bpftime | 2026-03-08T06:57:17.483Z | 27.2m | 3 | 26 | 109 | 16,686,170 |
| c381aa1ec0b25856 | codex | bpf-benchmark | 2026-04-06T05:32:06.807Z | 27.2m | 2 | 32 | 165 | 1,021,431,986 |
| f80a8d962f93a0df | codex | bpf-benchmark | 2026-05-09T06:28:56.944Z | 27.1m | 2 | 19 | 220 | 19,572,972 |
| 5368983983c0cbbb | codex | bpf-benchmark | 2026-04-07T09:26:24.190Z | 27.1m | 4 | 28 | 120 | 1,205,765,725 |
| 787cc5bf8eabec3f | codex | agentsight | 2026-07-22T09:30:11.758Z | 26.8m | 1 | 5 | 107 | 1,454,391,855 |
| f7d6a520b3471085 | codex | bpf-benchmark | 2026-03-29T22:09:20.037Z | 26.8m | 2 | 40 | 144 | 13,926,383 |
| 57a6899637622450 | codex | bpf-benchmark | 2026-04-24T02:33:58.621Z | 26.8m | 2 | 35 | 228 | 19,947,604 |
| 9c76fbcc6b6eef17 | codex | bpf-benchmark | 2026-05-07T03:22:47.547Z | 26.7m | 2 | 20 | 222 | 22,282,821 |
| bc759706e726540f | codex | bpftime | 2026-03-08T06:51:39.565Z | 26.6m | 1 | 50 | 112 | 25,956,216 |
| bf9c5fad70e08d74 | codex | bpf-benchmark | 2026-04-29T10:34:13.736Z | 26.6m | 2 | 14 | 157 | 14,041,383 |
| 35daa8e83ead50c4 | codex | datrail | 2026-04-28T01:07:01.254Z | 26.6m | 7 | 36 | 152 | 8,763,592 |
| 11e409cb23d7530c | codex | workspace | 2026-03-09T03:39:39.568Z | 26.6m | 3 | 31 | 148 | 324,220,154 |
| 0778bef1ec844790 | codex | bpfopt | 2026-05-12T19:06:52.866Z | 26.5m | 2 | 10 | 182 | 6,954,684 |
| 2608a0bee3cc75ea | codex | bpf-benchmark | 2026-03-24T01:51:52.936Z | 26.5m | 2 | 26 | 104 | 9,220,170 |
| daeb514cf6b09b56 | codex | bpf-benchmark | 2026-05-11T20:02:50.753Z | 26.5m | 2 | 12 | 164 | 19,642,981 |
| 314d29b889958bda | codex | bpf-benchmark | 2026-04-24T00:02:59.954Z | 26.4m | 2 | 21 | 227 | 11,920,042 |
| 14cc95f3c3d7c27c | codex | bpf-benchmark | 2026-03-29T22:52:18.458Z | 26.4m | 2 | 32 | 269 | 16,588,693 |
| 71cd5921836ccf97 | codex | bpf-benchmark | 2026-03-29T23:25:12.480Z | 26.3m | 2 | 19 | 139 | 13,601,010 |
| df85de134c1f9eaa | codex | bpf-benchmark | 2026-03-23T07:04:11.556Z | 26.3m | 2 | 20 | 136 | 11,771,337 |
| 98cb44676093e85b | codex | llvmbpf | 2026-03-12T03:11:31.740Z | 26.3m | 3 | 28 | 104 | 10,198,976 |
| 3ac120a938520e5a | codex | bpf-benchmark | 2026-03-19T00:02:53.496Z | 26.3m | 2 | 37 | 109 | 6,926,053 |
| 4b0ae52e096b6aba | codex | bpf-benchmark | 2026-03-29T15:12:45.176Z | 26.2m | 2 | 20 | 137 | 11,403,743 |
| 0bcbefb8c7c47b1c | codex | bpf-benchmark | 2026-05-11T18:41:07.420Z | 26.2m | 2 | 20 | 222 | 22,425,270 |
| a24f5eeb1d23c24d | codex | bpf-benchmark | 2026-03-28T20:01:28.916Z | 26.2m | 2 | 29 | 224 | 15,498,035 |
| 8595dd29dfbd3318 | codex | bpf-benchmark | 2026-03-11T03:10:12.785Z | 26.0m | 1 | 16 | 127 | 5,882,742 |
| ca439988ceac2113 | codex | bpf-benchmark | 2026-03-30T01:00:48.110Z | 25.9m | 2 | 67 | 221 | 16,017,530 |
| 39cfba4bc79b5037 | codex | bpf-benchmark | 2026-05-11T09:39:33.540Z | 25.9m | 2 | 11 | 222 | 27,625,444 |
| b2410f5419866800 | codex | ebpf-verifier-agent | 2026-03-11T15:32:15.367Z | 25.6m | 2 | 13 | 104 | 5,389,019 |
| 68aee85f7c1e0fd4 | codex | bpf-benchmark | 2026-03-27T16:23:02.191Z | 25.6m | 1 | 28 | 172 | 113,973,771 |
| f428b4e6c5cbbf74 | codex | bpf-benchmark | 2026-05-10T05:01:20.645Z | 25.5m | 2 | 24 | 220 | 29,686,627 |
| d89bf9b97fc884d9 | codex | bpf-benchmark | 2026-03-26T23:32:12.228Z | 25.4m | 2 | 50 | 158 | 7,834,724 |
| bd2524b2fb0e23b8 | codex | bpf-benchmark | 2026-04-30T04:11:22.506Z | 25.4m | 2 | 39 | 290 | 27,347,703 |
| ed6af0bdcb5a79c0 | codex | bpf-benchmark | 2026-05-01T00:36:02.247Z | 25.3m | 2 | 21 | 113 | 11,201,426 |
| 548056401dd3455e | codex | bpf-benchmark | 2026-05-05T15:30:18.023Z | 25.2m | 2 | 19 | 184 | 15,870,229 |
| 83f20e41a84bf749 | codex | bpf-benchmark | 2026-03-09T02:05:49.423Z | 25.2m | 2 | 48 | 112 | 6,032,480 |
| 3db96e0584d23010 | codex | agentsight | 2026-07-15T11:15:49.518Z | 25.1m | 6 | 38 | 108 | 3,970,565 |
| 9d0fb57df5978e75 | codex | bpf-benchmark | 2026-03-12T22:33:20.564Z | 24.8m | 4 | 23 | 141 | 13,472,730 |
| 86052d22eea57f6d | codex | bpf-benchmark | 2026-03-27T01:18:25.542Z | 24.8m | 2 | 28 | 122 | 10,397,383 |
| fe8d45a7a87925e6 | claude | ephemeral | 2026-07-17T08:43:57.844Z | 24.7m | 1 | 223 | 103 | 12,984,341 |
| 4d73e583199d02e9 | codex | bpf-benchmark | 2026-03-12T20:50:38.150Z | 24.7m | 2 | 25 | 115 | 4,685,868 |
| eab159bb8b73d2c8 | codex | bpf-benchmark | 2026-03-08T22:29:33.959Z | 24.7m | 4 | 18 | 124 | 8,017,729 |
| c715b9d83022d352 | codex | bpf-benchmark | 2026-03-13T04:32:43.129Z | 24.7m | 5 | 28 | 170 | 13,535,412 |
| 13133e989953dabb | codex | ebpf-verifier-agent | 2026-03-20T00:16:36.216Z | 24.7m | 2 | 44 | 143 | 15,446,410 |
| e226695da91c0904 | codex | eunomia.dev | 2026-07-12T09:39:00.633Z | 24.7m | 4 | 21 | 126 | 12,572,482 |
| 1d4027d6a16773c3 | codex | bpf-benchmark | 2026-05-11T18:40:29.900Z | 24.7m | 2 | 18 | 183 | 19,929,688 |
| 830e9bc362edca41 | codex | bpftime-gpu-verifier | 2026-03-19T02:10:23.042Z | 24.6m | 2 | 25 | 168 | 16,568,033 |
| f40fe1c023c48828 | codex | bpf-benchmark | 2026-03-13T04:33:03.025Z | 24.6m | 3 | 30 | 152 | 16,874,937 |
| 927ba5f912fb7412 | codex | bpf-benchmark | 2026-05-11T02:51:35.245Z | 24.6m | 2 | 14 | 217 | 31,139,049 |
| 422d83cc92c9b3ee | codex | bpftime | 2026-03-07T08:38:39.893Z | 24.4m | 6 | 32 | 165 | 11,582,292 |
| 6cfd173e60be996d | codex | bpf-benchmark | 2026-05-08T01:47:38.472Z | 24.4m | 9 | 30 | 165 | 5,916,954 |
| d299a5bb45a8e700 | codex | ebpf-verifier-agent | 2026-06-15T18:48:25.981Z | 24.3m | 7 | 36 | 114 | 4,535,559 |
| 9de0354666917ac2 | codex | bpf-benchmark | 2026-03-27T01:24:11.844Z | 24.2m | 2 | 32 | 117 | 4,940,122 |
| a7353f48028a1924 | codex | bpf-benchmark | 2026-05-01T16:20:05.216Z | 24.2m | 2 | 27 | 176 | 11,429,894 |
| e19e6d2b5ae23f40 | codex | bpf-benchmark | 2026-03-24T18:44:27.381Z | 24.2m | 2 | 31 | 145 | 8,501,685 |
| 98fd5c0962fdf797 | codex | bpf-benchmark | 2026-05-05T14:47:34.380Z | 24.1m | 2 | 24 | 184 | 13,446,840 |
| bf3f4374e1396e80 | codex | bpf-benchmark | 2026-03-21T03:00:27.277Z | 24.1m | 2 | 51 | 162 | 12,949,675 |
| b427a29e8b88cafe | codex | linux-framework | 2026-03-21T01:28:21.724Z | 24.0m | 2 | 29 | 143 | 8,464,437 |
| d9345791f58584ed | codex | bpf-benchmark | 2026-03-29T20:06:38.640Z | 24.0m | 2 | 21 | 199 | 15,611,375 |
| 761b97ef3791bd13 | codex | bpf-benchmark | 2026-03-27T16:42:59.843Z | 24.0m | 1 | 37 | 208 | 127,474,016 |
| e1898ad1757e2ef7 | codex | bpf-benchmark | 2026-05-01T16:58:19.996Z | 23.9m | 2 | 18 | 132 | 11,398,806 |
| 05a9af4512ca38c9 | codex | bpf-benchmark | 2026-03-26T05:05:01.625Z | 23.9m | 2 | 25 | 115 | 6,273,008 |
| 525a208c5bb2deeb | codex | gpu_ext | 2026-03-06T04:07:07.345Z | 23.8m | 5 | 34 | 130 | 6,502,774 |
| 5cb2dc5ce8ddddb2 | codex | bpf-benchmark | 2026-03-30T13:02:16.705Z | 23.8m | 2 | 24 | 110 | 8,828,338 |
| 01b2076084e0cb0a | codex | bpf-benchmark | 2026-03-12T22:34:10.054Z | 23.8m | 1 | 16 | 135 | 15,144,831 |
| ce38cc89ca6ea863 | codex | bpf-benchmark | 2026-03-12T00:44:59.448Z | 23.7m | 2 | 18 | 151 | 10,214,725 |
| eda6dd7035d398c1 | codex | bpf-benchmark | 2026-03-30T03:53:30.552Z | 23.7m | 2 | 27 | 117 | 8,608,109 |
| ddbbc1c6400a16fe | codex | bpf-benchmark | 2026-04-09T05:17:23.591Z | 23.7m | 2 | 26 | 130 | 1,952,391,051 |
| b04f2cefb4819e68 | codex | bpf-benchmark | 2026-03-30T01:16:07.889Z | 23.6m | 2 | 36 | 197 | 16,204,149 |
| b134849828414575 | codex | bpf-benchmark | 2026-04-30T17:30:18.150Z | 23.6m | 2 | 33 | 147 | 6,565,364 |
| be8e59847a9638a2 | codex | bpf-benchmark | 2026-05-09T20:18:44.715Z | 23.6m | 2 | 13 | 193 | 19,579,858 |
| c3f352a182232621 | codex | bpf-benchmark | 2026-03-11T18:05:57.512Z | 23.5m | 4 | 21 | 126 | 8,055,699 |
| 9fa48c3ad8bfda4c | codex | bpf-benchmark | 2026-03-21T07:46:22.543Z | 23.5m | 2 | 19 | 222 | 15,042,577 |
| 710d0a6ff2fe0250 | codex | bpf-benchmark | 2026-05-01T00:19:26.987Z | 23.4m | 2 | 29 | 236 | 21,148,976 |
| 603f8a9c6b88d8ea | codex | bpfopt | 2026-05-11T23:42:14.915Z | 23.4m | 2 | 12 | 137 | 14,763,726 |
| 0a9c3a65f594e539 | codex | bpf-benchmark | 2026-05-07T07:38:01.232Z | 23.4m | 2 | 16 | 176 | 17,087,753 |
| b1b5d6871a765ed2 | codex | bpf-benchmark | 2026-04-24T03:07:08.092Z | 23.4m | 2 | 59 | 252 | 13,897,149 |
| 40ca4fa258f53257 | codex | workspace | 2026-03-08T22:38:59.112Z | 23.3m | 2 | 51 | 168 | 300,821,334 |
| 98e6b49d43caa429 | codex | paper | 2026-03-11T01:06:38.502Z | 23.2m | 4 | 16 | 181 | 10,002,334 |
| 0aeebca454ad99fe | codex | paper | 2026-03-28T22:27:05.775Z | 23.2m | 5 | 31 | 104 | 5,049,138 |
| 0090f420c2306ae6 | codex | bpf-benchmark | 2026-03-12T00:54:54.857Z | 23.2m | 4 | 39 | 144 | 9,606,174 |
| a6edbb06a9bf8506 | codex | bpf-benchmark | 2026-05-01T01:57:36.932Z | 23.1m | 2 | 23 | 196 | 16,598,402 |
| 789d009123df4556 | codex | bpf-benchmark | 2026-03-21T06:59:35.438Z | 23.1m | 2 | 51 | 241 | 11,589,293 |
| df958f22f6db7395 | codex | bpf-benchmark | 2026-05-11T18:40:45.890Z | 23.1m | 2 | 9 | 172 | 16,462,172 |
| ce20a85024a6b2c3 | codex | bpf-benchmark | 2026-05-19T04:10:51.916Z | 23.0m | 7 | 30 | 151 | 7,148,301 |
| 7ec46b759597c4a3 | codex | bpf-benchmark | 2026-03-10T21:27:08.131Z | 23.0m | 4 | 24 | 136 | 11,340,507 |
| 1c3dfc1a81f0bb43 | codex | bpf-benchmark | 2026-03-27T01:00:51.231Z | 22.9m | 2 | 38 | 167 | 9,835,051 |
| 8e95fac158384529 | codex | bpf-benchmark | 2026-03-13T03:43:00.271Z | 22.9m | 4 | 22 | 101 | 9,781,855 |
| 23a93e9f7b3d38ac | codex | bpf-benchmark | 2026-03-11T15:11:26.290Z | 22.8m | 2 | 22 | 116 | 8,517,697 |
| 15394d2d35aabe69 | codex | bpf-benchmark | 2026-03-08T07:04:10.693Z | 22.8m | 3 | 23 | 171 | 10,632,851 |
| e0f1a85ca1cd51f4 | codex | bpf-benchmark | 2026-04-04T07:02:04.666Z | 22.7m | 4 | 36 | 191 | 270,071,995 |
| 462bcbfd71e71a99 | codex | workspace | 2026-03-07T05:14:29.870Z | 22.7m | 1 | 27 | 183 | 119,006,505 |
| cfb2ef317f6ba1f8 | codex | bpf-benchmark | 2026-03-30T04:18:49.150Z | 22.6m | 2 | 43 | 158 | 13,957,229 |
| 795399b266632be8 | codex | bpf-benchmark | 2026-05-06T07:12:49.722Z | 22.6m | 2 | 9 | 129 | 8,181,300 |
| 7c5a3b3e77260eee | codex | ebpf-verifier-agent | 2026-03-20T02:16:12.852Z | 22.6m | 2 | 21 | 113 | 9,061,673 |
| 7fc0adac3d89e469 | codex | linux-framework | 2026-03-11T19:07:04.007Z | 22.6m | 2 | 24 | 105 | 11,540,335 |
| a9fe7585541256e4 | codex | bpf-benchmark | 2026-03-20T05:02:59.905Z | 22.6m | 2 | 29 | 134 | 17,201,005 |
| caef570a5bd6601e | codex | bpf-benchmark | 2026-03-28T14:38:17.792Z | 22.5m | 2 | 33 | 139 | 9,999,333 |
| b462097d075934ed | codex | bpf-benchmark | 2026-03-25T01:49:53.869Z | 22.5m | 1 | 55 | 120 | 314,048,821 |
| 579dad83726069c0 | codex | bpf-benchmark | 2026-04-04T15:37:16.232Z | 22.5m | 1 | 24 | 133 | 448,548,703 |
| fa39f769d65409ce | codex | bpf-benchmark | 2026-05-10T23:24:27.773Z | 22.4m | 2 | 11 | 122 | 8,023,471 |
| b6ee640b55f71833 | codex | ebpf-verifier-agent | 2026-03-20T00:16:16.714Z | 22.4m | 2 | 38 | 143 | 14,014,441 |
| f202a744e1f118d5 | codex | bpf-benchmark | 2026-04-30T19:01:58.472Z | 22.4m | 2 | 23 | 149 | 13,827,099 |
| 9c8009ca7190ddcc | codex | bpf-benchmark | 2026-03-20T02:03:52.346Z | 22.4m | 2 | 59 | 163 | 9,036,534 |
| 7aaa87e0df76bb06 | codex | nccl-eBPF | 2026-03-10T22:01:09.298Z | 22.3m | 3 | 32 | 144 | 8,843,706 |
| 9dbcc377b6ac5462 | codex | ebpf-verifier-agent | 2026-03-11T19:09:00.899Z | 22.3m | 1 | 22 | 109 | 10,529,849 |
| 5bdcc8cbeec07a83 | codex | bpf-benchmark | 2026-03-31T02:20:46.507Z | 22.2m | 1 | 29 | 138 | 206,063,678 |
| f9833705d3dd90a5 | codex | bpf-benchmark | 2026-03-29T16:35:02.197Z | 22.2m | 2 | 19 | 201 | 15,412,604 |
| 110592f848b854e6 | codex | bpf-benchmark | 2026-04-23T02:51:41.811Z | 22.2m | 2 | 18 | 232 | 18,658,725 |
| 9ce70bcde9773f1d | codex | ebpf-verifier-agent | 2026-03-20T02:43:05.347Z | 22.2m | 2 | 30 | 109 | 7,161,941 |
| 2968440a926edfd8 | codex | bpf-benchmark | 2026-04-30T05:52:56.305Z | 22.1m | 2 | 24 | 283 | 22,961,556 |
| 8a837b81d44ebf97 | codex | bpf-benchmark | 2026-03-29T21:31:13.074Z | 22.1m | 2 | 20 | 176 | 13,213,577 |
| 59b43a217dbd2418 | codex | bpf-benchmark | 2026-03-24T17:08:49.985Z | 22.1m | 2 | 12 | 104 | 10,503,510 |
| 5f1c32c50229b235 | codex | workspace | 2026-03-07T23:36:07.808Z | 22.1m | 1 | 27 | 159 | 198,701,926 |
| 3bd0cb448f41d054 | codex | bpf-benchmark | 2026-05-01T21:30:49.511Z | 22.0m | 2 | 15 | 114 | 10,029,137 |
| 1810ffdd7a4462f2 | codex | bpftime-gpu-verifier | 2026-03-18T22:03:52.773Z | 21.9m | 2 | 21 | 126 | 13,403,202 |
| fbdb4fffee00dcb5 | codex | bpf-benchmark | 2026-03-20T21:52:47.600Z | 21.9m | 2 | 29 | 143 | 17,955,740 |
| d3088f8fa942954d | codex | bpf-benchmark | 2026-03-12T20:02:26.339Z | 21.9m | 4 | 21 | 142 | 11,206,572 |
| f9aa6fd2b5e249ba | codex | bpf-benchmark | 2026-04-23T07:47:16.195Z | 21.9m | 2 | 32 | 163 | 10,213,055 |
| c565bb448264ab3c | codex | bpftime-worktree-552 | 2026-03-18T19:40:48.911Z | 21.8m | 2 | 25 | 128 | 10,468,662 |
| 3b4a8cb5bdbdfd92 | codex | ebpf-verifier-agent | 2026-03-11T19:09:00.875Z | 21.8m | 1 | 18 | 132 | 11,500,410 |
| 97580c77d8b3983e | codex | agentsight | 2026-07-05T21:39:06.658Z | 21.8m | 6 | 25 | 110 | 3,600,172 |
| 2836585cc97ebfba | codex | bpf-benchmark | 2026-04-24T00:00:38.564Z | 21.8m | 2 | 26 | 206 | 10,968,106 |
| 7168aef121206f43 | codex | bpf-benchmark | 2026-03-24T17:09:18.089Z | 21.7m | 2 | 21 | 114 | 7,637,256 |
| 6a4193ce437d3ec3 | codex | bpf-benchmark | 2026-04-17T02:58:15.296Z | 21.7m | 2 | 14 | 156 | 13,589,940 |
| 5b06d7a9f7161d81 | codex | bpf-benchmark | 2026-03-12T21:44:22.667Z | 21.7m | 3 | 30 | 148 | 13,377,227 |
| 359b9335d0904be8 | codex | bpf-benchmark | 2026-03-10T04:05:24.207Z | 21.7m | 2 | 54 | 147 | 13,184,407 |
| af98fe52d31f104e | codex | bpf-benchmark | 2026-03-27T00:24:02.445Z | 21.7m | 2 | 35 | 115 | 3,747,083 |
| 1e9ca007d6cad5b5 | codex | linux-framework | 2026-03-11T19:08:05.970Z | 21.6m | 3 | 22 | 130 | 11,300,873 |
| 6c0d2570abd0b959 | codex | bpf-benchmark | 2026-03-26T23:39:10.494Z | 21.6m | 6 | 28 | 102 | 5,447,642 |
| d5199cd81277a8cc | codex | workspace | 2026-06-22T20:32:22.873Z | 21.5m | 4 | 68 | 128 | 5,517,439 |
| b77be7cd3a8bd497 | codex | bpf-benchmark | 2026-03-27T17:15:41.724Z | 21.5m | 2 | 16 | 161 | 9,531,790 |
| 5cd4ec0b0d1e625c | codex | bpf-benchmark | 2026-05-05T12:28:33.373Z | 21.5m | 2 | 23 | 165 | 12,763,128 |
| f41b1a75613b4897 | codex | bpf-benchmark | 2026-03-12T21:44:41.559Z | 21.4m | 1 | 17 | 129 | 12,105,120 |
| 188a194eedd109df | codex | bpf-benchmark | 2026-03-24T17:08:43.095Z | 21.4m | 2 | 28 | 121 | 6,952,605 |
| 59cc18aeedca4f03 | codex | bpf-benchmark | 2026-03-12T21:29:42.107Z | 21.3m | 2 | 32 | 111 | 6,785,426 |
| 00c8abc61072d7b7 | codex | bpf-benchmark | 2026-04-24T00:21:10.310Z | 21.3m | 2 | 23 | 168 | 11,644,299 |
| 459f7657b45cc213 | codex | bpf-benchmark | 2026-04-23T20:46:12.316Z | 21.3m | 2 | 20 | 169 | 13,601,901 |
| 9311bf0528a31dc7 | codex | bpf-benchmark | 2026-05-07T06:29:46.685Z | 21.3m | 2 | 12 | 287 | 16,598,460 |
| 8fa43b9dfbdc895d | codex | bpf-benchmark | 2026-03-12T20:00:56.762Z | 21.3m | 4 | 17 | 159 | 7,613,482 |
| 6cfd7f5935248cc1 | codex | bpfopt | 2026-05-12T22:02:06.941Z | 21.3m | 2 | 14 | 115 | 10,309,218 |
| bc66ce6d57d819e8 | codex | bpf-benchmark | 2026-04-23T07:24:39.033Z | 21.3m | 2 | 22 | 151 | 8,971,934 |
| 23cbb87a9a1c6f16 | codex | bpf-benchmark | 2026-03-30T04:00:31.512Z | 21.3m | 2 | 36 | 162 | 16,944,911 |
| 173b5418e7b25e78 | codex | bpf-benchmark | 2026-03-21T16:40:49.600Z | 21.3m | 2 | 17 | 197 | 12,009,563 |
| b4badd90273089b0 | codex | bpf-benchmark | 2026-03-26T00:36:54.055Z | 21.2m | 1 | 28 | 124 | 654,841,962 |
| 51e40ae7300b1dbc | codex | bpf-benchmark | 2026-05-11T04:02:55.181Z | 21.2m | 2 | 15 | 190 | 26,191,874 |
| be16a34514672ac3 | codex | bpf-benchmark | 2026-05-06T01:46:15.416Z | 21.2m | 2 | 16 | 153 | 10,481,785 |
| b2e1d9f5608187ee | codex | ActPlane | 2026-06-14T19:15:32.378Z | 21.2m | 3 | 28 | 109 | 466,119,835 |
| a17cdada565c8393 | codex | bpf-benchmark | 2026-05-06T01:38:23.270Z | 21.1m | 2 | 30 | 121 | 11,533,700 |
| d1d1110f5a5f4ed7 | codex | ebpf-verifier-agent | 2026-03-19T17:20:07.802Z | 21.1m | 2 | 22 | 110 | 9,455,912 |
| 0b9e3185983cf17d | codex | bpf-benchmark | 2026-03-12T20:02:54.937Z | 21.0m | 3 | 34 | 142 | 9,247,652 |
| 089d330de9a4334f | codex | bpf-benchmark | 2026-03-20T05:13:22.472Z | 21.0m | 2 | 34 | 194 | 9,929,529 |
| c3008d6990a70455 | codex | bpf-benchmark | 2026-04-29T05:18:15.934Z | 21.0m | 2 | 17 | 124 | 7,353,802 |
| a3f2e7bd5ab692fb | codex | bpf-benchmark | 2026-03-25T00:02:38.873Z | 21.0m | 1 | 37 | 184 | 252,432,953 |
| 08d9c41bbff0aa98 | codex | paper | 2026-03-28T23:16:19.003Z | 21.0m | 2 | 18 | 176 | 9,760,570 |
| 9ed9de597e7e39eb | codex | bpf-benchmark | 2026-03-11T23:28:18.729Z | 21.0m | 4 | 13 | 149 | 13,964,492 |
| 4dcdb5b9e5a6db40 | codex | bpf-benchmark | 2026-03-26T23:34:39.964Z | 21.0m | 2 | 51 | 133 | 13,003,583 |
| 7fa6c0d9247c35cc | codex | bpf-benchmark | 2026-03-18T18:55:02.291Z | 21.0m | 2 | 24 | 124 | 5,618,850 |
| b7f17d8a40c69c59 | codex | agentsight | 2026-06-02T18:35:24.302Z | 20.9m | 8 | 43 | 103 | 5,173,846 |
| 64cf84b0b7637f92 | codex | bpf-benchmark | 2026-03-23T07:04:00.391Z | 20.8m | 2 | 19 | 160 | 6,555,908 |
| 8fc6dc58a7a7570b | codex | bpf-benchmark | 2026-03-10T20:35:17.687Z | 20.8m | 4 | 19 | 125 | 12,153,413 |
| 9b0c5b8b21be3ca2 | codex | bpf-benchmark | 2026-04-29T07:22:30.830Z | 20.8m | 2 | 20 | 152 | 14,217,559 |
| bcfec906437fb509 | codex | bpf-benchmark | 2026-03-24T17:09:04.133Z | 20.7m | 2 | 21 | 109 | 4,571,177 |
| 91a51ce0b7a49054 | codex | ebpf-verifier-agent | 2026-03-20T00:07:32.206Z | 20.7m | 2 | 22 | 132 | 10,938,794 |
| e6e96e206d85334e | codex | bpf-benchmark | 2026-03-25T18:55:36.877Z | 20.6m | 2 | 28 | 154 | 510,258,985 |
| 8b1343885590dc21 | codex | bpf-benchmark | 2026-03-07T22:46:25.769Z | 20.6m | 2 | 35 | 148 | 6,628,201 |
| f3a6519c606fe39f | codex | bpf-benchmark | 2026-03-28T20:25:02.551Z | 20.6m | 2 | 27 | 167 | 14,453,013 |
| 706c9091d7abed14 | codex | bpf-benchmark | 2026-05-05T17:08:50.982Z | 20.5m | 2 | 17 | 235 | 30,169,408 |
| ee83c85e4d49c7ef | codex | bpf-benchmark | 2026-03-20T16:12:35.967Z | 20.5m | 2 | 21 | 104 | 8,420,319 |
| 4326dc6ff11c03a0 | codex | bpf-benchmark | 2026-04-29T12:48:38.487Z | 20.5m | 2 | 13 | 157 | 19,683,870 |
| 0874238ddc900df3 | codex | bpf-benchmark | 2026-04-03T06:07:04.529Z | 20.5m | 1 | 31 | 112 | 133,840,750 |
| 6c7168d0998c3cc8 | codex | bpf-benchmark | 2026-04-17T02:58:16.366Z | 20.4m | 2 | 13 | 155 | 14,410,657 |
| 6d7e401c7549793b | codex | bpf-benchmark | 2026-03-12T02:44:37.645Z | 20.4m | 4 | 21 | 138 | 17,430,188 |
| b9340b44f0d19752 | codex | linux-framework | 2026-03-20T02:42:58.317Z | 20.3m | 2 | 13 | 103 | 7,040,661 |
| cf799e152c81da6d | codex | bpf-benchmark | 2026-03-21T07:29:41.021Z | 20.3m | 2 | 19 | 109 | 7,159,945 |
| 96b19b887bf03e64 | codex | bpf-benchmark | 2026-04-26T23:57:49.889Z | 20.3m | 2 | 42 | 129 | 10,769,893 |
| 5594c85a61beb888 | codex | nccl-eBPF | 2026-03-09T02:02:13.178Z | 20.2m | 4 | 22 | 147 | 9,331,344 |
| d31c7c4bad2d3866 | codex | paper | 2026-03-10T21:32:10.529Z | 20.1m | 2 | 28 | 131 | 5,294,548 |
| dbb9bbab5e20dd27 | codex | bpf-benchmark | 2026-03-29T20:02:36.893Z | 20.1m | 2 | 17 | 151 | 9,709,120 |
| 8429710701649f51 | codex | bpftime-gpu-verifier | 2026-03-18T18:36:46.340Z | 20.1m | 2 | 40 | 102 | 8,113,178 |
| 88176d1ce0b3f43e | codex | bpftime-worktree-542 | 2026-03-19T14:52:48.982Z | 20.0m | 2 | 27 | 141 | 9,947,566 |
| ad50677e8855e2e9 | codex | bpf-benchmark | 2026-04-23T22:05:56.713Z | 20.0m | 2 | 9 | 149 | 6,889,217 |
| 7ca5c5d71a72de3c | codex | bpf-benchmark | 2026-03-13T03:35:13.756Z | 20.0m | 4 | 20 | 153 | 10,550,870 |
| c8d412c8270e3c52 | codex | bpf-benchmark | 2026-03-08T07:04:32.975Z | 20.0m | 1 | 14 | 117 | 11,396,466 |
| a9cfd32fc3235d22 | codex | bpftime-worktree-542 | 2026-03-19T16:44:25.620Z | 19.9m | 3 | 28 | 136 | 10,358,190 |
| ff2a47a6af0549a2 | codex | workspace | 2026-06-02T06:56:10.139Z | 19.9m | 7 | 45 | 112 | 2,989,428 |
| c7148d35907d46d3 | codex | linux-framework | 2026-03-20T00:49:40.248Z | 19.9m | 2 | 22 | 106 | 8,581,948 |
| 3633b72b625b9990 | codex | bpf-benchmark | 2026-04-30T16:41:13.654Z | 19.9m | 20 | 50 | 143 | 7,835,467 |
| 9f06c4beec15134a | codex | ebpf-verifier-agent | 2026-03-19T18:43:41.170Z | 19.9m | 2 | 17 | 122 | 12,266,177 |
| 1eb2a518d7f5ee83 | codex | bpf-benchmark | 2026-03-10T20:58:41.172Z | 19.9m | 3 | 34 | 111 | 9,031,194 |
| 3977c2399f09f5db | codex | bpf-benchmark | 2026-03-11T22:52:54.041Z | 19.9m | 2 | 21 | 132 | 14,223,621 |
| b9f2e566abf0098d | codex | bpfopt | 2026-05-11T19:38:34.020Z | 19.8m | 2 | 9 | 173 | 14,952,456 |
| ea42c74a6aefdc01 | codex | bpf-benchmark | 2026-04-25T19:40:56.095Z | 19.8m | 2 | 48 | 165 | 8,646,077 |
| d44ee8dd127ecb6b | codex | bpf-benchmark | 2026-05-10T23:03:05.657Z | 19.8m | 2 | 27 | 193 | 21,906,016 |
| f486df5517237e36 | codex | bpf-benchmark | 2026-03-25T00:02:39.197Z | 19.8m | 1 | 32 | 167 | 256,321,854 |
| 7c9aede23723b9ec | codex | bpf-benchmark | 2026-03-20T15:52:44.785Z | 19.8m | 2 | 32 | 124 | 12,672,491 |
| b185b7591e0cef0f | codex | nccl-eBPF | 2026-03-10T22:01:38.387Z | 19.7m | 2 | 9 | 103 | 7,333,340 |
| 64b4e2db32c9488f | codex | bpf-benchmark | 2026-04-03T18:37:15.374Z | 19.7m | 2 | 34 | 192 | 8,038,729 |
| f29d97698782baa5 | codex | linux-framework | 2026-03-21T01:28:54.151Z | 19.7m | 2 | 30 | 123 | 9,160,913 |
| 580abd3cdba5d0e4 | codex | bpf-benchmark | 2026-04-07T17:05:27.875Z | 19.6m | 2 | 20 | 229 | 9,894,630 |
| 901a68e06a0db0fc | codex | bpf-benchmark | 2026-03-24T17:08:03.371Z | 19.6m | 2 | 18 | 160 | 7,233,926 |
| 040e25594f1bb59f | codex | bpf-benchmark | 2026-03-13T01:29:32.401Z | 19.6m | 2 | 24 | 108 | 7,549,164 |
| a3d56c1b4d9a0062 | codex | nccl-eBPF | 2026-03-09T02:02:36.220Z | 19.5m | 2 | 9 | 123 | 10,169,955 |
| 36d28865774ce38a | codex | bpf-benchmark | 2026-05-07T06:12:01.751Z | 19.5m | 2 | 5 | 195 | 8,541,683 |
| f9fd9cbd194a499a | codex | bpf-benchmark | 2026-03-28T20:01:40.821Z | 19.5m | 2 | 29 | 215 | 14,196,757 |
| 63aef17d85664b77 | codex | bpf-benchmark | 2026-03-29T01:22:07.874Z | 19.5m | 2 | 36 | 174 | 11,639,260 |
| 87d627cfc62319ea | codex | bpf-benchmark | 2026-03-10T21:27:22.969Z | 19.4m | 3 | 25 | 112 | 7,497,330 |
| 544986d765e884e4 | codex | bpf-benchmark | 2026-06-01T02:04:36.253Z | 19.3m | 4 | 31 | 193 | 8,131,943 |
| 98435f412ed5e18e | codex | bpf-benchmark | 2026-05-09T07:19:13.449Z | 19.3m | 2 | 20 | 195 | 14,006,272 |
| 8c2be6a582250cc6 | codex | agentsight | 2026-06-26T07:43:24.038Z | 19.3m | 5 | 68 | 135 | 9,402,290 |
| 3ba67b801f837b2a | codex | bpf-benchmark | 2026-03-27T17:08:41.801Z | 19.3m | 2 | 29 | 112 | 9,759,324 |
| b3d81aa374c10503 | codex | bpf-benchmark | 2026-05-03T01:13:20.663Z | 19.3m | 2 | 16 | 160 | 14,669,202 |
| 0598df4c706172fc | codex | linux-framework | 2026-03-21T16:46:08.565Z | 19.3m | 2 | 26 | 154 | 15,886,345 |
| 0bd988dbda1e7da0 | codex | bpf-benchmark | 2026-04-27T21:43:22.262Z | 19.2m | 2 | 27 | 118 | 7,463,303 |
| 9e8c942823d55df6 | codex | bpf-benchmark | 2026-03-21T11:26:18.480Z | 19.1m | 2 | 10 | 107 | 9,615,584 |
| ee7343078ba37488 | codex | bpftime-worktree-542 | 2026-03-19T15:30:09.190Z | 19.1m | 2 | 29 | 104 | 7,424,858 |
| 4f3f94eec88da52a | codex | ebpf-verifier-agent | 2026-06-14T21:12:45.005Z | 19.1m | 6 | 40 | 102 | 379,471,236 |
| 801c55d5319e60ca | codex | eunomia-bpf | 2026-03-08T12:08:10.508Z | 19.1m | 1 | 17 | 120 | 9,807,128 |
| 3d5d496b0b3d901c | codex | bpf-benchmark | 2026-03-27T01:30:39.080Z | 19.0m | 2 | 27 | 105 | 9,452,145 |
| 275c1b8e9e831a1d | codex | bpf-benchmark | 2026-03-12T02:19:56.384Z | 19.0m | 4 | 26 | 106 | 7,948,261 |
| d47690cc0b88f045 | codex | nccl-eBPF | 2026-03-09T16:18:38.674Z | 19.0m | 2 | 17 | 104 | 9,001,310 |
| aae57925eb8b7ab7 | codex | ebpf-verifier-agent | 2026-03-12T04:29:03.973Z | 19.0m | 2 | 21 | 124 | 9,339,649 |
| 533f85d1472d2cc8 | codex | bpf-benchmark | 2026-03-21T07:14:07.157Z | 18.9m | 2 | 28 | 140 | 8,561,773 |
| 6aa31c363ee3e986 | codex | bpf-benchmark | 2026-05-06T06:15:23.943Z | 18.8m | 2 | 11 | 209 | 9,379,234 |
| 143e3b7b570c7cd8 | codex | gpu_ext | 2026-03-27T02:21:32.549Z | 18.8m | 2 | 18 | 121 | 6,348,412 |
| ab6cf2d457012f95 | codex | bpf-benchmark | 2026-03-13T04:33:56.944Z | 18.8m | 2 | 34 | 102 | 4,727,435 |
| 3dfd9d82f6827056 | codex | bpf-benchmark | 2026-03-22T17:54:15.208Z | 18.7m | 2 | 32 | 207 | 7,627,480 |
| dd75065602ecc695 | codex | ebpf-verifier-agent | 2026-03-18T20:31:18.639Z | 18.7m | 2 | 19 | 172 | 9,636,495 |
| e28e9b287697a77b | codex | bpf-benchmark | 2026-03-12T22:36:48.987Z | 18.6m | 1 | 15 | 102 | 15,775,214 |
| d71b605a97541734 | codex | bpf-benchmark | 2026-04-29T21:30:34.515Z | 18.6m | 2 | 13 | 122 | 10,202,823 |
| 51437fe12d42c025 | codex | bpf-benchmark | 2026-03-10T21:27:49.343Z | 18.5m | 2 | 21 | 116 | 10,328,313 |
| 378bf6a2257c0072 | codex | bpf-benchmark | 2026-03-11T23:13:28.927Z | 18.5m | 3 | 18 | 109 | 7,303,767 |
| a40ab5f397283f51 | codex | bpf-benchmark | 2026-03-29T16:29:18.084Z | 18.5m | 2 | 33 | 111 | 10,619,555 |
| 34e295a99b50acf8 | codex | ActPlane | 2026-05-28T04:13:59.440Z | 18.5m | 4 | 30 | 160 | 14,258,389 |
| 72aba3392ab46915 | codex | bpf-benchmark | 2026-04-29T01:51:08.020Z | 18.5m | 2 | 11 | 159 | 15,953,020 |
| 0ca030491f9828b6 | codex | linux-framework | 2026-03-19T18:54:33.209Z | 18.4m | 2 | 21 | 141 | 9,361,036 |
| 796591f2731110bf | codex | paper | 2026-03-28T23:05:43.238Z | 18.4m | 2 | 39 | 157 | 11,700,660 |
| 7dfe9476e077c1bb | codex | bpf-benchmark | 2026-05-06T06:03:09.840Z | 18.4m | 2 | 11 | 164 | 17,415,602 |
| 7a4a842654601144 | codex | bpf-benchmark | 2026-03-28T21:03:43.792Z | 18.4m | 2 | 18 | 108 | 11,249,010 |
| 6c829a13bcc941a7 | codex | bpf-benchmark | 2026-03-28T20:40:39.461Z | 18.3m | 2 | 9 | 116 | 9,595,618 |
| f1ad5112fda7641a | codex | bpftime | 2026-03-09T03:18:58.644Z | 18.3m | 1 | 31 | 112 | 5,130,956 |
| 25236237fd00e40a | codex | linux-framework | 2026-03-29T17:42:31.669Z | 18.3m | 2 | 29 | 117 | 9,214,759 |
| a144735157a226d5 | codex | bpf-benchmark | 2026-03-28T21:58:09.000Z | 18.3m | 2 | 11 | 108 | 10,872,915 |
| ad91b04dcef292b3 | codex | bpf-benchmark | 2026-05-12T17:02:09.810Z | 18.3m | 2 | 13 | 125 | 4,481,058 |
| f76d297393dd4758 | codex | bpf-benchmark | 2026-03-12T00:56:37.642Z | 18.3m | 2 | 17 | 114 | 8,982,555 |
| 559315040b68ae48 | codex | linux | 2026-03-09T17:30:35.812Z | 18.3m | 3 | 33 | 122 | 9,220,777 |
| 2679d53eb13a765a | codex | bpf-benchmark | 2026-03-10T20:16:17.893Z | 18.3m | 3 | 17 | 175 | 14,198,102 |
| 5564338bf88af663 | codex | bpf-benchmark | 2026-03-29T21:33:10.005Z | 18.2m | 2 | 25 | 151 | 10,539,218 |
| 5b4c15d167c533fb | codex | ebpf-verifier-agent | 2026-03-18T21:56:55.429Z | 18.2m | 2 | 17 | 149 | 5,660,331 |
| 3453cd13ad1d55e0 | codex | bpf-benchmark | 2026-05-06T06:15:23.252Z | 18.0m | 2 | 10 | 119 | 7,677,160 |
| f546b72f3bd6a1c7 | codex | bpf-benchmark | 2026-04-22T01:33:53.428Z | 18.0m | 2 | 22 | 145 | 7,430,031 |
| c9f24e551dc73d20 | codex | bpfopt | 2026-05-12T00:49:47.762Z | 18.0m | 2 | 11 | 138 | 10,653,179 |
| aedef7e3cd3dd451 | codex | bpf-benchmark | 2026-03-13T01:29:14.372Z | 17.9m | 2 | 16 | 107 | 9,824,814 |
| f9ed087198b1987a | codex | paper | 2026-03-28T23:56:56.251Z | 17.9m | 2 | 17 | 118 | 8,778,731 |
| 2ee40f012baa1238 | codex | bpf-benchmark | 2026-03-20T23:09:22.877Z | 17.9m | 2 | 34 | 115 | 10,368,879 |
| 0418d92d8bfca228 | codex | bpf-benchmark | 2026-03-10T19:44:51.989Z | 17.9m | 3 | 20 | 104 | 8,443,668 |
| 6c670c574d1bccfa | codex | bpf-benchmark | 2026-03-12T04:07:35.775Z | 17.9m | 2 | 22 | 109 | 7,497,885 |
| 434d56f970dc2366 | codex | bpf-benchmark | 2026-03-20T20:47:19.567Z | 17.8m | 2 | 24 | 185 | 11,134,967 |
| 61db9c394ec290db | codex | bpf-benchmark | 2026-03-28T15:15:50.125Z | 17.8m | 2 | 15 | 132 | 11,959,337 |
| c547605ea2db0f3e | codex | ebpf-verifier-agent | 2026-03-11T20:41:56.579Z | 17.7m | 3 | 25 | 109 | 6,773,750 |
| 19367b22938a3281 | codex | bpf-benchmark | 2026-05-12T00:33:53.093Z | 17.6m | 2 | 12 | 121 | 12,719,736 |
| 15191d8777457312 | codex | bpf-benchmark | 2026-04-29T03:58:55.067Z | 17.6m | 2 | 17 | 157 | 16,261,880 |
| 141a90a558cea141 | codex | bpf-benchmark | 2026-05-01T01:59:43.769Z | 17.6m | 2 | 14 | 205 | 16,364,736 |
| 0467399dc0444226 | codex | workspace | 2026-07-03T01:33:51.839Z | 17.6m | 6 | 30 | 131 | 4,012,603 |
| 526a23ec35a93a2a | codex | bpf-benchmark | 2026-05-06T07:50:43.091Z | 17.5m | 2 | 13 | 121 | 14,424,181 |
| 3a46e2e5d4de6d0e | codex | bpf-benchmark | 2026-05-01T12:07:56.496Z | 17.5m | 2 | 19 | 195 | 12,165,853 |
| aade4750df034d5e | codex | bpf-benchmark | 2026-03-11T17:07:14.515Z | 17.5m | 5 | 13 | 101 | 6,235,913 |
| 249bf520c7074645 | codex | bpf-benchmark | 2026-03-12T23:21:27.477Z | 17.5m | 2 | 31 | 114 | 7,594,528 |
| 2a7fa9cc993b64c2 | codex | bpf-benchmark | 2026-03-12T23:20:01.719Z | 17.4m | 5 | 22 | 117 | 3,137,652 |
| 57ce5dc61971e223 | codex | bpfopt | 2026-05-11T23:41:57.035Z | 17.4m | 2 | 18 | 162 | 12,953,943 |
| 510ab3677caefd82 | codex | bpf-benchmark | 2026-04-23T03:36:28.093Z | 17.4m | 2 | 17 | 161 | 9,782,120 |
| 050e26568c27b245 | codex | bpf-benchmark | 2026-03-27T03:14:57.654Z | 17.4m | 2 | 45 | 211 | 9,131,153 |
| cb23f6dfb7dd9507 | codex | ebpf-verifier-agent | 2026-03-12T04:30:46.768Z | 17.3m | 2 | 20 | 101 | 6,817,773 |
| e9c8d9d6d31e2302 | codex | bpf-benchmark | 2026-04-29T04:59:06.339Z | 17.2m | 2 | 12 | 147 | 14,545,633 |
| 89fda31ab9d7685d | codex | bpf-benchmark | 2026-04-30T19:33:50.929Z | 17.2m | 2 | 17 | 139 | 15,050,182 |
| 04c0d9934bd816fe | codex | ebpf-verifier-agent | 2026-03-18T19:58:18.255Z | 17.2m | 2 | 25 | 116 | 7,579,035 |
| a7a9b0e08c195442 | codex | bpf-benchmark | 2026-03-11T18:27:16.241Z | 17.1m | 2 | 24 | 150 | 14,049,202 |
| 24a99ee8d3470fe2 | codex | paper | 2026-03-28T22:22:06.423Z | 17.1m | 2 | 31 | 109 | 11,823,711 |
| 36ef8fdc8590e45b | codex | bpf-benchmark | 2026-03-11T22:35:01.611Z | 17.0m | 4 | 17 | 101 | 5,483,225 |
| a13294061688cfa3 | codex | bpf-benchmark | 2026-04-28T03:56:20.987Z | 17.0m | 2 | 9 | 128 | 11,888,917 |
| 24e4e82c254606bd | codex | bpftime-worktree-542 | 2026-03-19T16:07:11.499Z | 17.0m | 2 | 28 | 132 | 9,752,185 |
| cc269fceba638765 | codex | bpf-benchmark | 2026-04-29T22:19:03.242Z | 17.0m | 2 | 18 | 110 | 8,237,421 |
| 6ce1441f017a3ebf | codex | bpf-benchmark | 2026-05-11T20:03:35.267Z | 17.0m | 2 | 14 | 131 | 7,094,033 |
| 418f416a95ba4f0e | codex | bpf-benchmark | 2026-05-01T04:30:28.116Z | 17.0m | 2 | 22 | 252 | 13,904,453 |
| cf996106babcf364 | codex | bpf-benchmark | 2026-05-06T06:01:49.464Z | 16.9m | 2 | 17 | 140 | 13,937,234 |
| e976b838b46a555c | codex | bpf-benchmark | 2026-03-30T03:41:33.713Z | 16.9m | 2 | 27 | 185 | 6,513,480 |
| 117e8cef8c2c7254 | codex | bpf-benchmark | 2026-03-30T00:00:21.821Z | 16.9m | 2 | 18 | 195 | 6,675,512 |
| f26c7d95a4e5c5f9 | codex | bpf-benchmark | 2026-04-26T23:58:03.835Z | 16.9m | 2 | 27 | 103 | 6,427,732 |
| 4cab26d5d652fff0 | codex | agentsight | 2026-07-04T00:59:50.364Z | 16.8m | 5 | 28 | 102 | 4,083,279 |
| 4409e874068964d7 | codex | linux-framework | 2026-03-21T17:11:14.548Z | 16.8m | 2 | 31 | 107 | 8,824,797 |
| d78890a1161b620d | codex | bpf-benchmark | 2026-03-25T11:29:52.273Z | 16.7m | 1 | 43 | 141 | 412,032,201 |
| 3ef98cbfc5252c67 | codex | bpf-benchmark | 2026-04-29T12:30:52.945Z | 16.7m | 2 | 9 | 224 | 7,618,641 |
| 40c154ddd2e9e7b7 | codex | linux-framework | 2026-03-29T18:07:45.348Z | 16.6m | 2 | 19 | 104 | 11,445,168 |
| 34431975f8c5f99b | codex | bpf-benchmark | 2026-03-25T12:05:26.998Z | 16.5m | 2 | 15 | 120 | 8,729,056 |
| a45b42fb8b48e20d | codex | bpf-benchmark | 2026-04-24T04:23:51.444Z | 16.5m | 2 | 11 | 134 | 9,953,818 |
| 3e39d8306241ab89 | codex | bpf-benchmark | 2026-03-10T21:48:35.773Z | 16.5m | 2 | 19 | 107 | 8,741,821 |
| 2d9c4e2883a384be | codex | bpf-benchmark | 2026-03-21T23:04:35.587Z | 16.5m | 2 | 13 | 159 | 10,403,786 |
| 94fc21eb7de6a738 | codex | bpf-benchmark | 2026-03-12T23:21:11.404Z | 16.5m | 2 | 36 | 107 | 5,361,032 |
| 29f7c92e5a6b6cd2 | codex | bpf-benchmark | 2026-05-05T08:58:16.670Z | 16.4m | 2 | 21 | 151 | 15,953,171 |
| 1d3f49a05047a28c | codex | bpf-benchmark | 2026-03-30T03:19:06.064Z | 16.4m | 2 | 17 | 107 | 5,730,591 |
| 67c3c044203072cf | codex | bpf-benchmark | 2026-05-18T21:32:36.894Z | 16.4m | 2 | 15 | 137 | 6,324,029 |
| cfbe3d08554c9293 | codex | bpf-benchmark | 2026-03-10T22:06:15.196Z | 16.3m | 2 | 11 | 122 | 6,645,337 |
| 6e406346be6f1a1a | codex | bpf-benchmark | 2026-04-29T01:32:39.022Z | 16.3m | 2 | 16 | 139 | 13,025,168 |
| e80213b71a83e77b | codex | bpf-benchmark | 2026-03-30T13:04:41.001Z | 16.2m | 2 | 32 | 120 | 7,691,254 |
| 0cd7bb0bb3d8b846 | codex | bpf-benchmark | 2026-07-10T21:41:07.985Z | 16.2m | 13 | 57 | 120 | 3,940,638 |
| 8ecedb84d1bbf8cc | codex | bpf-benchmark | 2026-03-08T05:26:57.070Z | 16.2m | 2 | 24 | 106 | 3,349,577 |
| 99d01fa379337c2d | codex | linux-framework | 2026-03-21T01:04:34.273Z | 16.2m | 2 | 25 | 146 | 6,765,604 |
| 71446cbf764ff1fd | codex | bpf-benchmark | 2026-04-11T19:37:56.855Z | 16.1m | 2 | 12 | 135 | 15,178,745 |
| 08d09a700be2d97b | codex | bpf-benchmark | 2026-05-01T05:51:10.386Z | 16.0m | 2 | 11 | 191 | 13,317,273 |
| 30aa4705654ec904 | codex | bpf-benchmark | 2026-03-19T02:53:08.171Z | 16.0m | 2 | 36 | 108 | 5,818,988 |
| 48b154f99888d7eb | codex | bpf-benchmark | 2026-03-29T15:12:40.247Z | 16.0m | 2 | 15 | 103 | 7,804,665 |
| 32e1ed1a7bbb7cff | codex | bpf-benchmark | 2026-04-28T00:21:06.265Z | 16.0m | 2 | 38 | 120 | 7,935,662 |
| f64bc46e2375efe1 | codex | bpf-benchmark | 2026-03-28T21:34:44.284Z | 16.0m | 2 | 27 | 114 | 9,463,800 |
| 7637cc0ce4ee3e43 | codex | bpf-benchmark | 2026-03-27T16:42:59.614Z | 15.9m | 1 | 33 | 179 | 127,263,960 |
| fe24dc95f8754d54 | codex | bpf-benchmark | 2026-05-11T08:18:07.055Z | 15.8m | 2 | 11 | 151 | 16,645,191 |
| 3bdd1620b6e6f838 | codex | bpf-benchmark | 2026-03-26T19:49:52.145Z | 15.8m | 2 | 12 | 100 | 8,822,827 |
| c9287f0df1e38738 | codex | bpf-benchmark | 2026-03-11T21:21:42.594Z | 15.8m | 2 | 19 | 100 | 6,853,601 |
| ac35b51e67f005bc | codex | bpf-benchmark | 2026-03-11T18:16:02.218Z | 15.7m | 4 | 11 | 137 | 9,475,698 |
| c01b300d1a229ad5 | codex | bpf-benchmark | 2026-05-10T03:27:22.606Z | 15.7m | 2 | 14 | 124 | 10,785,049 |
| 5332971b2170eb0d | codex | bpf-benchmark | 2026-04-28T03:49:46.897Z | 15.7m | 2 | 9 | 100 | 8,479,677 |
| bb3e80c51f934820 | codex | bpf-benchmark | 2026-05-11T18:46:53.700Z | 15.7m | 2 | 13 | 153 | 14,460,461 |
| 0d687aea2317d2f5 | codex | bpf-benchmark | 2026-04-30T05:55:43.208Z | 15.7m | 2 | 16 | 222 | 18,956,530 |
| 22b33ddc3da8b488 | codex | bpf-benchmark | 2026-05-10T19:27:30.599Z | 15.6m | 2 | 20 | 133 | 11,779,338 |
| cd01024aa98a2603 | codex | bpf-benchmark | 2026-04-23T23:49:39.682Z | 15.6m | 2 | 16 | 158 | 8,152,367 |
| 97a6b3d499da86d7 | codex | bpf-benchmark | 2026-05-13T00:56:13.244Z | 15.6m | 2 | 10 | 157 | 7,235,429 |
| f1dfc0787e550e2f | codex | bpf-benchmark | 2026-03-28T18:31:13.487Z | 15.6m | 2 | 29 | 107 | 8,034,584 |
| 931139436a51c38d | codex | bpftime-worktree-552 | 2026-03-18T17:43:09.659Z | 15.5m | 2 | 28 | 118 | 6,065,740 |
| 59580a88cfaeceba | codex | bpf-benchmark | 2026-03-23T12:46:30.099Z | 15.5m | 2 | 21 | 100 | 7,231,495 |
| 0588c2712162841c | codex | my-paper-work | 2026-07-07T21:34:35.870Z | 15.5m | 6 | 45 | 154 | 7,376,335 |
| c0699e95b60f5d3f | codex | bpf-benchmark | 2026-03-27T03:29:22.009Z | 15.5m | 2 | 26 | 144 | 10,607,376 |
| b1b1da43a5bd4ce0 | codex | bpf-benchmark | 2026-03-21T06:59:37.221Z | 15.5m | 2 | 14 | 147 | 5,605,672 |
| b716ac46856cf453 | codex | bpf-benchmark | 2026-03-08T06:09:16.505Z | 15.4m | 2 | 31 | 116 | 5,524,528 |
| 76333cb798bf528d | codex | bpf-benchmark | 2026-03-30T01:00:08.954Z | 15.4m | 2 | 20 | 122 | 9,363,897 |
| bc2f3a6893d4e370 | claude | ActPlane | 2026-05-30T04:37:22.969Z | 15.4m | 1 | 163 | 108 | 11,412,396 |
| 5dc894ee716a4291 | codex | bpftime-gpu-verifier | 2026-03-18T18:17:50.856Z | 15.3m | 2 | 28 | 120 | 5,582,032 |
| ac384f23235e0560 | codex | bpf-benchmark | 2026-03-11T16:01:36.165Z | 15.3m | 3 | 20 | 103 | 5,041,030 |
| f62ae45a9a97807e | codex | bpf-benchmark | 2026-03-27T03:08:31.555Z | 15.3m | 2 | 16 | 122 | 10,109,186 |
| df03413d63dfb118 | codex | passes | 2026-05-13T01:47:41.408Z | 15.3m | 2 | 11 | 110 | 5,513,480 |
| ff4bbc7b36df1fb5 | codex | workspace | 2026-03-08T00:07:48.351Z | 15.3m | 1 | 21 | 113 | 213,168,403 |
| ac79930349c2d710 | codex | ebpf-verifier-agent | 2026-03-18T21:57:18.760Z | 15.3m | 2 | 13 | 129 | 14,473,147 |
| e74c814dce6268f1 | codex | bpf-benchmark | 2026-05-07T00:45:26.070Z | 15.3m | 2 | 22 | 105 | 8,035,240 |
| dff8c3dac4234fcf | codex | bpfopt | 2026-04-29T21:56:56.079Z | 15.3m | 2 | 15 | 148 | 9,854,774 |
| 55393ed4c89e796f | codex | linux-framework | 2026-03-29T17:10:53.498Z | 15.2m | 2 | 31 | 138 | 5,284,507 |
| 325fccf6d639dca3 | codex | bpf-benchmark | 2026-03-24T21:06:27.925Z | 15.2m | 1 | 28 | 151 | 158,493,402 |
| 2e45f3b9ef2d9d95 | codex | linux-framework | 2026-03-21T17:18:22.262Z | 15.2m | 2 | 19 | 163 | 6,813,066 |
| a94ceb00fe1b9c0b | codex | bpf-benchmark | 2026-03-27T03:29:37.302Z | 15.1m | 2 | 12 | 159 | 18,661,613 |
| 888d29d98cba8779 | codex | workspace | 2026-03-07T05:25:09.105Z | 15.1m | 1 | 27 | 142 | 124,652,695 |
| d6bc3e8beaff2fbf | codex | nccl-eBPF | 2026-03-09T03:13:24.401Z | 15.0m | 3 | 23 | 105 | 4,826,843 |
| 3cb26ca5777864f3 | codex | bpf-benchmark | 2026-05-11T05:30:32.196Z | 15.0m | 2 | 10 | 117 | 4,543,980 |
| 12bd4426891bb3c7 | codex | bpf-benchmark | 2026-05-06T02:55:38.281Z | 14.9m | 2 | 8 | 117 | 3,527,626 |
| 342d8d630352317a | codex | bpf-benchmark | 2026-03-20T04:21:27.756Z | 14.9m | 2 | 27 | 108 | 8,756,768 |
| e4bdcb517eececce | codex | bpf-benchmark | 2026-05-12T00:36:40.519Z | 14.9m | 2 | 19 | 125 | 9,503,282 |
| db1ea7234fef01d0 | codex | bpf-benchmark | 2026-03-28T18:33:09.954Z | 14.9m | 2 | 23 | 136 | 6,251,321 |
| 2b4a60f13b38af0c | codex | bpf-benchmark | 2026-05-08T21:29:12.070Z | 14.8m | 2 | 16 | 145 | 12,864,650 |
| 992b703771e0efcb | codex | bpf-benchmark | 2026-05-11T01:37:58.005Z | 14.8m | 2 | 8 | 166 | 8,214,308 |
| df78f107c65ffaa0 | codex | linux-framework | 2026-03-29T17:10:39.764Z | 14.8m | 2 | 16 | 112 | 9,088,145 |
| 4b9543d02fc96379 | codex | linux-framework | 2026-03-20T00:15:17.009Z | 14.7m | 2 | 17 | 100 | 10,036,871 |
| 5d81b48d0b2e9584 | codex | bpf-benchmark | 2026-04-23T02:50:14.370Z | 14.7m | 2 | 16 | 101 | 8,602,937 |
| 2b601d73ada63c36 | codex | bpf-benchmark | 2026-05-07T03:28:34.085Z | 14.7m | 2 | 7 | 160 | 7,782,189 |
| b529e5b3f6f2776f | codex | workspace | 2026-07-07T23:45:05.405Z | 14.7m | 2 | 42 | 108 | 650,724,215 |
| 3f9d327ebd60e130 | codex | bpf-benchmark | 2026-05-01T01:15:09.441Z | 14.6m | 2 | 13 | 157 | 11,343,623 |
| 45539c42dc1cbe47 | codex | bpftime | 2026-03-09T01:58:30.035Z | 14.6m | 2 | 28 | 133 | 3,192,125 |
| dbab06bc0fa40f1d | codex | bpf-benchmark | 2026-04-11T15:49:29.680Z | 14.5m | 2 | 9 | 119 | 11,270,897 |
| 14f4bd00eed0532e | codex | bpf-benchmark | 2026-04-08T09:27:30.557Z | 14.5m | 5 | 21 | 100 | 1,542,153,635 |
| 3eadbe34867aabae | codex | ebpf-verifier-agent | 2026-03-18T23:56:03.629Z | 14.5m | 2 | 32 | 113 | 5,400,166 |
| a6e66b3766a7929a | codex | bpf-benchmark | 2026-03-21T02:08:24.643Z | 14.5m | 2 | 37 | 106 | 6,712,438 |
| 41586ce3c3435153 | codex | bpf-benchmark | 2026-04-08T01:29:07.922Z | 14.5m | 5 | 26 | 124 | 1,276,485,488 |
| 44e836a4cc0c8c9d | codex | bpf-benchmark | 2026-05-01T01:42:54.054Z | 14.5m | 2 | 12 | 249 | 9,038,224 |
| 86c621d21a7ddd94 | codex | bpf-benchmark | 2026-05-10T07:38:45.189Z | 14.5m | 2 | 17 | 154 | 14,514,126 |
| 7429d0f219a9f514 | codex | bpf-benchmark | 2026-04-24T08:00:27.504Z | 14.4m | 2 | 22 | 101 | 9,708,262 |
| 78a0e4f265c89dd9 | codex | bpf-benchmark | 2026-03-28T16:14:34.791Z | 14.4m | 2 | 16 | 103 | 7,097,143 |
| 7b79b2b64eaa39ab | codex | bpf-benchmark | 2026-05-05T08:42:49.055Z | 14.4m | 2 | 20 | 146 | 13,233,437 |
| 66a6f1181771284c | codex | bpf-benchmark | 2026-03-12T22:10:54.065Z | 14.4m | 4 | 31 | 114 | 7,163,854 |
| 4a520ed7307c8448 | codex | bpf-benchmark | 2026-05-09T03:46:34.618Z | 14.3m | 2 | 12 | 128 | 12,021,050 |
| 4cd3df745fb8c9e3 | codex | bpf-benchmark | 2026-05-17T08:32:54.464Z | 14.3m | 2 | 10 | 137 | 6,283,433 |
| e5cb015b935a75ea | codex | bpf-benchmark | 2026-04-23T03:54:54.280Z | 14.3m | 2 | 23 | 120 | 7,448,072 |
| f6643779c938dd0a | codex | bpf-benchmark | 2026-04-29T01:36:20.951Z | 14.2m | 2 | 8 | 174 | 7,412,236 |
| b60ac5cc3ad299e2 | codex | bpf-benchmark | 2026-05-09T03:17:02.437Z | 14.2m | 2 | 15 | 123 | 9,785,437 |
| 6e15e9a28449ba7a | codex | bpf-benchmark | 2026-04-24T03:38:27.647Z | 14.2m | 2 | 21 | 126 | 6,560,156 |
| e2b562648680069c | codex | bpf-benchmark | 2026-04-22T07:43:44.186Z | 14.2m | 2 | 9 | 127 | 14,251,265 |
| 7ced6b377240c571 | codex | linux-framework | 2026-03-29T17:51:42.232Z | 14.1m | 2 | 10 | 119 | 7,093,859 |
| 0ba37f9f8008275b | codex | bpf-benchmark | 2026-03-26T23:56:16.451Z | 14.1m | 2 | 23 | 105 | 8,064,148 |
| 4997c4d79585dc19 | codex | eunomia-bpf | 2026-03-08T11:44:41.683Z | 14.1m | 1 | 33 | 121 | 2,007,308 |
| 039d836da932277d | codex | bpf-benchmark | 2026-03-27T00:46:10.742Z | 14.1m | 2 | 14 | 100 | 6,035,529 |
| d92342f22b535ddf | codex | bpf-benchmark | 2026-03-12T20:35:50.686Z | 14.1m | 2 | 12 | 126 | 8,309,168 |
| f1dab7d4f0ff241d | codex | bpftime-worktree-542 | 2026-03-19T15:51:01.153Z | 14.1m | 2 | 17 | 103 | 9,033,125 |
| 0f6cc5eee30cec47 | codex | bpf-benchmark | 2026-03-21T23:01:23.533Z | 14.0m | 2 | 20 | 130 | 8,651,131 |
| 2e20440ad14a782e | codex | bpf-benchmark | 2026-04-30T05:22:58.433Z | 14.0m | 2 | 13 | 144 | 4,975,025 |
| 9532af8d2ddc6685 | claude | ActPlane | 2026-05-31T19:42:05.065Z | 13.9m | 1 | 144 | 132 | 16,859,913 |
| 1fba328fdc18db5d | codex | ebpf-verifier | 2026-03-18T23:30:17.750Z | 13.9m | 2 | 35 | 125 | 7,078,593 |
| 58efe692b1eec7de | codex | bpf-benchmark | 2026-05-18T00:03:57.672Z | 13.9m | 2 | 7 | 119 | 5,123,612 |
| 26342214dd5fc963 | codex | bpf-benchmark | 2026-03-23T01:12:49.549Z | 13.9m | 2 | 40 | 138 | 5,372,251 |
| b2e0efdcf291aa87 | codex | bpf-benchmark | 2026-04-25T19:30:13.557Z | 13.9m | 2 | 13 | 138 | 7,244,630 |
| bd7d2bbb248f305e | codex | bpf-benchmark | 2026-03-29T16:42:53.771Z | 13.9m | 2 | 16 | 100 | 8,332,666 |
| d630019cb834cd67 | codex | bpf-benchmark | 2026-03-20T22:02:17.132Z | 13.8m | 2 | 25 | 105 | 7,686,505 |
| f4be73a89a235e9f | codex | bpf-benchmark | 2026-04-29T06:47:15.887Z | 13.8m | 2 | 14 | 131 | 9,895,540 |
| 25e2c01412a51890 | codex | bpf-benchmark | 2026-03-28T21:43:59.662Z | 13.8m | 2 | 20 | 152 | 11,505,502 |
| 35b988d6c80a8719 | codex | linux-framework | 2026-05-03T22:56:59.321Z | 13.8m | 2 | 11 | 119 | 6,823,373 |
| 926f41d0711ebbd4 | codex | bpf-benchmark | 2026-05-06T23:43:10.267Z | 13.8m | 2 | 12 | 166 | 5,290,954 |
| a98432caa44b80b2 | codex | bpf-benchmark | 2026-05-07T06:26:56.109Z | 13.8m | 2 | 6 | 102 | 8,071,842 |
| d36900646723fe48 | codex | eunomia-bpf | 2026-03-08T20:33:46.438Z | 13.8m | 1 | 20 | 107 | 3,600,264 |
| e6670c9003784152 | codex | bpf-benchmark | 2026-05-14T04:10:53.000Z | 13.8m | 2 | 10 | 126 | 7,784,206 |
| a6909f02b595302b | codex | bpf-benchmark | 2026-05-09T07:39:46.373Z | 13.7m | 2 | 19 | 105 | 7,743,290 |
| 91625b9811847e9f | codex | bpfopt | 2026-05-11T23:42:38.985Z | 13.7m | 2 | 15 | 136 | 9,199,297 |
| 861801a0b6fb00dd | codex | bpf-benchmark | 2026-04-27T03:05:18.433Z | 13.6m | 2 | 25 | 153 | 9,402,544 |
| 02f68c8a6d3ed7b0 | codex | bpfopt | 2026-05-09T19:16:55.676Z | 13.6m | 2 | 22 | 155 | 6,733,532 |
| 65dc47264ec8c32c | codex | bpf-benchmark | 2026-03-12T00:40:25.999Z | 13.6m | 3 | 10 | 112 | 7,703,125 |
| 391eb7c5843de91a | codex | bpftime | 2026-03-08T06:59:46.274Z | 13.6m | 2 | 28 | 107 | 18,147,102 |
| c3b0f35a08132503 | codex | linux-framework | 2026-05-04T01:07:53.851Z | 13.6m | 2 | 9 | 123 | 6,395,325 |
| 6e1f1f01dca89f5a | codex | workspace | 2026-03-07T05:25:08.992Z | 13.5m | 1 | 17 | 110 | 122,584,584 |
| 402587eca8583467 | codex | paper | 2026-03-28T22:20:33.427Z | 13.5m | 2 | 24 | 100 | 6,145,739 |
| 6164d8a3471eca74 | codex | bpf-benchmark | 2026-04-29T22:46:35.810Z | 13.5m | 2 | 17 | 153 | 6,679,415 |
| a15d84d5deebcf5a | codex | bpf-benchmark | 2026-03-28T18:31:28.133Z | 13.5m | 2 | 22 | 124 | 5,115,453 |
| 8b34252c142bcdf8 | codex | bpf-benchmark | 2026-05-09T01:52:31.603Z | 13.5m | 2 | 11 | 113 | 11,511,401 |
| e9b56032da149eee | codex | bpf-benchmark | 2026-04-22T05:36:44.735Z | 13.5m | 2 | 15 | 129 | 7,544,342 |
| 3e5ed9b29b7d73e0 | codex | bpf-benchmark | 2026-03-26T22:55:04.326Z | 13.4m | 2 | 18 | 109 | 9,117,468 |
| d8a7aebf492f6b52 | codex | bpf-benchmark | 2026-04-30T02:55:09.072Z | 13.4m | 2 | 10 | 120 | 7,760,585 |
| 7d08ee0098d9d9ce | codex | bpf-benchmark | 2026-05-11T23:06:08.816Z | 13.4m | 2 | 15 | 155 | 5,280,055 |
| e1a21826522abec8 | codex | bpf-benchmark | 2026-03-28T15:04:39.174Z | 13.4m | 2 | 11 | 118 | 10,454,094 |
| 742b6a73b7423576 | codex | bpf-benchmark | 2026-03-10T19:53:29.759Z | 13.4m | 4 | 13 | 103 | 6,197,787 |
| 47076560647605d9 | codex | bpf-benchmark | 2026-04-05T07:29:16.430Z | 13.3m | 2 | 31 | 189 | 817,020,457 |
| 1a5d8b65a88ea07b | codex | bpf-benchmark | 2026-04-23T01:57:23.659Z | 13.3m | 2 | 24 | 129 | 7,817,816 |
| 5c163d49449bcc70 | codex | bpftime-gpu-verifier | 2026-03-19T18:27:59.062Z | 13.3m | 2 | 19 | 106 | 6,727,147 |
| 39c96675d3ff7b3c | codex | bpf-benchmark | 2026-05-09T02:44:11.301Z | 13.3m | 2 | 11 | 110 | 7,055,336 |
| cfe5e414e59cc47d | codex | bpf-benchmark | 2026-05-09T18:21:26.329Z | 13.3m | 2 | 12 | 100 | 8,757,458 |
| 0a9513ccbc930ed4 | codex | bpf-benchmark | 2026-03-11T13:35:08.501Z | 13.3m | 4 | 19 | 147 | 3,930,410 |
| 72426c99295b790d | codex | bpf-benchmark | 2026-03-10T21:06:49.833Z | 13.2m | 5 | 20 | 112 | 5,959,771 |
| dd1ee77ab532739c | codex | bpf-benchmark | 2026-05-13T19:01:21.110Z | 13.2m | 2 | 11 | 115 | 6,852,294 |
| e468d90ec96ac8cf | codex | bpfopt | 2026-05-17T05:55:13.936Z | 13.1m | 2 | 11 | 123 | 6,008,155 |
| 1f3c15f257fb6431 | codex | bpf-benchmark | 2026-03-10T18:49:35.969Z | 13.1m | 3 | 28 | 102 | 4,377,847 |
| 39455e1b25831ae1 | codex | bpfopt | 2026-05-13T19:42:38.401Z | 13.1m | 2 | 8 | 107 | 9,550,692 |
| 03bed5ede3b4533c | codex | bpf-benchmark | 2026-05-06T01:49:52.552Z | 13.1m | 2 | 8 | 127 | 5,034,060 |
| 70595290b7ee589e | codex | bpf-benchmark | 2026-05-10T09:02:01.260Z | 13.0m | 2 | 13 | 107 | 9,720,495 |
| 7d06473cfc67004e | claude | ActPlane | 2026-05-31T19:17:35.411Z | 13.0m | 1 | 131 | 121 | 10,386,066 |
| ee83005851339b74 | codex | bpf-benchmark | 2026-04-30T05:37:57.663Z | 13.0m | 2 | 36 | 185 | 13,684,112 |
| a84be99c591b1629 | codex | gpu_ext | 2026-03-07T02:48:16.843Z | 12.9m | 5 | 8 | 107 | 8,557,733 |
| 83dac8257cb10bcb | codex | bpf-benchmark | 2026-05-11T20:03:15.172Z | 12.9m | 2 | 8 | 125 | 6,433,134 |
| 7811ab673ba51a4b | codex | bpf-benchmark | 2026-03-19T22:39:40.150Z | 12.9m | 2 | 22 | 110 | 3,649,656 |
| 0e820a93e4a78306 | codex | linux-framework | 2026-03-20T03:02:06.321Z | 12.8m | 2 | 20 | 114 | 7,597,849 |
| 2e9eea955fe341f6 | codex | linux-framework | 2026-03-29T17:11:34.704Z | 12.8m | 2 | 25 | 131 | 5,507,553 |
| b553027460ee0219 | codex | ActPlane | 2026-06-14T09:56:58.158Z | 12.8m | 2 | 37 | 115 | 419,287,295 |
| 31ef35ad54ac2163 | codex | bpf-benchmark | 2026-05-12T22:14:05.165Z | 12.8m | 2 | 13 | 134 | 7,754,144 |
| 310b41cb78702da0 | codex | bpf-benchmark | 2026-05-05T08:51:33.466Z | 12.7m | 2 | 6 | 106 | 9,487,829 |
| 6d1b79a52fd94937 | codex | bpf-benchmark | 2026-03-30T04:36:10.132Z | 12.7m | 2 | 11 | 116 | 7,263,950 |
| 759ae88f56ce3f33 | codex | bpf-benchmark | 2026-04-23T21:51:37.434Z | 12.7m | 2 | 22 | 102 | 6,052,527 |
| 371fbdebcf2b5335 | codex | bpf-benchmark | 2026-04-29T05:11:06.893Z | 12.6m | 2 | 17 | 115 | 4,718,576 |
| c2613b6b24d442de | codex | bpf-benchmark | 2026-03-28T15:06:09.125Z | 12.5m | 2 | 29 | 180 | 8,550,539 |
| 3983eeedd7656d4c | codex | nccl-eBPF | 2026-03-09T01:57:53.047Z | 12.5m | 2 | 11 | 110 | 2,707,648 |
| f892ed549660ea81 | codex | bpf-benchmark | 2026-05-06T02:46:41.258Z | 12.5m | 2 | 10 | 102 | 4,967,009 |
| 7b9264f6e75def77 | codex | bpf-benchmark | 2026-03-27T17:00:41.708Z | 12.5m | 1 | 30 | 126 | 137,882,035 |
| a992b4f89644994f | codex | bpf-benchmark | 2026-03-19T18:01:14.152Z | 12.4m | 2 | 30 | 109 | 8,560,520 |
| 9bb7b56f6d08c2b3 | codex | bpf-benchmark | 2026-04-25T20:19:15.942Z | 12.4m | 2 | 9 | 142 | 11,642,340 |
| 41a561e4309ffa7d | codex | bpf-benchmark | 2026-03-29T01:19:58.839Z | 12.4m | 2 | 29 | 132 | 10,891,115 |
| 9ff91c0363055b61 | codex | bpf-benchmark | 2026-05-06T02:39:32.289Z | 12.4m | 2 | 10 | 103 | 8,716,761 |
| a0c76c349c135f11 | claude | corpus | 2026-05-31T09:29:58.611Z | 12.3m | 1 | 117 | 112 | 6,919,847 |
| d53fd7c45ee76b5c | codex | bpf-benchmark | 2026-05-05T17:43:40.267Z | 12.3m | 2 | 12 | 134 | 6,524,637 |
| a7fc71dec7cc862d | codex | bpf-benchmark | 2026-05-09T04:17:22.046Z | 12.3m | 2 | 17 | 128 | 8,422,753 |
| e4bdecfbc7000a36 | codex | bpf-benchmark | 2026-05-11T03:41:54.436Z | 12.3m | 2 | 11 | 139 | 15,037,780 |
| 4feb22c8855209f5 | codex | bpf-benchmark | 2026-05-01T04:13:42.706Z | 12.3m | 2 | 10 | 167 | 9,236,841 |
| 396cd89b79e83689 | codex | bpf-benchmark | 2026-03-27T19:10:04.321Z | 12.3m | 2 | 16 | 156 | 192,234,953 |
| 7e5dc398340b3d7c | codex | bpf-benchmark | 2026-04-24T21:20:37.728Z | 12.2m | 2 | 17 | 104 | 7,979,712 |
| af8652b3d249882c | codex | bpf-benchmark | 2026-05-06T02:04:55.390Z | 12.2m | 2 | 23 | 109 | 7,767,996 |
| c54bf569bba1a827 | codex | bpf-benchmark | 2026-03-28T21:41:56.335Z | 12.2m | 2 | 24 | 109 | 8,962,978 |
| 17cf7d68eee2b863 | codex | bpf-benchmark | 2026-05-07T07:24:41.560Z | 12.2m | 2 | 8 | 139 | 6,437,631 |
| 3df13412b256dab7 | codex | workspace | 2026-03-07T03:43:41.608Z | 12.2m | 1 | 27 | 107 | 86,878,119 |
| e1fed5db3fdd9fd4 | codex | bpf-benchmark | 2026-05-10T07:35:47.100Z | 12.2m | 2 | 14 | 109 | 8,639,621 |
| a728049029206b7d | codex | bpf-benchmark | 2026-05-03T05:38:57.042Z | 12.1m | 2 | 18 | 127 | 10,795,653 |
| c9ffee76e132c775 | codex | bpf-benchmark | 2026-05-01T00:03:17.795Z | 12.1m | 2 | 11 | 107 | 3,881,031 |
| 00739b80d935cddf | codex | bpf-benchmark | 2026-03-24T23:09:48.319Z | 12.1m | 2 | 19 | 109 | 4,596,110 |
| 86cc8a949ffc8f33 | codex | bpf-benchmark | 2026-05-07T00:43:55.702Z | 12.1m | 2 | 7 | 108 | 8,841,643 |
| b291c0f5e87fef36 | codex | bpf-benchmark | 2026-03-11T03:10:12.856Z | 12.1m | 1 | 11 | 142 | 5,504,135 |
| 6cc7c720eed5772d | codex | bpf-benchmark | 2026-04-30T02:56:32.463Z | 12.1m | 2 | 9 | 126 | 11,809,898 |
| 00b31be31c94fc1f | codex | bpf-benchmark | 2026-03-11T20:47:35.573Z | 12.0m | 1 | 13 | 100 | 3,059,103 |
| f7374c3e0eeb67fa | codex | bpf-benchmark | 2026-04-17T02:58:17.263Z | 12.0m | 2 | 21 | 135 | 7,187,068 |
| 883fe6a3f86e519a | codex | bpf-benchmark | 2026-05-08T00:11:41.114Z | 12.0m | 2 | 12 | 105 | 4,319,062 |
| ce0243cb0f5cf711 | codex | bpf-benchmark | 2026-05-01T01:25:38.822Z | 11.9m | 2 | 16 | 124 | 7,628,745 |
| 1cf48718718c9007 | codex | bpf-benchmark | 2026-05-17T18:20:57.392Z | 11.9m | 2 | 5 | 109 | 4,144,909 |
| 74a632f0bb50bc7a | codex | bpf-benchmark | 2026-03-10T21:48:15.146Z | 11.9m | 2 | 16 | 106 | 10,239,225 |
| 9f494f7eebb2a7f4 | claude | corpus | 2026-05-31T09:17:34.270Z | 11.9m | 1 | 140 | 116 | 8,914,122 |
| 0bf29f7ab8bbbcaa | codex | bpf-benchmark | 2026-04-28T18:00:06.083Z | 11.9m | 2 | 14 | 116 | 4,661,578 |
| 406ac1829e3ac12f | codex | bpf-benchmark | 2026-05-01T05:36:19.466Z | 11.8m | 2 | 10 | 142 | 9,734,421 |
| 907dd98db58900aa | codex | bpf-benchmark | 2026-04-25T20:18:04.071Z | 11.8m | 2 | 17 | 104 | 5,854,455 |
| fa78db08dcf30559 | codex | bpf-benchmark | 2026-03-20T04:25:18.279Z | 11.8m | 2 | 10 | 144 | 7,613,095 |
| 8ed76a9e21972af0 | codex | bpf-benchmark | 2026-03-27T03:31:01.816Z | 11.8m | 2 | 13 | 105 | 8,224,886 |
| 049b38ad68ac763e | codex | bpf-benchmark | 2026-04-30T03:29:00.955Z | 11.7m | 2 | 14 | 134 | 6,624,913 |
| 19d71cb455b2aa41 | codex | bpf-benchmark | 2026-03-28T16:04:09.250Z | 11.7m | 2 | 26 | 139 | 5,966,660 |
| 48cde1f34eb01343 | codex | bpfopt | 2026-05-12T21:24:08.541Z | 11.7m | 2 | 16 | 141 | 9,360,546 |
| 2e8be430efb0a99b | codex | bpf-benchmark | 2026-04-20T21:55:04.215Z | 11.6m | 2 | 7 | 122 | 6,416,330 |
| f69280541715caa7 | codex | gpu_ext | 2026-03-06T22:50:13.746Z | 11.6m | 2 | 12 | 101 | 6,360,443 |
| bae4226ba1a2fcdd | codex | bpfopt | 2026-05-12T00:14:48.542Z | 11.6m | 2 | 13 | 107 | 5,304,965 |
| b0a1ccef97d684e8 | codex | bpf-benchmark | 2026-05-09T01:55:05.098Z | 11.6m | 2 | 15 | 105 | 5,547,421 |
| 3348df666d685b4e | codex | bpf-benchmark | 2026-04-29T22:46:17.508Z | 11.5m | 2 | 12 | 111 | 3,767,163 |
| f8fbfc6bcbfc5ab7 | codex | bpf-benchmark | 2026-05-11T06:20:38.373Z | 11.5m | 2 | 8 | 118 | 3,638,450 |
| b761e555e3b0a731 | codex | bpf-benchmark | 2026-05-05T18:10:47.346Z | 11.5m | 2 | 8 | 148 | 6,987,499 |
| 1f4893d316a0be5d | codex | bpf-benchmark | 2026-05-03T00:08:31.543Z | 11.5m | 2 | 13 | 145 | 7,892,493 |
| 4e67b80f6ef2ae47 | codex | bpf-benchmark | 2026-05-06T07:49:05.890Z | 11.5m | 2 | 6 | 108 | 6,834,502 |
| fe729132f7e4d53c | codex | bpf-benchmark | 2026-03-11T03:01:58.939Z | 11.4m | 1 | 6 | 110 | 9,011,208 |
| 62b34ea4bdce9216 | codex | bpf-benchmark | 2026-03-25T23:41:25.862Z | 11.4m | 2 | 15 | 103 | 4,386,551 |
| ed72e5bd1bbe6ba1 | codex | bpf-benchmark | 2026-05-12T00:24:19.130Z | 11.4m | 2 | 8 | 101 | 3,868,318 |
| 637d79882eedc2db | codex | bpf-benchmark | 2026-04-25T01:05:13.624Z | 11.4m | 2 | 19 | 101 | 5,660,574 |
| 2ac407af462aba37 | codex | workspace | 2026-03-07T08:37:37.658Z | 11.3m | 1 | 10 | 130 | 6,488,769 |
| 73b6d52507bfed7a | codex | workspace | 2026-03-08T22:30:57.438Z | 11.3m | 1 | 30 | 190 | 293,665,919 |
| a467c71a14605624 | codex | bpf-benchmark | 2026-04-29T07:10:31.103Z | 11.3m | 2 | 15 | 109 | 7,786,558 |
| a390d9957919c996 | codex | bpf-benchmark | 2026-05-11T00:44:52.858Z | 11.2m | 2 | 8 | 136 | 7,940,190 |
| 4df2de2198d9971a | codex | bpf-benchmark | 2026-04-23T20:41:05.460Z | 11.1m | 2 | 22 | 112 | 6,733,722 |
| ddd73aae141b1aea | codex | bpf-benchmark | 2026-05-06T19:04:08.458Z | 11.1m | 2 | 7 | 118 | 4,067,493 |
| 23f97bd443d67234 | codex | bpf-benchmark | 2026-05-09T18:27:23.829Z | 11.1m | 2 | 9 | 127 | 4,477,437 |
| a4eeefee1367fee0 | codex | bpfopt | 2026-05-11T21:36:10.482Z | 11.1m | 2 | 13 | 110 | 5,290,355 |
| 3a0a4ca3da8a1f7c | codex | bpf-benchmark | 2026-04-26T23:09:52.746Z | 10.9m | 2 | 16 | 104 | 5,744,270 |
| fa2d1a7fe972ca50 | codex | bpf-benchmark | 2026-05-03T05:32:53.313Z | 10.9m | 2 | 14 | 119 | 7,473,570 |
| 9b38fef683da146b | codex | bpf-benchmark | 2026-05-05T15:21:23.609Z | 10.9m | 2 | 11 | 130 | 5,759,829 |
| 28649126558719f0 | codex | bpf-benchmark | 2026-03-27T02:21:59.685Z | 10.8m | 2 | 16 | 105 | 5,121,607 |
| c8e42af571fcb14b | codex | bpf-benchmark | 2026-03-27T02:54:59.031Z | 10.8m | 2 | 18 | 106 | 5,045,153 |
| 6bfa743e26eef1bc | codex | bpf-benchmark | 2026-05-06T21:01:31.227Z | 10.8m | 2 | 7 | 111 | 5,630,888 |
| f126d1054e982601 | codex | bpf-benchmark | 2026-03-20T23:37:11.709Z | 10.8m | 2 | 40 | 106 | 5,427,065 |
| 7b883ab2fda72ea6 | codex | bpf-benchmark | 2026-05-19T16:25:01.788Z | 10.8m | 2 | 7 | 101 | 4,666,718 |
| 061238f84d55c959 | codex | bpf-benchmark | 2026-05-05T17:30:04.159Z | 10.8m | 2 | 12 | 124 | 9,133,618 |
| 47ac9adc31c22ab8 | codex | workspace | 2026-03-07T08:45:53.616Z | 10.8m | 1 | 9 | 100 | 5,375,880 |
| b359c0f99727921f | codex | bpftime-worktree-542 | 2026-03-19T17:20:46.295Z | 10.7m | 2 | 19 | 106 | 6,478,101 |
| e30060788d67c7eb | codex | bpf-benchmark | 2026-05-10T04:08:06.760Z | 10.7m | 2 | 17 | 109 | 8,520,088 |
| 238c404e62f5bd62 | codex | bpf-benchmark | 2026-04-29T01:15:11.820Z | 10.6m | 2 | 6 | 121 | 9,185,492 |
| 64fdff97845df3e6 | codex | bpf-benchmark | 2026-04-30T04:37:56.896Z | 10.6m | 2 | 7 | 151 | 9,580,368 |
| 7cf4d321d9250e0f | codex | bpf-benchmark | 2026-04-22T01:52:49.076Z | 10.6m | 2 | 26 | 120 | 4,882,383 |
| 20ad40ad03552ecd | claude | ActPlane | 2026-05-31T19:31:03.953Z | 10.5m | 1 | 136 | 130 | 1,292,355 |
| b1225f27e072ff09 | codex | bpf-benchmark | 2026-05-06T20:53:47.932Z | 10.5m | 2 | 9 | 120 | 5,906,920 |
| db893b02683f3c46 | codex | bpf-benchmark | 2026-03-29T16:29:24.884Z | 10.4m | 2 | 20 | 101 | 4,639,786 |
| 560e0a302604089a | codex | bpf-benchmark | 2026-05-06T04:57:02.069Z | 10.4m | 2 | 10 | 104 | 8,387,841 |
| 16bdfd20a21d4623 | codex | agentsight | 2026-06-13T18:32:52.067Z | 10.3m | 2 | 43 | 120 | 5,162,623 |
| 11a57cd48f81addc | codex | bpf-benchmark | 2026-03-26T04:05:03.716Z | 10.3m | 2 | 10 | 110 | 3,103,285 |
| 3cbfdbb2a1fd9362 | codex | bpf-benchmark | 2026-05-13T21:22:21.399Z | 10.3m | 2 | 9 | 132 | 5,873,765 |
| c8674ec8c60d09cb | codex | bpf-benchmark | 2026-05-05T17:10:48.986Z | 10.3m | 2 | 11 | 135 | 8,029,402 |
| 6e9f7ef4543231e7 | codex | bpf-benchmark | 2026-05-10T23:55:53.123Z | 10.3m | 2 | 4 | 104 | 6,601,708 |
| f55303fd38ea7e35 | codex | bpf-benchmark | 2026-03-25T00:44:33.343Z | 10.1m | 1 | 29 | 107 | 280,664,981 |
| 6475f39f7b338888 | codex | bpf-benchmark | 2026-05-13T22:51:37.620Z | 10.1m | 2 | 7 | 102 | 7,798,727 |
| 55121e3d2d47b0b1 | codex | bpf-benchmark | 2026-04-30T17:32:52.790Z | 10.1m | 2 | 13 | 126 | 6,310,984 |
| f3396adb7f17c1b2 | codex | bpf-benchmark | 2026-05-06T21:08:01.844Z | 10.0m | 2 | 17 | 107 | 5,280,021 |
| bf886691442106e2 | codex | bpf-benchmark | 2026-05-02T19:00:59.871Z | 10.0m | 2 | 12 | 154 | 7,672,237 |
| f8a0ffc029942678 | codex | bpf-benchmark | 2026-04-28T04:11:42.615Z | 10.0m | 2 | 11 | 140 | 13,888,337 |
| 797bc0e4ec688000 | codex | bpf-benchmark | 2026-03-26T19:43:52.432Z | 9.9m | 2 | 11 | 100 | 4,131,199 |
| 7ec70baa44adc7a6 | codex | bpf-benchmark | 2026-05-06T20:50:50.159Z | 9.9m | 2 | 7 | 136 | 8,883,834 |
| 8fbc35d797e8efca | claude | collector | 2026-06-03T21:03:25.410Z | 9.9m | 1 | 183 | 112 | 10,800,146 |
| 3d5b91bc187ccf54 | codex | bpf-benchmark | 2026-05-01T14:29:49.602Z | 9.9m | 2 | 21 | 102 | 7,072,362 |
| 6c0dde064afa4137 | codex | bpf-benchmark | 2026-05-08T21:57:15.603Z | 9.8m | 2 | 9 | 115 | 8,325,215 |
| e51bcbdf505d0fdc | codex | linux-framework | 2026-03-29T17:42:50.206Z | 9.8m | 2 | 13 | 102 | 6,766,055 |
| 40848a73dd97559c | codex | bpf-benchmark | 2026-04-29T03:48:08.459Z | 9.7m | 2 | 7 | 100 | 4,222,384 |
| c42a6c3462c1cc77 | codex | bpf-benchmark | 2026-04-29T01:17:43.144Z | 9.6m | 2 | 11 | 127 | 4,987,663 |
| 88cd1067c6c973da | codex | bpf-benchmark | 2026-05-06T20:39:08.250Z | 9.5m | 2 | 5 | 119 | 5,418,628 |
| 5e4481c516cf8be5 | codex | bpf-benchmark | 2026-04-29T21:18:23.764Z | 9.3m | 2 | 11 | 105 | 5,922,937 |
| 150a1e01cb152d9b | codex | bpf-benchmark | 2026-05-09T02:44:04.063Z | 9.2m | 2 | 17 | 126 | 6,520,460 |
| 5429bba65656a506 | codex | bpf-benchmark | 2026-05-06T20:44:50.385Z | 9.2m | 2 | 10 | 105 | 4,686,176 |
| b196496e2d87d7a7 | codex | bpf-benchmark | 2026-05-07T03:06:44.418Z | 9.1m | 2 | 7 | 125 | 7,590,082 |
| 91a4b97d89dc6419 | codex | bpfopt | 2026-05-13T02:54:34.473Z | 9.1m | 2 | 7 | 112 | 5,993,206 |
| d1df931ec09a6a06 | codex | bpf-benchmark | 2026-04-29T10:03:51.159Z | 9.1m | 2 | 8 | 125 | 7,051,233 |
| 38c9cf76acaaf090 | codex | workspace | 2026-03-07T08:37:37.566Z | 9.0m | 1 | 12 | 118 | 3,087,144 |
| 78132ce018cf755b | codex | bpf-benchmark | 2026-04-30T16:51:54.947Z | 8.8m | 2 | 7 | 116 | 4,627,269 |
| 5f7b707c25e0c0ae | codex | bpf-benchmark | 2026-04-28T17:54:19.723Z | 8.7m | 2 | 9 | 134 | 6,489,117 |
| 3d806b0b4c832fba | claude | collector | 2026-05-30T04:55:03.212Z | 8.6m | 1 | 199 | 140 | 14,280,308 |
| 299e850147449955 | claude | ActPlane | 2026-05-30T04:25:05.079Z | 8.6m | 1 | 194 | 144 | 13,187,614 |
| bbb9695e0e9bab8a | codex | bpf-benchmark | 2026-05-10T04:39:11.623Z | 8.5m | 2 | 7 | 112 | 5,930,771 |
| dfb82817458d9844 | codex | bpf-benchmark | 2026-04-30T02:19:21.255Z | 8.2m | 2 | 9 | 107 | 4,153,616 |
| bb77da12efb09475 | codex | bpf-benchmark | 2026-05-11T10:06:06.530Z | 8.2m | 2 | 10 | 114 | 4,606,694 |
| 0ff2ef28a94b9768 | claude | agent-a32ae6d0a8dbd25db | 2026-05-30T19:27:18.178Z | 8.2m | 1 | 138 | 102 | 7,337,921 |
| 26e72b39b9ad324a | codex | linux-framework | 2026-03-29T18:02:58.319Z | 8.2m | 2 | 11 | 112 | 6,482,612 |
| aebf1adeaac8291b | codex | bpf-benchmark | 2026-05-06T21:12:11.510Z | 8.1m | 2 | 6 | 105 | 3,308,550 |
| 04a360bc5788d97a | codex | bpf-benchmark | 2026-05-10T07:09:56.785Z | 8.1m | 2 | 10 | 110 | 6,155,772 |
| 565e9696316c305c | codex | bpf-benchmark | 2026-05-08T19:29:28.760Z | 7.9m | 2 | 5 | 111 | 4,203,413 |
| 0211ff5ef6081356 | codex | bpf-benchmark | 2026-03-25T04:03:20.439Z | 7.4m | 3 | 13 | 111 | 5,856,211 |
| 41edcc3f22998f3d | codex | bpf-benchmark | 2026-05-05T07:01:48.313Z | 7.3m | 2 | 9 | 106 | 5,190,515 |
| a7ce681a05bdfa33 | codex | bpf-benchmark | 2026-05-13T22:52:18.549Z | 7.3m | 2 | 7 | 100 | 6,165,090 |
| 41001aa3830bcfe0 | codex | bpf-benchmark | 2026-05-01T20:19:11.519Z | 7.3m | 2 | 6 | 100 | 3,135,543 |
| d091567df5f8f393 | codex | bpf-benchmark | 2026-05-01T17:20:52.341Z | 7.1m | 2 | 7 | 111 | 5,022,188 |
| e6c1d0667740f327 | codex | namei_ext | 2026-06-13T16:08:54.205Z | 6.6m | 2 | 23 | 107 | 3,444,569 |
| 9ac57f25531046ec | codex | bpf-benchmark | 2026-04-29T02:14:40.211Z | 6.3m | 2 | 10 | 105 | 4,454,623 |
| f9393615ec249cd0 | codex | my-paper-work | 2026-07-07T07:47:48.707Z | 6.1m | 2 | 20 | 100 | 2,586,253 |
| f7bc72d945e6d5f2 | claude | ActPlane | 2026-05-30T04:11:05.037Z | 6.1m | 1 | 157 | 140 | 3,659,467 |
| 8d18da8e2b3d9946 | codex | bpf-benchmark | 2026-04-29T01:17:55.768Z | 5.3m | 2 | 8 | 100 | 2,749,606 |
| 8d7e44d76de1e646 | codex | workspace | 2026-03-08T11:26:52.940Z | 3.5m | 1 | 8 | 110 | 284,224,619 |

## Candidate case-study populations

| Candidate population | Sessions | Long-horizon | Operations | Known provider tokens | Token coverage | Est. annotation input tokens | Est. worker time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Recent long-horizon (8 weeks) | 365 | 365 | 649,639 | 142,548,837,980 | 365/365 | 1,081,918,083 | 166.3 h |
| AgentSight research worktree | 42 | 10 | 8,991 | 897,606,071 | 42/42 | 14,973,740 | 2.3 h |
| Heavy project: bpf-benchmark | 2,341 | 828 | 578,174 | 176,016,696,282 | 2292/2341 | 962,899,250 | 148.0 h |

Population definitions:

- **Recent long-horizon (8 weeks):** All sessions ending since 2026-05-31 that last at least one hour or contain at least 100 tool calls.
- **AgentSight research worktree:** All sessions whose coarse project basename is exactly agentsight-research-semantic-flamegraph.
- **Heavy project: bpf-benchmark:** The complete session set of the highest-operation non-AgentSight project.

### Annotation-cost scaling

Step 0077 measured 27,362 actual annotation-backend input tokens and 15.14
summed worker-seconds per session over 7,229 source operations in 440 sessions,
or 16.4295 operations/session. Because the
candidate mean session sizes differ materially from that reference, this
inventory applies one transparent linear operation proxy:

`operation-equivalent sessions = population (LLM + tool calls) / 16.4295`

It multiplies operation-equivalent sessions by 27,362 input tokens and 15.14
worker-seconds. These are sizing estimates, not measured costs. They assume
annotation input scales linearly with source-visible operations and omit fixed
per-session overhead, batching/cache effects, output tokens, retries, and
provider latency. The reference measurement is
`step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`.

## Recommendation

**Use “AgentSight research worktree” as the primary Long Horizon case-study population.**
It combines a coherent real engineering objective with many complete long-running sessions, directly representing the agents that built the system and paper. The recent cross-project population is the stronger robustness population, but its heterogeneous objectives weaken a single case-study narrative.

Retain the other two populations as sensitivity or scope checks. Before a full
annotation run, freeze the selected session keys from
`inventory-results.json`; do not rescan-and-select after seeing annotations.
