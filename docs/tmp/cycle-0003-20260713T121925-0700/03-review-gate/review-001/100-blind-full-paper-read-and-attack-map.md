# Review 001 / Node 100 — Blind Full-Paper Read and Attack Map

**Started:** 2026-07-13 16:06:31 PDT
**Completed:** 2026-07-13 16:18:12 PDT
**Parent:** [`000-review-entry-20260713T160631-0700.md`](000-review-entry-20260713T160631-0700.md)
**Phase / cycle / gate:** `BUILD_AND_EVALUATE` / cycle 0003 / `REVIEW`
**Node status:** complete
**Paper edit authority:** none

## Objective

Read the complete authoritative AgentProf paper as a skeptical AAAI reviewer,
reconstruct its argument without using the Cycle 0003 result to redefine it,
and form the paper-only reject hypotheses that external search must attack.
This node does not decide a new story, alter an RQ, or select an experiment.

## Inputs and provenance

The reviewer read:

- `docs/user-instruction.md` for immutable user intent;
- all reader-facing content in `docs/paper/`, including `main.tex`, the
  bibliography, figures, tables, build files, and rendered PDF;
- `docs/agentpprof-paper/main.tex` only to verify scientific authority;
- the `iter-review-critique` skill and its research-taste, systems, AI/ML, and
  cross-domain review references.

The user-selected attachment is byte-identical to
`docs/agentpprof-paper/main.tex` after normalizing CRLF line endings. The active
`docs/paper/main.tex` differs scientifically only in the AAAI wrapper. The
submodule remained read-only and clean.

### Reviewer-context disclosure

The assignment necessarily disclosed the fixed thesis, four RQs, and the fact
that a HINTBench experiment existed. The initial assessment below was formed
from the paper before reading its current experiment reports or prior verdicts.
Those disclosed facts were treated only as scope constraints, not as intended
answers.

## Domain and venue classification

- **Target:** AAAI-27 Main Technical Track.
- **Contribution type:** genuinely cross-domain.
- **Systems load-bearing layer:** an operation representation, cross-layer
  attribution, query-time hierarchy, aggregation, and an implemented profiler.
- **AI/ML load-bearing layer:** semantic intent/tag derivation and claims about
  locating real failures across agent trajectories.
- **Review bar:** both the systems and AI/ML bars apply; strength in one cannot
  compensate for an unsupported claim in the other.

## Paper reconstructed in plain language

### Problem and stakes

Teams accumulate many long agent trajectories. A trace or debugger explains
one run, but does not directly answer population questions: which recurring
task categories consume tokens, time, file, or network resources; where
failures and unsafe effects concentrate; and which semantic workflows deserve
attention.

### Challenged belief

Per-execution traces and span trees are sufficient observability structures
for operating agents. The paper argues that occurrence in one execution is not
the same as recurring responsibility across executions.

### Simple principle

> Aggregate measured agent activity by recurring semantic responsibility
> across runs, rather than treating execution occurrence as the only organizing
> structure.

This is a large, economical, memorable principle and is faithful to the exact
authoritative thesis:

> **Agent observability needs profiling, not only debugging.**

### Mechanism

1. A uniform `operation` represents prompts, model calls, tools, and system
   effects using string fields and additive measures.
2. An `operation stack` projects an ordered set of fields into a hierarchical
   path at query time.
3. Intent attribution or mapping rules derive stable semantic fields.
4. Folding equal paths sums additive measures.
5. AgentProf emits pprof, folded-stack, SVG, and JSON views.

The conceptual center is deliberately small: operations and operation stacks.
Taggers, mappings, induction, ranking, and output formats are supporting
mechanisms, not separate headline abstractions.

## Fixed paper-level questions

The paper contains exactly the four user-fixed questions:

1. **RQ1 — resource attribution:** Does semantic profiling improve resource
   attribution?
2. **RQ2 — real-problem localization:** Does profiler output correspond to
   real problems?
3. **RQ3 — tag accuracy:** How accurate are the tags?
4. **RQ4 — profiling cost:** What is the profiling cost?

The review does not rename, merge, remove, or reinterpret any of them.

## Initial paper-only verdict

**Weak Reject / major scientific revision; incomplete-but-promising.**

The thesis and two-object model have top-venue potential. The paper is not
complicated-but-shallow: its principle is simple and potentially durable. The
visible evaluation, however, does not yet establish the causal chain from
semantic fields to correct responsibility attribution or useful problem
localization. This is an evidence problem, not permission to make the paper
smaller.

## Strongest paper-only reject hypothesis

> AgentProf currently demonstrates configurable grouping and visualization,
> but its headline attribution and localization results are measured or ranked
> using the same semantic or target information they claim to validate.
> Therefore the paper has not yet shown that profiling improves a real
> decision over a strong trace, raw-action, or information-equivalent
> aggregation baseline.

## Attack map

### Blocker B1 — RQ2 ranking uses the hidden target

**Paper location:** RQ2 protocol and Table 1.

