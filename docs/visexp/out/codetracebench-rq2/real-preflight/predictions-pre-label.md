# CodeTraceBench RQ2 Predictions (Pre-Label)

These scores were written before the runner projected `incorrect_stages`. They use only raw operations, public outcome/cohort metadata, and task-held-out reference profiles.

## `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-54ac67f0`

- Adapter: `miniswe-message-trajectory`
- Support: `agent-model-category` with 16 failed and 12 successful different-task references
- Public step count: 47

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> inspect | -0.0065992514282 | ls | -0.0450128045177 | explore | 0.0832129489789 |
| 2 | explore -> version-control | -0.0721649484536 | git | -0.0412371134021 | explore | 0.0832129489789 |
| 3 | explore -> inspect | -0.0065992514282 | ls | -0.0450128045177 | explore | 0.0832129489789 |
| 4 | explore -> inspect | -0.0065992514282 | cat | -0.0627913848578 | explore | 0.0832129489789 |
| 5 | explore -> inspect | -0.0065992514282 | ls | -0.0450128045177 | explore | 0.0832129489789 |
| 6 | explore -> search | 0.031551644888 | find | 0.0127388535032 | explore | 0.0832129489789 |
| 7 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 8 | change -> install | -0.0580471468908 | pip | -0.0142491299494 | change | -0.0832129489789 |
| 9 | explore -> inspect | -0.0065992514282 | python3 | 0.0342767089106 | explore | 0.0832129489789 |
| 10 | explore -> execute | 0.0527447632806 | python3 | 0.0342767089106 | explore | 0.0832129489789 |
| 11 | explore -> inspect | -0.0065992514282 | ls | -0.0450128045177 | explore | 0.0832129489789 |
| 12 | explore -> inspect | -0.0065992514282 | cat | -0.0627913848578 | explore | 0.0832129489789 |
| 13 | explore -> inspect | -0.0065992514282 | cat | -0.0627913848578 | explore | 0.0832129489789 |
| 14 | explore -> inspect | -0.0065992514282 | head | 0.0127388535032 | explore | 0.0832129489789 |
| 15 | explore -> inspect | -0.0065992514282 | cat | -0.0627913848578 | explore | 0.0832129489789 |
| 16 | change -> install | -0.0580471468908 | apt | -0.00431742071049 | change | -0.0832129489789 |
| 17 | change -> install | -0.0580471468908 | apt | -0.00431742071049 | change | -0.0832129489789 |
| 18 | explore -> inspect | -0.0065992514282 | python3 | 0.0342767089106 | explore | 0.0832129489789 |
| 19 | explore -> search | 0.031551644888 | find | 0.0127388535032 | explore | 0.0832129489789 |
| 20 | explore -> inspect | -0.0065992514282 | head | 0.0127388535032 | explore | 0.0832129489789 |
| 21 | explore -> inspect | -0.0065992514282 | cat | -0.0627913848578 | explore | 0.0832129489789 |
| 22 | explore -> search | 0.031551644888 | find | 0.0127388535032 | explore | 0.0832129489789 |
| 23 | explore -> version-control | -0.0721649484536 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 24 | change -> version-control | -0.0261507649879 | cd | 0.156707597347 | change | -0.0832129489789 |
| 25 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 26 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 27 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 28 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 29 | change -> install | -0.0580471468908 | 60 | 0 | change | -0.0832129489789 |
| 30 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 31 | explore -> inspect | -0.0065992514282 | col_name | 0 | explore | 0.0832129489789 |
| 32 | explore -> search | 0.031551644888 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 33 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 34 | explore -> inspect | -0.0065992514282 | col_name | 0 | explore | 0.0832129489789 |
| 35 | explore -> version-control | -0.0721649484536 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 36 | explore -> version-control | -0.0721649484536 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 37 | explore -> inspect | -0.0065992514282 | col_name | 0 | explore | 0.0832129489789 |
| 38 | change -> inspect | -0.000295488869919 | i | -0.00234749491103 | change | -0.0832129489789 |
| 39 | change -> install | -0.0580471468908 | cd | 0.156707597347 | change | -0.0832129489789 |
| 40 | change -> edit | -0.0407446319522 | cd | 0.156707597347 | change | -0.0832129489789 |
| 41 | explore -> edit | 0.0941132050693 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 42 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 43 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 44 | change -> install | -0.0580471468908 | pip | -0.0142491299494 | change | -0.0832129489789 |
| 45 | explore -> inspect | -0.0065992514282 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 46 | explore -> communicate | -0.0331932497209 | cd | 0.156707597347 | explore | 0.0832129489789 |
| 47 | explore -> communicate | -0.0331932497209 | echo | -0.115667476525 | explore | 0.0832129489789 |

