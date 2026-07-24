# Step 0072 Outer Audit

**Timestamp:** 2026-07-23T21:02:00-07:00  
**Parent:** Step 0072 hierarchical research cycle  
**Objective:** Decide whether the RQ2 EXPERIMENT, WRITE, and REVIEW inner loops
are complete and whether the outer state may advance.

## Inputs and provenance

This audit read the complete user-instruction log and idea-story invariants,
all Step 0072 experiment reports and outputs, the targeted write report, the
four independent whole-paper review reports, the current paper source/PDF, the
new scorer, and the final validation results.

## Gate completion

### EXPERIMENT Gate: PASS

- One fixed hypothesis was tested over all 1,756 trajectories and 27,346
  operations.
- The candidate, local-only control, information-matched raw+evidence control,
  and AgentProf-only component were built before target labels were loaded.
- Standard per-query AP/MAP and paired clustered uncertainty were used.
- Two plan reviews converged before the full run.
- An independent reviewer reimplemented the scorer from raw inputs and exactly
  reproduced every query AP, workload MAP, bootstrap draw, join count, and
  predecessor result.

The experiment provides partial support: Local+AgentProf clearly improves over
local-only, but no semantic-prefix advantage is detected over
Local+Raw+Evidence.

### WRITE Gate: PASS

The body table, protocol, result, uncertainty, adaptivity disclosure, evidence
ledger, closest-work ledger, and story history are synchronized. The A2
backend provenance error is corrected. A final causal-language repair now says
that the observed ranking gain belongs to group/evidence refinement in the
complete profile, not specifically to the semantic prefix; hierarchy and
drilldown remain separate representation capabilities.

The title, thesis, four RQs, contribution scope, and original story did not
change.

### REVIEW Gate: PASS for the cycle; paper routes back to EXPERIMENT

The independent full-paper reviewer classified the paper as
incomplete-but-promising and routed the next outer node to EXPERIMENT. It
accepted Step 0072's implementation and statistics but identified four
paper-level gaps:

1. closest-work coverage must add ACT*ONOMY and distinguish fixed hierarchical
   action taxonomies from variable-depth, source-linked conserved operation
   profiles;
2. RQ1 currently demonstrates a useful multi-resource attribution capability
   more directly than comparative improvement;
3. RQ3 needs stronger evidence that isolates structure from evidence, naming,
   grouping, and scoring, preferably on a fixed-instruction follow-on or
   distinct public family;
4. RQ4 must include automatic annotation and source adaptation rather than
   only fixed-mark profile construction.

The reviewer also flags that the abstract/introduction/conclusion still
foreground older weak-raw comparisons. Those numbers remain true, but the
final whole-paper WRITE must present the matched result as the strongest causal
test. That rewrite is intentionally deferred until the remaining RQs are
updated, so repeated headline editing does not cause story drift.

## Root disposition of reviewer recommendations

Reviewer findings are evidence, not automatic instructions.

- **Accepted:** ACT*ONOMY comparison, end-to-end RQ4 cost, fixed-method RQ3
  confirmation/mechanism isolation, final headline synchronization.
- **Accepted with scope correction:** a downstream population-level decision
  experiment is higher value than another local MAP retuning branch.
- **Not adopted as written:** mandatory human intervention or a newly invented
  hierarchy-labeling benchmark. The author forbids waiting for human
  intervention. Public annotations, independent automatic backends, and
  auditable source-grounded references remain eligible.
- **Not adopted as a story change:** matched-raw parity does not authorize
  shrinking the thesis. It determines which consequence requires stronger
  evidence.
- **Venue-format uncertainty retained:** the repository uses a 12-page
  `acmart` paper while the author has discussed AAAI/NeurIPS quality rather
  than declaring one final submission template. Scientific closure precedes a
  venue-format rewrite.

## User-intent and scope audit

- No RQ, thesis, hypothesis, or contribution was narrowed or replaced.
- No branch was created or switched.
- No skill was modified.
- No frontend or non-pprof product output was added.
- All experiment contracts and reports are Markdown; raw scientific outputs
  use the existing experiment formats.
- The complete public populations were run; no smoke result entered the paper.
- The user's newest RQ1–RQ4 supplement request is preserved as the next outer
  route rather than declared finished by this RQ2 result.

## Completion, uncertainty, and next node

Step 0072 is complete. Its exact scoring branch should not be retuned again.
The paper remains in EXPERIMENT because RQ3 structure isolation and RQ4
automatic-annotation cost are unresolved, and RQ1 needs a sharper comparative
test or an explicit motivation/capability role.

Next node: RQ3 EXPERIMENT Gate. First audit ACT*ONOMY's artifact and the
fixed-instruction 364-session follow-on; select the simplest complete
information-matched experiment that can distinguish recursive operation
structure from naming/evidence effects.
