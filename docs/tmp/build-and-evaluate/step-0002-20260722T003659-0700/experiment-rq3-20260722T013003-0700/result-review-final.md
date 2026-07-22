# RQ3 Independent Result Review

**Verdict: BLOCK**

The frozen data derivation is internally consistent, but the current F6 and
reported top-10% statistic do not yet implement the approved plan faithfully.
The blockers are figure/reporting defects; I did not find evidence that the
13,150-episode derivation itself is corrupted.

## Independent recomputation

- All recorded RQ1 input hashes and all recorded RQ3 output hashes match the
  files currently under review.
- A clean rerun reproduced the three CSV hashes and both PNG hashes exactly.
  The PDF hashes changed only because Matplotlib embeds a new `CreationDate`;
  this is a non-blocking byte-reproducibility limitation of the PDFs.
- All 13,152 RQ1 mutation rows resolve to the frozen source event JSON, with
  matching source call, session, vendor, timestamp, worktree-scoped path, and
  action operation. Their recorded `event_index` equals the event's exact
  index in the frozen per-project Tool-action sequence.
- Collapsing by `(project, worktree_id, artifact_id, event_id)` produces
  exactly 13,150 episodes. The two collapsed compound groups are both in
  ActPlane. Episode ordinals, first/repeat classification, cross-session
  classification, operation labels, and per-artifact loads all match the
  exported RQ3 CSVs.
- Denominators reconcile exactly: 7,154 observed identities, 2,219 mutated
  identities, 13,150 mutation episodes, and 13,152 raw mutation rows.
- The per-project reported loads and repeat fractions recompute exactly. The
  episode totals are 6,482, 5,768, 283, 170, 196, and 251; the corresponding
  repeat totals are 4,857, 5,297, 251, 122, 175, and 229.
- All four birth states are retained. The all-identity birth-state counts and
  the conditional medians/denominators in the sensitivity figure recompute
  exactly. No birth category was silently dropped.
- Every project passes the preregistered minimum of 20 episodes and 10 mutated
  identities. The CCDF and concentration curves use episode counts rather
  than raw mutation rows.

## Blocking findings

### 1. Panel C is not the preregistered exact Tool-action-prefix curve

The renderer orders individual artifact episodes and calls `plot(xs, ys)`.
It therefore exposes an arbitrary within-action artifact order when one Tool
action mutates several artifacts, then linearly connects observations across
action ranges in which the statistic is constant. This is material: 829 Tool
actions contain multiple artifact episodes (2,281 episodes in total), including
656 such actions in AgentSight and 125 in ActPlane.

For an exact action-prefix statistic, all episodes at one `event_index` must be
added atomically, and the curve must be rendered as a post-action step function.
The endpoint fractions are correct, but the current path between endpoints is
not the exact action-prefix evolution claimed by the panel annotation.

### 2. F6 omits preregistered denominators and composition annotations

The approved plan requires F6 to print the all/mutated identity, episode, and
raw-row denominators and to annotate cross-session share plus rename/delete
composition among repeat episodes. The current figure prints all/mutated
identity denominators, but not episode/raw-row denominators. Panel C gives a
cross-session count rather than a share and omits rename/delete composition;
it also contains no secondary wall-time annotation. `result.md` likewise
omits cross-session and rename/delete composition, although the underlying
summary CSV contains their counts. This fails the plan's explicit figure and
completion requirements.

### 3. “Top-10% episode share” is not an exact 10% statistic

The implementation uses `ceil(mutated_identities / 10)`. For small projects,
the reported group therefore covers materially more than 10% of identities:
4/32 (12.5%) for BPF tutorial, 3/21 (14.3%) for the AgentSkill paper, and 3/22
(13.6%) for Writing skills. The resulting reported shares are respectively
51.9%, 90.8%, and 64.5%; exact 10%-position interpolation on the already drawn
concentration curves gives about 42.0%, 86.7%, and 55.9%. The table must either
report the exact selected `k/n`, interpolate at 10%, or remove the ambiguous
top-10% number and rely on the full concentration curve.

## Claim audit

The figures and report correctly avoid a heavy-tail distribution claim,
convergence claim, thrashing label, defect-repair inference, and waste/failure
interpretation. The explicit warning text is appropriate. Cross-session
repetition is also not presented as forgetting or reset cost. These claim
boundaries should be preserved in any repaired artifact.

## Result judgment

```text
run status: incomplete
tested hypothesis: inconclusive
research value: supporting
paper impact: additional RQ evidence
next paper decision: do not include the current F6 or top-10% numbers; retain the frozen inputs and episode derivation, but regenerate the action-atomic step curve and complete the preregistered annotations/denominators before another result review
```

The valid portion is descriptive evidence for RQ3's mutation-concentration
facet: repeated mutation is concentrated to different degrees across these six
cases, and repeat-observed episodes constitute 71.8%--91.8% of observed
mutation episodes. It does not answer RQ3's convergence, validation-followed
revision, or module-switching facets.
