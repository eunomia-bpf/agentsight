# Round 10 — Citation Verification

- Parent: WRITE gate, cycle 0002
- Writing run: `iter-refine-writing-20260713T073140-0700`
- Recorded evidence window: 2026-07-13T09:44:16-07:00 to 2026-07-13T09:56:42-07:00
- Skill: `check-paper-citations`, full Pass 1, Pass 2, Pass 2.5, and Pass 3
- Entry paper: the Round-9 paper recorded in `1000-round-9-paragraph-flow-final-prose.md`
- Exit paper: `docs/paper/main.tex` SHA-256 `a6ff6f221c3400daa6a6f3d43176f9bcbb809f6073c5e96e410024401316a36b`
- Exit bibliography: `docs/paper/references.bib` SHA-256 `c4253a9d078d196db834ded9078a93b5d5be26863fef68b25e71dffc895be4c0`
- Exit PDF: `docs/paper/main.pdf` SHA-256 `ff602da01e20ae33599babcaa536b7cab3f74695eb2020f7146fe5cf3d75c0be`
- Verdict: **PASS WITH EXPERIMENT OBLIGATIONS UNCHANGED**

## Post-round correction — 2026-07-13T10:15:32-07:00

The later independent WRITE outer audit found two omissions in this round's
claim of a complete missing-citation and format pass. First, it did not close
the earlier source obligation for the Introduction's “thousands to millions”
scale statement. Second, it added the `pprof` citation inside the abstract,
although the official AAAI-27 Author Kit prohibits references in abstracts.
The current paper corrects both defects in the separate targeted-repair node;
the historical hashes and counts below remain the true Round-10 exit snapshot.
This round's unconditional citation-completion implication is therefore
superseded, not retroactively rewritten.

## Objective and authority

This round verifies that every bibliography entry exists, that every citation
supports the surrounding claim, and that named systems, methods, metrics, and
datasets have primary citations. The bibliography annotations remain the only
canonical citation-verification state; this node is the writing-round report,
not a second citation ledger.

Before acting, the root reread `docs/user-instruction.md`, the complete
`docs/idea-story.md`, the Round-9 report, the complete paper, and the complete
bibliography. The fixed authority was preserved:

- title and central thesis remain `AgentProf: Semantic Profiling for AI Agents`
  and “Agent observability needs profiling, not only debugging”;
- the four RQs remain resource attribution, real-problem localization, tag
  accuracy, and profiling cost;
- the read-only submodule remains the story source and was not edited;
- citation corrections may improve source fidelity but may not replace or
  narrow the paper's scientific position.

No Git operation was performed by this writing or citation skill.

## Mechanical pre-check and final verification

The mandatory verifier was run before and after manual work:

```text
python3 .../check-paper-citations/scripts/verify_bib.py references.bib
```

The first stable pre-check covered 35 then 37 active entries as annotation and
venue corrections activated previously misclassified citations. The final run
covered all 42 cited entries among 52 total entries:

```text
Found 52 bib entries (42 active)
Total entries checked: 42
Errors (must fix): 0
Warnings (should review): 2
OK: No VERIFIED entries have mismatches
```

The two warnings are false-positive title heuristics for the real, source-checked
titles “API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs” and
“GUIOdyssey: A Comprehensive Dataset for Cross-App GUI Navigation on Mobile
Devices.” Their titles were not changed.

Final annotation and use counts are:

| Check | Count | Result |
|---|---:|---|
| Bib entries | 52 | complete |
| `% VERIFIED:` | 52 | complete |
| `% REAL: yes` | 52 | complete |
| `% PDF:` | 52 | complete |
| `% ABSTRACT:` | 52 | complete |
| `% USED_FOR:` | 52 | complete |
| Explicitly retained unused entries | 10 | retained, not deleted |
| Unique cited keys | 42 | exactly matches 42 generated `\\bibitem`s |
| Citation commands | 51 | no undefined citation |

Twenty-one entries point to official documentation, specifications, project
repositories, or unavailable PDFs and therefore say `PDF: not available`; all
were nevertheless verified through stable first-party URLs or API metadata.
They are not unverified entries.

## Pass 1 — existence, metadata, and source reading

The ten entries whose annotation blocks were initially incomplete were checked
against primary sources and given complete blocks: Landlock's official site and
Linux Security Summit slides; the official Linux manual pages for Landlock,
seccomp, seccomp user notification, `pidfd_getfd`, and capabilities; Anthropic's
Claude Code documentation; the MVVM and AgentCgroup arXiv papers; and the Kgent
ACM/DOI record plus its available preprint. Existing `osworld` and `opencua`
annotation fields were completed rather than deleting the entries.

Two new source PDFs were retained from this audit:

- `docs/reference/2017-salaun-landlock-lss.pdf`, SHA-256
  `3809221e6813e3de96633fc1327c1e9270b3797a96532e3fca5476dffb627f25`;
- `docs/reference/2024-zheng-kgent.pdf`, SHA-256
  `1a49785cc23a8bd4f085b127991a947c99f55c5a330ca4a5c19392e76d259880`.

The audit found and fixed two real metadata/venue defects:

1. `osworld` had an incorrect author list. It now uses the complete official
   NeurIPS author list, official proceedings URL, and DOI
   `10.52202/079017-1650`.
2. `agentfixer` had been represented as a published workshop proceedings paper
   while its DOI resolved only to arXiv. The official ICSE 2026 AGENT program
   confirms acceptance, but no indexed proceedings DOI is available. The entry
   now truthfully records the accepted workshop status and cites the arXiv
   record instead of claiming a nonexistent proceedings publication.

