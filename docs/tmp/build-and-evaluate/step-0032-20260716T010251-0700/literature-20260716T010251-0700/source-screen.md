# RQ3 External Source Screen: Literal Phase And Action Identity

**Screen opened:** 2026-07-16T01:02:51-07:00

**CodeTraceBench decision recorded:** 2026-07-16T01:15:40-07:00

**ASE action source admitted:** 2026-07-16T01:42:43-07:00

**Paper question:** **RQ3 — How Accurate Are the Tags?**
**Fixed evidence need:** independently published, scorer-only task/phase/action
labels that remain semantically comparable across trajectories

## Objective And Admission Rule

This screen asks whether an already-held official trajectory source can support
one non-circular literal phase/action experiment without changing RQ3. A source
passes only when:

1. the published target is a semantic task, phase, or action identity rather
   than only a trajectory-local boundary or ordinal span identifier;
2. the same target vocabulary has the same meaning across trajectories;
3. target labels can be withheld from the tested tagger and read only by the
   scorer;
4. the public release contains enough target labels and source-visible trace
   content to run the complete declared population; and
5. the result adds literal identity evidence rather than another partition
   score already supplied by OSWorld-Human and CodeTraceBench.

The screen records uncertainty and chooses the strongest runnable source; it
does not wait for human intervention, invent labels, or reinterpret a partition
as literal accuracy.

## Search Record

The root searched official or primary sources on 2026-07-16 between 01:05 and
01:15 America/Vancouver with these queries:

- `CodeTracer CodeTraceBench official paper stage_id stages trajectory benchmark`
- `CodeTraceBench official GitHub stages stage_id`
- `NJU-LINK CodeTraceBench Hugging Face stages stage_id`
- `CodeTraceBench stage_id`
- `CodeTracer StageRange agent stages`
- `CodeTracer stage labeling failure localization`

Primary sources inspected:

