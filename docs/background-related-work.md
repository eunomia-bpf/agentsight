# Background And Related Work

Last updated: 2026-07-03
Stage at update: stage 1 novelty / stage 3 design bridge
Source/command: primary-source web search, PDF download to `docs/reference/`, HF Dataset Viewer checks
Completeness: partial

## Search Log

| Date | Query/source | Purpose | Result |
|---|---|---|---|
| 2026-07-03 | `Mind2Web dataset web agent trajectories annotated actions official GitHub Hugging Face` | Find labeled web-agent action traces | Primary project page, arXiv paper, GitHub, and HF dataset found. |
| 2026-07-03 | `WebLINX dataset web navigation demonstrations official GitHub Hugging Face` | Find expert web navigation demonstrations | Primary project page, GitHub, arXiv/PMLR paper, and HF dataset found. |
| 2026-07-03 | `AndroidControl dataset Google Research agent demonstrations` | Find labeled mobile control demonstrations | Google Research GitHub README and arXiv paper found; HF mirrors exist but viewer row groups are too large for lightweight rows API. |
| 2026-07-03 | `Android in the Wild dataset device control human demonstrations` | Find larger mobile-control oracle | Google Research publication and official google-research release found. |
| 2026-07-03 | `ToolBench ToolLLM official paper GitHub dataset` | Find tool-use action/reasoning traces | Official OpenBMB GitHub and paper found; release is hosted outside HF Dataset Viewer. |
| 2026-07-03 | `WebShop dataset expert demonstrations action trajectories official GitHub` | Find web-shopping human/expert trajectories | Official project and HF mirror with expert trajectories found; sampled in R273. |
| 2026-07-03 | `API-Bank tool use dataset API calls official GitHub Hugging Face` | Find gold API-call trajectories | HF mirror and official repo found; sampled 48 first rows in R273. |
| 2026-07-03 | `AgentTrek web trajectory synthesis dataset Hugging Face official` | Find large GUI/web trajectory source | Official project and HF dataset found; sampled in R273. |
| 2026-07-03 | `SWE-agent trajectories dataset Hugging Face` | Find software-engineering agent trajectories | HF dataset with 80K SWE-agent trajectories found; sampled in R273. |
| 2026-07-03 | `TRAIL trace reasoning agentic issue localization dataset annotated traces` | Find human-annotated failure traces | Official GitHub/HF gated dataset and paper found; access requires accepted HF gate. |
| 2026-07-03 | `GUI Odyssey dataset agent trajectories annotated actions Hugging Face` | Find large cross-app mobile GUI traces | Official GitHub, arXiv/ICCV 2025 paper, and HF dataset found; sampled 500 episodes in R279. |
| 2026-07-03 | `AGUVIS stage2 dataset agent trajectories xlangai aguvis-stage2 Hugging Face official GitHub` | Find additional cross-platform GUI trajectory training data | Official AGUVIS GitHub/project and HF `xlangai/aguvis-stage2` found; candidate for a larger mobile/desktop/web converter. |
| 2026-07-03 | `OSWorld verified trajectories Hugging Face ubuntu_osworld_verified_trajs official` | Find desktop/computer-use evaluation trajectories | Official OSWorld page says verified trajectories are hosted on HF; `xlangai/ubuntu_osworld_verified_trajs` found as a candidate desktop trajectory source. |
| 2026-07-03 | `BrowserGym WorkArena web agent benchmark trajectories official GitHub` | Find enterprise/browser workflow benchmark sources | Official BrowserGym and WorkArena repositories/pages found; useful benchmark environment, but not yet a lightweight labeled trajectory source in this repo. |
| 2026-07-03 | `PC Agent-E OS-Genesis agent trajectories dataset official GitHub Hugging Face` | Find newer computer-use trajectory corpora | PC Agent-E and OS-Genesis official repos/pages found; candidates for later trajectory conversion and scale comparison. |
| 2026-07-03 | `2025 2026 GUI agent trajectory dataset Mobile-R1 MobilityBench SATraj-OS Hugging Face` | Find newer large GUI/computer-use trajectory corpora | HF `AI45Research/SATraj-OS` found as a large-scale OSWorld GUI trajectory dataset; `PG23/Mobile-R1` reports 24,521 manually annotated instances from 4,635 mobile trajectories and an open 1,007-trajectory sample. |
| 2026-07-03 | `xlangai AgentNet desktop computer-use trajectory dataset human annotated` | Find desktop human-annotated computer-use trajectories | HF `xlangai/AgentNet` found; dataset card reports 22.6K human-annotated desktop computer-use tasks across Windows, macOS, and Ubuntu. |

