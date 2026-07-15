# External Search and Source Verification

Timestamp: 2026-07-15T06:01:00-07:00
Parent: `01-blind-read.md`
Objective: attack novelty, problem reality, baseline strength, and evaluation protocol

## Method and search coverage

Queries covered coding-agent trajectory replay/visualization, Git visual
analytics evaluation, agent-code attribution/provenance, software-visualization
evaluation, and large trace viewers. Search snippets were used only for
discovery; the assessment opened primary arXiv papers, author-hosted PDFs, and
official Perfetto documentation.

| Search question | Primary source | Finding and paper impact |
|---|---|---|
| Is fine-grained process replay already available? | [RECAP](https://arxiv.org/abs/2605.01104) | RECAP passively records chat and fine-grained IDE edits, merges a unified replay timeline, and reports 2,034 prompts/8,239 edits from 41 students over a multi-week project. Replay and joined process data are not novel; the atlas must win on cross-vendor actual-Git uncertainty and long-horizon review. |
| What is the expected strong Git-only baseline? | [Githru](https://arxiv.org/abs/2009.03115) | Githru uses domain interviews, requirements, context-preserving commit aggregation, global temporal brushing, and coordinated detail. A screenshot gallery without the frozen Git-only/task comparison is weaker evidence. |
| What evaluation bar does software visualization set? | [Merino et al.](https://homepages.ecs.vuw.ac.nz/~craig/publications/jss2018-merino.pdf) | The review distinguishes task experiments from design-study case/usage evaluation and reports that 62% of approaches lack strong evaluation. It explicitly recommends real systems and target-audience studies when variables can be controlled. This directly supports the main reject argument. |
| Do trajectories contain stable information beyond success? | [Agent Trajectories as Programs](https://arxiv.org/abs/2606.16988) | Ten agents are identifiable from procedural habits at 85.7% accuracy under task-leakage controls. This supports the importance of process representations but raises the bar for the paper's abandoned behavioral-structure RQ2. |
| Is agent attribution from Git a real fragmented-signal problem? | [Validated multi-method census](https://arxiv.org/abs/2606.24429) | Across 180M repositories, no single detection signal recovers more than a fraction of agent activity; different channels capture nearly disjoint populations. This strongly supports the three-layer problem and contradicts any simple Git-author or commit-message solution. |
| Is a custom browser timeline needed for scale? | [Perfetto external formats](https://perfetto.dev/docs/getting-started/other-formats), [large traces](https://perfetto.dev/docs/visualization/large-traces) | Perfetto accepts Chrome JSON and offers native TraceProcessor acceleration for large traces. It is both a compatibility path and a serious timeline/scale baseline. The paper implements export but does not measure or compare it. |

## Inclusion and exclusion

RECAP is the closest same-problem capture/replay system. Githru is the strongest
verified Git visual-analytics baseline. Merino supplies the domain evaluation
construct. The trajectory paper and multi-method census provide adjacent agent
evidence that respectively strengthens the process-value premise and the
multi-layer identity problem. Perfetto is an official artifact baseline.
Marketing pages, generic visualization summaries, Reddit posts, and search-only
snippets were excluded from the verdict.

## Changed attack map

External evidence makes the problem less strawman-like: agent traces carry
procedural information, and Git/PR/configuration signals are demonstrably
fragmented. It makes the novelty/evaluation bar harder, however. RECAP already
delivers multi-week linked replay with a larger human deployment, while Githru
already coordinates temporal filtering and details around explicit tasks.
Thus “event resolution + coordinated views” is insufficient alone. The durable
principle worth defending is the uncertainty-preserving separation among
process, outcome, and endpoint, and its value must be shown through tasks where
the layers disagree.

## Uncovered and unresolved communities

The targeted review did not comprehensively map provenance standards, program-
comprehension theory recovery, or visual analytics for autonomous-agent traces.
A later novelty cycle should expand those branches if the paper pursues a full
venue submission. The present closest-work set is sufficient to decide that the
missing review-utility study is the decisive gap.

## Completion and next node

Primary-source verification is complete for every load-bearing attack. The next
node rereads the full paper and checks whether its scoped artifact/experience
claims survive these comparisons.
