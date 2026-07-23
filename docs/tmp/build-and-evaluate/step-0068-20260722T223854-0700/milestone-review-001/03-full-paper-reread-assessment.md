# 03 — Full-Paper Reread and Scientific Assessment

- **Timestamp:** 2026-07-22T23:04:00-07:00
- **Parent:** `step-0068-20260722T223854-0700/milestone-review-001`
- **Inputs:** current 10-page paper, both independent reviews, verified primary
  sources, current evaluation tables, and the exact RQ2 arithmetic
- **Objective:** separate true blockers from reviewer overreach and select the
  minimum high-value repair that strengthens rather than narrows the paper

## Verified blocker

### RQ2 automatic-versus-declared attribution

The Table 1 values and prose were recomputed directly:

| Workload | Declared/reference−Raw | Automatic+Evidence−Raw |
|---|---:|---:|
| AgentProcessBench | +0.015749 | -0.000665 |
| HINTBench | +0.171136 | +0.132752 |
| TraceElephant | +0.108898 | +0.130656 |

The paper reports the left column as the primary AgentProf gain without making
the configuration explicit in the result sentence, while the caption
separately defines the target-blind declared/reference semantic hierarchy and
automatic Agent marks. A reader can infer that the automatic backend achieved
all three gains. The declared hierarchy is an AgentProf configuration fixed
before evaluator targets, not a gold-label oracle. This is not a stylistic
issue: the declared and automatic results must be attributed separately.

**Route:** targeted WRITE before another submission-like review. Preserve the
table; call `Sem.` the target-blind declared/reference hierarchy; report the
automatic results separately, including the full-precision small negative
AgentProcessBench difference. Do not change RQ2 or the thesis.

### RQ1 wording drift

The fixed RQ asks whether semantic profiling **improves resource attribution**.
The paper now asks only whether one hierarchy **exposes different resource
bottlenecks**. The current repeated-task result supports the latter but does not
authorize replacing the former. Targeted WRITE must restore the fixed RQ
wording and explain precisely which part the current evidence answers; the
experiment gate can then decide whether more attribution evidence has higher
paper value than another RQ.

## Shared major finding

Grok and Claude both ask for the same missing bridge, although only Grok is a
confirmed clean paper-only review:

> show a population-level question for which the automatic, source-drillable,
> multi-resource operation profile changes a decision relative to a strong
> hierarchical/process alternative.

This is a high-value EXPERIMENT candidate, not yet a mandatory gate. The current
sketch spans RQ1, RQ2, novelty, and utility, so it cannot be admitted as one
experiment until the experiment loop selects one fixed RQ and one falsifiable
claim.

If selected for one fixed RQ, an economical design would:

- reuse one complete existing population;
- define one independent diagnostic target before reading the compared outputs;
- compare automatic AgentProf against raw/source-native rollups and one strong
  trace-level hierarchical/process baseline;
- keep the same evidence and measure;
- score standard localization or decision quality with clustered uncertainty;
- retain a qualitative stock-pprof case explaining the quantitative result.

No human-in-the-loop gate is required. Existing expert labels, benchmark
targets, or a separately generated fixed answer key can supply the target. A
commercial product run is optional if its output can be exported; otherwise a
documented open capability-equivalent baseline is scientifically cleaner.

## Reviewer requests not promoted to blockers

### “Boundary F1 .394 means most profile boundaries are wrong”

This phrasing is too strong. Boundary F1 is exact event-boundary agreement in a
sparse, imbalanced sequence; `1-F1` is not an error rate over all nodes.
Ordinary B-cubed F1 is .704 and measures partition agreement. Nevertheless, the
gap between exact boundary and partition scores motivates a useful sensitivity
check: verify that the paper's aggregate top responsibilities and resource
shifts survive reasonable annotation perturbations or alternative automatic
backends. This can be an ablation inside the decisive experiment, not a new
standalone project.

### “Conservation is trivial, so remove it”

Mass conservation is algebraically simple but operationally essential: without
it, switching hierarchy or measure can manufacture or discard resource width.
The paper should present it as a design invariant, not a mathematical novelty.
The notation can be tightened later, but deleting the invariant would make the
system less auditable.

### “A user study is mandatory”

A user study is one valid protocol, not the only one. The user's instruction
forbids waiting for human intervention, and the thesis is testable with
independent diagnostic targets and measured decision quality. A clean automatic
head-to-head is preferable to a small convenience-sample study.

### “RQ4 excludes annotation, therefore it is invalid”

The current paper explicitly scopes RQ4 to the profiling core and states that
automatic annotation latency is separate. This is honest. Annotation cost
should be reported when available, but it is not a blocker for the measured
profile-construction claim.

### “The 2026 benchmarks cannot be verified”

Primary arXiv papers exist for all four load-bearing benchmark families.
Specific field/label leakage remains an audit question, but the general
existence/provenance objection is resolved.

## Product-quality hierarchy warnings

The mechanical hierarchy checks are appropriate but orthogonal to paper
acceptance:

- a semantic leaf with zero semantic children is legal;
- an optional semantic refinement with one explicit child emits a nonblocking
  unary warning;
- a broad optional leaf covering at least eight tool calls emits a coarse-span
  warning;
- a node with at least eight children and fewer than one quarter recursively
  refined emits a flat-fan-out warning;
- source-mandated session/prompt scope is exempt where unary structure is
  ordinary.

The rule is therefore `semantic_children ∈ {0} ∪ [2,∞)` as a hygiene
expectation, not a validity contract. It catches redundant wrappers but cannot
by itself make a flame graph insightful. Semantic naming, cross-session
identity, and the diagnostic question remain the substantive requirements.

## Terms and paper organization

Use two load-bearing terms:

1. **operation** for the weighted fielded/source-linked unit;
2. **operation stack** for the reusable responsibility path.

“Recursive annotation” is the construction method, not a third model object.
“Semantic responsibility” is explanatory prose. Stage, group, phase, and action
should be reserved for benchmark labels or named path roles. This cleanup is a
later WRITE task and must preserve abstract/introduction meaning.

## Reread verdict

**Current readiness: 4.5/10, weak reject / major revision.** The paper has a
top-conference-sized idea, a real artifact, broad data, and authentic case
profiles. It is not ready because one headline comparison is attributed to the
wrong AgentProf configuration and RQ1 wording has narrowed. The correct
immediate response is targeted WRITE. A same-input closest-capability
comparison remains a high-value candidate to be admitted only through one
fixed RQ and one claim—not a pre-authorized compound gate.

## Completion and uncertainty

**Status: complete.** All paper sections and figures were reconsidered after
source verification. The exact availability and export format of commercial
hierarchical outputs is uncertain; the experiment plan should choose the best
available capability-equivalent baseline and record that uncertainty rather
than wait.
