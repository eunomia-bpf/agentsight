# Authoritative AgentProf Paper Re-restoration

**Timestamp:** 2026-07-13 12:27:50 America/Vancouver  
**Outer-cycle position:** cycle 0003, before the RQ2 EXPERIMENT inner loop  
**Disposition:** complete baseline correction; resume EXPERIMENT next  
**Paper authority:** read-only `docs/agentpprof-paper/main.tex`  
**Editable paper:** `docs/paper/`

## Trigger And Scope

The author supplied a complete 809-line LaTeX paper and confirmed that this is
the intended original AgentProf version. Line-ending-normalized comparison
showed that the supplied file is identical to the current submodule
`main.tex`. The author had already prohibited changes to the submodule and
required the editable paper to begin from its problem, motivation, model,
system direction, contribution structure, and four RQs.

This node corrects the active paper baseline only. It does not change the
thesis, RQs, hypothesis, experimental plan, research skills, source selection,
or the submodule. It does not interpret any historical empirical number as
newly authorized evidence.

## Pre-restoration Finding

Commit `eb5f332e` had previously converted the canonical paper to the AAAI-27
anonymous-submission wrapper. Extracting its abstract and scientific sections
from Introduction through Conclusion and comparing them to the submodule
produced zero diff lines.

Cycle 0002 subsequently rewrote `docs/paper/main.tex`. It retained the exact
thesis sentence and four RQ headings, but changed the abstract, introduction,
background, design, evaluation narrative, related work, and conclusion. The
same normalized scientific-body comparison between that active paper and the
submodule produced 1,299 diff lines. Therefore the active paper no longer
implemented the author-designated baseline even though `docs/idea-story.md`
still said it did.

## Archive

The complete pre-correction `docs/paper/` workspace was copied to:

`docs/tmp/agentpprof-paper-pre-authoritative-rerestore-20260713T122602-0700/source/`

Its archive README records its provenance, why it is not a narrative authority,
and which individually verified citations or presentation improvements may
still be recovered later.

The older Chinese paper remains independently archived at:

`docs/tmp/agentpprof-paper-zh-20260711/source/`

Neither archive was used as the current story authority.

## Restoration

The active paper files changed by cycle 0002 were restored to their
`eb5f332e` state. That state contains the exact submodule scientific body and
bibliography under the official AAAI-27 submission wrapper. Cycle-0002-only
architecture outputs were removed from the active paper after being preserved
in the archive. Unrelated canonical documents, experiment reports, and source
archives were not reverted.

## Verification Evidence

1. Extracted scientific body, submodule versus active paper: **zero diff**.
2. Active bibliography versus verified AAAI restoration: **identical**.
3. Submodule status after restoration: **clean**.
4. `make -B` in `docs/paper/`: **success**.
5. Generated paper: **8 pages**, US Letter, AAAI-27 style.
6. Build log: no undefined citations, undefined references, or LaTeX errors.
7. The exact thesis remains: **“Agent observability needs profiling, not only
   debugging.”**
8. Evaluation retains exactly four RQs: resource attribution, correspondence
   to real problems, tag accuracy, and profiling cost.

## Scientific Meaning

This restoration reinstates the largest author-approved story. It does not
erase the evidence audits from cycles 0001–0002. The original positive numbers
remain the intended claim surface, while `docs/evaluation.md` and timestamped
experiment reports remain authoritative about which results are verified,
superseded, or still require a complete rerun.

The next state is still the admitted RQ2 EXPERIMENT gate. That experiment must
improve evidence for the original localization hypothesis; it may not replace
the paper story, narrow the RQ, or edit the paper before WRITE.
