# Independent result review

Timestamp: 2026-07-22T15:53:45-07:00
Verdict: PASS for the 405-session CodeTrace result, current-A0 fixed-input cost,
and retained 338-pair differential case; INCOMPLETE only for RQ2 in the full
experiment-001 method matrix

## Independent reconstruction

The reviewer reconstructed the gold partition directly from raw predictions,
the recurrence assignments, and the official parquet without calling the
experiment scorer's metric functions. It verified:

- 405 sessions, 17,148 source turns, and 20,866 operations;
- 20,461 adjacent pairs, 2,948 official stages, and 251 task clusters;
- complete nonoverlapping stage intervals and source order;
- every source turn belongs wholly to one Agent mark;
- 5,901 Agent occurrence groups are session-local and contiguous;
- operation mass 20,866 and token mass 494,862,929;
- identical operation keys across count, token, and prediction inputs.

The independent B-cubed and boundary results match `score/summary.json` in
full. It also reproduced all 10,000 task-cluster bootstrap deltas and the 95%
interval `[0.016986, 0.056883]`.

## Scientific judgment

- Run status: valid.
- Tested hypothesis: supported for flat partition and boundary fidelity.
- Research value: supporting evidence.
- Paper impact: additional RQ3 structure-fidelity evidence plus an RQ1
  attribution case; not a complete answer to either RQ.
- Current paper decision: A0 may be adopted on CodeTrace, but universal
  dominance, nested-hierarchy accuracy, semantic-name accuracy, cross-session
  equivalence, and practicality are not established.

Framework deltas versus recurrence are +0.1204 Terminus2, +0.0063 OpenHands,
-0.0207 SWE-agent, and -0.0397 mini-SWE-agent. A0 wins 140 tasks and loses 111.
Its 5,901 groups versus 2,948 official stages and boundary precision 0.2846
show material oversegmentation.

## Product judgment

Both full `.pb.gz` files load in stock `go tool pprof`, conserve their declared
mass, and retain source-session, call, and evidence labels. Omitting unique
session/prompt/call frames from the aggregate function stack is necessary for
cross-session folding and does not remove drilldown evidence.

The case-only pprof-name collision fix is valid and non-gold-driven: case-folding
changed only 17 display-name variants, left all 5,901 marks and every score
unchanged, and made standard pprof replay succeed. The Git deployment case
answers a real resource-localization question; time, file, and network widths
remain unmeasured in this result.

## Must-fix routing

1. Describe the score as RQ3 flat partition/structure fidelity, not direct
   proof of RQ1 attribution or semantic tag-name correctness.
2. Do not call the `native_turn` scorer row the richer planned N0.
3. Report framework heterogeneity and oversegmentation.
4. Do not infer nested topology, semantic equivalence, localization utility,
   or practicality from this score.
5. Keep the full matrix open until N0, RQ2, RQ4, and the differential case are
   complete.
6. Treat general cross-session name equivalence as unproven outside explicitly
   reconciled cases.

## N0 follow-up review

After the first review found that `native_turn` did not implement the
predeclared N0, the scorer added a separate `native_tree` row. A second
independent reconstruction verified all 20,866 occurrence IDs and reproduced
15,813 predicted groups, B-cubed P/R/F1 0.974547/0.248903/0.396530, and boundary
P/R/F1 0.151090/0.915454/0.259373.

Verdict: PASS. N0 reads only fixed source fields exposed as
`phase -> action_kind -> raw_action_key`, contracts only adjacent identical
paths, qualifies occurrences by session, and is constructed before the
official manifest is opened. It uses no learned rule, threshold, gold label,
resource weight, or A0 output. `native_turn` remains a diagnostic; N0 is the
structurally matched native-tree baseline; N1 remains the stronger registered
competitor and headline comparator.

## Differential-case follow-up review

Independent reconstruction confirms 1,289 consensus-success trajectories after
13 conflicts are excluded, 125 eligible mixed-outcome tasks, 440 distinct real
trajectories, and all 338 bad--good pair occurrences. The signed aggregate
contains 7,366 bad-side and 3,780 good-side operations, with 7,103 positive and
3,517 negative occurrences over 4,140 nonzero stacks. Stock-pprof readback
reproduces every reported major result/action difference.

The rematerialized profile changes no stack or weight. It adds the source model,
source session, and step evidence ID as pprof labels; `go tool pprof -tags`
exposes `agent`, `source_session`, `evidence_id`, and `comparison_side`. Release
and debug output hashes are identical, and `go tool pprof -top` is identical to
the old aggregate. Verdict: PASS for the precise collection-level claim that a
pair-occurrence-weighted signed pprof exposes failed-side excess and
successful-side missing trace-derived paths with source drilldown. It does not
support causality, classification, A0 accuracy, nested topology, name accuracy,
or human utility. No additional differential scientific run is required.