- [CodeTracer paper, arXiv:2604.11641](https://arxiv.org/abs/2604.11641)
- [official CodeTraceBench dataset](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench)
- [official Hub file tree](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench/tree/main)
- [official CodeTracer repository](https://github.com/NJU-LINK/CodeTracer)
- local official repository checkout at commit
  `2d302191dd07e7c0c2da6f7a5e9451c7cbb62d34`
- local official verified parquet with SHA-256
  `ae5926b496f2f7f4c3f6337c0ad6150311d3650c5f3bd00660556b3e41739505`

The Hugging Face Dataset Viewer `/is-valid`, `/splits`, and `/first-rows`
endpoints were also queried directly. The service reported a valid viewer,
`full` and `verified` splits, and the exact published nested schema summarized
below.

## Candidate 1: CodeTraceBench

### What the official paper says exists

The paper describes a real, stable semantic phase vocabulary. Its annotation
guidelines assign every trajectory step one of five labels:

1. environment verification;
2. dependency installation;
3. inspection/debugging;
4. patching; or
5. verification.

The paper also says that a trajectory may revisit a phase and that every
contiguous visit becomes a distinct stage span. These labels would be excellent
literal RQ3 phase gold: they are human annotations, shared across trajectories,
defined independently of AgentProf, and available for all solved and failed
trajectories in the paper's annotation protocol.

### What the current public release actually exposes

The published Dataset Viewer schema exposes `stages` only as:

```text
list<struct<
  end_step_id: int64,
  stage_id: int64,
  start_step_id: int64
>>
```

There is no `stage`, `stage_label`, `stage_name`, or equivalent semantic value.
The `incorrect_stages` field adds incorrect/unuseful step IDs and source
snippets for some stages, but still contains only the integer `stage_id`.

The complete local verified parquet contains 1,000 rows. A direct enumeration
found:

```text
rows                         1000
stage IDs exactly 1..k       1000
non-sequential stage IDs        0
rows with a repeated stage ID   0
```

Thus the released `stage_id` is the trajectory-local ordinal span number. It
cannot represent the paper's five-label vocabulary because the paper explicitly
allows revisiting a phase, whereas the release never repeats an ID and many
trajectories have more than five stages (up to 67).

The official Hub root file tree contains `bench_manifest.*`,
`bench_artifacts/`, `swe_raw/`, README, and build reports. It exposes no
annotation directory or separate phase-label file. The 3,291 published
`bench_artifacts/full/*.tar.zst` archives contain raw trajectory artifacts; a
direct archive inspection found agent logs, commands, panes, results, and
session files, not the paper's phase annotations. The manifest's
`annotation_relpath` therefore names an annotation-build source path that is not
present in the current public release.

The official repository confirms the distinction. Its `StageRange` runtime
model can carry a string `stage`, while the benchmark README and evaluator use
integer `stage_id` spans for failure localization. That capability does not
restore missing gold labels to the released benchmark rows.

### Source-fidelity decision

**Decision: reject the current CodeTraceBench release for literal phase-label
accuracy. Retain it for the already-completed boundary/partition evidence.**

This is a publication-availability failure, not a criticism of the paper's
annotation protocol. The semantic labels described by the paper are exactly the
right kind of gold, but the current public files do not expose the mapping from
step or ordinal span to those labels. Reconstructing that mapping from commands,
from span order, or with an LLM would create project-authored pseudo-gold and
would no longer be an independent literal-label experiment.

No experiment plan is admitted from CodeTraceBench at this point. If the
official semantic phase annotations are later released, the existing 3,291 raw
artifacts and current adapters make CodeTraceBench immediately eligible without
changing RQ3 or recollecting trajectories.

### Evidence impact

- The existing complete CodeTraceBench boundary and B-cubed results remain
  valid for trajectory-local stage partition fidelity.
- They must not be promoted to phase-name accuracy.
- The current paper statement that CodeTraceBench supplies partition rather
  than literal phase identity remains correct.
- RQ3 still needs one independent literal phase or action source in addition to
  the completed AgentBoard task-family experiment.

## Next Screen

The next source screen will first audit already-held public trajectory families
for a scorer-only semantic phase/action target. It will reject any action class
that is copied verbatim into AgentProf's visible `action` field. If no held
source passes, the search expands only to official published datasets with
manual subgoal, intent, workflow-phase, or step-role annotations and a complete
runnable release. No new partition-only benchmark is admitted.

## Additional Primary-Source Screen

The expanded search inspected official sources for GUIOdyssey, GUIDE,
Agentic Search in the Wild, TraceView, and the upstream ASE trajectory study:

- [GUIOdyssey paper](https://arxiv.org/abs/2406.08451),
  [official repository](https://github.com/OpenGVLab/GUI-Odyssey), and
  [official dataset](https://huggingface.co/datasets/hflqf88888/GUIOdyssey);
- [GUIDE project](https://guide-bench.github.io/) and
  [official GuideBench dataset](https://huggingface.co/datasets/saelyne/GuideBench);
- [Agentic Search in the Wild paper](https://arxiv.org/abs/2601.17617) and
  [official logs](https://huggingface.co/datasets/cx-cmu/deepresearchgym-agentic-search-logs);
- [TraceView paper](https://arxiv.org/abs/2606.22110) and
  [official repository](https://github.com/SOAR-Lab/agent-traj-visualization);
  and
- [ASE trajectory-study paper](https://arxiv.org/abs/2506.18824) and its
  [official artifact](https://github.com/sola-st/llm-agents-study).

GUIOdyssey exposes rich per-step natural-language descriptions and intentions,
but not a controlled scorer-only action vocabulary; copying its source-visible
action field would be circular. GUIDE has a useful nine-state/four-phase
taxonomy, but the current release is gated and its human GUI-video population
does not match the available text-agent input path. The Agentic Search logs are
large and real, but the public rows do not publish the paper's reformulation
labels. TraceView confirms the action taxonomy and provides labeling guidance,
but its bundled action population is only the AutoCodeRover subset. These
sources are retained as related evidence, not admitted as the first complete
literal-action experiment.

## Candidate 2: ASE 2025 Software-Engineering Agent Trajectories

### Published population and target

The official artifact for *Understanding Software Engineering Agents: A Study
of Thought-Action-Result Trajectories* accompanies an ASE 2025 SIGSOFT
Distinguished Paper. It contains 120 manually analyzed real software-
engineering agent trajectories, with 40 trajectories from each of:

- AutoCodeRover;
- OpenHands/CodeActAgent; and
- RepairAgent.

The artifact publishes one ordered `iteration,category` CSV per trajectory and
a common eight-class action taxonomy: Explore, Locate, Search, Reproduce,
Generate Fix, Run tests, Refactor, and Explain. The taxonomy has the same
meaning across agents and trajectories. It also separately publishes parsed
thought/action/result views, so the category column can remain invisible to the
candidate and enter only at scoring time.

The ASE methodology uses a hybrid annotation procedure: known agent tools are
mapped automatically to their categories, while remaining actions are manually
inspected; one author performs initial labeling and ambiguous cases are resolved
collaboratively. The output names and published category rows come from the ASE
artifact. The more operational prose descriptions used in the fixed prompt
come from the secondary TraceView companion labeling guide.

The official repository was inspected locally at commit
`e84f66f8d494e46ef336edfa137db25a629614fb`. The secondary TraceView repository
was inspected at commit `4b55f40efb495b9f7801ce9d25f473ed5ee2dffb`; its labeling guide supplies the
same operational descriptions:

| Label | Published meaning |
|---|---|
| Explore | Broadly inspect the task, repository, environment, or available context. |
| Locate | Identify the specific file, symbol, function, or code area to change. |
| Search | Run a targeted search for text, references, examples, or related behavior. |
| Reproduce | Run commands or checks to observe, reproduce, or isolate the problem. |
| Generate Fix | Create or edit code intended to solve the task. |
| Run tests | Run tests, linters, or validation commands after a change. |
| Refactor | Reorganize or simplify code without changing intended behavior. |
| Explain | Reason, summarize, or plan without directly changing or validating code. |

### Direct release audit

The complete release contains exactly 40 category files per agent and 2,737
published labels:

| Agent | Trajectories | Gold rows | Visible iterations | Coverage |
|---|---:|---:|---:|---:|
| AutoCodeRover | 40 | 218 | 218 | 100.00% |
| OpenHands | 40 | 1,108 | 1,113 | 99.55% |
| RepairAgent | 40 | 1,411 | 1,420 | 99.37% |
| **Total** | **120** | **2,737** | **2,751** | **99.49%** |

All 2,737 gold iteration IDs refer to an existing visible thought/action
iteration. No category file contains duplicate or out-of-range gold IDs. Four
trajectories omit 14 source iterations from the published category CSVs:
OpenHands `django__django-14017` omits iteration 0,
OpenHands `sphinx-doc__sphinx-11445` omits 93--96,
RepairAgent `Jsoup_16` omits 33--40, and
RepairAgent `experiment_454_JacksonDatabind_3` omits 38. The experiment will
score every published label and report 2,737/2,751 source coverage; it will not
guess those 14 targets or discard the four trajectories.

Class support is:

| Explore | Locate | Search | Reproduce | Generate Fix | Run tests | Refactor | Explain |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 606 | 196 | 364 | 153 | 883 | 294 | 23 | 218 |

A later outer-audit scan found that 39 AutoCodeRover visible action fields are
exactly the gold output literal `Locate`. This does not expose the hidden
category column, but it means the source is not uniformly free of verbatim
target strings. The full experiment therefore reports a sensitivity analysis
with those rows excluded rather than claiming blanket semantic separation.

### Source-fidelity decision

**Decision: admit the complete published labeled population for one literal
action-identity experiment.**

The candidate may read only the current iteration's visible thought and action
text and the fixed eight label descriptions. It may not read the category CSV,
trajectory outcome, resolved/unresolved membership, filename-derived agent
answer, neighboring gold, or class frequencies. Gold is joined by agent,
trajectory ID, and published iteration ID only after predictions are durable.

Primary outcome is eight-class operation-macro F1. Secondary outcomes are
accuracy, per-class precision/recall/F1, full confusion matrix, per-agent
macro-F1 and accuracy, exact prediction coverage, and repeat agreement. The
majority label is a lower-bound control. There is no universal 0.80 gate and no
composite score. Because `Refactor` has only 23 examples, the result must expose
class support and cannot rely on accuracy alone.

This source answers literal action identity, not operation partitioning,
cross-run identity, localization, resource attribution, or overhead. It adds a
new RQ3 evidence type without changing the fixed RQ or paper story.

## Screen Conclusion

The source-fidelity node is complete. CodeTraceBench remains valid only for
partition fidelity; the ASE 2025 trajectory artifact is the strongest complete
public source for literal action identity and advances to experiment planning.