## `miniswe-OpenAI__GPT-5-astropy__astropy-14598-416c95db`

- Adapter: `miniswe-message-trajectory`
- Support: `agent-model-category` with 51 failed and 146 successful different-task references
- Public step count: 26

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> search | -0.0103763887091 | cd | -0.0560714856808 | explore | 0.000536066460058 |
| 2 | explore -> search | -0.0103763887091 | cd | -0.0560714856808 | explore | 0.000536066460058 |
| 3 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 4 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 5 | explore -> search | -0.0103763887091 | grep | 0.0157857866242 | explore | 0.000536066460058 |
| 6 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 7 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 8 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 9 | explore -> inspect | 0.00703358791414 | python | 0.0230310598734 | explore | 0.000536066460058 |
| 10 | change -> inspect | -0.0170178257327 | applypatch | 0.00283795411454 | change | -0.000536066460058 |
| 11 | change -> search | 0.0183275335613 | i | 0.0145111058655 | change | -0.000536066460058 |
| 12 | change -> search | 0.0183275335613 | i | 0.0145111058655 | change | -0.000536066460058 |
| 13 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 14 | explore -> inspect | 0.00703358791414 | sed | -0.024685708194 | explore | 0.000536066460058 |
| 15 | explore -> execute | 0.00821080204375 | python | 0.0230310598734 | explore | 0.000536066460058 |
| 16 | change -> inspect | -0.0170178257327 | i | 0.0145111058655 | change | -0.000536066460058 |
| 17 | explore -> execute | 0.00821080204375 | python | 0.0230310598734 | explore | 0.000536066460058 |
| 18 | change -> inspect | -0.0170178257327 | i | 0.0145111058655 | change | -0.000536066460058 |
| 19 | change -> inspect | -0.0170178257327 | i | 0.0145111058655 | change | -0.000536066460058 |
| 20 | explore -> inspect | 0.00703358791414 | cd | -0.0560714856808 | explore | 0.000536066460058 |
| 21 | change -> edit | -0.00380043707691 | sed | -0.024685708194 | change | -0.000536066460058 |
| 22 | change -> inspect | -0.0170178257327 | i | 0.0145111058655 | change | -0.000536066460058 |
| 23 | explore -> execute | 0.00821080204375 | python | 0.0230310598734 | explore | 0.000536066460058 |
| 24 | change -> search | 0.0183275335613 | i | 0.0145111058655 | change | -0.000536066460058 |
| 25 | change -> communicate | -0.0218310020026 | echo | -0.015971582386 | change | -0.000536066460058 |
| 26 | change -> communicate | -0.0218310020026 | echo | -0.015971582386 | change | -0.000536066460058 |

## `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-7498555b`