## PDF Corpus

| Work | Local PDF path | Verification status | Why kept |
|---|---|---|---|
| Mind2Web | `docs/reference/2023-deng-mind2web.pdf` | arXiv / official project page | Web task descriptions and manually annotated action sequences are a direct oracle for operation-stack folding. |
| WebLINX | `docs/reference/2024-lu-weblinx.pdf` | PMLR asset / official project page | Expert web-navigation demonstrations provide action, turn, and demo-level structure. |
| AndroidControl | `docs/reference/2024-bishop-androidcontrol.pdf` | arXiv / Google Research repo | Mobile UI demonstrations include high-level goals, step instructions, screenshots, trees, and actions. |
| Android in the Wild | `docs/reference/2023-rawles-android-in-the-wild.pdf` | NeurIPS Datasets and Benchmarks / Google Research publication | Large-scale device-control oracle for robustness and generalization tests. |
| ToolLLM / ToolBench | `docs/reference/2023-qin-toolllm-toolbench.pdf` | Official OpenBMB GitHub asset | Tool-use paths and real API calls are the closest non-GUI oracle for operation stacks. |
| WebShop | `docs/reference/2022-yao-webshop.pdf` | NeurIPS proceedings / official project page | Human/expert web-shopping trajectories provide long action sequences with task rewards. |
| API-Bank | `docs/reference/2023-li-api-bank.pdf` | arXiv / official repo | Gold API requests provide a compact tool-use oracle. |
| AgentTrek | `docs/reference/2024-xu-agenttrek.pdf` | arXiv / official project page | Verified tutorial-guided GUI/web trajectories provide large-scale browser action traces. |
| SWE-agent | `docs/reference/2024-yang-swe-agent.pdf` | arXiv / HF dataset | Software-engineering trajectories test whether operation stacks generalize back to coding-agent behavior. |
| TRAIL | `docs/reference/2025-trail-trace-reasoning.pdf` | arXiv / official benchmark repo | Human annotated trace errors are a direct future oracle for boundary/failure analysis. |
| GUI-Odyssey | `docs/reference/2024-lu-gui-odyssey.pdf` | arXiv / official GitHub / HF dataset | Large cross-app mobile GUI episodes with annotated steps are a strong operation-stack oracle. |

## Claim-Oriented Novelty Map

| Claim | Closest prior work | Same-claim risk | Novelty delta | Baselines implied | Expansion opportunity |
|---|---|---|---|---|---|
| C1: AgentSight can profile agent behavior as operations and recursively folded operation stacks independent of prompt/session boundaries. | Mind2Web, WebLINX, GUI-Odyssey, AndroidControl, AITW, ToolBench | Medium | Prior datasets provide trajectories and labels, but not a profiler abstraction or pprof/flamegraph-compatible recursive folding over heterogeneous traces. | Flat action list, fixed prompt/session stack, dataset-native hierarchy, flat/fixed/mapped operation-stack ablation. | Show the same profiler handles local Codex/Claude traces, web demos, mobile demos, and tool-use traces by changing only operation fields and stack projection. |
| C2: Operation-stack folding can expose task/subtask/phase structure from linear event histories. | GUI-Odyssey step actions, WebLINX demos, Mind2Web action sequences, AndroidControl step instructions, ToolBench solution paths | Medium | Prior work uses labels to train/evaluate agents; our use is an observability/profile projection with explicit boundary and compression metrics. | Gold demo/session boundaries, action-type phase oracle, step-instruction oracle, solution-path oracle. | Add boundary adequacy metrics and compare deterministic operation mappings with inferred boundary rules. |