No hallucinated entry and no retraction notice were found. The paper contains
no first-person self-citation or double-blind identity disclosure.

## Pass 2 — claim/citation alignment

Every `\\cite{}` context was read with its surrounding sentences and compared
against the corresponding annotation and, for load-bearing claims, the primary
paper, specification, documentation, or project page. Dataset citations name
the dataset each source actually contributes; profiling citations describe
the tools' documented representations; and the Related Work citations are
scoped to the analysis each work performs.

Two inaccurate generalizations were repaired without changing the thesis:

1. The Background previously said OpenTelemetry/OpenInference “do not capture”
   semantic categories because prompts are natural language. Their
   specifications do define GenAI spans and attributes, but do not automatically
   derive AgentProf's low-cardinality categories from free-form prompts. The
   sentence now states exactly that boundary.
2. Related Work previously said AgentRx, TELBench, AgentAtlas, TrajAD, and
   AgentFixer all “localize faults.” AgentAtlas is better characterized as
   analysis/auditing. The sentence now says these systems “analyze or localize
   faults within trajectories,” while preserving the paper's cross-trajectory
   profiling distinction.

No quantitative value, RQ meaning, contribution, mechanism, title, or thesis
changed in these repairs.

## Pass 2.5 — academic-integrity checks

Preprint/publication status, venue wording, direct-versus-secondary sourcing,
retraction risk, citation chains, ghost citations, and double-blind language
were checked. The concrete changes were the OSWorld and AgentFixer corrections
above. Product and specification claims cite their official pages directly.
The classic methods and metric cite their original papers rather than a library
manual or secondary survey. Citation groups in the Introduction and Related
Work are survey-style lists; specific technical claims have an identifiable
supporting source.

## Pass 3 — missing citations found and added

The paper had seven citation sites that named a system, implementation method,
or metric without a source. They were repaired as follows:

| Site | Action | Primary source |
|---|---|---|
| First `pprof-compatible` output claim | added existing `pprof` citation (later moved from the abstract to the first body occurrence for AAAI compliance) | official Google pprof repository |
| Codex local histories | added `openaicodex` | official OpenAI “Introducing Codex” page |
| Claude Code local histories | added existing `claudecode` | official Anthropic documentation |
| llama.cpp tagger | added `llamacpp` | official ggml-org repository and grammar guide |
| TF-IDF backend | added `tfidf` | Salton and Buckley, 1988 |
| K-Means backend | added `kmeans` | MacQueen, 1967 |
| V-measure | added `vmeasure` | Rosenberg and Hirschberg, 2007 |

Five new, fully annotated bibliography entries were added. Three corresponding
primary PDFs were downloaded and read:

- V-measure: `docs/reference/2007-v-measure.pdf`, SHA-256
  `04ce978ea21197b5d4f442e2a068a9a3d9313054753c99c474ac47142f9fb2b3`;
- K-Means: `docs/reference/1967-macqueen-kmeans.pdf`, SHA-256
  `7b7bff0753f500c79e684f8e196b9cfdbf690768621110a195c3bd3a9733fec8`;
- term weighting: `docs/reference/1988-salton-buckley-term-weighting.pdf`,
  SHA-256
  `bcbbd4cc0aa49294312526f320d90c47e2554620ddac73512683dbdfdf3e11e8`.

The official web sources for OpenAI Codex and llama.cpp are kept as URLs in the
rendered bibliography. No citation was added merely to inflate density. The
Introduction and Background cite the external context they rely on; Design
mostly describes AgentProf's own mechanism; Evaluation cites every named public
dataset at setup and the nontrivial metric at use; every Related Work paragraph
has multiple directly relevant citations.

## Rejected or deferred actions

- The two “Comprehensive” warning titles were not rewritten because primary
  records prove those are the authors' real titles.
- No unused bibliography entry was deleted; the citation skill explicitly
  preserves verified unused sources for future use.
- No standalone citation ledger was created; annotation blocks remain the
  source of truth.
- No new claim, result, limitation, or negative experiment was introduced.
- The citation round did not attempt to solve the experiment obligations already
  recorded by Round 9; source verification cannot substitute for empirical
  authorization.

## Build, page, and rendering verification

`make -B` completed the full `pdflatex -> bibtex -> pdflatex -> pdflatex`
sequence with exit code 0. The final artifact is a 9-page US-letter PDF. The
reader-facing paper, including Conclusion, ends on page 7; the remaining space
on page 7 and pages 8--9 contain references. The log has:

- zero undefined citations or references;
- zero multiply-defined labels;
- zero overfull boxes;
- three local underfull horizontal boxes and one underfull vertical box, none of
  which clips or overlaps text.

Rendered page 7 was extracted in layout-preserving form. It contains the end of
RQ3, complete RQ4, Related Work, the complete Conclusion, and only then the
References heading. Pages 8--9 contain references only.

## Preservation and next action

The paper remains a positive four-RQ AgentProf paper based on the exact
submodule story. Round 10 adds source fidelity but does not authorize the
remaining experimental claims. In particular, the Round-9 obligations for the
strong RQ1 attribution result, direct prompt-tag validation, target-blind RQ2
ranking, a native profiler baseline, matched-decision evidence, unmistakable
real-problem localization, RQ3 backend coverage, and complete cold/warm RQ4
cost remain routed to EXPERIMENT/REVIEW.

The eleven-round `iter-refine-writing` inner loop is now complete. The next node
is an independent WRITE outer audit over the complete reports and rendered
paper; it must verify story fidelity, round completion, page compliance, and
that empirical objections were routed rather than disguised as prose fixes.
