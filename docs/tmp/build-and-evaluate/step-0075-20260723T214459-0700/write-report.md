# Step 0075 WRITE report — RQ4 end-to-end accounting

Timestamp: 2026-07-23T22:45:00-07:00
Outer gate: WRITE
Status: complete

## Accepted evidence

The WRITE pass used only the independently reviewed Step 0075 result:

- complete population: 405 sessions, 17,148 source-native turns, and 20,866
  operations;
- source-packet reconstruction median: 501.64 s over three full repetitions;
- deterministic assembly, root repair, validation, and canonicalization
  median: 3.54 s;
- current source-preserving operation and token replay median: 1.17 s each;
- exact token mass: 494,862,929;
- all reconstructed inputs and accepted A2 artifacts byte-identical across
  repetitions;
- all generated profiles readable by stock pprof and exactly
  mass-conserving;
- historical two-wave artifact-time envelope: 54.36 minutes.

## Paper change

`docs/paper/main.tex` now distinguishes:

1. fixed-input profile serialization over the four public cost workloads;
2. deterministic first-construction components from normalized operations and
   released raw archives;
3. the retained artifact-time envelope of the automatic-Agent workflow; and
4. unavailable instrumented model/provider inference time.

The text explicitly prevents three invalid interpretations:

- 1.17 s is not called automatic annotation latency;
- 54.36 minutes is not called model inference time or a lower bound;
- the experiment does not include capture, raw-to-normalized conversion, or
  live-agent overhead.

The thesis, fixed four RQs, and RQ1--RQ3 answers are unchanged.

## Build

`make` completed in `docs/paper/` and produced a 12-page PDF. The only reported
layout diagnostics were pre-existing underfull boxes; no LaTeX error or
undefined reference was introduced.

## Next step

The outer loop returns to EXPERIMENT for one matched same-input RQ1 control.
The RQ4 paper text remains provisional until whole-paper REVIEW checks all
numbers and scope statements together.
