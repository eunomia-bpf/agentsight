# AgentFlame Paper-Scale Human Evidence Bundle R258

This package combines the paper-scale C5 participant packets from R249 and the
paper-scale C6 labeler packets from R252. It contains collection inputs only.
It contains no answer key, scorer script, raw agent trace, participant response,
human label, or synthetic smoke output.

## Collection Flow

1. Send `c5/participants/P01.md` through `P12.md` to the corresponding
   participants.
2. Keep a private completed copy of `c5/user-task-response-template-r249-paper.csv` and fill one row per task.
3. Send `c6/L01/*.csv` and `c6/L02/*.csv` to two independent labelers.
4. Put completed returned files into the R195 inbox or pass them explicitly to
   `python3 docs/visexp/r195_human_evidence_pipeline.py`.
5. Do not claim C5, C6, or weak accept until R195 scores real completed returns.

## Return Files

| File | Package path | Rows | Required gate |
|------|--------------|------|---------------|
| `user-task-response-template-r249-paper.csv` | `c5/user-task-response-template-r249-paper.csv` | 168 | `yes` |
| `user-task-assignments-r249-paper.csv` | `c5/user-task-assignments-r249-paper.csv` | 168 | `yes` |
| `r124-labeler-1.csv` | `c6/L01/r124-labeler-1.csv` | 300 | `yes` |
| `r124-labeler-2.csv` | `c6/L02/r124-labeler-2.csv` | 300 | `yes` |
| `r190-labeler-1.csv` | `c6/L01/r190-labeler-1.csv` | 160 | `if claiming merge quality` |
| `r190-labeler-2.csv` | `c6/L02/r190-labeler-2.csv` | 160 | `if claiming merge quality` |
| `r203-labeler-1.csv` | `c6/L01/r203-labeler-1.csv` | 41 | `if claiming regenerated-tag promotion` |
| `r203-labeler-2.csv` | `c6/L02/r203-labeler-2.csv` | 41 | `if claiming regenerated-tag promotion` |
| `r195-inbox-template/*` | `r195-inbox-template/` | 1002 | `template only` |

Blank templates, this tarball, subagent review, synthetic rows, or LLM-filled
labels cannot upgrade any claim gate.