- Adapter: `openhands-agent-actions`
- Support: `agent-model-category` with 26 failed and 14 successful different-task references
- Public step count: 95

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 2 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 3 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 4 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 5 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 6 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 7 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 8 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 9 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 10 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 11 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 12 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 13 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 14 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 15 | change -> execute | -0.0390017335558 | think | -0.00314656723253 | change | -0.0723448794688 |
| 16 | change -> inspect | -0.00619500866778 | run | -0.101893827887 | change | -0.0723448794688 |
| 17 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 18 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 19 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 20 | change -> edit | -0.0054100022896 | run | -0.101893827887 | change | -0.0723448794688 |
| 21 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 22 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 23 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 24 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 25 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 26 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 27 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 28 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 29 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 30 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 31 | change -> edit | -0.0054100022896 | run | -0.101893827887 | change | -0.0723448794688 |
| 32 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 33 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 34 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 35 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 36 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 37 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 38 | change -> inspect | -0.00619500866778 | read | -0.0158832957184 | change | -0.0723448794688 |
| 39 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 40 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 41 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 42 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 43 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 44 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 45 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 46 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 47 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 48 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 49 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 50 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 51 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 52 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 53 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 54 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 55 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 56 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 57 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 58 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 59 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 60 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 61 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 62 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 63 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 64 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 65 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 66 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 67 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 68 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 69 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 70 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 71 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 72 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 73 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 74 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 75 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 76 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 77 | explore -> search | 0.00326431818925 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 78 | explore -> inspect | -0.0773427534099 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 79 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 80 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 81 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 82 | explore -> search | 0.00326431818925 | read | -0.0158832957184 | explore | 0.0723448794688 |
| 83 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 84 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 85 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 86 | change -> test | -0.00253164556962 | run | -0.101893827887 | change | -0.0723448794688 |
| 87 | explore -> edit | 0.160023550191 | edit | 0.160023550191 | explore | 0.0723448794688 |
| 88 | change -> execute | -0.0390017335558 | run | -0.101893827887 | change | -0.0723448794688 |
| 89 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 90 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 91 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 92 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 93 | explore -> inspect | -0.0773427534099 | run | -0.101893827887 | explore | 0.0723448794688 |
| 94 | explore -> execute | 0.0311909200929 | run | -0.101893827887 | explore | 0.0723448794688 |
| 95 | change -> inspect | -0.00619500866778 | finish | -0.0230399371995 | change | -0.0723448794688 |

## `openhands-OpenAI__GPT-5-astropy__astropy-13398-3106f9b1`

- Adapter: `openhands-maximal-visible-action-context`
- Support: `agent-model-difficulty-category` with 40 failed and 32 successful different-task references
- Public step count: 48

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> execute | -0.0161642614772 | task_tracker | -0.0102243382533 | explore | -0.0008839117111 |
| 2 | explore -> execute | -0.0161642614772 | task_tracker | -0.0102243382533 | explore | -0.0008839117111 |
| 3 | explore -> execute | -0.0161642614772 | task_tracker | -0.0102243382533 | explore | -0.0008839117111 |
| 4 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 5 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 6 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 7 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 8 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 9 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 10 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 11 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 12 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 13 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 14 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 15 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 16 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 17 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 18 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 19 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 20 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 21 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 22 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 23 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 24 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 25 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 26 | explore -> edit | -0.0314044334382 | str_replace_editor | -0.00465879912193 | explore | -0.0008839117111 |
| 27 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 28 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 29 | explore -> edit | -0.0314044334382 | str_replace_editor | -0.00465879912193 | explore | -0.0008839117111 |
| 30 | explore -> execute | -0.0161642614772 | task_tracker | -0.0102243382533 | explore | -0.0008839117111 |
| 31 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 32 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 33 | explore -> execute | -0.0161642614772 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 34 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 35 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 36 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 37 | explore -> execute | -0.0161642614772 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 38 | explore -> edit | -0.0314044334382 | str_replace_editor | -0.00465879912193 | explore | -0.0008839117111 |
| 39 | explore -> execute | -0.0161642614772 | task_tracker | -0.0102243382533 | explore | -0.0008839117111 |
| 40 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 41 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 42 | explore -> search | 0.0543852247948 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 43 | explore -> inspect | -0.0192515605425 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 44 | explore -> edit | -0.0314044334382 | str_replace_editor | -0.00465879912193 | explore | -0.0008839117111 |
| 45 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 46 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 47 | explore -> test | 0.00730322919977 | execute_bash | 0.0160181603679 | explore | -0.0008839117111 |
| 48 | explore -> edit | -0.0314044334382 | str_replace_editor | -0.00465879912193 | explore | -0.0008839117111 |

