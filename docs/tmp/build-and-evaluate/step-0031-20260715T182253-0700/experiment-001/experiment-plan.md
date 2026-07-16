# Experiment Plan: Declared-Vocabulary Task Identity on AgentBoard

**Proposed:** 2026-07-15T18:22:53-07:00
**State:** proposed; no experiment output is admitted before independent plan
review
**Paper question:** **RQ3 — How Accurate Are the Tags?**

## Tested Hypothesis

> On the complete official AgentBoard test population, a fixed target-blind
> declared-taxonomy mode of the existing local AgentProf tagger assigns goals
> to the user-declared official task-family taxonomy with at least 0.80
> macro-F1 and 0.80 micro accuracy, above a majority-tag control, while
> producing stable grammar-valid identities across identical repetitions.

This is one hypothesis about literal **task** identity. It cannot change RQ3,
and no outcome answers phase identity, action identity, boundary identity, or
all of RQ3. A failure can change the implementation of this hypothesis, not the
paper question or its positive direction.

## Why This Experiment Has Paper Value

The paper's load-bearing semantic story needs stable identities, while the
current local model derives an open-vocabulary one-word tag independently for
each prompt.
Existing RQ3 evidence establishes useful task partitions and operation-group
boundaries but explicitly excludes literal names. A declared vocabulary is the
smallest principled repair: profiling categories are chosen once, and the
existing target-blind tagger assigns new goals to them.

The experiment uses a published NeurIPS benchmark in full rather than another
local task or hand-labeled sample. A positive result connects the abstract
model's stable identifiers to an independently named real-agent task taxonomy.
A negative result is scientifically useful internally because it isolates the
remaining weakness to assignment under a declared taxonomy; it does not cause
a smaller story or another benchmark search.

## Population and Information Boundary

- Source: the nine official AgentBoard `test.jsonl` files from the released
  `data.tar.gz` whose SHA-256 is recorded in the source screen.
- Population: all 1,012 nonempty rows; no sampling, subsplit, deduplication, or
  filtering by result.
- Predictor input: the row's natural-language `goal` string only.
- Scorer-only fields: `task`, source filename, row `id`, `subgoals`,
  `difficulty`, `additional_info`, and all other fields.
- Training: none. Both taggers are zero-shot and fixed before the first scored
  row.
- Ordering: canonical file-name order followed by source row order. Ordering
  is not visible to either tagger.

Rows with a missing/empty goal or unknown official task would invalidate the
population rather than being silently dropped. The source inspection found
none, but full execution rechecks this condition.

## Declared Identities

AgentProf tags must be 3–12 lowercase letters, so two hyphenated official names
use a fixed lossless alias. The WebArena file already uses `webbrowse` in its
official `task` field.

| Scorer identity | Emitted tag | Description visible to the candidate |
|---|---|---|
| `alfworld` | `alfworld` | embodied household-object tasks |
| `babyai` | `babyai` | grid-world instruction and navigation tasks |
| `jericho` | `jericho` | interactive text-adventure game tasks |
| `pddl` | `pddl` | symbolic condition-satisfaction planning tasks |
| `scienceworld` | `scienceworld` | interactive science-environment tasks |
| `tool-operation` | `toolop` | tasks that operate on an application through tools |
| `tool-query` | `toolquery` | tasks that answer a query through information tools |
| `webbrowse` | `webbrowse` | website browsing and interaction tasks |
| `webshop` | `webshop` | product search and shopping tasks |

These labels are the official nine benchmark identities, not a learned or
author-invented replacement taxonomy. The descriptions are fixed
project-authored operational glosses of the published families; they are not
official per-row annotations and will not change after predictions are seen.

## Compared Methods

### Proposed: declared-taxonomy local tagger

- Same existing Qwen2.5-3B-Instruct Q4_K_M GGUF used by the retained R170
  local tagger evidence.
- Same local llama.cpp OpenAI-compatible chat path.
- Temperature zero, maximum eight output tokens, no examples, no target row
  labels, and no parameter fitting.
- System instruction: return exactly one allowed lowercase task tag.
- User instruction lists the fixed identity/description table once, then the
  goal, and asks for the single best identity.
- A grammar permits exactly the nine emitted tags. This is the only algorithm
  output vocabulary.

The intervention is evaluated as one declared-taxonomy assignment bundle:
declared ontology, fixed prompt, and enumerated grammar. The experiment does
not attribute any gain to grammar alone. The candidate is an optional mode of
the shared Rust `LlamaTagger`; it returns an additional canonical/task field
while retaining the existing raw open-vocabulary tag as a separate field. It
does not replace or change the existing default behavior.

### Context ablation: open-vocabulary local tagger

