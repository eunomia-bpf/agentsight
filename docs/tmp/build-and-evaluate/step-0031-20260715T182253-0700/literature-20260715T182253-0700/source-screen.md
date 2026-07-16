# RQ3 External Source Screen: Literal Task Identity

**Screened:** 2026-07-15T18:22:53-07:00 through
2026-07-15T18:22:53-07:00
**Question:** Which existing real public asset can directly test literal task,
phase, or action identity without collecting a new benchmark or repeating the
completed boundary studies?

## Inclusion Rule

A direct candidate must expose a visible input that AgentProf could tag and an
independent official identity for the same item. Preference order is:

1. peer-reviewed real-agent benchmark with a complete released population;
2. official public data and evaluator;
3. existing local real-agent trajectories with predeclared labels; and
4. a new author-designed suite only if no stronger asset exists.

Partition labels, model self-reports, post-hoc LLM judgments, process-level
success scores, and human-only workflows do not become literal agent-tag truth
by reinterpretation.

## Sources Inspected

### AgentBoard — selected for a task-identity cell

- Official paper: [NeurIPS 2024 Datasets and Benchmarks
  proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/877b40688e330a0e2a3fc24084208dfa-Abstract-Datasets_and_Benchmarks_Track.html).
- Official code: [hkust-nlp/AgentBoard](https://github.com/hkust-nlp/AgentBoard).
- Official data: [hkust-nlp/agentboard on Hugging
  Face](https://huggingface.co/datasets/hkust-nlp/agentboard).
- Inspected code commit:
  `bb7255e2daf1989069a186dad9e53f70680961db`.
- Downloaded official `data.tar.gz`: 1,403,423,961 bytes, SHA-256
  `26c2516eb2e4d45cb982cda94c0f14c0a31ae657776f45ef59c4c0bf7243787d`.

The nine official test files contain 1,012 complete goals with an official
`task` identity:

| Official file | Rows | Official identity |
|---|---:|---|
| `alfworld/test.jsonl` | 134 | `alfworld` |
| `babyai/test.jsonl` | 112 | `babyai` |
| `jericho/test.jsonl` | 20 | `jericho` |
| `pddl/test.jsonl` | 60 | `pddl` |
| `scienceworld/test.jsonl` | 90 | `scienceworld` |
| `tool-operation/test.jsonl` | 40 | `tool-operation` |
| `tool-query/test.jsonl` | 60 | `tool-query` |
| `webarena/test.jsonl` | 245 | `webbrowse` |
| `webshop/test.jsonl` | 251 | `webshop` |

The goal is a visible natural-language task input; the official `task` field is
kept scorer-only. This supports a full-population, zero-shot literal task-
identity experiment with no new examples, labels, split, or task taxonomy.

The release also contains 13 model baseline directories and 13,110 summary
rows. Source inspection found that the released `baseline_results` hold
per-example success, progress, grounding, and score-change tuples but no JSONL
action/observation trajectories. Therefore AgentBoard cannot directly provide
a new phase/action-boundary experiment from the released baseline logs. That
unavailable branch is rejected rather than inferred from scalar progress.

### OpenDiscoveryTrace — rejected as an independent phase oracle

The official trajectory format includes a `phase` field, but the agent prompt
asks the model to emit `PHASE:` and the parser extracts that self-report. It is
useful trajectory data and related-work precedent, not an independent phase
identity for scoring the same model output.

### GUIDE and GAE-Bench — precedent, not the target population

GUIDE provides human-annotated GUI behavior states and GAE-Bench derives a
large retrieval benchmark from real human GUI trajectories. Both demonstrate
that behavior-stage annotation is feasible, but their trajectories are human
demonstrations rather than AI-agent executions. They are not substituted for
the fixed RQ's agent-tag claim.

### Agentic-MME — protocol is public; model trajectories are not

The official release exposes tasks, human checkpoints, visual clues, search
evidence, and a runner. The inspected dataset does not release the paper's
model trajectories with paired step-level phase/action identity. Running new
models would create a large new collection project and is not the requested
reuse of existing trajectories.

### Microsoft Fara / CUAVerifierBench — RQ2 labels, not RQ3 identities

The release pairs Fara web trajectories with human outcome/process judgments
and comments. Those labels score trajectory quality, not a literal task,
phase, or action identity per visible step. It is relevant to process-quality
evaluation already covered by RQ2, not the open RQ3 cell.

### Existing R114 real Codex suite — retained backup, not primary evidence

The existing R114 artifact has 20 completed real Codex tasks and five
predeclared task categories. It is directly executable, but the distribution
is small and imbalanced (11 read, 4 edit, 2 test, 2 dependency, 1 failure) and
the task suite was locally authored. It remains a useful integration check and
backup literal-tag cell. It is not selected while the complete published
AgentBoard goal population provides a stronger official identity oracle.

## Selection

Proceed with one full AgentBoard task-identity experiment. It will reuse the
existing local Qwen2.5-3B llama.cpp tagger and make one minimal algorithmic
change: when the user declares a finite task vocabulary, constrain the same
tagger to choose one declared literal identity instead of inventing an open-
vocabulary word. The default open-vocabulary path remains unchanged.

This is not another benchmark search, tagger family, embedding model, training
run, or boundary method. It directly tests whether an explicit profiling
taxonomy solves the literal-name weakness of the current tagger on all 1,012
published goals. The result can strengthen the task-identity component of RQ3;
it cannot by itself answer phase/action identity or the complete RQ.
