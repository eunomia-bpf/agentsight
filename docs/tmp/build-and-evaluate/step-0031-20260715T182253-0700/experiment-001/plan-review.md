# Independent Plan Review: AgentBoard Declared Task Identity

**Reviewed:** 2026-07-15
**Reviewer role:** fresh scientific plan reviewer; no execution or plan editing
**Verdict:** **REVISE**

## Scope Read

I read the complete `research-experiment-design` skill and its plan template,
the complete user-instruction, idea-story, and evaluation-frontier documents,
the Step 0031 source screen and proposed plan, the current Rust tagger, and the
relevant predecessor semantic-contract design. I also inspected the official
AgentBoard source at `bb7255e2daf1989069a186dad9e53f70680961db` and all nine
released test files under `/tmp/agentboard-data/data`.

The official population is real and suitable for a bounded cell: 1,012 rows,
nine official `task` values, no empty goals, no unknown task value, and no goal
that appears under two different task values. The proposed goal-only/scorer-
only separation is executable and avoids row-label leakage. The experiment is
also decision-relevant: it targets the literal-task component that the current
paper explicitly leaves untested, rather than repeating the completed boundary
studies.

Three defects must be repaired before execution. They concern what mechanism is
actually tested and what a positive result would mean; they are not requests
for more benchmarks, evaluators, Git controls, or reproducibility machinery.

## Must-Fix Items

### 1. Test the AgentProf tagger path and preserve its established raw-tag contract

The plan currently says the adapter will first implement the candidate and that
the same mechanism *may* be ported into AgentProf only after a positive result.
That does not test an improvement to the existing tagger; it tests a parallel
experiment-only implementation and conditions product integration on the
observed answer.

The predecessor design also explicitly keeps the raw one-word tagger open
vocabulary and represents normalized identities in a separate canonical layer:
`raw_tag -> canonical_tag -> optional parent_tag`; the raw tag is never
overwritten. An optional finite taxonomy is compatible with this design only as
an additional declared task/canonical field, not as a replacement for the raw
open-vocabulary prompt tag.

Revise the plan so that, before any scored row is run:

- the existing raw open-vocabulary output remains unchanged and available;
- the declared-vocabulary assignment is implemented as an additional optional
  task/canonical field through the actual shared Rust `LlamaTagger` request,
  retry, sanitation, and cache path;
- the experiment adapter only loads AgentBoard rows and invokes that shared
  product path, rather than duplicating the tagger request; and
- the same implementation is evaluated regardless of whether the result is
  positive or negative.

This is still one small extension to the existing tagger, not a new tagger
family or a new profiling abstraction.

### 2. Separate the declared-taxonomy bundle from a grammar-only claim and require actual accuracy

The candidate receives both a nine-label ontology with descriptions **and** an
exact-enumeration grammar. The open-vocabulary condition receives neither the
ontology nor the same objective. Therefore the grammar is not “the only
algorithm change,” and exact-match superiority over the open-vocabulary output
cannot identify a grammar effect. The majority control is a valid lower bound,
but merely beating it could still yield a weak classifier and does not establish
that task identities are accurate.

Keep the experiment simple by treating the intervention as one declared-
taxonomy assignment bundle. Reclassify current open-vocabulary exact match as a
mechanism ablation/context row, not a fair generic classification competitor,
and remove any grammar-specific causal conclusion. Predeclare an absolute
positive accuracy bar in addition to beating the majority control. The existing
project adequacy precedent supplies a natural bar: require at least `0.80`
macro-F1 **and** `0.80` micro accuracy on the complete 1,012-row population.
Results below either bar are mixed or contradictory even if they beat both
weak comparison rows. If the intended claim is instead specifically about the
grammar, then a same-ontology, same-prompt, unconstrained-decoding condition is
required; the bundle framing is the smaller and better-aligned repair.

### 3. Bound the oracle and generalization claim to what AgentBoard actually labels

AgentBoard's `task` value is an official benchmark/environment-family identity,
not an independent human annotation of the most semantically appropriate task
word. In particular, goal text does not cleanly express the names'
“operation-versus-query” distinction: `tool-operation` contains many answer-
seeking queries, and both tool families require tools. Their separation can be
learned from domain/template fingerprints (todo/spreadsheet versus
DBLP/movie/weather), not necessarily from a general semantic distinction.

Revise the plan and interpretation boundary to say that this experiment tests
assignment to a **user-declared AgentBoard task-family taxonomy**. It does not
by itself establish open-vocabulary semantic-name adequacy, phase/action
identity, or generalization to an undeclared task family. Replace “unseen goal
texts” with the supportable statement that no AgentBoard row is used for
task-specific training, examples, prompt selection, or tuning; exposure of
public AgentBoard goals during the foundation model's pretraining is unknown.
Also identify the nine descriptions as fixed project-authored operational
glosses of the official families, rather than official per-row annotations.
Do not add scorer fields to the predictor to repair this limitation.

## Optional, Non-Blocking Improvements

- The release contains repeated identical goals within some classes (for
  example, 134 AlfWorld rows contain 78 unique goals and 112 BabyAI rows contain
  58). The full official row population should remain primary. A unique-goal-
  weighted sensitivity row would make the template-repetition boundary visible,
  but it is not required for plan approval.
- Because this is a census of the released population, the report may state
  that it gives no sampling interval for those 1,012 rows. Per-family metrics
  and the complete confusion matrix are sufficient; no bootstrap or additional
  evaluator is required.

## Approval Condition

Approval requires only the three plan repairs above: shared product-path
execution with raw-tag preservation, an honest bundle comparison with an
absolute accuracy criterion, and a precise official-task-family evidence
boundary. The benchmark provenance, complete-population run, scorer separation,
metrics, repetitions, real preflight, completion rule, and planned independent
result recomputation are otherwise sufficient.

## Revision Review

**Re-reviewed:** 2026-07-15
**Inputs:** revised `experiment-plan.md` and `plan-revision.md`
**Final verdict:** **APPROVE**

The revision closes all three original must-fix items without expanding the
experiment:

1. **Existing tagger and raw-tag contract:** the declared-taxonomy path must now
   be implemented in the shared Rust `LlamaTagger` before scoring, uses its
   request/retry/sanitation/cache path, preserves the raw open-vocabulary tag,
   and returns the declared task/canonical field separately. The adapter is
   limited to loading official rows, invoking that path, and scoring; product
   integration is no longer conditioned on a positive result.
2. **Mechanism and positive criterion:** the candidate is correctly defined as
   one ontology-plus-prompt-plus-grammar bundle. Open-vocabulary exact match is
   labeled a context ablation rather than a fair classifier or grammar-isolation
   baseline. Support now requires both macro-F1 and micro accuracy of at least
   0.80 and improvement over the majority control, so a weak but non-majority
   classifier cannot be called accurate.
3. **Oracle and generalization boundary:** the plan limits the result to a
   user-declared AgentBoard task-family taxonomy, identifies the descriptions
   as project-authored glosses, records possible goal-template/domain
   fingerprinting (including the two tool families), and explicitly excludes
   open-semantic-name, undeclared-family, phase/action, and unknown-pretraining
   generalization claims.

The approved experiment is therefore a simple, complete, target-blind test of
one additional canonical task field through the existing AgentProf tagger. No
new benchmark, evaluator, baseline family, protocol, or review layer is needed.
Proceed to the planned real preflight and then the complete run.