The same model, endpoint, temperature, output budget, and goal use the current
AgentProf one-word prompt and lowercase-word grammar verbatim. It receives no
declared identity table. Exact equality with one of the nine emitted tags is
scored; every other valid word remains a valid open-vocabulary output but is an
incorrect official identity.

This exact-match row exposes what the raw tag alone provides, but it is not a
fair generic classification baseline and does not identify the effect of the
grammar separately from the declared ontology and prompt.

### Simple control: majority identity

Every row receives `webshop`, the largest official class (251/1,012). No
custom lexical rules, embeddings, classifier training, extra model, or
post-hoc synonym map is added.

## Repetitions and Outcomes

Each model condition receives three independent identical calls per goal with
the same fixed request. Caches are disabled for scoring. The repeated calls
test output stability; they are not seeds for selecting a favorable result.

Primary outcome:

- candidate macro-F1 across the nine official identities, computed from the
  first repetition of every row.

Secondary outcomes:

- micro accuracy and per-identity precision/recall/F1;
- exact three-call stability per row;
- grammar-valid rate and coverage;
- current open-vocabulary macro-F1 and accuracy under exact identity scoring;
- majority macro-F1 and accuracy; and
- the complete candidate confusion matrix.

The tested hypothesis is supported only when the candidate reaches at least
0.80 macro-F1 and 0.80 micro accuracy, exceeds the majority control on both
metrics, all 1,012 rows are scored, and its outputs are grammar-valid. The
open-vocabulary row is reported as context rather than an additional support
condition. Stability and per-family results determine the strength and scope
of the conclusion rather than serving as a hidden post-hoc pass switch. No
numeric cutoff, family exclusion, label merge, synonym mapping, or model change
is selected from the observed answers.

## Minimal Implementation

Before any scored row is run, the existing Rust `LlamaTagger` must implement
the declared-taxonomy bundle through its shared request, retry, sanitation, and
cache path. Its returned record must keep `raw_tag` and the additional
`canonical_tag`/task field separately. The same implementation is evaluated
regardless of whether its result is positive or negative.

One thin experiment adapter may then:

1. read and validate the nine official JSONL files;
2. invoke the actual shared Rust AgentProf tagger path for both returned fields;
3. pass the fixed taxonomy to that product path without reimplementing its
   request;
4. write one prediction row per source row, method, and repetition;
5. compute the declared metrics and confusion matrix; and
6. write raw machine results under `.agentsight/experiments/` plus a detailed
   Markdown result report in this directory.

It may not add examples, training, retrieval, embedding similarity, a synonym
table, a second evaluator, model judging, label cleanup, parameter search, or a
replacement dataset. The adapter may not contain a parallel tagger
implementation or rewrite scored predictions.

## Real Preflight and Full Run

After independent plan approval:

1. Start the existing llama.cpp server with
   `/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf`
   on a dedicated local port.
2. Verify `/v1/models` and one real request.
3. Run a nine-row preflight containing the first row of each official identity
   through both model conditions and all output/score paths. Preflight output
   is connectivity evidence only and never enters paper metrics.
4. Run all 1,012 rows and all three repetitions for both conditions to
   completion.
5. Stop the dedicated server after outputs are durable.
6. Have a fresh independent reviewer recompute population counts, predictions,
   metrics, stability, and the confusion matrix from raw outputs before WRITE.

An adapter or server failure is repaired and the same approved full run is
resumed or rerun. It does not consume a scientific failure or trigger a new
benchmark. A change to the identities, visible input, model, prompt semantics,
comparison, repetition count, or metric requires returning to plan review.

## Paper and Story Boundary

WRITE may add a concise AgentBoard literal-task result to RQ3 only after a
valid positive result review. It must preserve:

- the exact thesis and four RQs;
- the existing recurrence algorithm and Step 0030 result;
- all current RQ1, RQ2, and RQ4 answers;
- the distinction between literal task identity, partition fidelity, and group
  boundaries; and
- the fact that phase/action literal identity remains a separate component.

The experiment may strengthen the paper's task-identity evidence. Its oracle is
the official AgentBoard environment/task-family field: this experiment tests
assignment to a user-declared AgentBoard taxonomy, not whether the emitted word
is the uniquely correct open semantic description. In particular,
`tool-operation` and `tool-query` may be distinguished partly by domain or goal
template fingerprints rather than a universal operation/query distinction.
No AgentBoard row is used for task-specific training, examples, prompt
selection, or tuning, but exposure of public AgentBoard goals during the
foundation model's pretraining is unknown. The result cannot establish
phase/action identity, open-vocabulary semantic-name adequacy, generalization
to an undeclared task family, replace the original story, turn task-family
classification into the paper's main contribution, or imply that AgentBoard
evaluates system-effect attribution.
