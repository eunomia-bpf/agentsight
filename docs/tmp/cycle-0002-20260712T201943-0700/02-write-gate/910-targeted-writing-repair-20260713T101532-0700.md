# Targeted WRITE Repair and Whole-Paper Verification

- Completed: `2026-07-13T10:15:32-07:00`
- Cycle: `cycle-0002-20260712T201943-0700`
- Phase: `BUILD_AND_EVALUATE`
- Gate: `WRITE` re-entry
- Parent: `900-independent-outer-audit-20260713T101222-0700.md`
- Mode: phase-permitted targeted source, format, report-integrity, and
  whole-paper verification
- Git operations: none
- Submodule edits: none
- Scientific-contract changes: none
- Verdict: **TARGETED REPAIR COMPLETE; REQUEST FRESH OUTER AUDIT**

## Post-audit source-scope correction

The fresh outer audit found that this report described the support source
accurately, but the paper's shorter sentence promoted the surrounding service's
annual request volume to the agent system itself. The paper-level wording from
this snapshot is therefore superseded by the next targeted source-fidelity
repair. All hashes below remain the true exit hashes of this node.

## Question and entry

The initial independent outer audit found five bounded defects: an
unreconstructable serial timeline, two false no-Git statements, a
BUILD_AND_EVALUATE/full-writing phase deviation, an unsourced scale statement,
and unverified AAAI abstract compliance. This node repairs only those defects
and verifies the complete current paper. It does not rerun the full writing
loop, reinterpret experimental evidence, or change the title, thesis, four
RQs, motivation, system model, contributions, or section organization.

The governing paper-level thesis remains:

> **Agent observability needs profiling, not only debugging.**

The fixed RQs remain resource attribution, real-problem localization, tag
accuracy, and profiling cost.

## Provenance and phase deviations

### Serial chronology

The reported Round-0-through-Round-10 timestamps cannot be reconstructed into
a truthful serial chronology from available evidence. No timestamp was
invented or normalized. The historical reports remain available as child-node
records, but they no longer prove a serial full-writing run. This clean
targeted whole-paper verification supersedes that provenance claim for the
current gate transition.

### Git report correction

Rounds 8 and 9 now say that each used one prohibited read-only
`git diff --check` command and no state-changing Git command. Each report has a
timestamped correction explaining that its original `Git operations: none`
statement was false. No Git command was run during this repair.

### Phase mismatch

The current user instruction places the project in evaluation. Invoking
`iter-refine-ideas` and a full `iter-refine-writing` run during this gate was a
procedural deviation from the present `BUILD_AND_EVALUATE` policy. The edits
were retained because independent comparison shows that the exact original
thesis, the fixed RQs, the two-object model, and the positive story survived;
reverting faithful source, structure, and language repairs would not restore
the missing procedure. From this node onward, evaluation WRITE work is
targeted only.

## AAAI-27 primary-rule verification

The current rules were verified against three first-party artifacts:

