# Task: mine existing records for evidence answering the PDF review

Read-only over the repository (write only into THIS directory). No git
commands. Repository: /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.

A PDF review demands the following controls/evidence. For EACH item, search
the complete experiment records (docs/tmp/build-and-evaluate/ steps 0001-0087,
docs/visexp/out/, .agentsight/experiments/, docs/evaluation.md) and report:
FOUND (with exact file paths and the exact numbers, and whether the paper
already contains it) or MISSING (nothing usable exists).

1. Flat semantic grouping vs recursive hierarchy — any experiment where a
   FLAT semantic tagging/grouping (no nesting) is compared against the
   recursive hierarchy on ranking, reading, detection, or structure metrics.
   (Note: Case Study 2 has a registered fixed-chain vs recursive comparison;
   assess whether it qualifies.)
2. LLM-generated summary control — any condition where equal-information
   summaries (not semantic operation names) drive grouping or reading.
3. Frozen Agent backend on an independent population — any run of the
   direct/Agent annotation backend on a population other than CodeTraceBench
   scored against independent human structure annotations.
4. Reader budget / quality-cost curve — any data on selection-budget
   sensitivity beyond the fixed 5-group point (step-0080 analysis-001 has
   budget-saturation data; assess it).
5. Second reader family — any reader-study condition executed with a
   non-Grok reader on TraceElephant (step 0083 used GLM on HINTBench;
   assess relevance).
6. Native-hierarchy and raw-action hierarchy controls for the reader study
   (0081 raw skeleton exists; native-session skeleton?).
7. Backend model/version/prompt/decoding disclosures sufficient for a
   reproducibility statement (search cost-records and execution logs for
   exact model IDs and configs of every evaluated backend).
8. Multiple-run variance for the direct backend (any repeated runs?).
9. Boundary-F1 context: any analysis explaining the 0.480 boundary result
   (e.g., near-miss distribution, off-by-one analysis).
10. Anything usable as a structured closest-work comparison (prior
    related-work notes, docs/background-related-work.md).

Output: evidence-report.md in THIS directory — one section per item:
FOUND/PARTIAL/MISSING, paths, exact numbers, and a one-line recommendation
(add-to-paper / run-new-experiment / not-needed).
