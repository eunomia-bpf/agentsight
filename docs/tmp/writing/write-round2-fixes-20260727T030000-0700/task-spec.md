# WRITE task: round-2 review fixes (eight enumerated edits)

Edit EXACTLY ONE file: docs/paper/main.tex in
/home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. No /tmp. Bilingual %-comments per house style. Keep
thesis x3, RQ titles, all numbers except where an edit below says.

1. Broken section refs: find every `\ref{sec:...}` that renders empty
   (the class does not number sections) — the PDF shows "Section measures
   this case", "the case previewed in Section .", "the responsibility
   described in Section ." Replace each `Section~\ref{sec:X}` with the
   section's NAME (e.g. "the Evaluation section", "Case Study 1"), exactly
   as done earlier for appendix refs. Verify zero empty refs remain via
   pdftotext grep for "Section \." and "Section ,".
2. Name consistency: replace every "AgentPProf" in main.tex prose/captions
   with \sys (the paper's system name). Do not touch bibliography keys.
3. Over-segmentation sentence (RQ3): replace the clause "the benign
   direction for profiling because extra splits subdivide work without
   merging unrelated responsibilities, as the 0.793 B$^3$ precision
   confirms" with: "the error therefore skews toward extra splits:
   predicted groups remain largely pure subsets of gold stages (B$^3$
   precision 0.793), so the dominant failure subdivides work rather than
   merging unrelated responsibilities". Chinese comment updated.
4. Budget sentence (reader paragraph): extend the existing budget
   sentence with the uncapped fact, verified against
   docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/analysis-001/analysis-report.md:
   re-parsing the uncapped stage-one responses shows the reader proposed
   more than five groups on zero of 220 queries, and every missed target
   group was entirely absent from its ordered selection.
5. "Complete workload" wording (RQ2): where HINTBench is introduced, make
   the one sentence say the complete RELEASED TEST SNAPSHOT (536 of the
   paper-reported 629) is used, and zero-positive trajectories are
   consumed for coverage but excluded from MAP as AP is undefined without
   a positive. (Both facts are already in the paper; unify them at first
   mention.)
6. Horizon distributions (one sentence, RQ3 or data-classes paragraph):
   per-workload mean operations per trajectory computed from numbers
   already in the paper: CodeTraceBench 20,866/405 = 51.5;
   OSWorld-Human 3,978/287 = 13.9; AgentProcessBench 8,509/1,000 = 8.5;
   HINTBench 12,877/536 = 24.0; TraceElephant 5,960/220 = 27.1; and the
   42-session population's longest sessions span tens of hours. Present
   as: benchmark trajectories are short-to-medium horizon while the
   workstation population supplies the long-horizon regime.
7. CS3 depth observation (one sentence after the 70.4% sentence): most
   token mass staying at prompt depth reflects genuinely many-tasked
   development sessions under the fixed one-pass protocol; operation mass
   resolves deeper (43.9% at depths three and four) exactly where
   repeated engineering work concentrates.
8. Privacy statement (one short paragraph at the end of Implementation):
   \sys runs entirely offline on local histories; profiles carry only
   short semantic names, bounded text previews, and numeric measures as
   labels; no trajectory content leaves the machine unless the user
   shares the profile, and packet previews are truncated as disclosed in
   the appendix.

Validate: latexmk clean, zero "^!" errors, thesis x3, cite keys
unchanged; pdftotext shows no "Section ." artifacts. write-report.md here
with before/after per edit.