## Closest Work

| Work | Claim / data shape | Method/artifact | Evaluation | Same problem/mechanism/metric/setting? | Gap relative to this project |
|---|---|---|---|---|---|
| Mind2Web | Generalist web agents over real websites; official page reports 2,350 tasks, 137 websites, 31 domains, and action sequences with Click/Hover/Type/Select operations. Source: https://osu-nlp-group.github.io/Mind2Web/ | Project page, GitHub, HF training data, raw trace/snapshot dump; R274 sampled an HF repo JSON shard into operation JSONL. | Web action prediction and generalization across task/website/domain. | Same setting and oracle data; different mechanism and metric. | Good oracle for operation boundaries and action phases, but not an observability profiler; needs larger shard/raw-dump profiling before strong scale claims. |
| WebLINX | Conversational web navigation; official page reports 100K interactions over 2,300 expert demonstrations across 150+ websites. Source: https://mcgill-nlp.github.io/weblinx/ | HF dataset with chat/reranking configs, GitHub, BrowserGym integration. | Next-action prediction and generalization to held-out website/category/visual/geographic splits. | Same setting and action traces; different system goal. | Best first external smoke because HF Dataset Viewer rows are small enough to sample. |
| AndroidControl | Google Research repo reports 15K+ human demonstrations over 833 apps and 40 categories, with screenshots, accessibility trees, instructions, and JSON actions. Source: https://github.com/google-research/google-research/blob/master/android_control/README.md | Official TFRecord release plus HF mirrors; R278 sampled `smolagents/android-control` rows into operation JSONL. | Offline low-level/high-level action prediction and OOD app/task generalization. | Same operation-boundary problem in mobile setting. | Step instructions are a strong oracle for recursive folding depth; full-scale runs need heavier screenshot-aware download handling. |
| GUI-Odyssey | ArXiv reports 8,334 episodes with average 15.3 steps across 6 mobile devices, 212 apps, and 1,357 app combinations. Source: https://arxiv.org/abs/2406.08451 | Official GitHub and HF dataset; R279 sampled 500 episodes into 7,868 operations. | Cross-app mobile GUI navigation and OdysseyAgent evaluation. | Same operation-boundary problem in a large cross-app mobile setting. | Excellent current primary source for large-scale action-boundary scoring; does not itself provide a profiler or cross-dataset operation-stack abstraction. |
| Android in the Wild | Google Research page reports 715K episodes and 30K unique instructions with screens/actions/instructions. Source: https://research.google/pubs/android-in-the-wild-a-large-scale-dataset-for-android-device-control/ | Official google-research release. | Device-control generalization across instructions/apps/platform versions. | Same operation sequence setting, much larger scale. | Useful for scale/robustness after AndroidControl converter exists. |
| ToolBench / ToolLLM | Official GitHub reports 3,451 tools, 16,464 APIs, 126,486 instances, 469,585 real API calls, and reasoning traces. Source: https://github.com/OpenBMB/ToolBench | Official dataset, training/eval scripts, ToolLLaMA, ToolEval; R278 sampled the `tuandunghcmut/toolbench-v1` HF mirror into operation JSONL. | Tool-use instruction following and API-call success/preference. | Same tool-call setting; different UI domain. | Strong oracle for planner/tool/API call stack layers; lightweight HF sampling is available, while official full-dataset conversion remains pending. |
| WebShop | Official project reports 12,087 crowd-sourced instructions and over 1,600 human demonstrations. Source: https://webshop-pnlp.github.io/ | Simulated shopping environment plus HF expert trajectory mirror. | Web shopping success and imitation/RL baselines. | Same web-action sequence setting with long trajectories. | Excellent for operation-stack compression because each row expands to many expert actions. |
| API-Bank | API-call benchmark for tool-augmented dialogue agents. Source: https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank | Official repo plus HF mirror. | API request generation and tool-use evaluation. | Same tool-call setting, but mostly single-step per row. | Good compact baseline; weaker for recursive boundary claims than WebShop/WebLINX/SWE-agent. |
| AgentTrek | Tutorial-guided web trajectory synthesis with VLM verification. Source: https://agenttrek.github.io/ | Official project and HF dataset. | GUI/web agent training and online/offline benchmark transfer. | Same GUI action setting and large-scale trajectory source. | Useful large-scale web GUI source; labels are synthetic/verified rather than human. |
| SWE-agent trajectories | HF page reports 80,036 trajectories generated by a SWE-agent framework. Source: https://huggingface.co/datasets/nebius/SWE-agent-trajectories | HF Dataset Viewer rows with action/observation trajectory fields. | SWE-bench issue-solving trajectories. | Same software-agent setting with commands, observations, success flags. | Strong coding-agent external oracle and closest to AgentSight's target domain. |
| TRAIL | Official benchmark reports 148 annotated execution traces and 841 errors. Source: https://github.com/patronus-ai/trail-benchmark | Official repo and HF auto-gated dataset. | Trace reasoning and issue localization. | Same trace-debugging setting, with human failure annotations. | Very strong future oracle once access is accepted; not yet sampled because gated. |

