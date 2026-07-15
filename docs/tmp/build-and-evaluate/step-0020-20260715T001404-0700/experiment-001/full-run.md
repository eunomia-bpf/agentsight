# FULL RUN — Recurrence-Based Operation-Stack Induction

**Executed:** 2026-07-15T00:54:47-07:00
**Execution status:** **COMPLETE**
**Registered verdict:** **SUPPORTED, pending independent result review**
**Scientific role:** post-hoc mechanism development on an already observed
population; not fresh RQ3 confirmation

## Command

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode full \
  --out-dir .agentsight/experiments/rq3-recurrence-inducer-v1/full
```

The command exited successfully after the single registered complete run. No
field, fold, cutoff, metric, control, population, or algorithm rule changed
after preflight.

## Complete Population And Integration

All five held-out folds jointly covered exactly 287 sessions, 3,978 operations,
3,691 adjacent pairs, and 2,042 human groups once. Their training partitions
were session-disjoint. All 3,691 pairs received one held-out prediction and all
3,978 operations received one candidate group and motif.

Across folds, deterministic two-means converged in two or three iterations.
Cutoffs ranged from 0.2311684011 to 0.3376588161. Ninety-five held-out
transitions were unseen and followed the registered boundary rule. The result
contained 2,656 predicted session-local groups and 44 recurring motif frames;
group length ranged from 1 to 80 with median 1.

Current release `agentpprof 0.2.37` consumed the complete 3,978-row candidate
operation file, produced 44 unique `project,dataset,operation` stacks, and
conserved exact total weight 3,978.

## Registered Primary Metrics

| Method | Boundary F1 | B-cubed F1 |
|---|---:|---:|
| Current cap-free information gain | 0.4719694746 | 0.6720062682 |
| Strongest simple control: always boundary | 0.6445097319 | 0.6784053156 |
| Recurrence candidate | **0.6799224054** | **0.7861695437** |
| Supervised out-of-fold comparator | 0.7387678235 | 0.8160191831 |

The candidate improves over the current information-gain implementation by
+0.2079529308 boundary F1 and +0.1141632755 B-cubed F1. It exceeds the strongest
simple control by +0.0354126735 and +0.1077642281 respectively. Therefore the
mechanically computed registered verdict is `supported`.

Candidate boundary precision is 0.5918 and recall 0.7989. Its B-cubed precision
is 0.8558715355 and recall 0.7269656216. These values show that the candidate
does not merely reproduce the always-boundary partition: it joins recurring
action transitions while retaining substantially higher partition fidelity.

## Claim Boundary

If the independent reviewer reproduces the result, this complete run supports
one implementation decision: cross-session label-free-at-prediction transition
association is a better candidate than the current per-session information-
gain inducer for segmenting this existing OSWorld-Human population. It is also
close to, but does not exceed, the supervised extra-information comparator.

Because the population's labels influenced earlier failure diagnosis and
candidate selection, these numbers are post-hoc development evidence. They do
not become fresh paper confirmation, validate literal motif names, establish
phase/action semantic identity, prove cross-family generalization, or answer
all RQ3. A supported independent review authorizes only a minimal Rust port and
mechanical Python-versus-Rust equivalence check before later independent
confirmation.

## Raw Artifacts

- `.agentsight/experiments/rq3-recurrence-inducer-v1/full/summary.json`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/full/pair-predictions.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/full/session-results.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/full/candidate-operations.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/full/candidate-profile.json`

No paper, Rust implementation, or read-only submodule file was edited during
the run.