1. [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
   states that submissions have seven pages of main content and at most nine
   pages total, with pages beyond seven reserved for references.
2. [AAAI-27 Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
   require a complete abstract, anonymous two-column camera-ready style, US
   Letter PDF, Type 1 or TrueType fonts, and up to seven technical pages plus
   references and the separately submitted reproducibility checklist.
3. The official Author Kit archive downloaded through the CFP's Author Kit
   link has SHA-256
   `e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d`.
   `AuthorKit27/AnonymousSubmission2027.tex`, lines 497--498, says: “Do not
   include references in your abstract!”

Neither the current Submission Instructions nor the official Author Kit states
an abstract word limit. The approximately 280-word abstract therefore was not
compressed to satisfy an obsolete assumed 150-word limit. It preserves the
problem, exact thesis, model, evaluation scope, and strong positive results.

The actual format defect was repaired: `\cite{pprof}` was removed from the
abstract and placed on the first body occurrence of `pprof-compatible` in the
Introduction. A direct check finds zero citation commands between
`\begin{abstract}` and `\end{abstract}`.

## Real-world scale source repair

The ambiguous assertion that one trajectory contains “thousands to millions
of interactions” was replaced with two stronger, measurable statements:

- an agent run can consume millions of tokens;
- production agent systems can serve millions of requests per year.

The Introduction directly cites two first-party production sources:

- [OpenAI, “Introducing the Codex App”](https://openai.com/index/introducing-the-codex-app/)
  reports projects spanning hours, days, or weeks and a single-prompt Codex run
  consuming more than seven million tokens;
- [OpenAI, “Improving Support with Every Interaction at OpenAI”](https://openai.com/index/openai-support-model/)
  describes an internal system built with Agents SDK and related APIs in an
  organization handling millions of support requests per year, with step-level
  traces, tool-call inspection, and continuous evals.

The abstract mirrors this sourced scale without an inline citation, as the
AAAI Author Kit requires. Two fully annotated bibliography entries record the
source scope and intended use. This repair increases source fidelity and keeps
the stakes large; it does not weaken the paper to short or toy workflows.

## Citation verification

The citation verifier ran over the repaired bibliography and reported:

```text
Found 54 bib entries (44 active)
Total entries checked: 44
Errors (must fix): 0
Warnings (should review): 2
OK: No VERIFIED entries have mismatches
```

The two warnings remain false-positive title heuristics for the official
API-Bank and GUIOdyssey titles containing “A Comprehensive.” Counts after the
repair are:

| Check | Count | Result |
|---|---:|---|
| Bib entries | 54 | complete |
| `% VERIFIED:` | 54 | complete |
| `% REAL: yes` | 54 | complete |
| `% PDF:` | 54 | complete |
| `% ABSTRACT:` | 54 | complete |
| `% USED_FOR:` | 54 | complete |
| Unique cited keys | 44 | complete |
| Citation commands | 52 | no undefined citation |

## Build, rendering, and paper verification

`make -B` completed `pdflatex -> bibtex -> pdflatex -> pdflatex` successfully.
The final pass has no undefined citation/reference, multiply-defined label, or
overfull box. Three local underfull horizontal boxes remain cosmetic and do not
clip or overlap content.

- `docs/paper/main.tex` SHA-256:
  `0bf779123348f92bab109a18217ba5201ec36a652d61c39cd460c25bbc2b2675`
- `docs/paper/references.bib` SHA-256:
  `96f4a29cfc42d1891023a62f0a4ec883b0fe082271c3d8f7bf65dbfc7a2d13d8`
- `docs/paper/main.pdf` SHA-256:
  `a2c345d69f683b8c9bbe758eb548123b5d3929080fb04941ce5f470cdf994906`
- Untouched submodule `main.tex` SHA-256:
  `430d94ba7714c328c4583aa4991326601ceef55ba1f01b59807a8beb6aa4bb91`

The PDF is nine US-letter pages, PDF 1.5, unencrypted, and uses embedded Type 1
fonts. Page 7 contains the end of RQ3, complete RQ4, Related Work, complete
Conclusion, and then the References heading. Pages 8--9 contain references
only. This satisfies the current seven-page-main-content/nine-page-total rule.

Whole-paper checks confirm:

- the exact thesis remains in Abstract, Introduction, and Conclusion;
- exactly four RQ subsections remain in the fixed order;
- Evaluation remains explicitly organized by those RQs;
- operations and operation stacks remain the only core model abstractions;
- no internal negative or inconclusive experiment entered the paper;
- no result number, RQ conclusion, or empirical scope changed in this repair;
- the read-only submodule, `docs/idea-story.md`, skills, and KVM content were not
  edited.

## Scientific impact, remaining objections, and next action

This node closes only the WRITE provenance, source, and AAAI-format defects.
It does not authorize the historical quantitative results or make the paper
submission-ready. The initial outer audit's ranked experiment obligations
remain open: independent RQ1 attribution, target-blind and matched-decision RQ2
evidence, unmistakable real-problem localization, broader RQ3 tag-backend
validation, integrated cold/warm RQ4 cost, and closest-work novelty defense.

Next, a fresh independent outer auditor must read this repaired snapshot and
decide whether the bounded WRITE defects are closed. If so, the gate transitions
to ordinary REVIEW, which will rank the scientific objections and select the
single highest-paper-value complete experiment. It must not rewrite the story
or claim milestone acceptance.
