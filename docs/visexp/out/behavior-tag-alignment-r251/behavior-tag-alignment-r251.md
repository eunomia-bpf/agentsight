# R251 Behavior-Tag Alignment

Status: `behavior_alignment_supported`

## Boundary

- Reads generated R170 semantic folded stacks only.
- Does not read raw agent histories.
- Does not call an LLM.
- Does not add human labels or user responses.
- Supports behavioral grounding only; C6 human semantic adequacy remains unsupported.

## Main Metrics

| metric | value |
|---|---:|
| total system-effect weight | 183714 |
| stack rows | 26829 |
| prompt tags | 263 |
| session tags | 53 |
| behavior keys | 987 |
| behavior entropy | 4.938 bits |
| prompt uncertainty reduction | 10.535% |
| prompt gain beyond session | 8.469% |
| prompt top-behavior purity | 20.196% |

## Session-Preserving Null

| metric | actual | null p95 | p value | pass p95 |
|---|---:|---:|---:|---|
| `prompt_gain_beyond_session_pct` | 8.469 | 1.925 | 0.0099 | True |
| `prompt_top_behavior_purity_pct` | 20.196 | 18.363 | 0.0099 | True |

## Top Prompt Profiles

| prompt | weight | top behavior | top share | distinct behaviors |
|---|---:|---|---:|---:|
| `refactor` | 73162 | `process:rg;effect:read;status:ok` | 18.985% | 546 |
| `review` | 33267 | `process:rg;effect:read;status:ok` | 20.474% | 350 |
| `design` | 15705 | `process:rg;effect:read;status:ok` | 18.606% | 207 |
| `analyze` | 11457 | `process:docker;effect:process;status:ok` | 10.98% | 145 |
| `test` | 8012 | `process:sed;effect:read;status:ok` | 15.14% | 232 |
| `research` | 4736 | `process:sed;effect:read;status:ok` | 19.637% | 146 |
| `benchmark` | 4033 | `process:sed;effect:read;status:ok` | 24.82% | 78 |
| `docs` | 3477 | `process:rg;effect:read;status:ok` | 15.243% | 126 |
| `debug` | 1587 | `process:rg;effect:read;status:ok` | 22.18% | 78 |
| `explain` | 1463 | `process:git;effect:read;status:ok` | 19.891% | 51 |

## Low-Coherence Review Queue

| prompt | weight | top share | distinct behaviors | top behaviors |
|---|---:|---:|---:|---|
| `analyze` | 11457 | 10.98% | 145 | `process:docker;effect:process;status:ok=1258; process:sed;effect:read;status:ok=1153; process:tail;effect:read;status:ok=993; process:rg;effect:read;status:ok=981; process:tool:tool;effect:process;status:observed=798; process:tool:tool;effect:process;status:ok=797; process:python3;effect:process;status:ok=773; process:git;effect:read;status:ok=685` |
| `branding` | 509 | 11.788% | 63 | `process:git;effect:read;status:ok=60; process:gh;effect:process;status:ok=58; process:sed;effect:read;status:ok=58; process:tool:tool;effect:process;status:ok=27; process:tool:tool;effect:process;status:observed=26; process:find;effect:read;status:ok=25; process:git;effect:repo;status:ok=24; process:rg;effect:read;status:ok=17` |
| `build` | 724 | 12.707% | 54 | `process:cd;effect:process;status:ok=92; process:git;effect:read;status:ok=91; process:tool:edit;effect:process;status:ok=76; process:rg;effect:read;status:ok=71; process:find;effect:read;status:ok=58; process:sed;effect:read;status:ok=44; process:tool:read;effect:process;status:ok=43; process:grep;effect:read;status:ok=25` |
| `docgen` | 131 | 12.977% | 22 | `process:python3;effect:process;status:ok=17; process:cargo;effect:process;status:ok=16; process:rg;effect:read;status:ok=13; process:find;effect:read;status:ok=10; process:git;effect:read;status:ok=10; process:jq;effect:read;status:ok=10; process:sed;effect:read;status:ok=8; process:head;effect:read;status:ok=6` |
| `todo` | 292 | 15.068% | 28 | `process:tool:tool;effect:process;status:ok=44; process:sed;effect:read;status:ok=38; process:rg;effect:read;status:ok=37; process:git;effect:read;status:ok=36; process:actplane;effect:process;status:ok=16; process:cargo;effect:test;status:ok=13; process:actplane;effect:process;status:observed=12; process:rm;effect:write;status:ok=12` |
| `test` | 8012 | 15.14% | 232 | `process:sed;effect:read;status:ok=1213; process:rg;effect:read;status:ok=911; process:git;effect:read;status:ok=781; process:tool:tool;effect:process;status:ok=601; process:tool:tool;effect:process;status:observed=521; process:find;effect:read;status:ok=359; process:python3;effect:process;status:ok=227; process:tail;effect:read;status:ok=213` |
| `docs` | 3477 | 15.243% | 126 | `process:rg;effect:read;status:ok=530; process:sed;effect:read;status:ok=494; process:git;effect:read;status:ok=365; process:nl;effect:read;status:ok=208; process:cd;effect:process;status:ok=118; process:tool:tool;effect:process;status:ok=118; process:python3;effect:process;status:ok=107; process:tool:read;effect:process;status:ok=105` |
| `install` | 151 | 15.894% | 25 | `process:git;effect:read;status:ok=24; process:sed;effect:read;status:ok=24; process:tool:tool;effect:process;status:observed=21; process:rg;effect:read;status:ok=13; process:gh;effect:process;status:ok=11; process:tool:tool;effect:process;status:ok=7; process:rm;effect:write;status:fail=6; process:cargo;effect:test;status:ok=5` |
| `backup` | 116 | 16.379% | 28 | `process:find;effect:read;status:ok=19; process:jq;effect:read;status:ok=19; process:tool:tool;effect:process;status:ok=10; process:f_find;effect:process;status:ok=8; process:ai-agent-trace-backups;effect:process;status:ok=7; process:ai-agent-traces-20260601-235658-pdt-root-owned-addendum.tar.zst;effect:process;status:ok=6; process:du;effect:process;status:ok=6; process:ai-agent-traces-20260601-235658-pdt.tar.zst;effect:process;status:ok=5` |
| `eval` | 273 | 16.85% | 24 | `process:python3;effect:process;status:ok=46; process:sed;effect:read;status:ok=45; process:find;effect:read;status:ok=31; process:rg;effect:read;status:ok=22; process:tool:tool;effect:process;status:ok=21; process:cat;effect:read;status:ok=20; process:tool:tool;effect:process;status:observed=15; process:du;effect:process;status:ok=14` |

## Claim Boundary

R251 is useful because it falsifies the weakest version of the tagging story: prompt tags are not treated as adequate merely because they are one-word strings. The run checks whether prompt tags retain behavior information beyond session membership under a session-preserving null. It still cannot decide whether a human developer would call each tag semantically correct; that requires the R124 label-return path.
