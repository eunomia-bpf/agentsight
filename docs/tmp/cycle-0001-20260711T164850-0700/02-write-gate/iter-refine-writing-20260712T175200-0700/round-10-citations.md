# Round 10 — Citation Gate

**Started:** 2026-07-12T18:56:44-07:00  
**Completed:** 2026-07-12T19:04:51-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** round-9-language-flow.md  
**Procedure:** complete check-paper-citations gate, including mechanical
verification, claim-citation alignment, academic-integrity checks, and missing
citation scan  
**Verdict:** PASS on citation authenticity and paper use; the mechanical script
retains two documented stale-index false positives

## Entry State And Scope

The bibliography contained 65 entries, and all 65 already had complete
VERIFIED, REAL, PDF, ABSTRACT, and USED_FOR annotations with REAL set to yes.
The paper cites 53 unique keys through 59 citation commands. Twelve unused
entries are retained and explicitly marked STATUS: unused, as required by the
citation skill.

This round read docs/paper/main.tex and docs/paper/references.bib, ran the
mandatory verify_bib.py script twice, checked each cited claim against the bib
annotation and primary source where needed, reviewed publication status, and
scanned the manuscript for uncited systems, techniques, datasets, benchmarks,
and external factual claims. No Git command was run.

## Mechanical Verification

The first script run checked 55 entries and reported five errors across four
entries:

- AgentRewardBench venue;
- OSWorld venue wording;
- OSWorld-Human year and venue;
- AndroidControl venue wording.

It also reported three warnings: the AgentSight workshop qualifier was absent
from the API's generic venue string, and the published API-Bank and GUIOdyssey
titles matched a superficial title-pattern warning.

Primary-source verification showed that:

- AgentRewardBench is published at COLM 2025. The official COLM accepted-paper
  list includes it, and the official OpenReview PDF says “Published as a
  conference paper at COLM 2025.”
- OSWorld and AndroidControl are NeurIPS 2024 Datasets and Benchmarks papers.
  Their official proceedings pages place them in Advances in Neural Information
  Processing Systems and identify the Datasets and Benchmarks track.
- OSWorld-Human is an MLSys 2026 paper. The MLSys 2026 program exposes the
  paper and presentation, while the authors' publication page gives the full
  proceedings citation. DBLP still exposes only the 2025 CoRR record.

The bibliography now uses the formal NeurIPS proceedings name plus a track note
for OSWorld and AndroidControl. AgentRewardBench now uses the full Second
Conference on Language Modeling name. OSWorld-Human now uses the full Ninth
Annual Conference on Machine Learning and Systems name. Verification dates for
these four records are 2026-07-12.

The second script run reduced the result to three errors on two entries:
AgentRewardBench and OSWorld-Human. Both are stale-index false positives: DBLP
still returns the earlier CoRR records and the script prefers DBLP over the
official conference sources. The paper retains the later, primary-source-backed
published metadata. Downgrading either entry to a preprint merely to satisfy the
script would violate the skill's published-version rule and make the
bibliography less accurate.

The remaining warnings require no paper change. AgentSight's DOI and paper
identify the PACMI workshop even though the generic API venue omits “workshop.”
API-Bank and GUIOdyssey are real published papers; their titles, authors,
venues, and URLs match official proceedings.

## Claim-Citation Alignment

All 53 cited keys have a clear use in the paper:

- Codex, Claude Code, SWE-agent, and OSWorld support the introductory
  multi-step-agent context.
- AgentRewardBench and the LLM-as-judge paper support the cost and form of
  per-trajectory evaluation.
- LangSmith, Langfuse, Phoenix, OpenTelemetry, Perfetto, pprof, domain-specific
  profiling, Pivot Tracing, Datadog, Laminar, and Hodoscope support the
  observability, aggregation, and cross-run comparison boundaries.
- AgentSight supports intent/system evidence capture and the supported input
  path.
- TF-IDF, K-Means, and V-measure are cited at their method and metric uses.
- Every named public trajectory family in Experimental Setup cites its source at
  first mention.
- Differential flame graphs support the RQ2 before/after profile design.
- Every Related Work grouping has direct citations matching the described
  function: tracing, profiling, localization, diagnostic annotations,
  cross-run comparison, and intervention.

No cited source was found to contradict or overstate its surrounding claim. No
secondary-source substitution, retraction, identity leak, or unexplained ghost
citation was found.

## Stale Annotation Repairs

The bib annotations no longer describe abandoned experiments as current:

- Hodoscope is now the closest cross-run cohort comparison in Introduction and
  Related Work, not a “completed RQ2 comparator.”
- AgentRx and TELBench are Related Work localization comparisons, not current
  RQ2 workloads.
- Eleven public-family entries now point to Experimental Setup and RQ3 where
  applicable rather than a nonexistent evaluation table.
- llama.cpp and the mini-batch K-Means paper are explicitly marked unused
  because the current paper does not cite them.

## Missing Citation Scan

No missing citation was added. All external systems and public datasets are
cited at first substantive mention. The uncited numerical statements are the
paper's own measurements and are explained in Evaluation. Rust, JSONL, additive
weighting, ordinary Jaccard similarity, and Shannon entropy do not require new
citations in the current sentences. Adding citations there would increase
density without supporting a disputed external claim.

## Outcome Counts

- Bibliography entries with complete annotations: 65 of 65
- Cited unique entries reviewed: 53
- Hallucinated citations: 0
- Inaccurate claim uses fixed: 0
- Missing citations added: 0
- Bib metadata records corrected: 4
- Stale USED_FOR annotations corrected: 14
- Newly marked unused entries: 2
- Remaining mechanically flagged entries: 2, both resolved against newer
  primary conference sources

## Preservation And Verification

No paper claim, RQ, number, citation command, or citation placement changed.
The citation-command count remains 59. The exact thesis and four RQ meanings
remain unchanged.

make completed successfully. main.log and main.blg contain no undefined
citation/reference, LaTeX error, emergency stop, overfull-box report, or missing
bib entry. The PDF remains 9 letter-size pages, and the Abstract remains exactly
200 words.

No shared skill, submodule, canonical research document, or user instruction
file changed.

## Next Node

The eleven-round writing loop is complete. Run a fresh independent outer WRITE
audit over the complete paper and all round reports. The audit must distinguish
the completed writing gate from the incomplete empirical answers and must not
recommend shrinking the thesis or four fixed RQs.
