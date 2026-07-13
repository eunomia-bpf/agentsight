# Serial plan reviews: finite-evidence AgentProcessBench ranking

## Round 1

**Reviewed:** 2026-07-13T06:15:08-07:00

**Plan read:** Revision 1

**Required skill:** `research-experiment-design`

**Reviewer mode:** independent and read-only

**Verdict:** **REVISE**

The reviewer read the complete skill, plan, method-selection report, prior
AgentProcessBench plan and full result, `docs/evaluation.md`,
`docs/user-instruction.md`, and the complete idea-story. It did not edit files
or calculate outcomes from human labels.

The reviewer found the core experiment scientifically worth executing:

- exact thesis, fixed RQ2, positive hypothesis, `target`, and complete raw leaf
  are preserved;
- all four real benchmark families and all operations remain;
- raw and semantic use the same external score and evaluation budget;
- query-cluster bootstrap, matched refinement shuffle, and atomic ties are
  appropriate;
- no extra benchmark, gate, Git/freeze mechanism, non-Markdown contract, or
  scope narrowing is needed.

### Must-fix 1: zero-vote groups

Revision 1 assigned `score_g = 0.5` when `n_g = 0`. That contradicts a lower-
evidence ranking: an unsupported group could outrank groups with observed
harmful votes but lower scores. Revision 2 assigns zero-vote groups score 0,
keeps their operations in all denominators and metrics, reports every such
path, and adds a focused test.

### Must-fix 2: benchmark-reuse evidence role

Materializing scores before loading labels prevents direct implementation
leakage but cannot turn a reused target into a new holdout. Revision 2 names the
planned role `supporting adaptive within-benchmark construction evidence`,
limits decisiveness to this fixed construction, and predeclares paper decisions
for `SUPPORTED`, `CONTRADICTED`, `INCONCLUSIVE`, and `INCOMPLETE`.

### Must-fix 3: unique atomic-tier AP

Revision 1 prohibited tie-breaking but did not uniquely define AP. Revision 2
fixes threshold/tier-end AP as:

```text
AP = sum_k (Recall_k - Recall_(k-1)) * Precision_k
```

Both precision and recall are computed after opening each complete score tier.
The implementation must match the previously audited scorer.

### Simplicity cleanup accepted by the root agent

Revision 2 removes adapted FirstErrAcc and binary accuracy from this experiment.
A Wilson score greater than 0.5 means unusually strong finite-ensemble support,
not the same probability threshold used by the mean-risk experiment, so those
non-decision metrics would be difficult to compare and add no necessary
evidence.

**Round-1 disposition:** all three must-fix items are addressed in Revision 2.
Round 2 must independently read and review the complete revised artifacts.

## Round 2

**Reviewed:** 2026-07-13T06:24:35-07:00

**Plan read:** Revision 2

**Required skill:** `research-experiment-design`

**Reviewer mode:** independent and read-only

**Verdict:** **REVISE**

The second reviewer independently read the complete revised artifacts and
verified all three Round-1 fixes. It found no remaining problem in the Wilson
formula, zero-vote handling, benchmark-reuse role, atomic AP, label sequencing,
query-cluster bootstrap, matched shuffle, baseline fairness, AgentProf realism,
execution paths, or story/RQ/hypothesis preservation.

### Must-fix: family-local group identity

Revision 2 wrote stack keys without an explicit `family` component. The source-
only screen, prior scorer, shuffle, bootstrap, and equal-family macro all imply
family-local scoring, but a literal implementation could pool identical stack
keys across families and change every score and outcome.

Revision 3 defines every scoring group as:

```text
(family, AgentProf stack key)
```

Votes never pool across families. Flat is one group per family, and the rule
applies to point estimates, controls, and every bootstrap draw. The focused
test plan now requires identical-looking keys in different families to remain
separate.

**Round-2 disposition:** the sole must-fix is addressed in Revision 3. Round 3
must independently audit the complete plan and return zero must-fix before
REAL PREFLIGHT.
