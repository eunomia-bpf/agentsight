# REAL PREFLIGHT — Recurrence-Based Operation-Stack Induction

**Executed:** 2026-07-15T00:50:00-07:00
**Status:** **COMPLETE; awaiting independent preflight review**
**Scientific role:** implementation/dependency check only; no experiment verdict

## Command

```bash
python3 script/rq3_recurrence_stack_induction_eval.py \
  --mode preflight \
  --out-dir .agentsight/experiments/rq3-recurrence-inducer-v1/preflight
```

The command exited successfully and wrote the declared summary, predictions,
session partitions, candidate operation file, and real AgentProf profile.

## Complete Fold-0 Coverage

- training: 242 sessions and 3,215 adjacent transitions;
- held out: all 45 fold-0 sessions, 521 operations, and 476 adjacent pairs;
- predictions: exactly one for every held-out pair;
- candidate assignments: exactly one for every held-out operation;
- unseen held-out transitions: 10, all handled by the registered boundary rule.

The source loader also revalidated the complete underlying population of 287
sessions, 3,978 operations, 3,691 adjacent pairs, and 2,042 human groups before
selecting fold 0.

## Fixed Algorithm Diagnostics

The fold-0 training population contained 102 unique ordered action pairs, 21
unique left actions, and 22 unique right actions. Deterministic occurrence-
weighted two-means converged in two iterations:

- low center: -0.0113841661 over 1,731 transition occurrences;
- high center: 0.4737209683 over 1,484 occurrences;
- fixed midpoint cutoff: 0.2311684011.

The candidate emitted 267 held-out groups and 25 unique run-length-compressed
action motifs. Group length ranged from 1 to 38 operations with median 1.
Every score and center was finite.

## Real AgentProf Integration

Current release `agentpprof 0.2.37` consumed the complete 521-row held-out
candidate operation file using stack `project,dataset,operation`. It returned
status `ok`, 521 samples, total profile weight 521, and 25 unique stacks. No
scorer-only field survived into the candidate operation file, and input/profile
mass was exactly conserved.

## Descriptive Output, Not A Verdict

Fold 0 alone produced boundary F1 0.4947589099 and operation-weighted B-cubed
F1 0.6991912305. The current information-gain baseline on the same fold was
0.4960937500 and 0.69910699999; always-boundary was 0.6976744186 and
0.7308160780. This fold is deliberately not interpreted as support, rejection,
or a tuning signal. The approved plan registers only one complete five-fold
run as the scientific test, and no field, cutoff, rule, fold, or metric changes
follow from preflight output.

## Artifacts

- `.agentsight/experiments/rq3-recurrence-inducer-v1/preflight/summary.json`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/preflight/pair-predictions.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/preflight/session-results.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/preflight/candidate-operations.jsonl`
- `.agentsight/experiments/rq3-recurrence-inducer-v1/preflight/candidate-profile.json`

No paper, Rust implementation, or read-only submodule file was edited.
