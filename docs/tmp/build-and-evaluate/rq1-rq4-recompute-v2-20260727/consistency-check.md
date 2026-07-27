# Two-run consistency check

## Result

**Pass.** Two independent executions of the repaired projection and all
requested downstream analyses produce identical research events, estimator
CSVs, result summaries, and rendered PNGs.

Run 1 is the committed output directory. Run 2 was generated under
`/tmp/agentsight-rq1-rq4-v2-rerun.ciVefV`. Project presentation order was
canonicalized before comparing aggregate files because source discovery order
is not an estimand.

## Exact comparisons

The following were byte-identical after canonicalizing only project row/object
presentation order where applicable:

- all six research event arrays and attributed actions;
- `rq1-artifacts.csv`, `rq1-mutations.csv`, and `rq1-summary.csv`;
- the 68,886-row status-preserving RQ3 access ledger;
- every CSV and JSON under `extensions/`;
- every CSV under `rq2/raw`, `rq3/raw`, `rq4/raw`, and
  `rq3-allocation/raw`;
- RQ1, RQ2, RQ3, RQ3-allocation, and RQ4 `result.md`;
- RQ6 `local-anchor.csv` and `local-anchor.json`;
- every generated PNG.

Generated PDFs were not used as the equality anchor because their renderer
metadata may vary. Their source CSVs and corresponding PNG pixels were exact.

## Live-source diagnostic normalization

The real-HOME corpus is live. During run 2, the AgentSight source scan observed
two additional current-session source rows whose timestamps were later than
the fixed cutoff:

| Field | Run 1 | Run 2 |
|---|---:|---:|
| AgentSight `source_events` diagnostic | 867,894 | 867,896 |
| Included roots | 301 | 301 |
| Tool actions | 97,586 | 97,586 |
| Attributed Tool actions | 94,031 | 94,031 |

Those two rows are cutoff-excluded diagnostics: they do not occur in the
research event arrays and do not enter any numerator, denominator, episode,
access, component, boundary, extension, or sensitivity estimand. All other
project diagnostics were identical. The equality result therefore compares
the cutoff-defined scientific corpus, while explicitly recording the harmless
live-source scan-count difference rather than hiding it.
