# RQ3 Boundary Experiment Loop Completion

## Completion record

- Completed: 2026-07-14T03:45:19-07:00
- State path: `PROPOSE -> REVIEW -> REAL PREFLIGHT -> FULL RUN -> RESULT REVIEW`
- Plan reviews: three serial reviews completed; final plan approved
- Full-run completion: 5/5 folds and 1/1 current-profiler integration
- Independent result review: PASS, zero must-fix
- Tested-hypothesis verdict: **SUPPORTED**

## Evidence released to the outer loop

On 287 held-out OSWorld-Human task-instance sessions, the fixed supervised
boundary tagger reaches 0.739 boundary F1 versus 0.645 for the strongest simple
control and 0.816 B-cubed partition F1 versus 0.678. It wins the boundary
comparison in every fold. Current `agentpprof 0.2.37` profiles all 3,978 learned
group operations with exact mass conservation.

The evidence answers one boundary-identity component of RQ3 and is ready for
the WRITE gate. It does not alter the fixed four RQs or the paper thesis and
does not claim to complete task, phase, or action identity evaluation.
