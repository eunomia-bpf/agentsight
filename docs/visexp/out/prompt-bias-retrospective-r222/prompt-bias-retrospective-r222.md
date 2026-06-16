# R222 Prompt Bias Retrospective

Generated: `2026-06-16T07:35:52+00:00`

R222 does not call an LLM. It checks whether existing old artifacts can support a prefer-list vs no-prefer comparison.

## Verdict

- Same-fragment old/new comparison available: `False`
- Shared prompt hashes: `0`
- Current Rust prompt has prefer-list wording: `True`
- Legacy Python prompt has prefer-list wording: `False`
- Bias risk observed in existing distributions: `True`
- True ablation still required: `True`

## Distribution Signals

| source | model | dimension | total | unique | effective | top1 | top1 % | review+refactor % | top tags |
|---|---:|---|---:|---:|---:|---|---:|---:|---|
| legacy_python_no_prefer_artifact | sample36 | prompt | 37 | 10 | 8.568 | reviewdoc | 18.919 | 5.405 | reviewdoc=7; readcheck=5; readline=5; readfile=5; readmd=5; prompt=4; reviewreq=2; review=2; auditdoc=1; reviewcode=1 |
| r170_tag_counts | r170_prefer_list | session_tag_by_sessions | 325 | 60 | 19.492 | review | 25.231 | 42.462 | review=82; refactor=56; docs=24; design=16; analyze=15; countlines=11; test=9; research=8; agentsightsm=8; coda=7; rootpidrefsc=5; docsupdate=5 |
| r170_tag_counts | r170_prefer_list | prompt_tag_by_prompt_rows | 2859 | 328 | 25.463 | refactor | 31.445 | 47.114 | refactor=899; review=448; analyze=200; design=124; docs=123; test=122; research=82; trace=53; testcodex=28; evaluate=26; validate=22; docsupdate=21 |
| r170_tag_counts | r170_prefer_list | llm_tag_by_llm_events | 114837 | 1423 | 11.652 | refactor | 35.932 | 40.502 | refactor=41263; analyze=18712; design=9592; test=9184; tokenize=7402; report=6494; review=5248; docs=3335; debug=1816; build=1432; research=1068; trace=566 |
| r170_tag_counts | r170_prefer_list | prompt_tag_by_system_effect_weight | 183714 | 263 | 11.881 | refactor | 39.824 | 57.932 | refactor=73162; review=33267; design=15705; analyze=11457; test=8012; research=4736; benchmark=4033; docs=3477; debug=1587; explain=1463; trace=1401; commitlog=1361 |
| r170_tag_counts | r170_prefer_list | llm_tag_by_estimated_tokens | 31805830937139 | 1423 | 1.957 | refactor | 83.575 | 83.659 | refactor=26581785501743; analyze=2392003375156; report=1575116380919; design=687595970247; tokenize=353773329489; docs=64181339368; test=63155433342; updateplan=42403496860; review=26623264835; research=12077660372; uxdesign=4071308666; debug=1138969674 |
| r180_model_runs | 0.6b | all_fragments | 900 | 48 | 8.744 | debug | 52.444 | 6.333 | debug=472; docs=78; review=54; render=51; build=39; research=24; root=12; trace=12; repo=9; run=9; paper=6; baseline=6 |
| r180_model_runs | 1.1b | all_fragments | 900 | 5 | 2.079 | localization | 71.333 | 0.0 | localization=642; localized=228; localsession=18; fragmentkind=9; localizedai=3 |
| r180_model_runs | 3b | all_fragments | 900 | 105 | 28.329 | review | 25.444 | 44.111 | review=229; refactor=168; test=57; design=34; docs=17; verify=15; trace=15; readdocs=12; analyze=12; build=11; cmt=9; claimid=9 |
| r122_candidate_modal_tags | 3b_modal_candidate | all | 300 | 98 | 27.399 | review | 25.333 | 44.333 | review=76; refactor=57; test=19; design=11; docs=6; verify=5; trace=5; rootpidcount=4; readdocs=4; analyze=4; build=4; cmt=3 |
| r122_candidate_modal_tags | 3b_modal_candidate | session | 100 | 34 | 17.65 | review | 26.0 | 43.0 | review=26; refactor=17; rootpidcount=4; readdocs=4; cmt=3; claimid=3; benchmarks=3; design=3; test=3; verify=3; paperagentfl=2; nextaction=2 |
| r122_candidate_modal_tags | 3b_modal_candidate | prompt | 100 | 44 | 21.163 | refactor | 22.0 | 41.0 | refactor=22; review=19; test=5; design=5; analyze=4; trace=4; audit=2; output=2; docs=2; bench=1; count=1; tag=1 |
| r122_candidate_modal_tags | 3b_modal_candidate | llm | 100 | 36 | 14.141 | review | 31.0 | 49.0 | review=31; refactor=18; test=11; design=3; build=3; check=2; docs=2; format=2; diff=1; verify=1; call=1; update=1 |

## Interpretation

- The old Python no-prefer artifact is not comparable to R170 by prompt hash; it is a different small sample.
- R180 already shows model/prompt concentration risks: 0.6B collapses heavily to `debug`, 1.1B collapses to `localization/localized`, and 3B concentrates on `review/refactor`.
- Existing data is enough to mark the prefer-list prompt as risky, but not enough to quantify the causal effect of the prefer-list itself.
- The next required experiment is a same-fragment R223 ablation: current prefer-list vs no-prefer vs anti-common no-prefer over the R122 300 redacted fragments.

Claim boundary: R222 is retrospective evidence only. It does not prove that removing the prefer-list improves adequacy.
