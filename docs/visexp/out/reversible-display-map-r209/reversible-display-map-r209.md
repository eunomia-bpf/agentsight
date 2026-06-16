# R209 Reversible Display Map

Status: `reversible_display_map_ready_no_map_update`

## Scope

- Reads generated R196/R203/R205 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not update the canonical map.
- Active display tags apply only deterministic R189 alias overlays.
- R189 lexical/profile merges and regenerated tags remain candidate labels unless a future reviewed diff promotes them.
- The drilldown CSV stores the complete raw-tag membership for each display bucket.

## Reversibility Checks

| check | value |
|---|---:|
| raw tag rows | 1811 |
| display map rows | 1811 |
| active display labels | 1509 |
| active merge rows | 63 |
| candidate rows | 209 |
| pending merge candidate rows | 168 |
| regenerated candidate rows | 41 |
| alias active rows | 63 |
| reviewed diff rows | 0 |
| raw coverage complete | True |
| drilldown support preserved | True |
| drilldown raw tags complete | True |
| hidden `other` rows | 0 |
| review-required support pct | 1.926 |

## Top Display Buckets

| dimension | display tag | support | raw tags | review support pct | top processes/effects |
|---|---|---:|---:|---:|---|
| session | `refactor` | 89914 | 1 | 0.0 | tool/tool=17836; sed=17136; rg=17101; git=5472; find=3754; python3=3500 |
| prompt | `refactor` | 73162 | 1 | 0.0 | rg=14677; sed=13638; tool/tool=11579; git=5966; find=2863; python3=2564 |
| llm | `refactor` | 41263 | 1 | 0.0 | refactor=18703601454726; benchmark=3022923252979; test=1576962068731; design=1571913627659; debug=365729985299; analyze=339497241823 |
| prompt | `review` | 33267 | 1 | 0.0 | rg=7176; sed=5012; git=4067; nl=2959; tool/tool=2176; find=1347 |
| session | `review` | 29164 | 1 | 0.0 | rg=5715; git=4767; sed=3451; nl=2226; cd=1227; cargo=1209 |
| session | `design` | 25434 | 1 | 0.0 | rg=5976; sed=4984; git=3224; nl=1446; find=1424; tool/tool=1140 |
| llm | `analyze` | 18713 | 2 | 0.0 | analyze=2023768216390; design=171634464620; tag=89788483023; analyzesess=55370639115; review=19357209899; branching=13479812106; docs=37 |
| prompt | `design` | 16109 | 2 | 0.0 | rg=3257; sed=2942; tool/tool=2572; git=1015; find=836; make=432; nl=98; cargo=28 |
| session | `analyze` | 12433 | 1 | 0.0 | tool/tool=1647; python3=1334; docker=1326; sed=1212; rg=1189; git=1093 |
| session | `research` | 11891 | 1 | 0.0 | sed=2009; git=1936; rg=1856; cargo=1320; tool/tool=740; python3=570 |
| prompt | `analyze` | 11460 | 2 | 0.0 | tool/tool=1683; docker=1294; python3=1178; sed=1154; rg=1068; tail=997 |
| llm | `design` | 9592 | 1 | 0.0 | review=265105638758; design=192828433349; refactor=99999540270; test=32636535064; research=31178247284; designcodex=20555081723 |
| llm | `test` | 9192 | 4 | 0.0 | refactor=16872277572; testcodex=8300797894; review=7320762161; trace=4205758292; diffpatch=2760030488; testrewrite=2042924363; smoketest=27714; research=84 |
| prompt | `test` | 8095 | 3 | 0.0 | sed=1230; tool/tool=1203; rg=980; git=916; find=361; python3=310; cargo=16; bash=6 |
| llm | `tokenize` | 7402 | 1 | 0.0 | review=147698595506; refactor=133962715668; test=14590948618; trace=10713577094; feedback=8740201875; docs=7333977446 |
| llm | `report` | 6494 | 1 | 0.0 | research=569048930420; commitlog=462112440758; refactor=376782499248; explain=72767463761; review=31517791297; test=22721780090 |
| llm | `review` | 5248 | 1 | 0.0 | review=13570669476; refactor=6655678383; docs=1640922844; merge=574123596; procfs=452010463; log=398643775 |
| session | `test` | 5192 | 2 | 0.0 | git=1094; sed=860; rg=764; tool/tool=418; find=276; python3=266; printf=2 |
| prompt | `docs` | 4859 | 15 | 0.0 | rg=804; sed=729; git=638; tool/tool=449; nl=252; python3=180; find=43; python=39 |
| prompt | `research` | 4736 | 1 | 0.0 | sed=937; rg=716; git=703; cargo=366; python3=252; tool/tool=246 |
| prompt | `benchmark` | 4050 | 2 | 0.0 | sed=1012; tool/tool=994; rg=829; find=168; nl=112; cargo=105; python3=3; ls=1 |
| llm | `docs` | 3519 | 12 | 0.0 | docs=24352123126; test=8525880300; docsanalyze=6108071239; codex=5059187265; analyze=3211785478; testdocs=2787237820; summary=146715413; docsupdate=142370633 |
| session | `docs` | 3392 | 3 | 0.0 | rg=574; sed=464; git=340; tool/tool=278; nl=268; python3=190; opencode=14; tool/plan=2 |
| llm | `debug` | 1959 | 5 | 0.0 | trace=271124795; hint=236888631; test=206254335; match=138609945; config=137545515; review=106838098; refactor=1543533; debug=921994 |
| prompt | `debug` | 1587 | 1 | 0.0 | rg=354; tool/tool=314; sed=295; git=90; python3=80; nl=49 |

## Claim Boundary

R209 supports a concrete UI/data contract for reversible compaction: every raw tag has one active display row and every display bucket has a raw-tag drilldown. It does not prove tag adequacy, merge quality, regenerated-tag quality, or developer utility. Those claims still require R124/R190/R203 human labels and R142/R151 developer-task results.
