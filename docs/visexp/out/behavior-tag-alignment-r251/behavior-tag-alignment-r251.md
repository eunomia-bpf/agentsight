# R251 Behavior-Tag Association

Status: `behavior_association_supported`

## Provenance

| field | value |
|---|---|
| repo commit | `c7cad77d094f9aca260d076ae3c1a0f76b4ec32e` |
| repo dirty | `False` |
| provenance semantics | `repo commit` is the clean source tree used to generate this report; a later commit may contain the generated report itself. |
| source run | `R170` / `full_history_refresh_passed` |
| source summary | `docs/visexp/out/full-history-r170.json` |
| source summary sha256 | `7162bcdd8c9e9bb21cfe82816cd8f230181da8484103411d25dc316dc9e757c6` |
| source repo dirty | `True` |
| folded stack | `.agentsight/agentflame/r170-full-current/semantic-system.folded.txt` |
| folded sha256 | `350d716412792826368e9778d153ac7cbe7a717b7280c40b32f71ba8b6d1789d` |
| seed | `251` |
| permutations | `1000` |
| p-value resolution | `0.000999` |
| privacy scan passed | `True` |
| privacy scan hits | `0` |
| privacy scope | Pattern-based redaction/scan for paths, archive names, timestamped artifacts, and private-looking labels; not full de-identification. |

## Boundary

- Reads generated R170 semantic folded stacks only.
- Does not read raw agent histories.
- Does not call an LLM.
- Does not add human labels or user responses.
- Reports a weighted behavior-association proxy only; C6 human semantic adequacy remains unsupported.
- The randomization p-values are over expanded system-effect weights, not independent session samples.

## Main Metrics

| metric | value |
|---|---:|
| total system-effect weight | 183714 |
| stack rows | 26829 |
| prompt tags with system effects | 263 |
| session tags | 53 |
| behavior keys | 882 |
| redacted behavior row weight | 373 |
| behavior entropy | 4.928 bits |
| prompt uncertainty reduction | 10.463% |
| prompt gain beyond session | 8.419% |
| prompt top-behavior purity | 20.196% |

## Session-Preserving Null

| metric | actual | null p95 | p value | pass p95 |
|---|---:|---:|---:|---|
| `prompt_gain_beyond_session_pct` | 8.419 | 1.903 | 0.0010 | True |
| `prompt_top_behavior_purity_pct` | 20.196 | 18.367 | 0.0010 | True |

Interpretation: the null preserves session membership and breaks only the
prompt-to-behavior assignment within each session. Passing this screen says
that prompt tags carry behavior information beyond session identity. It is
not a test of whether humans would choose the same tag.


## Top Prompt Profiles

| prompt | weight | top behavior | top share | distinct behaviors |
|---|---:|---|---:|---:|
| `refactor` | 73162 | `process:rg;effect:read;status:ok` | 18.985% | 491 |
| `review` | 33267 | `process:rg;effect:read;status:ok` | 20.474% | 346 |
| `design` | 15705 | `process:rg;effect:read;status:ok` | 18.606% | 195 |
| `analyze` | 11457 | `process:docker;effect:process;status:ok` | 10.98% | 143 |
| `test` | 8012 | `process:sed;effect:read;status:ok` | 15.14% | 225 |
| `research` | 4736 | `process:sed;effect:read;status:ok` | 19.637% | 146 |
| `benchmark` | 4033 | `process:sed;effect:read;status:ok` | 24.82% | 78 |
| `docs` | 3477 | `process:rg;effect:read;status:ok` | 15.243% | 124 |
| `debug` | 1587 | `process:rg;effect:read;status:ok` | 22.18% | 75 |
| `explain` | 1463 | `process:git;effect:read;status:ok` | 19.891% | 51 |

## Low-Coherence Review Queue