The paper says that groups are ranked by the fraction of hidden positives they
contain. That fraction is the gold target density. Hidden labels may not enter
stack construction, but using them to rank the groups means the reader-facing
localization policy is not target-blind.

Additional paper-only threats:

- stack fields, mappings, ranking criteria, and depth can be changed and rerun
  on the same evaluated tasks;
- operation-stack AP (`0.312`) is below per-session (`0.348`) and native
  hierarchy (`0.357`) in the visible median table;
- `9.4%` top-five work accompanies only `18.8%` top-five recall;
- the claimed `90%` inspection saving compares points with different recall.

**Required repair class:** a fresh target-blind full experiment at matched
recall with a fixed policy, complete population, strong same-information
baselines, and uncertainty. This routes to EXPERIMENT, not a smaller RQ2.

### Blocker B2 — RQ1 separation is partly a construction identity

**Paper location:** RQ1 semantic-axis ablation and Figure 3.

The mixed-weight metric asks whether a bucket mixes `prompt_tag` categories
while the experiment adds `prompt_tag` to the grouping key. The final zero-mix
row is therefore algebraic. A session-preserving permutation can show an
association beyond session membership, but it does not show that the semantic
tag is correct or that downstream effects truly belong to that intent.

The rise from about 12k to 25k stacks may be useful fragmentation, but is not
independent evidence of better responsibility attribution. RQ1 ultimately
needs an independent lineage or responsibility reference on real traces.

### Blocker B3 — RQ3 tests mappings, not the claimed taggers

**Paper location:** intent attribution design and RQ3.

The paper claims regex, local-LLM, and clustering backends for natural-language
intent attribution. RQ3 instead maps structured native fields to `phase` and
compares that derived field with native `action` annotations. High scores can
result from shared action vocabulary and do not validate natural-language
intent accuracy, paraphrase stability, coverage, abstention, or downstream
attribution robustness.

The `0.7` success threshold is not justified, and the seven-of-nine headline
hides severe transfer failures on ToolBench and API-Bank. The fixed RQ3 needs a
later experiment on the actual load-bearing tag behavior.

### Major M1 — RQ4 is not complete end-to-end cost

The `1.6 s` profile timing separates or excludes the cold tag-derivation path.
The paper reports 35,136 uncached tag calls but does not give a measured full
cold-corpus wall time, peak memory, output size, scaling curve, or complete
cold-versus-warm comparison. Offline AgentProf may add zero runtime overhead to
the target agent, but capture/import cost is a separate claim boundary.

### Major M2 — operation-stack novelty is not isolated

An ordered tuple of fields followed by grouping overlaps database rollups,
trace queries, labels, and profile pseudo-frames. The paper must show the
agent-specific property that matters: preserved additive responsibility across
heterogeneous intent and effect events, plus a real analyst outcome. pprof
serialization, semantic clustering, or cross-run aggregation alone cannot
carry novelty.

### Major M3 — related-work gap is too categorical

The statement that existing tools focus on single-execution debugging is
broader than the paper needs. Current products and research can aggregate
traces, run evaluations over datasets, and cluster failures. A stronger and
more accurate distinction is that these capabilities have not established
cross-layer additive responsibility profiling for agents.

### Major M4 — mechanism description requires artifact verification

The paper says it directly reads AgentSight recordings, reconstructs triggered
file/network effects, and uses TF-IDF cosine similarity for stack induction.
These are load-bearing implementation facts that must be checked against the
actual Rust artifact before submission.

### Minor presentation findings

- The architecture figure omits several load-bearing parsing, mapping,
  correlation, and folding details.
- The three flame graphs establish output existence more clearly than analyst
  actionability.
- The paper needs an explicit limitations/threats treatment.
- Several grammar defects remain, but prose is not the acceptance blocker.

## Research-taste assessment

| Dimension | Assessment |
|---|---|
| Real problem | Important and recurring |
| Belief challenge | Real if stated as insufficiency of per-run structure for population responsibility |
| Principle | Simple, non-obvious, and durable |
| Mechanism | Compact, but not yet distinguished empirically from ordinary fielded aggregation |
| Evidence | Currently target-informed or construct-coupled at load-bearing points |
| Ambition | Appropriate; must not be reduced |
| Overall character | Incomplete-but-promising |

## Paper and claim impact

No paper change is authorized. The exact thesis, title, semantic operation
stack model, contribution list, and four RQs remain intact. The attack map asks
for stronger external evidence and mechanism truth; it does not propose an
alternative story.

## Tree and search updates

The review opens four evidence attacks, one per fixed RQ. The highest-priority
external search question is whether a fresh official benchmark can test RQ2
with complete visible agent context and decisive-step labels without reusing a
target that shaped the current mechanism.

## Project-memory updates

None in this blind node. Canonical memory remains read-only until the complete
review and independent route audit converge.

## Completion assessment and next node

The complete paper-only attack map is formed. The next node must verify the
status quo, closest work, expected baselines, benchmark populations, venue
rules, and the strongest source for one decisive experiment using primary
sources.
