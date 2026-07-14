# HINTBench Evidence-Boundary Correction

- Timestamp: 2026-07-14T01:40:41-07:00
- Parent: `020-independent-outer-audit-v1-20260714T014041-0700.md`
- Objective: correct the single overbroad construction-isolation sentence without changing any result, claim, thesis, or RQ.

## Correction

The RQ2 subsection now states explicitly:

- HINTBench development labels select among 24 fixed field orders.
- Reported HINTBench test labels remain held out from tag, stack, and ranking construction.
- All AgentProcessBench and TraceElephant targets remain held out from those constructions.
- The held-out reported targets are read only by the final scorer.

No metric, result interpretation, citation, story element, or other paper section changed.

## Completion Condition

Rebuild the paper and obtain a PASS from a fresh read-only auditor on this corrected boundary and the previously verified evidence.
