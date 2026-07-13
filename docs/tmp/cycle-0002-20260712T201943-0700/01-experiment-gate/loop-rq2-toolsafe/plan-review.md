# ToolSafe Experiment Plan Review Log

**Review policy:** serial independent review using
`research-experiment-design`; minimum three and maximum five plan-review rounds.
Implementation is forbidden until the plan converges to PASS.

## Round 1 — 2026-07-13 — REVISE

The first valid independent reviewer read the complete source audit, plan, and
official ToolSafe artifacts. Two responses from a context-polluted prior
reviewer were rejected and do not count as review rounds because they answered
an unrelated paper-recovery question.

### Must-fix findings

1. The raw-tool baseline was not equally informed. The semantic triple
   deterministically refines the official risk rating, while raw tool discarded
   that detector signal and mostly used a global fallback. The required main
   baseline is `risk_rating -> exact_raw_tool`, with unseen joint keys backing
   off to the same risk-rating density. Exact-tool-only remains a lower-bound
   control.
2. Target-label isolation was declarative rather than real. Official
   `meta_data.json` embeds `meta_sample.score` and ASB attack metadata. Source
   preparation must emit an allowlisted unlabeled projection and separated
   per-family label tables; prediction accepts only the projection and the two
   named reference label tables; held-out labels first enter a separate scoring
   command after predictions exist.
3. Reference labels are valid published benchmark annotations, not independent
   deployment outcomes. Strict unsafe/controversial is primary, while official
   unsafe-only/loose mapping is mandatory robustness. A loose-mode reversal
   forbids an unconditional unsafe-operation interpretation.
4. Bootstrap cluster identity and resampling were underspecified. Every paired
   replicate must resample `(family, source file, id-interaction)` clusters
   independently within all three families, reuse the same draws for every
   method, reconstruct each fold's reference densities, and continue to 10,000
   valid paired replicates.
5. Tie and coarse-group loopholes remained. One label-blind tie-block rule,
   `Work@5`, maximum-group share, family results, and operation-level primacy are
   required. Eleven cells establish mechanism engagement, not localization.
6. The plan needed an exact role, commands, cost, terminal execution rule, and
   distinct supported/mixed/contradicted/inconclusive decisions. The valid role
   is supporting RQ2 evidence that structures an external detector, not a claim
   that AgentProf independently detects safety failures.

### Answers to the six review questions

1. Published TS-Guard outputs are a valid external signal, but the experiment
   can establish transfer from a finer structured partition, not independent
   safety detection or causal discovery.
2. Risk-only is strong; exact raw tool with global fallback is not matched.
   Risk-conditioned raw tool with risk-only backoff is required.
3. Leave-one-family-out is scientifically valid only after the source
   projection and held-out-label process are physically separated.
4. Excluding visible non-tool calls is justified because AgentProf profiles
   operations, provided the complete-set compatibility result remains and parse
   failures are not silently excluded.
5. Operation AP/work and family directions are necessary but insufficient
   without exact tie handling, group-size/work reporting, unsafe-only
   robustness, and the stronger raw baseline.
6. The core can remain simple: three folds, one semantic profile, two matched
   alternatives. Controls must not clutter or alter the main verdict.

### Revision 2 response

Revision 2 implements all six must-fix items without changing RQ2, the four-RQ
program, positive hypothesis, thesis, canonical story, or paper. It adds no
non-Markdown contract, freeze protocol, Git gate, or human wait.

## Round 2 — 2026-07-13 — REVISE

The same independent reviewer reread the complete Revision 2 plan, source
audit, and review log using `research-experiment-design`.

### Must-fix finding

Revision 2 gave an unseen `risk_rating -> raw_tool` key the correct risk-only
backoff but did not grant an unseen semantic triple the same backoff, even
though the triple deterministically maps to a risk rating. This left the two
refined main views asymmetric. Both must use:

```text
seen refined key -> refined-key density
unseen refined key -> corresponding risk-only density
absent risk key -> global reference prevalence
```

All fallback types and counts must be reported.

### Round 1 closure audit

- Equal-information baseline: partially closed only because of the asymmetric
  semantic fallback.
- Target-label isolation: closed at plan level; implementation remains a
  preflight audit item.
- Ground-truth meaning and unsafe-only robustness: closed.
- Paired interaction bootstrap: closed.
- Tie and coarse-group controls: closed.
- Role, commands, cost, and completion rule: closed.

### Revision 3 response

Revision 3 applies identical risk-only backoff to unseen semantic and raw-tool
refinements. It also makes nonempty unparsed actions execution failures,
clarifies that the 10x comparison uses the matched risk-conditioned raw view,
states that bootstrap prediction artifacts precede held-out-label scoring, and
marks the preliminary baseline text in the source audit as superseded. No new
method, metric, gate, claim, or paper change was introduced.

## Round 3 — 2026-07-13 — PASS

The same independent reviewer reread Revision 3 and all supporting reports
using `research-experiment-design`.

### Verdict

**PASS.** There are zero remaining must-fix items. Implementation is authorized
exactly under Revision 3, followed by real preflight and independent preflight
review. Paper, story, RQ, thesis, and skills remain outside this authorization.

### Closure table

| Prior item | Status | Verification |
|---|---|---|
| Equal-information raw baseline | CLOSED | Main raw view is `risk_rating -> raw_tool`; both refined views use identical risk-only backoff. |
| Target-label isolation | CLOSED | Preparation strips labels/attack metadata; prediction receives only the allowlisted projection and two reference-label tables; held-out labels first reach scoring after predictions exist. |
| Ground-truth meaning | CLOSED | Strict labels are benchmark-positive triage targets; unsafe-only robustness bounds stronger interpretation. |
| Paired cluster bootstrap | CLOSED | Family-scoped clusters, shared method draws, fold reconstruction, both mappings, and 10,000 valid replicates are explicit. |
| Ties/coarse grouping | CLOSED | Whole-block operation metrics, `Work@5`, maximum-group share, family tables, and operation-level primacy prevent compression gaming. |
| Role/executability | CLOSED | The experiment profiles an external detector; commands, cost, completion, and four outcomes are explicit. |
| Symmetric fallback | CLOSED | Both unseen refinements back off to risk density; only absent risk uses global prevalence. |

### Non-blocking notes

The reviewer suggested four optional reporting clarifications: interpret family
direction using AP; state the descriptive per-interaction aggregation; enlarge
the neutral preflight prefix if it accidentally lacks a class; and prefer
“structured semantic judgments” to “causal hierarchy” in result prose. None
changes the approved method or verdict and none is required before
implementation.