## Mandatory Baselines

| Baseline | Why reviewer will expect it | Reproduction risk | Fairness notes | Required for claim |
|---|---|---|---|---|
| Dataset-native sequence view | Shows what the benchmark already gives without AgentSight profiling. | Low | Use identical sampled rows and no inferred frames. | C1, C2 |
| Fixed prompt/session stack | Tests the user's objection directly: prompt/session boundaries should not be privileged. | Low for local traces; N/A for many external datasets. | For external datasets, use demo/session as the fixed boundary analog. | C1 |
| Flat action-type aggregation | Checks whether recursive stack adds value beyond counting action classes. | Low | Same operations and weights; stack is only `dataset,action,status`. | C2 |
| Rule-free default stack | Measures cost of no domain-specific folding rules. | Low | Use same operation JSONL and default view stack. | C2 |
| Inferred boundary rules | Needed before claiming automatic boundary detection. | Medium | Keep deterministic `--op-map`/`--stack-rule` runs separate from inferred-rule runs. | Future C3 |

## Absorbable Ideas

| Source/community | Idea to absorb | Claim expansion enabled | Experiment implication | Risk |
|---|---|---|---|---|
| Web agent benchmarks | Held-out website/category/domain splits | Generalization of operation mappings across task distributions | Run train-derived rules on WebLINX test_web/test_cat and Mind2Web cross-domain splits. | Rules may overfit action schemas. |
| Mobile control datasets | Step instruction to action alignment | Boundary adequacy oracle deeper than action type | Score task/subtask/phase recovery against step instructions. | Large files and screenshot/tree dependencies. |
| Cross-app mobile datasets | App-combo and category labels | Larger, more realistic mobile operation-stack scope | Use GUI-Odyssey as primary mobile scale source and AndroidControl as step-instruction oracle. | GUI-Odyssey action boundaries are strong, but subtask labels are still coarser than ideal. |
| Tool-use benchmarks | Solution paths and real API calls | Non-GUI operation-stack support | Convert ToolBench answer/toolenv JSON into planner/tool/api frames. | Official data is outside HF viewer. |
| Desktop/computer-use benchmarks | Verified desktop trajectories and environment tasks | Extend operation-stack folding beyond web/mobile/API into real OS task execution | Add OSWorld-Verified and PC Agent-E/OS-Genesis converters once row formats are inspected. | Some sources are generated/model trajectories rather than human-demonstration labels. |
| Browser benchmark environments | BrowserGym and WorkArena task suites | Stronger held-out benchmark protocol for web-operation stacks | Use them as evaluation environments or trace-generation baselines after static labeled datasets are exhausted. | Environment setup may be heavier than Dataset Viewer sampling. |
| New GUI/computer-use trajectory corpora | SATraj-OS, AgentNet, Mobile-R1 | Move from 9-dataset breadth to larger desktop/mobile scale and human-annotated task variety | Inspect HF row formats and add lightweight converters after R282 held-out validation. | Dataset cards differ in whether trajectories are human, model-generated, or safety-oriented. |

