# R208 OSDI Gate Review After R205/R207 Paper Alignment

Last updated: 2026-06-15
Stage at update: supplement / OSDI gate review
Source/command: read-only subagent review over `docs/visexp/RESEARCH_PLAN.md`,
`docs/visexp/EXPERIMENT_PLAN.md`, `docs/visexp/CLAIM_VERDICT.md`,
`docs/visexp/EXPERIMENT_AUDIT.md`, `docs/visexp/FOLLOWUP_PLAN.md`,
`docs/visexp/LONG_TAIL_COMPACTION.md`, `docs/visexp/paper/main.tex`,
R205 compaction metrics, R207 launch-readiness output, and R206 gate review.
Completeness: complete as review; no new participant responses or human labels.

## Verdict

Not OSDI weak accept yet.

The current plan and paper are stronger after adding the reversible long-tail
compaction boundary, R205 compaction metrics, and R207 launch-readiness
handoff. These revisions improve scoping and readiness. They do not provide
outcome evidence for developer utility, semantic adequacy, compaction quality,
or community adoption.

The honest maturity level remains Level 3: conference-paper mechanism evidence,
not Level 4 systems narrative.

## Must-Fix Evidence Gates

1. **C5 developer utility remains unsupported.**
   R207 is logistics only: the R142 response template is blank, there are no
   real participant responses, `c5_supported=false`, and real participants are
   required. Fix by running the frozen R142 pilot with real participants,
   scoring returned responses through the frozen R142/R195 contract, then
   running R151 or explicitly limiting claims to pilot evidence.

2. **C6 semantic adequacy remains unproven.**
   R180 supports syntax/stability only. The R124 label sheets are blank, with
   0 final labels and `adequacy_supported=false`. Fix by collecting two
   independent human label sheets over the 300 R124 rows, adjudicating
   disagreements, and reporting adequate/generic/misleading rates plus
   agreement. LLM, subagent, mock, or placeholder labels do not count.

3. **Compaction quality cannot be claimed from R205 alone.**
   R205 provides useful metrics: raw/canonical unique tags 1,546 -> 1,364,
   top-20 support coverage 93.683% -> 95.186%, and review-required support
   1.926%. However, R190 merge-quality rates are still `n/a`, R203 final labels
   are 0, and the canonical map is not updated. Fix by collecting R190
   merge-risk labels and R203 promotion labels before claiming merge quality or
   regenerated-tag quality.

## Should-Fix Scope Gaps

1. **Exact lineage scope remains narrow.**
   R114 is strong for a fixed 20-task command-mode suite. R182 is a record-mode
   `--trace-net` implementation smoke, but target-specific loopback/expected
   child-process network rows remain 0/0. Broader provenance claims require
   R191-style target-specific network lineage and cross-repo/more-agent
   replication.

2. **Community artifact readiness remains partial.**
   R160 and R200 are useful local smoke tests, including a public-safe generated
   fixture path. They are not an external-machine fresh-clone run, public
   real-report sanitization proof, full write-set audit, or external developer
   feedback.

## Positive Delta From This Revision

- The reversible long-tail compaction boundary is now explicit and auditable:
  raw tags remain immutable, canonical labels are a versioned display overlay,
  and regenerated tags need paired/adjudicated promotion review.
- R205 gives reviewer-checkable aggregation metrics without overclaiming
  adequacy or merge quality.
- R207 removes collection ambiguity by checking participant packets, blank
  response templates, blank R124/R190/R203 sheets, READMEs, and R195 return-file
  names.
- The paper now says the current version is not weak accept and keeps C5/C6
  limitations explicit.

## Next Highest-Value Actions

1. Run the real R142 pilot and score returned responses.
2. In parallel, collect R124 adequacy labels with two independent labelers and
   adjudication.
3. If compaction quality is a paper claim, collect R190 and R203 labels.
4. After real C5/C6 results exist, rerun the OSDI gate review and revise paper
   claim wording from scored outputs.
