# WRITE task: condensation pass 3c — Evaluation squeeze + references compaction

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Edit EXACTLY TWO files: `docs/paper/main.tex` and `docs/paper/references.bib`.
No git commands. Never touch `docs/agentpprof-paper/`. Invariants as before:
thesis x3 verbatim, four RQ titles, all tables, all figure PANELS, every
number, all 42 unique cite keys. Rewritten sentences get updated Chinese
comments.

## Edit 1 — figures to .70 and caption tightening

Reduce all five flamegraph `\includegraphics` widths from `.78\linewidth`
to `.70\linewidth`. Compress both flamegraph captions and the architecture
caption by removing restatement (keep panel identification and the
"AgentPProf emits only standard pprof" clause). Target: -6 rendered lines.

## Edit 2 — Evaluation prose squeeze (target -35 source lines total)

Within `\section{Evaluation}` ONLY, compress wording without deleting any
number, condition name, or claim:
- The data-classes paragraph ("We evaluate three data classes
  separately..."): fuse to ~4 lines keeping all counts and citations.
- RQ1 opening paragraph: fuse the population description sentences.
- The RQ1 population rank-agreement paragraph: fuse the reading sentences
  (keep all statistics and both citations).
- The profile-guided reading paragraph: fuse setup sentences 1-2; keep all
  numbers and disclosures.
- Case Study 2 analysis paragraphs (recovery/completion and the
  looping-AP paragraph): fuse overlapping clauses; keep every number.
- RQ3 CodeTraceBench paragraphs: the A2 description repeats mark counts
  ("5,752 marks" appears with depth breakdown and again near
  canonicalization); state each count once.
- RQ4: fuse the scaling-slope sentences; move the per-workload replay
  detail sentence ("Joining the fixed target operations...") if any
  remains to appendix app:a2-reconstruction.

## Edit 3 — references.bib compaction (no key dropped)

For every entry: remove `url` and `doi` fields when the entry has a
published venue (keep them for arXiv/web-only entries where they are the
only locator); remove `abstract`-like fields if any; keep the VERIFIED
comment blocks (they do not render). Do not remove or rename any entry.
Target: references block <= 2.0 rendered pages.

## Validation and deliverables

1. Compile clean; 0 undefined refs/citations; 42 cite keys; thesis x3;
   all 5 flamegraph panels present.
2. Report: total pages, page where BODY ends (before References), page
   where References ends, figure pages. Targets: body ends on page 7 or
   very close; References ends on page 9-10.
3. `write-report.md` in THIS directory with per-edit accounting.

## Amendment (after failed first attempt)

The first attempt exited without edits after a sandbox rejection. Binding
corrections:
- NEVER write to /tmp or any directory outside the repository; put any
  scratch files inside THIS task directory and delete them before
  finishing.
- Do NOT perform any citation audit beyond the single required check
  (count unique cite keys before and after your edits with one command and
  confirm equality; the absolute number may be 42 or 61 depending on the
  counting method — only before==after matters).
- Execute the three enumerated edits directly; no exploration beyond the
  files named in this spec and the appendix subsections referenced.
