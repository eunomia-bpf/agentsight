# WRITE task: remove historical-protocol remnants; unify backend naming

Edit EXACTLY ONE file: docs/paper/main.tex in
/home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Bilingual %-comments maintained. Keep thesis x3, RQ
titles, all current-backend numbers (0.764/0.480 etc.), all figures.

1. DELETE the historical prior-protocol result mentions: the "prior
   interval-protocol Agent artifact (0.704)" comparison clause and the
   "earlier Agent protocol reached 0.704 ... we retain..." sentence in
   RQ3 (and their Chinese comments), plus the Design clause noting an
   earlier interval-recursive protocol in the research record. The
   direct-vs-recurrence comparison (+0.101 [0.087, 0.116]) stays.
2. Sweep every remaining "A2" mention in the document (Design, RQ4,
   appendix subsection titles/labels/text). Rename to neutral wording
   ("the Agent annotation", "the adopted marks", "agent-mark
   reconstruction") ONLY where the underlying number is
   backend-independent or was measured on artifacts the current backend
   also uses. VERIFY provenance per number against
   docs/tmp/build-and-evaluate/step-0075-*/ and step-0087-*/ records:
   - source-packet construction 501.64 s: the same packets step 0087
     reused -> may be neutrally attributed;
   - numbers measured only on the prior marks (e.g., 3.54 s assembly,
     1.17 s replay, 54.36 min envelope): either replace with the
     equivalent measurement from step-0087 records if one exists, or
     delete the sentence; NEVER attribute a prior-marks measurement to
     the direct backend.
3. Appendix "A2 Reconstruction Cost Detail" subsection: retitle and
   rewrite consistently with rule 2, or delete it if nothing verifiable
   remains, removing its \ref pointer accordingly.
4. Compile clean, no undefined refs, cite keys unchanged, thesis x3.
   write-report.md in THIS directory: every deletion/relabel with the
   provenance decision made for each number.