## Must-Read List

| Priority | Work | Why |
|---|---|---|
| P0 | WebLINX paper and dataset docs | First sampled external oracle and immediate operation-file smoke. |
| P0 | Mind2Web paper and repo | Strong web action sequence oracle with raw traces and snapshots. |
| P1 | AndroidControl paper and README | Best mobile step-instruction oracle for recursive boundary tests. |
| P1 | ToolLLM / ToolBench paper and repo | Best tool-use oracle for non-GUI stack layers. |
| P2 | Android in the Wild | Scale/robustness after AndroidControl converter stabilizes. |
| P1 | WebShop | Long human/expert web trajectories with rewards; selected as a current top candidate. |
| P1 | SWE-agent trajectories | Large software-engineering trajectories; selected as a current top candidate. |
| P2 | AgentTrek | Large verified synthetic web GUI source; selected as a current top candidate if synthetic data is acceptable. |
| P2 | TRAIL | Human trace-error annotations; best future failure-boundary oracle after gated access. |
| P1 | GUI-Odyssey | Best current mobile/cross-app scale source; selected as a primary candidate after R279. |
| P2 | AGUVIS stage2 | Cross-platform GUI trajectory training data; likely useful after GUI-Odyssey/AndroidControl. |
| P2 | OSWorld-Verified trajectories | Desktop/computer-use verified trajectories; likely best next non-web/non-mobile expansion. |
| P2 | PC Agent-E / OS-Genesis | Newer computer-use trajectory corpora for scale and synthetic-data comparison. |
| P3 | BrowserGym / WorkArena | Strong web-agent benchmark environment; use after static trace converters stabilize. |
| P1 | AgentNet | Large human-annotated desktop computer-use trajectory corpus; likely strongest next desktop converter target. |
| P1 | SATraj-OS | Large OSWorld-style GUI trajectory dataset; useful for scale and desktop GUI stress tests. |
| P2 | Mobile-R1 | Mobile GUI trajectory dataset with manually annotated instances and an open trajectory sample. |

## Novelty Verdict

- Overall same-claim risk: medium. These works have labeled trajectories, but they do not claim a general operation-stack profiler or pprof/flamegraph projection for agent observability.
- Claims safe to keep: operation/operation-stack as a unifying profiling abstraction across local traces and third-party trajectories.
- Claims to narrow or drop: automatic boundary detection is not supported yet; current evidence supports deterministic operation mapping/stack rules plus normalized operation input.
- Larger claim opportunities: a single profiler can compare local coding-agent traces, web navigation demos, mobile UI demos, and tool-use traces by changing operation fields and stack projection rather than the profiler abstraction.
- Mandatory baselines: dataset-native sequence view, fixed prompt/session or demo/session stack, flat action aggregation, rule-free default stack.
- Current best candidates: GUI-Odyssey, WebShop, ToolBench, and WebLINX. Mind2Web and SWE-agent are strong secondary candidates; AndroidControl is the best deeper boundary oracle after heavier screenshot-aware sampling; API-Bank remains a compact baseline; TRAIL is likely strong but gated. AGUVIS stage2, OSWorld-Verified, AgentNet, SATraj-OS, PC Agent-E, OS-Genesis, and Mobile-R1 are the next expansion candidates once the current 9-dataset pipeline is stable.
- Next action: scale the top four candidates, add AgentNet/SATraj-OS or AGUVIS converters, and extend R280/R282 beyond action-boundary scoring to subtask/step-instruction adequacy.