## `sweagent-OpenAI__GPT-5-Significant-Gravitas__AutoGPT-4652-b968024b`

- Adapter: `sweagent-trajectory-elements`
- Support: `agent-model-category` with 27 failed and 94 successful different-task references
- Public step count: 32

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 2 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 3 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 4 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 5 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 6 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 7 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 8 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 9 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 10 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 11 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 12 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 13 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 14 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 15 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 16 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 17 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 18 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 19 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 20 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 21 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 22 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 23 | explore -> edit | 0.0507316995239 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 24 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 25 | explore -> inspect | 0.0501432512168 | str_replace_editor | -0.023860114388 | explore | 8.25425227124e-05 |
| 26 | change -> edit | -0.0130763331949 | str_replace_editor | -0.023860114388 | change | -8.25425227125e-05 |
| 27 | change -> execute | 0.00550904772555 | python | 0.0206835585945 | change | -8.25425227125e-05 |
| 28 | explore -> other | 0.00921281059952 | other | 0.00921281059952 | explore | 8.25425227124e-05 |
| 29 | explore -> execute | -0.24356434589 | submit | -0.0110846620017 | explore | 8.25425227124e-05 |
| 30 | explore -> execute | -0.24356434589 | submit | -0.0110846620017 | explore | 8.25425227124e-05 |
| 31 | explore -> other | 0.00921281059952 | other | 0.00921281059952 | explore | 8.25425227124e-05 |
| 32 | explore -> execute | -0.24356434589 | submit | -0.0110846620017 | explore | 8.25425227124e-05 |

## `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-accelerate-maximal-square-eca249fc`

- Adapter: `terminus2-commands-txt-strings`
- Support: `agent-model` with 56 failed and 42 successful different-task references
- Public step count: 22

| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |
|---:|---|---:|---|---:|---|---:|
| 1 | explore -> inspect | -0.100003936969 | ls | -0.0532069566244 | explore | -0.160364760189 |
| 2 | change -> edit | 0.193205381837 | mkdir | -0.0023306857216 | change | 0.160364760189 |
| 3 | explore -> execute | -0.0223657247468 | cd | -0.00741941516324 | explore | -0.160364760189 |
| 4 | change -> edit | 0.193205381837 | j | -0.0022641509434 | change | 0.160364760189 |
| 5 | explore -> inspect | -0.100003936969 | ls | -0.0532069566244 | explore | -0.160364760189 |
| 6 | explore -> inspect | -0.100003936969 | cat | -0.023828111928 | explore | -0.160364760189 |
| 7 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 8 | change -> edit | 0.193205381837 | cat | -0.023828111928 | change | 0.160364760189 |
| 9 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 10 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 11 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 12 | change -> edit | 0.193205381837 | cat | -0.023828111928 | change | 0.160364760189 |
| 13 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 14 | change -> edit | 0.193205381837 | j | -0.0022641509434 | change | 0.160364760189 |
| 15 | explore -> inspect | -0.100003936969 | cat | -0.023828111928 | explore | -0.160364760189 |
| 16 | change -> edit | 0.193205381837 | cat | -0.023828111928 | change | 0.160364760189 |
| 17 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 18 | change -> edit | 0.193205381837 | cat | -0.023828111928 | change | 0.160364760189 |
| 19 | explore -> execute | -0.0223657247468 | python3 | -0.0477129162115 | explore | -0.160364760189 |
| 20 | change -> edit | 0.193205381837 | rm | 0.00366827098158 | change | 0.160364760189 |
| 21 | explore -> inspect | -0.100003936969 | ls | -0.0532069566244 | explore | -0.160364760189 |
| 22 | explore -> execute | -0.0223657247468 | echo | 0.144369642031 | explore | -0.160364760189 |
