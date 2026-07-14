# Plan Review Round 2 — R337 Reuse Audit

## Review metadata

- **Review date:** `2026-07-14`
- **Plan reviewed:** `100-proposed-experiment-plan.md`
- **Prior review:** `110-plan-review-round-1.md`
- **Review scope:** only the three round-1 blockers and absence of scope
  expansion.
- **Edits performed by reviewer:** this report only. No plan, code, paper,
  skill, or Git change.

## Verdict

**PASS.** All three round-1 blockers are fixed with no experiment redesign or
scope expansion. No further plan change is required before round 3.

## Blocker resolution

### 1. REAL PREFLIGHT — fixed

The plan now runs the actual lightweight R337 target-extraction command into a
dedicated preflight directory. It requires the resulting output to contain all
six tasks, the existing 25% target, and the four required policies. This
executes the real summarizer and write path while correctly limiting the
preflight conclusion to executability.

### 2. Fixed-input equivalence topology — fixed

The plan now truthfully states the script topology:

- R333 reruns the R320 grouping and scoring implementation directly over the
  four existing public operation sources;
- R337 reads the repository's fixed R333 artifacts rather than the temporary
  R333 output; and
- fresh R333 scientific-output equivalence must pass before the fixed R337
  inputs are treated as equivalent.

The redundant standalone R320 replay is removed. Exact R333 and R337 commands
are present. Complete claim-bearing CSVs are compared with `diff`, and only
named scientific JSON fields are compared with `jq`, excluding elapsed-time
and commit/provenance metadata. This is executable without a new runner or
custom audit script.

### 3. Visible-field derivation audit — fixed

The plan now requires a read-only source-lineage audit in
`script/agent_trace_datasets.py`. It records that visible ranking fields come
from action signatures, actions, independent system/task outcomes, and source
metadata, while the AgentReward looping/side-effect, SATraj safety, AgentNet
step-correctness/redundancy, and OSWorld group-position fields remain distinct
target labels. It also records the public source identifiers. This closes the
upstream-derived-label gap rather than relying only on a visible/hidden field
name intersection.

## Scope audit

The revision adds no dataset, benchmark, model, annotation, policy, baseline,
recall target, metric, matched-cardinality construction, interpolation,
resampling, custom script, or paper claim. The tested hypothesis, decision
rule, six-task scope, existing 25% target, and supporting-evidence boundary are
unchanged. The plan remains one small reuse/equivalence audit.
