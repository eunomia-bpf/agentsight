# Common Error Audit — Existing Operation-Stack Trajectories

**Question:** Do the retained complete Step 0024/0025 decisions expose one
benchmark-independent error mechanism that authorizes another modification of
the same action-only recurrence algorithm?  
**Inputs:** retained OSWorld-Human and CodeTraceBench decision files only  
**Candidate runs:** none  
**Conclusion:** no common mechanism is currently identified

## Exact Inputs

- OSWorld Step 0024:
  `.agentsight/experiments/rq3-monotone-recurrence-v1/full/`
- CodeTraceBench Step 0024:
  `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`
- OSWorld rejected Step 0025:
  `.agentsight/experiments/rq3-contextual-recurrence-v1/full/`
- CodeTraceBench rejected Step 0025:
  `.agentsight/experiments/rq3-contextual-recurrence-codetracebench-v1/full/`

The audit joins only existing decisions, visible action sequences, official
scorer labels, NPMI values, cutoffs, folds, and reference inputs. It does not
modify an evaluator or calculate the outcome of a new decision rule.

## Step 0024 Error Shape

| Population / decision class | Decisions | Official boundaries | Predicted boundaries | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| OSWorld-Human, all | 3,691 | 1,755 | 2,369 | 1,402 | 967 | 353 |
| OSWorld-Human, same action | 843 | 657 | 560 | 432 | 128 | 225 |
| OSWorld-Human, action changing | 2,848 | 1,098 | 1,809 | 970 | 839 | 128 |
| CodeTraceBench, all | 20,461 | 2,543 | 6,492 | 1,297 | 5,195 | 1,246 |
| CodeTraceBench, same action | 7,925 | 526 | 0 | 0 | 0 | 526 |
| CodeTraceBench, action changing | 12,536 | 2,017 | 6,492 | 1,297 | 5,195 | 720 |

Both populations contain same-action false negatives and cross-action false
positives, but their boundary priors and decision consequences differ sharply.
The existence of the same confusion category is not enough to authorize one
repair when the visible occurrence is label-ambiguous.

## Observable-Context Aliasing

For each decision, the audit groups occurrences by the action pair and by
progressively larger immediate action contexts. A type is mixed when retained
official labels contain both boundary and continuation occurrences.

| Population | Observable key | Types | Mixed types | Decisions in mixed types | In-sample majority ceiling |
|---|---|---:|---:|---:|---:|
| OSWorld-Human | action pair | 111 | 45 | 91.2% | 78.2% |
| OSWorld-Human | left-action trigram | 320 | 93 | 78.1% | 83.3% |
| OSWorld-Human | right-action trigram | 322 | 90 | 76.1% | 82.4% |
| OSWorld-Human | four-action window | 667 | 111 | 53.8% | 88.0% |
| CodeTraceBench | action pair | 71 | 67 | 99.7% | 87.7% |
| CodeTraceBench | left-action trigram | 453 | 257 | 93.7% | 87.9% |
| CodeTraceBench | right-action trigram | 477 | 283 | 94.8% | 87.9% |
| CodeTraceBench | four-action window | 1,847 | 628 | 81.5% | 88.5% |

The ceiling is diagnostic in-sample majority accuracy, not a valid candidate
result. It shows why adding immediate context has different promise: the gain
from pair to four-action identity is 9.8 points on OSWorld-Human and only 0.8
points on CodeTraceBench, before any held-out or B-cubed penalty. This does not
support one shared context rule.

## Why The Step 0025 Result Is Mechanistically Mixed

| Population | Step 0024 boundaries suppressed | Official boundaries among them | Continuations among them |
|---|---:|---:|---:|
| OSWorld-Human | 842 | 504 | 338 |
| CodeTraceBench | 2,067 | 348 | 1,719 |

The identical label-free local-minimum rule mostly deletes true boundaries in
OSWorld-Human and mostly deletes false boundaries in CodeTraceBench. Its
CodeTraceBench B-cubed gain and OSWorld-Human loss are therefore not noise or
an incomplete run; they expose a population-granularity conflict under the
current action-only output.

## Score And Support Diagnostics

Among Step 0024 predicted boundaries, increasing `applied_cutoff - NPMI` does
not supply a clean shared correction. Boundary prevalence falls across the
first three within-population quartiles on both populations, but the fourth
OSWorld quartile rises again and unseen OSWorld pairs have 60/95 positive
labels. Reference support is similarly non-monotone on OSWorld-Human and has
different scale on CodeTraceBench. Picking a margin, occurrence-count bucket,
or unseen exception would therefore require selecting a new cutoff or special
case from already observed labels.

The cross-action cutoff sign is also unusable as an admission mechanism. All
five OSWorld folds have positive cross-action cutoffs and CodeTraceBench has a
negative cutoff; after Step 0025, the sign exactly identifies which population
favors which rule. There is no within-population or untouched variation that
separates sign from benchmark identity.

Session length does not recover a shared condition either. Reconstructing the
already-observed Step 0025 per-session B-cubed delta yields mean changes of
-0.0072, -0.0065, -0.0254, and -0.0353 for OSWorld length bins below 8, 8--11,
12--19, and at least 20 operations. CodeTraceBench changes are +0.0217,
+0.0218, and +0.0331 for 20--39, 40--79, and at least 80 operations. The local
rule becomes more harmful on longer OSWorld sessions and more helpful on longer
CodeTraceBench sessions, so a length gate would still hide population selection
rather than explain it.

## Scientific Decision

The current evidence supports a limitation of the input contract: action-only
recurrence can provide a useful target-blind partition, but official operation
boundaries are not functions of an action pair or small action window alone.
That does not narrow RQ3 or weaken its positive paper hypothesis. It means only
that another post-hoc flat-segmentation tweak on these same labels is not the
highest-value experiment.

No candidate is admitted. Step 0024 remains the release implementation. A
future change must add a scientifically motivated discriminator or resolution
contract and obtain evidence that is not equivalent to choosing between the
two already-observed population outcomes.
