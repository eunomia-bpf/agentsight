# Round 0 — Macro Structure

**Date:** 2026-07-07

## Findings
- Section order correct: Abstract → Intro → Background → Design → Impl → Eval → Related → Conclusion ✓
- Design separated from Implementation ✓
- Architecture diagram present (placeholder) ✓
- 9 `\paragraph{}` headers — banned by common-pitfalls.md (Must-fix)
- 3 `\textbf{}` run-in headers in Related Work — banned (Must-fix)

## Changes
- §3.3: Converted 3 backend \paragraph headers to "First/Second/Third" flowing prose
- §5: Removed \paragraph{Evaluation setup.}
- §5.2: Removed \paragraph{Benchmark setup.}, \paragraph{Localization results.}, \paragraph{Actionability...}
- §5.3: Removed \paragraph{Scale and syntax validity.}, \paragraph{Ground-truth agreement...}
- Related Work: Removed 3 \textbf{} run-in headers, paragraphs now start with topic sentences

## Verification
- 0 \paragraph{} remaining, 3 \textbf{} remaining (all in contribution \enumerate — standard)
- Compiles clean, 7 pages