| prompt | weight | top share | distinct behaviors | top behaviors |
|---|---:|---:|---:|---|
| `analyze` | 11457 | 10.98% | 143 | `process:docker;effect:process;status:ok=1258; process:sed;effect:read;status:ok=1153; process:tail;effect:read;status:ok=993; process:rg;effect:read;status:ok=981; process:tool:tool;effect:process;status:observed=798; process:tool:tool;effect:process;status:ok=797; process:python3;effect:process;status:ok=773; process:git;effect:read;status:ok=685` |
| `branding` | 509 | 11.788% | 63 | `process:git;effect:read;status:ok=60; process:gh;effect:process;status:ok=58; process:sed;effect:read;status:ok=58; process:tool:tool;effect:process;status:ok=27; process:tool:tool;effect:process;status:observed=26; process:find;effect:read;status:ok=25; process:git;effect:repo;status:ok=24; process:rg;effect:read;status:ok=17` |
| `build` | 724 | 12.707% | 54 | `process:cd;effect:process;status:ok=92; process:git;effect:read;status:ok=91; process:tool:edit;effect:process;status:ok=76; process:rg;effect:read;status:ok=71; process:find;effect:read;status:ok=58; process:sed;effect:read;status:ok=44; process:tool:read;effect:process;status:ok=43; process:grep;effect:read;status:ok=25` |
| `docgen` | 131 | 12.977% | 22 | `process:python3;effect:process;status:ok=17; process:cargo;effect:process;status:ok=16; process:rg;effect:read;status:ok=13; process:find;effect:read;status:ok=10; process:git;effect:read;status:ok=10; process:jq;effect:read;status:ok=10; process:sed;effect:read;status:ok=8; process:head;effect:read;status:ok=6` |
| `todo` | 292 | 15.068% | 28 | `process:tool:tool;effect:process;status:ok=44; process:sed;effect:read;status:ok=38; process:rg;effect:read;status:ok=37; process:git;effect:read;status:ok=36; process:actplane;effect:process;status:ok=16; process:cargo;effect:test;status:ok=13; process:actplane;effect:process;status:observed=12; process:rm;effect:write;status:ok=12` |
| `test` | 8012 | 15.14% | 225 | `process:sed;effect:read;status:ok=1213; process:rg;effect:read;status:ok=911; process:git;effect:read;status:ok=781; process:tool:tool;effect:process;status:ok=601; process:tool:tool;effect:process;status:observed=521; process:find;effect:read;status:ok=359; process:python3;effect:process;status:ok=227; process:tail;effect:read;status:ok=213` |
| `docs` | 3477 | 15.243% | 124 | `process:rg;effect:read;status:ok=530; process:sed;effect:read;status:ok=494; process:git;effect:read;status:ok=365; process:nl;effect:read;status:ok=208; process:cd;effect:process;status:ok=118; process:tool:tool;effect:process;status:ok=118; process:python3;effect:process;status:ok=107; process:tool:read;effect:process;status:ok=105` |
| `install` | 151 | 15.894% | 25 | `process:git;effect:read;status:ok=24; process:sed;effect:read;status:ok=24; process:tool:tool;effect:process;status:observed=21; process:rg;effect:read;status:ok=13; process:gh;effect:process;status:ok=11; process:tool:tool;effect:process;status:ok=7; process:rm;effect:write;status:fail=6; process:cargo;effect:test;status:ok=5` |
| `backup` | 116 | 16.379% | 25 | `process:find;effect:read;status:ok=19; process:jq;effect:read;status:ok=19; process:local-artifact;effect:process;status:ok=18; process:tool:tool;effect:process;status:ok=10; process:f_find;effect:process;status:ok=8; process:du;effect:process;status:ok=6; process:cd;effect:process;status:ok=4; process:tar;effect:process;status:ok=4` |
| `eval` | 273 | 16.85% | 24 | `process:python3;effect:process;status:ok=46; process:sed;effect:read;status:ok=45; process:find;effect:read;status:ok=31; process:rg;effect:read;status:ok=22; process:tool:tool;effect:process;status:ok=21; process:cat;effect:read;status:ok=20; process:tool:tool;effect:process;status:observed=15; process:du;effect:process;status:ok=14` |

## Claim Boundary

R251 is useful as a session-preserving weighted association screen. It does not treat prompt tags as adequate merely because they are one-word strings; instead, it checks whether prompt tags retain behavior information beyond session membership under a session-preserving null. It still cannot decide whether a human developer would call each tag semantically correct; that requires the R124 label-return path.
